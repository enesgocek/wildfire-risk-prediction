"""Training-only multi-sensor detection diagnostics; never infer negative labels.

snapshot explicitly downloads two public outage HTML tables. review is local.
Table overlaps are conservative diagnostic envelopes, not proof that a pilot
pixel was unobserved: rows can concern specific granules, bands or products.
"""

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import urlopen

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "outputs/reports/observation_coverage"
URLS = {
    "SNPP": "https://modaps.modaps.eosdis.nasa.gov/services/production/outages_suomi_npp.html",
    "N20": "https://modaps.modaps.eosdis.nasa.gov/services/production/outages_noaa_20.html",
}
START, END = "2018-01-01", "2024-01-01"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


class TableRows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.row, self.cell = [], None, None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        if tag in {"td", "th"} and self.row is not None:
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in {"td", "th"} and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        if tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def parse_outages(html, sensor):
    parser = TableRows()
    parser.feed(html)
    require(any(r[:1] == ["Year-Day"] for r in parser.rows), "Outage table header changed")
    intervals = []
    for row in parser.rows:
        if not row or not re.match(r"^\d{4}-\d{3}", row[0]):
            continue
        year = int(row[0][:4])
        if not 2018 <= year <= 2023:
            continue
        require(len(row) == 5, "Outage table schema changed")
        match = re.fullmatch(r"(\d{4}-\d{3})(?:\s*-\s*(\d{4}-\d{3}))?", row[0])
        require(match is not None, "Ambiguous outage date")
        first, last = match.group(1), match.group(2) or match.group(1)
        start = pd.Timestamp(datetime.strptime(first + " " + row[2], "%Y-%j %H:%M:%S"), tz="UTC")
        end = pd.Timestamp(datetime.strptime(last + " " + row[3], "%Y-%j %H:%M:%S"), tz="UTC")
        require(
            start < end
            and start >= pd.Timestamp(START, tz="UTC")
            and end <= pd.Timestamp(END, tz="UTC"),
            "Invalid training outage bounds",
        )
        require(
            start.strftime("%Y-%j") == first and end.strftime("%Y-%j") == last,
            "Invalid day-of-year",
        )
        intervals.append(
            {
                "sensor": sensor,
                "start_utc": start.isoformat(),
                "end_utc": end.isoformat(),
                "year_day": row[0],
                "calendar_text": row[1],
                "source_comment": row[4],
            }
        )
    require(bool(intervals), "No training outage rows found")
    return sorted(intervals, key=lambda x: x["start_utc"])


def snapshot():
    records = []
    for sensor, url in URLS.items():
        with urlopen(url, timeout=30) as response:
            content = response.read()
        intervals = parse_outages(content.decode("utf-8"), sensor)
        path = OUTPUT / "sources" / f"{sensor}.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        records.append(
            {
                "sensor": sensor,
                "url": url,
                "path": str(path.relative_to(ROOT)),
                "sha256": sha(path),
                "retrieved_at_utc": datetime.now(UTC).isoformat(),
                "training_intervals": len(intervals),
            }
        )
    write_json(OUTPUT / "sources/manifest.json", records)
    print("Official outage source snapshots saved", flush=True)


def overlap_seconds(day, intervals):
    """Union overlapping table envelopes within UTC [day, day+24h)."""
    stop = pd.Timestamp(day.value + 86_400_000_000_000, unit="ns", tz="UTC")
    pieces = sorted(
        (max(day, pd.Timestamp(i["start_utc"])), min(stop, pd.Timestamp(i["end_utc"])))
        for i in intervals
        if pd.Timestamp(i["start_utc"]) < stop and pd.Timestamp(i["end_utc"]) > day
    )
    merged = []
    for a, b in pieces:
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
        else:
            merged.append((a, b))
    return sum((b - a).total_seconds() for a, b in merged)


def daily_diagnostics(raw, pilot, candidates, sensor, intervals):
    days = pd.date_range(START, END, inclusive="left", tz="UTC")
    lower = pd.Timestamp("2018-04-01" if sensor == "N20" else START, tz="UTC")
    requested = days >= lower
    result = pd.DataFrame(
        {
            "date_utc": days.strftime("%Y-%m-%d"),
            "sensor": sensor,
            "within_archive_request": requested,
        }
    )
    for name, frame in [("turkey", raw), ("pilot", pilot), ("candidate", candidates)]:
        times = pd.to_datetime(frame.detection_timestamp_utc, utc=True)
        require(
            times.ge(lower).all() and times.lt(pd.Timestamp(END, tz="UTC")).all(),
            "Detection outside training/source range",
        )
        counts = times.dt.normalize().value_counts().reindex(days, fill_value=0)
        result[name + "_detection_count"] = pd.array(
            [int(c) if valid else pd.NA for c, valid in zip(counts, requested, strict=True)],
            dtype="Int64",
        )
    require(
        result.candidate_detection_count.le(result.pilot_detection_count).fillna(True).all()
        and result.pilot_detection_count.le(result.turkey_detection_count).fillna(True).all(),
        "Nested count mismatch",
    )
    result["zero_turkey_detections"] = requested & result.turkey_detection_count.eq(0).fillna(False)
    result["outage_table_overlap_seconds"] = [overlap_seconds(d, intervals) for d in days]
    result["outage_table_overlap"] = result.outage_table_overlap_seconds.gt(0)
    result["pixel_observation_status"] = "unknown"
    result["negative_label_permitted"] = False
    return result


def review():
    sources = json.loads((OUTPUT / "sources/manifest.json").read_text(encoding="utf-8"))
    require({s["sensor"] for s in sources} == set(URLS) and len(sources) == 2, "Snapshot inventory")
    intervals, provenance = [], []
    for record in sources:
        path = ROOT / record["path"]
        require(
            record["url"] == URLS[record["sensor"]] and sha(path) == record["sha256"],
            "Snapshot changed",
        )
        parsed = parse_outages(path.read_text(encoding="utf-8"), record["sensor"])
        require(len(parsed) == record["training_intervals"], "Snapshot row count drift")
        intervals.extend(parsed)
    combined_path = ROOT / "data/interim/firms_combined_candidates_2018_2024.csv"
    combined = pd.read_csv(combined_path, dtype="string")
    require(combined.detection_id.is_unique, "Duplicate detection ID")
    times = pd.to_datetime(combined.detection_timestamp_utc, utc=True)
    combined = combined.loc[times.ge(START) & times.lt(END)].copy()
    grid_ids = set(pd.read_csv(ROOT / "data/interim/meteorology/era5_land_grid_areas.csv").grid_id)
    require(combined.grid_id.isin(grid_ids).all(), "Unknown candidate grid")
    daily, summaries = [], []
    for sensor, request, raw_name, prefix in [
        ("SNPP", "815579", "fire_archive_SV-C2_815579.csv", "firms"),
        ("N20", "815590", "fire_archive_J1V-C2_815590.csv", "firms_noaa20"),
    ]:
        raw_path = ROOT / "data/raw/firms" / request / raw_name
        pilot_path = ROOT / f"data/interim/{prefix}_pilot_2018_2024.csv"
        prep = json.loads((ROOT / f"outputs/reports/{prefix}_pilot_preparation.json").read_text())
        require(sha(raw_path) == prep["source_sha256"], "Raw archive changed")
        hashes = {str(p.relative_to(ROOT)): sha(p) for p in [raw_path, pilot_path, combined_path]}
        raw = pd.read_csv(raw_path, dtype="string")
        raw["source_record_number"] = np.arange(1, len(raw) + 1).astype(str)
        raw["detection_timestamp_utc"] = pd.to_datetime(
            raw.acq_date + " " + raw.acq_time.str.zfill(4), format="%Y-%m-%d %H%M", utc=True
        ).astype("string")
        raw = raw.loc[pd.to_datetime(raw.detection_timestamp_utc, utc=True).lt(END)].copy()
        require(raw.satellite.eq(sensor).all(), "Archive sensor mismatch")
        pilot = pd.read_csv(pilot_path, dtype="string")
        pilot = pilot.loc[pd.to_datetime(pilot.detection_timestamp_utc, utc=True).lt(END)].copy()
        require(
            pilot.source_record_number.is_unique and pilot.grid_id.isin(grid_ids).all(),
            "Pilot keys",
        )
        matched = raw.set_index("source_record_number").loc[pilot.source_record_number]
        columns = [
            c for c in raw.columns if c not in {"source_record_number", "detection_timestamp_utc"}
        ]
        pd.testing.assert_frame_equal(
            pilot[columns].reset_index(drop=True), matched[columns].reset_index(drop=True)
        )
        require(
            pd.to_datetime(pilot.detection_timestamp_utc, utc=True)
            .reset_index(drop=True)
            .equals(
                pd.to_datetime(matched.detection_timestamp_utc, utc=True).reset_index(drop=True)
            ),
            "Pilot timestamp drift",
        )
        candidates = combined.loc[combined.source_sensor.eq(sensor)].copy()
        expected = pilot.loc[pilot.type.eq("0") & pilot.confidence.isin(["n", "h"])]
        require(
            set(candidates.source_record_number) == set(expected.source_record_number),
            "Candidate selection drift",
        )
        candidate_match = pilot.set_index("source_record_number").loc[
            candidates.source_record_number
        ]
        pd.testing.assert_frame_equal(
            candidates[pilot.columns].reset_index(drop=True),
            candidate_match.reset_index()[pilot.columns].reset_index(drop=True),
        )
        table = daily_diagnostics(
            raw, pilot, candidates, sensor, [i for i in intervals if i["sensor"] == sensor]
        )
        for name, frame in [("turkey", raw), ("pilot", pilot), ("candidate", candidates)]:
            require(int(table[name + "_detection_count"].sum()) == len(frame), "Daily count loss")
        require(all(sha(ROOT / k) == v for k, v in hashes.items()), "Input changed during review")
        provenance.append({"sensor": sensor, "input_sha256": hashes})
        zero = table.zero_turkey_detections
        summaries.append(
            {
                "sensor": sensor,
                "requested_days": int(table.within_archive_request.sum()),
                "days_outside_request": int((~table.within_archive_request).sum()),
                "training_turkey_detections": len(raw),
                "training_pilot_detections": len(pilot),
                "training_candidate_detections": len(candidates),
                "zero_turkey_days": int(zero.sum()),
                "zero_days_with_table_overlap": int((zero & table.outage_table_overlap).sum()),
                "zero_days_without_table_overlap": table.loc[
                    zero & ~table.outage_table_overlap, "date_utc"
                ].tolist(),
                "outage_table_overlap_days": int(table.outage_table_overlap.sum()),
                "requested_days_with_outage_table_overlap": int(
                    (table.within_archive_request & table.outage_table_overlap).sum()
                ),
            }
        )
        daily.append(table)
    all_daily = pd.concat(daily, ignore_index=True)
    daily_path = OUTPUT / "training_sensor_daily.csv"
    all_daily.to_csv(daily_path, index=False)
    pivot = all_daily.pivot(index="date_utc", columns="sensor", values="turkey_detection_count")
    both_zero = pivot.SNPP.eq(0) & pivot.N20.eq(0)
    report = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "status": "diagnostics_passed_coverage_unresolved",
        "start": START,
        "end_exclusive": END,
        "sensor_day_rows": len(all_daily),
        "day_definition": "UTC calendar [day,day+24h); not the target (T,T+24h] window",
        "sources": sources,
        "input_provenance": provenance,
        "sensors": summaries,
        "both_sensors_requested_and_zero_turkey_days": pivot.index[
            both_zero.fillna(False)
        ].tolist(),
        "daily_sha256": sha(daily_path),
        "script_sha256": sha(Path(__file__)),
        "grid_observation_coverage_verified": False,
        "negative_labels_created": False,
        "validation_used_for_rule_selection": False,
        "final_test_data_read": False,
        "limits": [
            "Hotspot CSVs have no non-fire/cloud/unobserved pixel denominator",
            "Outage tables are not exhaustive; some rows concern particular bands/products",
            "Another sensor's detections do not establish clear observations in every pilot cell",
            "No outage/count threshold is used as a negative-label rule",
        ],
        "next_requirement": (
            "Inspect historical VIIRS L2 fire mask + matching geolocation/QA on a training "
            "sample before defining cell-time observation coverage"
        ),
    }
    write_json(OUTPUT / "training_outage_intervals.json", intervals)
    write_json(OUTPUT / "training_review.json", report)
    print(
        json.dumps(
            {
                "sensors": summaries,
                "both_zero_days": report["both_sensors_requested_and_zero_turkey_days"],
            },
            indent=2,
        )
    )
    print(f"Report: {OUTPUT / 'training_review.json'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["snapshot", "review"])
    args = parser.parse_args()
    snapshot() if args.command == "snapshot" else review()
