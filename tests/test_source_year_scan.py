from collections import Counter
from io import BytesIO

import pandas as pd
import pytest

from wildfire_risk_prediction.feature_join import utc_times
from wildfire_risk_prediction.source_year_scan import canonical_utc_text, normalized_year_rows


def test_closed_year_invalid_text_never_reaches_decoder():
    stream = BytesIO(
        b"detection_timestamp_utc,id,quality\n"
        b"2023-12-31T23:59:00+00:00,closed,\xff\n"
        b"2024-01-01T00:00:00+00:00,open,n\n"
        b"2025-01-01T00:00:00+00:00,final,\xff\n"
    )
    counts = Counter()
    result = list(normalized_year_rows(stream, year=2024, counts=counts))
    assert [row["id"] for row in result] == ["open"]
    assert counts["other_year_records_left_opaque"] == 2


def test_legacy_space_separator_preserved_without_opening_other_years():
    counts = Counter()
    stream = BytesIO(
        b"detection_timestamp_utc,id,quality\n"
        b"2023-12-31 23:59:00+00:00,closed,\xff\n"
        b"2024-01-01 00:00:00+00:00,open,n\n"
    )
    result = list(normalized_year_rows(stream, year=2024, counts=counts))
    assert result[0]["detection_timestamp_utc"] == "2024-01-01 00:00:00+00:00"
    assert counts["other_year_records_left_opaque"] == 1


def test_catalog_and_weather_legacy_separator_do_not_shift_day_or_UTC_time():
    values = pd.Series(["2024-01-01 00:00:00+00:00", "2024-01-01T00:00:00+00:00"])
    normalized = utc_times(values.map(canonical_utc_text))
    assert normalized.eq(pd.Timestamp("2024-01-01T00:00:00Z")).all()


@pytest.mark.parametrize(
    "record", [b'2024-01-01T00:00:00Z,"a,b",n\n', b"2024-01-01T00:00:00Z,a\n", b"bad-time,a,n\n"]
)
def test_unexpected_source_layout_fails_before_year_selection(record):
    with pytest.raises(ValueError):
        list(
            normalized_year_rows(
                BytesIO(b"detection_timestamp_utc,id,quality\n" + record),
                year=2024,
                counts=Counter(),
            )
        )
