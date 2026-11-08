"""Audit five habitat pilot anchors against grouping, scan support and local perimeters."""

import hashlib
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pandas as pd
from geopandas import GeoSeries
from review_perimeter_sources import EFFIS, EFFIS_SHA
from review_pu_candidate_timeline import GRAPH, prior_neighbourhood
from review_pu_stable_batch import catalogue_sources, scan_windows
from review_public_event_cover import require, sha
from run_stratified_cover_pilot import BASE, ROOT, read_json, write_json
from shapely.geometry import Point

from wildfire_risk_prediction.event_review import GEOD
from wildfire_risk_prediction.perimeter_review import effis_gml
from wildfire_risk_prediction.preevent_imagery import prediction_time

PILOT = BASE / "stratified_cover_pilot_v1/20261108T002035Z_de57b547/plan.json"
PILOT_SHA = "706a7c2ad0676f4bdb24df970e23880e81f7c94f082bde2d799a4a32ab0e55aa"
SLOTS = ("H03", "H04", "H12", "H14", "H22")
ARCHIVES = (
    "data/raw/firms/815579/fire_archive_SV-C2_815579.csv",
    "data/raw/firms/815590/fire_archive_J1V-C2_815590.csv",
)


def memberships(anchors, graph, retain):
    summaries = {key: [] for key in anchors}
    for name, digests in sorted(graph["artifact_sha256"].items()):
        path = retain(
            f"data/interim/event_grouping/{name}_assignments.csv", digests["assignments_sha256"]
        )
        assignments = pd.read_csv(path).set_index("detection_id", verify_integrity=True)
        reviews = pd.read_csv(
            retain(f"{GRAPH}/{name}_review.csv", digests["review_sha256"])
        ).set_index("cluster_id", verify_integrity=True)
        for key, point in anchors.items():
            cluster = assignments.loc[point.detection_id, "cluster_id"]
            rows = assignments.loc[assignments.cluster_id.eq(cluster)]
            times = pd.to_datetime(rows.timestamp, utc=True, format="ISO8601")
            review = reviews.loc[cluster]
            digest = hashlib.sha256("\n".join(sorted(rows.index)).encode()).hexdigest()
            require(
                list(rows.index[times.eq(times.min())]) == [point.detection_id]
                and times.min() == point.timestamp == pd.Timestamp(review.first_detection_utc)
                and times.max() == pd.Timestamp(review.last_detection_utc)
                and len(rows) == review.detection_count
                and digest == review.membership_sha256,
                "Anchor and group identity",
            )
            summaries[key].append(
                {
                    "scenario": name,
                    "group": cluster,
                    "count": len(rows),
                    "last_utc": times.max().isoformat(),
                    "membership_sha256": digest,
                }
            )
    require(all(len(rows) == 9 for rows in summaries.values()), "Nine group scenarios")
    return summaries


def archive_context(archives, point):
    stamp = pd.Timestamp(point["timestamp"])
    start = stamp.to_pydatetime() - timedelta(hours=72)
    earlier = archives.loc[archives.timestamp.ge(start) & archives.timestamp.lt(stamp)].copy()
    _, _, distance = GEOD.inv(
        [point.longitude] * len(earlier),
        [point.latitude] * len(earlier),
        earlier.longitude.to_numpy(),
        earlier.latitude.to_numpy(),
    )
    earlier["distance_m"] = distance
    nearby = earlier.loc[earlier.distance_m.le(2000)]
    return {
        "by_type_and_confidence_within_2km": dict(
            sorted(Counter(f"{row.type}:{row.confidence}" for row in nearby.itertuples()).items())
        ),
        "nearest_within_2km": None if nearby.empty else float(nearby.distance_m.min()),
    }


def perimeter_context(refs, point):
    if (
        not pd.Timestamp("2021-07-01", tz="UTC")
        <= point.timestamp
        < pd.Timestamp("2021-09-01", tz="UTC")
    ):
        return {"state": "outside_local_effis_slice"}
    start = pd.to_datetime(refs.FIREDATE, format="ISO8601").dt.normalize()
    end = pd.to_datetime(refs.FINALDATE, format="ISO8601").dt.normalize()
    day = point.timestamp.tz_localize(None).normalize()
    candidates = refs.loc[start.le(day) & end.ge(day)]
    zone = 32635 if point.longitude < 30 else 32636
    center = Point(point.longitude, point.latitude)
    projected = GeoSeries([center], crs=4326).to_crs(zone).iloc[0]
    distance = candidates.to_crs(zone).distance(projected)
    nearest = None
    if not distance.empty:
        entry = candidates.loc[distance.idxmin()]
        nearest = {
            "id": entry.reference_id,
            "distance_m": float(distance.min()),
            "start_as_reported": entry.FIREDATE,
            "end_as_reported": entry.FINALDATE,
        }
    return {
        "state": "retained_effis_date_overlap",
        "covers_ids": sorted(candidates.loc[candidates.geometry.covers(center), "reference_id"]),
        "nearest_date_overlap": nearest,
    }


def main():
    pins = {}

    def retain(name, expected=None):
        path = ROOT / name
        require(path.resolve(strict=True).is_relative_to(ROOT), "Contained input")
        actual = sha(path)
        require(expected is None or actual == expected, "Input digest")
        pins[path.relative_to(ROOT).as_posix()] = actual
        return path

    plan = read_json(retain(PILOT, PILOT_SHA))
    pilot = {row["slot"]: row for row in plan["selected"] if row["slot"] in SLOTS}
    require(tuple(pilot) == SLOTS, "Fixed cover-supported pilot anchors")
    graph = read_json(
        retain(
            f"{GRAPH}/review.json",
            "61de3f798bb1462baf4f1d65bebc72539cef47467d5590baeec498951dc94d7e",
        )
    )
    source = catalogue_sources(retain, graph)
    index = source.set_index("detection_id", drop=False, verify_integrity=True)
    anchors = {key: index.loc[p["id"]] for key, p in pilot.items()}
    for key, anchor in anchors.items():
        p = pilot[key]
        require(
            anchor.timestamp == pd.Timestamp(p["detected_utc"])
            and anchor.grid_id == p["grid"]
            and (anchor.longitude, anchor.latitude) == (p["longitude"], p["latitude"]),
            "Pinned FIRMS source point",
        )
    groups = memberships(anchors, graph, retain)
    archives = pd.concat(
        [
            pd.read_csv(
                retain(name),
                usecols=["latitude", "longitude", "acq_date", "acq_time", "type", "confidence"],
                dtype={"acq_time": str},
            )
            for name in ARCHIVES
        ],
        ignore_index=True,
    )
    archives = archives.loc[archives.acq_date.str[:4].between("2018", "2023")].copy()
    archives["timestamp"] = pd.to_datetime(
        archives.acq_date + archives.acq_time.str.zfill(4), format="%Y-%m-%d%H%M", utc=True
    )
    cases = {
        key: {
            "grid_id": p["grid"],
            "prediction_utc": prediction_time(p["detected_utc"]).isoformat(),
        }
        for key, p in pilot.items()
    }
    windows, inner = scan_windows(retain, cases, pins)
    refs = effis_gml(retain(EFFIS, EFFIS_SHA).read_bytes())
    require(len(refs) == 84 and refs.geometry_valid.all(), "Retained EFFIS slice")
    result = []
    for key, point in anchors.items():
        result.append(
            {
                **pilot[key],
                "prediction_utc": cases[key]["prediction_utc"],
                "groups": groups[key],
                "distinct_memberships": len({r["membership_sha256"] for r in groups[key]}),
                "prior_eligible_catalogue": prior_neighbourhood(source, point),
                "prior_unfiltered_archive": archive_context(archives, point),
                "observation_windows": windows[key],
                "effis": perimeter_context(refs, point),
                "independent_origin_verified": False,
                "target": None,
            }
        )
    for name in (
        Path(__file__).resolve(),
        ROOT / "scripts/quality/review_pu_stable_batch.py",
        ROOT / "scripts/quality/review_pu_candidate_timeline.py",
        ROOT / "src/wildfire_risk_prediction/observation_window.py",
        ROOT / "src/wildfire_risk_prediction/observation_window_source.py",
    ):
        retain(name)
    require(all(sha(ROOT / name) == expected for name, expected in pins.items()), "Inputs changed")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = BASE / "stratified_event_candidate_v1" / stamp
    out.mkdir(parents=True, exist_ok=False)
    report = {
        "source_sha256": pins,
        "inner_sha256": inner,
        "cases": result,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
        "final_merge_performed": False,
    }
    path = out / "readback.json"
    write_json(path, report)
    print(path.relative_to(ROOT).as_posix(), sha(path), flush=True)


if __name__ == "__main__":
    main()
