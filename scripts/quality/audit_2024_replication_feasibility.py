"""Direct saved-source and weather-table count checks; no source labels or predictions."""

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.weather_policy import MODEL_FEATURES

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
RUN = BASE / "2024_replication_feasibility_v1/20261125T001419Z_2e1802f8"


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main():
    report = json.loads((RUN / "readback.json").read_bytes())
    launcher = json.loads((RUN / "launcher_receipt.json").read_bytes())
    require(
        launcher["status"] == "completed" and launcher["returncode"] == 0,
        "Completed bounded review",
    )
    require(digest(RUN / "readback.json") == launcher["readback_sha256"], "Parent report closure")
    require(digest(RUN / "child.log") == launcher["closed_child_log_sha256"], "Closed log identity")
    require(report["elapsed_seconds"] < 900, "Bounded execution")
    for name, expected in report["input_sha256"].items():
        require(digest(ROOT / name) == expected, "Unchanged source and daily weather inputs")
    for name, expected in report["artifact_sha256"].items():
        require(digest(RUN / name) == expected, "Review artifact identity")
    points = read_rows(RUN / "qualified_catalog_2024.csv")
    by_id = {r["detection_id"]: r for r in points}
    require(len(by_id) == len(points), "Unique saved detection inventory")
    source = ROOT / "data/interim/firms_combined_candidates_2018_2024.csv"
    expected_ids, count = set(), Counter()
    with source.open("rb") as handle:
        fields = handle.readline().decode("utf-8-sig").strip().split(",")
        ti = fields.index("detection_timestamp_utc")
        for raw in handle:
            parts = raw.rstrip(b"\r\n").split(b",")
            if parts[ti][:4] != b"2024":
                continue
            row = dict(zip(fields, (x.decode("utf-8") for x in parts), strict=True))
            # All selected source rows passed the scope rule in this exact file.
            require(row["type"] == "0" and row["confidence"] in {"n", "h"}, "Original quality rule")
            saved = by_id[row["detection_id"]]
            for name in ("grid_id", "source_sensor", "type", "confidence"):
                require(saved[name] == row[name], "Preserved source fields")
            require(
                saved["source_timestamp_text_preserved"] == row["detection_timestamp_utc"],
                "Original timestamp text",
            )
            require(
                float(saved["longitude"]) == float(row["longitude"])
                and float(saved["latitude"]) == float(row["latitude"]),
                "Preserved allowed-year coordinates",
            )
            require(
                not saved["target"]
                and not saved["accepted_L_membership"]
                and saved["negative_label_permitted"] == "False"
                and saved["daily_observation_status"] == "unknown",
                "No accepted labels",
            )
            expected_ids.add(row["detection_id"])
            count[(row["detection_timestamp_utc"][:10], row["source_sensor"])] += 1
    require(
        expected_ids == set(by_id) and len(expected_ids) == report["scope_catalog_rows"],
        "Independent source record inventory",
    )
    for row in read_rows(RUN / "catalog_days_2024.csv"):
        require(
            int(row["catalog_rows"])
            == int(row["scope_rows"])
            == count[(row["day"], row["sensor"])],
            "Saved daily catalog counts including zero",
        )
    weather = read_rows(RUN / "weather_readiness_2024.csv")
    require(
        len(weather) == 366 and len({r["day"] for r in weather}) == 366,
        "Leap-year weather inventory",
    )
    catalog_by_day = defaultdict(list)
    for row in points:
        catalog_by_day[row["conditional_prediction_timestamp_utc"][:10]].append(row)
    saved_support = {r["detection_id"]: r for r in read_rows(RUN / "catalog_weather_support.csv")}
    totals = Counter()
    for summary in weather:
        day = summary["day"]
        require(
            day.startswith("2024-") and summary["policy_readback_pass"] == "True",
            "Reviewed 2024 days only",
        )
        primary, complete, rows = 0, 0, 0
        wanted = {r["grid_id"] for r in catalog_by_day[day]}
        point_support = {}
        path = ROOT / "data/interim/meteorology/model_v1/daily" / (day + ".csv")
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                require(row["prediction_timestamp_utc"][:10] == day, "Saved weather day metadata")
                require(row["weather_primary_eligible"] in {"True", "False"}, "Boolean QA text")
                eligible = row["weather_primary_eligible"] == "True"
                primary += eligible
                complete += all(
                    row[f] != "" and math.isfinite(float(row[f])) for f in MODEL_FEATURES
                )
                rows += 1
                if row["grid_id"] in wanted:
                    point_support[row["grid_id"]] = eligible
        require(
            [rows, primary, complete]
            == [int(summary[k]) for k in ("rows", "primary_eligible", "weather_complete")],
            "Direct CSV quality/completeness count",
        )
        totals.update(
            {
                "weather_rows": rows,
                "weather_primary_eligible_rows": primary,
                "weather_11_complete_rows": complete,
            }
        )
        for row in catalog_by_day[day]:
            saved = saved_support[row["detection_id"]]
            require(
                (saved["weather_primary_eligible"] == "True") == point_support[row["grid_id"]],
                "Detection/day weather support readback",
            )
    require(all(totals[k] == report[k] for k in totals), "Year totals reconcile")
    require(
        len(saved_support) == report["catalog_rows_with_weather_day_file"],
        "Saved catalog support inventory",
    )
    require(
        sum(r["weather_primary_eligible"] == "True" for r in saved_support.values())
        == report["weather_primary_supported_catalog_rows"],
        "Catalog primary support count",
    )
    out = (
        BASE
        / "2024_replication_feasibility_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    result = {
        "status": "source_weather_readiness_counts_and_hashes_audited_not_fire_validation",
        "analysis_date": "2026-11-25",
        "review_receipt_sha256": digest(RUN / "readback.json"),
        "catalog_rows": len(points),
        "weather_days": len(weather),
        "weather_totals": dict(totals),
        "catalog_weather_support_rows": len(saved_support),
        "other_year_source_fields_decoded": False,
        "new_S_or_Y_or_L": False,
        "new_predictions_or_training": False,
        "final_merge": False,
        "auditor_sha256": digest(Path(__file__)),
    }
    (out / "readback.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix())
    print(json.dumps(result))


if __name__ == "__main__":
    main()
