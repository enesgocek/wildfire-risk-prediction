"""Bounded May 2022 ancestry for one WF1538 catalogue anchor; no ignition acceptance."""

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd
from prepare_marmaris_native_pair import write
from review_salur_lineage import prefix_equal, replay, resolve

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
NATIVE = BASE / "wf1538_native_support_v1/20261119T181411Z_926a75aa/readback.json"
CATALOG = ROOT / "data/interim/firms_combined_candidates_2018_2024.csv"
PINS = {
    NATIVE: "412c2a3209ea52b67c79f0460eefa31a3ade7c67fbad25ef8c3b5e22b198003a",
    CATALOG: "37ebb8e1f204b28faf2da21661ff6b0f8e9125c25876b7966df3ae9aea7551c5",
}
FIRST = pd.Timestamp("2022-05-27T10:30:00Z")
T = pd.Timestamp("2022-05-27T00:00:00Z")
END = pd.Timestamp("2022-05-28T00:00:00Z")


def main():
    require(all(digest(p) == h for p, h in PINS.items()), "Pinned native and catalogue")
    native = json.loads(NATIVE.read_text(encoding="utf-8"))
    anchor = native["detection_id"]
    with CATALOG.open(encoding="utf-8-sig", newline="") as stream:
        rows = [r for r in csv.DictReader(stream) if "2022-05-01" <= r["acq_date"] <= "2022-05-29"]
    frame = pd.DataFrame(rows)
    require(
        anchor in set(frame.detection_id)
        and frame.detection_timestamp_utc.str.startswith("2022-05").all(),
        "2022 fit-only bounded full AOI catalogue",
    )
    out = (
        BASE
        / "wf1538_temporal_context_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    frame.to_csv(out / "bounded_May_catalogue.csv", index=False)
    scenarios = []
    for radius in (500, 1000, 2000):
        for gap in (24, 48, 72):
            full = replay(frame, radius, gap)
            checks = {}
            for name, cutoff in (("catalogue_minute", FIRST), ("target_end", END)):
                prefix = replay(frame, radius, gap, cutoff)
                prefix_equal(prefix, full, cutoff)
                origins = resolve(prefix[2])
                matched = prefix[3].set_index("detection_id").loc[anchor]
                ids = origins[matched.ancestry_state_id_at_ingestion]
                born = prefix[0].loc[prefix[0].birth_candidate_id.isin(ids)]
                starts = pd.to_datetime(born.first_detection_utc, utc=True)
                checks[name] = {
                    "anchor_births": [
                        {
                            "birth_candidate_id": b.birth_candidate_id,
                            "first_detection_utc": b.first_detection_utc,
                            "earliest_grid_ids": json.loads(b.earliest_grid_ids_json),
                        }
                        for b in born.itertuples()
                    ],
                    "has_preT_catalogue_ancestry": bool(starts.lt(T).any()),
                    "all_ancestry_starts_at_anchor_minute": bool(starts.eq(FIRST).all()),
                    "prefix_history_preserved": True,
                    "within_72h_of_left_boundary": bool(
                        starts.lt(pd.Timestamp("2022-05-04T00:00:00Z")).any()
                    ),
                }
                folder = out / f"d{radius}_h{gap}" / name
                folder.mkdir(parents=True, exist_ok=False)
                for file, table in zip(
                    ("births.csv", "transitions.csv", "states.csv", "detections.csv"),
                    prefix[:4],
                    strict=True,
                ):
                    table.to_csv(folder / file, index=False)
            scenarios.append({"distance_m": radius, "gap_hours": gap, "checks": checks})
    result = {
        "scope": "WF1538_bounded_May_catalogue_ancestry_only",
        "catalogue_rows": len(frame),
        "catalogue_days": ["2022-05-01", "2022-05-29"],
        "anchor_id": anchor,
        "target_window": [T.isoformat(), END.isoformat()],
        "scenarios": scenarios,
        "full_outside_AOI_coverage_verified": False,
        "true_new_ignition_verified": False,
        "absence_of_prior_detections_is_coverage_proof": False,
        "source_clock_standard_resolved": False,
        "same_physical_fire_verified": False,
        "L_memberships_created": 0,
        "labels_created": False,
        "gate": specification(),
        "model_trained": False,
        "final_merge_performed": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in PINS.items()},
        "code_sha256": {
            p.relative_to(ROOT).as_posix(): digest(p)
            for p in [
                Path(__file__),
                ROOT / "scripts/quality/review_salur_lineage.py",
                ROOT / "src/wildfire_risk_prediction/event_lineage.py",
            ]
        },
        "artifact_sha256": {
            p.relative_to(out).as_posix(): digest(p) for p in out.rglob("*") if p.is_file()
        },
    }
    write(out / "readback.json", result)
    print((out / "readback.json").relative_to(ROOT).as_posix(), digest(out / "readback.json"))


if __name__ == "__main__":
    main()
