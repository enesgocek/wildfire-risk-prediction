"""Exploratory geodesic pixel-center neighborhoods; no uncertainty bound or label rule."""

import numpy as np
import pandas as pd
from pyproj import Geod, Transformer
from rasterio.windows import Window

from wildfire_risk_prediction.landscape import CLASS_CODES, FOREST_CODES
from wildfire_risk_prediction.point_cover_context import sample_centers

GEOD = Geod(ellps="WGS84")


def describe_neighborhoods(points, dataset, radii=(100, 250, 500)):
    if (
        not radii
        or len(set(radii)) != len(radii)
        or any(not np.isfinite(r) or r <= 0 or r > 1000 for r in radii)
    ):
        raise ValueError("Distinct exploratory radii in (0,1000] meters required")
    if dataset.crs is None or dataset.crs.to_epsg() != 3857:
        raise ValueError("This bounded implementation requires the retained EPSG:3857 map")
    centers = sample_centers(points, dataset)
    if not centers.latitude.between(30, 45).all() or not centers.longitude.between(20, 40).all():
        raise ValueError("Bounded geographic working envelope")
    to_map = Transformer.from_crs(4326, 3857, always_xy=True)
    to_geo = Transformer.from_crs(3857, 4326, always_xy=True)
    # At 30-45 degrees, twice the geodesic radius plus pixel margins is a
    # conservative search box in this map; membership uses WGS84 distances.
    margin = 2 * max(radii) + 2 * max(dataset.res)
    output = []
    for point in centers.itertuples():
        x, y = to_map.transform(point.longitude, point.latitude)
        top, left = dataset.index(x - margin, y + margin)
        bottom, right = dataset.index(x + margin, y - margin)
        clipped = top < 0 or left < 0 or bottom >= dataset.height or right >= dataset.width
        top, left = max(0, top), max(0, left)
        bottom, right = min(dataset.height - 1, bottom), min(dataset.width - 1, right)
        if top > bottom or left > right:
            raise ValueError("Point neighborhood outside retained map")
        window = Window(left, top, right - left + 1, bottom - top + 1)
        raw = dataset.read(1, window=window, masked=True)
        rr, cc = np.meshgrid(np.arange(top, bottom + 1), np.arange(left, right + 1), indexing="ij")
        transform = dataset.transform
        xx = transform.a * (cc + 0.5) + transform.b * (rr + 0.5) + transform.c
        yy = transform.d * (cc + 0.5) + transform.e * (rr + 0.5) + transform.f
        lon, lat = to_geo.transform(xx.ravel(), yy.ravel())
        _, _, dist = GEOD.inv(
            np.full(len(lon), point.longitude), np.full(len(lon), point.latitude), lon, lat
        )
        dist = np.asarray(dist).reshape(raw.shape)
        values = raw.data
        mapped = ~np.ma.getmaskarray(raw) & np.isin(values, CLASS_CODES) & (values != 0)
        forest_shrub = mapped & np.isin(values, [20, *FOREST_CODES])
        for radius in sorted(radii):
            selected = dist <= radius
            valid = selected & mapped
            count = int(valid.sum())
            nearby = selected & forest_shrub
            output.append(
                {
                    "detection_id": point.detection_id,
                    "radius_m": radius,
                    "center_cover_group_2017": point.center_cover_group_2017,
                    "map_pixel_centers_within_radius": int(selected.sum()),
                    "mapped_pixel_centers": count,
                    "unknown_or_masked_centers": int((selected & ~mapped).sum()),
                    "forest_shrub_pixel_centers": int(nearby.sum()),
                    "forest_shrub_center_count_fraction": int(nearby.sum()) / count
                    if count
                    else np.nan,
                    "agriculture_pixel_centers": int((valid & (values == 40)).sum()),
                    "urban_pixel_centers": int((valid & (values == 50)).sum()),
                    "nearest_forest_shrub_center_within_radius_m": float(dist[nearby].min())
                    if nearby.any()
                    else np.nan,
                    "conservative_search_window_clipped": clipped,
                    "radius_is_accepted_geolocation_error_bound": False,
                    "fraction_is_pixel_footprint_area": False,
                    "current_year_cover_verified": False,
                    "habitat_eligibility_accepted": False,
                    "positive_label_permitted": False,
                    "negative_label_permitted": False,
                    "target": np.nan,
                }
            )
    return pd.DataFrame(output)
