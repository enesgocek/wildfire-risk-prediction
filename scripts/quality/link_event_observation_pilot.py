"""Close a training-only intersection audit of candidate and observation evidence."""

import hashlib
import json
import socket
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction.event_observation_link import link_pilot
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
EVENT = "outputs/reports/dataset/full_event_sensitivity_v1/20261022T204358Z_820d043d"
PILOT = "outputs/reports/dataset/observation_protocol_evidence_v1/20261015T143126Z_dc01eb0c"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    def deny(*args, **kwargs):
        raise RuntimeError("Offline evidence link")

    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    pins = {}

    def retain(name, expected=None):
        p = ROOT / name
        require(
            p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(ROOT),
            "Contained regular input",
        )
        digest = sha(p)
        require(expected is None or digest == expected, "Input fingerprint")
        pins[name] = digest
        return p

    def report(folder, expected):
        r = json.loads(retain(folder + "/readback.json", expected).read_text())
        for name, digest in r["artifact_sha256"].items():
            retain(folder + "/" + name, digest)
        return r

    event = report(EVENT, "40818450ec28a2597eca1155bb6bb5896ce41fc65ec5fad2db6f1314d7229a86")
    obs = report(PILOT, "c87a96944635f650a9eb30005d959a56d998cd73154b3b48441a80e0e1a59df2")
    require(event["inside_training_union"] == 7610 and not event["labels_created"], "Event scope")
    require(obs["unit_count"] == 156 and not obs["labels_created"], "Pilot scope")
    for name in (
        "scripts/quality/link_event_observation_pilot.py",
        "src/wildfire_risk_prediction/event_observation_link.py",
        "src/wildfire_risk_prediction/target_admission.py",
    ):
        retain(name)
    candidates = pd.read_csv(ROOT / EVENT / "candidate_units.csv", float_precision="round_trip")
    observations = pd.read_csv(
        ROOT / PILOT / "unit_protocol_evidence.csv", float_precision="round_trip"
    )
    linked, outside = link_pilot(candidates, observations)
    counts = (
        linked.groupby(["candidate_review_category", "loaded_thermal_center_present"], dropna=False)
        .size()
        .rename("pilot_units")
        .reset_index()
    )
    # Existing illustrative cuts only; these are descriptive screens, not admission rules.
    screens = []
    for category, group in linked.groupby("candidate_review_category"):
        for field in (
            "nominal_land_fraction",
            "repeat_12h_fraction",
            "nominal_land_all_four_bins_fraction",
        ):
            screens.append(
                {
                    "candidate_review_category": category,
                    "pilot_units": len(group),
                    "diagnostic": field,
                    "illustrative_cut": 0.95,
                    "units_above_cut": int(group[field].ge(0.95).sum()),
                    "accepted_label_rule": False,
                }
            )
    # Independently count key intersection directly from the two input tables.
    keys = set(zip(candidates.grid_id, candidates.prediction_timestamp_utc, strict=True))
    pilot_keys = {(r.grid_id, r.target_day + "T00:00:00+00:00") for r in observations.itertuples()}
    require(
        len(keys & pilot_keys) == linked.first_candidate_present_in_catalog_union.sum(),
        "Independent intersection count",
    )
    require(len(keys - pilot_keys) == len(outside), "Independent outside-pilot count")
    out = (
        ROOT
        / "outputs/reports/dataset/event_observation_link_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    for name, frame in (
        ("pilot_evidence_links.csv", linked),
        ("candidates_outside_detailed_pilot.csv", outside),
        ("category_thermal_counts.csv", counts),
        ("illustrative_observation_screens.csv", pd.DataFrame(screens)),
    ):
        path = out / name
        frame.to_csv(path, index=False)
        reloaded = pd.read_csv(path, float_precision="round_trip")
        # All written content, including missing values, must round-trip.
        pd.testing.assert_frame_equal(frame.reset_index(drop=True), reloaded, check_dtype=False)
        artifacts[name] = sha(path)
    for name, digest in pins.items():
        require(sha(ROOT / name) == digest, "Inputs unchanged")
    path = out / "input_manifest.json"
    path.write_text(json.dumps(pins, indent=2) + "\n")
    artifacts[path.name] = sha(path)
    result = {
        "version": "event_observation_link_v1",
        "client_date": "2026-10-22",
        "status": "pilot_intersection_described_not_daily_label_acceptance",
        "completed_utc": datetime.now(UTC).isoformat(),
        "pilot_units": len(linked),
        "full_candidate_union": len(candidates),
        "candidate_keys_with_detailed_pilot": int(
            linked.first_candidate_present_in_catalog_union.sum()
        ),
        "candidate_keys_outside_this_pilot": len(outside),
        "pilot_units_without_first_candidate": int(
            (~linked.first_candidate_present_in_catalog_union).sum()
        ),
        "thermal_units_without_first_candidate": int(
            (
                linked.loaded_thermal_center_present
                & ~linked.first_candidate_present_in_catalog_union
            ).sum()
        ),
        "complete_pilot_geometry_plan_units": int(linked.pilot_geometry_plan_complete.sum()),
        "review_route_counts": {
            str(k): int(v) for k, v in linked.proposed_evidence_review_route.value_counts().items()
        },
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
        "model_ready": False,
        "final_merge_performed": False,
        "final_test_accessed": False,
        "validation_accessed": False,
        "network_requests": 0,
        "inherited_native_or_geometry_files_reopened": False,
        "reference_event_data_received": False,
        "input_count": len(pins),
        "artifact_sha256": artifacts,
    }
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    require(json.loads(path.read_text()) == result, "Report readback")
    require(all(sha(out / n) == h for n, h in artifacts.items()), "Artifact hashes")
    closure = {
        "report_sha256": sha(path),
        "all_input_hashes_unchanged": True,
        "all_csv_content_roundtrips_passed": True,
        "scientific_acceptance_granted": False,
    }
    (out / "completion_readback.json").write_text(json.dumps(closure, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    print("Result:", out.relative_to(ROOT).as_posix())
    print("Readback SHA256:", sha(path))


if __name__ == "__main__":
    main()
