"""Find Mersin archive rows for identity review without merging records."""

import hashlib
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from audit_mersin_open_incidents import (
    ARCHIVE,
    BASE,
    GEOD,
    GRID,
    PINS,
    PROVINCES,
    ROOT,
    clock_diagnostics,
    read_incidents,
    spatial_diagnostics,
)

from wildfire_risk_prediction.feature_join import require

SCENARIOS = ((0, 5000), (60, 1000), (60, 5000), (1440, 5000), (1440, 10000))


def candidate_pairs(rows):
    """Generate each pair once, using the archive clock on a relative basis."""
    pairs = []
    for i, one in enumerate(rows):
        for j in range(i + 1, len(rows)):
            two = rows[j]
            minutes = two.source_minute - one.source_minute
            if minutes > 1440:
                break
            _, _, distance = GEOD.inv(
                float(one.longitude), float(one.latitude), float(two.longitude), float(two.latitude)
            )
            require(distance >= 0, "Invalid distance between public records")
            if distance <= 10000:
                pairs.append((i, j, minutes, distance))
    return pairs


def components(edges):
    neighbors = defaultdict(set)
    for i, j, _, _ in edges:
        neighbors[i].add(j)
        neighbors[j].add(i)
    unseen = set(neighbors)
    groups = []
    while unseen:
        stack = [min(unseen)]
        found = set()
        while stack:
            i = stack.pop()
            if i in unseen:
                unseen.remove(i)
                found.add(i)
                stack.extend(neighbors[i] & unseen)
        groups.append(found)
    return groups


def summarize(rows, pairs):
    scenarios = []
    for minute_limit, meter_limit in SCENARIOS:
        edges = [p for p in pairs if p[2] <= minute_limit and p[3] <= meter_limit]
        groups = components(edges)
        result = {
            "minute_limit_inclusive": minute_limit,
            "meter_limit_inclusive": meter_limit,
            "pairs": len(edges),
            "rows_in_groups": sum(map(len, groups)),
            "groups": len(groups),
            "group_size_counts": dict(sorted(Counter(map(len, groups)).items())),
            "cross_district_pairs": sum(
                rows[i].district != rows[j].district for i, j, _, _ in edges
            ),
        }
        if (minute_limit, meter_limit) == (60, 5000):
            result["groups_for_review"] = [
                {
                    "dates": sorted({rows[i].date.isoformat() for i in group}),
                    "districts": sorted({rows[i].district for i in group}),
                    "rows": len(group),
                    "distinct_grid_cells": len({rows[i].grid_cell for i in group}),
                    "source_clock_span_minutes": max(rows[i].source_minute for i in group)
                    - min(rows[i].source_minute for i in group),
                    "pairs": sum(i in group and j in group for i, j, _, _ in edges),
                }
                for group in groups
            ]
        scenarios.append(result)
    return scenarios


def main():
    pins = {}
    for path in (ARCHIVE, GRID, PROVINCES):
        with path.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        require(digest == PINS[path], f"Input checksum mismatch: {path.name}")
        pins[path.relative_to(ROOT).as_posix()] = digest
    events, _ = read_incidents()
    clock_diagnostics(events)
    cells, _ = spatial_diagnostics(events)
    eligible = events.loc[cells.index].dropna(subset=["ignition_hour"]).copy()
    eligible["grid_cell"] = cells
    eligible["source_minute"] = [
        day.toordinal() * 1440 + round(Decimal(hour) * 60)
        for day, hour in zip(eligible.date, eligible.ignition_hour, strict=True)
    ]
    rows = list(eligible.sort_values("source_minute", kind="stable").itertuples(index=False))
    result = {
        "status": "public_archive_proximity_review_only",
        "period": "2018–2023",
        "scope": "Mersin; publisher QC, one cell center, provisional source clock",
        "input_sha256": pins,
        "geography_rows": len(events),
        "rows_with_one_cell_center": len(cells),
        "eligible_rows": len(rows),
        "scenarios": summarize(rows, candidate_pairs(rows)),
        "records_merged_or_removed": 0,
        "target_labels_admitted": 0,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "model_training_permitted": False,
        "validation_or_holdout_used": False,
    }
    run = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    out = BASE / "mersin_incident_proximity_v1" / run / "readback.json"
    out.parent.mkdir(parents=True, exist_ok=False)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix())
    print(hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
