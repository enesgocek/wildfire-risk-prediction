"""Cross-check a received read-only Drive probe against the accepted local capture."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from verify_gcp_source_aware_failure import archive_contents, require


def verify(probe, archive):
    require(probe.is_file() and 0 < probe.stat().st_size < 65536, "Probe byte bound")
    raw = probe.read_bytes()
    value = json.loads(raw)
    require(
        value["protocol"] == "gcp_continuation_readonly_probe_v1"
        and value["status"] == "readonly_checks_passed"
        and value["production_writes"] == value["drive_object_writes"] == 0
        and value["raw_processing"] is False
        and value["historical_exception_identified"] is False,
        "Probe policy/result",
    )
    captured, data = archive_contents(archive)
    quota = value["quota"]
    require(
        type(quota["usage"]) is int
        and quota["usage"] >= 0
        and (
            quota["limit"] is None
            or type(quota["limit"]) is int
            and quota["limit"] >= quota["usage"]
        ),
        "Quota values",
    )
    for field in ["object_count", "saved_bytes"]:
        require(type(value[field]) is int and value[field] > 0, "Listing values")
    manifest = value["manifest_readback"]
    require(
        manifest["sample_id"] == "manifest:" + captured["failed_month"]
        and manifest["local_sha256"] == hashlib.sha256(data["manifest.zip"]).hexdigest()
        and manifest["local_bytes"] == len(data["manifest.zip"])
        and manifest["state"] == "completed_matches_local",
        "Manifest readback identity",
    )
    expected = {
        t["sample_id"]: data[
            "tasks/" + hashlib.sha256(t["sample_id"].encode()).hexdigest() + "/pair.zip"
        ]
        for t in captured["task_inventory"]
        if t["pair_zip_present"]
    }
    rows = value["pairs"]
    require(
        len(rows) == len(expected) == 19 and len({r["sample_id"] for r in rows}) == 19,
        "Probe pair population",
    )
    for row in rows:
        require(row["sample_id"] in expected, "Foreign probe pair")
        payload = expected[row["sample_id"]]
        require(
            row["local_sha256"] == hashlib.sha256(payload).hexdigest()
            and row["local_bytes"] == len(payload)
            and row["state"]
            in {"not_published", "payload_without_completion", "completed_matches_local"},
            "Probe pair bytes/status",
        )
    return {
        "status": "probe_capture_crosscheck_passed",
        "probe_sha256": hashlib.sha256(raw).hexdigest(),
        "probe_bytes": len(raw),
        "pair_states": dict(Counter(r["state"] for r in rows)),
        "quota": quota,
        "production_writes": 0,
        "historical_exception_identified": False,
        "limitations": "Cross-check of remote probe report, not a new live Drive query",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("probe", type=Path)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.probe, args.archive)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
