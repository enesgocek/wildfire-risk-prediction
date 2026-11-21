import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def audit():
    path = (
        Path(__file__).resolve().parents[1] / "scripts/quality/verify_source_calendar_features.py"
    )
    spec = importlib.util.spec_from_file_location("calendar_X_audit_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def toy(audit):
    frame = pd.DataFrame(
        {
            "grid_id": ["A"] * 3,
            "prediction_timestamp_utc": [f"2022-05-{d:02d}T00:00:00+00:00" for d in (1, 2, 3)],
        }
    )
    metadata = frame.copy()
    metadata["known_proposal_key_in_union"] = [True, True, False]
    metadata["review_temporal_role"] = "proposed_assessment_2022"
    metadata["target"] = np.nan
    metadata["accepted_L_membership"] = np.nan
    metadata["daily_observation_status"] = "unknown"
    metadata["role_is_model_training_permission"] = False
    for field in audit.join.feature_names():
        frame[field] = 0.2
    frame["temperature_mean_c"] = [1.0, 2.0, np.nan]
    return frame, metadata


def test_context_pairs_include_other_candidate_days_without_creating_opposite_labels(audit):
    features, metadata = toy(audit)
    result = audit.temporal_support(features, metadata).iloc[0]
    assert result.anchor_other_date_context_pairs == 4
    assert result.weather_complete_anchor_other_date_context_pairs == 2
    assert result.distinct_weather_vectors_including_missing == 3
    assert not result.pairs_are_verified_opposite_fire_labels
    assert metadata.target.isna().all() and metadata.accepted_L_membership.isna().all()


def test_static_fields_cannot_silently_vary_over_calendar_dates(audit):
    features, metadata = toy(audit)
    features.loc[2, "elevation_mean_m"] = 999.0
    with pytest.raises(ValueError, match="Static fields constant"):
        audit.temporal_support(features, metadata)


@pytest.mark.parametrize(
    "field", ["target", "accepted_L_membership", "role_is_model_training_permission"]
)
def test_metadata_cannot_promote_calendar_preparation_to_labels_or_training(audit, field):
    _, metadata = toy(audit)
    metadata.loc[0, field] = True if field == "role_is_model_training_permission" else 0
    with pytest.raises(ValueError):
        audit.check_metadata(metadata)
