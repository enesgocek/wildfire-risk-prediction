"""Verify public reference context and prepare unfilled incident/coverage templates."""

import json
import re
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.reference_readiness import matching_readiness, turkish_area

ROOT = Path(__file__).resolve().parents[2]
ACCESS = Path("outputs/reports/dataset/reference_access_v1/20261015T144111Z_e70215f0")
CURATION_SHA = "01b61897e689d16a8dbb6f492b6acb572d7f1027779328a60f7117e707e1b4ee"
CATALOG = Path("docs/research/reference_validation_sources_2026-10-15.json")


def run():
    def deny(*args, **kwargs):
        raise RuntimeError("Offline reference validation preparation")

    socket.socket.connect = deny
    socket.create_connection = deny
    pins = {}

    def retained(name, expected=None):
        path = ROOT / name
        require(
            path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(ROOT),
            "Contained reference input",
        )
        sha = digest(path)
        require(expected is None or sha == expected, "Reference source unchanged")
        pins[path.relative_to(ROOT).as_posix()] = sha
        return path

    def read(name, expected=None):
        return json.loads(retained(name, expected).read_text(encoding="utf-8"))

    receipts = read(ACCESS / "source_receipts.json")
    require(
        receipts["credentials_used"] is False and len(receipts["sources"]) == 4,
        "Anonymous public retrieval",
    )
    for record in receipts["sources"]:
        require(
            record["success"] is True and record["http_status"] == 200, "Successful bounded sources"
        )
        path = retained(ACCESS / record["name"], record["sha256"])
        require(path.stat().st_size == record["bytes"], "Reference byte count")
    retained("scripts/quality/fetch_reference_publications.py", receipts["script_sha256"])
    catalog = read(CATALOG)
    require(
        catalog["status"] == "research_preparation_not_label_acceptance", "Closed source inventory"
    )
    sources = {s["source_id"]: s for s in catalog["sources"]}
    curation = read(ACCESS / "curated_context_records.json", CURATION_SHA)
    records = curation["records"]
    require(
        len(records) == 12 and len({r["reference_id"] for r in records}) == 12,
        "Fixed public context sample",
    )
    pages = read(ACCESS / "mugla_2023.pdf.pages.json")
    require(len(pages) == 54, "Inspected 54-page OGM publication")
    text = pages[45]["text"]
    parsed = {
        int(n): (prefix.strip(), day, area)
        for n, prefix, day, area in re.findall(
            r"(?m)^\s*(\d{1,2})\s+(.+?)\s+(\d{2}\.\d{2}\.\d{4})\s+.+?\s+([\d.]+,\d+)\s*$", text
        )
    }
    require(set(parsed) == set(range(1, 32)), "All source table row identities")
    context, readiness = [], []
    for row in records:
        if row["source_pdf_page"] == 46:
            prefix, day, area = parsed[row["source_row_no"]]
            require(
                " ".join(prefix.split()) == row["reported_unit"] + " " + row["reported_place"],
                "Table location transcription",
            )
            require(
                datetime.strptime(day, "%d.%m.%Y").strftime("%Y-%m-%d") == row["reported_date"]
                and area == row["reported_area_ha_text"],
                "Table date and area transcription",
            )
        else:
            narrative = re.sub(r"\s+", "", pages[8]["text"])
            require(
                row["source_pdf_page"] == 9
                and "14.07.2023" in narrative
                and "14:42" in narrative
                and "132,32" in narrative,
                "Narrative source witnesses",
            )
        context.append(
            {
                **row,
                "reported_area_ha": turkish_area(row["reported_area_ha_text"]),
                "exact_event_identity_proven": False,
                "source_review": "assistant_visual_and_text_check_not_independent_human_review",
            }
        )
        decision = matching_readiness(row, sources[row["source_id"]])
        decision["unresolved_requirements_json"] = json.dumps(
            decision.pop("unresolved_requirements")
        )
        readiness.append(decision)
    out = (
        ROOT
        / "outputs/reports/dataset/independent_reference_plan_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    pd.DataFrame(context).to_csv(out / "institutional_context_records.csv", index=False)
    checked = pd.DataFrame(readiness)
    require(
        checked.target.isna().all() and not checked.can_review_exact_grid_time_match.any(),
        "No exact grid/time reference acceptance",
    )
    checked.to_csv(out / "matching_readiness.csv", index=False)
    pd.DataFrame(catalog["sources"]).to_csv(out / "source_inventory.csv", index=False)
    incident_fields = [
        "reference_id",
        "source_id",
        "source_record_id",
        "reported_date",
        "reported_clock_local",
        "time_semantics",
        "time_standard",
        "event_time_lower_utc",
        "event_time_upper_utc",
        "reported_province",
        "reported_district",
        "location_kind",
        "longitude",
        "latitude",
        "source_crs",
        "location_uncertainty_m",
        "record_origin",
        "source_document_sha256",
        "use_terms",
    ]
    coverage_fields = [
        "source_id",
        "reported_province",
        "coverage_start_date",
        "coverage_end_date",
        "recorded_fire_types",
        "minimum_recorded_area_ha",
        "known_missing_periods",
        "reporting_exclusions",
        "coverage_completeness_statement",
        "location_generalisation",
        "time_definition",
        "source_document_sha256",
    ]
    pd.DataFrame(columns=incident_fields).to_csv(
        out / "incident_reference_template.csv", index=False
    )
    pd.DataFrame(columns=coverage_fields).to_csv(
        out / "reference_coverage_template.csv", index=False
    )
    for path in (
        Path(__file__).relative_to(ROOT),
        "src/wildfire_risk_prediction/reference_readiness.py",
        "docs/research/OGM_DATA_REQUEST_DRAFT_2026-10-15.md",
    ):
        retained(path)
    # Preserve the already-verified pilot identity; no native files or holdout data opened here.
    parent = Path(
        "outputs/reports/dataset/observation_protocol_evidence_v1/20261015T143126Z_dc01eb0c"
    )
    previous = read(
        parent / "readback.json", "c87a96944635f650a9eb30005d959a56d998cd73154b3b48441a80e0e1a59df2"
    )
    closing = read(parent / "completion_readback.json")
    require(
        closing["report_sha256"] == digest(ROOT / parent / "readback.json")
        and previous["labels_created"] is False,
        "Closed pilot parent",
    )
    pilot = pd.read_csv(
        retained(
            parent / "unit_protocol_evidence.csv",
            previous["artifact_sha256"]["unit_protocol_evidence.csv"],
        )
    )
    require(len(pilot) == 156 and pilot.target.isna().all(), "Fixed unlabelled pilot")
    calendar = set(pilot.target_day)
    require(
        all(digest(ROOT / name) == sha for name, sha in pins.items()), "Final source/input closure"
    )
    (out / "input_manifest.json").write_text(json.dumps(pins, indent=2) + "\n", encoding="utf-8")
    result = {
        "status": "reference_access_assessed_templates_ready_labels_closed",
        "source_inventory_entries": len(sources),
        "context_records": len(context),
        "large_fire_table_training_rows": 11,
        "narrative_training_rows": 1,
        "pilot_target_day_count": len(calendar),
        "context_outbreak_dates_matching_pilot_calendar": sum(
            r["reported_date"] in calendar for r in records
        ),
        "exact_grid_time_matching_ready_records": 0,
        "accepted_independent_negative_references": 0,
        "input_file_count": len(pins),
        "network_bytes_this_preparation": 0,
        "cloud_jobs_started": 0,
        "external_message_sent": False,
        "data_request_submitted": False,
        "independent_human_review_completed": False,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "positive_label_permitted": False,
        "labels_created": False,
        "model_ready": False,
        "final_merge_performed": False,
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir() if p.is_file()},
    }
    (out / "readback.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (out / "completion_readback.json").write_text(
        json.dumps(
            {
                "status": "passed_preparation_not_label_acceptance",
                "report_sha256": digest(out / "readback.json"),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(out.relative_to(ROOT).as_posix(), flush=True)


if __name__ == "__main__":
    run()
