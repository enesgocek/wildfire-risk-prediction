"""Join clock/location sensitivity, map context and nearby-record flags for review."""

import json
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from audit_mersin_incident_proximity import candidate_pairs
from audit_mersin_open_incidents import (
    ARCHIVE,
    CORINE_RASTER,
    CORINE_RECEIPT,
    FOREST_SHRUB,
    GRID,
    PINS,
    PROVINCES,
    ROOT,
    read_incidents,
)
from audit_stage_one_selection import verify
from pyproj import Transformer
from rasterio.features import geometry_mask
from rasterio.mask import mask as raster_mask

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require


def main():
    stable_path = ROOT / (
        "outputs/reports/dataset/mersin_reference_stability_v1/"
        "20261118T134919Z_c9750a10/readback.json"
    )
    verify(stable_path, "2b3413aa2957f0bc926fd99d1d634974cfa25d3921edcceb25624a757dd2b604")
    for path in (ARCHIVE, GRID, PROVINCES, CORINE_RECEIPT, CORINE_RASTER):
        verify(path, PINS[path])
    stable = json.loads(stable_path.read_bytes())
    units = pd.DataFrame(stable["reference_units"]).set_index("archive_row")
    events, _ = read_incidents()
    rows = events.loc[units.index].copy()
    rows["source_minute"] = [
        day.toordinal() * 1440 + round(Decimal(hour) * 60)
        for day, hour in zip(rows.date, rows.ignition_hour, strict=True)
    ]
    ordered = list(
        rows.rename_axis("event_id")
        .reset_index()
        .sort_values("source_minute", kind="stable")
        .itertuples(index=False)
    )
    pairs = candidate_pairs(ordered)
    edge_counts = {}
    for minutes, meters, column in (
        (60, 5000, "nearby_60min_5km"),
        (1440, 10000, "nearby_24h_10km"),
    ):
        selected = [p for p in pairs if p[2] <= minutes and p[3] <= meters]
        ids = {ordered[i].event_id for p in selected for i in p[:2]}
        units[column] = units.index.isin(ids)
        edge_counts[column] = len(selected)
    require(
        edge_counts == {"nearby_60min_5km": 7, "nearby_24h_10km": 35},
        "Same prior proximity scope and counts",
    )
    require(
        units.nearby_60min_5km.sum() == 11 and units.nearby_24h_10km.sum() == 46,
        "Same prior proximity row counts",
    )
    legend = json.loads(CORINE_RECEIPT.read_bytes())["legend"]
    with rasterio.open(CORINE_RASTER) as raster:
        transform = Transformer.from_crs(4326, raster.crs, always_xy=True)
        x, y = transform.transform(rows.longitude.astype(float), rows.latitude.astype(float))
        codes = []
        for (value,) in raster.sample(zip(x, y, strict=True), masked=True):
            codes.append(None if np.ma.is_masked(value) else legend[str(int(value))]["clc_code"])
    units["corine_2018_center_code"] = codes
    units["center_context"] = [
        "forest_shrub"
        if code in FOREST_SHRUB
        else "agriculture"
        if code is not None and 200 <= code < 300
        else "unmapped"
        if code is None
        else "other"
        for code in codes
    ]
    points = gpd.GeoSeries(
        gpd.points_from_xy(rows.longitude.astype(float), rows.latitude.astype(float)),
        index=units.index,
        crs=4326,
    ).to_crs(6933)
    with rasterio.open(CORINE_RASTER) as raster:
        for radius in (250, 1000):
            circles = points.buffer(radius).to_crs(raster.crs)
            records = []
            for circle in circles:
                data, transform = raster_mask(raster, [circle], crop=True, filled=False)
                selected = geometry_mask(
                    [circle], out_shape=data.shape[1:], transform=transform, invert=True
                )
                mapped = selected & ~np.ma.getmaskarray(data[0])
                values = data[0].data[mapped]
                mapped_codes = np.array([legend[str(int(v))]["clc_code"] for v in values])
                forest = int(np.isin(mapped_codes, list(FOREST_SHRUB)).sum())
                agriculture = int(((mapped_codes >= 200) & (mapped_codes < 300)).sum())
                record = {
                    "sampled_pixels": int(selected.sum()),
                    "mapped_pixels": len(values),
                    "forest_shrub_pixels": forest,
                    "agriculture_pixels": agriculture,
                }
                require(
                    record["sampled_pixels"] > 0 and forest + agriculture <= len(values),
                    "Circle pixel support and distinct class counts",
                )
                records.append(record)
            for column in records[0]:
                units[f"{column}_{radius}m"] = [r[column] for r in records]
    require(units.index.is_unique and len(units) == 479, "All reference rows retained")
    for column in ("sampled_pixels", "mapped_pixels", "forest_shrub_pixels", "agriculture_pixels"):
        require(
            units[f"{column}_1000m"].ge(units[f"{column}_250m"]).all(),
            "Nested map sampling circles",
        )
    require(
        units.loc[units.center_context.eq("forest_shrub"), "forest_shrub_pixels_250m"].gt(0).all(),
        "Forest center agrees with local map sampling",
    )
    summaries = []
    for scope, frame in (
        ("all_479", units),
        ("stable_day_and_250m", units.loc[units.stable_day_and_250m]),
        ("stable_day_and_1000m", units.loc[units.stable_day_and_1000m]),
    ):
        for cover, group in frame.groupby("center_context"):
            summaries.append(
                {
                    "scope": scope,
                    "corine_center_context": cover,
                    "records": len(group),
                    "under_1_ha": int(group.small.sum()),
                    "nearby_60min_5km": int(group.nearby_60min_5km.sum()),
                    "nearby_24h_10km": int(group.nearby_24h_10km.sum()),
                    "agriculture_present_250m": int(group.agriculture_pixels_250m.gt(0).sum()),
                    "agriculture_present_1000m": int(group.agriculture_pixels_1000m.gt(0).sum()),
                    "incomplete_map_support_250m": int(
                        group.mapped_pixels_250m.lt(group.sampled_pixels_250m).sum()
                    ),
                    "incomplete_map_support_1000m": int(
                        group.mapped_pixels_1000m.lt(group.sampled_pixels_1000m).sum()
                    ),
                }
            )
    result = {
        "records": len(units),
        "summary": summaries,
        "proximity_edge_counts": edge_counts,
        "inputs_sha256": {
            p.relative_to(ROOT).as_posix(): digest(p)
            for p in (stable_path, ARCHIVE, GRID, PROVINCES, CORINE_RECEIPT, CORINE_RASTER)
        },
        "reference_units": units.astype(object)
        .where(units.notna(), None)
        .reset_index()
        .to_dict("records"),
        "cover_basis": "2018_map_center_only_event_date_cover_unverified",
        "identity_basis": "proximity_flag_only_unique_events_unverified",
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "labels_created": False,
    }
    out = (
        ROOT
        / "outputs/reports/dataset/mersin_joint_reference_v1"
        / (f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}_{uuid4().hex[:8]}")
    )
    out.mkdir(parents=True, exist_ok=False)
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_bytes()) == result, "Joint reference roundtrip")
    print(json.dumps(summaries, indent=2))
    print(path.relative_to(ROOT), digest(path))


if __name__ == "__main__":
    main()
