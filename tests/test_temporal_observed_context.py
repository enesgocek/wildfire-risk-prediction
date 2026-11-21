import importlib.util
from datetime import UTC, datetime, timedelta
from pathlib import Path


def test_target_window_is_right_closed_and_prior_context_never_means_absence():
    path = (
        Path(__file__).resolve().parents[1] / "scripts/quality/audit_temporal_observed_context.py"
    )
    spec = importlib.util.spec_from_file_location("temporal_observed_context_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    t = datetime(2022, 5, 15, tzinfo=UTC)
    times = [
        t - timedelta(days=7),
        t,
        t + timedelta(hours=1),
        t + timedelta(days=1),
        t + timedelta(days=1, seconds=1),
    ]
    assert module.windows(times, ["outside", "past", "A", "B", "outside"], t) == (1, 2, {"A", "B"})
    assert module.windows([], [], t) == (0, 0, set())
