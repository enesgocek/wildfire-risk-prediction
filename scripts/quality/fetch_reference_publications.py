"""Bounded anonymous GETs for four inspected public reference publications; no cloud APIs."""

import json
import urllib.parse
import urllib.request
import uuid
from datetime import UTC, datetime
from pathlib import Path

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
URLS = {
    "effis_technical_2014.pdf": "https://data.effis.emergency.copernicus.eu/effis/reports-and-publications/effis-related-publications/eudb_tech_spec_final_2register.pdf",
    "mugla_2023.pdf": "https://www.ogm.gov.tr/muglaobm/duyurular-sitesi/Documents/mugla-obm-2023-yili-yangin-degerlendirme-raporu/2023%2BYili%2BOrman%2BYanginlari%2BDegerlendirme%2BRaporu.pdf",
    "effis_database.html": "https://forest-fire.emergency.copernicus.eu/about-effis/technical-background/european-fire-database",
    "effis_access.html": "https://forest-fire.emergency.copernicus.eu/applications/data-and-services",
}
HOSTS = {
    "data.effis.emergency.copernicus.eu",
    "www.ogm.gov.tr",
    "forest-fire.emergency.copernicus.eu",
}


def public_url(url):
    p = urllib.parse.urlsplit(url)
    require(
        p.scheme == "https"
        and p.hostname in HOSTS
        and not p.username
        and not p.password
        and not p.query
        and not p.fragment
        and p.port in (None, 443),
        "Inspected public reference URL",
    )


class Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def run():
    out = (
        ROOT
        / "outputs/reports/dataset/reference_access_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    opener = urllib.request.build_opener(Redirect())
    receipts = []
    for name, url in URLS.items():
        record = {
            "name": name,
            "url": url,
            "retrieved_at_utc": datetime.now(UTC).isoformat(),
            "success": False,
        }
        try:
            public_url(url)
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; WildfireResearchReference/1.0)"},
            )
            with opener.open(req, timeout=30) as response:
                public_url(response.geturl())
                data = response.read(25_000_001)
                require(
                    len(data) <= 25_000_000 and response.status == 200,
                    "Bounded successful response",
                )
                require(not name.endswith(".pdf") or data.startswith(b"%PDF-"), "PDF signature")
                with (out / name).open("xb") as stream:
                    stream.write(data)
                record.update(
                    success=True,
                    http_status=response.status,
                    bytes=len(data),
                    sha256=digest(out / name),
                    final_url=response.geturl(),
                    content_type=response.headers.get_content_type(),
                )
        except Exception as error:
            record["error_type"] = type(error).__name__
            if hasattr(error, "code"):
                record["http_status"] = error.code
        receipts.append(record)
        print(name, record["success"], record.get("bytes", record.get("error_type")), flush=True)
    report = {
        "status": "public_reference_retrieval_only_not_label_acceptance",
        "sources": receipts,
        "script_sha256": digest(Path(__file__)),
        "cloud_jobs_started": 0,
        "credentials_used": False,
        "labels_created": False,
    }
    (out / "source_receipts.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(out.relative_to(ROOT).as_posix(), flush=True)


if __name__ == "__main__":
    run()
