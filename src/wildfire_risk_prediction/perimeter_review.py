"""Bounded historical reference perimeters and spatial diagnostics, never binary targets."""

import json
import xml.etree.ElementTree as ET

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import MultiPolygon, Point, Polygon

from wildfire_risk_prediction.feature_join import require

NS = {"ms": "http://mapserver.gis.umn.edu/mapserver", "gml": "http://www.opengis.net/gml"}


def effis_gml(data):
    """Read inspected WFS1.1/GML3 EPSG:4326 lat/lon; never resolve remote schemas."""
    require(
        len(data) <= 10_000_000 and b"<!DOCTYPE" not in data and b"<!ENTITY" not in data,
        "Bounded XML without external entity declarations",
    )
    root = ET.fromstring(data)
    require(root.tag == "{http://www.opengis.net/wfs}FeatureCollection", "WFS feature collection")
    rows = []

    def ring(element):
        require(element is not None, "Polygon exterior ring")
        values = element.findall(".//gml:posList", NS)
        require(len(values) == 1 and values[0].get("srsDimension") == "2", "2D GML ring")
        numbers = np.array([float(v) for v in values[0].text.split()])
        require(
            len(numbers) >= 8 and len(numbers) % 2 == 0 and np.isfinite(numbers).all(),
            "Finite closed coordinate ring",
        )
        latlon = numbers.reshape(-1, 2)
        require(
            np.array_equal(latlon[0], latlon[-1])
            and np.abs(latlon[:, 0]).max() <= 90
            and np.abs(latlon[:, 1]).max() <= 180,
            "Latitude-longitude ring bounds",
        )
        return latlon[:, ::-1]

    for record in root.findall(".//ms:modis.ba.poly", NS):
        row = {
            k: record.findtext("ms:" + k, namespaces=NS)
            for k in ("id", "FIREDATE", "FINALDATE", "COUNTRY", "PROVINCE", "AREA_HA")
        }
        require(
            all(row[k] for k in ("id", "FIREDATE", "FINALDATE", "COUNTRY")),
            "Reference identity and dates",
        )
        start, end = pd.Timestamp(row["FIREDATE"]), pd.Timestamp(row["FINALDATE"])
        require(
            start.tzinfo is None
            and end.tzinfo is None
            and pd.Timestamp("2021-07-01") <= start < pd.Timestamp("2021-09-01")
            and start <= end < pd.Timestamp("2024-01-01"),
            "Filtered training period only",
        )
        geometry = record.find("ms:msGeometry", NS)
        require(geometry is not None, "Reference geometry present")
        surface = geometry[0] if len(geometry) == 1 else None
        require(
            surface is not None
            and surface.tag in {"{" + NS["gml"] + "}MultiSurface", "{" + NS["gml"] + "}Polygon"}
            and surface.get("srsName") == "EPSG:4326",
            "Inspected WFS1.1 latitude-longitude CRS",
        )
        polygons = []
        components = (
            [surface] if surface.tag.endswith("}Polygon") else surface.findall(".//gml:Polygon", NS)
        )
        for poly in components:
            exterior = ring(poly.find("gml:exterior", NS))
            interiors = [ring(h) for h in poly.findall("gml:interior", NS)]
            polygons.append(Polygon(exterior, interiors))
        require(polygons, "Polygon components")
        shape = polygons[0] if len(polygons) == 1 else MultiPolygon(polygons)
        # A second independent axis-order check against the server's feature envelope.
        lower = np.fromstring(
            record.findtext("gml:boundedBy/gml:Envelope/gml:lowerCorner", namespaces=NS), sep=" "
        )
        upper = np.fromstring(
            record.findtext("gml:boundedBy/gml:Envelope/gml:upperCorner", namespaces=NS), sep=" "
        )
        require(
            len(lower) == len(upper) == 2
            and np.allclose(
                shape.bounds, [lower[1], lower[0], upper[1], upper[0]], rtol=0, atol=1e-6
            ),
            "Geometry agrees with WFS envelope",
        )
        row["geometry"] = shape
        row["geometry_valid"] = bool(shape.is_valid and not shape.is_empty)
        rows.append(row)
    require(rows and len(rows) <= 100, "Bounded nonempty reference selection")
    result = gpd.GeoDataFrame(rows, crs="EPSG:4326")
    require(result.id.is_unique, "Unique EFFIS identities")
    return result.rename(columns={"id": "reference_id"})


def medeu_inventory(frame):
    """Prop_step zero geometries are context placeholders, not burned areas or negatives."""
    require(frame.crs.to_epsg() == 3035, "Published MedEU CRS")
    dates = pd.to_datetime(frame.Acqu_date, errors="raise")
    require(dates.dt.year.between(2017, 2023).all(), "Published reference scope; no holdout")
    step = frame.Prop_step
    require(
        step.dropna().ge(0).all() and step.dropna().eq(step.dropna().round()).all(),
        "Nonnegative integer propagation steps",
    )
    burned = step.gt(0)
    require(frame.loc[burned].geometry.notna().all(), "Positive steps need perimeter geometry")
    return pd.DataFrame(
        {
            "reference_id": frame.EFFIS_id,
            "acquisition_date": frame.Acqu_date,
            "propagation_step": step,
            "is_burned_step": burned,
            "is_pre_fire_context": step.eq(0),
            "geometry_present": frame.geometry.notna(),
            "geometry_valid": frame.is_valid,
            "training_burned_reference_candidate": burned & dates.dt.year.ge(2018) & frame.is_valid,
        }
    )


def spatial_context(cases, members, references):
    """Point-in-final-perimeter context without identity, daily burning or absence inference."""
    require(
        cases.cluster_id.is_unique and cases.event_status.eq("exploratory_cluster_only").all(),
        "Unique exploratory cases",
    )
    first = pd.to_datetime(cases.first_detection_utc, utc=True, errors="raise")
    require(first.dt.year.between(2018, 2023).all(), "Training case catalog")
    selected = cases.loc[first.ge("2021-07-01") & first.lt("2021-09-01")]
    require(
        not selected.empty and references.crs.to_epsg() == 4326 and references.geometry_valid.all(),
        "Scoped cases and valid reference geometry",
    )
    members = members.loc[members.cluster_id.isin(selected.cluster_id)].copy()
    require(not members.duplicated(["cluster_id", "detection_id"]).any(), "Unique member keys")
    counts = members.groupby("cluster_id").size()
    require(
        counts.to_dict() == selected.set_index("cluster_id").detection_count.to_dict(),
        "Retained case-member counts",
    )
    members["time"] = pd.to_datetime(members.detection_timestamp_utc, utc=True, errors="raise")
    require(members.time.dt.year.between(2018, 2023).all(), "Training members only")
    members["is_first"] = members.time.eq(members.groupby("cluster_id").time.transform("min"))
    for case in selected.itertuples():
        group = members.loc[members.cluster_id.eq(case.cluster_id)]
        require(
            group.time.min() == pd.Timestamp(case.first_detection_utc)
            and sorted(group.loc[group.is_first, "grid_id"].unique())
            == json.loads(case.earliest_grid_ids_json),
            "All tied first cells retained",
        )
    points = gpd.GeoDataFrame(
        members,
        geometry=[Point(x, y) for x, y in zip(members.longitude, members.latitude, strict=True)],
        crs=4326,
    )
    joined = gpd.sjoin(points, references, how="inner", predicate="intersects")
    rows, summaries = [], []
    for case in selected.itertuples():
        group = members.loc[members.cluster_id.eq(case.cluster_id)]
        hits = joined.loc[joined.cluster_id.eq(case.cluster_id)]
        summaries.append(
            {
                "cluster_id": case.cluster_id,
                "scenario": case.scenario,
                "member_rows": len(group),
                "first_rows": int(group.is_first.sum()),
                "first_grid_count": len(json.loads(case.earliest_grid_ids_json)),
                "reference_count_with_member": int(hits.reference_id.nunique()),
                "reference_count_with_first": int(hits.loc[hits.is_first].reference_id.nunique()),
                "member_rows_in_any_reference": int(hits.detection_id.nunique()),
                "first_rows_in_any_reference": int(hits.loc[hits.is_first].detection_id.nunique()),
                "identity_accepted": False,
                "target": pd.NA,
            }
        )
        for reference_id, hit in hits.groupby("reference_id"):
            ref = references.set_index("reference_id").loc[reference_id]
            rows.append(
                {
                    "cluster_id": case.cluster_id,
                    "scenario": case.scenario,
                    "reference_id": reference_id,
                    "reference_province": ref.PROVINCE,
                    "reference_start_raw": ref.FIREDATE,
                    "reference_end_raw": ref.FINALDATE,
                    "member_rows_inside_or_boundary": int(hit.detection_id.nunique()),
                    "member_rows": len(group),
                    "first_rows_inside_or_boundary": int(
                        hit.loc[hit.is_first].detection_id.nunique()
                    ),
                    "first_rows": int(group.is_first.sum()),
                    "calendar_interval_overlap_hint": bool(
                        pd.Timestamp(case.first_detection_utc).date()
                        <= pd.Timestamp(ref.FINALDATE).date()
                        and pd.Timestamp(case.last_detection_utc).date()
                        >= pd.Timestamp(ref.FIREDATE).date()
                    ),
                    "link_status": "spatial_context_only",
                    "identity_accepted": False,
                    "source_independence": "shared_satellite_lineage_not_independent_ground_truth",
                    "target": pd.NA,
                }
            )
    require(rows, "Some spatial context links found")
    return pd.DataFrame(rows), pd.DataFrame(summaries)
