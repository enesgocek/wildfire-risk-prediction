"""Audit an autumn fire-table transcription as candidate source context."""

import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime, time
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

import pandas as pd

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.reference_intake import FIELDS, audit_intake
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset/autumn_reference_audit_v1"
PROJECTION = BASE / "table_projection.json"
PROJECTION_SHA256 = "ccc0810bef22dbbf37f84ba027a8c7a8a9be02c77691381bba4bb93745d39de6"
SOURCE_ID = "turnali_2020_autumn_tables"
PROVINCES = {"ANTALYA": "Antalya", "MUĞLA": "Muğla", "İZMİR": "İzmir", "MERSİN": "Mersin"}
EXPECTED = {
    "2.3": (2018, 11, 1, 24, 78, 35),
    "2.4": (2019, 10, 10, 31, 174, 63),
}


def read_selected_rows(projection):
    require([table["table"] for table in projection["tables"]] == list(EXPECTED), "Table order")
    normalized = []
    for table in projection["tables"]:
        name = table["table"]
        year, month, first_day, last_day, source_count, selected_count = EXPECTED[name]
        rows = table["selected_rows"]
        require(
            table["year"] == year
            and table["source_row_count"] == source_count
            and len(rows) == selected_count,
            f"Reviewed table size: {name}",
        )
        serials = [row["row"] for row in rows]
        require(
            serials == sorted(set(serials)) and all(1 <= n <= source_count for n in serials),
            f"Table row identity: {name}",
        )
        for row in rows:
            day = datetime.strptime(row["date_text"], "%d.%m.%Y").date()
            require(
                (day.year, day.month) == (year, month) and first_day <= day.day <= last_day,
                f"Publication date scope: {name}",
            )
            clock_match = re.match(r"^(\d{1,2})\s*[.:]\s*(\d{2})(?!\d)", row["clock_text"])
            require(clock_match is not None, f"Published clock field: {name}")
            clock = time(*(int(value) for value in clock_match.groups()))
            require(
                row["secondary_text_checked"] is ("alternate_view" not in row),
                f"Second-view review state: {name}",
            )
            normalized.append(
                {
                    **row,
                    "table": name,
                    "province": PROVINCES[row["reported_location"]],
                    "date": day.isoformat(),
                    "clock": clock.strftime("%H:%M"),
                }
            )
    return normalized


def review_intake(rows):
    consistent = [row for row in rows if row["secondary_text_checked"]]
    records = [
        {
            "reference_id": f"turnali_table_{row['table']}_row_{row['row']}",
            "source_id": SOURCE_ID,
            "reported_date": row["date"],
            "reported_clock_local": row["clock"],
            "reported_province": row["province"],
            "location_kind": "province_only",
            "record_origin": "secondary_transcription_of_ogm_publications",
        }
        for row in consistent
    ]
    source = {
        "source_id": SOURCE_ID,
        "lineage_status": "secondary_publication_of_ogm_table",
        "access_status": "public_text_views_only",
    }
    frame = pd.DataFrame(records, columns=FIELDS)
    results = audit_intake(frame, {SOURCE_ID: source}, {})
    status = Counter(row["row_status"] for row in results)
    require(status == {"needs_source_review": len(consistent)}, "Expected closed intake review")
    require(
        all(not row["can_review_matching"] and row["target"] is None for row in results),
        "Context references do not enter matching",
    )
    return dict(status), dict(Counter(code for row in results for code in row["reason_codes"]))


def summarize(rows):
    timestamps = defaultdict(list)
    local_zone = ZoneInfo("Europe/Istanbul")
    possible_day_shifts = []
    for row in rows:
        if not row["secondary_text_checked"]:
            continue
        key = (row["table"], row["province"], row["date"], row["clock"])
        timestamps[key].append(row["row"])
        local = datetime.fromisoformat(f"{row['date']}T{row['clock']}").replace(tzinfo=local_zone)
        if local.astimezone(UTC).date() != local.date():
            possible_day_shifts.append({"table": row["table"], "table_row": row["row"]})
    shared_clocks = [
        {"table": table, "province": province, "date": day, "clock": clock, "rows": serials}
        for (table, province, day, clock), serials in timestamps.items()
        if len(serials) > 1
    ]
    return shared_clocks, possible_day_shifts


def main():
    raw = PROJECTION.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == PROJECTION_SHA256, "Text projection identity")
    projection = json.loads(raw)
    rows = read_selected_rows(projection)
    intake_counts, intake_issues = review_intake(rows)
    shared_clocks, possible_day_shifts = summarize(rows)
    report = {
        "scope": "autumn_publication_rows_without_original_incident_geometry",
        "source_url": projection["source_url"],
        "secondary_source_url": projection["secondary_source_url"],
        "projection_sha256": PROJECTION_SHA256,
        "producer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "table_counts": {
            name: dict(Counter(row["province"] for row in rows if row["table"] == name))
            for name in EXPECTED
        },
        "selected_publication_rows": len(rows),
        "text_view_conflicts": [row for row in rows if not row["secondary_text_checked"]],
        "same_province_date_clock_groups": shared_clocks,
        "rows_with_earlier_utc_calendar_day_if_local_clock": possible_day_shifts,
        "intake_status_counts": intake_counts,
        "intake_reason_counts": intake_issues,
        "target_admission": specification(),
    }
    out = BASE / f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}_{uuid4().hex[:8]}" / "readback.json"
    out.parent.mkdir()
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    require(json.loads(out.read_bytes()) == report, "Output roundtrip")
    print(out.relative_to(ROOT).as_posix(), hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
