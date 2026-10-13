"""Run on the user's Windows PC, with VM stopped. Never print OAuth credentials."""

import argparse
import base64
import hashlib
import http.server
import json
import os
import re
import secrets
import time
import urllib.parse
import webbrowser
from pathlib import Path

from drive_job_store import SCOPE, TOKEN, DriveAPI, require


def safe_failure(error):
    labels = {
        "Browser could not open": "BROWSER_NOT_OPENED",
        "Browser authorization timed out; rerun locally": "BROWSER_TIMEOUT",
        "Offline authorization absent": "OFFLINE_AUTHORIZATION_ABSENT",
        "Granted scope differs": "SCOPE_DIFFERS",
        "Existing private connection required": "PRIVATE_CONNECTION_MISSING",
        "Renewed authorization must access the existing folder": "EXISTING_FOLDER_ACCESS_FAILED",
        "Drive HTTP 400; no secrets logged": "OAUTH_OR_DRIVE_HTTP_400",
    }
    message = error.args[0] if len(error.args) == 1 else None
    return labels.get(message, "UNCLASSIFIED") if isinstance(message, str) else "UNCLASSIFIED"


def authorize(client):
    require(client.get("client_id", "").endswith(".apps.googleusercontent.com"), "Desktop client")
    verifier, state = secrets.token_urlsafe(64), secrets.token_urlsafe(32)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    )
    received = {}

    class Callback(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Callback URL contains a code: do not log it.

        def do_GET(self):
            parsed = urllib.parse.urlsplit(self.path)
            values = urllib.parse.parse_qs(parsed.query)
            valid = (
                parsed.path == "/callback"
                and values.get("state") == [state]
                and len(values.get("code", [])) == 1
                and "error" not in values
            )
            self.send_response(200 if valid else 400)
            self.end_headers()
            self.wfile.write(
                b"Authorization received. Return to your terminal."
                if valid
                else b"Invalid callback."
            )
            if valid:
                received["code"] = values["code"][0]

    with http.server.HTTPServer(("127.0.0.1", 0), Callback) as server:
        redirect = f"http://127.0.0.1:{server.server_port}/callback"
        url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(
            {
                "client_id": client["client_id"],
                "redirect_uri": redirect,
                "response_type": "code",
                "scope": SCOPE,
                "access_type": "offline",
                "prompt": "consent",
                "state": state,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            }
        )
        require(webbrowser.open(url), "Browser could not open")
        server.timeout = 1
        deadline = time.monotonic() + 300
        while not received and time.monotonic() < deadline:
            server.handle_request()
        require(received, "Browser authorization timed out; rerun locally")
    # Reuse the bounded transport, with an in-memory placeholder refresh token.
    api = DriveAPI({**client, "scope": SCOPE, "refresh_token": "not-used"})
    body = urllib.parse.urlencode(
        {
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "code": received["code"],
            "code_verifier": verifier,
            "redirect_uri": redirect,
            "grant_type": "authorization_code",
        }
    ).encode()
    token = json.loads(
        api.wire(TOKEN, "POST", body, {"Content-Type": "application/x-www-form-urlencoded"})
    )
    require(token.get("refresh_token"), "Offline authorization absent")
    require(set(token.get("scope", "").split()) == {SCOPE}, "Granted scope differs")
    return {
        "client_id": client["client_id"],
        "client_secret": client["client_secret"],
        "refresh_token": token["refresh_token"],
        "scope": SCOPE,
    }


def main():
    require(os.name == "nt", "Connect from the Windows PC while the VM is stopped")
    parser = argparse.ArgumentParser()
    parser.add_argument("--renew", action="store_true")
    parser.add_argument("--connection", type=Path)
    args = parser.parse_args()
    require(args.connection is None or args.renew, "Explicit connection is renewal-only")
    target = args.connection or (
        Path(os.environ["LOCALAPPDATA"]) / "wildfire-cloud-auth" / "drive_connection.json"
    )
    if args.renew:
        require(
            target.is_absolute() and target.is_file() and not target.is_symlink(),
            "Existing private connection required",
        )
        previous = json.loads(target.read_text(encoding="utf-8"))
        connection = authorize(previous)
        require(
            connection["client_id"] == previous["client_id"]
            and connection["client_secret"] == previous["client_secret"]
            and connection["scope"] == previous["scope"] == SCOPE,
            "Renewal must preserve client and scope",
        )
        connection["folder_id"] = previous["folder_id"]
        require(
            re.fullmatch(r"[A-Za-z0-9_-]{10,200}", connection["folder_id"]),
            "Existing Drive folder identity",
        )
        folder = json.loads(
            DriveAPI(connection).request(
                f"/files/{connection['folder_id']}?fields=id,mimeType,trashed,capabilities(canAddChildren)"
            )
        )
        require(
            folder.get("id") == connection["folder_id"]
            and folder.get("mimeType") == "application/vnd.google-apps.folder"
            and folder.get("trashed") is False
            and folder.get("capabilities", {}).get("canAddChildren") is True,
            "Renewed authorization must access the existing folder",
        )
        pending = target.with_suffix(".pending")
        with pending.open("x", encoding="utf-8") as stream:
            json.dump(connection, stream)
        pending.replace(target)
        print("Authorization renewed; the same Drive folder and saved jobs are preserved.")
        print("Upload the renewed connection file privately to the stopped/run-ready VM:", target)
        return
    require(not target.exists(), "Existing Drive connection: reuse or --renew")
    source = Path(input("Downloaded Desktop OAuth JSON path: ").strip().strip('"'))
    document = json.loads(source.read_text(encoding="utf-8"))
    require(set(document) == {"installed"}, "Select Desktop app, not Web application")
    connection = authorize(document["installed"])
    name = "wildfire-gcp-checkpoints-" + secrets.token_hex(6)
    connection["folder_id"] = DriveAPI(connection).create_file(
        {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    # Never overwrite an existing connection to a previous persistent store.
    with target.open("x", encoding="utf-8") as stream:
        json.dump(connection, stream)
    print("Drive connection saved outside the project:", target)
    print("New Drive folder:", name)
    print("Do not send the JSON contents or an authorization screenshot to chat.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(
            "Drive setup failed:", type(error).__name__, safe_failure(error), "; no secrets logged."
        )
        raise SystemExit(1) from None
