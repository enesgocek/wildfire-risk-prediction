"""Check selected public fire accounts with the existing reference intake rules."""

import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

import pandas as pd

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.reference_intake import FIELDS, audit_intake

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
RECEIPTS = {
    "manavgat_reported_starts_v1/20261108T022757Z_358ef972": (
        "cf24f1c2839f3f92942de1d569644e599a84a854b76cb5263cd6e1871e3c7b9e"
    ),
    "open_reference_antalya_v1/20261108T022002Z_6b97aff6": (
        "1f45ce37875a869110a45dd134af3bfffdf76b40d9d1d845511fba0557054f57"
    ),
    "three_province_start_context_v1/20261108T024231Z_67d3f799": (
        "f0d86451068aa0ec86aa7f2967eb31fdeb713f9776404f7786c6ad493cb4da09"
    ),
    "manavgat_cluster_overlap_v1/20261108T023504Z_5c2435a8": (
        "e1365de5c839a772d23fc388d63f851cbf0251bc6eec4e484586226e0c10e2a1"
    ),
}


def case(case_id, source, province, district, stamp, precision, context):
    local = stamp.astimezone(ZoneInfo("Europe/Istanbul"))
    fields = {
        "reference_id": case_id,
        "source_id": source,
        "reported_date": local.date().isoformat(),
        "reported_clock_local": local.strftime("%H:%M"),
        "time_semantics": "reported_outbreak",
        "time_standard": "Europe/Istanbul",
        "reported_province": province,
        "reported_district": district,
        "location_kind": context,
        "record_origin": source,
    }
    # A published map mark or place name does not supply the original incident point.
    return {
        "intake_fields": {key: fields.get(key) for key in FIELDS},
        "reported_time_utc": stamp.isoformat(),
        "reported_time_precision": precision,
        "representative_record_coverage_documented": False,
    }


def main():
    receipts = {}
    hashes = {}
    for directory, expected in RECEIPTS.items():
        path = BASE / directory / "readback.json"
        content = path.read_bytes()
        require(hashlib.sha256(content).hexdigest() == expected, "Frozen receipt identity")
        receipts[directory.split("/", 1)[0]] = json.loads(content)
        hashes[path.relative_to(ROOT).as_posix()] = expected

    manavgat = receipts["manavgat_reported_starts_v1"]["cases"]
    require(
        all(
            r["original_start_coordinate_verified"] is False and r["target"] is None
            for r in manavgat
        ),
        "Manavgat references remain approximate",
    )
    cases = [
        case(
            f"manavgat_{r['case']}",
            "published_ogm_transcription",
            "Antalya",
            "Manavgat",
            datetime.fromisoformat(r["reported_start_utc"]),
            "reported_minute",
            "map_marker",
        )
        for r in manavgat
    ]
    kuyucak = receipts["open_reference_antalya_v1"]
    require(kuyucak["independent_origin_verified"] is False, "Kuyucak origin still unresolved")
    cases.append(
        case(
            "kuyucak_2022",
            "dha_kuyucak_field_report",
            "Antalya",
            "Akseki",
            datetime.fromisoformat(kuyucak["local_day"] + "T09:00:00+00:00"),
            "approximate",
            "settlement_proxy",
        )
    )
    for key, source, province, district, precision, context in (
        (
            "tirazli_2019",
            "aa_tirazli_field_report",
            "İzmir",
            "Karabağlar",
            "approximate",
            "village_or_study_area",
        ),
        (
            "marmaris_2022",
            "official_ogm_summary",
            "Muğla",
            "Marmaris",
            "approximate",
            "shore_proxy",
        ),
        (
            "gulnar_2022",
            "official_ministry_summary",
            "Mersin",
            "Gülnar",
            "reported_minute",
            "locality_or_settlement_proxy",
        ),
    ):
        row = receipts["three_province_start_context_v1"]["cases"][key]
        require(
            row["original_ignition_verified"] is False and row["target"] is None, "Origin status"
        )
        cases.append(
            case(
                key,
                source,
                province,
                district,
                datetime.fromisoformat(row["reported_start_utc"]),
                precision,
                context,
            )
        )
    require(len(cases) == 11, "Frozen public review scope")
    records = pd.DataFrame([row["intake_fields"] for row in cases])
    sources = {
        key: {
            "source_id": key,
            "lineage_status": "public_case_summary",
            "access_status": "source_incident_table_unavailable",
        }
        for key in records.source_id.unique()
    }
    for row, result in zip(cases, audit_intake(records, sources, {}), strict=True):
        row["intake_result"] = result
    statuses = Counter(row["intake_result"]["row_status"] for row in cases)
    require(statuses == {"needs_source_review": 11}, "All selected references require review")
    overlaps = receipts["manavgat_cluster_overlap_v1"]["scenarios"]
    radius_checks = [radius for scenario in overlaps for radius in scenario["radii"]]
    shared = sum(
        any(p["cases"] == [3, 4] and p["same_only_component"] for p in r["overlapping_pairs"])
        for r in radius_checks
    )
    report = {
        "source_receipt_sha256": hashes,
        "producer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "selected_public_case_slots_not_an_incident_population",
        "case_counts_by_province": dict(Counter(records.reported_province)),
        "intake_status_counts": dict(statuses),
        "manavgat_3_4_same_only_satellite_component": {
            "scenario_radius_checks": len(radius_checks),
            "checks_with_shared_component": shared,
            "same_physical_event_verified": False,
        },
        "cases": cases,
    }
    run = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = BASE / "public_start_evidence_v1" / run / "readback.json"
    out.parent.mkdir(parents=True, exist_ok=False)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    require(json.loads(out.read_bytes()) == report, "Output roundtrip")
    print(out.relative_to(ROOT).as_posix(), hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
