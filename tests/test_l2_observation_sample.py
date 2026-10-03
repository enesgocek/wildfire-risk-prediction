"""Prevent mismatched swaths, bounding-box false hits and QA misinterpretation."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
from shapely.geometry import Polygon

SPEC = importlib.util.spec_from_file_location(
    "sample", Path(__file__).resolve().parents[1] / "scripts/firms/inspect_l2_observation_sample.py"
)
sample = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sample)
FIRE = Path("VNP14IMG.A2019014.1018.002.2024086175855.nc")
GEO = Path("VNP03IMG.A2019014.1018.002.2021102055836.nc")


@pytest.mark.parametrize("year", [2024, 2025])
def test_non_training_file_is_rejected_before_array_read(year):
    with pytest.raises(ValueError, match="training"):
        sample.training_key(FIRE.name.replace("A2019014", f"A{year}014"))


def test_non_leap_day_does_not_roll_into_next_year():
    with pytest.raises(ValueError, match="day-of-year"):
        sample.training_key(FIRE.name.replace("A2019014", "A2019366"))


def test_same_time_but_different_processing_input_is_rejected():
    common = {"StartTime": "2019-01-14 10:18:00.000", "EndTime": "2019-01-14 10:24:00.000"}
    fire_tags = dict(common, ShortName="VNP14IMG", VNP03IMG=GEO.name)
    geo_tags = dict(common, ShortName="VNP03IMG", LocalGranuleID=GEO.name)
    assert sample.validate_pair(FIRE, GEO, fire_tags, geo_tags) == "2019014.1018"
    fire_tags["VNP03IMG"] = GEO.name.replace("2021102055836", "2021102055837")
    with pytest.raises(ValueError, match="actual geolocation input"):
        sample.validate_pair(FIRE, GEO, fire_tags, geo_tags)


def test_shifted_acquisition_interval_is_rejected():
    fire_tags = {
        "StartTime": "2019-01-14 10:18:00.000",
        "EndTime": "2019-01-14 10:24:00.000",
        "ShortName": "VNP14IMG",
        "VNP03IMG": GEO.name,
    }
    geo_tags = dict(fire_tags, ShortName="VNP03IMG", LocalGranuleID=GEO.name)
    geo_tags["EndTime"] = "2019-01-14 10:30:00.000"
    with pytest.raises(ValueError, match="interval mismatch"):
        sample.validate_pair(FIRE, GEO, fire_tags, geo_tags)


def test_polygon_hole_is_not_observed_even_when_bbox_hits():
    aoi = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)], holes=[[(1, 1), (2, 1), (2, 2), (1, 2)]])
    lon = np.array([0.0, 1.5, 4.0, -999.9, np.nan])
    lat = np.array([0.0, 1.5, 1.0, 1.0, 1.0])
    valid, bbox, inside = sample.pilot_selection(lon, lat, aoi)
    np.testing.assert_array_equal(valid, [True, True, True, False, False])
    np.testing.assert_array_equal(bbox, [True, True, False, False, False])
    np.testing.assert_array_equal(inside, [True, False, False, False, False])


def test_fire_test_bits_are_not_input_failure_or_residual_bowtie():
    qa = np.array([0, 1 << 10, 1 << 5, 1 << 22, (1 << 3) | (1 << 22)], dtype="uint32")
    bad, geo_bad, residual = sample.input_quality_flags(qa)
    np.testing.assert_array_equal(bad, [False, False, True, False, True])
    np.testing.assert_array_equal(geo_bad, [False, False, True, False, False])
    np.testing.assert_array_equal(residual, [False, False, False, True, True])


def test_same_size_corrupted_download_fails_cmr_checksum(tmp_path):
    path = tmp_path / GEO.name
    path.write_bytes(b"incorrect")
    meta = {
        "CollectionReference": {"ShortName": "VNP03IMG", "Version": "2"},
        "RelatedUrls": [{"URL": "https://example.org/" + GEO.name}],
        "DataGranule": {
            "ArchiveAndDistributionInformation": [
                {"SizeInBytes": 9, "Checksum": {"Algorithm": "MD5", "Value": "0" * 32}}
            ]
        },
    }
    metadata_path = tmp_path / "cmr.json"
    metadata_path.write_text(json.dumps(meta), encoding="utf-8")
    with pytest.raises(ValueError, match="checksum mismatch"):
        sample.verify_cmr(path, metadata_path, "VNP03IMG")


def test_nominal_qa_does_not_turn_cloud_or_missing_pixels_into_observed_land():
    mask = np.array([0, 1, 3, 4, 5, 5, 5, 8], dtype="uint8")
    qa = np.array([0, 0, 0, 0, 1 << 10, 1 << 3, 1 << 22, 0], dtype="uint32")
    np.testing.assert_array_equal(
        sample.diagnostic_land(mask, qa), [False, False, False, False, True, False, False, False]
    )


N20_FIRE = Path("VJ114IMG.A2019014.0930.002.2024024073342.nc")
N20_GEO = Path("VJ103IMG.A2019014.0930.021.2021037000804.nc")


def n20_tags():
    common = {"StartTime": "2019-01-14 09:30:00.000", "EndTime": "2019-01-14 09:36:00.000"}
    return (
        dict(common, ShortName="VJ114IMG", VJ103IMG=N20_GEO.name),
        dict(common, ShortName="VJ103IMG", LocalGranuleID=N20_GEO.name),
    )


def test_noaa20_fire_and_geolocation_versions_are_distinguished():
    assert sample.product_identity(N20_FIRE.name)[:3] == ("N20", "fire", "2019014.0930")
    assert sample.product_identity(N20_GEO.name)[:3] == ("N20", "geolocation", "2019014.0930")
    with pytest.raises(ValueError, match="version"):
        sample.product_identity(N20_GEO.name.replace(".021.", ".002."))


@pytest.mark.parametrize("year", [2024, 2025])
def test_noaa20_non_training_files_are_rejected(year):
    with pytest.raises(ValueError, match="training"):
        sample.training_key(N20_FIRE.name.replace("A2019014", f"A{year}014"))


def test_same_time_different_sensor_is_rejected():
    fire_tags, geo_tags = n20_tags()
    with pytest.raises(ValueError, match="Sensor mismatch"):
        sample.validate_pair(N20_FIRE, Path(GEO.name.replace("1018", "0930")), fire_tags, geo_tags)


@pytest.mark.parametrize("reference", ["VJ103IMG", "VNP03IMG", "InputPointer"])
def test_noaa20_requires_exact_processing_input(reference):
    fire_tags, geo_tags = n20_tags()
    fire_tags.pop("VJ103IMG")
    fire_tags[reference] = ("radiance.nc," if reference == "InputPointer" else "") + N20_GEO.name
    assert sample.validate_pair(N20_FIRE, N20_GEO, fire_tags, geo_tags) == "2019014.0930"
    fire_tags[reference] = fire_tags[reference].replace("2021037000804", "2021037000805")
    with pytest.raises(ValueError, match="actual geolocation input"):
        sample.validate_pair(N20_FIRE, N20_GEO, fire_tags, geo_tags)


def test_noaa20_report_names_cannot_overwrite_snpp_same_time():
    assert sample.sample_stem("SNPP", "2019014.0930") != sample.sample_stem("N20", "2019014.0930")


def test_empty_sparse_fire_datasets_are_not_opened(monkeypatch):
    def fail(*args):
        pytest.fail("Attempted to open empty sparse dataset")

    monkeypatch.setattr(sample, "layer", fail)
    result = sample.read_sparse(None, N20_FIRE, 0)
    assert all(len(v) == 0 for v in result.values())
