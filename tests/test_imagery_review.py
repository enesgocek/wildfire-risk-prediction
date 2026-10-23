import numpy as np
import pytest
from affine import Affine
from shapely.geometry import box

from wildfire_risk_prediction.imagery_review import bounded_window, support_quality


def test_quality_counts_include_unknown_and_do_not_label_vegetation_forest():
    array = np.arange(12, dtype="uint8").reshape(3, 4)
    result = support_quality(
        array, np.ones_like(array, dtype=bool), Affine(20, 0, 0, 0, -20, 60), box(0, 0, 80, 60)
    )
    assert result["support_pixel_centres"] == 12
    assert sum(result["scl_counts"].values()) == 12
    assert result["cloud_cirrus_fraction"] == 3 / 12
    assert result["nodata_defective_fraction"] == 2 / 12
    assert result["vegetation_fraction_not_forest"] == 1 / 12
    assert not result["habitat_accepted"] and not result["fire_label_accepted"]


def test_invalid_source_mask_is_nodata_even_when_value_vegetation():
    array = np.full((2, 2), 4, dtype="uint8")
    valid = np.array([[True, False], [True, True]])
    result = support_quality(array, valid, Affine(20, 0, 0, 0, -20, 40), box(0, 0, 40, 40))
    assert result["nodata_defective_fraction"] == 0.25
    assert result["vegetation_fraction_not_forest"] == 0.75


def test_polygon_excludes_clouds_outside_support():
    array = np.array([[4, 9], [5, 9]], dtype="uint8")
    result = support_quality(
        array, np.ones_like(array, dtype=bool), Affine(20, 0, 0, 0, -20, 40), box(0, 0, 20, 40)
    )
    assert result["support_pixel_centres"] == 2
    assert result["cloud_cirrus_fraction"] == 0


@pytest.mark.parametrize("code", [12, 255])
def test_unknown_scl_code_rejected(code):
    array = np.full((2, 2), code, dtype="uint8")
    with pytest.raises(ValueError):
        support_quality(
            array, np.ones_like(array, dtype=bool), Affine(20, 0, 0, 0, -20, 40), box(0, 0, 40, 40)
        )


def test_empty_support_rejected():
    array = np.zeros((2, 2), dtype="uint8")
    with pytest.raises(ValueError):
        support_quality(
            array, array.astype(bool), Affine(20, 0, 0, 0, -20, 40), box(80, 80, 100, 100)
        )


def test_window_rounds_outward_preserving_context():
    window = bounded_window((1001, 1001, 1201, 1201), Affine(10, 0, 0, 0, -10, 3000), 300, 300)
    assert window.col_off == 50
    assert window.row_off == 129
    assert window.width == 121 and window.height == 121


@pytest.mark.parametrize("bounds", [(1, 1, 20, 20), (800, 800, 2800, 2800)])
def test_window_boundary_or_size_not_silently_clipped(bounds):
    with pytest.raises(ValueError):
        bounded_window(bounds, Affine(10, 0, 0, 0, -10, 4000), 400, 400)


def test_explicit_context_clip_preserves_entire_scientific_support():
    window = bounded_window(
        (1, 1, 20, 20), Affine(10, 0, 0, 0, -10, 1000), 100, 100, clip_context=True
    )
    assert window.col_off == 0 and window.row_off + window.height == 100
    with pytest.raises(ValueError, match="Approximate support"):
        bounded_window((-1, 1, 20, 20), Affine(10, 0, 0, 0, -10, 1000), 100, 100, clip_context=True)
