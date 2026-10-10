"""Graph chaining, source boundaries and open-left target windows stay explicit."""

import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction.event_review import (
    GEOD,
    review_partition,
    spatial_links,
    training_detections,
)


def detections(times, offsets=None, grids=None):
    if offsets is None:
        offsets = [0] * len(times)
    if grids is None:
        grids = ["g"] * len(times)
    rows = []
    for i, (time, metres, grid) in enumerate(zip(times, offsets, grids, strict=True)):
        lon, lat, _ = GEOD.fwd(30, 37, 90, metres)
        rows.append(
            {
                "detection_id": f"id_{i}",
                "grid_id": grid,
                "source_sensor": "SNPP" if i % 2 else "N20",
                "detection_timestamp_utc": time,
                "latitude": lat,
                "longitude": lon,
                "type": "0",
                "confidence": "n",
            }
        )
    return pd.DataFrame(rows)


def assignments(frame, clusters):
    result = frame[["detection_id", "grid_id", "source_sensor", "timestamp"]].copy()
    result["cluster_id"] = clusters
    return result


def test_rebuilds_chained_cluster_without_calling_it_one_confirmed_fire():
    frame = training_detections(
        detections(
            ["2020-01-01T10:00Z", "2020-01-02T06:00Z", "2020-01-03T02:00Z"],
            offsets=[0, 400, 800],
            grids=["a", "b", "c"],
        )
    )
    catalog, summary = review_partition(
        frame, assignments(frame, ["cluster"] * 3), spatial_links(frame, 500), 500, 24
    )
    assert summary["cluster_count"] == 1 and summary["pair_connection_count"] == 2
    assert summary["temporal_chain_review_clusters"] == 1
    assert summary["spatial_chain_review_clusters"] == 1
    assert catalog.earliest_grid_ids_json.iloc[0] == '["a"]'
    assert catalog.grid_count.iloc[0] == 3
    assert catalog.event_status.iloc[0] == "exploratory_cluster_only"
    assert not catalog.negative_label_permitted.any()


@pytest.mark.parametrize(
    "time,expected",
    [
        ("2020-02-02T00:00:00Z", "2020-02-01T00:00:00+00:00"),
        ("2020-02-02T00:00:01Z", "2020-02-02T00:00:00+00:00"),
        ("2020-02-02T23:59:59Z", "2020-02-02T00:00:00+00:00"),
    ],
)
def test_registered_open_left_closed_right_target_window(time, expected):
    frame = training_detections(detections([time]))
    catalog, _ = review_partition(
        frame, assignments(frame, ["c"]), spatial_links(frame, 500), 500, 24
    )
    assert catalog.candidate_prediction_timestamp_utc.iloc[0] == expected


def test_simultaneous_cross_sensor_first_detections_preserve_ambiguous_grids():
    frame = training_detections(detections(["2020-06-01T10:00Z"] * 2, grids=["a", "b"]))
    catalog, summary = review_partition(
        frame, assignments(frame, ["c", "c"]), spatial_links(frame, 500), 500, 24
    )
    assert catalog.sensor_count.iloc[0] == 2 and catalog.detection_count.iloc[0] == 2
    assert catalog.earliest_grid_ids_json.iloc[0] == '["a", "b"]'
    assert summary["multi_grid_first_detection_clusters"] == 1


@pytest.mark.parametrize("clusters", [["a", "b", "c"], ["a", "a", "a"]])
def test_partition_rejects_both_false_split_and_false_merge(clusters):
    frame = training_detections(detections(["2020-06-01T10:00Z"] * 3, offsets=[0, 100, 3000]))
    with pytest.raises(ValueError, match="partition"):
        review_partition(frame, assignments(frame, clusters), spatial_links(frame, 500), 500, 24)


def test_inclusive_gap_and_one_second_outside_gap():
    frame = training_detections(
        detections(["2020-06-01T10:00Z", "2020-06-02T10:00Z", "2020-06-03T10:00:01Z"])
    )
    _, summary = review_partition(
        frame, assignments(frame, ["a", "a", "b"]), spatial_links(frame, 500), 500, 24
    )
    assert summary["cluster_count"] == 2


def test_year_crossing_and_missing_period_context_remain_review_flags():
    frame = training_detections(
        detections(
            ["2018-01-01T00:00Z", "2019-12-31T23:00Z", "2020-01-01T01:00Z", "2023-12-31T23:00Z"]
        )
    )
    catalog, summary = review_partition(
        frame, assignments(frame, ["a", "b", "b", "c"]), spatial_links(frame, 500), 500, 24
    )
    assert summary["calendar_year_crossing_clusters"] == 1
    assert summary["period_context_missing_clusters"] == 2
    assert catalog.candidate_prediction_timestamp_utc.iloc[0] == "2017-12-31T00:00:00+00:00"


@pytest.mark.parametrize(
    "column,value",
    [
        ("detection_timestamp_utc", "2024-01-01T00:00Z"),
        ("detection_timestamp_utc", "2025-01-01T00:00Z"),
        ("longitude", np.nan),
        ("latitude", 85),
        ("type", "2"),
        ("confidence", "l"),
    ],
)
def test_holdout_invalid_geometry_and_changed_candidate_selection_rejected(column, value):
    frame = detections(["2020-06-01T10:00Z"])
    frame[column] = value
    with pytest.raises(ValueError):
        training_detections(frame)


def test_source_identity_and_time_mismatches_rejected():
    frame = training_detections(detections(["2020-06-01T10:00Z"] * 2))
    links = spatial_links(frame, 500)
    for column, value in [
        ("detection_id", "other"),
        ("grid_id", "other"),
        ("timestamp", "2020-07-01T10:00Z"),
    ]:
        saved = assignments(frame, ["c", "c"])
        saved[column] = saved[column].astype(str)
        saved.loc[0, column] = value
        with pytest.raises(ValueError):
            review_partition(frame, saved, links, 500, 24)


def test_shuffle_does_not_change_readback_or_membership_digest():
    frame = training_detections(detections(["2020-06-01T10:00Z"] * 2, offsets=[0, 50]))
    saved = assignments(frame, ["c", "c"])
    links = spatial_links(frame, 500)
    first, a = review_partition(frame, saved, links, 500, 24)
    second, b = review_partition(frame.iloc[::-1], saved.iloc[::-1], links, 500, 24)
    pd.testing.assert_frame_equal(first, second)
    assert a == b


def test_spatial_cache_cannot_be_reused_with_changed_coordinates_or_scenario():
    frame = training_detections(detections(["2020-06-01T10:00Z"] * 2, offsets=[0, 50]))
    saved = assignments(frame, ["c", "c"])
    links = spatial_links(frame, 500)
    changed = frame.copy()
    changed.loc[0, "longitude"] += 0.1
    for candidate, distance in [(changed, 500), (frame, 1000)]:
        with pytest.raises(ValueError, match="Spatial link"):
            review_partition(candidate, saved, links, distance, 24)


def test_pilot_envelope_search_keeps_true_links_and_rejects_far_points():
    frame = detections(["2020-06-01T10:00Z"] * 3)
    for i, metres in enumerate([0, 499, 1001]):
        lon, lat, _ = GEOD.fwd(39.5, 44.9, 90, metres)
        frame.loc[i, ["longitude", "latitude"]] = [lon, lat]
    frame = training_detections(frame)
    _, summary = review_partition(
        frame, assignments(frame, ["a", "a", "b"]), spatial_links(frame, 500), 500, 24
    )
    assert summary["pair_connection_count"] == 1


def test_entrypoint_rejects_changed_source_before_csv_read(tmp_path, monkeypatch):
    import importlib.util
    import json
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "scripts/firms/review_event_grouping.py"
    spec = importlib.util.spec_from_file_location("event_review_script", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = tmp_path / "outputs/reports/event_grouping_sensitivity.json"
    report.parent.mkdir(parents=True)
    report.write_text(json.dumps({"source_sha256": "expected"}), encoding="utf-8")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "sha", lambda _: "changed")

    def forbidden(*args, **kwargs):
        raise AssertionError("CSV opened before source acceptance")

    monkeypatch.setattr(module.pd, "read_csv", forbidden)
    with pytest.raises(ValueError, match="source changed"):
        module.main()
