"""Boundary-offset scenarios for existing approximate training polygons; no labels.

Offsets are EPSG:6933 coordinate metres, not calibrated ground-error bounds.
Neighboring coverage is unioned before buffering, avoiding false analysis-cell edges.
The common comparison domain excludes AOI borders by the largest offset.
Finite buffer approximations can vary with local/global geometric decomposition;
the separate global-reference readback records rather than hides differences.
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
OFFSETS = (-100, -50, -25, 0, 25, 50, 100)


def scenario_areas(regions, coverage, offsets):
    """Compare offsets within one common domain; preserve holes and empty regions."""
    offsets = np.asarray(offsets, dtype="float64")
    audit.require(
        offsets.ndim == 1
        and len(offsets) > 0
        and np.isfinite(offsets).all()
        and (np.diff(offsets) > 0).all()
        and 0 in offsets,
        "Need finite, increasing offsets including zero",
    )
    regions, coverage = np.asarray(regions, dtype=object), np.asarray(coverage, dtype=object)
    audit.require(
        len(regions) > 0
        and len(regions) == len(coverage)
        and shapely.is_valid(regions).all()
        and shapely.is_valid(coverage).all(),
        "Invalid or unmatched geometries",
    )
    audit.require((shapely.area(regions) > 0).all(), "Empty analysis region")
    audit.require(
        (shapely.area(shapely.difference(coverage, regions)) <= 0.01).all(),
        "Coverage outside its analysis region",
    )
    domain = shapely.union_all(regions)
    audit.require(
        abs(domain.area - shapely.area(regions).sum()) < 0.1,
        "Analysis regions overlap",
    )
    margin = float(np.abs(offsets).max())
    comparison_domain = domain.buffer(-margin, quad_segs=16) if margin else domain
    audit.require(not comparison_domain.is_empty, "No AOI interior for these offsets")
    # The AOI has few components; retain its exact comparison geometry per cell.
    comparison_parts = shapely.intersection(regions, comparison_domain)
    denominator = shapely.area(comparison_parts)
    values = np.zeros((len(offsets), len(regions)), dtype="float64")
    tree = shapely.STRtree(coverage)
    for index, region in enumerate(comparison_parts):
        if region.is_empty:
            continue
        west, south, east, north = region.bounds
        # Crop only beyond the largest possible influence distance. The additional
        # metre keeps every comparison point strictly away from artificial edges.
        halo = shapely.box(
            west - margin - 1, south - margin - 1, east + margin + 1, north + margin + 1
        )
        neighbors = tree.query(halo, predicate="intersects")
        if not len(neighbors):
            continue
        local = shapely.union_all(shapely.intersection(coverage[neighbors], halo))
        for scenario, offset in enumerate(offsets):
            shifted = local if offset == 0 else local.buffer(float(offset), quad_segs=16)
            audit.require(shapely.is_valid(shifted), "Invalid shifted coverage")
            values[scenario, index] = region.intersection(shifted).area
    audit.require(
        (values >= 0).all() and (values <= denominator + 0.01).all(), "Area outside domain"
    )
    audit.require((np.diff(values, axis=0) >= -0.01).all(), "Offsets are not monotonic")
    return denominator, values


def main():
    parts_path, parts = area.load_parts()
    report_path = audit.OUTPUT / f"{STEM}.json"
    geometry_path = audit.OUTPUT / f"{STEM}.gpkg"
    table_path = audit.OUTPUT / f"{STEM}.csv"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    audit.require(report["day_utc"] == "2019-01-14", "Wrong training day")
    audit.require(report["method"] == area.METHOD, "Unexpected area method")
    audit.require(
        report["daily_observation_status"] == "unknown"
        and report["negative_label_permitted"] is False,
        "Unexpected label policy",
    )
    audit.require(report["grid_count"] == len(parts), "Grid count differs")
    audit.require(
        report["geometry_sha256"] == audit.digest(geometry_path)
        and report["area_csv_sha256"] == audit.digest(table_path),
        "Changed union output",
    )
    for source in report["sources"].values():
        audit.require(source["aoi_parts_sha256"] == audit.digest(parts_path), "Changed AOI")
    frame = gpd.read_file(geometry_path, layer="nominal_nonfire_land")
    audit.require(frame.crs.to_epsg() == 6933, "Wrong projection")
    audit.require(
        frame.grid_id.is_unique and set(frame.grid_id) == set(parts.grid_id), "Wrong geometry keys"
    )
    frame = frame.set_index("grid_id").loc[parts.grid_id]
    saved = pd.read_csv(table_path)
    audit.require(
        saved.grid_id.is_unique and set(saved.grid_id) == set(parts.grid_id), "Wrong CSV keys"
    )
    saved = saved.set_index("grid_id").loc[parts.grid_id]
    audit.require(
        saved.negative_label_permitted.eq(False).all()
        and saved.daily_observation_status.eq("unknown").all()
        and saved.method.eq(area.METHOD).all(),
        "Unexpected saved label policy",
    )
    audit.require(
        np.allclose(
            frame.geometry.area, saved.nominal_nonfire_land_area_estimate_m2, rtol=1e-10, atol=0.01
        ),
        "Geometry/CSV mismatch",
    )
    baseline_area = float(frame.geometry.area.sum())
    audit.require(
        abs(baseline_area / 1e6 - report["area_estimate_km2"]["nominal_nonfire_land"]) < 1e-6,
        "Original area summary mismatch",
    )
    source_paths = (parts_path, report_path, geometry_path, table_path)
    before = {str(p.relative_to(audit.ROOT)): audit.digest(p) for p in source_paths}
    print("Computing neighbor-union offset scenarios within a common AOI interior...", flush=True)
    denominator, values = scenario_areas(
        parts.geometry.to_numpy(), frame.geometry.to_numpy(), OFFSETS
    )
    baseline = values[OFFSETS.index(0)]
    output = pd.DataFrame({"grid_id": parts.grid_id, "comparison_area_m2": denominator})
    scenarios = []
    for offset, observed in zip(OFFSETS, values, strict=True):
        name = f"offset_{offset:+d}_m"
        fractions = np.divide(
            observed, denominator, out=np.full(len(parts), np.nan), where=denominator > 0
        )
        output[f"{name}_area_m2"] = observed
        output[f"{name}_fraction"] = fractions
        scenarios.append(
            {
                "offset_projected_m": offset,
                "area_km2": float(observed.sum() / 1e6),
                "comparison_domain_fraction": float(observed.sum() / denominator.sum()),
                "change_from_zero_km2": float((observed - baseline).sum() / 1e6),
                "cells_changed_over_1_m2": int((abs(observed - baseline) > 1).sum()),
                "max_cell_fraction_change": float(
                    np.nanmax(
                        abs(
                            np.divide(
                                observed - baseline,
                                denominator,
                                out=np.full(len(parts), np.nan),
                                where=denominator > 0,
                            )
                        )
                    )
                ),
            }
        )
    output["daily_observation_status"] = "unknown"
    output["negative_label_permitted"] = False
    destination = audit.OUTPUT / "area_boundary_sensitivity_2019-01-14.csv"
    output.to_csv(destination, index=False)
    reread = pd.read_csv(destination)
    audit.require(reread.grid_id.tolist() == output.grid_id.tolist(), "Saved grid keys differ")
    for name in output.select_dtypes(include="number").columns:
        audit.require(
            np.allclose(reread[name], output[name], equal_nan=True, rtol=1e-12, atol=1e-6),
            "Saved numeric values differ",
        )
    audit.require(reread.negative_label_permitted.eq(False).all(), "Saved label permission")
    audit.require(reread.daily_observation_status.eq("unknown").all(), "Saved daily status")
    audit.require(
        before == {str(p.relative_to(audit.ROOT)): audit.digest(p) for p in source_paths},
        "Source changed during analysis",
    )
    result = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "status": "projected_boundary_scenarios_only",
        "day_utc": "2019-01-14",
        "grid_count": len(parts),
        "offset_units": "EPSG:6933 coordinate metres, not ground-error distances",
        "original_nominal_nonfire_area_km2": baseline_area / 1e6,
        "comparison_domain_area_km2": float(denominator.sum() / 1e6),
        "excluded_aoi_border_area_km2": float(
            (parts.geometry.area.sum() - denominator.sum()) / 1e6
        ),
        "cells_without_comparison_interior": int((denominator == 0).sum()),
        "scenarios": scenarios,
        "source_sha256": before,
        "script_sha256": audit.digest(Path(__file__)),
        "csv_sha256": audit.digest(destination),
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "limitations": [
            "Offsets are exploratory scenarios, not calibrated errors or confidence intervals",
            "Union shifted after scanning; not a per-pixel physical footprint perturbation",
            "Equal-area CRS does not preserve all ground distances",
            "AOI boundary strip excluded consistently; outside-AOI coverage remains unknown",
            "No thresholds, vegetation denominator, temporal coverage or labels selected",
            "One existing training day; no seasonal or full-period representativeness claim",
        ],
    }
    result_path = audit.OUTPUT / "area_boundary_sensitivity_2019-01-14.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Report: {result_path}", flush=True)


if __name__ == "__main__":
    main()
