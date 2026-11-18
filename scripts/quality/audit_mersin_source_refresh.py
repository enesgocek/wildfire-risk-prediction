"""Verify captured public catalogue metadata against the retained Mersin archive."""

import hashlib
import json
from datetime import UTC, datetime
from uuid import uuid4

from audit_mersin_open_incidents import ARCHIVE, PINS, ROOT
from audit_stage_one_selection import verify

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require

BASE = ROOT / "outputs/reports/dataset"
PARENTS = {
    "mersin_source_refresh_v1/20261118T202928Z_e648f8e8": (
        "9b8408b7624539ad355801b691dd637950d9ffaec2bdb6cd6b2e41700d3592c5"
    ),
    "mersin_source_latest_v1/20261118T203009Z_00aecdab": (
        "4ad1e3f77ea0aaf5fa93a94e50e499b75ae7d987926244591473411b0040a523"
    ),
    "mersin_publication_access_v1/20261118T203039Z_74f30195": (
        "ee76d967823ac4124107c51622a3ac8c9e76625383783681c5e5895537178432"
    ),
}


def main():
    snapshots, inputs = {}, {}
    for folder, expected in PARENTS.items():
        path = BASE / folder / "readback.json"
        verify(path, expected)
        inputs[path.relative_to(ROOT).as_posix()] = expected
        for record in json.loads(path.read_bytes())["sources"]:
            snapshots[record["key"]] = record
            if "path" in record:
                verify(ROOT / record["path"], record["sha256"])
                inputs[record["path"]] = record["sha256"]

    def payload(key):
        require(snapshots[key]["http_status"] == 200, "Successful metadata snapshot")
        return json.loads((ROOT / snapshots[key]["path"]).read_bytes())

    zenodo, versions = payload("zenodo"), payload("versions")
    require(zenodo["id"] == 21455927, "Expected public record")
    require(
        versions["hits"]["total"] == 1
        and {v["id"] for v in versions["hits"]["hits"]} == {21455927},
        "One published version at check time",
    )
    require(len(zenodo["files"]) == 1, "One published archive file")
    verify(ARCHIVE, PINS[ARCHIVE])
    md5 = hashlib.md5(ARCHIVE.read_bytes()).hexdigest()
    require(zenodo["files"][0]["checksum"] == "md5:" + md5, "Published and local bytes match")
    crossref = payload("crossref")["message"]
    require(crossref["DOI"].lower() == "10.1177/00368504261495731", "DOI registry identity")
    index = payload("europepmc")
    require(index["hitCount"] == 1, "One DOI index record")
    indexed = index["resultList"]["result"][0]
    require(indexed["doi"].lower() == crossref["DOI"].lower(), "Two indexes agree on DOI")
    result = {
        "public_record": zenodo["id"],
        "version": zenodo["metadata"]["version"],
        "published_version_count": versions["hits"]["total"],
        "local_archive_matches_published_md5": True,
        "archive_sha256": PINS[ARCHIVE],
        "published_title": crossref["title"],
        "publication_index_id": indexed["id"],
        "pmcid": indexed.get("pmcid"),
        "publisher_html_http_status": snapshots["article"]["http_status"],
        "publisher_xml_http_status": snapshots["publisher_xml"]["http_status"],
        "source_snapshots": snapshots,
        "input_sha256": inputs,
        "new_archive_version_available_at_check": False,
        "publisher_methods_fulltext_reviewed": False,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "labels_created": False,
    }
    out = (
        BASE
        / "mersin_source_refresh_audit_v1"
        / (f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}_{uuid4().hex[:8]}")
    )
    out.mkdir(parents=True, exist_ok=False)
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_bytes()) == result, "Refresh audit readback")
    print(path.relative_to(ROOT), digest(path))


if __name__ == "__main__":
    main()
