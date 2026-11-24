"""Fetch at most the public vector headers, never event records or cube chunks."""

import hashlib
import json
import struct
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from wildfire_risk_prediction.mesogeos_reference import dbf_header, shp_header

ROOT = Path(__file__).resolve().parents[2]
LISTING = ROOT / "outputs/reports/dataset/mesogeos_vector_access_v1/20261124T223857Z_2b72c128"
MAX_HEADER = 65535


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    listing_receipt = json.loads((LISTING / "readback.json").read_bytes())
    if sha(LISTING / "items.json") != listing_receipt["artifact_sha256"]["items.json"]:
        raise ValueError("Exact public file-list snapshot")
    items = json.loads((LISTING / "items.json").read_bytes())
    by_suffix = {Path(row["name"]).suffix: row for row in items}
    if set(by_suffix) != {".dbf", ".shp", ".shx", ".prj", ".cpg"} or len(items) != 5:
        raise ValueError("Exactly the observed vector bundle")
    out = (
        ROOT
        / "outputs/reports/dataset/mesogeos_reference_header_probe_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    responses = []

    def first_bytes(item, count, target):
        if not 0 < count <= MAX_HEADER:
            raise ValueError("Metadata byte cap")
        url = "https://drive.google.com/uc?export=download&id=" + item["id"]
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "wildfire-public-reference-metadata/1",
                "Range": f"bytes=0-{count - 1}",
            },
        )
        with urllib.request.urlopen(request, timeout=25) as response:
            mime = response.headers.get_content_type()
            if mime in {"text/html", "application/json", "application/xml", "text/xml"}:
                raise ValueError("Public binary access not established; no confirmation bypass")
            if response.status == 206:
                expected = f"bytes 0-{count - 1}/"
                if not response.headers.get("Content-Range", "").startswith(expected):
                    raise ValueError("Exact initial byte range required")
            elif response.status != 200:
                raise ValueError("Unexpected public response")
            raw = response.read(count)
            # Even if Range is ignored, close after precisely the metadata prefix.
            if len(raw) != count:
                raise ValueError("Incomplete initial metadata bytes")
            (out / target).write_bytes(raw)
            responses.append(
                {
                    "file_name": item["name"],
                    "requested_bytes": count,
                    "status": response.status,
                    "stored_name": target,
                    "response_prefix_sha256": hashlib.sha256(raw).hexdigest(),
                }
            )
            return raw

    try:
        first = first_bytes(by_suffix[".dbf"], 32, "dbf_initial_32.bin")
        header_length = struct.unpack_from("<H", first, 8)[0]
        raw_dbf = first_bytes(by_suffix[".dbf"], header_length, "dbf_schema.bin")
        schema = dbf_header(raw_dbf)
        index = shp_header(first_bytes(by_suffix[".shx"], 100, "shx_header.bin"))
        prj_size = by_suffix[".prj"]["numeric_fields"]["13"]
        crs = first_bytes(by_suffix[".prj"], prj_size, "projection.prj").decode("utf-8")
        if (index["file_bytes_declared"] - 100) // 8 != schema["record_count_declared"]:
            raise ValueError("Declared geometry and DBF counts differ")
        result = {
            "status": "reference_metadata_only_complete_not_event_acceptance",
            "dbf": schema,
            "shx": index,
            "shape_metadata_source": "small_SHX_index_header_not_SHP_geometry_file",
            "shp_geometry_file_opened": False,
            "crs_wkt": crs,
        }
    except Exception as exc:
        result = {
            "status": "header_probe_incomplete_outputs_retained",
            "error_type": type(exc).__name__,
        }
    result.update(
        {
            "analysis_date": "2026-11-25",
            "listing_receipt_sha256": sha(LISTING / "readback.json"),
            "responses": responses,
            "bytes_read": sum(r["requested_bytes"] for r in responses),
            "event_records_opened": 0,
            "new_training": False,
            "new_labels": False,
            "final_merge": False,
            "producer_sha256": sha(Path(__file__)),
            "parser_sha256": sha(ROOT / "src/wildfire_risk_prediction/mesogeos_reference.py"),
            "artifact_sha256": {p.name: sha(p) for p in out.iterdir() if p.is_file()},
        }
    )
    (out / "readback.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(out.relative_to(ROOT).as_posix())
    print(result["status"])


if __name__ == "__main__":
    main()
