"""Choose distinct pre-event dates before observing their local image quality."""

from wildfire_risk_prediction.preevent_imagery import inspect_item, utc_time


def alternative_dates(items, original, support, cutoff, count=2):
    """Rank by scene cloud, recency, ID; never select two products of one UTC day."""
    if not 2018 <= cutoff.year <= 2023 or count < 1:
        raise ValueError("Training-only positive selection count required")
    seen_ids, candidates = set(), []
    for item in items:
        if item["id"] in seen_ids:
            raise ValueError("Duplicate scene identity")
        seen_ids.add(item["id"])
        review = inspect_item(item, support, cutoff)
        if review["metadata_candidate"] and "visual" in item["assets"]:
            candidates.append((item, review))
    if original["id"] not in seen_ids:
        raise ValueError("Original scene missing")
    used_dates = {utc_time(original["properties"]["datetime"]).date()}
    candidates.sort(
        key=lambda pair: (
            float("inf")
            if pair[1]["scene_cloud_percent"] is None
            else float(pair[1]["scene_cloud_percent"]),
            pair[1]["days_before_prediction"],
            pair[0]["id"],
        )
    )
    selected = []
    for item, review in candidates:
        day = utc_time(review["acquired_utc"]).date()
        if day in used_dates:
            continue
        used_dates.add(day)
        selected.append(item)
        if len(selected) == count:
            return selected
    raise ValueError("Insufficient distinct pre-event dates")
