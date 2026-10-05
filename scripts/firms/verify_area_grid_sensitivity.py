"""Read back every diagnostic column and independently reconstruct selected rasters."""

import importlib.util
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import shapely
from shapely.geometry import Point, box
from shapely.ops import unary_union
from shapely.prepared import prep

SPEC = importlib.util.spec_from_file_location(
    "grid_diagnostic", Path(__file__).with_name("check_area_grid_sensitivity.py")
)
grid = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(grid)
audit = grid.audit


def reference_area(region, coverage, resolution, phase):
    """Scalar points + union of selected squares; no production sampling helper."""
    if region.is_empty or coverage.is_empty:
        return 0.0
    west, south, east, north = region.bounds
    x0, y0 = (p * resolution for p in phase)
    prepared = prep(coverage)
    selected = []
    for ix in range(math.floor((west - x0) / resolution), math.ceil((east - x0) / resolution)):
        for iy in range(
            math.floor((south - y0) / resolution), math.ceil((north - y0) / resolution)
        ):
            left, bottom = x0 + ix * resolution, y0 + iy * resolution
            if prepared.covers(Point(left + resolution / 2, bottom + resolution / 2)):
                selected.append(box(left, bottom, left + resolution, bottom + resolution))
    return unary_union(selected).intersection(region).area if selected else 0.0


def require_close(actual, expected, name, atol=1e-6):
    audit.require(np.allclose(actual, expected, rtol=1e-11, atol=atol, equal_nan=True), name)


def main():
    parts, coverage, sources = grid.load_training_union()
    report_path = audit.OUTPUT / "area_grid_sensitivity_2019-01-14.json"
    csv_path = audit.OUTPUT / "area_grid_sensitivity_2019-01-14.csv"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    audit.require(report["script_sha256"] == audit.digest(Path(grid.__file__)), "Stale code")
    audit.require(report["csv_sha256"] == audit.digest(csv_path), "Changed result CSV")
    audit.require(report["source_sha256"] == sources, "Source identity differs")
    audit.require(
        report["status"] == "approximate_polygon_centre_sampling_diagnostic_only"
        and report["day_utc"] == "2019-01-14"
        and report["negative_label_permitted"] is False
        and report["daily_observation_status"] == "unknown",
        "Unexpected report policy",
    )
    audit.require(
        report["resolutions_projected_m"] == list(grid.RESOLUTIONS)
        and report["origin_fractions"] == [list(p) for p in grid.PHASES]
        and report["aoi_comparison_margin_projected_m"] == grid.COMPARISON_MARGIN_M
        and report["centre_boundary_convention"] == "closed polygon (intersects_xy)",
        "Unexpected scenario definition",
    )
    table = pd.read_csv(csv_path)
    audit.require(table.grid_id.tolist() == parts.grid_id.tolist(), "Wrong saved grid order")
    audit.require(
        table.negative_label_permitted.eq(False).all()
        and table.daily_observation_status.eq("unknown").all(),
        "Unexpected CSV policy",
    )
    domain = unary_union(parts.geometry.to_list())
    interior = domain.buffer(-grid.COMPARISON_MARGIN_M, quad_segs=16)
    regions = shapely.intersection(parts.geometry.to_numpy(), interior)
    denominator, exact = (
        shapely.area(regions),
        shapely.area(shapely.intersection(regions, coverage)),
    )
    valid = denominator > 0
    fraction = np.divide(exact, denominator, out=np.full(len(parts), np.nan), where=valid)
    require_close(table.comparison_area_m2, denominator, "Wrong denominators")
    require_close(table.vector_area_m2, exact, "Wrong vector areas")
    require_close(table.vector_fraction, fraction, "Wrong vector fractions", atol=1e-12)
    require_close(report["comparison_domain_area_km2"], denominator.sum() / 1e6, "Wrong domain")
    require_close(report["vector_baseline_area_km2"], exact.sum() / 1e6, "Wrong baseline")
    require_close(
        report["vector_baseline_fraction"], exact.sum() / denominator.sum(), "Wrong fraction"
    )
    require_close(
        report["excluded_aoi_border_area_km2"],
        domain.area / 1e6 - denominator.sum() / 1e6,
        "Wrong excluded border area",
    )
    audit.require(
        report["cells_without_comparison_interior"] == int((~valid).sum()), "Missing cells"
    )
    audit.require(report["grid_count"] == len(parts), "Wrong count")
    combinations = [(r, p) for r in grid.RESOLUTIONS for p in grid.PHASES]
    expected_columns = ["grid_id", "comparison_area_m2", "vector_area_m2", "vector_fraction"]
    for resolution, phase in combinations:
        name = f"r{resolution}_phase{int(phase[0] * 2)}{int(phase[1] * 2)}"
        expected_columns.extend([f"{name}_area_m2", f"{name}_fraction"])
    expected_columns.extend(f"r{r}_origin_range_fraction" for r in grid.RESOLUTIONS)
    expected_columns.extend(["daily_observation_status", "negative_label_permitted"])
    audit.require(table.columns.tolist() == expected_columns, "Unexpected saved schema")
    audit.require(len(report["scenarios"]) == len(combinations), "Missing scenarios")
    candidates, arrays = [], {}
    for summary, (resolution, phase) in zip(report["scenarios"], combinations, strict=True):
        name = f"r{resolution}_phase{int(phase[0] * 2)}{int(phase[1] * 2)}"
        observed = table[f"{name}_area_m2"].to_numpy()
        actual_fraction = np.divide(
            observed, denominator, out=np.full(len(parts), np.nan), where=valid
        )
        audit.require(
            np.isfinite(observed).all()
            and (observed >= 0).all()
            and (observed <= denominator + 0.01).all(),
            "Wrong area range",
        )
        require_close(
            table[f"{name}_fraction"], actual_fraction, "Wrong sampled fraction", atol=1e-12
        )
        audit.require(
            summary["resolution_projected_m"] == resolution
            and summary["origin_fraction"] == list(phase),
            "Wrong scenario identity",
        )
        require_close(summary["area_km2"], observed.sum() / 1e6, "Wrong scenario sum")
        require_close(
            summary["comparison_domain_fraction"], observed.sum() / denominator.sum(), "Wrong share"
        )
        require_close(
            summary["signed_area_difference_from_vector_km2"],
            (observed - exact).sum() / 1e6,
            "Wrong signed error",
        )
        require_close(
            summary["sum_cell_absolute_area_difference_km2"],
            abs(observed - exact).sum() / 1e6,
            "Wrong absolute error",
        )
        errors = abs(actual_fraction[valid] - fraction[valid])
        audit.require(
            set(summary["cell_absolute_fraction_error_quantiles"])
            == {"0.5", "0.95", "0.99", "1.0"},
            "Missing error quantiles",
        )
        for q, value in summary["cell_absolute_fraction_error_quantiles"].items():
            require_close(value, np.quantile(errors, float(q)), "Wrong error quantiles", atol=1e-12)
        arrays.setdefault(resolution, []).append(observed)
        if phase == (0, 0):
            candidates.append((int(np.argmax(abs(observed - exact))), resolution, phase))
    for summary, resolution in zip(report["origin_sensitivity"], grid.RESOLUTIONS, strict=True):
        values = np.asarray(arrays[resolution])
        ranges = np.divide(
            np.ptp(values, axis=0), denominator, out=np.full(len(parts), np.nan), where=valid
        )
        require_close(
            table[f"r{resolution}_origin_range_fraction"], ranges, "Wrong phase range", atol=1e-12
        )
        require_close(
            summary["total_area_origin_range_km2"],
            np.ptp(values.sum(axis=1)) / 1e6,
            "Wrong total phase range",
        )
        for q, value in summary["cell_fraction_origin_range_quantiles"].items():
            require_close(
                value, np.quantile(ranges[valid], float(q)), "Wrong phase quantiles", atol=1e-12
            )
        audit.require(
            summary["resolution_projected_m"] == resolution
            and set(summary["cell_fraction_origin_range_quantiles"])
            == {"0.5", "0.95", "0.99", "1.0"},
            "Wrong phase summary identity or quantiles",
        )
    coarse = table.r200_phase11_fraction.to_numpy()
    candidates.append((int(np.nanargmax(abs(coarse - fraction))), 200, (0.5, 0.5)))
    for state in (exact == 0, np.isclose(exact, denominator, atol=0.01, rtol=0)):
        indices = np.flatnonzero(state & valid)
        if len(indices):
            candidates.append((int(indices[0]), 100, (0.5, 0)))
    tree, controls = shapely.STRtree(coverage), []
    for index, resolution, phase in sorted(set(candidates)):
        region = regions[index]
        west, south, east, north = region.bounds
        halo = box(west - 200, south - 200, east + 200, north + 200)
        neighbors = tree.query(halo, predicate="intersects")
        local = unary_union([coverage[i].intersection(halo) for i in neighbors])
        expected = reference_area(region, local, resolution, phase)
        name = f"r{resolution}_phase{int(phase[0] * 2)}{int(phase[1] * 2)}_area_m2"
        actual = float(table.iloc[index][name])
        require_close(
            actual, expected, "Independent square-union reconstruction differs", atol=0.01
        )
        controls.append(
            {
                "grid_id": parts.iloc[index].grid_id,
                "resolution_m": resolution,
                "phase": phase,
                "difference_m2": actual - expected,
            }
        )
    # Stratify by actual rectangular geometry, without a minimum-area eligibility rule.
    rectangles = np.zeros(len(regions), dtype=bool)
    for index in np.flatnonzero(valid):
        rectangles[index] = regions[index].equals(box(*regions[index].bounds))
    rectangular_summaries = []
    for resolution in grid.RESOLUTIONS:
        values = table.loc[rectangles, f"r{resolution}_origin_range_fraction"]
        rectangular_summaries.append(
            {
                "resolution_projected_m": resolution,
                "cell_count": int(rectangles.sum()),
                "origin_range_quantiles": {
                    str(q): float(values.quantile(q)) for q in (0.5, 0.95, 0.99, 1.0)
                },
            }
        )
    audit.require(sources == {p: audit.digest(audit.ROOT / p) for p in sources}, "Source changed")
    result = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "status": "all_columns_readback_and_selected_square_unions_verified",
        "grid_count": len(parts),
        "scenario_count": len(combinations),
        "independent_controls": controls,
        "rectangular_comparison_region_diagnostics": rectangular_summaries,
        "report_sha256": audit.digest(report_path),
        "csv_sha256": audit.digest(csv_path),
        "source_sha256": sources,
        "verifier_sha256": audit.digest(Path(__file__)),
        "negative_label_permitted": False,
        "limitation": "Computational diagnostic verification, not physical coverage validation",
    }
    destination = audit.OUTPUT / "area_grid_sensitivity_readback.json"
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
