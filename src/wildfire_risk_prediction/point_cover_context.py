"""Sample a fixed reference map at detection centers; no fire or habitat admission."""

import numpy as np
from pyproj import Transformer

from wildfire_risk_prediction.landscape import CLASS_CODES, FOREST_CODES


def cover_group(code):
    if code is None or code == 0:
        return "unknown_or_unmapped"
    if code not in CLASS_CODES:
        raise ValueError("Unknown reference-map class")
    if code in FOREST_CODES:
        return "forest"
    return {
        20: "shrub",
        30: "herbaceous",
        40: "agriculture",
        50: "urban_built",
        60: "bare_sparse",
        70: "snow_ice",
        80: "water",
        90: "herbaceous_wetland",
        100: "moss_lichen",
        200: "ocean",
    }[code]


def sample_centers(points, dataset):
    """EPSG:4326 input, explicit xy transform to the retained raster's CRS."""
    if points.empty or not points.detection_id.is_unique:
        raise ValueError("Unique nonempty point inventory")
    if dataset.count != 1 or dataset.crs is None:
        raise ValueError("One-band georeferenced reference map")
    xy = points[["longitude", "latitude"]].to_numpy(float)
    if not np.isfinite(xy).all() or (np.abs(xy[:, 0]) > 180).any() or (np.abs(xy[:, 1]) > 90).any():
        raise ValueError("Finite geographic coordinates")
    transformer = Transformer.from_crs("EPSG:4326", dataset.crs, always_xy=True)
    xs, ys = transformer.transform(xy[:, 0], xy[:, 1])
    codes, rows, columns = [], [], []
    for x, y in zip(xs, ys, strict=True):
        row, col = dataset.index(x, y)
        inside = 0 <= row < dataset.height and 0 <= col < dataset.width
        rows.append(row if inside else None)
        columns.append(col if inside else None)
        if not inside:
            codes.append(None)
            continue
        value = next(dataset.sample([(x, y)], masked=True))[0]
        if np.ma.is_masked(value):
            codes.append(None)
        else:
            number = float(value)
            if not np.isfinite(number) or not number.is_integer():
                raise ValueError("Discrete class required")
            codes.append(int(number))
    result = points.copy()
    result["reference_map_row"] = rows
    result["reference_map_column"] = columns
    result["center_cover_code_2017"] = codes
    result["center_cover_group_2017"] = [cover_group(code) for code in codes]
    result["point_cover_is_fire_truth"] = False
    result["current_year_cover_verified"] = False
    return result
