"""Temporal and spatial screening of imagery metadata; never a label decision."""

from datetime import UTC, datetime, timedelta

from shapely.geometry import shape


def utc_time(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Timezone required")
    return result.astimezone(UTC)


def prediction_time(detection):
    """Assign the daily (T,T+24h] target, including exactly midnight."""
    value = utc_time(detection) - timedelta(microseconds=1)
    if not 2018 <= value.year <= 2023:
        raise ValueError("Training prediction date required")
    return value.replace(hour=0, minute=0, second=0, microsecond=0)


def inspect_item(item, support, cutoff, lookback_days=60):
    if item.get("collection") != "sentinel-2-l2a":
        raise ValueError("Unexpected collection")
    properties = item["properties"]
    acquired = utc_time(properties["datetime"])
    footprint = shape(item["geometry"])
    if not footprint.is_valid or footprint.is_empty:
        raise ValueError("Invalid scene footprint")
    cloud = properties.get("eo:cloud_cover")
    if cloud is not None and not 0 <= float(cloud) <= 100:
        raise ValueError("Invalid scene cloud percentage")
    generated = properties.get("s2:generation_time")
    assets = item["assets"]
    before = cutoff - timedelta(days=lookback_days) <= acquired < cutoff
    covers = footprint.covers(support)
    return {
        "item_id": item["id"],
        "acquired_utc": acquired.isoformat(),
        "days_before_prediction": (cutoff - acquired).total_seconds() / 86400,
        "within_60_days_before_prediction": before,
        "footprint_covers_approximate_support": covers,
        "scene_cloud_percent": cloud,
        "mgrs_tile": properties.get("s2:mgrs_tile"),
        "relative_orbit": properties.get("sat:relative_orbit"),
        "processing_baseline": properties.get("s2:processing_baseline"),
        "product_generated_utc": generated,
        "product_generated_after_prediction": (
            utc_time(generated) >= cutoff if generated else None
        ),
        "rgb_and_scl_assets_present": all(k in assets for k in ("B04", "B03", "B02", "SCL")),
        "metadata_candidate": before
        and covers
        and all(k in assets for k in ("B04", "B03", "B02", "SCL")),
        "local_cloud_quality_checked": False,
        "historical_available_at_verified": False,
        "cover_label_accepted": False,
    }
