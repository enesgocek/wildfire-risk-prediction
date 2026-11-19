"""Offline closure of WF1206 raw diagnostic and seven prepared, unexecuted pair plans."""

import json
import socket
import warnings
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import numpy as np
import rasterio
from prepare_marmaris_native_pair import module, write
from pyproj import Transformer, network
from rasterio.windows import Window

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
POINT = BASE / "source_sample_point_v1/20261119T140051Z_000dc2bf/readback.json"
QUEUE = BASE / "source_review_queue_v1/20261119T141303Z_9c1e2156/queue_plan.json"
PROPOSAL = BASE / "marmaris_L_proposal_v1/20261119T134021Z_5272c4bd/readback.json"
PINS = {
    POINT: "9970de0d18f2717c0f72294e35a61938f55af452d034d3f341e2ecc10edc7efa",
    QUEUE: "dc6f2e51af888f7650a6a3652d50286f5c6d3b06becc91590a2929f246f27f01",
    PROPOSAL: "89d0305b9f5c54809e6c1170a30c21fe1a0230da4afc65720d5eef5bc8c5f476",
}


def main():
    def deny(*args, **kwargs):
        raise RuntimeError("Offline closure")

    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    network.set_network_enabled(False)
    require(all(digest(p) == h for p, h in PINS.items()), "Exact result versions")
    point, proposal = [json.loads(p.read_text(encoding="utf-8")) for p in (POINT, PROPOSAL)]
    require(
        all(digest(ROOT / n) == h for n, h in point["input_sha256"].items())
        and all(digest(ROOT / n) == h for n, h in point["code_sha256"].items()),
        "Raw audit source and code closure",
    )
    require(
        point["archive_row"] == "WF1206"
        and point["scans_examined"] == 202
        and len(point["local_scan_contexts"]) == 1
        and point["gate"] == specification()
        and point["L_memberships_created"] == 0
        and point["labels_created"] is False,
        "Single source result and closed gates",
    )
    local = point["local_scan_contexts"][0]
    require(local["scan_index"] == 113, "Recorded local scan")
    for context in local["contexts"]:
        require(
            abs(context["domain_fraction"] - 1) < 1e-12
            and abs(context["class_fractions"]["5"] - 1) < 1e-12
            and context["point_mask_codes"] == [5],
            "Approximate local support; floating error tolerance, no result editing",
        )
    # Independent bounded read of the witness, without repeating the full footprint audit.
    inspector = module("closure_inspector", "scripts/firms/inspect_l2_observation_sample.py")
    native_plan = next(ROOT / n for n in point["input_sha256"] if n.endswith("native_plan.json"))
    plan = json.loads(native_plan.read_text(encoding="utf-8"))
    cache = ROOT / "data/raw/observation_core_v1" / digest(native_plan)[:16]
    files = {
        s["role"]: cache / s["filename"] for s in plan["all_pairs_inventory_only"][0]["sources"]
    }
    witness = local["nearest_native_pixel"]
    r, c = witness["row"], witness["column"]
    with warnings.catch_warnings(), ExitStack() as stack:
        warnings.simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
        mask = inspector.layer(stack, files["fire"], "fire_mask")
        qa = inspector.layer(stack, files["fire"], "algorithm_QA")
        require(np.all(mask.read(1, window=Window(c - 1, r - 1, 3, 3)) == 5), "Witness 3x3 mask")
        require(int(qa.read(1, window=Window(c, r, 1, 1))[0, 0]) == 0, "Witness raw QA")
        lng, lat = [
            float(
                inspector.layer(stack, files["geolocation"], "geolocation_data/" + name).read(
                    1, window=Window(c, r, 1, 1)
                )[0, 0]
            )
            for name in ("longitude", "latitude")
        ]
    project = Transformer.from_crs(4326, 6933, always_xy=True)
    x, y = project.transform(lng, lat)
    px, py = project.transform(point["source_row"]["longitude"], point["source_row"]["latitude"])
    require(
        abs(np.hypot(x - px, y - py) - witness["projected_distance_m"]) < 1e-8,
        "Independent witness coordinate/distance read",
    )
    queue_runner = module("closure_queue", "scripts/firms/run_source_review_queue.py")
    runner = queue_runner.runner_module()
    queue = queue_runner.load_plan(QUEUE, runner)
    require(
        all(queue_runner.completed_probe(u, runner) is None for u in queue["units"]),
        "Queue preparation is not download success",
    )
    require(
        all(digest(ROOT / n) == h for n, h in proposal["input_sha256"].items()),
        "Prior proposal and U unchanged",
    )
    out = (
        BASE
        / "source_review_closure_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    result = {
        "status": "WF1206_reviewed_seven_pair_download_queue_waiting_private_login",
        "source_rows_retained": 10,
        "source_rows_raw_reviewed_this_sample": 1,
        "pending_transport_rows": 7,
        "metadata_untransportable_rows_retained": 2,
        "independent_raw_witness_check": True,
        "new_L_memberships": 0,
        "prior_possible_L_review_index_rows_unchanged": 2,
        "U_sha256_unchanged": proposal["U_sample_sha256_unchanged"],
        "pending_bytes": queue["total_raw_bytes"],
        "new_private_downloads_started": 0,
        "labels_created": False,
        "model_trained": False,
        "final_merge_performed": False,
        "gate": specification(),
        "network_used": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in PINS.items()},
        "producer_sha256": digest(Path(__file__)),
    }
    write(out / "readback.json", result)
    print((out / "readback.json").relative_to(ROOT).as_posix(), digest(out / "readback.json"))
    print("PASS source review closure; private seven-pair download still required")


if __name__ == "__main__":
    main()
