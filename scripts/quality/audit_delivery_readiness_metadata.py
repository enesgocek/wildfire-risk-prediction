"""Inventory accepted feature-file metadata and closed research gates; never read daily values."""

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
FEATURES = BASE / "waiting_features_v1/20261017T010902Z_2aa6320b"
RELATIVE = ROOT / "configs/relative_risk_product_direction_v1.json"
CALENDAR = BASE / "source_calendar_feature_review_v1/20261121T164603Z_741c2896"
PAIRS = BASE / "temporal_pairwise_run_v1/20261121T174415Z_5a77b21e"
CROSS_SOURCE = BASE / "cross_source_fixed_model_run_v1/20261121T181438Z_bc972c9e"
PINS = {
    FEATURES / "readback.json": "a71675fa75d4176a80090be55519fef92aabcad3212e55e561278eb9ac4372fd",
    CALENDAR / "readback.json": "b718ed5d7ff492ddaf6d5217e7f88b3f62a6024a9d2138f4225154b3e3576040",
    PAIRS / "readback.json": "b8e847f8d510721ce84b788161ae40ac5f3bfa098154b0e56a013fc380f83d82",
    CROSS_SOURCE
    / "readback.json": "a4fb83beea02226eca149c5ca8a0383326a1db0143b2ca395adbc50a1e6ab6f9",
}


def inventory_index(root, rows):
    """Only path/existence/stat operations on daily artifacts, no content reads or hashes."""
    inventory, seen, day_kinds = [], set(), defaultdict(set)
    allowed = (root / "outputs/reports/dataset").resolve()
    for row in rows:
        day = date.fromisoformat(row["day"])
        kind = row["kind"]
        require(kind in {"features", "provenance"}, "Declared daily metadata kinds only")
        identity = (row["day"], kind)
        require(identity not in seen, "No duplicate day/kind in metadata index")
        seen.add(identity)
        day_kinds[row["day"]].add(kind)
        require(re.fullmatch(r"[0-9a-f]{64}", row["sha256"]) is not None, "Recorded SHA-256 shape")
        expected_bytes = int(row["bytes"])
        require(expected_bytes > 0, "Positive recorded file size")
        path = (root / row["path"]).resolve()
        require(
            path.is_relative_to(allowed), "Daily path stays inside accepted feature output store"
        )
        exists = path.is_file()
        size = path.stat().st_size if exists else None
        inventory.append(
            {
                "day": day.isoformat(),
                "year": day.year,
                "kind": kind,
                "path": row["path"],
                "recorded_sha256_not_rehashed": row["sha256"],
                "recorded_bytes": expected_bytes,
                "exists": exists,
                "current_stat_bytes": size,
                "size_matches": size == expected_bytes,
            }
        )
    return inventory, day_kinds


def main():
    pins = dict(PINS)
    require(all(digest(p) == h for p, h in pins.items()), "Pinned existing completion receipts")
    parent = json.loads((FEATURES / "readback.json").read_bytes())
    index = FEATURES / "verified_daily_files.csv"
    pins[index] = parent["artifact_sha256"][index.name]
    pins[RELATIVE] = digest(RELATIVE)
    pins[ROOT / "src/wildfire_risk_prediction/target_admission.py"] = digest(
        ROOT / "src/wildfire_risk_prediction/target_admission.py"
    )
    require(digest(index) == pins[index], "Exact accepted metadata index")
    with index.open(encoding="utf-8", newline="") as stream:
        inventory, days = inventory_index(ROOT, csv.DictReader(stream))
    require(
        len(days) == 2191
        and len(inventory) == 4382
        and all(k == {"features", "provenance"} for k in days.values())
        and all(2018 <= int(d[:4]) <= 2023 for d in days),
        "Exact accepted 2018-2023 metadata scope",
    )
    relative = json.loads(RELATIVE.read_bytes())
    gate = specification()
    require(
        gate["daily_observation_status"] == "unknown"
        and gate["negative_label_permitted"] is False
        and relative["prediction_horizon_hours"] == 24,
        "Existing observation and target contract",
    )
    rows = []
    for year in range(2018, 2026):
        selected = [r for r in inventory if r["year"] == year]
        counts = Counter(r["kind"] for r in selected)
        rows.append(
            {
                "year": year,
                "days_in_this_verified_index": len({r["day"] for r in selected}),
                "feature_files": counts["features"],
                "provenance_files": counts["provenance"],
                "missing_files": sum(not r["exists"] for r in selected),
                "stat_size_mismatches": sum(
                    r["exists"] and not r["size_matches"] for r in selected
                ),
                "recorded_bytes": sum(r["recorded_bytes"] for r in selected),
                "index_scope": "accepted_feature_candidate_index"
                if selected
                else "not_covered_by_this_index_not_proof_of_global_absence",
            }
        )
    packet = {
        "status": (
            "metadata_readiness_and_stage_one_evidence_packet_complete_not_transition_approval"
        ),
        "feature_index_days": len(days),
        "feature_index_files": len(inventory),
        "feature_index_years": sorted({r["year"] for r in inventory}),
        "missing_indexed_files": sum(not r["exists"] for r in inventory),
        "stat_size_mismatches": sum(r["exists"] and not r["size_matches"] for r in inventory),
        "scope_is_complete_disk_or_provider_inventory": False,
        "daily_feature_or_provenance_contents_read": False,
        "daily_file_content_hashes_recomputed": False,
        "new_2023_2024_2025_scientific_values_read": False,
        "diagnostic_target_gate_snapshot": gate,
        "relative_product_method_accepted": relative["main_research_method_accepted"],
        "unvalidated_source_score_publication_permitted": relative[
            "unvalidated_source_S_score_may_be_published_as_fire_risk"
        ],
        "three_stage_one_topics": {
            "new_forest_shrub_event_and_membership_admission": "scientific_basis_pending",
            "noisy_PU_target_transfer_basis": (
                "assumptions_and_uncertainty_not_accepted_for_main_research"
            ),
            "real_target_evaluation_reference": (
                "different_source_diagnostic_completed_reference_semantics_still_pending"
            ),
        },
        "low_auxiliary_AUC_is_automatic_PU_refutation_or_gate_rule": False,
        "FWI_file_received": any(
            p.is_file() for p in (ROOT / "data/raw/external/cems_fwi_pilot_v1").glob("*")
        ),
        "FWI_reference_can_replace_event_labels": False,
        "new_models_or_labels_created": 0,
        "final_merge_performed": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
    }
    out = (
        BASE
        / "delivery_readiness_metadata_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(out / "verified_feature_index_by_year.csv", index=False)
    pd.DataFrame(inventory).to_csv(out / "daily_artifact_stat_inventory.csv", index=False)
    packet["artifact_sha256"] = {p.name: digest(p) for p in out.iterdir()}
    require(
        all(digest(p) == h for p, h in pins.items()), "Evidence receipts/index/config unchanged"
    )
    p = out / "readback.json"
    p.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)
    print(
        "days",
        len(days),
        "files",
        len(inventory),
        "missing",
        packet["missing_indexed_files"],
        "size mismatches",
        packet["stat_size_mismatches"],
        flush=True,
    )


if __name__ == "__main__":
    main()
