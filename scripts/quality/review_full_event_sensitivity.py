"""Read frozen catalogs to quantify the scope of unresolved grouping choices."""

import hashlib
import json
import socket
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction.event_sensitivity import summarize_candidates
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.first_cell_candidates import candidate_cells
from wildfire_risk_prediction.label_protocol_review import FLAGS, SCENARIOS
from wildfire_risk_prediction.target_admission import review_catalog

ROOT = Path(__file__).resolve().parents[2]
GRAPH = "outputs/reports/events/review_v1/20261010T001137Z_320433ed"
REFRESH = "outputs/reports/dataset/firms_refresh_comparison_v1/20261021T164652Z_313527d8"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    def deny(*args, **kwargs):
        raise RuntimeError("Offline scenario sensitivity")

    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    pins = {}

    def retain(name, expected=None):
        path = ROOT / name
        require(
            path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(ROOT),
            "Contained input",
        )
        digest = sha(path)
        require(expected is None or digest == expected, "Input hash")
        pins[name] = digest
        return path

    graph = json.loads(
        retain(
            GRAPH + "/review.json",
            "61de3f798bb1462baf4f1d65bebc72539cef47467d5590baeec498951dc94d7e",
        ).read_text()
    )
    require(
        graph["training_detection_count"] == 30295 and not graph["labels_created"],
        "Frozen training-only catalogs",
    )
    retain(
        REFRESH + "/readback.json",
        "7809413ec37b9a104b6cea36f060f0895e4d6908260a0cdd576ae1e4fa6fc5a7",
    )
    policy = json.loads(retain("configs/first_cell_candidates_v1.json").read_text())
    for name in (
        "scripts/quality/review_full_event_sensitivity.py",
        "src/wildfire_risk_prediction/event_sensitivity.py",
        "src/wildfire_risk_prediction/first_cell_candidates.py",
        "src/wildfire_risk_prediction/target_admission.py",
        "src/wildfire_risk_prediction/label_protocol_review.py",
    ):
        retain(name)
    expanded = []
    scenario_counts = []
    for scenario in SCENARIOS:
        catalog = pd.read_csv(
            retain(
                GRAPH + f"/{scenario}_review.csv",
                graph["artifact_sha256"][scenario]["review_sha256"],
            ),
            float_precision="round_trip",
        )
        validated, _ = review_catalog(catalog)
        require(catalog.detection_count.sum() == 30295, "Full scenario detection count")
        components = catalog.assign(scenario=scenario, target=None)
        cells = candidate_cells(components, policy)
        context = validated.assign(
            review_flags_json=validated.apply(
                lambda r: json.dumps([flag for flag in FLAGS if r[flag]]), axis=1
            )
        )
        cells = cells.merge(
            context[
                [
                    "cluster_id",
                    "candidate_prediction_timestamp_utc",
                    "membership_sha256",
                    "review_flags_json",
                ]
            ],
            left_on="candidate_component_id",
            right_on="cluster_id",
            validate="many_to_one",
        )
        cells = cells.rename(
            columns={"candidate_prediction_timestamp_utc": "prediction_timestamp_utc"}
        )
        expanded.append(cells)
        scenario_counts.append(
            {
                "scenario": scenario,
                "components": len(catalog),
                "component_first_cell_rows": len(cells),
                "candidate_cell_days": len(
                    cells.drop_duplicates(["grid_id", "prediction_timestamp_utc"])
                ),
            }
        )
    detail = pd.concat(expanded, ignore_index=True)
    units = summarize_candidates(detail)
    require(units.target.isna().all(), "No labels produced")
    # A second, simple set calculation checks support counts without the summarizer.
    support = {}
    for _scenario, group in detail.groupby("scenario"):
        keys = set(zip(group.grid_id, group.prediction_timestamp_utc, strict=True))
        for key in keys:
            support[key] = support.get(key, 0) + 1
    for row in units.itertuples():
        require(
            support[(row.grid_id, row.prediction_timestamp_utc)] == row.scenarios_with_candidate,
            "Independent scenario-set count",
        )
    require(len(units) == len(support), "Union key count")
    inside = units.loc[units.prediction_inside_training]
    counts = inside.scenarios_with_candidate.value_counts().reindex(range(1, 10), fill_value=0)
    histogram = pd.DataFrame(
        {"scenarios_with_candidate": counts.index, "candidate_cell_days": counts.values}
    )
    yearly = (
        inside.assign(year=inside.prediction_timestamp_utc.str[:4])
        .groupby(["year", "review_category"])
        .size()
        .rename("candidate_cell_days")
        .reset_index()
    )
    out = (
        ROOT
        / "outputs/reports/dataset/full_event_sensitivity_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    for name, frame in (
        ("candidate_units.csv", units),
        ("component_cell_evidence.csv", detail),
        ("support_histogram.csv", histogram),
        ("year_category_counts.csv", yearly),
        ("scenario_counts.csv", pd.DataFrame(scenario_counts)),
    ):
        path = out / name
        frame.to_csv(path, index=False)
        reread = pd.read_csv(path, dtype=str, keep_default_na=False)
        require(len(reread) == len(frame) and list(reread) == list(frame), "CSV shape readback")
        if "target" in reread:
            require(reread.target.eq("").all(), "Disk targets empty")
        artifacts[name] = sha(path)
    for name, digest in pins.items():
        require(sha(ROOT / name) == digest, "Inputs unchanged")
    path = out / "input_manifest.json"
    path.write_text(json.dumps(pins, indent=2) + "\n")
    artifacts[path.name] = sha(path)
    report = {
        "version": "full_event_sensitivity_v1",
        "client_date": "2026-10-22",
        "completed_utc": datetime.now(UTC).isoformat(),
        "status": "full_training_first_candidate_sensitivity_described",
        "source_training_detections": 30295,
        "scenarios": 9,
        "scenario_component_first_cell_rows": len(detail),
        "candidate_cell_day_union": len(units),
        "inside_training_union": len(inside),
        "outside_training_context_keys": len(units) - len(inside),
        "category_counts": {
            str(k): int(v) for k, v in inside.review_category.value_counts().items()
        },
        "support_histogram": {str(k): int(v) for k, v in counts.items()},
        "keys_with_any_review_flag": int(inside.review_flags_json.ne("[]").sum()),
        "independent_set_count_passed": True,
        "source_detection_rows_reparsed": False,
        "new_graphs_built": False,
        "source_refreshed": False,
        "all_scenarios_agreement_is_independent_evidence": False,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
        "scenario_selected": None,
        "final_merge_authorized": False,
        "final_test_accessed": False,
        "validation_accessed": False,
        "network_requests": 0,
        "input_count": len(pins),
        "artifact_sha256": artifacts,
    }
    path = out / "readback.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    require(json.loads(path.read_text()) == report, "JSON readback")
    require(all(sha(out / n) == h for n, h in artifacts.items()), "Artifact readback")
    closure = {
        "report_sha256": sha(path),
        "artifact_count": len(artifacts),
        "all_input_hashes_unchanged": True,
        "scientific_acceptance_granted": False,
    }
    (out / "completion_readback.json").write_text(json.dumps(closure, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print("Result:", out.relative_to(ROOT).as_posix())
    print("Readback SHA256:", sha(path))


if __name__ == "__main__":
    main()
