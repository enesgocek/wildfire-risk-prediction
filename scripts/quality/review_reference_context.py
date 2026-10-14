"""Retrieve bounded official pages and record candidate context without issuing labels."""

import argparse
import hashlib
import json
import urllib.parse
import urllib.request
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.reference_context import link_context, verify_page

ROOT = Path(__file__).resolve().parents[2]
CATALOG = "docs/research/label_reference_sources_2026-10-14.json"
PACKET = "outputs/reports/dataset/label_review_v1/20261014T153649Z_ca3fb92e"
PACKET_SHA = "36ce8565a452efbf2a4f1e69fe3254ae33ccdd818eb08584f57b41a9eaf28037"
HOSTS = {"www.antalya.gov.tr", "www.ogm.gov.tr"}
USER_AGENT = "Mozilla/5.0 (compatible; WildfireResearchReference/1.0)"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def public_url(url):
    parsed = urllib.parse.urlsplit(url)
    require(
        parsed.scheme == "https"
        and parsed.hostname in HOSTS
        and parsed.username is None
        and parsed.password is None
        and parsed.port in (None, 443)
        and not parsed.query
        and not parsed.fragment,
        "Only inspected public institutional URLs",
    )


class PublicRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def run(fetch_public_pages=False):
    require(fetch_public_pages is True, "Explicit public page retrieval flag required")
    pins = {}

    def retained(name, digest=None):
        data = (ROOT / name).read_bytes()
        require(digest is None or sha(data) == digest, "Retained context input changed")
        pins[name] = sha(data)
        return data

    catalog = json.loads(retained(CATALOG))
    packet = json.loads(retained(PACKET + "/readback.json", PACKET_SHA))
    require(
        packet["labels_created"] is False
        and packet["model_ready"] is False
        and packet["independent_expert_review_completed"] is False,
        "Unreviewed packet",
    )
    retained(
        PACKET + "/purposive_event_cases.csv",
        packet["artifact_sha256"]["purposive_event_cases.csv"],
    )
    cases = pd.read_csv(ROOT / PACKET / "purposive_event_cases.csv")
    linked = link_context(cases, catalog)
    for name in (
        "src/wildfire_risk_prediction/reference_context.py",
        "scripts/quality/review_reference_context.py",
    ):
        retained(name)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    out = ROOT / "outputs/reports/dataset/reference_context_v1" / stamp
    out.mkdir(parents=True, exist_ok=False)
    receipts = []
    # No cookies, credentials, cloud APIs, POST requests or unbounded downloads.
    opener = urllib.request.build_opener(PublicRedirect())
    for source in catalog["sources"]:
        public_url(source["url"])
        request = urllib.request.Request(source["url"], headers={"User-Agent": USER_AGENT})
        with opener.open(request, timeout=25) as response:
            public_url(response.geturl())
            require(
                response.status == 200 and response.headers.get_content_type() == "text/html",
                "Successful public HTML response",
            )
            data = response.read(3_000_001)
            verify_page(data, source)
            receipt = {
                "source_id": source["source_id"],
                "requested_url": source["url"],
                "retrieved_url": response.geturl(),
                "bytes": len(data),
                "sha256": sha(data),
                "http_status": response.status,
                "retrieved_at_utc": datetime.now(UTC).isoformat(),
                "visible_terms_checked": True,
                "claims_geocoded": False,
                "request_user_agent": USER_AGENT,
            }
        path = out / (source["source_id"] + ".html")
        with path.open("xb") as stream:
            stream.write(data)
        require(sha(path.read_bytes()) == receipt["sha256"], "Retained source page readback")
        receipts.append(receipt)
    linked.to_csv(out / "candidate_context_links.csv", index=False, mode="x")
    reread = pd.read_csv(out / "candidate_context_links.csv")
    require(
        reread.target.isna().all()
        and reread.ignition_timestamp_utc.isna().all()
        and reread.exact_event_identity_proven.eq(False).all()
        and reread.first_cell_identity_proven.eq(False).all()
        and reread.cluster_id.tolist() == linked.cluster_id.tolist(),
        "Context stays unlabelled",
    )
    require(all(sha((ROOT / n).read_bytes()) == h for n, h in pins.items()), "Inputs unchanged")
    result = {
        "status": "institutional_context_readback_passed",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "input_sha256": pins,
        "source_receipts": receipts,
        "candidate_case_links": len(linked),
        "candidate_membership_patterns": int(linked.membership_sha256.nunique()),
        "total_purposive_cases": len(cases),
        "labels_created": False,
        "exact_identities_confirmed": 0,
        "independent_expert_review_completed": False,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "positive_label_permitted": False,
        "model_ready": False,
        "validation_accessed": False,
        "final_test_accessed": False,
        "source_pages_retrieved": len(receipts),
        "links_sha256": sha((out / "candidate_context_links.csv").read_bytes()),
        "limits": [
            "Candidate regional context only; not a geocoded event match",
            "Official narrative sensor lineage not independently audited",
            "Reported clock has no explicit timezone; no ignition lag computed",
            "No no-fire reference or negative observation supplied",
            "No graph scenario chosen and no four-way split inferred",
        ],
    }
    (out / "readback.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Reference context result:", out.relative_to(ROOT).as_posix())
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch-public-pages", action="store_true")
    run(parser.parse_args().fetch_public_pages)
