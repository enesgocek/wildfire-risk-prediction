import pytest

from wildfire_risk_prediction.prototype_geography import bounds, path, rings


def polygon():
    return {
        "type": "Polygon",
        "coordinates": [
            [[25, 35], [26, 35], [26, 36], [25, 36], [25, 35]],
            [[25.2, 35.2], [25.4, 35.2], [25.4, 35.4], [25.2, 35.2]],
        ],
    }


def test_polygon_hole_and_multipolygon_rings_remain_separate():
    geometry = polygon()
    assert len(rings(geometry)) == 2 and bounds(geometry) == [25, 35, 26, 36]
    transform = {"west": 25, "north": 36, "x_scale": 100, "y_scale": 120}
    svg = path(geometry, transform)
    assert svg.count("M") == svg.count("Z") == 2
    assert svg.startswith("M0.000000,120.000000")
    multi = {
        "type": "MultiPolygon",
        "coordinates": [geometry["coordinates"], geometry["coordinates"]],
    }
    assert path(multi, transform).count("M") == 4


def test_nonfinite_vertices_and_unclosed_ring_are_rejected():
    with pytest.raises(ValueError, match="Finite WGS84"):
        bounds({"type": "Polygon", "coordinates": [[[float("nan"), 35]] * 4]})
    with pytest.raises(ValueError, match="Closed"):
        path(
            {"type": "Polygon", "coordinates": [[[25, 35], [26, 35], [26, 36], [25, 36]]]},
            {"west": 25, "north": 36, "x_scale": 1, "y_scale": 1},
        )
