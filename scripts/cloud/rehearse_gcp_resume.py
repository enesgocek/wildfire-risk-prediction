"""Local interruption/recovery rehearsal with one actual received GCP pair.

No NASA/VM/Drive/GCS access. The saved products are validated by frozen science
code in new temporary output directories; this is not raw reprocessing.
"""

import importlib.util
import io
import json
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rehearse():
    core = load("resume_store", ROOT / "scripts/cloud/verified_job_store.py")
    frozen = load("resume_native", ROOT / "scripts/cloud/run_gcp_benchmark.py")
    received = ROOT / "outputs/gcp_benchmark/received/gcp_benchmark_results.zip"
    verified = json.loads(
        (
            ROOT / "outputs/reports/observation_coverage/gcp_benchmark_received_verification.json"
        ).read_text()
    )
    assert verified["status"] == "independent_gcp_two_arm_readback_passed"
    assert core.sha(received.read_bytes()) == verified["result_zip_sha256"]
    out = ROOT / "outputs/gcp_resume_rehearsal"
    out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out) as directory:
        work = Path(directory).resolve()
        assert work.is_relative_to(out.resolve())
        frozen.unpack(ROOT / "outputs/cloud_summer/l2_summer_B_bundle.zip", work / "native")
        science = frozen.load_summer(work / "native")
        manifest, manifest_sha = science.manifest_read()
        pair = manifest["pairs"][0]
        names = {f"{pair['stem']}_{suffix}" for suffix in (*science.SUFFIXES, "checkpoint.json")}
        payload = work / "pair.zip"
        with (
            zipfile.ZipFile(received) as outer,
            zipfile.ZipFile(io.BytesIO(outer.read("workers_1.zip"))) as arm,
            zipfile.ZipFile(payload, "w", compression=zipfile.ZIP_DEFLATED) as dst,
        ):
            for name in sorted(names):
                dst.writestr(name, arm.read(name))
        checks = []

        def scientific_check(path):
            with tempfile.TemporaryDirectory(dir=work) as fresh:
                target = Path(fresh) / "restored"
                assert not target.exists()
                science.restore_pair(path, pair, manifest_sha, target)
                assert science.checkpoint_read(pair, target, manifest_sha) is not None
            checks.append(True)

        backend = core.RehearsalFileStore(work / "separate_store")
        worker_sha = core.sha((ROOT / "scripts/cloud/verified_job_store.py").read_bytes())
        job = core.VerifiedJobStore(backend, manifest_sha, worker_sha, 20_000_000)
        create = backend.create

        def interrupted(key, data):
            if key.endswith("completed.json"):
                raise OSError("Injected interruption before completion")
            return create(key, data)

        backend.create = interrupted
        interrupted_once = False
        try:
            job.save(pair["sample_id"], payload, names, scientific_check)
        except OSError as error:
            assert str(error) == "Injected interruption before completion"
            interrupted_once = True
        assert interrupted_once
        assert job.restore(pair["sample_id"], names, scientific_check) is None
        backend.create = create
        restarted = core.VerifiedJobStore(backend, manifest_sha, worker_sha, 20_000_000)
        saved = restarted.save(pair["sample_id"], payload, names, scientific_check)
        assert restarted.restore(pair["sample_id"], names, scientific_check) == saved
        assert core.sha(received.read_bytes()) == verified["result_zip_sha256"]
        report = {
            "status": "local_received_pair_resume_rehearsal_passed",
            "sample_id": pair["sample_id"],
            "payload_bytes": saved["payload_bytes"],
            "payload_sha256": saved["payload_sha256"],
            "scientific_readbacks": len(checks),
            "interruption_before_marker_injected": True,
            "uncommitted_not_reused": True,
            "fresh_restore_directories": True,
            "received_zip_unchanged": True,
            "negative_label_permitted": False,
            "raw_reprocessed": False,
            "filesystem_only": True,
            "off_vm_persistence_proven": False,
            "production_launcher_ready": False,
        }
        (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    rehearse()
