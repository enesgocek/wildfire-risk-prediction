"""Offline synthesis and separate raw witnesses for the frozen ten-row source review."""

import argparse
import csv
import json
import socket
import warnings
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import numpy as np
import rasterio
from audit_source_sample_batch import verify_result
from prepare_marmaris_native_pair import module, write
from pyproj import Transformer, network
from rasterio.windows import Window

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
SAMPLE = BASE / "source_sampling_review_v1/20261119T133150Z_f94ebe6e/readback.json"
SAMPLE_SHA = "9647a69248ac158aad6f7a864b48bfad8eb61860be08ff3250f8dc643cd4d453"
PROPOSAL = BASE / "marmaris_L_proposal_v1/20261119T134021Z_5272c4bd/readback.json"
PROPOSAL_SHA = "89d0305b9f5c54809e6c1170a30c21fe1a0230da4afc65720d5eef5bc8c5f476"


def point_codes(report):
    """Retain every class from every local scan; never treat missing support as clear."""
    codes = sorted(
        {
            code
            for scan in report["local_scan_contexts"]
            for context in scan["contexts"]
            for code in context["point_mask_codes"]
        }
    )
    supported = [
        context
        for scan in report["local_scan_contexts"]
        for context in scan["contexts"]
        if context["point_mask_codes"]
    ]
    return {
        "point_mask_codes": codes,
        "point_support_found": bool(supported),
        "point_fire_mask_present_in_reviewed_pair": bool(set(codes) & {7, 8, 9}),
        "point_cloud_mask_present_in_reviewed_pair": 4 in codes,
        "all_point_support_mask5": bool(supported) and codes == [5],
        "is_negative_label": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=Path, required=True)
    args = parser.parse_args()

    def deny(*a, **kw):
        raise RuntimeError("Offline synthesis")

    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    network.set_network_enabled(False)
    batch_path = args.batch.resolve()
    require(batch_path.is_relative_to(BASE / "source_sample_batch_v1"), "Local batch result")
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    receipt = json.loads(
        (batch_path.parent / "completion_readback.json").read_text(encoding="utf-8")
    )
    require(receipt["report_sha256"] == digest(batch_path), "Completed batch bytes")
    require(
        batch["status"] == "seven_point_reviews_complete"
        and not batch["failures"]
        and batch["producer_sha256"]
        == digest(ROOT / "scripts/quality/audit_source_sample_batch.py")
        and digest(SAMPLE) == SAMPLE_SHA
        and digest(PROPOSAL) == PROPOSAL_SHA,
        "Current code and pinned full source sample",
    )
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    sources = {r["archive_row"]: r for r in sample["intake"]}
    records = {"WF1206": batch["first_review"], **{r["archive_row"]: r for r in batch["results"]}}
    require(len(records) == 8 and len(sources) == 10, "Eight measurements; ten rows retained")
    inspector = module("synthesis_inspector", "scripts/firms/inspect_l2_observation_sample.py")
    project = Transformer.from_crs(4326, 6933, always_xy=True)
    summaries, contexts, witnesses, inputs = (
        [],
        [],
        [],
        {
            batch_path.relative_to(ROOT).as_posix(): digest(batch_path),
            SAMPLE.relative_to(ROOT).as_posix(): SAMPLE_SHA,
            PROPOSAL.relative_to(ROOT).as_posix(): PROPOSAL_SHA,
        },
    )
    for row, source in sorted(sources.items()):
        require(2018 <= source["year"] <= 2022, "Fit-role source rows only")
        item = {
            "archive_row": row,
            "source_year": source["year"],
            "source_date": source["reported_date"],
            "target": None,
            "new_L_membership": False,
            "source_final_area_ha_context_only": source["reported_final_area_ha_context_only"],
        }
        if row not in records:
            require(row in {"WF1342", "WF1556"}, "No missing measured row substitution")
            item["review_status"] = (
                "source_clock_link_unresolved" if row == "WF1342" else "source_point_outside_Mersin"
            )
            summaries.append(item)
            continue
        ref = records[row]
        path = ROOT / ref["report"]
        require(digest(path) == ref["sha256"], "Exact point result bytes")
        report = verify_result(path, row)
        require(report["source_row"] == source, "Same frozen source metadata")
        inputs[path.relative_to(ROOT).as_posix()] = digest(path)
        item.update(point_codes(report))
        item.update(
            {
                "review_status": "single_pair_raw_reviewed_not_L",
                "scans_examined": report["scans_examined"],
                "local_scan_count": len(report["local_scan_contexts"]),
                "sample_id": report["sample_id"],
            }
        )
        plan_path = next(ROOT / n for n in report["input_sha256"] if n.endswith("native_plan.json"))
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        cache = ROOT / "data/raw/observation_core_v1" / digest(plan_path)[:16]
        files = {
            s["role"]: cache / s["filename"] for s in plan["all_pairs_inventory_only"][0]["sources"]
        }
        with warnings.catch_warnings(), ExitStack() as stack:
            warnings.simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
            mask = inspector.layer(stack, files["fire"], "fire_mask")
            qa = inspector.layer(stack, files["fire"], "algorithm_QA")
            lng, lat = [
                inspector.layer(stack, files["geolocation"], "geolocation_data/" + n)
                for n in ("longitude", "latitude")
            ]
            for scan in report["local_scan_contexts"]:
                witness = scan["nearest_native_pixel"]
                r, c = witness["row"], witness["column"]
                win = Window(c, r, 1, 1)
                top = max(scan["scan_index"] * 32, r - 1)
                bottom = min((scan["scan_index"] + 1) * 32, r + 2)
                codes = sorted(
                    set(
                        map(
                            int,
                            mask.read(
                                1,
                                window=Window(
                                    max(0, c - 1),
                                    top,
                                    min(mask.width, c + 2) - max(0, c - 1),
                                    bottom - top,
                                ),
                            ).ravel(),
                        )
                    )
                )
                require(
                    codes == witness["mask_neighbour_codes"]
                    and int(mask.read(1, window=win)[0, 0]) == witness["mask_code"]
                    and int(qa.read(1, window=win)[0, 0]) == witness["qa_raw"],
                    "Independent raw mask/QA witness",
                )
                x, y = project.transform(
                    float(lng.read(1, window=win)[0, 0]), float(lat.read(1, window=win)[0, 0])
                )
                px, py = project.transform(source["longitude"], source["latitude"])
                require(
                    abs(np.hypot(x - px, y - py) - witness["projected_distance_m"]) < 1e-8,
                    "Independent coordinate distance",
                )
                witnesses.append({"archive_row": row, "scan_index": scan["scan_index"], **witness})
                for context in scan["contexts"]:
                    contexts.append(
                        {
                            "archive_row": row,
                            "sample_id": report["sample_id"],
                            "scan_index": scan["scan_index"],
                            "scan_start_utc": scan["start_utc"],
                            "scan_end_utc": scan["end_utc"],
                            "scan_quality": scan["scan_quality"],
                            "clock_context": scan["clock_context"],
                            **context,
                        }
                    )
        summaries.append(item)
    proposal = json.loads(PROPOSAL.read_text(encoding="utf-8"))
    require(
        all(digest(ROOT / n) == h for n, h in proposal["input_sha256"].items()),
        "Prior L/U inputs unchanged",
    )
    out = (
        BASE
        / "source_sample_native_summary_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    fields = sorted(set().union(*(set(r) for r in summaries)))
    with (out / "source_rows.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(
            [
                {k: json.dumps(v) if isinstance(v, list) else v for k, v in r.items()}
                for r in summaries
            ]
        )
    write(
        out / "scan_contexts.json", {"contexts": contexts, "independent_raw_witnesses": witnesses}
    )
    result = {
        "status": "eight_single_pair_reviews_complete_two_source_metadata_limits_retained",
        "source_rows": summaries,
        "source_rows_total": 10,
        "raw_reviewed_rows": 8,
        "total_native_scans_examined": sum(r.get("scans_examined", 0) for r in summaries),
        "local_scan_contexts": len(witnesses),
        "rows_with_point_fire_mask_in_reviewed_pair": sum(
            r.get("point_fire_mask_present_in_reviewed_pair", False) for r in summaries
        ),
        "rows_with_point_cloud_mask_in_reviewed_pair": sum(
            r.get("point_cloud_mask_present_in_reviewed_pair", False) for r in summaries
        ),
        "rows_with_point_only_mask5_in_reviewed_pair": sum(
            r.get("all_point_support_mask5", False) for r in summaries
        ),
        "new_L_memberships": 0,
        "labels_created": False,
        "model_trained": False,
        "final_merge_performed": False,
        "negative_count_inferred": False,
        "detection_recall_or_source_error_rate_estimated": False,
        "source_clock_or_start_coordinate_role_resolved": False,
        "prior_possible_L_proposals_unchanged": 2,
        "U_sha256_unchanged": proposal["U_sample_sha256_unchanged"],
        "gate": specification(),
        "input_sha256": inputs,
        "producer_sha256": digest(Path(__file__)),
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
    }
    write(out / "readback.json", result)
    write(out / "completion_readback.json", {"report_sha256": digest(out / "readback.json")})
    print((out / "readback.json").relative_to(ROOT).as_posix(), digest(out / "readback.json"))
    print("PASS ten rows retained; no labels, L expansion or training")


if __name__ == "__main__":
    main()
