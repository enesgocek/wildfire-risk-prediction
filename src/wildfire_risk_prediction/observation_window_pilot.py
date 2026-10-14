"""Preserve the fixed sampling design while appending window diagnostics."""

import numpy as np
import pandas as pd

from wildfire_risk_prediction.feature_join import require, utc_times
from wildfire_risk_prediction.label_review import KEYS, STRATA
from wildfire_risk_prediction.observation_review import audit_sample
from wildfire_risk_prediction.water_scope import attach_water_scope


def append_diagnostics(sample, summaries, scope):
    """One-to-one key match; never replace the frozen nominal-day observations."""
    audit_sample(sample)
    require(
        not summaries.duplicated(KEYS).any() and len(summaries) == len(sample),
        "One window result per sampled unit",
    )
    fields = [c for c in summaries if c not in KEYS]
    renamed = summaries.rename(columns={c: "window_" + c for c in fields})
    require(
        not set(renamed.columns).difference(KEYS).intersection(sample.columns),
        "Separate window diagnostic namespace",
    )
    require(
        "_window_join_time" not in sample and "_window_join_time" not in renamed,
        "Reserved timestamp join key",
    )
    left = sample.assign(_window_join_time=utc_times(sample.prediction_timestamp_utc))
    right = renamed.drop(columns="prediction_timestamp_utc").assign(
        _window_join_time=utc_times(summaries.prediction_timestamp_utc)
    )
    result = left.merge(
        right, on=["grid_id", "_window_join_time"], how="left", validate="one_to_one", sort=False
    ).drop(columns="_window_join_time")
    require(result.window_processing_version.notna().all(), "Every sampled key matched")
    pd.testing.assert_frame_equal(result[sample.columns], sample.reset_index(drop=True))
    require(
        result.target.isna().all()
        and result.window_target.isna().all()
        and result.window_daily_observation_status.eq("unknown").all()
        and not result.window_negative_label_permitted.any()
        and not result.window_positive_label_permitted.any(),
        "Closed pilot label gates",
    )
    result = attach_water_scope(result, scope)
    # Compare total centres from nominal packets to definite + boundary centres in loaded windows.
    # This is a diagnostic difference; missing-source rows stay missing.
    nominal = result.obs_nominal_confidence_fire + result.obs_high_confidence_fire
    loaded = (
        result.window_loaded_thermal_center_definite_count
        + result.window_loaded_thermal_center_boundary_count
    )
    result["loaded_window_vs_nominal_thermal_count_delta"] = (loaded - nominal).where(
        result.obs_product_present
    )
    result["window_incomplete_packet_set"] = ~result.window_all_three_nominal_packets_present
    result["window_boundary_scan_present"] = result.window_loaded_boundary_scan_rows.gt(0)
    result["window_boundary_thermal_present"] = (
        result.window_loaded_thermal_center_boundary_count.gt(0)
    )
    result["window_loaded_definite_thermal_present"] = (
        result.window_loaded_thermal_center_definite_count.gt(0)
    )
    return result


def stratum_impacts(frame):
    """Keep N/n per stratum; expanded counts are estimates, never label error rates."""
    flags = [
        "window_incomplete_packet_set",
        "window_boundary_scan_present",
        "window_boundary_thermal_present",
        "window_loaded_definite_thermal_present",
    ]
    rows = []
    for key, group in frame.groupby(STRATA, sort=True, dropna=False):
        n, population = len(group), int(group.population_n.iloc[0])
        require(
            group.sample_n.eq(n).all()
            and group.population_n.eq(population).all()
            and np.allclose(group.expansion_weight, population / n),
            "Unchanged pilot design",
        )
        row = {
            **dict(zip(STRATA, key, strict=True)),
            "sample_n": n,
            "population_n": population,
            "expansion_weight": population / n,
            "water_scope_excluded_sample_n": int((~group.water_scope_included).sum()),
        }
        for flag in flags:
            row[flag + "_sample_n"] = int(group[flag].sum())
            row[flag + "_expanded_count_estimate"] = float(
                (group[flag] * group.expansion_weight).sum()
            )
        rows.append(row)
    return pd.DataFrame(rows)
