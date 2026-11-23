import importlib.util
from pathlib import Path


def test_eight_increments_are_not_evidence_of_exactly_eight_used_fields():
    p = Path(__file__).resolve().parents[1] / "scripts/quality/review_fwi_increment_boundary.py"
    spec = importlib.util.spec_from_file_location("increment_boundary", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    original = {
        "forcing_base_UTC": "2022-06-01T00:00:00+00:00",
        "first_step_hours": 0,
        "number_of_steps": 8,
        "step_increment_hours": 3,
        "forcing_timestamps_UTC": [],
        "forcing_last_UTC": "2022-06-01T21:00:00+00:00",
    }
    corrected = mod.corrected_clock(original)
    assert corrected["number_of_time_increments_encoded"] == 8
    assert (
        corrected["conservative_increment_span_end_UTC_not_verified_last_used_field"]
        == "2022-06-02T00:00:00+00:00"
    )
    assert corrected["strict_previous_day_before_midnight_cutoff_proven_by_this_header"] is False
    assert "forcing_last_UTC" not in corrected
    assert original["forcing_last_UTC"] == "2022-06-01T21:00:00+00:00"
