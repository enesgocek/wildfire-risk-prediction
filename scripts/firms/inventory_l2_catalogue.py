"""Harvest training-only CMR metadata and diagnose nominal pairing, never labels.

No granule data downloads or authentication. Cache each Search-After page with
its query/header provenance. Pairing by sensor/time is only a candidate match;
the actual geolocation InputPointer must still be verified from product headers.
"""

import argparse
import gzip
import hashlib
import importlib.util
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd

SPEC = importlib.util.spec_from_file_location(
    "capacity", Path(__file__).with_name("snapshot_l2_capacity.py")
)
capacity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(capacity)
SPEC = importlib.util.spec_from_file_location(
    "audit", Path(__file__).with_name("inspect_l2_observation_sample.py")
)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)
ROOT, OUTPUT = capacity.ROOT, capacity.OUTPUT
CACHE = OUTPUT / "catalogue_pages_v1"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def query_url(product, bbox):
    split = urllib.parse.urlsplit(capacity.query_url(product, bbox))
    params = urllib.parse.parse_qs(split.query)
    params["page_size"] = ["1000"]
    params["sort_key[]"] = ["start_date", "producer_granule_id"]
    return urllib.parse.urlunsplit(split._replace(query=urllib.parse.urlencode(params, doseq=True)))


def normalize(entry, product):
    sensor, role, collection = capacity.PRODUCTS[product]
    audit.require(entry["collection_concept_id"] == collection, "Wrong collection")
    filename = entry["producer_granule_id"]
    if not filename.endswith(".nc"):
        filename += ".nc"
    file_sensor, file_role, key, stamp = audit.product_identity(filename)
    audit.require((file_sensor, file_role) == (sensor, role), "Wrong sensor/product role")
    audit.require(filename.split(".")[0] == product, "Wrong product filename")
    start, end = pd.Timestamp(entry["time_start"]), pd.Timestamp(entry["time_end"])
    audit.require(start.tz is not None and end.tz is not None, "Missing timezone")
    audit.require(start == pd.Timestamp(stamp) and end > start, "Filename/interval mismatch")
    requested_start = pd.Timestamp("2018-01-01T00:00Z" if sensor == "SNPP" else "2018-04-01T00:00Z")
    audit.require(
        requested_start <= start < pd.Timestamp("2024-01-01T00:00Z"), "Outside training request"
    )
    size_mb = Decimal(str(entry["granule_size"]))
    audit.require(size_mb.is_finite() and size_mb > 0, "Missing/invalid catalogue size")
    links = entry.get("links", [])
    data_links = [
        link["href"]
        for link in links
        if not link.get("inherited")
        and link.get("rel", "").endswith("/data#")
        and urllib.parse.urlsplit(link["href"]).path.endswith(".nc")
    ]
    audit.require(len(set(data_links)) == 1, "Expected one exact granule data URL")
    audit.require(
        urllib.parse.urlsplit(data_links[0]).path.rsplit("/", 1)[-1] == filename,
        "Filename/URL mismatch",
    )
    services = [
        link["href"]
        for link in links
        if not link.get("inherited") and "opendap" in link.get("href", "").lower()
    ]
    return {
        "sensor": sensor,
        "role": role,
        "product": product,
        "collection": collection,
        "concept_id": entry["id"],
        "filename": filename,
        "pair_key": key,
        "start_utc": start.isoformat(),
        "end_utc": end.isoformat(),
        "interval_seconds": (end - start).total_seconds(),
        "day_night": entry.get("day_night_flag", "unknown"),
        "catalogue_size_mb": str(size_mb),
        "catalogue_size_bytes_estimate": float(size_mb * 2**20),
        "data_url": data_links[0],
        "opendap_urls": "|".join(sorted(set(services))),
        "actual_input_identity_verified": False,
        "negative_label_permitted": False,
    }


def request_page(url, token):
    headers = {"User-Agent": "wildfire-risk-catalogue-audit/0.1", "Accept-Encoding": "gzip"}
    if token is not None:
        headers["CMR-Search-After"] = token
    for attempt in range(3):
        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, headers=headers), timeout=45
            ) as response:
                body = response.read()
                if response.headers.get("Content-Encoding") == "gzip":
                    body = gzip.decompress(body)
                audit.require(
                    response.headers.get("CMR-Timed-Out", "false").lower() != "true", "CMR timeout"
                )
                hits = response.headers.get("CMR-Hits", "")
                audit.require(hits.isdigit(), "Missing hit count")
                return {
                    "query_url": url,
                    "request_search_after": token,
                    "next_search_after": response.headers.get("CMR-Search-After"),
                    "hits": int(hits),
                    "request_id": response.headers.get("CMR-Request-Id"),
                    "checked_at_utc": datetime.now(UTC).isoformat(),
                    "body": json.loads(body),
                }
        except (TimeoutError, urllib.error.URLError) as exc:
            if isinstance(exc, urllib.error.HTTPError) and exc.code not in {
                429,
                500,
                502,
                503,
                504,
            }:
                raise
            if attempt == 2:
                raise
            time.sleep(1 + attempt)
    raise AssertionError("Unreachable")


def harvest(product, bbox, offline=False):
    url = query_url(product, bbox)
    directory = CACHE / product
    directory.mkdir(parents=True, exist_ok=True)
    token, expected, rows, pages, seen_tokens = None, None, [], [], set()
    while expected is None or len(rows) < expected:
        number = len(pages) + 1
        path = directory / f"page_{number:03d}.json.gz"
        if path.exists():
            page = json.loads(gzip.decompress(path.read_bytes()))
        else:
            audit.require(not offline, "Missing cached page in offline mode")
            page = request_page(url, token)
            data = gzip.compress(json.dumps(page).encode("utf-8"), mtime=0)
            temporary = path.with_suffix(".tmp")
            temporary.write_bytes(data)
            temporary.replace(path)
        audit.require(
            page["query_url"] == url and page["request_search_after"] == token,
            "Stale/misaligned cached page",
        )
        expected = page["hits"] if expected is None else expected
        audit.require(page["hits"] == expected, "Catalogue changed during paging; restart snapshot")
        entries = page["body"]["feed"]["entry"]
        audit.require(0 < len(entries) <= 1000 or expected == 0, "Empty/truncated page")
        rows.extend(normalize(entry, product) for entry in entries)
        audit.require(len(rows) <= expected, "Too many catalogue records")
        pages.append(
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": digest(path),
                "records": len(entries),
                "request_id": page["request_id"],
            }
        )
        token = page["next_search_after"]
        print(f"Catalogue {product}: {len(rows)}/{expected}", flush=True)
        if len(rows) < expected:
            audit.require(token and token not in seen_tokens, "Missing/repeated Search-After token")
            seen_tokens.add(token)
    frame = pd.DataFrame(rows)
    audit.require(len(frame) == expected, "Hit count mismatch")
    if rows:
        audit.require(
            frame.concept_id.is_unique and frame.filename.is_unique, "Duplicate catalogue records"
        )
        audit.require(frame.start_utc.is_monotonic_increasing, "Unordered catalogue records")
    return rows, {"query_url": url, "hits": expected, "pages": pages}


def pair_catalogue(frame):
    audit.require(not frame.duplicated(["product", "concept_id"]).any(), "Duplicate concept")
    rows = []
    for (sensor, key), group in frame.groupby(["sensor", "pair_key"], sort=True):
        fire, geo = (group.loc[group.role.eq(role)] for role in ("fire", "geolocation"))
        status = "nominal_unique_pair"
        if len(fire) > 1 or len(geo) > 1:
            status = "ambiguous_production"
        elif len(fire) == 0:
            status = "geolocation_only"
        elif len(geo) == 0:
            status = "fire_only"
        elif (
            fire.iloc[0].start_utc != geo.iloc[0].start_utc
            or fire.iloc[0].end_utc != geo.iloc[0].end_utc
        ):
            status = "interval_mismatch"
        rows.append(
            {
                "sensor": sensor,
                "pair_key": key,
                "day": group.iloc[0].start_utc[:10],
                "fire_count": len(fire),
                "geolocation_count": len(geo),
                "pair_status": status,
                "fire_concepts": "|".join(fire.concept_id),
                "geolocation_concepts": "|".join(geo.concept_id),
                "actual_input_identity_verified": False,
                "negative_label_permitted": False,
            }
        )
    return pd.DataFrame(rows)


def run(offline=False):
    inventory_path = OUTPUT / "l2_training_sample_inventory.json"
    bbox = json.loads(inventory_path.read_text())["bounding_box"]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda product: harvest(product, bbox, offline), capacity.PRODUCTS))
    audit.require(all(rows for rows, _ in results), "Expected all four training products")
    frame = pd.DataFrame([row for rows, _ in results for row in rows])
    pairs = pair_catalogue(frame)
    sizes = []
    for path in sorted(OUTPUT.glob("l2_sample_*_audit.json")):
        sample = json.loads(path.read_text())
        for source in sample["sources"].values():
            file = ROOT / source["path"]
            audit.require(digest(file) == source["sha256"], "Local sample changed")
            match = frame.loc[frame.filename.eq(file.name)]
            audit.require(len(match) == 1, "Local sample absent/ambiguous in catalogue")
            error = abs(match.iloc[0].catalogue_size_bytes_estimate - file.stat().st_size)
            audit.require(error <= 1, "Catalogue MB interpretation disagrees with local bytes")
            sizes.append({"filename": file.name, "difference_bytes": error})
    outputs = {}
    for name, table in [("granules", frame), ("pairs", pairs)]:
        path = OUTPUT / f"l2_training_catalogue_{name}.csv"
        table.to_csv(path, index=False)
        outputs[name] = {
            "path": str(path.relative_to(ROOT)),
            "sha256": digest(path),
            "records": len(table),
        }
    summary = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "status": "metadata_inventory_nominal_pairing_only",
        "script_sha256": digest(Path(__file__)),
        "inspector_sha256": digest(Path(audit.__file__)),
        "capacity_script_sha256": digest(Path(capacity.__file__)),
        "sample_inventory_sha256": digest(inventory_path),
        "catalogue": {p: result[1] for p, result in zip(capacity.PRODUCTS, results, strict=True)},
        "outputs": outputs,
        "pair_status_counts": pairs.groupby(["sensor", "pair_status"]).size().to_dict(),
        "local_size_unit_checks": sizes,
        "catalogue_size_tib": frame.catalogue_size_bytes_estimate.sum() / 2**40,
        "raw_granules_downloaded": 0,
        "negative_label_permitted": False,
        "limitations": [
            "Spatial envelopes are not pilot pixel coverage",
            "Nominal pair is not actual geolocation InputPointer validation",
            "Metadata sizes use binary MB, checked against local samples; "
            "transfer sizes can change",
            "Equal page hit counts cannot guarantee an immutable live catalogue snapshot",
            "Only requested training dates, no 2024/2025 rule selection or final labels",
        ],
    }
    summary["pair_status_counts"] = {
        f"{sensor}:{status}": int(count)
        for (sensor, status), count in summary["pair_status_counts"].items()
    }
    path = OUTPUT / "l2_training_catalogue_inventory.json"
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Report: {path}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    run(parser.parse_args().offline)
