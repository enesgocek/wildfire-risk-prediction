"""Register a published start symbol; keep clipped-AOI misses and labels unassigned."""

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
from PIL import Image, ImageFilter
from pyproj import Transformer
from scipy.signal import fftconvolve
from shapely.geometry import MultiPoint, Point, Polygon
from shapely.ops import transform

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.event_review import GEOD, training_detections
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import detection_windows, specification

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
SOURCE = BASE / "L_expansion_sources_v1/20261119T122526Z_9d545fe4"
GRID = ROOT / "data/interim/grid_aoi_parts.geojson"
CATALOG = ROOT / "data/interim/firms_combined_candidates_2018_2024.csv"
REGISTRY = BASE / "mugla_public_extension_v1/20261119T002147Z_990adb00/readback.json"
ANNOUNCEMENT = BASE / "marmaris_public_map_access_v1/20261119T001353Z_bf53a8d1/announcement.html"
PINS = {
    SOURCE
    / "ercan_uygunol_2022.pdf": "82d1ddb27577c8da4aedbe9aafe7c3a519f5d3415d8f7e03f983d51edcb63537",
    SOURCE
    / "source_receipt.json": "9b38e60deab0f8761cfbfb09397f45942158fd05fb6399b3b0a3086dadf978b4",
    SOURCE / "page6.png": "45b2310f62645cc071bf85916fa61a7605483a1c8bbe322eb7fe3dd554936a43",
    SOURCE
    / "imagery_reference.png": "2d49ca323c8de01d9dad36f326c48443b028031809ce1f7573b98151916a7f59",
    SOURCE
    / "imagery_reference.json": "f9638ebbaf45df71bcabe4748aee0064891682b0ba80e159afb248c873645757",
    SOURCE / "egeorman_field_report_2022.pdf": (
        "0b41f3af4a794a8454ec559b1844364f916cab4645c42dedce34a97355c4865c"
    ),
    SOURCE / "field_report_receipt.json": (
        "615006b484a6b77c39c01fa7d98e13e7c6dd1f2bbe57f84799c83928c68b9564"
    ),
    SOURCE / "field_page20.png": "8e23ac325cba4218e70ca0a4e04f458b490bd1590884e862b9a6023775c99661",
    ANNOUNCEMENT: "3cb44323dea1990f2d7279d3c570e0b02451470d93f9f23ce73086299af30970",
    GRID: "f589f6027d28ce1911d080763e195062dcaaf4e9567fb4072d14c454bf28a2f9",
    CATALOG: "37ebb8e1f204b28faf2da21661ff6b0f8e9125c25876b7966df3ae9aea7551c5",
    REGISTRY: "671a6958e3b72b87b19dab944b85f48d911889b78a0a908dc8e7199bde75a83a",
}
MAP_RECT = (178, 550, 1199, 1123)  # Page 6, pdftoppm -scale-to 1900.
MARKER = np.array([18.0, 124.0])  # Yellow circle center, not the arrow's label end.
GLYPH_RADIUS_PX = 11  # Visible ink extent, NOT a location error bound.
PATCHES = (
    (885, 175, 995, 345),
    (520, 270, 630, 370),
    (70, 340, 190, 440),
    (210, 430, 330, 520),
    (805, 20, 970, 110),
    (140, 220, 235, 270),
    (0, 175, 70, 255),
)
REPORTED_START = pd.Timestamp("2022-06-21T17:02:00Z")  # Earlier pinned OGM context.


def high_pass(image):
    return np.asarray(image, float) - np.asarray(image.filter(ImageFilter.GaussianBlur(4)), float)


def register_patches(published, reference):
    """Narrow search after exploratory registration, without using any fire coordinates."""
    matches = []
    for i, bounds in enumerate(PATCHES):
        left = round(138 + 0.85 * bounds[0]) - 35
        top = round(163 + 0.85 * bounds[1]) - 35
        region = reference.crop(
            (left, top, round(138 + 0.85 * bounds[2]) + 35, round(163 + 0.85 * bounds[3]) + 35)
        )
        ref = high_pass(region)
        trials = []
        for sx in np.arange(0.80, 0.911, 0.01):
            for sy in np.arange(0.80, 0.911, 0.01):
                size = (round((bounds[2] - bounds[0]) * sx), round((bounds[3] - bounds[1]) * sy))
                patch = high_pass(published.crop(bounds).resize(size))
                patch -= patch.mean()
                ones = np.ones_like(patch)
                sums = fftconvolve(ref, ones, mode="valid")
                squares = fftconvolve(ref * ref, ones, mode="valid")
                numerator = fftconvolve(ref, patch[::-1, ::-1], mode="valid")
                variance = np.maximum(squares - sums * sums / patch.size, 1e-9)
                scores = numerator / np.sqrt(variance * np.sum(patch * patch))
                y, x = np.unravel_index(scores.argmax(), scores.shape)
                trials.append((float(scores[y, x]), size, left + int(x), top + int(y)))
        score, (width, height), x, y = max(trials)
        require(np.isfinite(score) and score > 0.35, "Patch match needs visual/technical review")
        matches.append(
            {
                "patch_id": i + 1,
                "source_box": list(bounds),
                "ncc": score,
                "source_center": [(bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2],
                "reference_center": [x + width / 2, y + height / 2],
                "reference_box": [x, y, x + width, y + height],
            }
        )
    return matches


def affine_fit(source, metric_reference, marker):
    """LOO agreement is registration consistency, never physical origin accuracy."""
    a = np.c_[source, np.ones(len(source))]
    require(len(source) >= 4 and np.linalg.matrix_rank(a) == 3, "Noncollinear controls required")
    coeff = np.linalg.lstsq(a, metric_reference, rcond=None)[0]
    v = np.r_[marker, 1]
    predicted = v @ coeff
    omitted, shifts = [], []
    for i in range(len(a)):
        part_a, part_b = np.delete(a, i, axis=0), np.delete(metric_reference, i, axis=0)
        require(np.linalg.matrix_rank(part_a) == 3, "Omitted controls must still span the map")
        part = np.linalg.lstsq(part_a, part_b, rcond=None)[0]
        omitted.append(float(np.linalg.norm(a[i] @ part - metric_reference[i])))
        shifts.append(float(np.linalg.norm(v @ part - predicted)))
    return coeff, {
        "marker_utm35": predicted.tolist(),
        "max_control_residual_m": float(np.linalg.norm(a @ coeff - metric_reference, axis=1).max()),
        "max_omitted_control_error_m": max(omitted),
        "max_marker_loo_shift_m": max(shifts),
        "marker_inside_control_hull": bool(MultiPoint(source).convex_hull.covers(Point(marker))),
        "is_physical_location_accuracy_bound": False,
    }


def covered_keys(grid, point):
    """Do not snap a symbol on water/outside clipped AOI to the closest land cell."""
    return sorted(grid.loc[grid.geometry.covers(point), "grid_id"].tolist())


def main():
    require(all(digest(p) == h for p, h in PINS.items()), "Pinned sources changed")
    metadata = json.loads((SOURCE / "imagery_reference.json").read_text())
    require(metadata["extent"]["spatialReference"]["latestWkid"] == 3857, "Reference CRS")
    require((metadata["width"], metadata["height"]) == (2200, 1800), "Pinned image geometry")
    published = Image.open(SOURCE / "page6.png").crop(MAP_RECT).convert("L")
    reference = Image.open(SOURCE / "imagery_reference.png").convert("L").resize((1100, 900))
    matches = register_patches(published, reference)
    extent = metadata["extent"]
    to_utm = Transformer.from_crs(3857, 32635, always_xy=True)
    to_wgs = Transformer.from_crs(32635, 4326, always_xy=True)
    to_grid = Transformer.from_crs(32635, 6933, always_xy=True).transform
    anchors = np.array([r["source_center"] for r in matches])
    pixels = np.array([r["reference_center"] for r in matches])
    xs = extent["xmin"] + pixels[:, 0] * (extent["xmax"] - extent["xmin"]) / 1100
    ys = extent["ymax"] - pixels[:, 1] * (extent["ymax"] - extent["ymin"]) / 900
    controls = np.array(to_utm.transform(xs, ys)).T
    grid = gpd.read_file(GRID).to_crs(6933)
    estimates = {}
    for name, ids in (("all_seven", list(range(7))), ("four_uncolored_regions", [0, 2, 3, 4])):
        coeff, fit = affine_fit(anchors[ids], controls[ids], MARKER)
        require(fit["max_omitted_control_error_m"] < 40, "Registration consistency needs review")
        xy = np.array(fit["marker_utm35"])
        point = transform(to_grid, Point(xy))
        angles = np.linspace(0, 2 * np.pi, 129)
        outline = MARKER + GLYPH_RADIUS_PX * np.c_[np.cos(angles), np.sin(angles)]
        glyph = transform(to_grid, Polygon(np.c_[outline, np.ones(len(outline))] @ coeff))
        estimates[name] = {
            **fit,
            "approximate_marker_lon_lat": list(to_wgs.transform(*xy)),
            "center_AOI_cells": covered_keys(grid, point),
            "center_distance_to_clipped_AOI_m_E6933": float(grid.distance(point).min()),
            "visible_glyph_AOI_cells": sorted(grid.loc[grid.intersects(glyph), "grid_id"].tolist()),
            "glyph_is_uncertainty_bound": False,
            "exploratory_buffer_cell_counts_E6933": {
                str(r): int(grid.intersects(point.buffer(r)).sum())
                for r in (50, 100, 250, 500, 1000)
            },
        }
    # Parse date keys, then retain only this 2022 case's rows before scientific conversion.
    days = tuple(f"2022-06-{d:02d}" for d in (20, 21, 22))
    with CATALOG.open(encoding="utf-8-sig", newline="") as stream:
        rows = [r for r in csv.DictReader(stream) if r["acq_date"] in days]
    catalogue = training_detections(pd.DataFrame(rows))
    require(
        catalogue.timestamp.dt.year.eq(2022).all(), "Current pilot excludes calibration/holdouts"
    )
    lon, lat = estimates["all_seven"]["approximate_marker_lon_lat"]
    _, _, distances = GEOD.inv(
        np.full(len(catalogue), lon),
        np.full(len(catalogue), lat),
        catalogue.longitude.to_numpy(float),
        catalogue.latitude.to_numpy(float),
    )
    window_start, window_end, boundary = detection_windows(
        pd.Series([REPORTED_START.isoformat()])
    ).iloc[0]
    require(not boundary, "Fit-role window only")
    catalogue["distance_to_published_symbol_m"] = distances
    local = catalogue.loc[distances <= 3000].copy()
    local["target"] = pd.Series(pd.NA, index=local.index, dtype="string")
    local["is_confirmed_same_event"] = False
    radial = {}
    for radius in (250, 500, 1000, 2000, 3000):
        near = local.loc[local.distance_to_published_symbol_m.le(radius)]
        after = near.loc[near.timestamp.ge(REPORTED_START) & near.timestamp.le(window_end)]
        radial[str(radius)] = {
            "before_report_same_window": int(
                (near.timestamp.gt(window_start) & near.timestamp.lt(REPORTED_START)).sum()
            ),
            "at_or_after_report_same_window": len(after),
            "first_same_window_utc": after.timestamp.min().isoformat() if len(after) else None,
            "first_same_time_cells": sorted(
                after.loc[after.timestamp.eq(after.timestamp.min()), "grid_id"].unique().tolist()
            ),
        }
    registry = json.loads(REGISTRY.read_text())["cases"]
    roles = [
        {
            "reference_key": r["reference_key"],
            "reported_local_day": r["reported_local_day"],
            "source_metadata_role": "fit_reference_context"
            if r["reported_local_day"] < "2023-01-01"
            else "calibration_reference_context",
            "is_L_assignment": False,
        }
        for r in registry
    ]
    out = (
        BASE
        / "marmaris_published_marker_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    local.to_csv(out / "local_catalog_context.csv", index=False)
    pd.DataFrame(roles).to_csv(out / "reference_role_routing.csv", index=False)
    (out / "patch_matches.json").write_text(json.dumps(matches, indent=2) + "\n", encoding="utf-8")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].imshow(published, cmap="gray")
    axes[0].scatter(*anchors.T, c="cyan", s=20)
    for i, (x, y) in enumerate(anchors):
        axes[0].text(x + 6, y, str(i + 1), color="cyan")
    axes[0].scatter(*MARKER, c="yellow", s=40)
    axes[0].set_title("Published symbol / seven registration patches")
    center_px = (
        np.r_[MARKER, 1] @ np.linalg.lstsq(np.c_[anchors, np.ones(7)], pixels, rcond=None)[0]
    )
    axes[1].imshow(reference, cmap="gray")
    axes[1].scatter(*pixels.T, c="cyan", s=20)
    axes[1].scatter(*center_px, c="yellow", s=40)
    axes[1].set_title("Undated reference: geometry only, not historical cover")
    for ax in axes:
        ax.set_xticks([])
        ax.set_yticks([])
    fig.tight_layout()
    fig.savefig(out / "registration_review.png", dpi=95)
    plt.close(fig)
    report = {
        "status": "published_symbol_registered_no_L_or_target_admission",
        "source_case_id": "marmaris_2022",
        "source_page": 6,
        "source_figure": 9,
        "estimates": estimates,
        "registration_patch_count": len(matches),
        "reported_start_utc": REPORTED_START.isoformat(),
        "catalog_context_by_radius_m": radial,
        "source_role_conflict": "one_symbol_vs_municipal_three_vs_field_report_four_start_points",
        "field_report_page": 20,
        "field_report_claimed_start_count": 4,
        "field_report_claimed_approximate_line_length_km": 2,
        "reported_count_conflict_resolved": False,
        "number_of_distinct_real_fires_inferred": None,
        "control_subset_fits_are_independent_reference_images": False,
        "origin_coordinate_table_present": False,
        "symbol_placement_error_bound_known": False,
        "source_selection_design_documented": False,
        "L_memberships_created": 0,
        "reference_metadata_rows_by_role": dict(
            pd.Series([r["source_metadata_role"] for r in roles]).value_counts().items()
        ),
        "catalog_value_dates_used": list(days),
        "reference_imagery_used_as_model_feature": False,
        "target": None,
        "training_authorized": False,
        "final_merge_permitted": False,
        "target_gate": specification(),
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in PINS.items()},
        "producer_sha256": digest(Path(__file__)),
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
    }
    (out / "readback.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix())
    print(digest(out / "readback.json"))


if __name__ == "__main__":
    main()
