"""Compare whole-AOI cell cover maps offline, without applying a habitat filter."""

import hashlib
import json
import socket
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from exactextract import exact_extract
from measure_corine_review_supports import class_areas
from pyproj import network
from shapely import segmentize

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
DELIVERY = BASE / "corine_delivery_review_v1/20261103T212921Z_3cc30ebb/readback.json"
WATER = BASE / "water_scope_v1/20261014T185242Z_f2e469bd"
WOODY = {311, 312, 313, 322, 323, 324}


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def deny(*args, **kwargs):
    raise RuntimeError("Offline cell cover comparison")


def main():
    pins = {}

    def pin(path, expected=None):
        path = Path(path)
        actual = sha(path)
        require(expected is None or actual == expected, "Input identity changed")
        pins[path.relative_to(ROOT).as_posix()] = actual
        return path

    manifest = json.loads(
        pin(
            ROOT / "data/interim/landscape/v1/manifest.json",
            "8fad7a76759baeebe0342dbe67343f7f02be4d86af64dece22956939c2c2e1bb",
        ).read_bytes()
    )
    static = pd.read_csv(
        pin(ROOT / manifest["table"], manifest["table_sha256"]), float_precision="round_trip"
    )
    parts = gpd.read_file(
        pin(ROOT / "data/interim/grid_aoi_parts.geojson", manifest["parts_sha256"])
    ).to_crs(6933)
    require(len(parts) == 2899 and parts.grid_id.is_unique, "All clipped AOI cells")
    require(parts.geometry.is_valid.all() and (parts.area > 0).all(), "Valid AOI geometries")
    require(
        np.allclose(parts.area / 1e6, parts.aoi_area_km2, rtol=1e-6, atol=1e-6),
        "Use AOI intersections, not full 25 km2 cells",
    )
    require(
        len(static) == 2899 and static.grid_id.is_unique and static.reference_year.eq(2017).all(),
        "Frozen source composition",
    )
    water_report = json.loads(
        pin(
            WATER / "readback.json",
            "7b5d296bae6c3744790817409db4bce3a947e92919a06abde9271eac07814cae",
        ).read_bytes()
    )
    water = pd.read_csv(
        pin(WATER / "grid_water_scope.csv", water_report["artifact_sha256"]["grid_water_scope.csv"])
    )
    require(
        water.water_scope_included.sum() == 2889 and water.grid_id.is_unique, "Retained water scope"
    )
    delivery = json.loads(
        pin(
            DELIVERY, "be52cf11729cec66f84a8abf8d45c3ac9bfaf8d764f68255f2c5ab4ae3b4313f"
        ).read_bytes()
    )
    raster_rel = next(
        k for k in delivery["source_sha256"] if k.endswith("U2018_CLC2018_V2020_20u1.tif")
    )
    raster = pin(ROOT / raster_rel, delivery["source_sha256"][raster_rel])
    pin(Path(__file__))
    pin(Path(__file__).with_name("measure_corine_review_supports.py"))
    pin(ROOT / "src/wildfire_risk_prediction/target_admission.py")

    out = (
        BASE
        / "cell_cover_scope_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    rows_by_step = {}
    with rasterio.open(raster) as ds:
        require(ds.crs.to_wkt() == delivery["raster"]["wkt"], "Verified source CRS")
        require(ds.transform.a == 100 and ds.transform.e == -100, "Native 100 m squares")
        for step in (100, 50):
            polygons = parts[["grid_id", "geometry"]].copy()
            polygons.geometry = segmentize(parts.geometry.array, step)
            polygons = polygons.to_crs(ds.crs)
            require(polygons.is_valid.all(), "Valid transformed geometries")
            print(f"Extracting {len(polygons)} clipped cells; edge step {step} m", flush=True)
            raw = exact_extract(ds, polygons, ["unique", "frac", "count"], include_cols=["grid_id"])
            rows = []
            for feature, polygon in zip(raw, polygons.itertuples(), strict=True):
                r = feature["properties"]
                require(r["grid_id"] == polygon.grid_id, "Extraction row identity")
                area = polygon.geometry.area
                classes = dict(zip(map(int, r["unique"]), map(float, r["frac"]), strict=True))
                require(set(classes) <= set(range(1, 45)) | {48}, "Known source raster values")
                mapped = sum(v for k, v in classes.items() if k != 48) * r["count"] * 10000
                woody = sum(
                    v
                    for k, v in classes.items()
                    if k != 48 and int(delivery["legend"][str(k)]["clc_code"]) in WOODY
                )
                woody *= r["count"] * 10000
                tolerance = max(1e-5, area * 1e-6)
                require(
                    -tolerance <= area - mapped <= area + tolerance
                    and 0 <= woody <= mapped + tolerance,
                    "Area accounting",
                )
                rows.append(
                    {
                        "grid_id": r["grid_id"],
                        "aoi_projected_area_m2": area,
                        "clc_mapped_area_m2": mapped,
                        "clc_woody_area_m2": woody,
                        "clc_woody_fraction_of_aoi": woody / area,
                        "clc_missing_fraction_of_aoi": max(0, area - mapped) / area,
                    }
                )
            rows_by_step[step] = pd.DataFrame(rows).set_index("grid_id")
        result = rows_by_step[50]
        convergence = (
            result.clc_woody_fraction_of_aoi - rows_by_step[100].clc_woody_fraction_of_aoi
        ).abs()
        require(convergence.max() < 1e-5, "Densification did not converge")
        # A different intersection algorithm checks spatially spread rows, not cover truth.
        verification = []
        for index in np.linspace(0, len(polygons) - 1, 5, dtype=int):
            row = polygons.iloc[index]
            areas = class_areas(ds, row.geometry)
            known = {k: v for k, v in areas.items() if k in range(1, 45)}
            woody = sum(
                v for k, v in known.items() if int(delivery["legend"][str(k)]["clc_code"]) in WOODY
            )
            error = abs(
                woody / row.geometry.area - result.loc[row.grid_id, "clc_woody_fraction_of_aoi"]
            )
            require(error < 1e-6, "Independent square intersection disagreement")
            verification.append({"grid_id": row.grid_id, "fraction_error": error})

    result = (
        result.reset_index()
        .merge(
            static[["grid_id", "forest_fraction", "shrub_fraction", "covered_area_km2"]],
            on="grid_id",
            validate="one_to_one",
        )
        .merge(water[["grid_id", "water_scope_included"]], on="grid_id", validate="one_to_one")
    )
    result["cgls_2017_woody_fraction_of_mapped_support"] = (
        result.forest_fraction + result.shrub_fraction
    )
    retained = result[result.water_scope_included]
    c17 = retained.cgls_2017_woody_fraction_of_mapped_support
    c18 = retained.clc_woody_fraction_of_aoi
    thresholds = []
    for limit in (0, 0.01, 0.1, 0.25, 0.5, 0.75):
        a, b = (c17 > 0, c18 > 0) if limit == 0 else (c17 >= limit, c18 >= limit)
        thresholds.append(
            {
                "fraction_limit": limit,
                "comparison": ">" if limit == 0 else ">=",
                "cgls_2017_cells": int(a.sum()),
                "clc_2018_cells": int(b.sum()),
                "maps_both_meet": int((a & b).sum()),
                "maps_disagree": int((a != b).sum()),
                "selected": False,
            }
        )
    table = out / "cell_map_comparison.csv"
    result.to_csv(table, index=False)
    report = {
        "scope": "historical_map_comparison_not_temporal_change_or_habitat_truth",
        "source_sha256": pins,
        "cells_total": len(result),
        "water_scope_retained": len(retained),
        "thresholds": thresholds,
        "cells_cgls_zero_clc_positive": int(((c17 == 0) & (c18 > 0)).sum()),
        "max_densification_fraction_difference": float(convergence.max()),
        "independent_intersections": verification,
        "artifact_sha256": {table.name: sha(table)},
        "threshold_selected": None,
        "cells_excluded_by_this_work": 0,
        "target_admission": specification(),
        "model_trained": False,
        "network_requests": 0,
        "validation_or_final_data_opened": False,
    }
    require(len(result) == 2899 and len(retained) == 2889, "Complete scope comparison")
    require(all(sha(ROOT / p) == expected for p, expected in pins.items()), "Input closure")
    saved = out / "readback.json"
    saved.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    require(json.loads(saved.read_bytes()) == report, "Readback")
    print(out.relative_to(ROOT).as_posix(), flush=True)
    print("readback_sha256", sha(saved), flush=True)
    print(json.dumps(thresholds), flush=True)


if __name__ == "__main__":
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    network.set_network_enabled(False)
    main()
