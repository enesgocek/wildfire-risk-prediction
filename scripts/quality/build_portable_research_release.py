"""Assemble immutable research parts and relocate only UI evidence links."""

import json
import os
import shutil
import subprocess
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from verify_local_research_release import verify

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.portable_review_links import local_target, verify_html

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
PREVIOUS = BASE / "local_research_release_v2/20261124T023339Z_6f277b31"
UI = BASE / "historical_research_prototype_v3/20261124T173653Z_3a064f3e"
UI_AUDIT = BASE / "geographic_research_prototype_audit_v1/20261124T174542Z_20acbee4"
OVERLAP = BASE / "source_disjoint_frozen_assessment_v1/20261124T031245Z_91cd329d"
OVERLAP_AUDIT = BASE / "source_disjoint_frozen_assessment_audit_v1/20261124T031414Z_9c5bc04c"
OVERLAP_CLOSURE = BASE / "source_disjoint_assessment_closure_v1/20261124T031637Z_136916ba"
CASES = BASE / "frozen_rank_case_review_v1/20261124T024256Z_abeb3e00"
CASE_AUDIT = BASE / "frozen_rank_case_audit_v1/20261124T024500Z_68829a04"
SOURCES = {
    UI: "f6140ef72f09416f2a6fbc01e1fafa61d241b64e2b0cd63e95fc6604cf43f4a8",
    UI_AUDIT: "3b31d9886e2586cbf03a2e3185eabbe7d1009058755fd5421683e0e541f5c135",
    OVERLAP: "7f6e16ff58084954610dea8ca41d9ca87ece9fd02192b076cfec5973845a5d23",
    OVERLAP_AUDIT: "caf4f7650b1d8c5842e27a14d387081bb1967aa8b728a10e83c82d012afc2275",
    OVERLAP_CLOSURE: "aa2e31f94b371844d4aeb14587dc91fe97011982641515c1942dc67e894023f5",
    CASES: "a65579afa7165b72a830f22e39367bb9331e100c0b5aa7d0b982bdf8dcc8c4af",
    CASE_AUDIT: "28ec52a4689ef17b2b5b4754faeb480d3a779cc1a37844c0e3a83e1428a7ad59",
}


def main():
    if (
        digest(PREVIOUS / "readback.json")
        != "0e11f0ef7d24d74a139e812a3b6f8faf659f81a2319c3ff2f72a8955660990d2"
    ):
        raise ValueError("Exact previous separate-part release")
    verify(PREVIOUS)
    base_manifest = json.loads((PREVIOUS / "package/manifest.json").read_bytes())
    pins = {PREVIOUS / "readback.json": digest(PREVIOUS / "readback.json")}
    for folder, expected in SOURCES.items():
        path = folder / "readback.json"
        if digest(path) != expected:
            raise ValueError("Frozen input receipt")
        pins[path] = expected
        for name, sha in json.loads(path.read_bytes()).get("artifact_sha256", {}).items():
            pins[folder / name] = sha
    if not all(digest(p) == sha for p, sha in pins.items()):
        raise ValueError("Frozen input artifacts")
    out = (
        BASE
        / "portable_research_release_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    package = out / "package"
    package.mkdir(parents=True)
    entries = {}

    def copy(source, name, origin):
        target = package / name
        if target.exists():
            raise ValueError("Duplicate package member: " + name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        sha = digest(source)
        if digest(target) != sha:
            raise ValueError("Byte copy mismatch")
        entries[name] = {"sha256": sha, "bytes": target.stat().st_size, "origin": origin}

    def repo_copy(source, name):
        copy(source, name, {"repository_path": source.relative_to(ROOT).as_posix()})

    def generated(name, content, origin):
        path = package / name
        if path.exists():
            raise ValueError("Duplicate generated member")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        entries[name] = {"sha256": digest(path), "bytes": path.stat().st_size, "origin": origin}

    for name, entry in base_manifest["files"].items():
        if name.startswith("interface/") or name in ("README.md", "AI_USE.md"):
            continue
        copy(
            PREVIOUS / "package" / name,
            name,
            {
                "base_release_readback_sha256": pins[PREVIOUS / "readback.json"],
                "member": name,
                "original_source_path": entry.get("source_path"),
            },
        )
    for name in (
        "inceleme.html",
        "research-app.js",
        "research-core.js",
        "research-map.js",
        "review_data.js",
        "geography_data.js",
    ):
        repo_copy(UI / name, "interface/" + name)
    names = subprocess.check_output(["git", "ls-files", "docs"], cwd=ROOT, text=True).splitlines()
    documents = [ROOT / n for n in names if n.endswith(".md")]
    for path in documents:
        repo_copy(path, "documents/" + path.relative_to(ROOT / "docs").as_posix())
    repo_copy(ROOT / "docs/research/AI_USE.md", "AI_USE.md")
    context_path = UI / "research_context.js"
    raw = context_path.read_text(encoding="utf-8").strip()
    prefix = "globalThis.RESEARCH_CONTEXT="
    context = json.loads(raw.removeprefix(prefix)[:-1])
    original_links = context["links"]
    links = []
    for link in original_links:
        source = (UI / link["path"]).resolve()
        if not source.is_relative_to(ROOT / "docs") or digest(source) != link["sha256"]:
            raise ValueError("Current evidence source")
        target = package / "documents" / source.relative_to(ROOT / "docs")
        links.append(
            link | {"path": os.path.relpath(target, package / "interface").replace("\\", "/")}
        )
    context["links"] = links
    generated(
        "interface/research_context.js",
        prefix
        + json.dumps(context, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        + ";\n",
        {
            "derived_from": context_path.relative_to(ROOT).as_posix(),
            "source_sha256": digest(context_path),
            "change": "evidence_link_paths_only",
        },
    )
    for folder in SOURCES:
        repo_copy(folder / "readback.json", "evidence/current/" + folder.parent.name + ".json")
    destinations = {
        OVERLAP: "results/source_overlap/assessment",
        OVERLAP_CLOSURE: "results/source_overlap",
        CASES: "results/case_context",
    }
    for folder, destination in destinations.items():
        receipt = json.loads((folder / "readback.json").read_bytes())
        for name in receipt["artifact_sha256"]:
            repo_copy(folder / name, destination + "/" + name)
    for path in (
        Path(__file__),
        Path(__file__).with_name("portable_research_start.html"),
        Path(__file__).with_name("audit_portable_research_release.py"),
        ROOT / "src/wildfire_risk_prediction/portable_review_links.py",
        ROOT / "tests/js/research_prototype_v3_dom.test.cjs",
    ):
        repo_copy(path, "reproducibility/extensions/" + path.relative_to(ROOT).as_posix())
    repo_copy(Path(__file__).with_name("portable_research_start.html"), "index.html")
    generated(
        "README.md",
        "# Taşınabilir deneysel araştırma paketi\n\n"
        "ZIP'in tamamını çıkardıktan sonra index.html dosyasını aç.\n"
        "interface/inceleme.html güncel v3 ekranıdır; kanıt bağlantıları paket içindedir.\n"
        "data/ altında özellikler, üyelikler ve kaynak izleri ayrı tutulur.\n"
        "Bu, nihai etiketli eğitim birleştirmesi veya doğrulanmış risk ürünü değildir.\n"
        "documents/ içindeki tarihsel belgeler özgün depo/ham veri yollarını da anlatır;\n"
        "bu eski ham kaynakların tamamı burada varmış sayılmaz.\n"
        "Yeni eğitim, tahmin, indirme, bulut veya yayın yapılmaz.\n",
        {"generated": "portable_entry_instructions"},
    )
    manifest = {
        "version": "portable_research_release_v1",
        "client_date": "2026-11-24",
        "experimental_research_only": True,
        "labelled_training_dataset": False,
        "final_merge": False,
        "base_release_readback_sha256": pins[PREVIOUS / "readback.json"],
        "prototype_readback_sha256": SOURCES[UI],
        "files": entries,
    }
    path = package / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    checked_html_links = verify_html(package, "index.html") + verify_html(
        package, "interface/inceleme.html"
    )
    for link in context["links"]:
        target = local_target(package, "interface/inceleme.html", link["path"])
        if digest(target) != link["sha256"]:
            raise ValueError("Portable evidence copy")
    archive = out / "research_release.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
        for path in sorted(package.rglob("*")):
            if path.is_file():
                zipped.write(path, path.relative_to(package).as_posix())
    if not all(digest(p) == sha for p, sha in pins.items()):
        raise ValueError("Existing artifacts modified")
    body = {
        "status": "portable_release_built_pending_relocation_audit",
        "manifest_sha256": digest(package / "manifest.json"),
        "zip_sha256": digest(archive),
        "zip_bytes": archive.stat().st_size,
        "files_including_manifest": len(entries) + 1,
        "document_snapshots": len(documents),
        "html_links_checked": checked_html_links,
        "only_interface_context_link_paths_changed": True,
        "new_training_predictions_or_labels": False,
        "closed_years_or_final_merge": False,
        "base_release_readback_sha256": pins[PREVIOUS / "readback.json"],
        "input_receipt_sha256": {
            p.relative_to(ROOT).as_posix(): sha
            for p, sha in pins.items()
            if p.name == "readback.json"
        },
        "producer_sha256": digest(Path(__file__)),
    }
    (out / "readback.json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    verify(out)
    print(out.relative_to(ROOT).as_posix(), body["status"], "files", len(entries) + 1, flush=True)


if __name__ == "__main__":
    main()
