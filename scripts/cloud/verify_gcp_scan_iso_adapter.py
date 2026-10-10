"""Offline proof of a scoped UTC parser adapter; never starts production."""

import contextlib
import hashlib
import importlib.util
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

PROBE_SHA = "308c301a837924286dcce398685ff64c2b97da64f5fd373204b6bdfef029e1b1"
SCAN_SHA = "870a6cf565f211964dca9b01aa4e790f4914f21ecae1ba83719fbd8aa8922b9b"
EVIDENCE_SHA = "528f74b8091232a8e54ed598b20d5acedec89e1ee07401eacbacb3b3c65476a5"
EVIDENCE_NAME = "gcp_v2_scan_time_probe_20261010T013345428183Z.json"
UTC_ISO = r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?(?:Z|\+00:00)"
COLUMNS = {"start_utc", "end_utc", "ev_mid_utc"}


class AdapterCheck(ValueError):
    """Only constant diagnostic labels may be displayed."""


def require(ok, label):
    if not ok:
        raise AdapterCheck(label)


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class ScanPandas:
    """A proxy for one frozen module, never a global Pandas modification."""

    def __init__(self, pandas, calls):
        self.pandas, self.calls = pandas, calls

    def __getattr__(self, name):
        return getattr(self.pandas, name)

    def to_datetime(self, values, *args, **kwargs):
        require(
            not args
            and kwargs == {"utc": True}
            and isinstance(values, self.pandas.Series)
            and values.name in COLUMNS,
            "Only frozen scan UTC conversion",
        )
        require(
            values.notna().all()
            and values.map(lambda value: isinstance(value, str)).all()
            and values.str.fullmatch(UTC_ISO).all(),
            "Strict scan UTC schema",
        )
        parsed = self.pandas.to_datetime(values, utc=True, format="ISO8601", errors="raise")
        require(parsed.array.unit == "ns", "Scan nanosecond unit")
        self.calls.append({"column": values.name, "rows": len(values)})
        return parsed


@contextlib.contextmanager
def scan_parser(timing, calls):
    import pandas as pd

    source = Path(timing.__file__).resolve()
    require(
        not source.is_symlink()
        and digest(source) == SCAN_SHA
        and timing.pd is pd
        and timing.source_scans.__name__ == "source_scans"
        and Path(timing.source_scans.__code__.co_filename).resolve() == source,
        "Pinned scan implementation",
    )
    original = timing.pd
    timing.pd = ScanPandas(pd, calls)
    try:
        yield
    finally:
        timing.pd = original
        require(digest(source) == SCAN_SHA, "Scan source unchanged")


def checked_probe(home):
    path = home / "diagnose_gcp_v2_scan_times.py"
    require(path.is_file() and not path.is_symlink() and digest(path) == PROBE_SHA, "Pinned probe")
    spec = importlib.util.spec_from_file_location("checked_scan_probe", path)
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    return probe


def verify(home, probe, snapshot):
    evidence_path = home / EVIDENCE_NAME
    require(
        evidence_path.is_file()
        and not evidence_path.is_symlink()
        and digest(evidence_path) == EVIDENCE_SHA,
        "Pinned original replay evidence",
    )
    evidence = json.loads(evidence_path.read_bytes())
    snapshot.collect(home)  # Package and failed-state checks precede all imports.
    sys.path.insert(0, str(home / "wildfire-gcp-production-package"))
    import run_gcp_production as runner

    original_science = runner.science
    calls = []
    restored = []

    def adapted_science(root):
        compact, native = original_science(root)
        timing = native.timing
        original_scans = timing.source_scans

        def adapted_scans(*args, **kwargs):
            # The context guard checks the original code object before enabling the proxy.
            timing.source_scans = original_scans
            try:
                with scan_parser(timing, calls):
                    return original_scans(*args, **kwargs)
            finally:
                timing.source_scans = original_scans
                restored.append(timing.pd is __import__("pandas"))

        timing.source_scans = adapted_scans
        return compact, native

    runner.science = adapted_science
    try:
        result = probe.run(home, snapshot)
    finally:
        runner.science = original_science
    require(
        result["input_hashes"] == evidence["input_hashes"], "Same retained source and references"
    )
    result.pop("native_code_changed", None)
    result.update(
        protocol="gcp_scan_iso_adapter_proof_v1",
        verification_script_sha256=digest(Path(__file__).resolve()),
        original_replay_sha256=EVIDENCE_SHA,
        runtime_parser_adapter_applied=True,
        frozen_source_files_changed=False,
        adapter_calls=calls,
        parser_namespace_restored=bool(restored) and all(restored),
        production_resumed=False,
    )
    replay = result.get("scan_replay", {})
    result["adapter_acceptance"] = (
        "passed_single_retained_source"
        if replay.get("status") == "passed"
        and replay.get("native_counts_match") is True
        and result["production_input_hashes_unchanged"] is True
        and result["parser_namespace_restored"]
        and len(calls) == 3
        and {call["column"] for call in calls} == COLUMNS
        and all(call["rows"] == 203 for call in calls)
        else "failed_no_production_resume"
    )
    return result


def main():
    require(
        sys.platform == "linux"
        and sys.version_info[:2] == (3, 12)
        and sys.prefix != sys.base_prefix,
        "Existing Linux Python environment",
    )
    home = Path.home()
    probe = checked_probe(home)
    snapshot = probe.helper(home)
    probe.no_network()
    import resource

    resource.setrlimit(resource.RLIMIT_AS, (6 * 2**30, 6 * 2**30))
    with snapshot.stopped_lock(home / "wildfire-gcp-production-v1"):
        with (
            open(os.devnull, "w") as quiet,
            contextlib.redirect_stdout(quiet),
            contextlib.redirect_stderr(quiet),
        ):
            report = verify(home, probe, snapshot)
        report["created_at_utc"] = datetime.now(UTC).isoformat()
        data = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False).encode()
        require(len(data) < 100000, "Proof output byte bound")
        target = home / (
            "gcp_scan_iso_adapter_proof_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + ".json"
        )
        with target.open("xb") as stream:
            stream.write(data)
    print("Adapter check:", report["adapter_acceptance"])
    print("Download:", target)
    print("Stop VM after downloading; production was not resumed")


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    os.umask(0o077)
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "GDAL_NUM_THREADS"):
        os.environ[name] = "1"
    os.environ["GDAL_PAM_ENABLED"] = "NO"
    try:
        main()
    except AdapterCheck as error:
        print("Adapter check failed:", str(error))
        raise SystemExit(1) from None
    except Exception as error:
        print("Adapter proof stopped:", type(error).__name__, "; no external text logged")
        raise SystemExit(1) from None
