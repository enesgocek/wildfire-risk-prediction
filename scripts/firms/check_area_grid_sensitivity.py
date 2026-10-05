"""Raster centre sampling of approximate training polygons, never final labels.

Diagnostic only: does not resample the native VIIRS radiometry or certify IFOV.
Use a fixed EPSG:6933 lattice, exact AOI-interior denominators, four origins,
and area-weighted intersections for cells crossing analysis-grid boundaries.
"""

import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

SPEC = importlib.util.spec_from_file_location(
    "area", Path(__file__).with_name("estimate_l2_observed_area.py")
)
area = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(area)
audit = area.audit
STEM = "l2_area_union_2019-01-14_SNPP_N20_8samples"
RESOLUTIONS = (50, 100, 200)
PHASES = ((0.0, 0.0), (0.5, 0.0), (0.0, 0.5), (0.5, 0.5))
COMPARISON_MARGIN_M = 300


def sampled_area(region, coverage, resolution, phase):
    """Closed-polygon centre membership, weighted by exact region intersection."""
    phase = np.asarray(phase, dtype="float64")
    audit.require(
        np.isfinite(resolution)
        and resolution > 0
        and phase.shape == (2,)
        and np.isfinite(phase).all()
        and ((phase >= 0) & (phase < 1)).all(),
        "Invalid resolution or lattice phase",
    )
    audit.require(shapely.is_valid(region) and shapely.is_valid(coverage), "Invalid geometry")
    if region.is_empty or coverage.is_empty:
        return 0.0
    west, south, east, north = region.bounds
    origin_x, origin_y = phase * resolution
    first_x = int(np.floor((west - origin_x) / resolution))
    last_x = int(np.ceil((east - origin_x) / resolution))
    first_y = int(np.floor((south - origin_y) / resolution))
    last_y = int(np.ceil((north - origin_y) / resolution))
    audit.require(
        (last_x - first_x) * (last_y - first_y) <= 1_000_000,
        "Too many lattice cells for one diagnostic region",
    )
    x, y = np.meshgrid(
        origin_x + (np.arange(first_x, last_x) + 0.5) * resolution,
        origin_y + (np.arange(first_y, last_y) + 0.5) * resolution,
    )
    shapely.prepare(coverage)
    selected = shapely.intersects_xy(coverage, x.ravel(), y.ravel())
    x, y = x.ravel()[selected], y.ravel()[selected]
    if not len(x):
        return 0.0
    half = resolution / 2
    squares = shapely.box(x - half, y - half, x + half, y + half)
    shapely.prepare(region)
    full = shapely.contains(region, squares)
    result = float(full.sum() * resolution**2)
    if (~full).any():
        result += float(shapely.area(shapely.intersection(squares[~full], region)).sum())
    audit.require(0 <= result <= region.area + 0.01, "Sample area exceeds region")
    return result


def load_training_union():
    parts_path, parts = area.load_parts()
    report_path = audit.OUTPUT / f"{STEM}.json"
    geometry_path = audit.OUTPUT / f"{STEM}.gpkg"
    csv_path = audit.OUTPUT / f"{STEM}.csv"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    audit.require(report["day_utc"] == "2019-01-14", "Wrong training sample")
    audit.require(report["method"] == area.METHOD, "Unexpected geometry method")
    audit.require(
        report["negative_label_permitted"] is False
        and report["daily_observation_status"] == "unknown",
        "Unexpected label policy",
    )
    audit.require(report["grid_count"] == len(parts), "Changed grid count")
    audit.require(
        report["geometry_sha256"] == audit.digest(geometry_path)
        and report["area_csv_sha256"] == audit.digest(csv_path),
        "Changed union outputs",
    )
    for source in report["sources"].values():
        audit.require(source["aoi_parts_sha256"] == audit.digest(parts_path), "Changed AOI parts")
    frame = gpd.read_file(geometry_path, layer="nominal_nonfire_land")
    table = pd.read_csv(csv_path)
    audit.require(frame.crs.to_epsg() == 6933, "Wrong geometry CRS")
    for data in (frame, table):
        audit.require(
            data.grid_id.is_unique and set(data.grid_id) == set(parts.grid_id), "Wrong grid keys"
        )
    frame = frame.set_index("grid_id").loc[parts.grid_id]
    table = table.set_index("grid_id").loc[parts.grid_id]
    audit.require(
        table.negative_label_permitted.eq(False).all()
        and table.daily_observation_status.eq("unknown").all()
        and table.method.eq(area.METHOD).all(),
        "Unexpected CSV policy",
    )
    audit.require(shapely.is_valid(frame.geometry.to_numpy()).all(), "Invalid coverage geometry")
    audit.require(
        np.allclose(
            frame.geometry.area, table.nominal_nonfire_land_area_estimate_m2, rtol=1e-10, atol=0.01
        ),
        "Geometry/CSV mismatch",
    )
    audit.require(
        abs(frame.geometry.area.sum() / 1e6 - report["area_estimate_km2"]["nominal_nonfire_land"])
        < 1e-6,
        "Original area summary differs",
    )
    sources = {
        str(p.relative_to(audit.ROOT)): audit.digest(p)
        for p in (parts_path, report_path, geometry_path, csv_path)
    }
    return parts, frame.geometry.to_numpy(), sources


def main():
    parts, coverage, sources = load_training_union()
    audit.require(
        COMPARISON_MARGIN_M > max(RESOLUTIONS) / np.sqrt(2),
        "AOI margin does not isolate outside-AOI sample centres",
    )
    domain = shapely.union_all(parts.geometry.to_numpy())
    comparison_domain = domain.buffer(-COMPARISON_MARGIN_M, quad_segs=16)
    regions = shapely.intersection(parts.geometry.to_numpy(), comparison_domain)
    denominator = shapely.area(regions)
    exact = shapely.area(shapely.intersection(regions, coverage))
    audit.require(
        (shapely.area(shapely.difference(coverage, parts.geometry.to_numpy())) <= 0.01).all(),
        "Coverage outside its analysis cell",
    )
    valid = denominator > 0
    vector_fraction = np.divide(exact, denominator, out=np.full(len(parts), np.nan), where=valid)
    combinations = [(r, p) for r in RESOLUTIONS for p in PHASES]
    values = np.zeros((len(combinations), len(parts)), dtype="float64")
    tree = shapely.STRtree(coverage)
    margin = max(RESOLUTIONS)
    for index, region in enumerate(regions):
        if not region.is_empty:
            west, south, east, north = region.bounds
            # Neighbour pieces are required when a fine-cell centre lies across
            # the 5-km analysis-cell border. No per-analysis-cell raster origin.
            halo = shapely.box(west - margin, south - margin, east + margin, north + margin)
            neighbors = tree.query(halo, predicate="intersects")
            local = shapely.union_all(shapely.intersection(coverage[neighbors], halo))
            for scenario, (resolution, phase) in enumerate(combinations):
                values[scenario, index] = sampled_area(region, local, resolution, phase)
        if (index + 1) % 250 == 0 or index + 1 == len(parts):
            print(f"Raster comparison: {index + 1}/{len(parts)} regions", flush=True)
    result = pd.DataFrame(
        {
            "grid_id": parts.grid_id,
            "comparison_area_m2": denominator,
            "vector_area_m2": exact,
            "vector_fraction": vector_fraction,
        }
    )
    summaries, spread = [], []
    for scenario, (resolution, phase) in enumerate(combinations):
        observed = values[scenario]
        fraction = np.divide(observed, denominator, out=np.full(len(parts), np.nan), where=valid)
        name = f"r{resolution}_phase{int(phase[0] * 2)}{int(phase[1] * 2)}"
        result[f"{name}_area_m2"] = observed
        result[f"{name}_fraction"] = fraction
        errors = abs(fraction[valid] - vector_fraction[valid])
        summaries.append(
            {
                "resolution_projected_m": resolution,
                "origin_fraction": list(phase),
                "area_km2": float(observed.sum() / 1e6),
                "comparison_domain_fraction": float(observed.sum() / denominator.sum()),
                "signed_area_difference_from_vector_km2": float((observed - exact).sum() / 1e6),
                "sum_cell_absolute_area_difference_km2": float(abs(observed - exact).sum() / 1e6),
                "cell_absolute_fraction_error_quantiles": {
                    str(q): float(np.quantile(errors, q)) for q in (0.5, 0.95, 0.99, 1.0)
                },
            }
        )
    for resolution in RESOLUTIONS:
        selected = values[[i for i, (r, _) in enumerate(combinations) if r == resolution]]
        difference = selected.max(axis=0) - selected.min(axis=0)
        fraction_range = np.divide(
            difference, denominator, out=np.full(len(parts), np.nan), where=valid
        )
        result[f"r{resolution}_origin_range_fraction"] = fraction_range
        spread.append(
            {
                "resolution_projected_m": resolution,
                "total_area_origin_range_km2": float(np.ptp(selected.sum(axis=1)) / 1e6),
                "cell_fraction_origin_range_quantiles": {
                    str(q): float(np.quantile(fraction_range[valid], q))
                    for q in (0.5, 0.95, 0.99, 1.0)
                },
            }
        )
    result["daily_observation_status"] = "unknown"
    result["negative_label_permitted"] = False
    csv_path = audit.OUTPUT / "area_grid_sensitivity_2019-01-14.csv"
    result.to_csv(csv_path, index=False)
    reread = pd.read_csv(csv_path)
    audit.require(reread.grid_id.tolist() == result.grid_id.tolist(), "Saved keys differ")
    for field in result.select_dtypes(include="number").columns:
        audit.require(
            np.allclose(reread[field], result[field], rtol=1e-12, atol=1e-6, equal_nan=True),
            "Saved numeric values differ",
        )
    audit.require(
        reread.negative_label_permitted.eq(False).all()
        and reread.daily_observation_status.eq("unknown").all(),
        "Saved labels differ",
    )
    audit.require(
        sources == {p: audit.digest(audit.ROOT / p) for p in sources},
        "Source changed during comparison",
    )
    report = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "status": "approximate_polygon_centre_sampling_diagnostic_only",
        "day_utc": "2019-01-14",
        "grid_count": len(parts),
        "resolutions_projected_m": list(RESOLUTIONS),
        "origin_fractions": PHASES,
        "centre_boundary_convention": "closed polygon (intersects_xy)",
        "aoi_comparison_margin_projected_m": COMPARISON_MARGIN_M,
        "comparison_domain_area_km2": float(denominator.sum() / 1e6),
        "excluded_aoi_border_area_km2": float(domain.area / 1e6 - denominator.sum() / 1e6),
        "cells_without_comparison_interior": int((~valid).sum()),
        "vector_baseline_area_km2": float(exact.sum() / 1e6),
        "vector_baseline_fraction": float(exact.sum() / denominator.sum()),
        "scenarios": summaries,
        "origin_sensitivity": spread,
        "source_sha256": sources,
        "script_sha256": audit.digest(Path(__file__)),
        "csv_sha256": audit.digest(csv_path),
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "limitations": [
            "Samples existing approximate polygon union, not native VIIRS arrays or physical IFOV",
            "Binary centre membership has aliasing; exact fractional raster-cell AOI weights used",
            "Same AOI interior and exact denominator for every scenario; outer strip excluded",
            "EPSG:6933 coordinate metres are not ground-distance accuracy claims",
            "No production resolution, origin, eligibility threshold or negative labels selected",
            "One winter training day; no seasonal or full-period representativeness claim",
        ],
    }
    destination = audit.OUTPUT / "area_grid_sensitivity_2019-01-14.json"
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Report: {destination}", flush=True)


if __name__ == "__main__":
    main()
