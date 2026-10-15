"""Offline rehearsal on retained public context; no institutional incident data received."""

import json
import socket
import uuid
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.reference_intake import FIELDS, REVIEW_FLAGS, audit_intake

ROOT = Path(__file__).resolve().parents[2]
PARENT = Path("outputs/reports/dataset/independent_reference_plan_v1/20261015T145033Z_81f53320")
PARENT_SHA = "20e6d42f35c4c7310ef34f980dcb80de589fcc73b839d4daa93cb7185ce40e06"
ACCESS = Path("outputs/reports/dataset/reference_access_v1/20261015T144111Z_e70215f0")
CATALOG = Path("docs/research/reference_validation_sources_2026-10-15.json")


def run():
    def deny(*args, **kwargs):
        raise RuntimeError("Offline reference intake preparation")

    socket.socket.connect = deny
    socket.create_connection = deny
    pins = {}

    def retained(name, expected=None):
        path = ROOT / name
        require(
            path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(ROOT),
            "Contained regular reference input",
        )
        sha = digest(path)
        require(expected is None or expected == sha, "Intake input unchanged")
        pins[path.relative_to(ROOT).as_posix()] = sha
        return path

    def read(name, expected=None):
        return json.loads(retained(name, expected).read_text(encoding="utf-8"))

    parent = read(PARENT / "readback.json", PARENT_SHA)
    closing = read(PARENT / "completion_readback.json")
    require(
        closing["report_sha256"] == PARENT_SHA and parent["labels_created"] is False,
        "Closed independent-reference preparation",
    )
    for name, sha in parent["artifact_sha256"].items():
        retained(PARENT / name, sha)
    upstream = read(PARENT / "input_manifest.json")
    for name, sha in upstream.items():
        retained(name, sha)
    sources = {s["source_id"]: s for s in read(CATALOG)["sources"]}
    context = read(ACCESS / "curated_context_records.json")["records"]
    receipts = read(ACCESS / "source_receipts.json")
    document = next(s for s in receipts["sources"] if s["name"] == "mugla_2023.pdf")
    retained(ACCESS / "mugla_2023.pdf", document["sha256"])
    reviews = {
        source: {
            **dict.fromkeys(REVIEW_FLAGS, False),
            "verified_document_sha256": [document["sha256"]],
        }
        for source in {r["source_id"] for r in context}
    }
    normalized = []
    for record in context:
        # Publication row identities are not independently verified incident IDs.
        row = dict.fromkeys(FIELDS, "")
        for field in FIELDS:
            if record.get(field) is not None:
                row[field] = str(record[field])
        row["source_record_id"] = (
            "p"
            + str(record["source_pdf_page"])
            + ":"
            + (str(record["source_row_no"]) if "source_row_no" in record else "narrative")
        )
        row["source_document_sha256"] = document["sha256"]
        row["record_origin"] = "institutional_publication_context"
        normalized.append(row)
    diagnostics = audit_intake(pd.DataFrame(normalized, columns=FIELDS), sources, reviews)
    require(
        len(diagnostics) == 12
        and all(
            r["row_status"] == "needs_source_review"
            and not r["can_review_matching"]
            and r["target"] is None
            and not r["negative_label_permitted"]
            for r in diagnostics
        ),
        "Same twelve context records remain unadmitted",
    )
    empty = pd.read_csv(
        ROOT / PARENT / "incident_reference_template.csv", dtype=str, keep_default_na=False
    )
    require(list(empty.columns) == list(FIELDS) and len(empty) == 0, "Unfilled incident template")
    empty_diagnostics = audit_intake(empty, sources, {})
    require(empty_diagnostics == [], "No received incidents cannot imply absence")
    for name in (
        Path(__file__).relative_to(ROOT),
        "src/wildfire_risk_prediction/reference_intake.py",
        "src/wildfire_risk_prediction/reference_readiness.py",
    ):
        retained(name)
    out = (
        ROOT
        / "outputs/reports/dataset/reference_intake_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    (out / "context_intake_diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8"
    )
    reasons = Counter(code for row in diagnostics for code in row["reason_codes"])
    pd.DataFrame(
        [{"reason_code": k, "context_records": v} for k, v in sorted(reasons.items())]
    ).to_csv(out / "reason_counts.csv", index=False)
    (out / "pending_source_reviews.json").write_text(
        json.dumps(reviews, indent=2) + "\n", encoding="utf-8"
    )
    (out / "empty_template_receipt.json").write_text(
        json.dumps(
            {
                "status": "no_institutional_incident_records_received",
                "input_rows": 0,
                "diagnostic_rows": 0,
                "absence_inference_permitted": False,
                "labels_created": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    require(all(digest(ROOT / name) == sha for name, sha in pins.items()), "Final intake closure")
    (out / "input_manifest.json").write_text(json.dumps(pins, indent=2) + "\n", encoding="utf-8")
    report = {
        "status": "reference_intake_rehearsed_context_only_no_incident_acceptance",
        "parent_sha256": PARENT_SHA,
        "public_context_records": len(context),
        "context_records_held_for_review": len(diagnostics),
        "institutional_incident_rows": 0,
        "matching_ready_context_records": 0,
        "input_file_count": len(pins),
        "reason_code_count": len(reasons),
        "network_bytes": 0,
        "cloud_jobs_started": 0,
        "private_correspondence_read": False,
        "provider_records_automatically_mapped": False,
        "source_review_completed": False,
        "population_error_rate_estimated": False,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "labels_created": False,
        "model_ready": False,
        "final_merge_performed": False,
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir() if p.is_file()},
    }
    (out / "readback.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (out / "completion_readback.json").write_text(
        json.dumps(
            {
                "status": "passed_intake_preparation_not_reference_acceptance",
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
