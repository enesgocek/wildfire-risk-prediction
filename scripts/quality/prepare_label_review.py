"""Offline review packet: retained difficult cases and a separate grid-day pilot sample."""

import argparse
import hashlib
import json
import socket
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from wildfire_risk_prediction import feature_month
from wildfire_risk_prediction import label_review as review
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
OBS = "outputs/reports/dataset/observation_materialization_v1/20261014T145638Z_c0881064"
OBS_SHA = "fb5fa5ce8c83be2c4e21b130bb06935a5e2d8014e45460c1f61660b73262cb14"
DECISION = "outputs/reports/dataset/decision_review_v1/20261010T124447Z_f3e2eef2"
DECISION_SHA = "ad0567e829719d4b2b45cb7b696ce4442c8fc083268a670c4696b1bd642aa5a9"
PROTECTED = (
    "outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/"
    "protected_inputs_readback_20261013.json"
)
CONTEXT = [
    "grid_id",
    "forest_fraction",
    "shrub_fraction",
    "agriculture_fraction",
    "water_fraction",
    "weather_support_group",
    "habitat_eligibility",
]


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def checked(name, expected, pins):
    path = ROOT / name
    require(path.is_file() and not path.is_symlink(), "Regular retained review input")
    digest = sha(path)
    require(expected is None or digest == expected, "Review input hash changed")
    pins[name] = digest
    return path


def accepted_sources(pins):
    observation = json.loads(checked(OBS + "/accepted_readback.json", OBS_SHA, pins).read_text())
    months = [f"{y}-{m:02d}" for y in range(2018, 2024) for m in range(1, 13)]
    require(
        observation["status"] == "selected_observation_months_materialized"
        and observation["scope_is_full_training"] is True
        and sorted(observation["selected_months"]) == months
        and sorted(r["month"] for r in observation["reports"]) == months
        and observation["daily_observation_status"] == "unknown"
        and observation["negative_label_permitted"] is False
        and observation["labels_created"] is False
        and observation["diagnostics_are_model_inputs"] is False
        and observation["model_ready"] is False
        and observation["final_test_accessed"] is False,
        "Full training source and closed gates",
    )
    for name, digest in observation["source_and_method_sha256"].items():
        checked(name, digest, pins)
    decision = json.loads(checked(DECISION + "/readback.json", DECISION_SHA, pins).read_text())
    require(
        decision["status"] == "decision_review_packet_readback_passed"
        and decision["labels_created"] is False
        and decision["independent_expert_review_completed"] is False
        and decision["scenario_selected"] is None,
        "Retained unreviewed case packet",
    )
    tables = {}
    for name in ("event_cases.csv", "event_members.csv", "support_cells.csv"):
        tables[name] = pd.read_csv(
            checked(DECISION + "/" + name, decision["artifact_sha256"][name], pins),
            float_precision="round_trip",
        )
    return observation, tables


def deny(*args, **kwargs):
    raise RuntimeError("Offline label review preparation")


def write_verified_table(path, frame):
    frame.to_csv(path, index=False, mode="x")
    reread = pd.read_csv(path, float_precision="round_trip")
    # Compare missingness explicitly; pandas NA and CSV NaN have different types.
    pd.testing.assert_frame_equal(frame.reset_index(drop=True).isna(), reread.isna())
    expected = frame.reset_index(drop=True).astype(object).where(frame.notna().to_numpy(), None)
    actual = reread.astype(object).where(reread.notna(), None)
    pd.testing.assert_frame_equal(expected, actual, check_exact=False, rtol=1e-12, atol=1e-12)


def run(per_stratum=2):
    require(isinstance(per_stratum, int) and 1 <= per_stratum <= 10, "Bounded pilot allocation")
    started = time.monotonic()
    pins = {}
    accepted, tables = accepted_sources(pins)
    for name in (
        "src/wildfire_risk_prediction/label_review.py",
        "src/wildfire_risk_prediction/target_admission.py",
        "scripts/quality/prepare_label_review.py",
        PROTECTED,
    ):
        checked(name, None, pins)
    protected = json.loads((ROOT / PROTECTED).read_text())
    for name, digest in protected.items():
        checked(name, digest, pins)
    cases = tables["event_cases.csv"]
    support = tables["support_cells.csv"]
    require(support.grid_id.is_unique and len(support) == 2899, "Accepted complete grid")
    grid = review.geography(support.grid_id.tolist())
    requests = review.event_requests(cases, tables["event_members.csv"])
    needed = pd.MultiIndex.from_frame(
        requests.loc[
            requests.lookup_in_training_calendar, ["grid_id", "observation_lookup_timestamp_utc"]
        ].drop_duplicates()
    )
    populations, links, candidates = [], [], []
    total = 0
    for report in sorted(accepted["reports"], key=lambda r: r["month"]):
        require(time.monotonic() - started < 900, "Local review runtime reserve")
        month = report["month"]
        month_report = json.loads(checked(OBS + f"/{month}/readback.json", None, pins).read_text())
        require(month_report == report, "Monthly observation report agrees with final")
        table = checked(OBS + f"/{month}/observations.csv.gz", report["table_sha256"], pins)
        frame = pd.read_csv(table, float_precision="round_trip")
        expected_days = feature_month.calendar_days(month)
        require(
            len(frame) == report["rows"] == len(expected_days) * len(grid)
            and set(frame.prediction_timestamp_utc)
            == {d + "T00:00:00+00:00" for d in expected_days}
            and frame.groupby("prediction_timestamp_utc").size().eq(len(grid)).all(),
            "Exact monthly calendar and row count",
        )
        selected = review.classify(frame, grid)
        total += len(frame)
        populations.append(
            selected.groupby(review.STRATA).size().rename("population_n").reset_index()
        )
        part = review.smallest(selected, per_stratum)
        candidates = (
            part
            if isinstance(candidates, list)
            else review.smallest(pd.concat([candidates, part], ignore_index=True), per_stratum)
        )
        links.append(frame.loc[pd.MultiIndex.from_frame(frame[review.KEYS]).isin(needed)])
        print("REVIEW FRAME", month, total, flush=True)
    population = pd.concat(populations).groupby(review.STRATA, as_index=False).population_n.sum()
    require(
        total == accepted["totals"]["rows"] == int(population.population_n.sum()),
        "Full sampling population reconciled",
    )
    sample = review.finalize_sample(candidates, population, per_stratum)
    sample = sample.merge(support[CONTEXT], on="grid_id", validate="many_to_one")
    linked = review.attach_events(requests, pd.concat(links, ignore_index=True))
    linked = linked.merge(support[CONTEXT], on="grid_id", validate="many_to_one")
    hard = cases.copy()
    hard["review_unit_id"] = "event:" + hard.scenario + ":" + hard.cluster_id
    hard["target"] = pd.NA
    tasks = pd.concat(
        [
            review.blank_reviews(hard.review_unit_id.tolist(), "purposive_event_scenario"),
            review.blank_reviews(sample.review_unit_id.tolist(), "stratified_grid_day_pilot"),
        ],
        ignore_index=True,
    )
    strata = sample.groupby(review.STRATA).agg(sample_n=("grid_id", "size")).reset_index()
    strata = population.merge(strata, on=review.STRATA, validate="one_to_one")
    strata["inclusion_fraction"] = strata.sample_n / strata.population_n
    strata["expansion_weight"] = strata.population_n / strata.sample_n
    # Keep evidence snapshots immutable; human work belongs in a separate revision.
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    out = ROOT / "outputs/reports/dataset/label_review_v1" / stamp
    out.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    for name, frame in (
        ("random_grid_days.csv", sample),
        ("purposive_event_cases.csv", hard),
        ("event_observation_links.csv", linked),
        ("stratum_allocation.csv", strata),
        ("sampling_geography.csv", grid),
        ("review_decisions_template.csv", tasks),
    ):
        path = out / name
        write_verified_table(path, frame)
        artifacts[name] = sha(path)
    require(
        tasks[review.REVIEW_FIELDS].isna().all().all()
        and tasks.review_status.eq("not_reviewed").all(),
        "No human verdict fabricated",
    )
    require(
        all(sha(ROOT / name) == digest for name, digest in pins.items()),
        "All retained inputs unchanged at close",
    )
    result = {
        "version": review.VERSION,
        "status": "review_packet_readback_passed",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "seconds": time.monotonic() - started,
        "population_grid_days": total,
        "nonempty_strata": len(strata),
        "random_pilot_grid_days": len(sample),
        "purposive_event_scenario_cases": len(hard),
        "unique_purposive_membership_patterns": int(hard.membership_sha256.nunique()),
        "event_cell_role_links": len(linked),
        "event_links_outside_training_calendar": int(
            linked.lookup_status.eq("outside_training_calendar").sum()
        ),
        "review_units": len(tasks),
        "seed": review.SEED,
        "pilot_per_nonempty_stratum": per_stratum,
        "strata": review.STRATA,
        "sampling_rank": "SHA256(seed|grid_id|UTC-midnight-iso)",
        "allocation": "smallest hash ranks; min(pilot_per_stratum, population_n)",
        "geography": "four equal-width EPSG:6933 grid-column sectors; not provinces",
        "signal_population": population.groupby("signal_stratum").population_n.sum().to_dict(),
        "signal_sample": sample.signal_stratum.value_counts().to_dict(),
        "sampling_is_operational_pilot": True,
        "error_rate_estimated": False,
        "independent_expert_review_completed": False,
        "scenario_selected": None,
        "labels_created": False,
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "exact_target_window_coverage_proven": False,
        "model_ready": False,
        "validation_accessed": False,
        "final_test_accessed": False,
        "network_requests": 0,
        "input_sha256": pins,
        "artifact_sha256": artifacts,
        "limits": [
            "Purposive cases overlap across scenarios and are not independent fires",
            "Grid-day sample is not an event sample or reviewed accuracy estimate",
            "Hash rank is a reproducible pseudorandom design; fixed seed, no seed search",
            "Unequal stratum sampling fractions; pooled unweighted rates are invalid",
            "Two units per stratum is a workflow pilot, not an error-rate power calculation",
            "Nominal granule-day lookup does not prove exact (T,T+24h] observation",
            "Thermal class and no selected thermal center are not binary ground truth",
            "Human evidence fields are blank; independent reference work remains",
        ],
    }
    (out / "readback.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Label review result:", out.relative_to(ROOT).as_posix(), flush=True)
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-stratum", type=int, default=2)
    args = parser.parse_args()
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    run(args.per_stratum)
