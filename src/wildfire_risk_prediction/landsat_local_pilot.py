"""Bounded range access and diagnostic local Landsat math; not accepted feature production."""

import hashlib
import json
import multiprocessing
import re
import threading
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, urlunsplit

import numpy as np
import requests


class PilotStop(Exception):
    pass


def require(ok, code):
    if not ok:
        raise PilotStop(code)


def unsigned(url):
    part = urlsplit(url)
    return urlunsplit((part.scheme, part.netloc, part.path, "", ""))


class BudgetHTTP:
    """Serialize transfers; count bodies and never persist URLs containing a token."""

    def __init__(self, decision, folder):
        self.start = datetime.fromisoformat(decision["original_probe_start_utc"])
        self.limit = decision["max_body_bytes"]
        self.max_requests = decision["max_requests"]
        self.max_seconds = decision["max_seconds"]
        self.bytes = decision["prior_probe_body_bytes"]
        self.requests = decision["prior_probe_request_attempts"]
        self.folder = folder
        self.ledger = []
        self.lock = threading.RLock()
        self.session = requests.Session()
        self.session.headers.update({"Accept-Encoding": "identity"})

    def check(self):
        require((datetime.now(UTC) - self.start).total_seconds() < self.max_seconds, "time_limit")
        require(self.bytes < self.limit, "body_byte_limit")
        require(self.requests < self.max_requests, "request_limit")

    def get(self, url, *, role, method="GET", headers=None, maximum=None):
        with self.lock:
            self.check()
            parsed = urlsplit(url)
            require(
                parsed.scheme == "https"
                and (
                    parsed.hostname == "planetarycomputer.microsoft.com"
                    or parsed.hostname.endswith(".blob.core.windows.net")
                ),
                "unexpected_remote_host",
            )
            self.requests += 1
            item = {"request": self.requests, "role": role, "method": method, "bytes": 0}
            self.ledger.append(item)
            try:
                response = self.session.request(
                    method, url, headers=headers, timeout=20, stream=True, allow_redirects=False
                )
                with response:
                    item["status"] = response.status_code
                    require(
                        response.status_code in {200, 206},
                        "remote_http_" + str(response.status_code),
                    )
                    if method == "HEAD":
                        return b"", dict(response.headers)
                    cap = min(maximum or self.limit, self.limit - self.bytes)
                    length = response.headers.get("Content-Length")
                    require(length is None or int(length) <= cap, "response_exceeds_bound")
                    payload = bytearray()
                    while len(payload) < cap:
                        self.check_time_only()
                        chunk = response.raw.read(min(16384, cap - len(payload)))
                        if not chunk:
                            break
                        self.bytes += len(chunk)
                        item["bytes"] += len(chunk)
                        payload.extend(chunk)
                    require(
                        len(payload) < cap or (length is not None and int(length) == cap),
                        "bounded_response_eof_unverified",
                    )
                    return bytes(payload), dict(response.headers)
            except PilotStop:
                raise
            except Exception:
                raise PilotStop("remote_connection_failure") from None
            finally:
                (self.folder / "network_checkpoint.json").write_text(
                    json.dumps(
                        {
                            "body_bytes": self.bytes,
                            "request_attempts": self.requests,
                            "ledger": self.ledger,
                        },
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )

    def check_time_only(self):
        require((datetime.now(UTC) - self.start).total_seconds() < self.max_seconds, "time_limit")

    def json(self, url, role):
        data, _ = self.get(url, role=role, maximum=1048576)
        return json.loads(data)


class RangeProxy:
    """GDAL sees localhost only; all Internet reads pass through the budget."""

    def __init__(self, http):
        self.http = http
        self.assets = {}
        self.cache = {}
        self.last_stop = None
        self.tokens = {}
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_HEAD(self):
                self.respond(True)

            def do_GET(self):
                self.respond(False)

            def respond(self, head):
                try:
                    key = self.path.removeprefix("/").removesuffix(".tif")
                    require(key in owner.assets, "unknown_proxy_asset")
                    href = owner.assets[key]
                    if head:
                        _, headers = owner.http.get(href, role="raster_head", method="HEAD")
                        self.send_response(200)
                        self.send_header("Content-Length", headers["Content-Length"])
                        self.send_header("Accept-Ranges", "bytes")
                        self.end_headers()
                        return
                    value = self.headers.get("Range", "")
                    match = re.fullmatch(r"bytes=(\d+)-(\d+)", value)
                    require(match is not None, "raster_range_required")
                    start, end = map(int, match.groups())
                    require(0 <= start <= end and end - start < 8388608, "range_size_limit")
                    cache_key = (key, start, end)
                    if cache_key not in owner.cache:
                        data, headers = owner.http.get(
                            href,
                            role="raster_range",
                            headers={"Range": value},
                            maximum=end - start + 1,
                        )
                        require(
                            headers.get("Content-Range", "").startswith(f"bytes {start}-"),
                            "range_response_identity",
                        )
                        name = f"range_{key}_{start}_{end}.bin"
                        (owner.http.folder / name).write_bytes(data)
                        owner.cache[cache_key] = (data, headers["Content-Range"])
                    data, content_range = owner.cache[cache_key]
                    self.send_response(206)
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("Content-Range", content_range)
                    self.end_headers()
                    self.wfile.write(data)
                except Exception as exc:
                    owner.last_stop = (
                        str(exc) if isinstance(exc, PilotStop) else "proxy_read_failure"
                    )
                    self.send_response(503)
                    self.end_headers()

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def url(self, href):
        parsed = urlsplit(href)
        require(parsed.hostname.endswith(".blob.core.windows.net"), "raster_not_azure_blob")
        account = parsed.hostname.split(".")[0]
        container = parsed.path.strip("/").split("/")[0]
        cache_key = (account, container)
        if parsed.query:
            signed = href
        else:
            if cache_key not in self.tokens:
                token = self.http.json(
                    f"https://planetarycomputer.microsoft.com/api/sas/v1/token/{account}/{container}",
                    "anonymous_read_token",
                )
                self.tokens[cache_key] = token["token"]
            signed = href + "?" + self.tokens[cache_key]
        key = hashlib.sha256(unsigned(href).encode()).hexdigest()[:20]
        self.assets[key] = signed
        return f"http://127.0.0.1:{self.server.server_port}/{key}.tif"

    def close(self):
        self.server.shutdown()
        self.server.server_close()


def native_indices(red, nir, swir, qa, saturation):
    red, nir, swir = [x.astype(float) * 0.0000275 - 0.2 for x in (red, nir, swir)]
    valid = ((qa & 191) == 0) & (saturation == 0)
    for value in (red, nir, swir):
        valid &= (value >= 0) & (value <= 1)
    valid &= (nir + red > 0) & (nir + swir > 0)
    a, b = np.full(red.shape, np.nan), np.full(red.shape, np.nan)
    np.divide(nir - red, nir + red, out=a, where=valid)
    np.divide(nir - swir, nir + swir, out=b, where=valid)
    return a, b


def _serve_process(decision, folder, assets, connection):
    http = BudgetHTTP(decision, folder)
    proxy = RangeProxy(http)
    try:
        urls = {href: proxy.url(href) for href in assets}
        connection.send({"urls": urls})
        connection.recv()
    except Exception:
        connection.send({"error": "proxy_process_failed"})
    finally:
        proxy.close()


class ProcessProxy:
    """Separate interpreter prevents a GDAL call from starving Python HTTP handlers."""

    def __init__(self, http, assets):
        context = multiprocessing.get_context("spawn")
        parent, child = context.Pipe()
        decision = {
            "original_probe_start_utc": http.start.isoformat(),
            "max_body_bytes": http.limit,
            "max_requests": http.max_requests,
            "max_seconds": http.max_seconds,
            "prior_probe_body_bytes": http.bytes,
            "prior_probe_request_attempts": http.requests,
        }
        self.http, self.connection = http, parent
        self.process = context.Process(
            target=_serve_process, args=(decision, http.folder, assets, child), daemon=True
        )
        self.process.start()
        require(parent.poll(30), "proxy_start_timeout")
        result = parent.recv()
        require("urls" in result, "proxy_start_failed")
        self.urls = result["urls"]
        self.last_stop = None

    def url(self, href):
        return self.urls[href]

    def close(self):
        try:
            self.connection.send("stop")
            self.process.join(5)
        finally:
            if self.process.is_alive():
                self.process.terminate()
                self.process.join()
            checkpoint = json.loads((self.http.folder / "network_checkpoint.json").read_bytes())
            self.http.bytes, self.http.requests = (
                checkpoint["body_bytes"],
                checkpoint["request_attempts"],
            )
