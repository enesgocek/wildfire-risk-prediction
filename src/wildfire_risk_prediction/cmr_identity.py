"""Exact public CMR identity checks; no download, byte integrity or label admission."""

import re
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode, urlsplit

from wildfire_risk_prediction.feature_join import require, training_day

PRODUCTS = {
    "VNP14IMG": ("SNPP", "fire", "002", "C2734202914-LPCLOUD", {"2", "002"}),
    "VNP03IMG": ("SNPP", "geolocation", "002", "C2105092163-LAADS", {"2", "002"}),
    "VJ114IMG": ("N20", "fire", "002", "C2734197957-LPCLOUD", {"2", "002"}),
    "VJ103IMG": ("N20", "geolocation", "021", "C2105086226-LAADS", {"2.1", "021"}),
}
ENDPOINT = "https://cmr.earthdata.nasa.gov/search/granules.umm_json"


def identity(reference):
    name = reference["filename"]
    match = re.fullmatch(
        r"(VNP14IMG|VNP03IMG|VJ114IMG|VJ103IMG)\.A(\d{7}\.\d{4})\.(\d{3})\.\d{13}\.nc",
        name,
    )
    require(match is not None, "Exact native filename required")
    product, pair, version = match.groups()
    sensor, role, expected_version, collection, _ = PRODUCTS[product]
    day = datetime.strptime(pair, "%Y%j.%H%M").strftime("%Y-%m-%d")
    training_day(day)
    require(
        version == expected_version
        and reference["source_day"] == day
        and reference["sample_id"] == f"{sensor}:{pair}"
        and reference["role"] == role
        and reference["source_id"] == f"{sensor}:{pair}|{role}",
        "Native reference identity agreement",
    )
    require(
        type(reference["bytes"]) is int
        and reference["bytes"] > 0
        and re.fullmatch(r"[a-f0-9]{64}", reference["sha256"]) is not None,
        "Historical native size and hash",
    )
    return product, collection, datetime.strptime(pair, "%Y%j.%H%M").replace(tzinfo=UTC)


def query_url(references):
    require(0 < len(references) <= 16, "Bounded exact batch")
    specs = [identity(r) for r in references]
    require(len({s[0] for s in specs}) == 1, "One collection per query")
    names = [r["filename"] for r in references]
    require(len(set(names)) == len(names), "Unique query filenames")
    params = [
        ("collection_concept_id", specs[0][1]),
        ("page_size", "64"),
        ("options[producer_granule_id][pattern]", "false"),
        ("options[producer_granule_id][ignore_case]", "false"),
    ]
    # Providers differ only in whether ProducerGranuleId includes the .nc extension.
    for name in names:
        params.extend(("producer_granule_id[]", n) for n in (name, name.removesuffix(".nc")))
    return ENDPOINT + "?" + urlencode(params)


def producer_name(item):
    names = {
        x["Identifier"].removesuffix(".nc") + ".nc"
        for x in item["umm"]["DataGranule"]["Identifiers"]
        if x["IdentifierType"] == "ProducerGranuleId"
    }
    require(len(names) == 1, "Unambiguous producer identity")
    return names.pop()


def complete_items(payload, headers, references):
    """Reject truncated, timed-out or unrelated responses before interpreting zero hits."""
    h = {k.lower(): v for k, v in headers.items()}
    require(h.get("cmr-timed-out", "false").lower() == "false", "CMR timeout")
    hits = h.get("cmr-hits", "")
    require(hits.isdigit(), "CMR hit count required")
    require(type(payload["hits"]) is int and payload["hits"] == int(hits), "CMR body/header hits")
    items = payload["items"]
    require(isinstance(items, list) and len(items) == int(hits), "Complete bounded CMR response")
    expected = {r["filename"] for r in references}
    concepts = []
    for item in items:
        require(producer_name(item) in expected, "Unrequested metadata identity")
        concept = item["meta"]["concept-id"]
        require(re.fullmatch(r"G\d+-[A-Z0-9]+", concept) is not None, "CMR granule concept")
        concepts.append(concept)
    require(len(concepts) == len(set(concepts)), "Duplicate CMR result concept")
    return items


def assess(reference, items):
    product, collection, start = identity(reference)
    found = [i for i in items if producer_name(i) == reference["filename"]]
    result = {
        "source_id": reference["source_id"],
        "filename": reference["filename"],
        "product": product,
        "expected_collection": collection,
        "historical_bytes": reference["bytes"],
        "historical_sha256": reference["sha256"],
        "catalogue_match_count": len(found),
        "catalogue_status": "not_found_in_exact_query" if not found else "ambiguous_exact_identity",
        "metadata_checks_passed": False,
        "issues": [],
        "data_endpoint_checked": False,
        "raw_bytes_verified": False,
        "native_input_lineage_rechecked": False,
        "negative_label_permitted": False,
    }
    if len(found) != 1:
        return result
    item = found[0]
    u, meta = item["umm"], item["meta"]
    result.update(
        concept_id=meta["concept-id"],
        revision_id=meta["revision-id"],
        revision_date=meta.get("revision-date"),
    )
    issues = result["issues"]
    if meta.get("collection-concept-id") != collection:
        issues.append("collection_concept_mismatch")
    c = u["CollectionReference"]
    if c["ShortName"] != product or c["Version"] not in PRODUCTS[product][4]:
        issues.append("collection_product_version_mismatch")
    interval = u["TemporalExtent"]["RangeDateTime"]
    actual = [
        datetime.fromisoformat(interval[k].replace("Z", "+00:00"))
        for k in ("BeginningDateTime", "EndingDateTime")
    ]
    if actual != [start, start + timedelta(minutes=6)] or any(t.tzinfo is None for t in actual):
        issues.append("acquisition_interval_mismatch")
    result["catalogue_start_utc"], result["catalogue_end_utc"] = [t.isoformat() for t in actual]
    links = []
    for link in u.get("RelatedUrls", []):
        url = urlsplit(link["URL"])
        if (
            link.get("Type") == "GET DATA"
            and url.scheme == "https"
            and url.hostname
            in {
                "data.lpdaac.earthdatacloud.nasa.gov",
                "data.laadsdaac.earthdatacloud.nasa.gov",
                "ladsweb.modaps.eosdis.nasa.gov",
            }
            and not url.username
            and not url.password
            and not url.query
            and not url.fragment
            and url.path.rsplit("/", 1)[-1] == reference["filename"]
        ):
            links.append(link["URL"])
    result["metadata_data_urls"] = sorted(set(links))
    if not links:
        issues.append("exact_nasa_data_url_absent")
    archive = u["DataGranule"]["ArchiveAndDistributionInformation"]
    result["provider_checksum_status"] = "not_provided"
    if len(archive) != 1:
        issues.append("ambiguous_archive_size")
    else:
        entry = archive[0]
        size = entry.get("SizeInBytes")
        if size is not None:
            valid = type(size) is int and size > 0
            result["size_basis"] = "SizeInBytes"
        elif entry.get("SizeUnit") == "MB":
            size = round(float(entry["Size"]) * 2**20)
            valid = size > 0
            result["size_basis"] = "rounded_binary_MB_metadata"
        else:
            valid = False
            result["size_basis"] = "unsupported"
        result["catalogue_bytes"] = size
        tolerance = 0 if result["size_basis"] == "SizeInBytes" else 1
        if not valid or abs(size - reference["bytes"]) > tolerance:
            issues.append("historical_size_mismatch_or_unknown")
        checksum = entry.get("Checksum")
        if checksum:
            algorithm = checksum["Algorithm"].upper().replace("-", "")
            result["provider_checksum_algorithm"] = algorithm
            result["provider_checksum_status"] = "not_comparable_to_historical_sha256"
            if algorithm == "SHA256":
                matches = checksum["Value"].lower() == reference["sha256"]
                result["provider_checksum_status"] = (
                    "matches_historical_sha256" if matches else "conflict"
                )
                if not matches:
                    issues.append("historical_sha256_conflict")
    result["catalogue_status"] = (
        "exact_identity_metadata_match" if not issues else "metadata_conflict"
    )
    result["metadata_checks_passed"] = not issues
    return result
