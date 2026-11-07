"""Compare broader FIRMS Type records with the stable pilot scan summaries."""

import csv
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from review_pu_candidate_timeline import CASE, sha

from wildfire_risk_prediction.event_review import GEOD
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
BASE = "outputs/reports/dataset"
BATCH = f"{BASE}/pu_stable_batch_v1/20261107T225006Z_5a7bc291/readback.json"
AUDIT = {
    "SNPP": (
        "data/interim/firms_pilot_candidate_audit.csv",
        "f83773d20264940560710feb8a29cbca42f43265a536ecca25f627bb402fa4da",
    ),
    "N20": (
        "data/interim/firms_noaa20_pilot_candidate_audit.csv",
        "44871212a16f4ce323d1274263703f140062ffafba4ce06cd51a06840578c3bd",
    ),
}


def main():
    pins = {}

    def retain(name, expected):
        path = ROOT / name
        require(sha(path) == expected, f"Source changed: {name}")
        pins[name] = expected
        return path

    batch = json.loads(
        retain(
            BATCH, "52c18d0d64eb6d054d93628f5fae9dfa6c2ef26b6588a6452adcc4f907b94235"
        ).read_text()
    )
    pilot = json.loads(
        retain(CASE, "5b7fd0cc69efe03ff73dac67e65d58878add917f0a133917fe204715d07824ce").read_text()
    )
    cases = {row["review_unit_id"]: row for row in pilot["review_cases"]}
    target_days = {
        (window["grid_id"], window["prediction_timestamp_utc"][:10])
        for case in batch["cases"]
        for window in case["observation_windows"]
    }
    target_grids = {grid for grid, _ in target_days}
    retained, keys = defaultdict(list), set()
    for sensor, (name, expected) in AUDIT.items():
        with retain(name, expected).open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                raw_time = row["detection_timestamp_utc"]
                if not 2018 <= int(raw_time[:4]) <= 2023:
                    continue
                if row["grid_id"] not in target_grids:
                    continue
                utc = datetime.fromisoformat(raw_time)
                require(utc.utcoffset() == timedelta(0), "UTC source rows")
                day = (utc - timedelta(microseconds=1)).date().isoformat()
                key = row["grid_id"], day
                if key not in target_days:
                    continue
                record = sensor, row["source_record_number"]
                require(record not in keys, "Unique source row")
                keys.add(record)
                retained[key].append(
                    {
                        "sensor": sensor,
                        "record_number": row["source_record_number"],
                        "utc": utc.isoformat(),
                        "type": row["type"],
                        "confidence": row["confidence"],
                        "reason": row["candidate_selection_reason"],
                        "longitude": float(row["longitude"]),
                        "latitude": float(row["latitude"]),
                    }
                )
    results = []
    for case in batch["cases"]:
        parent = cases[case["review_unit_id"]]
        windows = []
        for window in case["observation_windows"]:
            key = window["grid_id"], window["prediction_timestamp_utc"][:10]
            records = retained[key]
            counts = Counter(row["type"] for row in records if row["confidence"] in ("n", "h"))
            windows.append(
                {
                    "utc_day": key[1],
                    "day_offset": window["day_offset"],
                    "firms_nominal_high_type_counts": dict(counts),
                    "firms_other_confidence_count": len(records) - sum(counts.values()),
                    "compact_thermal_center_count": window["loaded_thermal_center_definite_count"],
                }
            )
        result = {"codes": case["codes"], "windows": windows}
        if case["codes"] == ["R05"]:
            first = parent["first_times_utc"][0]
            grid = parent["grid_id"]
            anchor = [
                row
                for row in retained[grid, parent["prediction_utc"][:10]]
                if row["utc"] == first and row["type"] == "0"
            ]
            require(len(anchor) == 1, "R05 anchor")
            anchor = anchor[0]
            first_time = datetime.fromisoformat(first)
            earlier = [
                row
                for (cell, _), records in retained.items()
                if cell == grid
                for row in records
                if row["type"] == "2"
                and row["confidence"] in ("n", "h")
                and first_time - timedelta(hours=72)
                <= datetime.fromisoformat(row["utc"])
                < first_time
            ]
            for row in earlier:
                _, _, distance = GEOD.inv(
                    anchor["longitude"], anchor["latitude"], row["longitude"], row["latitude"]
                )
                row["distance_to_r05_m"] = distance
            result["earlier_nominal_high_type2_same_cell_72h"] = sorted(
                earlier, key=lambda row: (row["distance_to_r05_m"], row["utc"])
            )
        results.append(result)
    name = Path(__file__).relative_to(ROOT).as_posix()
    retain(name, sha(ROOT / name))
    require(all(sha(ROOT / name) == digest for name, digest in pins.items()), "Source changed")
    record = {
        "status": "firms_type_and_compact_scan_count_context",
        "source_sha256": pins,
        "cases": results,
        "counts_are_not_pixel_identity_matches": True,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
        "final_merge_performed": False,
    }
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    path = ROOT / BASE / "pu_filter_context_v1" / stamp / "readback.json"
    path.parent.mkdir(parents=True, exist_ok=False)
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text(encoding="utf-8")) == record, "JSON readback")
    print(path.relative_to(ROOT).as_posix(), sha(path))


if __name__ == "__main__":
    main()
