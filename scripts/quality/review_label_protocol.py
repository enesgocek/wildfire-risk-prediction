"""Offline protocol comparison packet; keeps labels and final assembly approval closed."""

import hashlib
import json
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.final_merge_gate import require_final_merge_approval
from wildfire_risk_prediction.label_protocol_review import compare_catalogs

ROOT = Path(__file__).resolve().parents[2]
PILOT = "outputs/reports/dataset/window_pilot_v1/20261014T191547Z_b008fcf9"
GRAPH = "outputs/reports/events/review_v1/20261010T001137Z_320433ed"
WATER = "outputs/reports/dataset/water_scope_v1/20261014T185242Z_f2e469bd"
PROTECTED = (
    "outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/"
    "protected_inputs_readback_20261013.json"
)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def deny(*args, **kwargs):
    raise RuntimeError("Offline label protocol review")


def run():
    pins = {}

    def retained(name, expected=None):
        path = ROOT / name
        require(path.is_file() and not path.is_symlink(), "Regular protocol evidence")
        digest = sha(path)
        require(expected is None or expected == digest, "Protocol evidence hash changed")
        pins[name] = digest
        return path

    def report(name, expected):
        return json.loads(retained(name, expected).read_text(encoding="utf-8"))

    pilot = report(
        PILOT + "/readback.json", "f79fcb11ede0b7d0c24cf3a976146eae6df871791e9abddf179b4fa96a9e195f"
    )
    files = {n: retained(PILOT + "/" + n, h) for n, h in pilot["artifact_sha256"].items()}
    sample = pd.read_csv(files["pilot_window_audit.csv"], float_precision="round_trip")
    require(len(sample) == 400 and not pilot["labels_created"], "Fixed unlabelled pilot")
    graph = report(
        GRAPH + "/review.json", "61de3f798bb1462baf4f1d65bebc72539cef47467d5590baeec498951dc94d7e"
    )
    catalogs = {
        scenario: pd.read_csv(
            retained(GRAPH + "/" + scenario + "_review.csv", h["review_sha256"]),
            float_precision="round_trip",
        )
        for scenario, h in graph["artifact_sha256"].items()
    }
    water = report(
        WATER + "/readback.json", "7b5d296bae6c3744790817409db4bce3a947e92919a06abde9271eac07814cae"
    )
    scope = pd.read_csv(
        retained(WATER + "/grid_water_scope.csv", water["artifact_sha256"]["grid_water_scope.csv"])
    )
    reviewed, matches, scenarios = compare_catalogs(sample, catalogs, scope.grid_id)
    gate = json.loads(retained("configs/final_merge_review_v1.json").read_text())
    require(
        gate["explicit_user_approval_required"] and not gate["final_merge_authorized"],
        "Unapproved final merge policy",
    )
    try:
        require_final_merge_approval(None, None)
    except PermissionError:
        pass
    else:
        raise ValueError("Missing final approval must block assembly")
    options = {
        "status": "draft_options_not_accepted",
        "selected_event_policy": None,
        "selected_negative_policy": None,
        "final_merge_authorized": False,
        "event_options": [
            {
                "id": "single_scenario_after_review",
                "benefit": "One interpretable distance/time rule",
                "limit": "Threshold choice changes first-candidate keys and membership",
            },
            {
                "id": "scenario_agreement_review_first",
                "recommended_next_review": True,
                "benefit": "Separate stable and parameter-sensitive candidates before choosing",
                "limit": "Agreement is not fire identity; not proposed as a final label filter",
            },
            {
                "id": "reference_anchored_subset",
                "benefit": "Use dated event references for an independently assessed subset",
                "limit": "Reference coverage, event size selection and shared sensor dependence",
            },
        ],
        "negative_next_review": {
            "proposal": "Review source-complete, no-boundary, no-thermal cases with land support",
            "not_accepted_as_sufficient": True,
            "must_resolve": [
                "Target-window area support",
                "Cloud/time interpretation",
                "Event absence semantics",
                "Selection bias and independent evidence",
            ],
        },
        "before_final_merge": gate,
    }
    for name in (
        "src/wildfire_risk_prediction/label_protocol_review.py",
        "src/wildfire_risk_prediction/final_merge_gate.py",
        "src/wildfire_risk_prediction/target_admission.py",
        "scripts/quality/review_label_protocol.py",
        PROTECTED,
    ):
        retained(name)
    protected = json.loads((ROOT / PROTECTED).read_text())
    for name, digest in protected.items():
        retained(name, digest)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    out = ROOT / "outputs/reports/dataset/label_protocol_v1" / stamp
    out.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    for name, frame in (
        ("pilot_protocol_review.csv", reviewed),
        ("pilot_scenario_matches.csv", matches),
        ("scenario_overview.csv", scenarios),
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
        original = frame.reset_index(drop=True)
        pd.testing.assert_frame_equal(
            original.astype(object).where(original.notna(), None),
            reread.astype(object).where(reread.notna(), None),
            check_exact=True,
        )
        artifacts[name] = sha(path)
    path = out / "protocol_options.json"
    path.write_text(json.dumps(options, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text()) == options, "Options readback")
    artifacts[path.name] = sha(path)
    result = {
        "status": "protocol_comparison_readback_passed",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "input_sha256": pins,
        "artifact_sha256": artifacts,
        "sample_units": len(reviewed),
        "scenario_count": len(scenarios),
        "pilot_scenario_rows": len(matches),
        "catalog_match_state_counts": reviewed.catalog_match_state.value_counts().to_dict(),
        "proposed_review_route_counts": reviewed.proposed_review_route.value_counts().to_dict(),
        "selected_event_policy": None,
        "selected_negative_policy": None,
        "labels_created": False,
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "model_ready": False,
        "final_merge_authorized": False,
        "final_merge_performed": False,
        "protected_inputs_verified": len(protected),
        "validation_accessed": False,
        "final_test_accessed": False,
        "network_requests": 0,
        "limits": [
            "Catalog matches are review evidence, never binary targets",
            "Equal memberships across scenarios do not prove physical event identity",
            "No catalog first-candidate match does not mean no ongoing fire or reliable negative",
            "Primary routes order work; flags and all samples are retained",
            "Final part checks and actual user approval remain future work",
        ],
    }
    require(all(sha(ROOT / n) == h for n, h in pins.items()), "Input closure")
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text()) == result, "Report readback")
    require(all(sha(out / n) == h for n, h in artifacts.items()), "Artifact closure")
    (out / "completion_readback.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "report_sha256": sha(path),
                "input_files_verified": len(pins),
                "artifacts_verified": len(artifacts),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("Protocol review result:", out.relative_to(ROOT).as_posix(), flush=True)
    return out


if __name__ == "__main__":
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    run()
