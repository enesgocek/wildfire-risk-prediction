"""Additional Salur-motivated checks of the unchanged chronological lineage core."""

import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction.event_lineage import trace_lineage, verify_ancestry_records
from wildfire_risk_prediction.event_review import GEOD


def source(records):
    return pd.DataFrame(
        [
            {
                "detection_id": key,
                "grid_id": grid,
                "source_sensor": "SNPP",
                "detection_timestamp_utc": stamp,
                "latitude": 37.0,
                "longitude": lon,
                "type": 0,
                "confidence": "n",
            }
            for key, grid, stamp, lon in records
        ]
    )


def test_older_disconnected_record_merges_later_without_erasing_local_birth():
    frame = source(
        [
            ("older", "G2", "2019-01-01T22:59:00+00:00", 31.02),
            ("anchor", "G1", "2019-01-01T23:00:00+00:00", 31.0),
            ("bridge", "G3", "2019-01-02T23:00:00+00:00", 31.01),
        ]
    )
    before = trace_lineage(frame.iloc[:2], distance_m=1000, gap_hours=48)
    after = trace_lineage(frame, distance_m=1000, gap_hours=48)
    pd.testing.assert_frame_equal(before[0], after[0])
    local = after[0].loc[after[0].earliest_grid_ids_json.eq('["G1"]')].iloc[0]
    assert local.first_detection_utc == "2019-01-01T23:00:00+00:00"
    assert len(after[0]) == 2 and after[4]["final_graph_components"] == 1
    cols = [c for c in before[3] if c != "final_graph_membership_sha256"]
    pd.testing.assert_frame_equal(
        before[3][cols],
        after[3].loc[after[3].detection_id.ne("bridge"), cols].reset_index(drop=True),
    )
    assert verify_ancestry_records(after[0], after[2], after[3])["ancestry_dag_verified"]


def test_exact_gap_and_one_nanosecond_later_give_different_hypotheses():
    frame = source(
        [
            ("a", "G1", "2019-01-01T12:00:00+00:00", 31.0),
            ("b", "G1", "2019-01-02T12:00:00+00:00", 31.0),
        ]
    )
    assert len(trace_lineage(frame, distance_m=500, gap_hours=24)[0]) == 1
    frame.loc[1, "detection_timestamp_utc"] = "2019-01-02T12:00:00.000000001+00:00"
    result = trace_lineage(frame, distance_m=500, gap_hours=24)
    assert len(result[0]) == 2 and result[4]["physical_events_accepted"] == 0
    assert not result[3].event_membership_complete.any()


@pytest.mark.parametrize("distance", [500, 1000, 2000])
@pytest.mark.parametrize("gap", [24, 48, 72])
def test_independent_partition_and_unchanged_prefix_history(distance, gap):
    rng = np.random.default_rng(140)
    hours = rng.integers(0, 110, size=18)
    frame = source(
        [
            (
                f"D{i}",
                f"G{i % 3}",
                (pd.Timestamp("2021-06-01", tz="UTC") + pd.Timedelta(int(h), unit="h")).isoformat(),
                float(lon),
            )
            for i, (h, lon) in enumerate(zip(hours, 31 + rng.uniform(0, 0.05, 18), strict=True))
        ]
    )
    full = trace_lineage(frame, distance_m=distance, gap_hours=gap)
    for cutoff in (24, 72, 110):
        stamp = pd.Timestamp("2021-06-01", tz="UTC") + pd.Timedelta(cutoff, unit="h")
        part = frame.loc[hours <= cutoff].reset_index(drop=True)
        result = trace_lineage(part, distance_m=distance, gap_hours=gap)
        neighbours = {i: set() for i in range(len(part))}
        for i in range(len(part)):
            for j in range(i):
                a, b = part.iloc[i], part.iloc[j]
                delta = abs(
                    pd.Timestamp(a.detection_timestamp_utc).value
                    - pd.Timestamp(b.detection_timestamp_utc).value
                )
                metres = GEOD.inv(a.longitude, a.latitude, b.longitude, b.latitude)[2]
                if delta <= gap * 3_600_000_000_000 and metres <= distance:
                    neighbours[i].add(j)
                    neighbours[j].add(i)
        unseen, hashes = set(neighbours), set()
        while unseen:
            todo = [unseen.pop()]
            visited = set(todo)
            while todo:
                for j in neighbours[todo.pop()] - visited:
                    visited.add(j)
                    unseen.discard(j)
                    todo.append(j)
            ids = sorted(part.iloc[list(visited)].detection_id)
            hashes.add(hashlib.sha256("\n".join(ids).encode()).hexdigest())
        assert set(result[3].final_graph_membership_sha256) == hashes
        for index, time_col in (
            (0, "first_detection_utc"),
            (1, "recorded_at_utc"),
            (2, "recorded_at_utc"),
            (3, "timestamp_utc"),
        ):
            expected = full[index]
            expected = expected.loc[pd.to_datetime(expected[time_col], utc=True).le(stamp)]
            cols = [c for c in expected if c != "final_graph_membership_sha256"]
            pd.testing.assert_frame_equal(
                result[index][cols], expected[cols].reset_index(drop=True)
            )
        assert verify_ancestry_records(result[0], result[2], result[3])["ancestry_dag_verified"]
        assert result[0].target.isna().all() and result[3].target.isna().all()
        assert all(isinstance(json.loads(x), list) for x in result[0].earliest_grid_ids_json)
