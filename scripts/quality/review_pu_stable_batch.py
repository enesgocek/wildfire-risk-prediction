"""Batch readback of preceding catalogue and scan support for the 15 stable cases."""

import csv
import hashlib
import json
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd
import rasterio
from geopandas import GeoSeries
from rasterio.warp import transform
from review_pu_candidate_timeline import CASE, GRAPH, OBS, prior_neighbourhood, sha
from shapely.geometry import Point

from wildfire_risk_prediction.event_review import training_detections
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.observation_window import review_window, source_schedule
from wildfire_risk_prediction.observation_window_source import read_month_offline
from wildfire_risk_prediction.perimeter_review import effis_gml

ROOT = Path(__file__).resolve().parents[2]
BASE = "outputs/reports/dataset"
C_TIMELINE = f"{BASE}/pu_candidate_timeline_v1/20261107T224018Z_21d83b2a/readback.json"
EFFIS = "data/raw/reference/effis/2021_summer_pilot_2026-10-14/effis_2021_summer.gml"
STABLE = "all_presence_time_and_membership_equal"


def catalogue_sources(retain, graph):
    source = retain("data/interim/firms_combined_candidates_2018_2024.csv", graph["source_sha256"])
    with source.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    train = [row for row in rows if not row["detection_timestamp_utc"].startswith("2024-")]
    require(len(rows) - len(train) == graph["validation_rows_excluded"], "Validation exclusion")
    result = training_detections(pd.DataFrame(train))
    require(len(result) == graph["training_detection_count"], "Training catalogue count")
    return result


def memberships(retain, graph, case_index, source):
    result = defaultdict(list)
    for scenario, hashes in sorted(graph["artifact_sha256"].items()):
        assignments = pd.read_csv(
            retain(
                f"data/interim/event_grouping/{scenario}_assignments.csv",
                hashes["assignments_sha256"],
            )
        ).set_index("detection_id", verify_integrity=True)
        catalogue = pd.read_csv(
            retain(f"{GRAPH}/{scenario}_review.csv", hashes["review_sha256"])
        ).set_index("cluster_id", verify_integrity=True)
        require(len(assignments) == len(source), "Assignment denominator")
        for unit, case in case_index.items():
            anchors = assignments.loc[case["point_ids"]]
            require(anchors.grid_id.eq(case["grid_id"]).all(), "First point grid")
            rows = []
            for cluster in sorted(set(anchors.cluster_id)):
                members = assignments.loc[assignments.cluster_id.eq(cluster)]
                ids = sorted(members.index)
                record = catalogue.loc[cluster]
                digest = hashlib.sha256("\n".join(ids).encode()).hexdigest()
                timestamps = source.loc[ids, "timestamp"]
                require(
                    digest == record.membership_sha256
                    and len(ids) == record.detection_count
                    and timestamps.min() == pd.Timestamp(record.first_detection_utc)
                    and timestamps.max() == pd.Timestamp(record.last_detection_utc),
                    "Member keys and time bounds",
                )
                in_cell = members.index[members.grid_id.eq(case["grid_id"])]
                first_in_cell = set(in_cell) & set(
                    timestamps.index[timestamps.eq(timestamps.min())]
                )
                require(
                    first_in_cell == set(anchors.index[anchors.cluster_id.eq(cluster)])
                    and timestamps.min().isoformat() in case["first_times_utc"],
                    "Complete first points in review cell",
                )
                rows.append({"member_count": len(ids), "membership_sha256": digest})
            result[unit].append({"scenario": scenario, "components": rows})
    for rows in result.values():
        signatures = {
            tuple(sorted(r["membership_sha256"] for r in row["components"])) for row in rows
        }
        require(len(rows) == 9 and len(signatures) == 1, "Stable group signature")
    return result


def scan_windows(retain, cases, inputs):
    master = json.loads(
        retain(
            f"{OBS}/accepted_readback.json",
            "fb5fa5ce8c83be2c4e21b130bb06935a5e2d8014e45460c1f61660b73262cb14",
        ).read_text()
    )
    blocks = json.loads(
        retain(
            "configs/gcp_source_blocks_2026-10-13.json",
            "c5dcb61b6ccd0c6055f96a929cebcbdc6cea41857270b8581ba7a519495aec95",
        ).read_text()
    )
    schedules, requested = {}, defaultdict(lambda: defaultdict(set))
    for unit, case in cases.items():
        day = pd.Timestamp(case["prediction_utc"])
        for offset in (-3, -2, -1, 0):
            target = (day + pd.Timedelta(days=offset)).strftime("%Y-%m-%d")
            schedule = source_schedule(target, set(blocks["deferred_days"]))
            schedules[unit, offset, target] = schedule
            for nominal in schedule.loc[
                schedule.source_status.eq("available_training_packet"), "source_nominal_day"
            ]:
                requested[nominal[:7]][nominal].add(case["grid_id"])
    months = {report["month"]: report for report in master["reports"]}
    frames, inner = {}, {}
    for month, days in sorted(requested.items()):
        packet = read_month_offline(ROOT, months[month], days, time.monotonic() + 120)
        frames.update(packet["frames"])
        inner.update(packet["inner"])
        inputs.update(packet["inputs"])
        print("Checked month", month, "nominal packets", len(days), flush=True)
    output = defaultdict(list)
    for (unit, offset, target), schedule in schedules.items():
        grid = cases[unit]["grid_id"]
        parts = [frames[day] for day in schedule.source_nominal_day if day in frames]
        source = pd.concat(parts, ignore_index=True)
        _, result = review_window(source.loc[source.grid_id.eq(grid)], target, grid, schedule)
        del result["target"]
        output[unit].append({"day_offset": offset, **result})
    return output, inner


def spatial_context(retain, anchor):
    refs = effis_gml(
        retain(
            EFFIS, "351506b52949e292aaaf62b51556ae0cfd9d553c2c198d24b81ecdb758e65eba"
        ).read_bytes()
    )
    require(len(refs) == 84 and refs.geometry_valid.all(), "Known EFFIS slice")
    point = Point(anchor.longitude, anchor.latitude)
    c = GeoSeries([point], crs=4326).to_crs(32636).iloc[0]
    dist = refs.to_crs(32636).distance(c)
    closest = refs.loc[dist.idxmin()]
    sample = "data/raw/burned_area/samples/burned_area_sample_2021_08.tif"
    with rasterio.open(retain(sample, sha(ROOT / sample))) as raster:
        x, y = transform("EPSG:4326", raster.crs, [point.x], [point.y])
        row, col = raster.index(x[0], y[0])
        inside = 0 <= row < raster.height and 0 <= col < raster.width
    return {
        "effis_polygons": len(refs),
        "covers_anchor_count": int(refs.geometry.covers(point).sum()),
        "nearest_reference_id": closest.reference_id,
        "nearest_distance_utm36n_m": float(dist.min()),
        "nearest_start_as_reported": closest.FIREDATE,
        "nearest_end_as_reported": closest.FINALDATE,
        "modis_local_sample_covers_anchor": inside,
    }


def main():
    pins = {}

    def retain(name, expected):
        path = ROOT / name
        require(path.resolve(strict=True).is_relative_to(ROOT), "Contained input")
        require(sha(path) == expected, f"Hash mismatch: {name}")
        pins[name] = expected
        return path

    pilot = json.loads(
        retain(CASE, "5b7fd0cc69efe03ff73dac67e65d58878add917f0a133917fe204715d07824ce").read_text()
    )
    c_prior = json.loads(
        retain(
            C_TIMELINE, "dc2489f28a0e4fcf3ce31fe8e9db3a570ddf792fe85562e4266a751d974b2b20"
        ).read_text()
    )
    graph = json.loads(
        retain(
            f"{GRAPH}/review.json",
            "61de3f798bb1462baf4f1d65bebc72539cef47467d5590baeec498951dc94d7e",
        ).read_text()
    )
    cases = {
        row["review_unit_id"]: row for row in pilot["review_cases"] if row["grouping"] == STABLE
    }
    require(
        len(cases) == 15 and all(row["target"] is None for row in cases.values()), "Fixed case set"
    )
    source = catalogue_sources(retain, graph)
    index = source.set_index("detection_id", drop=False, verify_integrity=True)
    membership = memberships(retain, graph, cases, index)
    observation, inner = scan_windows(retain, cases, pins)
    results = []
    for unit, case in cases.items():
        points = [index.loc[point_id] for point_id in case["point_ids"]]
        prior = [prior_neighbourhood(source, point) for point in points]
        result = {
            "review_unit_id": unit,
            "codes": case["point_codes"],
            "point_ids": case["point_ids"],
            "memberships": membership[unit],
            "preceding_context_by_point": prior,
            "observation_windows": observation[unit],
            "target": None,
        }
        if case["point_codes"] == ["C"]:
            require(prior == [c_prior["preceding_catalogue_context"]], "C prior record reconciles")
            require(
                [{k: v for k, v in row.items() if k != "day_offset"} for row in observation[unit]]
                == c_prior["observation_context"]["daily_windows"],
                "C scan records reconcile",
            )
            result["retained_reference_context"] = spatial_context(retain, points[0])
        results.append(result)
    for name in (
        Path(__file__).relative_to(ROOT).as_posix(),
        "scripts/quality/review_pu_candidate_timeline.py",
        "src/wildfire_risk_prediction/event_review.py",
        "src/wildfire_risk_prediction/observation_window.py",
        "src/wildfire_risk_prediction/observation_window_source.py",
        "src/wildfire_risk_prediction/perimeter_review.py",
    ):
        retain(name, sha(ROOT / name))
    for name, expected in pins.items():
        require(sha(ROOT / name) == expected, "Input changed")
    result = {
        "status": "stable_pilot_batch_context_only",
        "source_sha256": pins,
        "inner_sha256": inner,
        "case_count": len(results),
        "point_count": sum(len(row["point_ids"]) for row in results),
        "cases": results,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
        "final_merge_performed": False,
    }
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    output = ROOT / BASE / "pu_stable_batch_v1" / stamp / "readback.json"
    output.parent.mkdir(parents=True, exist_ok=False)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(output.read_text(encoding="utf-8")) == result, "JSON readback")
    print(output.relative_to(ROOT).as_posix(), sha(output))
    print("pins", len(pins), "nominal packets", len(inner), "cases", len(results))


if __name__ == "__main__":
    main()
