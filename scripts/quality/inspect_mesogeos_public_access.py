"""Bounded anonymous public metadata checks; never fetch datacube chunks."""

import ast
import hashlib
import json
import re
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
TREE = "https://api.github.com/repos/Orion-AI-Lab/mesogeos/git/trees/main?recursive=1"
FOLDER = "https://drive.google.com/drive/folders/1aRXQXVvw6hz0eYgtJDoixjPQO-_bRKz9"
MAX_BYTES = 1_000_000


def metadata(url):
    request = urllib.request.Request(
        url, headers={"User-Agent": "wildfire-research-public-metadata/1.0"}
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                return {"requested_url": url, "status": "metadata_size_cap_reached"}, None
            return {
                "requested_url": url,
                "final_url": response.url.split("?")[0],
                "status": int(response.status),
                "bytes": len(body),
                "response_sha256": hashlib.sha256(body).hexdigest(),
            }, body
    except (urllib.error.URLError, TimeoutError):
        # No response body, headers, cookies or auth URLs are printed.
        return {"requested_url": url, "status": "public_metadata_unavailable"}, None


def main():
    out = (
        ROOT
        / "outputs/reports/dataset/mesogeos_public_access_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    tree_receipt, tree_body = metadata(TREE)
    paths = []
    if tree_body:
        tree = json.loads(tree_body)
        tree_receipt["commit"] = tree["sha"]
        tree_receipt["truncated"] = tree.get("truncated", True)
        for row in tree["tree"]:
            paths.append({key: row[key] for key in ("path", "type", "sha", "size") if key in row})
    drive_receipt, drive_body = metadata(FOLDER)
    items = []
    if drive_body:
        html = drive_body.decode("utf-8")
        pattern = r"window\['_DRIVE_ivd'\]\s*=\s*('(?:[^'\\]|\\.)*');"
        matches = re.findall(pattern, html)
        if len(matches) == 1:
            payload = json.loads(ast.literal_eval(matches[0]))
            for row in payload[0] or []:
                if isinstance(row, list) and len(row) >= 4:
                    items.append({"id": row[0], "name": row[2], "mime_type": row[3]})
        drive_receipt["public_listing_decoded"] = bool(items)
    for name, value in [("repository_tree.json", paths), ("public_folder_items.json", items)]:
        (out / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    result = {
        "status": "public_metadata_only_no_reference_data_acceptance",
        "repository": tree_receipt,
        "drive_root": drive_receipt,
        "data_files_downloaded": 0,
        "scientific_values_opened": False,
        "credentials_used": False,
        "new_model_or_labels": False,
        "artifact_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob("*.json")
        },
    }
    (out / "readback.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(out.relative_to(ROOT).as_posix())
    print("repository_paths", len(paths), "public_folder_items", len(items))


if __name__ == "__main__":
    main()
