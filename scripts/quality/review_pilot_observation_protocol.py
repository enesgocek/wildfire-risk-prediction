"""Offline evidence about time gaps in the completed pilot; retain all unknown targets."""

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
import shapely

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require, training_day, utc_times
from wildfire_risk_prediction.observation_window import classify_intervals
from wildfire_risk_prediction.pilot_protocol import unit_evidence
from wildfire_risk_prediction.scan_support import read_scan_table

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PARENT = Path("outputs/reports/dataset/observation_pilot_review_v1/20261015T141509Z_6f7a885a")
PARENT_SHA = "8cd0e4730da5d539996f9e00f8984003c549aa2bb7e0edd9b91879eba3fdd116"
ATTEMPT = Path("outputs/reports/dataset/observation_pilot_run_v1/20261015T134047Z_b6b84ca8")
PLAN = Path(
    "outputs/reports/dataset/observation_pilot_queue_v2/20261015T114055Z_a141e892/queue_plan.json"
)


def run():
    def deny(*args, **kwargs):
        raise RuntimeError("Offline observation protocol evidence")

    socket.socket.connect = deny
    socket.create_connection = deny
    pyproj.network.set_network_enabled(False)
    pins = {}

    def retained(name, expected=None):
        path = ROOT / name
        require(
            path.resolve().is_relative_to(ROOT) and path.is_file() and not path.is_symlink(),
            "Local regular input",
        )
        sha = digest(path)
        require(expected is None or sha == expected, "Bound protocol input unchanged")
        pins[path.relative_to(ROOT).as_posix()] = sha
        return path

    parent = json.loads(retained(PARENT / "readback.json", PARENT_SHA).read_text())
    closing = json.loads(retained(PARENT / "completion_readback.json").read_text())
    require(
        closing["report_sha256"] == PARENT_SHA and parent["summary_replay_identical"] is True,
        "Parent closure",
    )
    for name, sha in parent["artifact_sha256"].items():
        retained(PARENT / name, sha)
    spec = importlib.util.spec_from_file_location(
        "protocol_queue", ROOT / "scripts/firms/run_observation_pilot_queue.py"
    )
    queue = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(queue)
    plan = queue.load_queue(retained(PLAN, parent["queue_sha256"]))
    for name, sha in plan["input_sha256"].items():
        retained(name, sha)
    report = queue.verified_attempt(ROOT / ATTEMPT, parent["queue_sha256"])
    retained(ATTEMPT / "readback.json", parent["attempt_sha256"])
    retained(ATTEMPT / "completion_readback.json")
    for name in (
        Path(__file__).relative_to(ROOT),
        "src/wildfire_risk_prediction/pilot_protocol.py",
    ):
        retained(name)
    units = pd.read_csv(ROOT / PARENT / "unit_diagnostics.csv")
    examples = pd.read_csv(ROOT / PARENT / "human_review_examples.csv")
    regions = (
        gpd.read_file(retained("data/interim/grid_aoi_parts.geojson"))
        .to_crs(6933)
        .set_index("grid_id")
        .geometry
    )
    frames, shapes = {}, {}
    for sample, receipt in report["pair_receipts"].items():
        folder = Path(receipt["path"])
        p = json.loads(retained(folder / "readback.json", receipt["report_sha256"]).read_text())
        c = json.loads(retained(folder / "completion_readback.json").read_text())
        require(
            c["report_sha256"] == receipt["report_sha256"]
            and p["negative_label_permitted"] is False,
            "Pair closure",
        )
        csv = retained(folder / "scan_grid.csv", p["artifact_sha256"]["scan_grid.csv"])
        gpkg = retained(
            folder / "scan_geometries.gpkg", p["artifact_sha256"]["scan_geometries.gpkg"]
        )
        frame = read_scan_table(csv)
        saved = gpd.read_file(gpkg, layer="nominal_nonfire_land")
        require(
            saved.crs.to_epsg() == 6933
            and saved.grid_id.tolist() == frame.grid_id.tolist()
            and saved.scan_id.tolist() == frame.scan_id.tolist(),
            "Saved scan/geometry alignment",
        )
        arr = saved.geometry.to_numpy()
        require(
            np.allclose(shapely.area(arr), frame.nominal_nonfire_land_m2, rtol=0, atol=0.05),
            "Scan geometry areas",
        )
        frames[sample], shapes[sample] = frame, arr
    out = (
        ROOT
        / "outputs/reports/dataset/observation_protocol_evidence_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    detail, bins, orbit_rows, timelines = [], [], [], {}
    for day, chosen in units.groupby("target_day", sort=True):
        needed = plan["day_expected_pairs"][day]
        frame = pd.concat([frames[s] for s in needed], ignore_index=True)
        arr = np.concatenate([shapes[s] for s in needed])
        for unit in chosen.to_dict("records"):
            mask = frame.grid_id.eq(unit["grid_id"]).to_numpy()
            local, geo = frame.loc[mask].reset_index(drop=True), arr[mask]
            metrics, slots = unit_evidence(local, geo, regions.loc[unit["grid_id"]], day)
            require(
                abs(
                    metrics["nominal_land_daily_m2"] - unit["nominal_nonfire_land_loaded_inside_m2"]
                )
                <= 0.05,
                "Daily union conserved",
            )
            detail.append({**unit, **metrics})
            bins.extend(
                {
                    "review_unit_id": unit["review_unit_id"],
                    "grid_id": unit["grid_id"],
                    "target_day": day,
                    **r,
                }
                for r in slots
            )
            inside = classify_intervals(local, day).eq("inside")
            supported = shapely.area(geo) > 0
            thermal = local.nominal_confidence_fire + local.high_confidence_fire
            for orbit, group in local.loc[inside & (supported | thermal.gt(0))].groupby(
                "orbit_id", sort=True
            ):
                orbit_rows.append(
                    {
                        "review_unit_id": unit["review_unit_id"],
                        "orbit_id": orbit,
                        "first_retained_scan_start_utc": utc_times(group.start_utc)
                        .min()
                        .isoformat(),
                        "last_retained_scan_end_utc": utc_times(group.end_utc).max().isoformat(),
                        "span_is_continuous_observation": False,
                        "scan_count": len(group),
                        "thermal_center_count": int(
                            (group.nominal_confidence_fire + group.high_confidence_fire).sum()
                        ),
                        "largest_single_scan_land_fraction": float(
                            group.nominal_nonfire_land_m2.max() / regions.loc[unit["grid_id"]].area
                        ),
                    }
                )
            if unit["review_unit_id"] in set(examples.review_unit_id):
                timelines[unit["review_unit_id"]] = (local, unit)
    table = pd.DataFrame(detail)
    require(
        len(table) == 156 and table.review_unit_id.is_unique and table.target.isna().all(),
        "Same closed cohort",
    )
    table.to_csv(out / "unit_protocol_evidence.csv", index=False)
    pd.DataFrame(bins).to_csv(out / "six_hour_support.csv", index=False)
    pd.DataFrame(orbit_rows).to_csv(out / "orbit_witnesses.csv", index=False)
    thermal_groups = (
        table.assign(actual_window_thermal=table.thermal_center_definite_count.gt(0))
        .groupby(["signal_group", "actual_window_thermal"], sort=True)
        .size()
        .reset_index(name="purpose_selected_unit_count")
    )
    thermal_groups.to_csv(out / "thermal_window_comparison.csv", index=False)
    screens = []
    for cut in (0.5, 0.8, 0.9, 0.95, 0.99):
        daily = table.nominal_land_fraction.ge(cut)
        repeat = table.repeat_12h_fraction.ge(cut)
        four = table.nominal_land_all_four_bins_fraction.ge(cut)
        for group, selection in table.groupby("signal_group", sort=True):
            ids = selection.index
            screens.append(
                {
                    "area_fraction_cut": cut,
                    "signal_group": group,
                    "denominator": len(ids),
                    "daily_land_passing": int(daily.loc[ids].sum()),
                    "repeat_12h_passing": int(repeat.loc[ids].sum()),
                    "all_four_bins_passing": int(four.loc[ids].sum()),
                    "accepted_label_rule": False,
                }
            )
    pd.DataFrame(screens).to_csv(out / "descriptive_protocol_comparison.csv", index=False)
    fig, axes = plt.subplots(
        len(examples), 1, figsize=(11, 2.2 * len(examples)), sharex=True, layout="constrained"
    )
    for ax, example in zip(axes, examples.to_dict("records"), strict=True):
        local, unit = timelines[example["review_unit_id"]]
        inside = classify_intervals(local, unit["target_day"]).eq("inside")
        start, end = utc_times(local.start_utc), utc_times(local.end_utc)
        middle = start.astype("int64") + (end.astype("int64") - start.astype("int64")) // 2
        hour = (middle - training_day(unit["target_day"]).value) / 3_600_000_000_000
        area = unit["aoi_part_area_m2"]
        for name, color in (("nominal_nonfire_land", "teal"), ("cloud", "slategray")):
            positive = inside & local[name + "_m2"].gt(0)
            ax.scatter(
                hour[positive],
                local.loc[positive, name + "_m2"] / area,
                s=12,
                alpha=0.6,
                color=color,
                label=name,
            )
        thermal = inside & (local.nominal_confidence_fire + local.high_confidence_fire).gt(0)
        ax.scatter(
            hour[thermal],
            np.full(int(thermal.sum()), 1.06),
            marker="v",
            color="crimson",
            s=20,
            label="thermal centers (not events)",
        )
        ax.set_title(
            unit["grid_id"] + " / " + unit["target_day"] + " / " + example["inspection_reason"],
            fontsize=9,
        )
        ax.set_ylim(-0.05, 1.12)
        ax.set_ylabel("Scan area / AOI")
        ax.grid(alpha=0.2)
        for edge in (6, 12, 18):
            ax.axvline(edge, color="gray", linestyle="--", linewidth=0.5)
    axes[0].legend(fontsize=7, loc="lower right")
    axes[-1].set(
        xlim=(0, 24),
        xlabel="UTC hour; points are scan witnesses, no interpolation between passes",
        xticks=range(0, 25, 3),
    )
    fig.suptitle("Five purpose-selected method witnesses: gaps remain unknown, no labels")
    fig.savefig(out / "review_timelines.png", dpi=150)
    plt.close(fig)
    require(
        all(digest(ROOT / name) == sha for name, sha in pins.items()),
        "Final protocol input closure",
    )
    queue.write_json(out / "input_manifest.json", pins)
    result = {
        "status": "time_quality_protocol_evidence_only_not_label_acceptance",
        "parent_sha256": PARENT_SHA,
        "unit_count": len(table),
        "six_hour_rows": len(bins),
        "input_file_count": len(pins),
        "source_pair_count": len(frames),
        "thermal_definite_units": int(table.thermal_center_definite_count.gt(0).sum()),
        "thermal_boundary_units": int(table.thermal_center_boundary_count.gt(0).sum()),
        "largest_anypart_land_gap_hours": float(
            table.anypart_land_longest_envelope_gap_seconds.max() / 3600
        ),
        "median_anypart_land_gap_hours": float(
            table.anypart_land_longest_envelope_gap_seconds.median() / 3600
        ),
        "all_four_bins_positive_units": int(table.nominal_land_all_four_bins_m2.gt(0).sum()),
        "original_selection_group_window_disagreements": int(
            (
                table.signal_group.eq("thermal_center_present")
                != table.thermal_center_definite_count.gt(0)
            ).sum()
        ),
        "network_bytes": 0,
        "cloud_jobs_started": 0,
        "native_raw_arrays_read": 0,
        "inherited_native_files_hashed_only": sum(
            Path(name).suffix in {".nc", ".h5"} for name in pins
        ),
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "labels_created": False,
        "model_ready": False,
        "final_merge_performed": False,
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir() if p.is_file()},
    }
    queue.write_json(out / "readback.json", result)
    queue.write_json(
        out / "completion_readback.json",
        {"status": "passed_not_label_acceptance", "report_sha256": digest(out / "readback.json")},
    )
    print(out.relative_to(ROOT).as_posix(), flush=True)


if __name__ == "__main__":
    run()
