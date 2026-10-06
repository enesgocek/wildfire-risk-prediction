"""Drive-file scoped, single-writer store. No delete/update/sync operations.

Flat object names avoid path/folder ambiguity. Duplicate logical objects fail
closed. Creation uses a pre-generated Drive ID so uncertain retries keep the
same identity. This is not a distributed lock or GCS conditional-create.
"""

import hashlib
import json
import os
import re
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SCOPE = "https://www.googleapis.com/auth/drive.file"
API = "https://www.googleapis.com/drive/v3"
UPLOAD = "https://www.googleapis.com/upload/drive/v3"
TOKEN = "https://oauth2.googleapis.com/token"
MAX_BYTES = 150_000_000
PAYLOAD_MIMES = {
    "application/octet-stream",
    "application/zip",
    "application/x-zip",
    "application/x-zip-compressed",
}
MARKER_MIMES = {"application/octet-stream", "application/json", "text/plain"}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("Drive redirect refused")


def require(ok, message):
    if not ok:
        raise ValueError(message)


class DriveAPI:
    """Bounded requests; errors deliberately exclude response bodies/secrets."""

    def __init__(self, connection, opener=None, sleep=time.sleep):
        require(connection.get("scope") == SCOPE, "Drive-file scope required")
        for field in ("client_id", "client_secret", "refresh_token"):
            require(
                isinstance(connection.get(field), str) and connection[field], "OAuth connection"
            )
        self.connection = connection
        self.opener = opener or urllib.request.build_opener(NoRedirect()).open
        self.sleep = sleep
        self.access_token = None
        self.expiry = 0

    def wire(self, url, method, data=None, headers=None, retry=False):
        # Never follow a redirect with an Authorization header to another host.
        allowed = {"www.googleapis.com", "oauth2.googleapis.com"}
        parsed = urllib.parse.urlsplit(url)
        require(
            parsed.scheme == "https" and parsed.hostname in allowed, "Unapproved Drive endpoint"
        )
        for attempt in range(3 if retry else 1):
            request = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
            try:
                with self.opener(request, timeout=45) as response:
                    require(
                        urllib.parse.urlsplit(response.geturl()).hostname in allowed,
                        "Drive response endpoint",
                    )
                    value = response.read(MAX_BYTES + 1)
                    require(len(value) <= MAX_BYTES, "Drive response oversized")
                    return value
            except urllib.error.HTTPError as error:
                if error.code not in {429, 500, 502, 503, 504} or attempt == 2 or not retry:
                    raise RuntimeError(f"Drive HTTP {error.code}; no secrets logged") from None
            except (TimeoutError, OSError):
                if attempt == 2 or not retry:
                    raise RuntimeError("Drive transport failed; checkpoint retained") from None
            self.sleep(2 ** (attempt + 1))
        raise RuntimeError("Drive retry exhausted")

    def token(self):
        if self.access_token is None or time.monotonic() >= self.expiry:
            body = urllib.parse.urlencode(
                {
                    "client_id": self.connection["client_id"],
                    "client_secret": self.connection["client_secret"],
                    "refresh_token": self.connection["refresh_token"],
                    "grant_type": "refresh_token",
                }
            ).encode()
            result = json.loads(
                self.wire(
                    TOKEN, "POST", body, {"Content-Type": "application/x-www-form-urlencoded"}, True
                )
            )
            require(result.get("token_type", "").lower() == "bearer", "OAuth token type")
            require(result.get("access_token"), "OAuth access token missing")
            if "scope" in result:
                require(set(result["scope"].split()) == {SCOPE}, "Unexpected OAuth scope")
            self.access_token = result["access_token"]
            self.expiry = time.monotonic() + max(0, int(result["expires_in"]) - 60)
        return self.access_token

    def request(self, path, method="GET", data=None, content_type=None, upload=False):
        headers = {"Authorization": "Bearer " + self.token()}
        if content_type:
            headers["Content-Type"] = content_type
        return self.wire((UPLOAD if upload else API) + path, method, data, headers, method == "GET")

    def listing(self, query):
        files, page = [], None
        for _ in range(100):
            params = {
                "q": query,
                "fields": (
                    "nextPageToken,incompleteSearch,files(id,name,size,mimeType,appProperties)"
                ),
                "pageSize": "1000",
                "spaces": "drive",
            }
            if page:
                params["pageToken"] = page
            result = json.loads(self.request("/files?" + urllib.parse.urlencode(params)))
            require(result.get("incompleteSearch") is not True, "Incomplete Drive listing")
            files.extend(result["files"])
            page = result.get("nextPageToken")
            if not page:
                return files
        raise ValueError("Drive listing exceeds bound")

    def create_file(self, metadata, data=None):
        ids = json.loads(self.request("/files/generateIds?count=1&space=drive"))["ids"]
        require(
            len(ids) == 1 and re.fullmatch(r"[A-Za-z0-9_-]{5,200}", ids[0]),
            "Drive generated identity",
        )
        metadata = {**metadata, "id": ids[0]}
        if data is None:
            return json.loads(
                self.request(
                    "/files?fields=id", "POST", json.dumps(metadata).encode(), "application/json"
                )
            )["id"]
        boundary = "wildfire_" + secrets.token_hex(16)
        body = (
            f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n".encode()
            + json.dumps(metadata).encode()
            + f"\r\n--{boundary}\r\nContent-Type: application/octet-stream\r\n\r\n".encode()
            + data
            + f"\r\n--{boundary}--\r\n".encode()
        )
        # On an uncertain upload, inspect the SAME generated ID; never blindly
        # re-create a second file. Failure leaves any orphan for inspection.
        try:
            result = self.request(
                "/files?uploadType=multipart&fields=id",
                "POST",
                body,
                f"multipart/related; boundary={boundary}",
                upload=True,
            )
            require(json.loads(result)["id"] == ids[0], "Drive created identity changed")
        except RuntimeError:
            found = json.loads(self.request(f"/files/{ids[0]}?fields=id"))
            require(found["id"] == ids[0], "Uncertain Drive create")
        return ids[0]


class DriveJobStore:
    def __init__(self, api, folder_id):
        require(re.fullmatch(r"[A-Za-z0-9_-]{10,200}", folder_id), "Drive folder identity")
        self.api, self.folder_id = api, folder_id

    @classmethod
    def from_file(cls, path):
        path = Path(path)
        require(path.is_file() and not path.is_symlink(), "Private Drive connection required")
        if os.name == "posix":
            require(path.stat().st_mode & 0o077 == 0, "Connection must be chmod 600")
        connection = json.loads(path.read_text(encoding="utf-8"))
        return cls(DriveAPI(connection), connection["folder_id"])

    def entries(self):
        entries = self.api.listing(f"'{self.folder_id}' in parents and trashed = false")
        return self.validate_entries(entries)

    @staticmethod
    def validate_entries(entries):
        seen = set()
        for entry in entries:
            require(
                re.fullmatch(r"[A-Za-z0-9_-]{5,200}", entry.get("id", ""))
                and isinstance(entry.get("size"), str)
                and entry["size"].isascii()
                and entry["size"].isdigit()
                and 0 < int(entry["size"]) <= MAX_BYTES,
                "Drive object metadata",
            )
            props = entry.get("appProperties", {})
            key_hash = props.get("key_hash", "")
            require(
                set(props) == {"key_hash", "job", "protocol"}
                and props["protocol"] == "wildfire_store_v1"
                and re.fullmatch(r"[a-f0-9]{64}", key_hash)
                and re.fullmatch(r"[a-f0-9]{64}", props["job"]),
                "Foreign Drive object",
            )
            require(key_hash not in seen, "Duplicate Drive object; manual review required")
            seen.add(key_hash)
            require(entry["name"] == key_hash + ".object", "Drive object name changed")
            require(
                entry.get("mimeType") in PAYLOAD_MIMES | MARKER_MIMES,
                "Drive object type",
            )
        return entries

    @staticmethod
    def name(key):
        require(
            isinstance(key, str)
            and 0 < len(key) <= 512
            and not key.startswith("/")
            and "\\" not in key
            and all(p not in {"", ".", ".."} for p in key.split("/")),
            "Drive object key",
        )
        return hashlib.sha256(key.encode()).hexdigest() + ".object"

    @staticmethod
    def job(key):
        parts = key.split("/")
        require(
            len(parts) >= 2 and parts[0] == "jobs" and re.fullmatch(r"[a-f0-9]{64}", parts[1]),
            "Drive job identity",
        )
        return parts[1]

    def get(self, key):
        name = self.name(key)
        found = [e for e in self.entries() if e["name"] == name]
        if not found:
            return None
        entry = found[0]
        require(entry["appProperties"]["job"] == self.job(key), "Drive job changed")
        allowed = PAYLOAD_MIMES if key.endswith(".zip") else MARKER_MIMES
        require(entry["mimeType"] in allowed, "Drive object type does not match checkpoint role")
        size = int(entry["size"])
        require(0 < size <= MAX_BYTES, "Drive object size")
        data = self.api.request(f"/files/{entry['id']}?alt=media")
        require(len(data) == size, "Drive download size changed")
        return data

    def create(self, key, data):
        name = self.name(key)
        require(0 < len(data) <= MAX_BYTES, "Drive upload size")
        previous = self.get(key)
        if previous is not None:
            require(previous == data, "Immutable Drive collision")
            return
        self.api.create_file(
            {
                "name": name,
                "parents": [self.folder_id],
                "mimeType": "application/zip" if key.endswith(".zip") else "application/json",
                "appProperties": {
                    "protocol": "wildfire_store_v1",
                    "key_hash": name.removesuffix(".object"),
                    "job": self.job(key),
                },
            },
            data,
        )
        require(self.get(key) == data, "Drive upload readback differs")

    def used_bytes(self, prefix):
        return sum(
            int(e["size"]) for e in self.entries() if e["appProperties"]["job"] == self.job(prefix)
        )
