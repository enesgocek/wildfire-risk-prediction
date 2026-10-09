"""Scientific regression cases for landscape support, aspect and temporal leakage."""

import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction import landscape as land


def integrals(elevations, slopes, aspects, weights):
    z, slope, angle, area = [
        np.asarray(a, dtype=float) for a in (elevations, slopes, aspects, weights)
    ]
    orient = slope > 0
    return {
        "support_m2": area.sum(),
        "elevation_m_m2": (z * area).sum(),
        "elevation2_m2_m2": (z**2 * area).sum(),
        "slope_deg_m2": (slope * area).sum(),
        "aspect_support_m2": area[orient].sum(),
        "northness_m2": (np.cos(np.deg2rad(angle[orient])) * area[orient]).sum(),
        "eastness_m2": (np.sin(np.deg2rad(angle[orient])) * area[orient]).sum(),
    }


def test_area_weighting_and_circular_north_across_zero():
    result = land.terrain_summary(integrals([10, 30], [20, 20], [359, 1], [1, 1]))
    assert result["elevation_mean_m"] == pytest.approx(20)
    assert result["elevation_std_m"] == pytest.approx(10)
    assert result["northness_mean"] > 0.999
    assert result["eastness_mean"] == pytest.approx(0, abs=1e-12)
    weighted = land.terrain_summary(integrals([10, 30], [0, 30], [0, 90], [3, 1]))
    assert weighted["elevation_mean_m"] == 15
    assert weighted["slope_mean_deg"] == 7.5
    assert weighted["eastness_mean"] == pytest.approx(1)
    assert weighted["aspect_valid_area_m2"] == 1


def test_flat_land_has_elevation_and_slope_but_no_aspect():
    result = land.terrain_summary(integrals([100], [0], [0], [1000]))
    assert result["elevation_mean_m"] == 100
    assert result["slope_mean_deg"] == 0
    assert np.isnan(result["northness_mean"])
    assert np.isnan(result["eastness_mean"])


def test_no_support_is_missing_and_conflicting_values_are_rejected():
    result = land.terrain_summary({})
    assert result["terrain_valid_area_m2"] == 0
    assert np.isnan(result["elevation_mean_m"])
    with pytest.raises(ValueError, match="without terrain"):
        land.terrain_summary({"elevation_m_m2": 1})
    broken = integrals([100], [10], [90], [1])
    broken["elevation2_m2_m2"] = 0
    with pytest.raises(ValueError, match="variance"):
        land.terrain_summary(broken)


def test_landsat_scale_offset_cloud_saturation_and_water():
    # Reflectances red=.2, NIR=.6, SWIR=.4 after source scale and offset.
    def dn(reflectance):
        return (reflectance + 0.2) / 0.0000275

    qa = np.array([0, 8, 16, 32, 128, 2, 4, 1, 64, 0], dtype=np.uint16)
    sat = np.array([0] * 9 + [16], dtype=np.uint16)
    vi, mi, valid = land.landsat_indices(
        np.full(10, dn(0.2)), np.full(10, dn(0.6)), np.full(10, dn(0.4)), qa, sat
    )
    assert valid.tolist() == [True, False, False, False, False, False, False, False, True, False]
    np.testing.assert_allclose(vi[valid], 0.5)
    np.testing.assert_allclose(mi[valid], 0.2)
    assert np.isnan(vi[~valid]).all()


@pytest.mark.parametrize("date", ["2025-01-01", "2017-12-31", "2018-01-01T01:00Z"])
def test_sealed_or_off_contract_dates_rejected(date):
    with pytest.raises(ValueError):
        land.validate_past_window(date, [])


def test_future_and_old_images_rejected_but_strict_past_accepted():
    land.validate_past_window("2018-01-01", ["2017-12-31T23:59:59Z"])
    with pytest.raises(ValueError, match="strict past"):
        land.validate_past_window("2018-01-01", ["2018-01-01T00:00:00Z"])
    with pytest.raises(ValueError, match="strict past"):
        land.validate_past_window("2018-01-01", ["2017-01-01T00:00:00Z"])


def test_missing_dates_and_negative_reflectance_cannot_become_valid():
    with pytest.raises(ValueError, match="date missing"):
        land.validate_past_window(None, [])
    with pytest.raises(ValueError, match="strict past"):
        land.validate_past_window("2018-01-01", [None])
    vi, mi, valid = land.landsat_indices([0], [15000], [15000], [0], [0])
    assert not valid[0]
    assert np.isnan(vi[0]) and np.isnan(mi[0])


def test_cover_all_classes_keys_and_derived_values():
    row = {f"lc_{c}_fraction": 0.0 for c in land.CLASS_CODES}
    row.update(
        grid_id="g",
        reference_year=2017,
        covered_area_km2=1,
        lc_111_fraction=0.5,
        lc_20_fraction=0.5,
        forest_fraction=0.5,
        shrub_fraction=0.5,
        herbaceous_fraction=0,
        agriculture_fraction=0,
        urban_fraction=0,
        water_fraction=0,
        unknown_fraction=0,
        natural_vegetation_fraction=1,
    )
    frame = pd.DataFrame([row])
    pd.testing.assert_frame_equal(land.validate_cover(frame, ["g"]), frame)
    with pytest.raises(ValueError, match="keys"):
        land.validate_cover(frame, ["other"])
    with pytest.raises(ValueError, match="composition"):
        land.validate_cover(frame.assign(forest_fraction=1), ["g"])
