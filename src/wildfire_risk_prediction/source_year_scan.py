"""Year-guarded reading of the repository's normalized unquoted source CSV."""

import csv
import re


def canonical_utc_text(value):
    """Normalize the repository's legacy date/time separator, without shifting time."""
    if len(value) < 11 or value[10] not in {" ", "T"}:
        raise ValueError("Source timestamp separator malformed")
    return value[:10] + "T" + value[11:]


def normalized_year_rows(stream, *, year, counts):
    """Other years stay byte strings; unfamiliar quoting/layout fails closed."""
    header = stream.readline(65537)
    if len(header) > 65536 or not header.endswith(b"\n"):
        raise ValueError("Bounded normalized CSV header required")
    names = next(csv.reader([header.decode("utf-8-sig").strip()]))
    if len(names) != len(set(names)) or "detection_timestamp_utc" not in names:
        raise ValueError("Unique normalized source schema required")
    timestamp_column = names.index("detection_timestamp_utc")
    for raw in stream:
        counts["source_byte_records_scanned"] += 1
        if b'"' in raw or len(raw) > 65536:
            raise ValueError("Unexpected source quoting or record length")
        fields = raw.rstrip(b"\r\n").split(b",")
        if len(fields) != len(names):
            raise ValueError("Normalized source record boundary changed")
        time_metadata = fields[timestamp_column]
        if not re.match(rb"\d{4}-\d{2}-\d{2}[T ]", time_metadata):
            raise ValueError("Source time metadata malformed")
        if time_metadata[:4] != str(year).encode("ascii"):
            counts["other_year_records_left_opaque"] += 1
            continue
        counts["selected_year_records_decoded"] += 1
        yield dict(
            zip(names, (field.decode("utf-8", errors="strict") for field in fields), strict=True)
        )
