import pandas as pd
import pytest

from wildfire_risk_prediction.pilot_time_filter import required_pairs


def sources():
    pairs = [
        {"sample_id": "a", "bytes": 10, "source_day": "2018-02-14"},
        {"sample_id": "b", "bytes": 20, "source_day": "2018-02-15"},
    ]
    table = pd.DataFrame(
        [
            {
                "sample_id": "a",
                "raw_bytes": 10,
                "source_nominal_day": "2018-02-14",
                "scan_count": 203,
                "inside_scan_count": 0,
                "boundary_scan_count": 0,
                "outside_scan_count": 203,
                "decision": "outside_by_full_scan_witness",
            },
            {
                "sample_id": "b",
                "raw_bytes": 20,
                "source_nominal_day": "2018-02-15",
                "scan_count": 203,
                "inside_scan_count": 202,
                "boundary_scan_count": 1,
                "outside_scan_count": 0,
                "decision": "retain_raw_inside_or_boundary",
            },
        ]
    )
    return pairs, table


def test_only_fully_outside_native_witness_is_excluded():
    pairs, table = sources()
    assert required_pairs(pairs, table) == [pairs[1]]
    table.loc[0, ["boundary_scan_count", "outside_scan_count", "decision"]] = [
        1,
        202,
        "retain_raw_inside_or_boundary",
    ]
    assert required_pairs(pairs, table) == pairs


@pytest.mark.parametrize(
    "kind",
    [
        "missing",
        "duplicate",
        "extra",
        "incorrect_decision",
        "unaccounted",
        "fractional",
        "wrong_bytes",
        "wrong_day",
    ],
)
def test_incomplete_or_inconsistent_witness_cannot_cut_source_queue(kind):
    pairs, table = sources()
    if kind == "missing":
        table = table.iloc[:1]
    elif kind == "duplicate":
        table = pd.concat([table, table.iloc[:1]])
    elif kind == "extra":
        table = pd.concat([table, table.iloc[:1].assign(sample_id="other")])
    elif kind == "incorrect_decision":
        table.loc[1, "decision"] = "outside_by_full_scan_witness"
    elif kind == "unaccounted":
        table.loc[0, "outside_scan_count"] = 202
    elif kind == "fractional":
        table["inside_scan_count"] = table.inside_scan_count.astype(float)
        table.loc[0, "inside_scan_count"] = 0.5
    elif kind == "wrong_bytes":
        table.loc[0, "raw_bytes"] = 11
    else:
        table.loc[0, "source_nominal_day"] = "2018-02-13"
    with pytest.raises(ValueError):
        required_pairs(pairs, table)
