"""Bind selected public source notes to local bytes; never infer fire labels or identities."""

import hashlib
import json
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
NOTES = ROOT / "docs/research/mugla_public_extension_2026-11-19.json"
EARLIER = ROOT / (
    "outputs/reports/dataset/public_case_distribution_v1/20261108T130911Z_460265b4/readback.json"
)
EARLIER_SHA = "13e3a6d3def4836ce32907e46ca1ba0723c5b75f41992b9558934dc27527a20d"
PROVINCES = {"Antalya", "Muğla", "İzmir", "Mersin"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    notes_bytes = NOTES.read_bytes()
    notes = json.loads(notes_bytes)
    require(digest(EARLIER) == EARLIER_SHA, "Earlier registry identity")
    earlier = json.loads(EARLIER.read_bytes())
    artifacts = []
    for source in notes["sources"].values():
        for path_key, hash_key in (("path", "sha256"), ("render_path", "render_sha256")):
            if path_key not in source:
                continue
            path = (ROOT / source[path_key]).resolve()
            require(path.is_relative_to(ROOT / "outputs"), "Local output source only")
            require(digest(path) == source[hash_key], "Source identity")
            if path.suffix == ".pdf":
                require(path.read_bytes().startswith(b"%PDF-"), "PDF signature")
            artifacts.append({"path": source[path_key], "sha256": source[hash_key]})

    added = notes["selected_context_records"]
    require(len(added) == 4, "Bounded selected source notes")
    keys = [row["reference_key"] for row in earlier["cases"] + added]
    require(len(keys) == len(set(keys)), "No reused registry keys")
    for row in added:
        require(row["source_id"] in notes["sources"], "Documented source")
        require(row["province"] in PROVINCES, "Requested province")
        require(2018 <= date.fromisoformat(row["reported_local_day"]).year <= 2023, "Training")
        require("latitude" not in row and "longitude" not in row, "No inferred origin point")
        require("target" not in row, "No label assignment in source notes")
    for key in (
        "matching_ready",
        "positive_label_permitted",
        "negative_label_permitted",
        "model_ready",
        "final_merge_permitted",
        "new_correspondence_permitted",
    ):
        require(notes[key] is False, "Closed scientific and correspondence permissions")
    require(notes["daily_observation_status"] == "unknown", "Observation remains unknown")
    require(
        all(not row["added_to_project_cases"] for row in notes["table_quality_flags"]),
        "Flagged table examples stay outside selected registry",
    )

    def strata(rows):
        return Counter(
            (r["province"], date.fromisoformat(r["reported_local_day"]).year) for r in rows
        )

    before = strata(earlier["cases"])
    after = strata(earlier["cases"] + added)
    require(len(earlier["cases"]) == 23 and len(before) == 13, "Earlier selected scope")
    require(len(after) == 14 and ("Muğla", 2021) not in before, "New context stratum")
    cases = earlier["cases"] + [
        {
            **r,
            "matching_ready": False,
            "target": None,
            "source_document_sha256": notes["sources"][r["source_id"]]["sha256"],
        }
        for r in added
    ]
    report = {
        "scope": notes["scope"],
        "notes_sha256": hashlib.sha256(notes_bytes).hexdigest(),
        "earlier_registry_sha256": EARLIER_SHA,
        "producer_sha256": digest(Path(__file__)),
        "verified_artifacts": artifacts,
        "selected_context_rows_before": len(earlier["cases"]),
        "selected_context_rows_after": len(cases),
        "represented_province_years_before": len(before),
        "represented_province_years_after": len(after),
        "province_year_rows": [
            {"province": p, "year": y, "selected_context_rows": after[(p, y)]}
            for p in sorted(PROVINCES)
            for y in range(2018, 2024)
        ],
        "cases": cases,
        "distinct_real_fire_count": None,
        "additional_independent_measurements_from_republication": 0,
        "binary_labels_created": 0,
        "target_admission": specification(),
        "new_correspondence_started": False,
        "local_validation_or_final_test_data_opened": False,
    }
    out = (
        ROOT
        / "outputs/reports/dataset/mugla_public_extension_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    path = out / "readback.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_bytes()) == report, "Saved report readback")
    print(out.relative_to(ROOT).as_posix())
    print("PASS source_identity_and_selected_context_scope; no labels accepted")
    print("readback_sha256", digest(path))


if __name__ == "__main__":
    main()
