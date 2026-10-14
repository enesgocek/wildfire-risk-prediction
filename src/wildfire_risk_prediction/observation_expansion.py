"""Geographic method-pilot planning and deduplicated source bytes, never target admission."""

import hashlib
import re
from datetime import datetime
from pathlib import PurePosixPath

import numpy as np
import pandas as pd
import shapely

from wildfire_risk_prediction.feature_join import require, training_day, utc_times

SIGNALS = ("no_selected_thermal_center", "thermal_center_present")


def province_support(parts, provinces):
    """Largest-overlap sampling province, retaining every positive provincial intersection."""
    require(parts.grid_id.is_unique and parts.grid_id.notna().all(), "Unique province/grid keys")
    require(provinces.province.is_unique and provinces.province.notna().all(), "Unique provinces")
    parts, provinces = parts.to_crs(6933), provinces.sort_values("province").to_crs(6933)
    cells = parts.geometry.to_numpy()
    borders = provinces.geometry.to_numpy()
    require(
        shapely.is_valid(cells).all() and shapely.is_valid(borders).all(), "Valid province inputs"
    )
    areas = shapely.area(cells)
    require((areas > 0).all() and (shapely.area(borders) > 0).all(), "Positive source geometries")
    weights = np.stack([shapely.area(shapely.intersection(cells, b)) for b in borders])
    union = shapely.union_all(borders)
    uncovered = shapely.area(shapely.difference(cells, union))
    coverage = areas - uncovered
    chosen = weights.argmax(axis=0)
    maximum = weights.max(axis=0)
    names = provinces.province.to_numpy()[chosen].astype(object)
    names[maximum <= 0.05] = None  # Numerical area reporting tolerance, not habitat eligibility.
    result = pd.DataFrame(
        {
            "grid_id": parts.grid_id.to_numpy(),
            "primary_province": names,
            "primary_province_aoi_fraction": maximum / areas,
            "province_intersection_count": (weights > 0.05).sum(axis=0),
            "unassigned_province_area_m2": uncovered,
            "province_overlap_sum_excess_m2": np.maximum(weights.sum(axis=0) - coverage, 0),
        }
    )
    rows = [
        {
            "grid_id": cell,
            "province": province,
            "intersection_area_m2": float(weight),
            "aoi_fraction": float(weight / area),
        }
        for j, province in enumerate(provinces.province)
        for cell, weight, area in zip(parts.grid_id, weights[j], areas, strict=True)
        if weight > 0.05
    ]
    return result, pd.DataFrame(rows)


def calendar_dates(years, seasons):
    require(len(years) == len(set(years)) and bool(years), "Distinct calendar years")
    rows = []
    for year in years:
        require(type(year) is int, "Integer training years")
        for season, suffix in seasons.items():
            day = f"{year}-{suffix}"
            training_day(day)
            rows.append({"target_day": day, "calendar_season": season})
    result = pd.DataFrame(rows)
    require(result.target_day.is_unique and not result.empty, "Distinct pilot dates")
    return result


def select_core(frame, dates, provinces, seed):
    """Up to two purpose-selected cases per fixed day/province/signal; no replacement dates."""
    require(
        not frame.empty and not frame.duplicated(["grid_id", "prediction_timestamp_utc"]).any(),
        "Unique expansion frame",
    )
    times = utc_times(frame.prediction_timestamp_utc)
    require(
        times.notna().all()
        and times.dt.year.between(2018, 2023).all()
        and times.eq(times.dt.normalize()).all(),
        "Training midnight candidates",
    )
    require(
        frame.obs_daily_observation_status.eq("unknown").all()
        and frame.obs_negative_label_permitted.eq(False).all(),
        "Closed observation gates",
    )
    require("target" not in frame or frame.target.isna().all(), "Unassigned targets")
    source = frame.copy()
    source["target_day"] = times.dt.strftime("%Y-%m-%d")
    require(set(source.target_day) == set(dates.target_day), "Exact prespecified calendar")
    source["selection_rank_sha256"] = [
        hashlib.sha256(f"{seed}|{g}|{t}".encode()).hexdigest()
        for g, t in zip(source.grid_id, source.target_day, strict=True)
    ]
    rows, quotas = [], []
    for day, season in dates[["target_day", "calendar_season"]].itertuples(index=False, name=None):
        for province in provinces:
            for signal in SIGNALS:
                candidates = source.loc[
                    source.target_day.eq(day)
                    & source.primary_province.eq(province)
                    & source.signal_group.eq(signal)
                    & source.water_scope_included.eq(True)
                ]
                candidates = candidates.sort_values(["selection_rank_sha256", "grid_id"])
                selected = candidates.iloc[:1]
                if len(candidates) > 1:
                    other = candidates.loc[~candidates.grid_id.isin(selected.grid_id)]
                    different = other.loc[other.cover_group.ne(selected.cover_group.iloc[0])]
                    selected = pd.concat(
                        [selected, (different if not different.empty else other).iloc[:1]]
                    )
                if not selected.empty:
                    selected = selected.copy()
                    selected["calendar_season"] = season
                    selected["selection_plan"] = "calendar_core"
                    selected["review_unit_id"] = "expansion:" + selected.grid_id + ":" + day
                    selected["target"] = np.nan
                    selected["population_error_estimation_permitted"] = False
                    rows.append(selected)
                quotas.append(
                    {
                        "target_day": day,
                        "calendar_season": season,
                        "primary_province": province,
                        "signal_group": signal,
                        "available_candidates": len(candidates),
                        "requested_units": 2,
                        "selected_units": len(selected),
                        "unfilled_slots": 2 - len(selected),
                    }
                )
    require(bool(rows), "At least one pilot candidate")
    return pd.concat(rows, ignore_index=True), pd.DataFrame(quotas)


def raw_references(report):
    """Extract accepted native filenames/sizes/SHA; these do not certify current remote access."""
    day = report["day"]
    training_day(day)
    require(
        report["daily_observation_status"] == "unknown"
        and report["negative_label_permitted"] is False,
        "Closed source packet",
    )
    ids = report["pair_ids"]
    sources = report["sources"]
    require(
        isinstance(ids, list)
        and bool(ids)
        and len(ids) == len(set(ids))
        and isinstance(sources, list)
        and sorted(ids) == sorted(s["sample_id"] for s in sources),
        "Exact source pair inventory",
    )
    rows = []
    for item in sources:
        identity = item["sample_id"]
        match = re.fullmatch(r"(SNPP|N20):(\d{7}\.\d{4})", identity)
        require(match is not None, "Source pair identity")
        sensor, pair = match.groups()
        require(
            datetime.strptime(pair, "%Y%j.%H%M").strftime("%Y-%m-%d") == day, "Nominal source day"
        )
        audit = item["audit"]
        require(
            audit["sample_id"] == identity and audit["negative_label_permitted"] is False,
            "Source audit identity",
        )
        require(set(audit["sources"]) == {"fire", "geolocation"}, "Both source roles")
        for role, source in audit["sources"].items():
            filename = PurePosixPath(source["path"].replace("\\", "/")).name
            prefix = {
                ("SNPP", "fire"): "VNP14IMG",
                ("SNPP", "geolocation"): "VNP03IMG",
                ("N20", "fire"): "VJ114IMG",
                ("N20", "geolocation"): "VJ103IMG",
            }[sensor, role]
            version = "021" if prefix == "VJ103IMG" else "002"
            require(
                re.fullmatch(re.escape(f"{prefix}.A{pair}.{version}.") + r"\d{13}\.nc", filename)
                is not None,
                "Expected native source filename",
            )
            require(
                type(source["bytes"]) is int
                and source["bytes"] > 0
                and re.fullmatch(r"[0-9a-f]{64}", source["sha256"]) is not None,
                "Positive native bytes and SHA-256",
            )
            rows.append(
                {
                    "source_id": identity + "|" + role,
                    "source_day": day,
                    "sample_id": identity,
                    "role": role,
                    "filename": filename,
                    "bytes": source["bytes"],
                    "sha256": source["sha256"],
                    "current_remote_availability": "not_checked",
                }
            )
    return pd.DataFrame(rows)


def unique_sources(frame):
    fields = ["source_day", "sample_id", "role", "filename", "bytes", "sha256"]
    require(not frame.empty and frame.source_id.notna().all(), "Identified native sources")
    for _, group in frame.groupby("source_id", sort=False):
        require(len(group[fields].drop_duplicates()) == 1, "Conflicting native source versions")
    return frame.drop_duplicates("source_id").sort_values("source_id").reset_index(drop=True)
