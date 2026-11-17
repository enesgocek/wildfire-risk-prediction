"""Inventory cached native pairs for the fixed Mersin clock sample, offline."""

import hashlib
import json
from datetime import UTC, datetime
from uuid import uuid4

from audit_mersin_open_incidents import ARCHIVE, GRID, PINS, PROVINCES
from audit_mersin_scan_times import ROOT, incident_windows, selected_windows
from audit_stage_one_selection import OBS, read_report, verify

from wildfire_risk_prediction.core_transfer import check_file, digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.observation_window import source_schedule


def main():
    for path in (ARCHIVE, GRID, PROVINCES):
        verify(path, PINS[path])
    plan_path = ROOT / (
        "outputs/reports/dataset/observation_pilot_queue_v2/"
        "20261015T114055Z_a141e892/queue_plan.json"
    )
    require(plan_path.is_file(), "Existing fixed pilot plan")
    require(
        digest(plan_path) == "af4a8e1d7c6e8929cbb2a998864acb1ad7814f1bbd4a74a6cb4fd09acfc1112b",
        "Fixed pilot plan hash",
    )
    plan = json.loads(plan_path.read_bytes())
    master = read_report(OBS / "accepted_readback.json")
    windows = selected_windows(incident_windows())
    days = set()
    for day in windows.prediction_timestamp_utc.str[:10].unique():
        schedule = source_schedule(day, set(master["missing_source_days"]))
        days.update(schedule.source_nominal_day)
    cache = ROOT / "data/raw/observation_pilot_v1"
    cached = {}
    for path in cache.rglob("*.nc"):
        cached.setdefault(path.name, []).append(path)
    pairs = []
    for pair in plan["pairs"]:
        if pair["source_day"] not in days:
            continue
        sources = []
        for source in pair["sources"]:
            paths = cached.get(source["filename"], [])
            for path in paths:
                check_file(path, source)
                sources.append(
                    {
                        "path": path.relative_to(ROOT).as_posix(),
                        "sha256": source["sha256"],
                        "role": source["role"],
                    }
                )
        if sources:
            pairs.append(
                {
                    "sample_id": pair["sample_id"],
                    "source_day": pair["source_day"],
                    "complete_pair": {s["role"] for s in sources}
                    == {s["role"] for s in pair["sources"]},
                    "sources": sources,
                }
            )
    result = {
        "scope": "date_overlap_only_point_coverage_pending",
        "archive_rows": int(windows.archive_row.nunique()),
        "nominal_days": len(days),
        "cache_nc_files": sum(map(len, cached.values())),
        "complete_cached_pairs": sum(p["complete_pair"] for p in pairs),
        "source_plan_sha256": digest(plan_path),
        "pairs": pairs,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
    }
    out = (
        ROOT
        / "outputs/reports/dataset/mersin_local_sources_v1"
        / (f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}_{uuid4().hex[:8]}")
    )
    out.mkdir(parents=True, exist_ok=False)
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_bytes()) == result, "Receipt roundtrip")
    print(json.dumps({k: v for k, v in result.items() if k != "pairs"}, indent=2))
    print(path.relative_to(ROOT), hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
