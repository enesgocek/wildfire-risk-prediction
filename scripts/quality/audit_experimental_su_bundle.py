"""Independent package, proposal, time, display-payload and ZIP verification; no browser claim."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

import numpy as np
import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
BUNDLE = BASE / "experimental_SU_inspection_v2/20261123T102954Z_6d6e52c1"
KEYS = ["grid_id", "prediction_timestamp_utc"]


def parse_source_times(values):
    return pd.to_datetime(values, utc=True, errors="coerce", format="ISO8601")


def main():
    receipt = BUNDLE / "readback.json"
    require(
        digest(receipt) == "86270dea5d9d12a1764ead780dcfa79166bed60a0977bf712e3df497d84bc366",
        "Original inspection receipt",
    )
    r = json.loads(receipt.read_bytes())
    require(
        all(digest(ROOT / name) == sha for name, sha in r["input_sha256"].items()),
        "Original input identity",
    )
    require(
        all(digest(BUNDLE / name) == sha for name, sha in r["artifact_sha256"].items()),
        "Current package artifacts",
    )
    require(
        digest(ROOT / "scripts/quality/build_experimental_su_bundle.py") == r["producer_sha256"],
        "Current producer",
    )
    x, q, m = [
        pd.read_csv(BUNDLE / name, float_precision="round_trip")
        for name in ("features.csv", "provenance.csv", "inspection_memberships.csv")
    ]
    pd.testing.assert_frame_equal(x[KEYS], m[KEYS], check_exact=True)
    pd.testing.assert_frame_equal(x[KEYS], q[KEYS], check_exact=True)
    require(len(x) == 44082 and not x.duplicated(KEYS).any(), "All unique review keys")
    require(
        m.target.isna().all()
        and m.accepted_L_membership.isna().all()
        and m.daily_observation_status.eq("unknown").all()
        and not m.negative_label_permitted.any()
        and not m.role_is_model_training_permission.any(),
        "No true labels, negatives or training promotion",
    )
    feature_names = x.columns[2:].tolist()
    require(
        len(feature_names) == 27 and x.columns.tolist() == KEYS + feature_names,
        "Original 27-field candidate schema",
    )
    missing = x[feature_names].isna().sum(axis=1)
    np.testing.assert_array_equal(missing, m.missing_feature_count)
    require(
        int((missing > 0).sum()) == 2724 and int((missing == 0).sum()) == 41358,
        "No missingness removal or fill",
    )
    dates = pd.to_datetime(x.prediction_timestamp_utc, utc=True)
    require(dates.dt.year.between(2018, 2022).all(), "No later-year scientific rows")
    require(
        (m.review_temporal_role.eq("proposed_fit_2018_2021") == dates.dt.year.le(2021)).all(),
        "Unchanged pilot role/year relation",
    )
    time_checks = {}
    for name, strict in [
        ("weather_source_last_timestamp_utc", True),
        ("weather_source_window_end_exclusive_utc", False),
        ("vegetation_30d_snapshot_cutoff_utc", False),
        ("vegetation_30d_source_acquisition_latest_utc", True),
        ("vegetation_60d_snapshot_cutoff_utc", False),
        ("vegetation_60d_source_acquisition_latest_utc", True),
    ]:
        stamps = parse_source_times(q[name])
        present = q[name].notna()
        require(stamps[present].notna().all(), "No malformed recorded source time")
        valid = stamps[present] < dates[present] if strict else stamps[present] <= dates[present]
        require(valid.all(), "No recorded source time beyond its policy cutoff")
        time_checks[name] = {
            "present": int(present.sum()),
            "missing_preserved": int((~present).sum()),
            "violations": int((~valid).sum()),
        }
    lineage = pd.read_csv(BUNDLE / "original_candidate_lineage.csv")
    proposal = lineage.loc[lineage.possible_L_proposal.eq(True)]
    scenarios = sorted(proposal.scenario.unique())
    require(len(scenarios) == 9, "All scenario proposals preserved")
    expected_masks = np.zeros(len(m), dtype=int)
    keys = list(map(tuple, m[KEYS].to_numpy()))
    for bit, scenario in enumerate(scenarios):
        selected = set(map(tuple, proposal.loc[proposal.scenario.eq(scenario), KEYS].to_numpy()))
        expected = np.array([key in selected for key in keys])
        np.testing.assert_array_equal(m["S_candidate_context_" + scenario], expected)
        expected_masks += expected * (2**bit)
    np.testing.assert_array_equal(expected_masks, m.scenario_proposal_bitmask_for_display_only)
    require(int((expected_masks > 0).sum()) == 1670, "Exact union without new memberships")
    forbidden = ("E6933_5K_V1_C642_R876", "2022-05-27T00:00:00+00:00")
    require(
        forbidden not in set(map(tuple, proposal[KEYS].to_numpy())),
        "WF1538 remains outside S proposals",
    )
    text = (BUNDLE / "review_data.js").read_text(encoding="utf-8")
    require(
        text.startswith("window.REVIEW=") and text.endswith(";\n"),
        "Static JSON data assignment only",
    )
    payload = json.loads(text.removeprefix("window.REVIEW=").removesuffix(";\n"))
    require(
        payload["scenarios"] == scenarios and len(payload["rows"]) == 44082,
        "Display key count and all settings",
    )
    display_keys = [(row[0], row[1]) for row in payload["rows"]]
    require(
        display_keys == keys and all(len(row) == 33 for row in payload["rows"]),
        "Display key/value alignment",
    )
    displayed = np.asarray(
        [[np.nan if value is None else value for value in row[6:]] for row in payload["rows"]]
    )
    np.testing.assert_allclose(
        displayed, x[feature_names].to_numpy(), rtol=0, atol=1e-12, equal_nan=True
    )
    np.testing.assert_array_equal([row[4] for row in payload["rows"]], missing)
    np.testing.assert_array_equal([row[5] for row in payload["rows"]], expected_masks)
    filters = {
        "all_rows": len(m),
        "2022_all": int(dates.dt.year.eq(2022).sum()),
        "2022_any_proposal": int((dates.dt.year.eq(2022) & (expected_masks > 0)).sum()),
        "all_years_Mersin": int(
            m.province_area_intersections.str.split("|").map(lambda xs: "Mersin" in xs).sum()
        ),
        "2022_Mersin": int(
            (
                dates.dt.year.eq(2022)
                & m.province_area_intersections.str.split("|").map(lambda xs: "Mersin" in xs)
            ).sum()
        ),
    }
    archive = BUNDLE / "deneysel_SU_inceleme.zip"
    require(
        digest(archive) == "13a90a265c3b17906b9ac8bb16e7210b4190368678a3698091a719bfd20bf7a4",
        "Frozen portable ZIP",
    )
    with ZipFile(archive) as z:
        require(
            z.testzip() is None
            and set(z.namelist()) == set(r["artifact_sha256"]) | {"readback.json"},
            "Complete ZIP CRC and member inventory",
        )
        for name in z.namelist():
            require(
                z.read(name) == (BUNDLE / name).read_bytes(),
                "Every zipped member matches local artifact",
            )
    out = (
        BASE
        / "experimental_SU_inspection_audit_v2"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    result = {
        "status": "experimental_package_data_and_archive_verified_browser_user_check_pending",
        "bundle_receipt_sha256": digest(receipt),
        "archive_sha256": digest(archive),
        "keys": len(m),
        "features": 27,
        "scenario_membership_flags_rechecked": len(m) * 9,
        "time_metadata_checks": time_checks,
        "expected_UI_filter_counts_not_browser_observations": filters,
        "UI_automatically_observed_working": False,
        "UI_blocker": "browser_tool_rejected_file_protocol_security_policy_no_workaround_attempted",
        "true_Y_or_accepted_L_created": 0,
        "new_training_or_final_merge": False,
        "producer_sha256": digest(Path(__file__)),
    }
    p = out / "readback.json"
    p.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)
    print(json.dumps(filters), flush=True)


if __name__ == "__main__":
    main()
