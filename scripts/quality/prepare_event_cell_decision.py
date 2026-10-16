"""Compare two first-cell review directions on frozen sensitive cases; no labels."""

import hashlib
import json
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from wildfire_risk_prediction.feature_join import boolean, require
from wildfire_risk_prediction.first_cell_candidates import candidate_cells

ROOT = Path(__file__).resolve().parents[2]
TRACE = "outputs/reports/dataset/sensitive_trace_v1/20261014T194620Z_284f08c1"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def deny(*args, **kwargs):
    raise RuntimeError("Offline event-cell decision preparation")


def compare_candidates(units, contexts, components):
    """Count unit/scenario eligibility, retaining every unit and unassigned target.

    A keeps all recorded simultaneous earliest cells as candidates. B admits only
    single-earliest-cell components to a primary candidate pool. Neither is an
    accepted label policy, and an unmatched component is never a negative.
    """
    for frame in (units, contexts, components):
        require(frame.target.isna().all(), "Only unassigned source targets")
    require(units.review_unit_id.is_unique, "Unique review units")
    require(components.cluster_id.is_unique, "Unique component contexts")
    require(
        not contexts.duplicated(["review_unit_id", "scenario", "cluster_id"]).any()
        and set(contexts.review_unit_id) == set(units.review_unit_id)
        and set(contexts.cluster_id) == set(components.cluster_id),
        "Exact unique context coverage",
    )
    scenarios = set(components.scenario)
    require(
        all(set(g.scenario) == scenarios for _, g in contexts.groupby("review_unit_id")),
        "Every scenario present for every review unit",
    )
    boolean(contexts.catalog_first_candidate_match, "Saved first-candidate match")
    rows = contexts.merge(
        components[["cluster_id", "scenario", "earliest_grid_count", "duration_hours"]],
        on=["cluster_id", "scenario"],
        how="left",
        validate="many_to_one",
    )
    require(rows.earliest_grid_count.notna().all(), "Scenario/component keys agree")
    first_sets = rows.earliest_grid_ids_json.map(json.loads)
    require(
        all(
            isinstance(v, list)
            and len(v) > 0
            and all(isinstance(x, str) and x for x in v)
            and len(set(v)) == len(v)
            for v in first_sets
        )
        and first_sets.map(len).eq(rows.earliest_grid_count).all(),
        "All distinct first cells retained",
    )
    require(
        rows.grid_id.eq(rows.review_unit_id.map(units.set_index("review_unit_id").grid_id)).all()
        and rows.prediction_timestamp_utc.eq(
            rows.review_unit_id.map(units.set_index("review_unit_id").prediction_timestamp_utc)
        ).all(),
        "Context unit keys agree",
    )
    first = pd.to_datetime(rows.first_detection_utc, utc=True, format="ISO8601")
    t = pd.to_datetime(rows.prediction_timestamp_utc, utc=True, format="ISO8601")
    require(
        t.dt.year.between(2018, 2023).all() and t.eq(t.dt.floor("D")).all(),
        "Training daily decision examples only",
    )
    expected = (
        first.gt(t)
        & first.le(t + pd.Timedelta(24, unit="h"))
        & pd.Series(
            [grid in cells for grid, cells in zip(rows.grid_id, first_sets, strict=True)],
            index=rows.index,
        )
    )
    require(expected.eq(rows.catalog_first_candidate_match).all(), "Recomputed first matches")
    rows["A_candidate"] = expected
    rows["B_candidate"] = expected & rows.earliest_grid_count.eq(1)
    summaries = []
    for unit in units.sort_values("review_unit_id").itertuples():
        group = rows.loc[rows.review_unit_id.eq(unit.review_unit_id)]
        a = set(group.loc[group.A_candidate, "scenario"])
        b = set(group.loc[group.B_candidate, "scenario"])
        summaries.append(
            {
                "review_unit_id": unit.review_unit_id,
                "grid_id": unit.grid_id,
                "prediction_timestamp_utc": unit.prediction_timestamp_utc,
                "scenario_count": len(scenarios),
                "A_scenarios_with_candidate": len(a),
                "B_scenarios_with_candidate": len(b),
                "scenarios_losing_all_candidates_under_B": len(a - b),
                "multi_first_cell_component_present": bool(group.earliest_grid_count.gt(1).any()),
                "multi_first_cell_matched_component_present": bool(
                    (group.A_candidate & group.earliest_grid_count.gt(1)).any()
                ),
                "largest_context_hours": float(group.duration_hours.max()),
                "review_status": "automated_candidate_comparison_not_adjudicated",
                "target": None,
            }
        )
    impact = []
    for scenario, group in rows.groupby("scenario", sort=True):
        a = set(group.loc[group.A_candidate, "review_unit_id"])
        b = set(group.loc[group.B_candidate, "review_unit_id"])
        impact.append(
            {
                "scenario": scenario,
                "purposive_unit_denominator": len(units),
                "A_units_with_candidate": len(a),
                "B_units_with_candidate": len(b),
                "units_losing_all_candidates_under_B": len(a - b),
                "target": None,
            }
        )
    return pd.DataFrame(summaries), pd.DataFrame(impact)


def run():
    socket.create_connection = deny
    socket.socket.connect = deny
    pins = {}

    def bind(name, expected=None):
        path = ROOT / name
        require(path.is_file() and not path.is_symlink(), "Regular decision evidence")
        value = digest(path)
        require(expected is None or value == expected, "Decision evidence hash")
        pins[name] = value
        return path

    old = json.loads(
        bind(
            TRACE + "/readback.json",
            "f613115b0d67caea55353b102e2c420d1879666dfc8f94ea52416b0e9954fa11",
        ).read_text()
    )
    receipt = json.loads(
        bind(
            TRACE + "/completion_readback.json",
            "000ed76785212fc4a2b32cc4bdb806aabddba7c22b7ddee0caab85a3ad40dac1",
        ).read_text()
    )
    require(not old["labels_created"] and not old["model_ready"], "Unlabelled trace")
    require(receipt["report_sha256"] == digest(ROOT / TRACE / "readback.json"), "Trace receipt")
    files = {n: bind(TRACE + "/" + n, h) for n, h in old["artifact_sha256"].items()}
    units = pd.read_csv(files["unit_trace_summary.csv"])
    contexts = pd.read_csv(files["unit_scenario_components.csv"])
    components = pd.read_csv(files["component_graph_review.csv"])
    members = pd.read_csv(files["component_source_members.csv"])
    require(len(units) == 19 and len(contexts) == len(components) == 181, "Frozen case scope")
    require(set(members.cluster_id) == set(components.cluster_id), "Member coverage")
    require(not members.duplicated(["cluster_id", "detection_id"]).any(), "Distinct members")
    require(members.target.isna().all(), "No member labels")
    times = pd.to_datetime(members.detection_timestamp_utc, utc=True, format="ISO8601")
    require(times.dt.year.between(2018, 2023).all(), "Training members only")
    for row in components.itertuples():
        group = members.loc[members.cluster_id.eq(row.cluster_id)]
        t = times.loc[group.index]
        earliest = group.loc[t.eq(t.min())]
        require(
            len(group) == row.detection_count
            and t.min() == pd.Timestamp(row.first_detection_utc)
            and t.max() == pd.Timestamp(row.last_detection_utc)
            and earliest.grid_id.nunique() == row.earliest_grid_count
            and sorted(earliest.grid_id.unique()) == json.loads(row.earliest_grid_ids_json)
            and len(earliest) == row.earliest_detection_count
            and hashlib.sha256("\n".join(sorted(group.detection_id)).encode()).hexdigest()
            == row.membership_sha256,
            "Source membership and all simultaneous first cells agree",
        )
    cases, impact = compare_candidates(units, contexts, components)
    policy = json.loads(bind("configs/first_cell_candidates_v1.json").read_text())
    first_cells = candidate_cells(components, policy)
    require(
        len(first_cells) == int(components.earliest_grid_count.sum())
        and not first_cells.duplicated(["candidate_component_id", "grid_id"]).any()
        and first_cells.groupby("candidate_component_id").size().to_dict()
        == components.set_index("cluster_id").earliest_grid_count.to_dict(),
        "No first cell lost or component identity split by expansion",
    )
    require(
        cases.set_index("review_unit_id").A_scenarios_with_candidate.equals(
            units.set_index("review_unit_id").scenarios_with_first_candidate_match.sort_index()
        ),
        "Original nine-scenario matches reproduced",
    )
    for name in (
        "scripts/quality/prepare_event_cell_decision.py",
        "tests/test_event_cell_decision.py",
        "src/wildfire_risk_prediction/feature_join.py",
        "src/wildfire_risk_prediction/first_cell_candidates.py",
        "src/wildfire_risk_prediction/evaluation_folds.py",
    ):
        bind(name)
    out = (
        ROOT
        / "outputs/reports/dataset/event_cell_decision_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True)

    def save(name, value):
        (out / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )

    cases.to_csv(out / "case_decision_matrix.csv", index=False)
    impact.to_csv(out / "scenario_impact.csv", index=False)
    first_cells.to_csv(out / "component_first_cells.csv", index=False)
    save(
        "decision_options.json",
        {
            "status": "user_selected_A_candidate_direction_not_label_acceptance",
            "selected": "A",
            "policy_version": policy["version"],
            "recommended": "A",
            "A": (
                "Retain all recorded simultaneous earliest cells as candidates with shared event ID"
            ),
            "B": (
                "Keep multi-first-cell components for review; primary pool uses unique first cells"
            ),
            "neither_option": [
                "chooses spatial/time grouping thresholds or establishes physical event identity",
                "turns excluded/unmatched/unknown units into negative labels",
                "accepts binary targets, starts training or authorizes final merge",
            ],
            "population_coverage_effect": "not_estimated_from_selected_sensitive_cases",
        },
    )
    require(all(digest(ROOT / n) == h for n, h in pins.items()), "Final direct-input closure")
    save("input_manifest.json", pins)
    reloaded_cases = pd.read_csv(out / "case_decision_matrix.csv", float_precision="round_trip")
    reloaded_impact = pd.read_csv(out / "scenario_impact.csv", float_precision="round_trip")
    reloaded_first = pd.read_csv(out / "component_first_cells.csv")
    require(
        reloaded_cases.target.isna().all()
        and reloaded_impact.target.isna().all()
        and reloaded_first.target.isna().all(),
        "Empty targets preserved through CSV readback",
    )
    pd.testing.assert_frame_equal(
        reloaded_cases.drop(columns="target"), cases.drop(columns="target")
    )
    pd.testing.assert_frame_equal(
        reloaded_impact.drop(columns="target"), impact.drop(columns="target")
    )
    pd.testing.assert_frame_equal(
        reloaded_first.drop(columns="target"), first_cells.drop(columns="target")
    )
    require(
        json.loads((out / "input_manifest.json").read_text()) == pins
        and json.loads((out / "decision_options.json").read_text())["selected"] == "A",
        "Persisted input map and selected candidate-only direction",
    )
    save(
        "readback.json",
        {
            "status": "first_cell_options_readback_passed_not_adjudicated",
            "created_at_utc": datetime.now(UTC).isoformat(),
            "input_file_count": len(pins),
            "purposive_units": len(cases),
            "scenario_component_contexts": len(contexts),
            "first_cell_rows": len(first_cells),
            "multi_first_cell_contexts": int(components.earliest_grid_count.gt(1).sum()),
            "units_with_multi_first_cell_context": int(
                cases.multi_first_cell_component_present.sum()
            ),
            "units_with_candidate_loss_under_B": int(
                cases.scenarios_losing_all_candidates_under_B.gt(0).sum()
            ),
            "unit_scenarios_losing_all_candidates_under_B": int(
                cases.scenarios_losing_all_candidates_under_B.sum()
            ),
            "direct_input_closure_checked": True,
            "old_graph_partition_recomputed": False,
            "selected_event_policy": None,
            "selected_first_cell_policy": policy["version"],
            "labels_created": False,
            "negative_label_permitted": False,
            "daily_observation_status": "unknown",
            "model_ready": False,
            "final_merge_performed": False,
            "validation_accessed": False,
            "final_test_accessed": False,
            "network_requests": 0,
            "cloud_jobs_started": 0,
            "artifact_sha256": {p.name: digest(p) for p in out.iterdir() if p.is_file()},
        },
    )
    save("completion_readback.json", {"report_sha256": digest(out / "readback.json")})
    print(out.relative_to(ROOT).as_posix(), flush=True)


if __name__ == "__main__":
    run()
