"""Check the fixed 584-file training pilot in public CMR; never fetch data URLs."""

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from wildfire_risk_prediction.cmr_identity import assess, complete_items, identity, query_url
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
PARENT = ROOT / "outputs/reports/dataset/observation_expansion_v1/20261014T233502Z_81275155"
PARENT_SHA = "8a29ea70339965497e4e5499ef718c684ecdbc9c833e3e2fa0c0db824a14e7c2"
OUTPUT = ROOT / "outputs/reports/dataset/observation_core_catalogue_v1"
PROTECTED = ROOT / (
    "outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/"
    "protected_inputs_readback_20261013.json"
)
MAX_RESPONSE_BYTES = 4_000_000


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    require(not path.exists(), "Never overwrite catalogue evidence")
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Public catalogue redirect refused")


def fetch_batch(out, number, references):
    url = query_url(references)
    body_path = out / "responses" / f"{number:03d}.json"
    receipt_path = out / "responses" / f"{number:03d}_receipt.json"
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        require(
            receipt["query_url"] == url and sha(body_path) == receipt["sha256"], "Cached CMR bytes"
        )
        payload = json.loads(body_path.read_bytes())
        items = complete_items(payload, receipt["headers"], references)
        return number, items, receipt, 0
    require(not body_path.exists(), "Incomplete response without receipt requires a new output")
    opener = urllib.request.build_opener(NoRedirect())
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "wildfire-observation-identity/1.0", "Accept": "application/json"},
    )
    for attempt in range(3):
        try:
            with opener.open(request, timeout=40) as response:
                require(
                    response.status == 200 and response.geturl() == url, "Exact public CMR endpoint"
                )
                body = response.read(MAX_RESPONSE_BYTES + 1)
                require(len(body) <= MAX_RESPONSE_BYTES, "Bounded metadata response")
                headers = {
                    k: response.headers.get(k, "")
                    for k in ("CMR-Hits", "CMR-Timed-Out", "CMR-Request-Id", "Content-Type")
                }
                # Missing timed-out header means false, matching CMR's documented response.
                headers["CMR-Timed-Out"] = headers["CMR-Timed-Out"] or "false"
            payload = json.loads(body)
            items = complete_items(payload, headers, references)
            body_path.write_bytes(body)
            receipt = {
                "query_url": url,
                "checked_at_utc": datetime.now(UTC).isoformat(),
                "headers": headers,
                "sha256": sha(body_path),
                "response_bytes": len(body),
                "attempts": attempt + 1,
                "anonymous_request": True,
                "raw_data_endpoint_requested": False,
            }
            write_json(receipt_path, receipt)
            return number, items, receipt, attempt + 1
        except urllib.error.HTTPError as error:
            if error.code not in {429, 500, 502, 503, 504} or attempt == 2:
                raise RuntimeError(f"Public CMR HTTP {error.code}") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            if attempt == 2:
                raise RuntimeError("Public CMR transport unavailable") from None
        time.sleep(2**attempt)
    raise RuntimeError("Public CMR attempts exhausted")


def run(resume=None, max_batches=None):
    require(sha(PARENT / "readback.json") == PARENT_SHA, "Accepted parent report")
    parent = json.loads((PARENT / "readback.json").read_text(encoding="utf-8"))
    require(
        parent["daily_observation_status"] == "unknown"
        and parent["negative_label_permitted"] is False,
        "Closed parent gates",
    )
    pins = {str((PARENT / "readback.json").relative_to(ROOT).as_posix()): PARENT_SHA}
    for name in ("native_source_queue.csv", "plan_source_links.csv", "calendar_core.csv"):
        path = PARENT / name
        require(sha(path) == parent["artifact_sha256"][name], "Frozen source plan")
        pins[path.relative_to(ROOT).as_posix()] = sha(path)
    queue = pd.read_csv(PARENT / "native_source_queue.csv")
    links = pd.read_csv(PARENT / "plan_source_links.csv")
    wanted = set(links.loc[links.selection_plan.eq("calendar_core"), "source_id"])
    core = queue.loc[queue.source_id.isin(wanted)].sort_values("source_id")
    require(
        len(core) == 584
        and core.source_id.is_unique
        and set(core.source_id) == wanted
        and core.current_remote_availability.eq("not_checked").all(),
        "Exact 584-reference scope",
    )
    references = core.to_dict("records")
    for reference in references:
        identity(reference)
    protected = json.loads(PROTECTED.read_text(encoding="utf-8"))
    pins[PROTECTED.relative_to(ROOT).as_posix()] = sha(PROTECTED)
    for name, digest in protected.items():
        require(sha(ROOT / name) == digest, "Frozen production input")
        pins[name] = digest
    for path in (Path(__file__), ROOT / "src/wildfire_risk_prediction/cmr_identity.py"):
        pins[path.relative_to(ROOT).as_posix()] = sha(path)
    batches = []
    for product in sorted({identity(r)[0] for r in references}):
        group = [r for r in references if identity(r)[0] == product]
        batches.extend(group[i : i + 16] for i in range(0, len(group), 16))
    manifest = {
        "scope": "calendar_core_exact_public_catalogue_only",
        "input_sha256": pins,
        "expected_files": len(core),
        "batch_count": len(batches),
        "batch_size_max": 16,
        "workers": 2,
        "raw_downloads_authorized": False,
    }
    if resume:
        out = Path(resume).resolve()
        require(
            out.is_relative_to(OUTPUT) and not out.is_symlink(), "Project-local catalogue resume"
        )
        require(
            json.loads((out / "request_manifest.json").read_text(encoding="utf-8")) == manifest,
            "Exact code/scope resume manifest",
        )
    else:
        out = OUTPUT / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8])
        out.mkdir(parents=True, exist_ok=False)
        (out / "responses").mkdir()
        write_json(out / "request_manifest.json", manifest)
    require(not (out / "readback.json").exists(), "Completed catalogue evidence is immutable")
    print("Catalogue output:", out.relative_to(ROOT).as_posix(), flush=True)
    count = len(batches) if max_batches is None else min(max_batches, len(batches))
    require(count > 0, "Positive bounded query count")
    results = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(fetch_batch, out, i, batch) for i, batch in enumerate(batches[:count])
        ]
        for future in futures:
            value = future.result()
            results.append(value)
            print("Catalogue metadata batch:", value[0] + 1, "/", len(batches), flush=True)
    if count < len(batches):
        print("Partial metadata checkpoint; resume explicitly with the same code/scope", flush=True)
        return
    rows, artifacts = [], {}
    for number, items, receipt, _ in results:
        for reference in batches[number]:
            record = assess(reference, items)
            record["query_batch"] = number
            record["checked_at_utc"] = receipt["checked_at_utc"]
            rows.append(record)
        for name in (f"{number:03d}.json", f"{number:03d}_receipt.json"):
            artifacts["responses/" + name] = sha(out / "responses" / name)
    write_json(out / "source_metadata_checks.json", rows)
    flat = pd.DataFrame(
        [
            {
                **r,
                "issues": "|".join(r["issues"]),
                "metadata_data_urls": "|".join(r.get("metadata_data_urls", [])),
            }
            for r in rows
        ]
    )
    flat.to_csv(out / "source_metadata_checks.csv", index=False)
    actual = pd.read_csv(out / "source_metadata_checks.csv", keep_default_na=False)
    require(actual.source_id.tolist() == flat.source_id.tolist(), "CSV identity readback")
    require(len(actual) == 584 and actual.source_id.is_unique, "Complete unique source readback")
    require(
        json.loads((out / "source_metadata_checks.json").read_text(encoding="utf-8")) == rows,
        "Full metadata JSON readback",
    )
    for name in (
        "request_manifest.json",
        "source_metadata_checks.csv",
        "source_metadata_checks.json",
    ):
        artifacts[name] = sha(out / name)
    require(all(sha(ROOT / n) == h for n, h in pins.items()), "Immutable input closure")
    report = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "status": "catalogue_check_complete",
        "parent_readback_sha256": PARENT_SHA,
        "source_files": len(rows),
        "source_pairs": core.sample_id.nunique(),
        "nominal_source_days": core.source_day.nunique(),
        "status_counts": flat.catalogue_status.value_counts().to_dict(),
        "provider_checksum_status_counts": flat.get(
            "provider_checksum_status", pd.Series(dtype=str)
        )
        .value_counts()
        .to_dict(),
        "query_batches": len(batches),
        "http_attempts_in_saved_receipts": sum(x[2]["attempts"] for x in results),
        "response_bytes": sum(x[2]["response_bytes"] for x in results),
        "new_http_attempts_this_invocation": sum(x[3] for x in results),
        "first_query_utc": min(x[2]["checked_at_utc"] for x in results),
        "last_query_utc": max(x[2]["checked_at_utc"] for x in results),
        "historical_raw_bytes": int(core.bytes.sum()),
        "raw_files_downloaded": 0,
        "data_endpoints_checked": 0,
        "raw_integrity_verified": False,
        "native_lineage_rechecked": False,
        "cloud_jobs_started": 0,
        "validation_accessed": False,
        "final_test_accessed": False,
        "labels_created": False,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "model_ready": False,
        "protected_inputs_verified": len(protected),
        "input_sha256": pins,
        "artifact_sha256": artifacts,
        "limits": [
            "Exact current catalogue metadata is not a data endpoint download/access test",
            "No granule bytes or native input pointers were rechecked",
            "MD5 cannot be compared to historical SHA-256 without the raw bytes",
            "Zero hits means absent from this exact current collection query, not every archive",
            "No current alternative filename is silently substituted",
            "Purpose-selected method pilot, not population label accuracy evidence",
        ],
    }
    write_json(out / "readback.json", report)
    require(
        json.loads((out / "readback.json").read_text(encoding="utf-8")) == report, "Report readback"
    )
    require(all(sha(out / n) == h for n, h in artifacts.items()), "Catalogue artifact closure")
    write_json(
        out / "completion_readback.json",
        {
            "status": "passed",
            "report_sha256": sha(out / "readback.json"),
            "inputs_verified": len(pins),
            "artifacts_verified": len(artifacts),
        },
    )
    print("Catalogue status:", json.dumps(report["status_counts"]), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", required=True)
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--max-batches", type=int)
    args = parser.parse_args()
    try:
        run(args.resume, args.max_batches)
    except Exception as error:
        # Never print transport response bodies, auth links or arbitrary exception text.
        print("Catalogue check incomplete:", type(error).__name__, flush=True)
        raise SystemExit(1) from None
