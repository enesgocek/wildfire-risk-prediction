"""Compare recorded thermal groups and mapped areas without assigning fire labels."""

import csv
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import geopandas as gpd
import numpy as np
import pandas as pd
from affine import Affine
from audit_menderes_burn_signal import PRIOR as HONA
from audit_menderes_burn_signal import PRIOR_SHA as HONA_SHA
from audit_menderes_patch_context import EFFIS_RESULTS, PINS
from prepare_pu_calendar_sample import digest
from pyproj import Transformer
from rasterio.features import shapes
from review_anamur_burn_signal import EPSG as ANAMUR_CRS
from review_anamur_burn_signal import SOURCE as ANAMUR_COVER
from review_anamur_burn_signal import SOURCE_SHA as ANAMUR_COVER_SHA
from review_anamur_burn_signal import nbr
from review_anamur_preevent_cover import CASE_RECEIPT, CASE_SHA
from review_manavgat_reported_starts import CATALOG, PARTS
from review_three_province_start_context import CATALOG_SHA
from run_stratified_cover_pilot import BASE, ROOT, read_json, write_json
from shapely import contains_xy, segmentize
from shapely.geometry import Point, shape
from shapely.ops import transform

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.observation_window_source import PARTS_SHA
from wildfire_risk_prediction.perimeter_review import effis_gml
from wildfire_risk_prediction.target_admission import (
    assert_targets_unassigned,
    detection_windows,
    specification,
)

ANAMUR_SCAN = BASE / "anamur_observation_windows_v1/20261108T033344Z_46e15ad3/readback.json"
ANAMUR_BURN = BASE / "anamur_burn_signal_v1/20261108T032607Z_71a08960/readback.json"
MENDERES_PATCH = BASE / "menderes_patch_context_v1/20261108T042450Z_308aaf99/readback.json"
SOURCES = {
    HONA: HONA_SHA,
    ANAMUR_SCAN: "34a0a2eafa99dcf66f9cd813a8f6c8d6125e99216d24c0600f8d79a117c885f6",
    ANAMUR_BURN: "9ea89af5489310a5baa5f089605f87746a469ec54331a191f3b64f7ba59043e9",
    MENDERES_PATCH: "ba4ec1b522a81e1077df9e1f3b8a5951370c6e01d67c1d8930ceddb8ece9c22d",
    ANAMUR_COVER: ANAMUR_COVER_SHA,
    CASE_RECEIPT: CASE_SHA,
    ROOT / CATALOG: CATALOG_SHA,
    ROOT / PARTS: PARTS_SHA,
    EFFIS_RESULTS: PINS[EFFIS_RESULTS],
}


def menderes_members(hona, pins):
    """Recover the 14 already reconciled signatures, then inspect entire components."""
    expected = Counter(
        {
            (grid, row["sensor"], row["utc"]): row["catalogue"]
            for grid, review in hona["whole_cell_scan_comparison"].items()
            for row in review["minutes"]
        }
    )
    require(
        all(
            review["same_sensor_minute_counts"]
            and review["window"]["loaded_boundary_scan_rows"] == 0
            for review in hona["whole_cell_scan_comparison"].values()
        ),
        "Previously reconciled Menderes cell-minute signatures",
    )
    actual, selected = Counter(), {}
    with (ROOT / CATALOG).open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            stamp = row["detection_timestamp_utc"]
            if not stamp.startswith("2023-07-10"):
                continue
            key = row["grid_id"], row["source_sensor"], pd.Timestamp(stamp).isoformat()
            if key in expected:
                actual[key] += 1
                selected[row["detection_id"]] = "north" if key[0].endswith("C525_R906") else "south"
    require(
        actual == expected and len(selected) == hona["selected_count"] == 14, "14 selected rows"
    )
    sizes = Counter(selected.values())
    results = {}
    for setting in hona["groupings"]:
        name = f"data/interim/event_grouping/{setting}_assignments.csv"
        pins[ROOT / name] = hona["input_sha256"][name]
        require(digest(ROOT / name) == pins[ROOT / name], "Frozen full component assignments")
        rows = pd.read_csv(
            ROOT / name, usecols=["detection_id", "grid_id", "timestamp", "cluster_id"]
        )
        selection = rows.loc[rows.detection_id.isin(selected)]
        require(
            len(selection) == len(selected)
            and selection.detection_id.is_unique
            and selection.cluster_id.nunique() == 2,
            "Two distinct components for the selected Menderes detections",
        )
        results[setting] = {}
        for group, ids in selection.groupby(selection.detection_id.map(selected)):
            require(
                len(ids) == sizes[group] and ids.cluster_id.nunique() == 1, "Selection membership"
            )
            cluster = rows.loc[rows.cluster_id.eq(ids.cluster_id.iloc[0])]
            stamps = pd.to_datetime(cluster.timestamp, utc=True, format="ISO8601")
            first = stamps.min()
            results[setting][group] = {
                "members": len(cluster),
                "additional_members": len(cluster) - len(ids),
                "first_detection_utc": first.isoformat(),
                "first_grid_ids": sorted(cluster.loc[stamps.eq(first), "grid_id"].unique()),
                "last_detection_utc": stamps.max().isoformat(),
            }
    return results


def anamur_change(pins):
    """Rebuild the previously measured 0.15 patch before intersecting the project grid."""
    previous = read_json(ANAMUR_BURN)
    before = read_json(ANAMUR_COVER)
    project = Transformer.from_crs(4326, ANAMUR_CRS, always_xy=True)
    centre = Point(*project.transform(*before["points"]["tespit_1"]["lon_lat"]))
    indexes = {}
    affine = Affine(*previous["scenes"]["jul07"]["transforms"]["SCL"])
    for day, scene in previous["scenes"].items():
        path = ANAMUR_BURN.with_name(f"{day}.npz")
        pins[path] = scene["crop_sha256"]
        require(
            digest(path) == pins[path] and Affine(*scene["transforms"]["SCL"]) == affine,
            "Verified aligned optical crop",
        )
        with np.load(path, allow_pickle=False) as data:
            indexes[day] = nbr(data, scene["calibration"])
    minimum = np.min([indexes[a] - indexes[b] for a, b in previous["pairs"]], axis=0)
    row, col = np.indices(minimum.shape)
    x, y = affine * (col + 0.5, row + 0.5)
    mask = (minimum >= 0.15) & contains_xy(centre.buffer(previous["radius_m"]), x, y)
    polygons = [shape(g) for g, _ in shapes(mask.astype("uint8"), mask=mask, transform=affine)]
    largest = max(polygons, key=lambda g: g.area)
    require(
        largest.area == previous["all_pair_threshold_diagnostics"]["0.15"]["largest_connected_m2"],
        "Previously measured patch",
    )
    to_grid = Transformer.from_crs(ANAMUR_CRS, 6933, always_xy=True).transform
    return transform(to_grid, segmentize(largest, 10))


def intersect_cells(geometry, grid):
    clipped = grid.loc[grid.intersects(geometry)].copy()
    clipped["intersection_m2"] = clipped.intersection(geometry).area
    clipped = clipped.loc[clipped.intersection_m2.gt(0)].sort_values("grid_id")
    require(
        abs(clipped.intersection_m2.sum() / geometry.area - 1) < 1e-5, "Area within project cells"
    )
    return {row.grid_id: row.intersection_m2 / 10_000 for row in clipped.itertuples()}


def main():
    pins = SOURCES.copy()
    require(all(digest(path) == value for path, value in pins.items()), "Frozen evidence")
    hona, scan, patch = (read_json(path) for path in (HONA, ANAMUR_SCAN, MENDERES_PATCH))
    menderes = menderes_members(hona, pins)
    anamur = read_json(CASE_RECEIPT)["cases"]["anamur_belensazak_approximate"]
    groups = anamur["belensazak_2km_grouping"]["exploratory_scenarios"]
    require(groups.keys() == menderes.keys(), "Same nine settings")
    grid = gpd.read_file(ROOT / PARTS).to_crs(6933)
    require(grid.grid_id.is_unique, "Unique project cells")
    ref = effis_gml(EFFIS_RESULTS.read_bytes(), fire_date_window=("2023-07-09", "2023-07-13"))
    require(ref.reference_id.tolist() == [patch["effis"]["id"]], "Same EFFIS polygon")
    areas = {
        "menderes_effis": intersect_cells(ref.to_crs(6933).geometry.iloc[0], grid),
        "anamur_optical_0_15": intersect_cells(anamur_change(pins), grid),
    }

    windows = [row["window"] for row in hona["whole_cell_scan_comparison"].values()]
    windows.extend(scan["windows"])
    frame = pd.DataFrame(windows)
    assert_targets_unassigned(frame)
    require(
        frame.loaded_thermal_center_definite_count.gt(0).all()
        and not frame.duplicated(["grid_id", "prediction_timestamp_utc"]).any(),
        "Distinct thermal cell-days",
    )
    candidates = {}
    for setting, subsets in menderes.items():
        require(len(groups[setting]) == 1, "One Anamur component")
        firsts = {**subsets, "anamur": groups[setting][0]}
        mapped = detection_windows(
            pd.Series({k: v["first_detection_utc"] for k, v in firsts.items()})
        )
        candidates[setting] = {
            k: {
                "prediction_timestamp_utc": row.prediction_timestamp_utc.isoformat(),
                "first_grid_ids": firsts[k]["first_grid_ids"],
            }
            for k, row in mapped.iterrows()
        }
    pins[Path(__file__).resolve()] = digest(Path(__file__))
    out = (
        BASE
        / "july_case_admission_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    receipt = out / "readback.json"
    write_json(
        receipt,
        {
            "scope": "two_case_training_period_review_only",
            "inputs_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
            "menderes_full_components": menderes,
            "anamur_full_components": groups,
            "first_candidate_windows": candidates,
            "reference_intersections_ha": areas,
            "thermal_cell_days": frame[
                [
                    "grid_id",
                    "prediction_timestamp_utc",
                    "loaded_thermal_center_definite_count",
                    "target",
                ]
            ].to_dict("records"),
            "target_admission": specification(),
        },
    )
    print(receipt.relative_to(ROOT).as_posix(), digest(receipt))


if __name__ == "__main__":
    main()
