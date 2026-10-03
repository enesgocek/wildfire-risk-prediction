"""Count training-period catalogue hits, without downloading granule data.

Catalogue envelopes can intersect the AOI bbox without covering any pilot pixel.
Counts do not verify fire/geolocation pairing or observation completeness.
Volume scenarios use the nine existing samples, not per-granule catalogue sizes.
"""

import json
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "outputs/reports/observation_coverage"
PRODUCTS = {
    "VNP14IMG": ("SNPP", "fire", "C2734202914-LPCLOUD"),
    "VNP03IMG": ("SNPP", "geolocation", "C2105092163-LAADS"),
    "VJ114IMG": ("N20", "fire", "C2734197957-LPCLOUD"),
    "VJ103IMG": ("N20", "geolocation", "C2105086226-LAADS"),
}


def query_url(product, bbox):
    # Fixed training-only overlap interval; no validation/test catalogue queries.
    sensor, _, concept = PRODUCTS[product]
    start = "2018-01-01" if sensor == "SNPP" else "2018-04-01"
    params = {
        "collection_concept_id": concept,
        "temporal": f"{start}T00:00:00.000001Z,2023-12-31T23:59:59.999999Z",
        "bounding_box": bbox,
        "page_size": 1,
        "sort_key[]": "start_date",
    }
    return "https://cmr.earthdata.nasa.gov/search/granules.json?" + urllib.parse.urlencode(params)


def query(product, bbox):
    url = query_url(product, bbox)
    req = urllib.request.Request(url, headers={"User-Agent": "wildfire-risk-capacity-audit/0.1"})
    with urllib.request.urlopen(req, timeout=45) as response:
        body = response.read()
        if response.headers.get("CMR-Timed-Out", "false").lower() == "true":
            raise ValueError("CMR query timed out; counts cannot be used")
        raw_hits = response.headers.get("CMR-Hits")
        if raw_hits is None or not raw_hits.isdigit():
            raise ValueError("Missing/invalid CMR-Hits")
        hits = int(raw_hits)
        request_id = response.headers.get("CMR-Request-Id")
    entry = json.loads(body)["feed"]["entry"]
    if len(entry) != min(hits, 1):
        raise ValueError("Header/sample entry mismatch")
    snapshot = OUTPUT / f"capacity_{product}_cmr_response.json"
    snapshot.write_bytes(body)
    sensor, role, collection = PRODUCTS[product]
    return {
        "product": product,
        "sensor": sensor,
        "role": role,
        "collection": collection,
        "query_url": url,
        "cmr_hits": hits,
        "cmr_request_id": request_id,
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "response_path": str(snapshot.relative_to(ROOT)),
        "first_result": entry[0].get("title") if entry else None,
    }


def main():
    import hashlib

    def digest(path):
        with path.open("rb") as stream:
            return hashlib.file_digest(stream, "sha256").hexdigest()

    inventory_path = OUTPUT / "l2_training_sample_inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    for product, (sensor, role, collection) in PRODUCTS.items():
        if inventory["collections"][sensor][role] != collection:
            raise ValueError(f"Unexpected collection: {product}")
    bbox = inventory["bounding_box"]
    samples, audits = {}, {}
    for path in sorted(OUTPUT.glob("l2_sample_*_audit.json")):
        report = json.loads(path.read_text(encoding="utf-8"))
        if not 2018 <= int(report["pair_key"][:4]) <= 2023:
            raise ValueError("Non-training sample in capacity estimate")
        audits[str(path.relative_to(ROOT))] = digest(path)
        for source in report["sources"].values():
            file = ROOT / source["path"]
            if digest(file) != source["sha256"]:
                raise ValueError("Sample source changed")
            product = file.name.split(".")[0]
            samples.setdefault(product, []).append(file.stat().st_size)
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(lambda product: query(product, bbox), PRODUCTS))
    for record in records:
        record["response_sha256"] = digest(ROOT / record["response_path"])
        sizes = samples[record["product"]]
        record["local_sample_count"] = len(sizes)
        record["observed_sample_size_bytes"] = {
            "min": min(sizes),
            "mean": sum(sizes) / len(sizes),
            "max": max(sizes),
        }
        record["size_scenario_bytes"] = {
            key: record["cmr_hits"] * size
            for key, size in record["observed_sample_size_bytes"].items()
        }
    result = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "status": "catalogue_hit_count_only_not_paired_acquisition_inventory",
        "training_start_utc": "2018-01-01T00:00:00Z",
        "training_end_exclusive_utc": "2024-01-01T00:00:00Z",
        "sensor_query_start_dates": {"SNPP": "2018-01-01", "N20": "2018-04-01"},
        "bounding_box": bbox,
        "inventory_sha256": digest(inventory_path),
        "sample_audits": audits,
        "script_sha256": digest(Path(__file__)),
        "records": records,
        "total_catalogue_hits": sum(r["cmr_hits"] for r in records),
        "total_size_scenario_tib": {
            key: sum(r["size_scenario_bytes"][key] for r in records) / 2**40
            for key in ("min", "mean", "max")
        },
        "raw_granules_downloaded": 0,
        "negative_label_permitted": False,
        "limitations": [
            "Spatial envelope hits are not pilot pixel observations",
            "Fire and geolocation hit counts can differ; actual input identity pairing not checked",
            "Size min/max are scenarios, not guaranteed bounds; only nine local samples",
            "Start/end overlap query, not exact-start-time inventory",
            "Training dates only; NOAA-20 starts on the existing FIRMS request date, 2018-04-01",
            "No authentication, data URLs fetched, final observation policy or labels",
        ],
    }
    output = OUTPUT / "l2_training_capacity_snapshot.json"
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "hits": result["total_catalogue_hits"],
                "scenario_tib": result["total_size_scenario_tib"],
            }
        ),
        flush=True,
    )
    print(f"Report: {output}", flush=True)


if __name__ == "__main__":
    main()
