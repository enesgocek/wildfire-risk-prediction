"""Offline inventory and runtime options; never create cloud resources or raw downloads."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "outputs/reports/observation_coverage"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plan():
    proof_path = REPORTS / "gcp_benchmark_received_verification.json"
    proof = json.loads(proof_path.read_text())
    assert proof["status"] == "independent_gcp_two_arm_readback_passed"
    assert proof["cross_arm_exact_comparison"]["area_tables_exactly_equal"] is True
    assert proof["cross_arm_exact_comparison"]["geometry_coordinates_exactly_equal"] is True
    assert proof["negative_label_permitted"] is False
    pair_path = REPORTS / "l2_training_catalogue_pairs.csv"
    granule_path = REPORTS / "l2_training_catalogue_granules.csv"
    pairs = pd.read_csv(pair_path, dtype={"pair_key": str})
    granules = pd.read_csv(granule_path, dtype={"pair_key": str})
    assert pairs.day.between("2018-01-01", "2023-12-31").all()
    assert not pairs.duplicated(["sensor", "pair_key"]).any()
    assert pairs.negative_label_permitted.eq(False).all()
    months = sorted(pairs.day.str[:7].unique())
    assert len(months) == 72
    completed = json.loads((REPORTS / "colab_month_received_verification.json").read_text())
    assert completed["complete_month"] is True and completed["completed_days"] == 31
    pending_months = [m for m in months if m != "2023-07"]
    assert len(pending_months) == 71
    seconds_per_pair = proof["summary"]["arms"][1]["cold_pair_wall_seconds"] / 6
    pending_pairs = pairs[
        pairs.pair_status.eq("nominal_unique_pair") & ~pairs.day.str.startswith("2023-07")
    ]
    pair_phase_hours = len(pending_pairs) * seconds_per_pair / 3600
    throughput = {
        "remaining_nominal_pairs": len(pending_pairs),
        "measured_pairs": 6,
        "measured_workers": 2,
        "pair_phase_hours_extrapolated": pair_phase_hours,
        "calendar_days_pair_phase_only": {
            str(hours): pair_phase_hours / hours for hours in (8, 12, 24)
        },
        "hypothetical_extra_time_multiplier": 1.5,
        "calendar_days_with_hypothetical_50_percent_extra_time": {
            str(hours): pair_phase_hours * 1.5 / hours for hours in (8, 12, 24)
        },
        "not_measured": [
            "daily_geometry_union",
            "production_Drive_publish",
            "retries_and_idle_time",
        ],
        "not_included": ["implementation_time", "2024_validation", "remaining_features_and_model"],
        "six_pair_extrapolation_is_not_a_completion_guarantee": True,
        "four_worker_speed_not_measured": True,
    }
    drive_report_path = REPORTS / "gcp_drive_returned_proof_v2.json"
    drive_checked = False
    if drive_report_path.exists():
        drive_report = json.loads(drive_report_path.read_text())
        assert drive_report["status"] == "returned_drive_proof_summary_validated"
        assert drive_report["negative_label_permitted"] is False
        drive_checked = drive_report["vm_reported_off_vm_persistence_passed"] is True
    choices = []
    for begin, end in [("2023-08-01", "2023-08-04"), ("2023-08-01", "2023-09-01")]:
        chosen = pairs[(pairs.day >= begin) & (pairs.day < end)]
        assert chosen.pair_status.eq("nominal_unique_pair").all()
        rows = granules[
            (granules.start_utc.str[:10] >= begin) & (granules.start_utc.str[:10] < end)
        ]
        assert len(rows) == 2 * len(chosen)
        assert not rows.duplicated(["sensor", "pair_key", "role"]).any()
        assert (rows.groupby(["sensor", "pair_key"]).role.agg(set) == {"fire", "geolocation"}).all()
        choices.append(
            {
                "start": begin,
                "end_exclusive": end,
                "pairs": len(chosen),
                "catalogue_estimated_source_bytes": int(
                    rows.catalogue_size_bytes_estimate.round().sum()
                ),
                "naive_pair_phase_seconds_at_two_worker_sample_rate": len(chosen)
                * seconds_per_pair,
                "naive_rate_is_not_a_runtime_or_cost_guarantee": True,
            }
        )
    report = {
        "prepared_at_utc": datetime.now(UTC).isoformat(),
        "status": "offline_design_not_production_ready",
        "sha256": {
            str(p.relative_to(ROOT)).replace("\\", "/"): digest(p)
            for p in [proof_path, pair_path, granule_path]
        },
        "completed_production_months": ["2023-07"],
        "remaining_training_months": pending_months,
        "unpaired_catalogue_records_retained": int(
            (pairs.pair_status != "nominal_unique_pair").sum()
        ),
        "first_persistence_gate": "existing_verified_pair_no_raw_downloads",
        "suggested_first_new_raw_trial": choices[0],
        "following_month_option": choices[1],
        "runtime_options_hours": [2, 6, 8],
        "runtime_option_applied": None,
        "first_trial_keeps_two_hour_vm_cap": True,
        "time_planning_scenarios": throughput,
        "Drive_VM_persistence_report_locally_validated": drive_checked,
        "storage_backend": "google_drive_prior_user_preference",
        "missing_before_production": [
            "independent_remote_payload_readback",
            "VM_restart_resume_and_SSH_disconnect_trial",
            "production_science_worker_and_daily_spatial_union",
            "bounded_retry_upload_and_credit_status_review",
        ],
        "raw_local_downloads": 0,
        "cloud_resources_created": False,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
    }
    output = REPORTS / "gcp_production_readiness_plan.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "unpaired_retained": report["unpaired_catalogue_records_retained"],
                "trial": choices[0],
                "month": choices[1],
                "report": str(output),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    plan()
