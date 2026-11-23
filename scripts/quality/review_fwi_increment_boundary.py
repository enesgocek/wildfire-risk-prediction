"""Correct the first review's increment-versus-field inference; preserve original receipts."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
PRIOR = BASE / "fwi_local_time_review_v1/20261123T001956Z_0458f2b3/readback.json"


def corrected_clock(clock):
    result = dict(clock)
    first = result.pop("first_step_hours")
    count = result.pop("number_of_steps")
    increment = result.pop("step_increment_hours")
    result.pop("forcing_timestamps_UTC")
    result.pop("forcing_last_UTC")
    base = datetime.fromisoformat(result["forcing_base_UTC"])
    start = base + timedelta(hours=first)
    result.update(
        {
            "forecast_time_hours_encoded": first,
            "number_of_time_increments_encoded": count,
            "time_increment_hours_encoded": increment,
            "forcing_interval_start_UTC": start.isoformat(),
            "conservative_increment_span_end_UTC_not_verified_last_used_field": (
                start + timedelta(hours=count * increment)
            ).isoformat(),
            "enumerated_actual_used_fields_verified": False,
            "strict_previous_day_before_midnight_cutoff_proven_by_this_header": False,
            "correction_reason": "increments_do_not_prove_N_fields_or_last_used_time_at_21UTC",
        }
    )
    return result


def main():
    require(
        digest(PRIOR) == "41b6fd67ef5455bf9af4706fea67a4b519c939dce922158994f7abef0ada4e01",
        "Preserved first review",
    )
    r = json.loads(PRIOR.read_bytes())
    for name, sha in r["input_sha256"].items():
        require(digest(ROOT / name) == sha, "Unchanged original source or definition")
    result = {
        "status": "increment_interpretation_corrected_original_value_comparison_retained",
        "clock": corrected_clock(r["clock"]),
        "one_day_format_comparison": r["one_day_format_comparison"],
        "previous_value_comparison_recomputed": False,
        "previous_last_used_time_inference_accepted": False,
        "method_or_operational_time_policy_accepted": False,
        "new_features_models_labels_or_final_merge": 0,
        "input_receipt_sha256": digest(PRIOR),
        "source_rule": "PDT_4.93_octet_46_number_of_time_increments_not_number_of_fields",
        "source_url": "https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_temp4-93.shtml",
        "producer_sha256": digest(Path(__file__)),
    }
    out = (
        BASE
        / "fwi_increment_interpretation_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    p = out / "readback.json"
    p.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)


if __name__ == "__main__":
    main()
