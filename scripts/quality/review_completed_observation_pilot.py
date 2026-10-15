"""Offline receipt/raw/geometry replay and descriptive review of the fixed method pilot."""

import importlib.util
import json
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
import pyproj

from wildfire_risk_prediction.core_transfer import check_file, digest
from wildfire_risk_prediction.feature_join import require, training_day

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ATTEMPT = ROOT / "outputs/reports/dataset/observation_pilot_run_v1/20261015T134047Z_b6b84ca8"
ATTEMPT_SHA = "51e9f504ad2a6c6334ec37f5d5080b70185d1e35d9c4177c7906fa4032d65885"
PLAN = (
    ROOT
    / "outputs/reports/dataset/observation_pilot_queue_v2/20261015T114055Z_a141e892/queue_plan.json"
)
METRICS = {
    "domain": "reconstructed_domain_loaded_inside_m2",
    "nominal_land": "nominal_nonfire_land_loaded_inside_m2",
    "cloud": "cloud_loaded_inside_m2",
    "repeat_1h": "loaded_repeat_1h_area_m2",
    "repeat_6h": "loaded_repeat_6h_area_m2",
    "repeat_12h": "loaded_repeat_12h_area_m2",
}


def validate_summary(table, units, areas, expected, outside):
    """Check complete planned scope without promoting source completeness to labels."""
    keys = list(units.columns)
    require(table.review_unit_id.is_unique and units.review_unit_id.is_unique, "Unique units")
    require(len(table) == len(units), "Fixed unit count")
    left = table.sort_values("review_unit_id").reset_index(drop=True)
    right = units.sort_values("review_unit_id").reset_index(drop=True)
    require(left[keys].equals(right), "Exact fixed cohort metadata")
    for day in table.target_day.unique():
        training_day(day)
    require(
        table.target.isna().all()
        and table.daily_observation_status.eq("unknown").all()
        and table.negative_label_permitted.eq(False).all()
        and table.labels_created.eq(False).all()
        and table.full_daily_observation_proven.eq(False).all(),
        "Closed scientific gates",
    )
    require(
        table.all_planned_pairs_processed.eq(True).all()
        and table.missing_pair_count.eq(0).all()
        and table.missing_pairs_json.map(json.loads).map(lambda v: v == []).all(),
        "Complete planned source accounting",
    )
    needed = table.target_day.map(lambda d: len(expected[d]))
    excluded = table.target_day.map(lambda d: len(outside[d]))
    require(
        table.expected_pair_count.eq(needed).all()
        and table.completed_pair_count.eq(needed).all()
        and table.required_geometry_pair_count.eq(needed).all()
        and table.outside_by_native_time_pair_count.eq(excluded).all()
        and table.reference_neighbour_pair_count.eq(needed + excluded).all(),
        "Day-specific pair inventory",
    )
    numeric = table.select_dtypes(include="number").drop(columns="target", errors="ignore")
    require(np.isfinite(numeric.to_numpy()).all() and (numeric >= 0).all().all(), "Finite metrics")
    counts = [c for c in numeric if c.endswith("count") or c == "loaded_scan_rows"]
    require((numeric[counts] == np.floor(numeric[counts])).all().all(), "Integer counts")
    require(
        table.loaded_scan_rows.eq(
            table.loaded_inside_scan_count
            + table.loaded_boundary_scan_count
            + table.loaded_outside_scan_count
        ).all(),
        "Scan class conservation",
    )
    size = table.grid_id.map(areas)
    require(size.notna().all() and (size > 0).all(), "Known positive AOI parts")
    for suffix in ("inside", "boundary"):
        domain = table[f"reconstructed_domain_loaded_{suffix}_m2"]
        land = table[f"nominal_nonfire_land_loaded_{suffix}_m2"]
        cloud = table[f"cloud_loaded_{suffix}_m2"]
        require(
            (domain <= size + 0.05).all()
            and (land <= domain + 0.05).all()
            and (cloud <= domain + 0.05).all(),
            "Within-cell class area bounds",
        )
        require(
            np.allclose(table[f"loaded_{suffix}_area_m2"], land, rtol=0, atol=0.05),
            "Nominal land aliases",
        )
    previous = table.nominal_nonfire_land_loaded_inside_m2
    for gap in (1, 6, 12):
        current = table[f"loaded_repeat_{gap}h_area_m2"]
        require((current <= previous + 0.05).all(), "Nested temporal-repeat areas")
        previous = current
    result = table.copy()
    result["aoi_part_area_m2"] = size
    for name, column in METRICS.items():
        result[name + "_fraction"] = table[column] / size
    return result


def run():
    def deny(*args, **kwargs):
        raise RuntimeError("Offline pilot review")

    socket.socket.connect = deny
    socket.create_connection = deny
    pyproj.network.set_network_enabled(False)
    spec = importlib.util.spec_from_file_location(
        "queue_review", ROOT / "scripts/firms/run_observation_pilot_queue.py"
    )
    queue = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(queue)
    pair_reader = queue.__file__  # Dynamic sibling imports need the firms script directory.
    import sys

    sys.path.insert(0, str(Path(pair_reader).parent))
    from process_observation_pilot_pair import read_completed

    plan = queue.load_queue(PLAN)
    require(digest(ATTEMPT / "readback.json") == ATTEMPT_SHA, "Pinned completed attempt")
    report = queue.verified_attempt(ATTEMPT, digest(PLAN))
    require(
        report["status"] == "planned_pairs_processed_method_pilot_only"
        and report["failure"] is None
        and report["completed_pair_count"] == 98
        and report["missing_pair_count"] == 0
        and report["complete_source_units"] == 156,
        "Complete fixed method pilot",
    )
    out = (
        ROOT
        / "outputs/reports/dataset/observation_pilot_review_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    completed, sources, bound = {}, [], {}
    raw = ROOT / "data/raw/observation_pilot_v1" / digest(PLAN)[:16]
    for pair in plan["pairs"]:
        receipt = report["pair_receipts"][pair["sample_id"]]
        folder = ROOT / receipt["path"]
        checked = read_completed(folder, pair, digest(PLAN))
        require(
            checked["labels_created"] is False
            and checked["model_ready"] is False
            and checked["daily_observation_status"] == "unknown",
            "Closed pair gates",
        )
        for source in pair["sources"]:
            path = raw / queue.pair_name(pair) / source["filename"]
            record = check_file(path, source)
            require(
                checked["raw_source_sha256"][source["filename"]] == record["sha256"],
                "Raw receipt provenance",
            )
            sources.append({"sample_id": pair["sample_id"], "role": source["role"], **record})
            bound[path.relative_to(ROOT).as_posix()] = record["sha256"]
        for name, sha in checked["artifact_sha256"].items():
            bound[(folder / name).relative_to(ROOT).as_posix()] = sha
        for name in ("readback.json", "completion_readback.json"):
            bound[(folder / name).relative_to(ROOT).as_posix()] = digest(folder / name)
        completed[pair["sample_id"]] = folder
    # Replay the saved scan geometries; never re-download or recompute native pixels.
    table = queue.summarise(plan, completed, out)
    require(
        digest(out / "pilot_partial_summary.csv")
        == report["artifact_sha256"]["pilot_partial_summary.csv"],
        "Exact saved-geometry summary replay",
    )
    parts = gpd.read_file(ROOT / "data/interim/grid_aoi_parts.geojson").to_crs(6933)
    detail = validate_summary(
        table,
        pd.DataFrame(plan["units"]),
        parts.set_index("grid_id").geometry.area,
        plan["day_expected_pairs"],
        plan["day_outside_pairs"],
    )
    detail.to_csv(out / "unit_diagnostics.csv", index=False)
    pd.DataFrame(sources).to_csv(out / "source_checks.csv", index=False)
    # Descriptive area cuts only; none is an accepted negative-label threshold.
    screens = []
    for cut in (0.5, 0.8, 0.9, 0.95, 0.99):
        for metric in ("nominal_land", "repeat_1h", "repeat_6h", "repeat_12h"):
            screens.append(
                {
                    "area_fraction_cut": cut,
                    "metric": metric,
                    "unit_count": int((detail[metric + "_fraction"] >= cut).sum()),
                    "denominator": len(detail),
                    "accepted_label_rule": False,
                }
            )
    pd.DataFrame(screens).to_csv(out / "descriptive_area_cuts.csv", index=False)
    selected = []
    for reason, score in (
        ("lowest_nominal_land", detail.nominal_land_fraction),
        ("largest_land_vs_12h_gap", -(detail.nominal_land_fraction - detail.repeat_12h_fraction)),
        (
            "cloud_and_land_at_different_passes",
            -np.minimum(detail.cloud_fraction, detail.nominal_land_fraction),
        ),
        ("largest_boundary_area", -detail.nominal_nonfire_land_loaded_boundary_m2),
        ("highest_12h_repeat", -detail.repeat_12h_fraction),
    ):
        if reason == "largest_boundary_area" and not score.lt(0).any():
            continue
        index = score.sort_values(kind="stable").index[0]
        selected.append(
            {
                "inspection_reason": reason,
                **detail.loc[index].to_dict(),
                "researcher_decision": None,
            }
        )
    pd.DataFrame(selected).to_csv(out / "human_review_examples.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout="constrained")
    for signal, group in detail.groupby("signal_group", sort=True):
        axes[0].scatter(
            group.nominal_land_fraction, group.repeat_12h_fraction, label=signal, s=25, alpha=0.65
        )
        axes[1].scatter(group.nominal_land_fraction, group.cloud_fraction, s=25, alpha=0.65)
    axes[0].plot([0, 1], [0, 1], color="grey", linestyle="--", linewidth=1)
    axes[0].set_ylabel("Nominal land overlap, >=12 h separation / AOI area")
    axes[1].set_ylabel("Cloud union / AOI area (can overlap other passes)")
    for ax in axes:
        ax.set_xlabel("Nominal nonfire land union / AOI area")
        ax.set_xlim(-0.03, 1.03)
        ax.set_ylim(-0.03, 1.03)
        ax.grid(alpha=0.2)
    axes[0].legend(fontsize=7, loc="upper left")
    fig.suptitle("156 purpose-selected cell-days: approximate support, no labels")
    fig.savefig(out / "support_diagnostics.png", dpi=160)
    plt.close(fig)
    bound.update(plan["input_sha256"])
    for name in ("readback.json", "completion_readback.json", "pilot_partial_summary.csv"):
        bound[(ATTEMPT / name).relative_to(ROOT).as_posix()] = digest(ATTEMPT / name)
    require(all(digest(ROOT / p) == h for p, h in bound.items()), "Final input closure")
    queue.write_json(out / "input_manifest.json", bound)
    summary = {
        "status": "complete_fixed_pilot_replayed_not_daily_label_acceptance",
        "attempt_sha256": ATTEMPT_SHA,
        "queue_sha256": digest(PLAN),
        "input_file_count": len(bound),
        "reverified_raw_files": len(sources),
        "raw_source_bytes": sum(r["bytes"] for r in sources),
        "completed_pair_count": len(completed),
        "unit_count": len(detail),
        "target_day_count": detail.target_day.nunique(),
        "total_scan_cell_rows": int(detail.loaded_scan_rows.sum()),
        "boundary_scan_cell_rows": int(detail.loaded_boundary_scan_count.sum()),
        "outside_scan_cell_rows": int(detail.loaded_outside_scan_count.sum()),
        "nominal_land_zero_units": int(detail.nominal_land_fraction.eq(0).sum()),
        "repeat_12h_zero_units": int(detail.repeat_12h_fraction.eq(0).sum()),
        "support_fraction_medians": {n: float(detail[n + "_fraction"].median()) for n in METRICS},
        "summary_replay_identical": True,
        "network_bytes": 0,
        "cloud_jobs_started": 0,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "labels_created": False,
        "model_ready": False,
        "final_merge_performed": False,
        "scope": "purpose_selected_method_pilot_not_population_error",
        "script_sha256": digest(Path(__file__)),
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir() if p.is_file()},
    }
    queue.write_json(out / "readback.json", summary)
    queue.write_json(
        out / "completion_readback.json",
        {
            "status": "passed_not_daily_label_acceptance",
            "report_sha256": digest(out / "readback.json"),
        },
    )
    print(out.relative_to(ROOT).as_posix(), flush=True)


if __name__ == "__main__":
    run()
