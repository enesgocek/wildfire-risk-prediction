"""Metadata matching never certifies raw access, file integrity or observation labels."""

import copy
from urllib.parse import parse_qs, urlsplit

import pytest

from wildfire_risk_prediction.cmr_identity import assess, complete_items, identity, query_url


def reference():
    return {
        "source_id": "SNPP:2021046.0100|fire",
        "source_day": "2021-02-15",
        "sample_id": "SNPP:2021046.0100",
        "role": "fire",
        "filename": "VNP14IMG.A2021046.0100.002.2024000000000.nc",
        "bytes": 1000,
        "sha256": "a" * 64,
    }


def item():
    return {
        "meta": {
            "concept-id": "G12345-LPCLOUD",
            "collection-concept-id": "C2734202914-LPCLOUD",
            "revision-id": 1,
        },
        "umm": {
            "CollectionReference": {"ShortName": "VNP14IMG", "Version": "2"},
            "DataGranule": {
                "Identifiers": [
                    {"Identifier": reference()["filename"], "IdentifierType": "ProducerGranuleId"}
                ],
                "ArchiveAndDistributionInformation": [{"SizeInBytes": 1000}],
            },
            "TemporalExtent": {
                "RangeDateTime": {
                    "BeginningDateTime": "2021-02-15T01:00:00Z",
                    "EndingDateTime": "2021-02-15T01:06:00Z",
                }
            },
            "RelatedUrls": [
                {
                    "Type": "GET DATA",
                    "URL": "https://data.lpdaac.earthdatacloud.nasa.gov/path/"
                    + reference()["filename"],
                }
            ],
        },
    }


def test_query_is_collection_bound_exact_and_has_both_suffix_variants():
    q = parse_qs(urlsplit(query_url([reference()])).query)
    assert q["collection_concept_id"] == ["C2734202914-LPCLOUD"]
    assert q["producer_granule_id[]"] == [reference()["filename"], reference()["filename"][:-3]]
    assert q["options[producer_granule_id][pattern]"] == ["false"]
    assert q["options[producer_granule_id][ignore_case]"] == ["false"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("filename", "VNP14IMG.A2021046.0100.002.*.nc"),
        ("source_day", "2025-02-15"),
        ("sample_id", "N20:2021046.0100"),
        ("role", "geolocation"),
        ("bytes", 0),
        ("bytes", 1.5),
        ("sha256", "missing"),
    ],
)
def test_invalid_reference_never_becomes_a_query(field, value):
    r = reference()
    r[field] = value
    with pytest.raises(ValueError):
        query_url([r])


def test_matching_holdout_filename_and_day_are_also_rejected():
    r = reference()
    for k in ("filename", "sample_id", "source_id"):
        r[k] = r[k].replace("2021046", "2025046")
    r["source_day"] = "2025-02-15"
    with pytest.raises(ValueError):
        identity(r)


def test_duplicate_query_names_are_rejected():
    with pytest.raises(ValueError):
        query_url([reference(), reference()])


@pytest.mark.parametrize(
    "payload,headers",
    [
        ({"hits": 1, "items": []}, {"CMR-Hits": "1"}),
        ({"hits": 0, "items": []}, {}),
        ({"hits": 0, "items": []}, {"CMR-Hits": "0", "CMR-Timed-Out": "true"}),
        ({"hits": 0, "items": []}, {"CMR-Hits": "1"}),
    ],
)
def test_incomplete_responses_cannot_be_interpreted_as_absence(payload, headers):
    with pytest.raises(ValueError):
        complete_items(payload, headers, [reference()])


def test_zero_hits_is_query_specific_absence_with_closed_gates():
    items = complete_items({"hits": 0, "items": []}, {"CMR-Hits": "0"}, [reference()])
    r = assess(reference(), items)
    assert r["catalogue_status"] == "not_found_in_exact_query"
    assert not r["metadata_checks_passed"] and not r["negative_label_permitted"]


def test_unrequested_or_duplicate_metadata_is_rejected():
    a = item()
    a["umm"]["DataGranule"]["Identifiers"][0]["Identifier"] = "different.nc"
    with pytest.raises(ValueError):
        complete_items({"hits": 1, "items": [a]}, {"CMR-Hits": "1"}, [reference()])
    with pytest.raises(ValueError):
        complete_items({"hits": 2, "items": [item(), item()]}, {"CMR-Hits": "2"}, [reference()])


def test_ambiguous_concepts_do_not_choose_the_first_version():
    a = item()
    b = copy.deepcopy(a)
    b["meta"]["concept-id"] = "G999-LPCLOUD"
    r = assess(reference(), [a, b])
    assert r["catalogue_status"] == "ambiguous_exact_identity" and not r["metadata_checks_passed"]


def test_metadata_match_keeps_byte_access_lineage_and_label_checks_closed():
    a = item()
    a["umm"]["DataGranule"]["Identifiers"][0]["Identifier"] = reference()["filename"][:-3]
    r = assess(reference(), [a])
    assert r["catalogue_status"] == "exact_identity_metadata_match"
    assert r["provider_checksum_status"] == "not_provided"
    for k in (
        "data_endpoint_checked",
        "raw_bytes_verified",
        "native_input_lineage_rechecked",
        "negative_label_permitted",
    ):
        assert r[k] is False


@pytest.mark.parametrize(
    "change,expected",
    [
        ("collection", "collection_concept_mismatch"),
        ("version", "collection_product_version_mismatch"),
        ("time", "acquisition_interval_mismatch"),
        ("size", "historical_size_mismatch_or_unknown"),
        ("archive", "ambiguous_archive_size"),
        ("checksum", "historical_sha256_conflict"),
        ("url", "exact_nasa_data_url_absent"),
        ("url_query", "exact_nasa_data_url_absent"),
    ],
)
def test_metadata_conflicts_are_recorded_not_admitted(change, expected):
    a = item()
    u = a["umm"]
    archive = u["DataGranule"]["ArchiveAndDistributionInformation"]
    if change == "collection":
        a["meta"]["collection-concept-id"] = "C999-LPCLOUD"
    if change == "version":
        u["CollectionReference"]["Version"] = "1"
    if change == "time":
        u["TemporalExtent"]["RangeDateTime"]["EndingDateTime"] = "2021-02-15T01:12:00Z"
    if change == "size":
        archive[0]["SizeInBytes"] = 999
    if change == "archive":
        archive.append({"SizeInBytes": 1000})
    if change == "checksum":
        archive[0]["Checksum"] = {"Algorithm": "SHA-256", "Value": "b" * 64}
    if change == "url":
        u["RelatedUrls"][0]["URL"] = "https://example.com/" + reference()["filename"]
    if change == "url_query":
        u["RelatedUrls"][0]["URL"] += "?token=value"
    r = assess(reference(), [a])
    assert r["catalogue_status"] == "metadata_conflict" and expected in r["issues"]


@pytest.mark.parametrize(
    "algorithm,value,status",
    [
        ("MD5", "b" * 32, "not_comparable_to_historical_sha256"),
        ("SHA-256", "A" * 64, "matches_historical_sha256"),
    ],
)
def test_checksum_comparison_never_confuses_md5_with_sha256(algorithm, value, status):
    a = item()
    a["umm"]["DataGranule"]["ArchiveAndDistributionInformation"][0]["Checksum"] = {
        "Algorithm": algorithm,
        "Value": value,
    }
    r = assess(reference(), [a])
    assert r["metadata_checks_passed"] and r["provider_checksum_status"] == status
    assert not r["raw_bytes_verified"]


def test_laads_cloud_host_is_recognized_without_following_it():
    a = item()
    a["umm"]["RelatedUrls"][0]["URL"] = (
        "https://data.laadsdaac.earthdatacloud.nasa.gov/path/" + reference()["filename"]
    )
    assert assess(reference(), [a])["metadata_checks_passed"]


def test_rounded_mb_metadata_is_explicit_not_an_exact_raw_size_claim():
    a = item()
    a["umm"]["DataGranule"]["ArchiveAndDistributionInformation"] = [
        {"Size": 1000 / 2**20, "SizeUnit": "MB"}
    ]
    r = assess(reference(), [a])
    assert r["metadata_checks_passed"] and r["size_basis"] == "rounded_binary_MB_metadata"
