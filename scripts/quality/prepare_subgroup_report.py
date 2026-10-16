"""Offline unlabelled pilot denominators and a separate synthetic error-report rehearsal."""

import json
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require, training_day
from wildfire_risk_prediction.subgroup_report import METRICS, PROVINCES, grouped_report

ROOT = Path(__file__).resolve().parents[2]
PARENT = Path("outputs/reports/dataset/imbalance_calibration_plan_v1/20261016T130102Z_b916804c")
PARENT_SHA = "9fe78387323202ff09ff68a06215f1bc3540da434c74c053b6669df096e0a4f6"
UNITS = Path(
    "outputs/reports/dataset/observation_protocol_evidence_v1/20261015T143126Z_dc01eb0c/unit_protocol_evidence.csv"
)


def synthetic_fixture():
    return pd.DataFrame(
        {
            "grid_id": [f"synthetic_{i}" for i in range(8)],
            "prediction_timestamp_utc": ["2021-07-01T00:00:00Z"] * 4
            + ["2021-01-01T00:00:00Z"] * 2
            + ["2021-04-01T00:00:00Z", "2021-10-01T00:00:00Z"],
            "primary_province": ["Mersin"] * 4 + ["Antalya"] * 2 + [PROVINCES[2], PROVINCES[1]],
            "calendar_season": ["summer"] * 4 + ["winter"] * 2 + ["spring", "autumn"],
            "nominal_land_fraction": [1.0, 0, 1.0, np.nan, 0, 1, 1, 1],
            "target": [0, 0, 1, 1, np.nan, 1, 0, 0],
            "probability": [0.1, 0.4, 0.35, 0.8, 0.9, 0.7, np.nan, 0.2],
            "daily_observation_status": "unknown",
            "negative_label_permitted": False,
            "labels_created": False,
            "accepted_label_rule": False,
        }
    )


def run():
    def deny(*args, **kwargs):
        raise RuntimeError("Offline subgroup reporting preparation")

    socket.socket.connect = deny
    socket.create_connection = deny
    pins = {}

    def retained(name, expected=None):
        path = ROOT / name
        require(
            path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(ROOT),
            "Contained subgroup report input",
        )
        sha = digest(path)
        require(expected is None or expected == sha, "Subgroup input unchanged")
        pins[path.relative_to(ROOT).as_posix()] = sha
        return path

    def read(name, expected=None):
        return json.loads(retained(name, expected).read_text(encoding="utf-8"))

    parent = read(PARENT / "readback.json", PARENT_SHA)
    require(
        read(PARENT / "completion_readback.json")["report_sha256"] == PARENT_SHA, "Parent closure"
    )
    for name, sha in parent["artifact_sha256"].items():
        retained(PARENT / name, sha)
    for name, sha in read(PARENT / "input_manifest.json").items():
        retained(name, sha)
    require(
        parent["training_authorized"] is False
        and parent["calendar_feasibility_verified"] is False
        and parent["data_role_direction"] == "fit_2018_2022_calibration_2023_selection_2024",
        "Retained user direction without training or calendar admission",
    )
    spec = read("configs/error_analysis_v1.json")
    require(
        spec["real_scoring_implemented"] is False
        and spec["minimum_group_units"] is None
        and spec["minimum_independent_events"] is None
        and spec["confidence_interval_method"] is None
        and spec["labels_accepted"] is False,
        "Reporting rehearsal only; no invented support or confidence policy",
    )
    for name in (
        Path(__file__).relative_to(ROOT),
        "src/wildfire_risk_prediction/subgroup_report.py",
        "tests/test_subgroup_report.py",
    ):
        retained(name)
    require(UNITS.as_posix() in pins, "Pilot table already bound by previous evidence")
    units = pd.read_csv(retained(UNITS, pins[UNITS.as_posix()]))
    require(
        len(units) == 156 and units.grid_id.nunique() == 117 and units.target_day.nunique() == 12,
        "Same purpose-chosen 156-unit pilot",
    )
    # Original target_day is an issue date, not a first-detection timestamp.
    units["prediction_timestamp_utc"] = units.target_day.map(
        lambda day: training_day(day).strftime("%Y-%m-%dT00:00:00Z")
    )
    real = grouped_report(units, scope="unlabelled_method_pilot")
    synthetic = grouped_report(synthetic_fixture(), scope="synthetic_scores")
    total = real.loc[real.dimension.eq("all")].iloc[0]
    require(
        total.unknown_target_count == 156
        and total.known_target_count == 0
        and real[list(METRICS)].isna().all().all(),
        "Real unknown targets remain unscored",
    )
    toy_all = synthetic.loc[synthetic.dimension.eq("all")].iloc[0]
    require(
        toy_all.paired_known_prediction_count == 6 and toy_all[list(METRICS)].isna().all(),
        "No silent complete-case scoring of six out of eight toy units",
    )
    toy_mersin = synthetic.loc[
        synthetic.dimension.eq("primary_province") & synthetic.stratum.eq("Mersin")
    ].iloc[0]
    require(abs(toy_mersin.average_precision - 5 / 6) < 1e-12, "Hand-computable synthetic AP")
    out = (
        ROOT
        / "outputs/reports/dataset/subgroup_report_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True)

    def save(name, value):
        (out / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )

    real.to_csv(out / "real_pilot_denominators.csv", index=False)
    synthetic.to_csv(out / "synthetic_error_report.csv", index=False)
    save(
        "reconciliation.json",
        {
            "real_units": 156,
            "real_grids": 117,
            "real_issue_dates": 12,
            "real_unknown_targets": 156,
            "real_metrics_computed": 0,
            "real_nominal_support_zero_units": int(total.nominal_support_zero_count),
            "real_nominal_support_positive_units": int(total.nominal_support_positive_count),
            "real_nominal_support_missing_units": int(total.nominal_support_missing_count),
            "real_nominal_support_above_one_within_tolerance_units": int(
                total.nominal_support_above_one_within_tolerance_count
            ),
            "synthetic_units": 8,
            "synthetic_all_group_metrics_withheld": True,
            "synthetic_complete_group_AP": float(toy_mersin.average_precision),
            "group_rows_each_report": len(real),
            "marginal_dimensions": 5,
            "independent_event_counts_available": False,
            "confidence_intervals_computed": False,
        },
    )
    require(
        all(digest(ROOT / name) == sha for name, sha in pins.items()),
        "Final subgroup input closure",
    )
    save("input_manifest.json", pins)
    save(
        "readback.json",
        {
            "status": "real_denominators_and_synthetic_error_schema_only",
            "input_file_count": len(pins),
            "real_units": 156,
            "group_rows_each_report": len(real),
            "real_model_scores_computed": 0,
            "classifiers_fitted": 0,
            "calibrators_fitted": 0,
            "network_bytes": 0,
            "cloud_jobs_started": 0,
            "labels_accepted": False,
            "model_ready": False,
            "training_authorized": False,
            "final_merge_performed": False,
            "validation_or_final_data_accessed": False,
            "artifact_sha256": {p.name: digest(p) for p in out.iterdir() if p.is_file()},
        },
    )
    save(
        "completion_readback.json",
        {
            "status": "passed_reporting_preparation_only",
            "report_sha256": digest(out / "readback.json"),
        },
    )
    print(out.relative_to(ROOT).as_posix(), flush=True)


if __name__ == "__main__":
    run()
