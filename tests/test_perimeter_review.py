"""Axis order, temporal scope, missingness and ambiguous reference links stay explicit."""

import copy

import geopandas as gpd
import pandas as pd
import pytest
from geopandas.testing import assert_geodataframe_equal
from shapely.geometry import Polygon, box

from wildfire_risk_prediction.perimeter_review import effis_gml, medeu_inventory, spatial_context


def gml(kind="Polygon"):
    polygon = """<gml:Polygon srsName="EPSG:4326"><gml:exterior><gml:LinearRing>
    <gml:posList srsDimension="2">36 31 36 32 37 32 37 31 36 31</gml:posList>
    </gml:LinearRing></gml:exterior></gml:Polygon>"""
    geometry = (
        polygon
        if kind == "Polygon"
        else (
            '<gml:MultiSurface srsName="EPSG:4326"><gml:surfaceMember>'
            + polygon
            + "</gml:surfaceMember></gml:MultiSurface>"
        )
    )
    return (
        """<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs"
      xmlns:ms="http://mapserver.gis.umn.edu/mapserver" xmlns:gml="http://www.opengis.net/gml">
      <gml:featureMember><ms:modis.ba.poly><ms:id>001</ms:id>
      <ms:FIREDATE>2021-07-28 09:00:00</ms:FIREDATE><ms:FINALDATE>2021-08-06 23:03:00</ms:FINALDATE>
      <ms:COUNTRY>TR</ms:COUNTRY><ms:PROVINCE>Antalya</ms:PROVINCE><ms:AREA_HA>5</ms:AREA_HA>
      <gml:boundedBy><gml:Envelope><gml:lowerCorner>36 31</gml:lowerCorner>
      <gml:upperCorner>37 32</gml:upperCorner></gml:Envelope></gml:boundedBy><ms:msGeometry>"""
        + geometry
        + "</ms:msGeometry></ms:modis.ba.poly></gml:featureMember></wfs:FeatureCollection>"
    ).encode()


@pytest.mark.parametrize("kind", ["Polygon", "MultiSurface"])
def test_wfs_latitude_longitude_axes_and_string_identity(kind):
    frame = effis_gml(gml(kind))
    assert frame.reference_id.tolist() == ["001"]
    assert frame.geometry.iloc[0].bounds == (31.0, 36.0, 32.0, 37.0)
    assert frame.geometry_valid.all()


@pytest.mark.parametrize("change", ["future", "wrong_crs", "wrong_envelope", "entity", "unclosed"])
def test_source_mismatch_or_unsafe_xml_rejected(change):
    data = gml()
    if change == "future":
        data = data.replace(b"2021-07-28", b"2025-07-28")
    elif change == "wrong_crs":
        data = data.replace(b"EPSG:4326", b"EPSG:3857")
    elif change == "wrong_envelope":
        data = data.replace(b"36 31</gml:lowerCorner>", b"31 36</gml:lowerCorner>")
    elif change == "entity":
        data = b'<!DOCTYPE sample [<!ENTITY secret SYSTEM "file:///private">]>' + data
    else:
        data = data.replace(b"37 31 36 31</gml:posList>", b"37 31 36 31.5</gml:posList>")
    with pytest.raises(ValueError):
        effis_gml(data)


def test_prefire_placeholder_and_missing_step_never_become_burned_or_negative():
    invalid = Polygon([(0, 0), (2, 2), (0, 2), (2, 0), (0, 0)])
    frame = gpd.GeoDataFrame(
        {
            "EFFIS_id": [1] * 4,
            "Acqu_date": ["2021-07-27", "2021-07-28", "2021-07-29", "2021-07-30"],
            "Prop_step": [0, 1, float("nan"), 2],
        },
        geometry=[box(0, 0, 1, 1), box(0, 0, 10, 10), None, invalid],
        crs=3035,
    )
    before = frame.copy(deep=True)
    inventory = medeu_inventory(frame)
    assert inventory.is_burned_step.tolist() == [False, True, False, True]
    assert inventory.training_burned_reference_candidate.tolist() == [False, True, False, False]
    assert inventory.is_pre_fire_context.tolist() == [True, False, False, False]
    assert_geodataframe_equal(before, frame)


def fixture():
    case = pd.DataFrame(
        [
            {
                "cluster_id": "C",
                "scenario": "test",
                "event_status": "exploratory_cluster_only",
                "first_detection_utc": "2021-07-28T10:00:00Z",
                "last_detection_utc": "2021-08-02T10:00:00Z",
                "detection_count": 3,
                "earliest_grid_ids_json": '["G1","G2"]',
            }
        ]
    )
    members = pd.DataFrame(
        {
            "cluster_id": ["C"] * 3,
            "detection_id": ["a", "b", "c"],
            "grid_id": ["G1", "G2", "G3"],
            "longitude": [31.5, 32, 32.5],
            "latitude": [36.5] * 3,
            "detection_timestamp_utc": ["2021-07-28T10:00:00Z"] * 2 + ["2021-08-02T10:00:00Z"],
        }
    )
    refs = gpd.GeoDataFrame(
        {
            "reference_id": ["R1", "R2"],
            "FIREDATE": ["2021-07-28", "2021-08-20"],
            "FINALDATE": ["2021-08-05", "2021-08-21"],
            "PROVINCE": ["example"] * 2,
            "geometry_valid": [True] * 2,
        },
        geometry=[box(31, 36, 32, 37), box(32, 36, 33, 37)],
        crs=4326,
    )
    return case, members, refs


def test_spatial_boundary_ambiguity_and_calendar_mismatch_are_not_identity_or_targets():
    cases, members, refs = fixture()
    original = copy.deepcopy(members)
    links, summary = spatial_context(cases, members, refs)
    assert len(links) == 2 and summary.reference_count_with_first.tolist() == [2]
    assert summary.member_rows_in_any_reference.tolist() == [3]  # boundary counted once in union
    assert links.calendar_interval_overlap_hint.tolist() == [True, False]
    assert links.identity_accepted.eq(False).all() and links.target.isna().all()
    assert summary.first_grid_count.tolist() == [2]
    pd.testing.assert_frame_equal(members, original)


@pytest.mark.parametrize("change", ["tie_lost", "count", "holdout", "invalid_reference"])
def test_case_evidence_mismatch_is_rejected(change):
    cases, members, refs = fixture()
    if change == "tie_lost":
        cases["earliest_grid_ids_json"] = '["G1"]'
    elif change == "count":
        cases["detection_count"] = 4
    elif change == "holdout":
        cases["first_detection_utc"] = "2025-07-28T10:00:00Z"
    else:
        refs["geometry_valid"] = False
    with pytest.raises(ValueError):
        spatial_context(cases, members, refs)
