"""Separate readback of proposal flags, temporal roles and X; no fitting or labels."""

import csv
import json
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_partition import parse_csv

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
REPORTS = {
    "proposals": (
        "satellite_PU_L_proposals_v1/20261120T005519Z_62f3f815",
        "679a5ad9eab6342fa153c46cbbcc8f1e494b92256b592ba84f24823d0c0a4a85",
    ),
    "partition": (
        "satellite_PU_partition_v1/20261120T010148Z_74c8eee5",
        "7f8169cf0dbc365ea576e722c66e018d63812829be1810f1bf90bd3dfebef7ff",
    ),
    "features": (
        "satellite_PU_feature_review_v1/20261120T010533Z_6d61c80e",
        "64262888976fe43530897f9c069eb73866dea42003ffc4fd31fcfa17ddd74138",
    ),
}
KEYS = join.KEYS


def rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def key(row):
    return tuple(row[n] for n in KEYS)


def main():
    reports, folders = {}, {}
    for name, (relative, sha) in REPORTS.items():
        folder = folders[name] = BASE / relative
        join.require(not (folder / "separate_readback.json").exists(), "Never replace receipts")
        p = folder / "readback.json"
        join.require(digest(p) == sha, "Frozen run receipt")
        report = reports[name] = json.loads(p.read_bytes())
        for artifact, expected in report["artifact_sha256"].items():
            join.require(digest(folder / artifact) == expected, "Current output identity")
    parent = BASE / "satellite_PU_preparation_v1/20261120T004314Z_88c008ce"
    parent_report = json.loads((parent / "readback.json").read_bytes())
    raw = parent / "all_scenario_first_cell_cover_review.csv"
    join.require(digest(raw) == parent_report["artifact_sha256"][raw.name], "Parent first cells")
    originals = rows(raw)
    proposed = rows(folders["proposals"] / "all_first_cells_with_proposal_flags.csv")
    join.require(len(originals) == len(proposed) == 62331, "Every first cell retained")
    policy = reports["proposals"]["decision"]
    wf = tuple(policy["WF1538_retained_key"])
    proposals, scenario_keys = set(), defaultdict(set)
    for original, row in zip(originals, proposed, strict=True):
        join.require(all(row[k] == v for k, v in original.items()), "Unchanged first-cell fields")
        expected = (
            int(row["cgls_2017_woody_center_count"]) == int(row["first_center_count"])
            and row["fit_role_boundary_review"] == "False"
            and key(row) != wf
        )
        join.require(row["possible_L_proposal"] == str(expected), "Exact approved cover direction")
        join.require(not row["target"] and not row["weak_positive_membership"], "No Y or L")
        if expected:
            proposals.add(key(row))
            scenario_keys[row["scenario"]].add(key(row))
    union = rows(folders["proposals"] / "proposal_key_union.csv")
    join.require(len(union) == len(proposals) == 1670, "Proposal union count")
    join.require({key(r) for r in union} == proposals, "Exact proposal union")
    join.require(
        all(not r["target"] and not r["accepted_L_membership"] for r in union), "No admission"
    )
    # Include the three protected case receipts and the current cover decision.
    for relative, sha in reports["proposals"]["input_sha256"].items():
        join.require(digest(ROOT / relative) == sha, "Protected inputs unchanged")
    u_file = BASE / "noisy_positive_pu_pilot_v1/20261119T121014Z_122b22c7/U_key_sample.csv"
    join.require(
        digest(u_file) == "fd77c27454083e45f625e7e94ef0a14e5ace7d65636cace59b92261666c4d19f",
        "Original U acquisition unchanged",
    )
    u_keys = {key(r) for r in rows(u_file)}
    join.require(len(u_keys) == 2048 and not proposals & u_keys, "Same U, measured zero overlap")
    roles = rows(folders["partition"] / "proposed_key_roles.csv")
    join.require(len(roles) == len(proposals | u_keys) == 3718, "Every review key once")
    join.require({key(r) for r in roles} == proposals | u_keys, "Partition key conservation")
    # Reconstruct graph context directly, without the partition producer's helpers.
    lineage = BASE / "satellite_PU_lineage_v1/20261120T003414Z_a21f7422"
    lineage_report = json.loads((lineage / "readback.json").read_bytes())
    detected_file = lineage / "d2000m_t72h/detections.csv"
    join.require(
        digest(detected_file) == lineage_report["artifact_sha256"]["d2000m_t72h/detections.csv"],
        "Frozen maximum graph context",
    )
    detected = rows(detected_file)
    by_id = {r["detection_id"]: r["final_graph_membership_sha256"] for r in detected}
    contexts = defaultdict(set)
    for row in detected:
        stamp = datetime.fromisoformat(row["timestamp_utc"])
        day = (stamp - timedelta(microseconds=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        k = (row["grid_id"], day.isoformat())
        if k in u_keys:
            contexts[k].add(row["final_graph_membership_sha256"])
    for row in proposed:
        if row["possible_L_proposal"] == "True":
            contexts[key(row)].update(by_id[i] for i in json.loads(row["first_detection_ids_json"]))
    phase_blocks = defaultdict(set)
    cut = datetime(2022, 1, 1, tzinfo=UTC)
    end = datetime(2023, 1, 1, tzinfo=UTC)
    start = datetime(2018, 1, 1, tzinfo=UTC)
    for row in roles:
        k = key(row)
        t = datetime.fromisoformat(k[1])
        expected = (
            "proposed_fit_2018_2021"
            if start <= t and t + timedelta(days=1) < cut
            else "proposed_assessment_2022"
            if cut <= t and t + timedelta(days=1) < end
            else "boundary_review_not_used"
        )
        join.require(row["proposed_partition"] == expected, "This run has no crossing blocks")
        join.require(
            set(json.loads(row["observed_graph_context_ids_json"])) == contexts[k],
            "Raw graph context",
        )
        join.require(row["original_U_sample_present"] == str(k in u_keys), "Original U flag")
        join.require(row["possible_L_proposal_present"] == str(k in proposals), "Proposal flag")
        join.require(not row["target"] and not row["accepted_L_membership"], "Roles are not labels")
        expected_scenarios = {s for s, keys in scenario_keys.items() if k in keys}
        join.require(
            set(json.loads(row["proposed_scenarios_json"])) == expected_scenarios,
            "Scenario membership",
        )
        phase_blocks[expected].update(contexts[k])
    join.require(
        not phase_blocks["proposed_fit_2018_2021"] & phase_blocks["proposed_assessment_2022"],
        "No shared observed blocks",
    )
    scenario_counts = []
    for scenario in sorted(scenario_keys):
        counts = {"scenario": scenario}
        for phase in (
            "proposed_fit_2018_2021",
            "proposed_assessment_2022",
            "boundary_review_not_used",
        ):
            counts[phase] = {
                "U": sum(key(r) in u_keys and r["proposed_partition"] == phase for r in roles),
                "possible_L_keys": sum(
                    key(r) in scenario_keys[scenario] and r["proposed_partition"] == phase
                    for r in roles
                ),
            }
        scenario_counts.append(counts)
    join.require(
        scenario_counts == reports["partition"]["scenario_summaries"], "Independent temporal counts"
    )
    features = parse_csv((folders["features"] / "features.csv").read_bytes())
    qa = parse_csv((folders["features"] / "provenance.csv").read_bytes())
    metadata = parse_csv((folders["features"] / "review_roles.csv").read_bytes())
    join.require(
        features.columns.tolist() == KEYS + join.feature_names(), "Only 27 allowed X fields"
    )
    for table in (features, qa, metadata):
        join.require(len(table) == 3718 and not table.duplicated(KEYS).any(), "Unique feature keys")
        join.require(
            set(table[KEYS].itertuples(index=False, name=None)) == proposals | u_keys,
            "Exact X universe",
        )
    u_parent = BASE / "full_U_feature_review_v1/20261120T000956Z_1a58d019"
    u_report = json.loads((u_parent / "readback.json").read_bytes())
    for name, combined in (("features.csv", features), ("provenance.csv", qa)):
        p = u_parent / name
        join.require(digest(p) == u_report["artifact_sha256"][name], "Frozen U snapshot")
        previous = parse_csv(p.read_bytes()).set_index(KEYS).sort_index()
        pd.testing.assert_frame_equal(
            combined.set_index(KEYS).loc[previous.index], previous, check_exact=True
        )
    join.require(
        metadata.target.isna().all() and metadata.accepted_L_membership.isna().all(),
        "Unknown real targets",
    )
    join.require(
        metadata.daily_observation_status.eq("unknown").all(), "Unknown observation status"
    )
    for flag, keys in (
        ("original_U_sample_present", u_keys),
        ("possible_L_proposal_present", proposals),
    ):
        join.require(
            set(metadata.loc[metadata[flag], KEYS].itertuples(index=False, name=None)) == keys,
            "Exact role flags",
        )
    join.require(qa.static_reference_year.eq(2017).all(), "Past static context")
    # ISO parser accepts both whole and fractional seconds, with no inferred format.
    for row in rows(folders["features"] / "provenance.csv"):
        t = datetime.fromisoformat(row["prediction_timestamp_utc"])
        join.require(2018 <= t.year <= 2022, "No scientific future-role rows")
        for field in ("weather_source_last_timestamp_utc", "weather_rain_interval_end_utc"):
            join.require(
                datetime.fromisoformat(row[field]) == t - timedelta(hours=1),
                "Weather strictly before T",
            )
        for w in (30, 60):
            prefix = f"vegetation_{w}d_"
            if row[prefix + "vegetation_present"] == "True":
                cutoff = datetime.fromisoformat(row[prefix + "snapshot_cutoff_utc"])
                acquired = datetime.fromisoformat(row[prefix + "source_acquisition_latest_utc"])
                lower = datetime.fromisoformat(row[prefix + "window_start_utc"])
                join.require(lower <= acquired < cutoff <= t, "Vegetation strictly past")
    join.require(
        not qa.operational_eligible.any(), "Retrospective X is not operational availability"
    )
    common = {
        "status": "separate_readback_passed_not_independent_physical_fire_validation",
        "checker_sha256": digest(Path(__file__)),
        "real_Y_and_accepted_L_created": 0,
        "model_fitted": False,
        "final_merge_performed": False,
    }
    for name, folder in folders.items():
        result = common | {"parent_readback_sha256": REPORTS[name][1], "checked": name}
        if name == "proposals":
            result.update(
                first_cell_rows=62331, possible_proposal_keys=1670, protected_WF1538_excluded=True
            )
        elif name == "partition":
            result.update(
                unique_keys=3718, shared_observed_graph_blocks=0, scenario_counts=scenario_counts
            )
        else:
            result.update(
                unique_keys=3718,
                unchanged_U_keys=2048,
                complete_27_features=int(features[join.feature_names()].notna().all(axis=1).sum()),
                raw_daily_files_rehashed_in_this_separate_check=False,
            )
        p = folder / "separate_readback.json"
        p.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(name, digest(p), flush=True)


if __name__ == "__main__":
    main()
