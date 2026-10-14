"""Offline readback of nineteen sensitive pilot units, including nonmatching components."""

import hashlib
import json
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.pilot_event_trace import trace_sensitive_units

ROOT = Path(__file__).resolve().parents[2]
PILOT = "outputs/reports/dataset/label_protocol_v1/20261014T193224Z_54fdbb95"
GRAPH = "outputs/reports/events/review_v1/20261010T001137Z_320433ed"
PROXIMITY = "data/interim/source_audit/firms_candidates_static_proximity.csv"
REGISTRY = "configs/gcp_source_blocks_2026-10-13.json"
PROTECTED = (
    "outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/"
    "protected_inputs_readback_20261013.json"
)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def deny(*args, **kwargs):
    raise RuntimeError("Offline sensitive pilot trace")


def run():
    pins = {}

    def retained(name, expected=None):
        path = ROOT / name
        require(path.is_file() and not path.is_symlink(), "Regular pilot trace source")
        digest = sha(path)
        require(expected is None or digest == expected, "Pinned pilot trace source changed")
        pins[name] = digest
        return path

    old = json.loads(
        retained(
            PILOT + "/readback.json",
            "534d67c44cad55a267aaf57330b4396a9cbb6aa65baa8bfdd71b9037b7bb0cab",
        ).read_text()
    )
    require(not old["labels_created"] and not old["final_merge_performed"], "Unlabelled pilot")
    retained(
        PILOT + "/completion_readback.json",
        "97bb378040b2a7dd74893ddb163803794316fc29f6a28932ad992cee917d7e40",
    )
    files = {n: retained(PILOT + "/" + n, h) for n, h in old["artifact_sha256"].items()}
    pilot = pd.read_csv(files["pilot_protocol_review.csv"], float_precision="round_trip")
    units = pilot.loc[pilot.proposed_review_route.eq("event_scenario_disagreement_review")]
    require(len(pilot) == 400 and len(units) == 19, "Fixed sensitive pilot selection")
    matches = pd.read_csv(files["pilot_scenario_matches.csv"])
    graph = json.loads(
        retained(
            GRAPH + "/review.json",
            "61de3f798bb1462baf4f1d65bebc72539cef47467d5590baeec498951dc94d7e",
        ).read_text()
    )
    catalogs, assignments = {}, {}
    for scenario, hashes in graph["artifact_sha256"].items():
        catalogs[scenario] = pd.read_csv(
            retained(
                GRAPH + "/" + scenario + "_review.csv",
                hashes["review_sha256"],
            ),
            float_precision="round_trip",
        )
        assignments[scenario] = pd.read_csv(
            retained(
                "data/interim/event_grouping/" + scenario + "_assignments.csv",
                hashes["assignments_sha256"],
            )
        )
    source = pd.read_csv(
        retained(
            PROXIMITY,
            "98585c8bc4a8711af605089a73779f7150cf33d413c3e692afb197b0677b8f94",
        ),
        float_precision="round_trip",
    )
    require(len(source) == 30295, "Frozen training candidate coverage")
    registry = json.loads(
        retained(
            REGISTRY,
            "c5dcb61b6ccd0c6055f96a929cebcbdc6cea41857270b8581ba7a519495aec95",
        ).read_text()
    )
    require(
        not registry["negative_label_permitted"]
        and registry["daily_observation_status"] == "unknown",
        "Closed source gates",
    )
    retained(PROTECTED)
    protected = json.loads((ROOT / PROTECTED).read_text())
    for name, digest in protected.items():
        retained(name, digest)
    for name in (
        "src/wildfire_risk_prediction/pilot_event_trace.py",
        "src/wildfire_risk_prediction/event_case_trace.py",
        "src/wildfire_risk_prediction/event_review.py",
        "src/wildfire_risk_prediction/label_protocol_review.py",
        "src/wildfire_risk_prediction/target_admission.py",
        "src/wildfire_risk_prediction/feature_join.py",
        "scripts/quality/trace_sensitive_pilot.py",
    ):
        retained(name)
    summary, contexts, variants, members, paths = trace_sensitive_units(
        units,
        matches,
        catalogs,
        assignments,
        source,
        registry["deferred_days"],
    )
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    out = ROOT / "outputs/reports/dataset/sensitive_trace_v1" / stamp
    out.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    for name, frame in (
        ("unit_trace_summary.csv", summary),
        ("unit_scenario_components.csv", contexts),
        ("component_graph_review.csv", variants),
        ("component_source_members.csv", members),
        ("first_to_pilot_anchor_paths.csv", paths),
    ):
        path = out / name
        frame.to_csv(path, index=False, mode="x")
        strings = {
            c: str
            for c in frame
            if not frame[c].dropna().empty
            and frame[c].dropna().map(lambda x: isinstance(x, str)).all()
        }
        reread = pd.read_csv(path, dtype=strings, float_precision="round_trip")
        pd.testing.assert_frame_equal(
            frame.astype(object).where(frame.notna(), None).reset_index(drop=True),
            reread.astype(object).where(reread.notna(), None),
            check_exact=True,
        )
        artifacts[name] = sha(path)
    unique = members.drop_duplicates("detection_id")
    result = {
        "status": "sensitive_pilot_trace_readback_passed",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "input_sha256": pins,
        "artifact_sha256": artifacts,
        "review_units": len(summary),
        "pilot_window_anchor_detections": int(summary.anchor_detection_count.sum()),
        "unit_scenario_pairs": len(contexts[["review_unit_id", "scenario"]].drop_duplicates()),
        "unit_scenario_component_rows": len(contexts),
        "unique_component_variants": len(variants),
        "component_member_rows": len(members),
        "unique_source_detections": len(unique),
        "path_node_rows": len(paths),
        "first_to_anchor_paths": len(paths.loc[paths.path_step.eq(0)]),
        "first_match_explanation_counts": contexts.first_match_explanation.value_counts().to_dict(),
        "units_with_first_time_signature_change": int(summary.first_time_signatures.gt(1).sum()),
        "units_with_first_cell_signature_change": int(summary.first_cell_signatures.gt(1).sum()),
        "largest_traced_component_detections": int(variants.detection_count.max()),
        "longest_traced_component_hours": float(variants.duration_hours.max()),
        "unique_members_with_prior_type2_within_1000m": int(
            unique.static_prior_records_1000m.gt(0).sum()
        ),
        "variants_with_deferred_day_in_calendar_context": int(
            variants.deferred_days_in_calendar_context_json.ne("[]").sum()
        ),
        "variants_with_context_beyond_training": int(
            variants.context_extends_outside_training.sum()
        ),
        "labels_created": False,
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "model_ready": False,
        "event_identities_accepted": 0,
        "selected_event_policy": None,
        "final_merge_authorized": False,
        "final_merge_performed": False,
        "protected_inputs_verified": len(protected),
        "validation_accessed": False,
        "final_test_accessed": False,
        "network_requests": 0,
        "limits": [
            "Selected disagreements do not estimate population errors or independent fire counts",
            "Internal graph witnesses do not prove physical event identity or spread direction",
            "Whole graph maximality relies on the earlier pinned partition review",
            "Source attributes and Type=2 proximity are retrospective, not admission or predictors",
            "First-signature differences include splits/merges; not one-to-one event changes",
            "Calendar context is not exact observation or missing-pixel impact",
            "No human adjudication, label selection or final assembly",
        ],
    }
    require(all(sha(ROOT / n) == h for n, h in pins.items()), "Pilot trace input closure")
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text()) == result, "Pilot trace report readback")
    require(all(sha(out / n) == h for n, h in artifacts.items()), "Pilot trace artifact closure")
    closure = {
        "status": "passed",
        "report_sha256": sha(path),
        "input_files_verified": len(pins),
        "artifacts_verified": len(artifacts),
    }
    completion = out / "completion_readback.json"
    completion.write_text(json.dumps(closure, indent=2) + "\n", encoding="utf-8")
    require(json.loads(completion.read_text()) == closure, "Completion readback")
    print("Sensitive trace result:", out.relative_to(ROOT).as_posix(), flush=True)
    return out


if __name__ == "__main__":
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    run()
