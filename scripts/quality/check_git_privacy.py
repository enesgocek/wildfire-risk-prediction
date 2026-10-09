"""Check working candidates or exact staged blobs without displaying secret values."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
MAX_BYTES = 2 * 1024 * 1024
RULES = {
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(rb"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{40,})\b"),
    "google_access_token": re.compile(rb"\bya29\.[A-Za-z0-9_-]{20,}"),
    "google_client_secret": re.compile(rb"\bGOCSPX-[A-Za-z0-9_-]{20,}"),
    "google_api_key": re.compile(rb"\bAIza[A-Za-z0-9_-]{35}\b"),
    "aws_access_key": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "jwt": re.compile(rb"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{15,}\b"),
    "credential_json": re.compile(
        rb'"(?:refresh_token|client_secret|private_key)"\s*:\s*"[^"\r\n]{20,}"'
    ),
    "url_credentials": re.compile(rb"https?://[^\s/@:]{3,}:[^\s/@]{8,}@"),
}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.DEVNULL)


def paths(raw):
    return [value.decode("utf-8") for value in raw.split(b"\0") if value]


def findings(name, content):
    """Return only path/rule/line metadata, never the matched credential."""
    path = PurePosixPath(name)
    lower = name.lower()
    basename = path.name.lower()
    result = []
    if (
        lower.startswith(("outputs/", "data/raw/", "data/interim/", "data/processed/", "models/"))
        or any(p.lower() in {".aws", ".codex", ".venv", "node_modules"} for p in path.parts)
        or (basename.startswith(".env") and basename != ".env.example")
        or basename in {"drive_connection.json", "credentials.json", "token.json", ".netrc"}
        or (basename.startswith("client_secret") and path.suffix.lower() == ".json")
        or path.suffix.lower()
        in {
            ".zip",
            ".docx",
            ".pdf",
            ".pem",
            ".key",
            ".p12",
            ".pfx",
            ".tif",
            ".tiff",
            ".hdf",
            ".h5",
            ".nc",
            ".parquet",
            ".pkl",
            ".joblib",
            ".sqlite",
            ".db",
        }
    ):
        result.append({"path": name, "rule": "private_or_bulk_path"})
    if len(content) > MAX_BYTES:
        result.append({"path": name, "rule": "oversized_blob"})
    if b"\0" in content:
        result.append({"path": name, "rule": "binary_blob_requires_review"})
    for rule, pattern in RULES.items():
        for match in pattern.finditer(content):
            result.append(
                {"path": name, "rule": rule, "line": content[: match.start()].count(b"\n") + 1}
            )
    return result


def scan(scope):
    if scope == "staged":
        names = paths(git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"))
        blobs = [(name, git("show", f":{name}")) for name in names]
    else:
        names = sorted(
            set(
                paths(git("diff", "HEAD", "--name-only", "--diff-filter=ACMR", "-z"))
                + paths(git("ls-files", "--others", "--exclude-standard", "-z"))
            )
        )
        blobs = [(name, (ROOT / name).read_bytes()) for name in names]
    matches = [finding for name, blob in blobs for finding in findings(name, blob)]
    report = {
        "status": "passed" if not matches else "blocked",
        "scope": scope,
        "files_checked": len(blobs),
        "bytes_checked": sum(len(blob) for _, blob in blobs),
        "findings": matches,
        "limits": (
            "Pattern/path checks plus human diff review; "
            "not proof that every possible secret is absent"
        ),
    }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=["working", "staged"], default="staged")
    args = parser.parse_args()
    report = scan(args.scope)
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
