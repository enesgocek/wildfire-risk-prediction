"""Bind completed evidence and a future-year proposal without opening future-year values."""

import csv
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
RECEIPTS = {
    "experimental_SU_inspection_v2/20261123T102954Z_6d6e52c1": (
        "86270dea5d9d12a1764ead780dcfa79166bed60a0977bf712e3df497d84bc366"
    ),
    "primary_weather_rank_run_v1/20261123T143258Z_35678270": (
        "004f7d27d6b0f1825b2b00d7a2825b311e2483b5f2d73c7063cadd9b45b2946d"
    ),
    "fwi_reference_comparison_run_v1/20261123T101431Z_805e6449": (
        "5e5a7bd7a920b15d1288c7969b9841c62ac9948af5e74255c901ff6eb5a4d40c"
    ),
    "source_disjoint_frozen_assessment_v1/20261124T031245Z_91cd329d": (
        "7f6e16ff58084954610dea8ca41d9ca87ece9fd02192b076cfec5973845a5d23"
    ),
    "mesogeos_reference_pilot_audit_v1/20261124T233152Z_7d080df8": (
        "544f5fe7490ae72ec109bed48d6cd60be09404784bfd0baf540136e263ba1d44"
    ),
    "mesogeos_candidate_context_v1/20261124T234645Z_8d88cfe5": (
        "ae94cfbf8659e42bd463af33b2357bfaba3e74f63e9ed4b59b7a1d49650ecb48"
    ),
    "mesogeos_candidate_context_audit_v1/20261124T234801Z_9b662cb9": (
        "c1a181f96e6a7f09079eb0108d243b0c7b9bb90f06b59a0cab48016c0b09b449"
    ),
}
FEATURES = BASE / "waiting_features_v1/20261017T010902Z_2aa6320b"
PROPOSAL = ROOT / "configs/2024_source_replication_feasibility_proposal_v1.json"


def main():
    inputs, evidence = {}, {}

    def read_receipt(path, expected):
        require(digest(path) == expected, "Pinned completed receipt")
        inputs[path.relative_to(ROOT).as_posix()] = expected
        return json.loads(path.read_bytes())

    for relative, expected in RECEIPTS.items():
        evidence[relative.split("/")[0]] = read_receipt(BASE / relative / "readback.json", expected)
    source = read_receipt(
        FEATURES / "readback.json",
        "a71675fa75d4176a80090be55519fef92aabcad3212e55e561278eb9ac4372fd",
    )
    index = FEATURES / "verified_daily_files.csv"
    require(digest(index) == source["artifact_sha256"][index.name], "Unchanged metadata index")
    inputs[index.relative_to(ROOT).as_posix()] = digest(index)
    with index.open(encoding="utf-8", newline="") as handle:
        metadata = list(csv.DictReader(handle))
    by_year = Counter(row["day"][:4] for row in metadata if row["kind"] == "features")
    require(sum(by_year.values()) == 2191 and "2024" not in by_year, "Existing feature index scope")
    model_run = "primary_weather_rank_run_v1/20261123T143258Z_35678270"
    models = evidence["primary_weather_rank_run_v1"]
    frozen = []
    for name, expected in models["artifact_sha256"].items():
        if not name.endswith("/ranker.json"):
            continue
        path = BASE / model_run / name
        require(digest(path) == expected, "Current frozen model bytes; no loading or inference")
        inputs[path.relative_to(ROOT).as_posix()] = expected
        frozen.append({"scenario": name.split("/")[0], "sha256": expected})
    require(
        len(frozen) == 9 and len(models["features"]) == 15,
        "Nine existing models and fixed feature order",
    )
    proposal = json.loads(PROPOSAL.read_bytes())
    require(proposal["execute_authorized"] is False, "Unexecuted proposal")
    require(
        all(
            proposal[f"scientific_values_{year}_permitted_now"] is False
            for year in (2023, 2024, 2025)
        ),
        "All closed year gates stay closed",
    )
    require(
        proposal["first_phase"]["source_scientific_years_if_authorized"] == [2024],
        "Narrow future decision scope",
    )
    inputs[PROPOSAL.relative_to(ROOT).as_posix()] = digest(PROPOSAL)
    catalog = ROOT / "data/interim/firms_combined_candidates_2018_2024.csv"
    # One schema line only. Do not scan dates, event counts, coordinates or scores.
    with catalog.open("rb") as handle:
        header = handle.readline(65537)
    require(len(header) <= 65536 and header.endswith(b"\n"), "Bounded single schema line")
    names = next(csv.reader([header.decode("utf-8-sig").strip()]))
    require(
        {"detection_timestamp_utc", "grid_id", "longitude", "latitude", "type", "confidence"}
        <= set(names),
        "Existing combined catalog schema",
    )
    gate = specification()
    require(
        gate["daily_observation_status"] == "unknown"
        and gate["negative_label_permitted"] is False
        and gate["model_ready"] is False,
        "Scientific gate unchanged",
    )
    output = (
        BASE
        / "stage_transition_review_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    output.mkdir(parents=True, exist_ok=False)
    result = {
        "status": "technical_route_complete_scientific_acceptance_open_new_year_proposal_only",
        "analysis_date": "2026-11-25",
        "receipt_count": len(RECEIPTS) + 1,
        "frozen_model_count": len(frozen),
        "fixed_dynamic_features": models["features"],
        "frozen_models": frozen,
        "feature_index_days_by_year": dict(sorted(by_year.items())),
        "index_is_global_disk_inventory": False,
        "combined_catalog_schema_only": {
            "path": catalog.relative_to(ROOT).as_posix(),
            "stat_bytes": catalog.stat().st_size,
            "header_sha256": hashlib.sha256(header).hexdigest(),
            "body_read": False,
        },
        "technical_route_basis": "researcher_selected_A_2026_11_23;not_a_new_scientific_acceptance",
        "scientific_acceptance_open": [
            "new_forest_shrub_event_membership",
            "PU_transfer_assumptions",
            "true_target_evaluation_reference",
        ],
        "current_gate": gate,
        "proposal_sha256": digest(PROPOSAL),
        "new_year_scientific_values_read": False,
        "new_training_or_prediction": False,
        "new_S_or_Y_or_L": False,
        "final_merge": False,
        "input_sha256": inputs,
        "producer_sha256": digest(Path(__file__)),
    }
    destination = output / "readback.json"
    destination.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    require(json.loads(destination.read_bytes()) == result, "Receipt readback")
    require(all(digest(ROOT / p) == h for p, h in inputs.items()), "Frozen input closure")
    print(output.relative_to(ROOT).as_posix())
    print(
        "PASS eight receipts, nine frozen models, metadata-only index; "
        "no future values or inference"
    )


if __name__ == "__main__":
    main()
