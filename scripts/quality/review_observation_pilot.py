"""Offline 400-unit observation evidence review and six human-facing examples."""

import hashlib
import io
import json
import socket
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import matplotlib
import pandas as pd

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.label_review import REVIEW_FIELDS, STRATA
from wildfire_risk_prediction.observation_review import (
    audit_sample,
    boundary_scan_review,
    select_human_examples,
)

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PACKET = "outputs/reports/dataset/label_review_v1/20261014T153649Z_ca3fb92e"
MONTH = "outputs/gcp_delivery/2026-10-14/compact/products/month/2022-01/payload.zip"
OBS_MONTH = (
    "outputs/reports/dataset/observation_materialization_v1/"
    "20261014T145638Z_c0881064/2022-01/readback.json"
)
PROTECTED = (
    "outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/"
    "protected_inputs_readback_20261013.json"
)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def deny(*args, **kwargs):
    raise RuntimeError("Offline observation evidence review")


def run():
    pins = {}

    def retained(name, expected=None):
        path = ROOT / name
        require(path.is_file() and not path.is_symlink(), "Regular observation source")
        digest = sha(path)
        require(expected is None or digest == expected, "Observation input hash changed")
        pins[name] = digest
        return path

    master = json.loads(
        retained(
            PACKET + "/readback.json",
            "36ce8565a452efbf2a4f1e69fe3254ae33ccdd818eb08584f57b41a9eaf28037",
        ).read_text()
    )
    sources = {n: retained(PACKET + "/" + n, h) for n, h in master["artifact_sha256"].items()}
    sample = pd.read_csv(sources["random_grid_days.csv"], float_precision="round_trip")
    forms = pd.read_csv(sources["review_decisions_template.csv"])
    require(
        len(sample) == 400
        and len(forms) == 453
        and forms.review_status.eq("not_reviewed").all()
        and forms[REVIEW_FIELDS].isna().all().all(),
        "Unreviewed pilot and human forms",
    )
    audited = audit_sample(sample)
    examples = select_human_examples(audited)
    boundary = examples.loc[examples.example_id.eq("E_midnight_boundary")].iloc[0]
    require(
        boundary.grid_id == "E6933_5K_V1_C522_R918"
        and boundary.obs_nominal_granule_day == "2022-01-18",
        "Fixed midnight witness",
    )
    month_report = json.loads(retained(OBS_MONTH, master["input_sha256"][OBS_MONTH]).read_text())
    with zipfile.ZipFile(retained(MONTH, month_report["input_payload_sha256"][MONTH])) as monthly:
        with zipfile.ZipFile(io.BytesIO(monthly.read("2022-01-18.zip"))) as daily:
            report = json.loads(daily.read("report.json"))
            require(
                report["day"] == "2022-01-18"
                and not report["negative_label_permitted"]
                and report["daily_observation_status"] == "unknown",
                "Closed daily source",
            )
            data = daily.read("scan_grid.csv")
            require(
                hashlib.sha256(data).hexdigest() == report["outputs_sha256"]["scan_grid.csv"],
                "Boundary scan table hash",
            )
            scans = pd.read_csv(io.BytesIO(data), dtype={"pair_key": str})
    scans = boundary_scan_review(scans.loc[scans.grid_id.eq(boundary.grid_id)], "2022-01-18")
    require(
        scans.day_window_status.eq("boundary_unknown").sum()
        == boundary.obs_boundary_unknown_scan_count,
        "Selected pilot boundary counter agrees with source scans",
    )
    for name in (
        "src/wildfire_risk_prediction/observation_review.py",
        "scripts/quality/review_observation_pilot.py",
        PROTECTED,
    ):
        retained(name)
    for n, h in json.loads((ROOT / PROTECTED).read_text()).items():
        retained(n, h)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    out = ROOT / "outputs/reports/dataset/observation_review_v1" / stamp
    out.mkdir(parents=True, exist_ok=False)
    present = audited.obs_product_present
    no_thermal = audited.signal_stratum.eq("product_present_no_selected_thermal_center")
    sensitivity = pd.DataFrame(
        [
            {
                "illustrative_land_fraction_cut_not_accepted": cut,
                "nominal_no_thermal_rows_meeting_cut": int(
                    (no_thermal & audited.obs_nominal_nonfire_land_fraction_estimate.ge(cut)).sum()
                ),
                "also_nonexclusive_land_cloud_union_rows": int(
                    (
                        no_thermal
                        & audited.obs_nominal_nonfire_land_fraction_estimate.ge(cut)
                        & audited.land_cloud_union_overlap_diagnostic
                    ).sum()
                ),
                "negative_labels_admitted": 0,
            }
            for cut in (0.5, 0.8, 0.9, 0.95)
        ]
    )
    strata = (
        audited.groupby(STRATA, sort=True)
        .agg(
            sample_n=("review_unit_id", "size"),
            population_n=("population_n", "first"),
            missing_source_n=("obs_product_present", lambda s: int((~s).sum())),
            nonexclusive_area_n=("land_cloud_union_overlap_diagnostic", "sum"),
            no_land_center_n=("no_nominal_land_center", "sum"),
        )
        .reset_index()
    )
    artifacts = {}
    for name, frame in (
        ("pilot_observation_audit.csv", audited),
        ("human_examples.csv", examples),
        ("nominal_boundary_scan_rows.csv", scans),
        ("stratum_diagnostics.csv", strata),
        ("illustrative_area_cut_sensitivity.csv", sensitivity),
    ):
        path = out / name
        frame.to_csv(path, index=False, mode="x")
        strings = {
            c: str
            for c in frame
            if not frame[c].dropna().empty
            and frame[c].dropna().map(lambda v: isinstance(v, str)).all()
        }
        reread = pd.read_csv(path, dtype=strings, float_precision="round_trip")
        expected = (
            frame.reset_index(drop=True)
            .astype(object)
            .where(frame.reset_index(drop=True).notna(), None)
        )
        actual = reread.astype(object).where(reread.notna(), None)
        pd.testing.assert_frame_equal(expected, actual, check_exact=True)
        artifacts[name] = sha(path)
    fig, axes = plt.subplots(6, 2, figsize=(12, 13))
    fig.subplots_adjust(left=0.12, right=0.98, bottom=0.05, top=0.9, hspace=1.15, wspace=0.45)
    for (left, right), row in zip(axes, examples.itertuples(), strict=True):
        left.set_title(row.example_id + "; " + row.obs_nominal_granule_day, fontsize=9)
        left.set_xlim(0, 1.02)
        if row.obs_product_present:
            left.barh(
                ["Cloud union", "Land union"],
                [row.obs_cloud_fraction_estimate, row.obs_nominal_nonfire_land_fraction_estimate],
                color=["#999999", "#266786"],
            )
            right.barh(
                ["Selected envelope gap"],
                [row.nominal_land_longest_envelope_gap_hours],
                color="#c67c22",
            )
            right.set_title(
                f"Land scans {row.obs_nominal_land_center_scan_count:g}; thermal centers "
                f"{row.obs_nominal_confidence_fire + row.obs_high_confidence_fire:g}; boundary "
                f"{row.obs_boundary_unknown_scan_count:g}",
                fontsize=9,
            )
        else:
            left.text(0.1, 0.5, "SOURCE ABSENT; values missing", transform=left.transAxes)
            right.text(0.1, 0.5, "No measured gap value", transform=right.transAxes)
        left.set_xlabel("Separate area fractions; not a partition", fontsize=8)
        right.set_xlim(0, 24.5)
        right.set_xlabel("Longest gap between selected center envelopes (hours)", fontsize=8)
    fig.suptitle(
        "Six purpose-selected examples for human review\n"
        "Area unions and center envelopes do not establish reliable negative labels",
        fontsize=12,
    )
    fig.savefig(out / "human_observation_examples.png", dpi=140)
    plt.close(fig)
    near = scans.sort_values("start_utc").tail(2)
    endpoint = pd.Timestamp("2022-01-19T00:00:00Z")
    fig, ax = plt.subplots(figsize=(9, 3.6))
    for n, row in enumerate(near.itertuples()):
        a, b = [
            (pd.Timestamp(v).value - endpoint.value) / 1e9 for v in (row.start_utc, row.end_utc)
        ]
        ax.plot(
            [a, b],
            [n, n],
            linewidth=9,
            color="#c67c22" if row.day_window_status == "boundary_unknown" else "#266786",
        )
    ax.set_yticks(range(len(near)), [f"SNPP scan {i}" for i in near.scan_index])
    ax.axvline(0, color="black", linestyle="--")
    ax.set(
        xlabel="Seconds relative to 19 Jan 2022 00:00:00 UTC",
        title="A scan crosses the target-window endpoint\n"
        "One thermal center in the crossing scan; exact pixel time unresolved",
    )
    fig.tight_layout()
    fig.savefig(out / "midnight_boundary_example.png", dpi=150)
    plt.close(fig)
    for n in ("human_observation_examples.png", "midnight_boundary_example.png"):
        artifacts[n] = sha(out / n)
    result = {
        "status": "observation_pilot_evidence_readback_passed",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "input_sha256": pins,
        "artifact_sha256": artifacts,
        "sample_units": len(audited),
        "nonempty_strata": len(strata),
        "signal_counts": audited.signal_stratum.value_counts().to_dict(),
        "source_present": int(present.sum()),
        "source_absent": int((~present).sum()),
        "land_cloud_union_nonexclusive": int(audited.land_cloud_union_overlap_diagnostic.sum()),
        "no_thermal_land_cloud_union_nonexclusive": int(
            (no_thermal & audited.land_cloud_union_overlap_diagnostic).sum()
        ),
        "no_land_centers_with_product": int(audited.no_nominal_land_center.sum()),
        "no_selected_center_with_product": int(audited.no_selected_center.sum()),
        "boundary_scan_units": int(audited.boundary_scan_present.sum()),
        "land_center_longest_gap_hours_unweighted_pilot": audited.loc[
            present, "nominal_land_longest_envelope_gap_hours"
        ]
        .quantile([0, 0.5, 1])
        .rename(index={0: "min", 0.5: "median", 1: "max"})
        .to_dict(),
        "human_examples": len(examples),
        "human_review_completed": False,
        "population_error_rate_estimated": False,
        "cut_selected": None,
        "labels_created": False,
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "model_ready": False,
        "validation_accessed": False,
        "final_test_accessed": False,
        "network_requests": 0,
        "limits": [
            "Unequal-stratum 400-unit pilot; unweighted summaries are not population rates",
            "No thermal center does not imply no fire; thermal class does not confirm a wildfire",
            "Area cuts are illustrations, not accepted observation thresholds",
            "One raw scan witness does not resolve all nominal-day boundary alignment",
            "Human cards explain limits; independent outcome verification is still required",
        ],
    }
    require(all(sha(ROOT / n) == h for n, h in pins.items()), "Observation input closure")
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text()) == result, "Observation report readback")
    require(all(sha(out / n) == h for n, h in artifacts.items()), "Observation artifact closure")
    (out / "completion_readback.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "report_sha256": sha(path),
                "input_files_verified": len(pins),
                "artifacts_verified": len(artifacts),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("Observation pilot result:", out.relative_to(ROOT).as_posix())
    return out


if __name__ == "__main__":
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    run()
