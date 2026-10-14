"""Narrative sources are retrievable evidence, never automatic event or label admission."""

import copy
import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

from wildfire_risk_prediction.reference_context import link_context, verify_page


def fixture():
    cases = pd.DataFrame(
        [
            {
                "cluster_id": "C1",
                "scenario": "exploratory",
                "membership_sha256": "a" * 64,
                "event_status": "exploratory_cluster_only",
                "first_detection_utc": "2021-07-28T10:12:00Z",
                "last_detection_utc": "2021-08-04T00:00:00Z",
                "detection_count": 250,
                "earliest_grid_ids_json": '["G1","G2"]',
            }
        ]
    )
    source = {
        "source_id": "S1",
        "url": "https://www.antalya.gov.tr/example",
        "required_visible_terms": ["Manavgat", "28.07.2021"],
        "candidate_case_selection": {"first_detection_utc_date": "2021-07-28", "case_ids": ["C1"]},
    }
    catalog = {
        "scope": "training_case_context_only",
        "labels_permitted": False,
        "sources": [source],
    }
    return cases, catalog


def test_regional_account_keeps_ties_and_does_not_attest_identity_ignition_or_target():
    cases, catalog = fixture()
    before = cases.copy(deep=True)
    linked = link_context(cases, catalog)
    assert linked.first_grid_count.tolist() == [2]
    assert linked.exact_event_identity_proven.eq(False).all()
    assert linked.first_cell_identity_proven.eq(False).all()
    assert linked.target.isna().all() and linked.ignition_timestamp_utc.isna().all()
    pd.testing.assert_frame_equal(cases, before)


@pytest.mark.parametrize("change", ["gate", "missing_case", "wrong_date", "holdout"])
def test_wrong_scope_or_case_correspondence_rejected(change):
    cases, catalog = fixture()
    if change == "gate":
        catalog["labels_permitted"] = True
    elif change == "missing_case":
        catalog["sources"][0]["candidate_case_selection"]["case_ids"] = ["absent"]
    elif change == "wrong_date":
        cases["first_detection_utc"] = "2021-07-29T10:12:00Z"
    else:
        cases["first_detection_utc"] = "2025-07-28T10:12:00Z"
    with pytest.raises(ValueError):
        link_context(cases, catalog)


def test_visible_page_terms_ignores_script_and_supports_html_entities():
    _, catalog = fixture()
    source = catalog["sources"][0]
    assert "Manavgat" in verify_page(b"<p>Manavgat</p><p>28.07.2021</p>", source)
    with pytest.raises(ValueError):
        verify_page(b"<script>Manavgat 28.07.2021</script><p>Unrelated</p>", source)
    changed = copy.deepcopy(source)
    changed["required_visible_terms"] = ["Muğla & Antalya"]
    assert "Muğla & Antalya" in verify_page("<p>Muğla &amp; Antalya</p>".encode(), changed)


def test_changed_or_oversized_reference_page_is_not_accepted():
    _, catalog = fixture()
    source = catalog["sources"][0]
    for data in (b"", b"unrelated", b"x" * 3_000_001):
        with pytest.raises(ValueError):
            verify_page(data, source)


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/quality/review_reference_context.py"
spec = importlib.util.spec_from_file_location("reference_context_driver_test", SCRIPT)
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


@pytest.mark.parametrize(
    "url",
    [
        "http://www.antalya.gov.tr/path",
        "https://www.antalya.gov.tr.attacker.invalid/path",
        "https://name:secret@www.ogm.gov.tr/path",
        "https://www.ogm.gov.tr:444/path",
        "https://www.ogm.gov.tr/path?token=example",
        "https://127.0.0.1/path",
    ],
)
def test_non_public_or_uninspected_reference_url_rejected(url):
    with pytest.raises(ValueError):
        driver.public_url(url)


def test_inspected_public_urls_allowed_and_fetch_flag_required(monkeypatch):
    driver.public_url("https://www.antalya.gov.tr/manavgatta-4-ayri-noktada-orman-yangini-cikti")
    monkeypatch.setattr(Path, "read_bytes", lambda *a: pytest.fail("No source access"))
    with pytest.raises(ValueError, match="Explicit public"):
        driver.run(False)


def test_complete_driver_retains_source_bytes_and_never_creates_labels(tmp_path, monkeypatch):
    cases, catalog = fixture()
    monkeypatch.setattr(driver, "ROOT", tmp_path)
    monkeypatch.setattr(driver, "PACKET", "packet")
    monkeypatch.setattr(driver, "CATALOG", "catalog.json")
    (tmp_path / "catalog.json").write_text(json.dumps(catalog))
    (tmp_path / "packet").mkdir()
    case_path = tmp_path / "packet/purposive_event_cases.csv"
    cases.to_csv(case_path, index=False)
    packet = {
        "labels_created": False,
        "model_ready": False,
        "independent_expert_review_completed": False,
        "artifact_sha256": {"purposive_event_cases.csv": driver.sha(case_path.read_bytes())},
    }
    report = json.dumps(packet).encode()
    (tmp_path / "packet/readback.json").write_bytes(report)
    monkeypatch.setattr(driver, "PACKET_SHA", driver.sha(report))
    for name in (
        "src/wildfire_risk_prediction/reference_context.py",
        "scripts/quality/review_reference_context.py",
    ):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("retained code fixture\n")
    data = b"<html><p>Manavgat 28.07.2021</p></html>"

    class Headers:
        def get_content_type(self):
            return "text/html"

    class Response:
        status = 200
        headers = Headers()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def geturl(self):
            return catalog["sources"][0]["url"]

        def read(self, count):
            assert count == 3_000_001
            return data

    class Opener:
        def open(self, request, timeout):
            assert request.get_header("User-agent") == driver.USER_AGENT and timeout == 25
            return Response()

    monkeypatch.setattr(driver.urllib.request, "build_opener", lambda *a: Opener())
    out = driver.run(True)
    result = json.loads((out / "readback.json").read_text())
    assert result["labels_created"] is False and result["exact_identities_confirmed"] == 0
    assert result["source_receipts"][0]["sha256"] == driver.sha(data)
    assert (out / "S1.html").read_bytes() == data
    actual = pd.read_csv(out / "candidate_context_links.csv")
    assert actual.target.isna().all() and actual.ignition_timestamp_utc.isna().all()
