"""Prepare two historical map contexts for every fit detection, without habitat/label filtering."""

import csv
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from rasterio.transform import rowcol
from replay_satellite_pu_lineage import (
    POLICY,
    ROOT,
    SOURCE,
    SOURCE_SHA,
    fit_source,
    validate_policy,
)

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.landscape import CLASS_CODES, FOREST_CODES
from wildfire_risk_prediction.target_admission import specification

BASE = ROOT / "outputs/reports/dataset"
CGLS = ROOT / "data/raw/landcover/landcover_copernicus_2017.tif"
CGLS_SHA = "ee8bd6c9f742dbbdfcdcbbb6ecc446499f05d676eaeb202c4345c11ea6006470"
CORINE_DIR = BASE / "corine_delivery_review_v1/20261103T212921Z_3cc30ebb"
CORINE = CORINE_DIR / "source/DATA/U2018_CLC2018_V2020_20u1.tif"
CORINE_SHA = "69057d527b4338b89f58cf15693effcf18017611ff48144e5c491d083cf1b004"
LEGEND = CORINE_DIR / "readback.json"
LEGEND_SHA = "be52cf11729cec66f84a8abf8d45c3ac9bfaf8d764f68255f2c5ab4ae3b4313f"
WOODY_CLC = {311, 312, 313, 322, 323, 324}


def context(code, scheme):
    require(scheme in {"CGLS2017", "CORINE2018"}, "Known historical map")
    if code is None or (scheme == "CGLS2017" and code == 0):
        return "unmapped"
    if scheme == "CGLS2017":
        require(code in CLASS_CODES, "Known CGLS class")
        return (
            "forest_shrub"
            if code in {*FOREST_CODES, 20}
            else "agriculture"
            if code == 40
            else "other"
        )
    return "forest_shrub" if code in WOODY_CLC else "agriculture" if 200 <= code < 300 else "other"


def sample_centers(path, longitude, latitude, *, legend=None):
    result = []
    with rasterio.open(path) as raster:
        transform = Transformer.from_crs(4326, raster.crs, always_xy=True)
        xs, ys = transform.transform(longitude, latitude)
        rows, columns = rowcol(raster.transform, xs, ys)
        for row, col, value in zip(
            rows, columns, raster.sample(zip(xs, ys, strict=True), masked=True), strict=True
        ):
            raw = None if np.ma.is_masked(value[0]) else int(value[0])
            if raw is None:
                code = None
            elif legend is None:
                code = raw
            else:
                require(str(raw) in legend, "Known CORINE raster code")
                code = legend[str(raw)]["clc_code"]
            result.append(
                {
                    "raw_raster_value": raw,
                    "class_code": code,
                    "raster_row": int(row),
                    "raster_column": int(col),
                }
            )
    return result


def main():
    policy = json.loads(POLICY.read_bytes())
    validate_policy(policy)
    pins = {
        POLICY: digest(POLICY),
        SOURCE: SOURCE_SHA,
        CGLS: CGLS_SHA,
        CORINE: CORINE_SHA,
        LEGEND: LEGEND_SHA,
    }
    for path in (
        ROOT / "src/wildfire_risk_prediction/landscape.py",
        Path(__file__).with_name("replay_satellite_pu_lineage.py"),
    ):
        pins[path] = digest(path)
    require(all(digest(p) == h for p, h in pins.items()), "Existing raster/source/decision pins")
    with SOURCE.open(encoding="utf-8-sig", newline="") as stream:
        frame = fit_source(csv.DictReader(stream))
    require(len(frame) == 28396, "Same fit source as lineage")
    legend = json.loads(LEGEND.read_bytes())["legend"]
    points = frame[
        ["detection_id", "grid_id", "detection_timestamp_utc", "longitude", "latitude"]
    ].copy()
    for name, path, scheme, mapping in (
        ("cgls_2017", CGLS, "CGLS2017", None),
        ("corine_2018", CORINE, "CORINE2018", legend),
    ):
        samples = sample_centers(
            path, points.longitude.to_numpy(), points.latitude.to_numpy(), legend=mapping
        )
        for field in ("raw_raster_value", "class_code", "raster_row", "raster_column"):
            points[name + "_" + field] = [x[field] for x in samples]
        points[name + "_center_context"] = [context(x["class_code"], scheme) for x in samples]
        print(name, points[name + "_center_context"].value_counts().to_dict(), flush=True)
    points["map_contexts_agree"] = points.cgls_2017_center_context.eq(
        points.corine_2018_center_context
    )
    points["both_map_centers_forest_shrub"] = points.cgls_2017_center_context.eq(
        "forest_shrub"
    ) & points.corine_2018_center_context.eq("forest_shrub")
    points["target"] = pd.NA
    points["weak_positive_membership"] = pd.NA
    out = (
        BASE
        / "satellite_PU_cover_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    path = out / "historical_center_context.csv"
    points.to_csv(path, index=False)
    report = {
        "status": "fit_detection_historical_map_context_only_no_habitat_admission",
        "source_detections": len(points),
        "map_context_pair_counts": dict(
            Counter(
                a + "|" + b
                for a, b in zip(
                    points.cgls_2017_center_context, points.corine_2018_center_context, strict=True
                )
            )
        ),
        "event_date_cover_verified": False,
        "maps_have_identical_definitions": False,
        "map_disagreement_is_accuracy_estimate": False,
        "mapped_center_is_whole_native_fire_pixel": False,
        "corine_2018_can_postdate_2018_fire": True,
        "landcover_added_to_model_inputs": False,
        "filter_applied": False,
        "new_L_or_Y_memberships": 0,
        "model_trained": False,
        "final_merge_performed": False,
        "gate": specification(),
        "artifact_sha256": {path.name: digest(path)},
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
    }
    require(all(digest(p) == h for p, h in pins.items()), "Frozen input closure")
    destination = out / "readback.json"
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), flush=True)
    print("readback_sha256", digest(destination), flush=True)


if __name__ == "__main__":
    main()
