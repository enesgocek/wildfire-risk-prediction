"""Scoped UTC parsing for frozen vegetation functions; original products remain immutable."""

import contextlib
import hashlib
import importlib
import importlib.util
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = "vegetation_scoped_utc_iso8601_ns_v1"
BASE = {
    "scripts/landcover/prepare_vegetation_month.py": (
        "aa675d60aa380281ad4b778a4d9e0718710c19c7c1a189804f53f140808fd4fa"
    ),
    "scripts/landcover/prepare_vegetation_full_grid.py": (
        "7ab26bd0b3910943fd5643113f56273ae35fd19e7ba02093d068c0b2c04e4952"
    ),
    "scripts/quality/verify_vegetation_month.py": (
        "226b378fce4e2ea2be24b322f11c1862262ace85f2c00f6a202761dea37317a4"
    ),
    "scripts/quality/verify_vegetation_full_grid.py": (
        "3cd5c1a00ca674776d4a5e802e0128fe2f4cffb2be03eba8121a02ff21b2d94b"
    ),
    "src/wildfire_risk_prediction/vegetation.py": (
        "76dfa37176d17d988940523219d19e440f4d301265517beab99906e9e3557d71"
    ),
    "src/wildfire_risk_prediction/vegetation_series.py": (
        "9643bdb8f804484da94ead6a26fc5082697c3d87dea5c266a9ddec88600feac6"
    ),
    "data/interim/grid_aoi_parts.geojson": (
        "f589f6027d28ce1911d080763e195062dcaaf4e9567fb4072d14c454bf28a2f9"
    ),
    "scripts/landcover/prepare_vegetation_period.py": (
        "0b54605dfa389576db51304694556f3ce5e62b67b6ac83f76e5ca160b0746a1e"
    ),
    "scripts/landcover/run_vegetation_training.py": (
        "d092e8ef9608f9a9f9b5a25649b0183ca419a21bfd8f2d1e618536adb74f1cf8"
    ),
    "uv.lock": ("4297e6edaa8ba1c0a05000e9a787bfde1bb51f2d71a931bb5c1f825b9671d9b5"),
    "pyproject.toml": ("aaad1dd293730e9bdcd6b079051c565eb5326d5644ee3ef5126c7577a5773593"),
}
UTC_ISO = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?(?:Z|\+00:00)")


def require(ok, label):
    if not ok:
        raise ValueError(label)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def checked_base():
    for name, expected in BASE.items():
        path = ROOT / name
        require(not path.is_symlink() and sha(path) == expected, "Frozen vegetation source changed")
    return BASE.copy()


def identity():
    return {"protocol": PROTOCOL, "adapter_sha256": sha(Path(__file__))}


def missing(value):
    return (
        value is None
        or value is pd.NA
        or value is pd.NaT
        or isinstance(value, float)
        and math.isnan(value)
    )


class PandasScope:
    """Only the bound module uses this proxy; pandas itself is never patched."""

    def __init__(self, calls):
        self.calls = calls

    def __getattr__(self, name):
        return getattr(pd, name)

    def to_datetime(self, values, *args, **kwargs):
        if args or kwargs != {"utc": True} or not isinstance(values, (list, tuple, pd.Series)):
            return pd.to_datetime(values, *args, **kwargs)
        present = [v for v in values if not missing(v)]
        if present and all(isinstance(v, (pd.Timestamp, datetime)) for v in present):
            return pd.to_datetime(values, *args, **kwargs)
        require(
            all(isinstance(v, str) and UTC_ISO.fullmatch(v) for v in present),
            "Strict UTC ISO timestamps",
        )
        result = pd.to_datetime(values, utc=True, format="ISO8601", errors="raise")
        if isinstance(result, pd.Series):
            result = result.dt.as_unit("ns")
        else:
            result = result.as_unit("ns")
        require(
            sum(missing(v) for v in values) == int(result.isna().sum()),
            "Timestamp missingness changed",
        )
        self.calls.append(
            {
                "field": values.name if isinstance(values, pd.Series) else "raw_scene_times",
                "rows": len(values),
                "missing": int(result.isna().sum()),
            }
        )
        return result


@contextlib.contextmanager
def scoped(module, calls):
    original = module.pd
    require(original is pd, "Unexpected module pandas namespace")
    module.pd = PandasScope(calls)
    try:
        yield module
    finally:
        module.pd = original


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_metadata(path):
    if path.exists():
        value = json.loads(path.read_text())
        if "datetime_parser_adapter" in value:
            require(
                value["datetime_parser_adapter"] == identity(), "Stored execution adapter changed"
            )


class ScopedLoader:
    def __init__(self, original, stack, calls):
        self.original, self.stack, self.calls = original, stack, calls

    def __getattr__(self, name):
        return getattr(self.original, name)

    def create_module(self, spec):
        return self.original.create_module(spec)

    def exec_module(self, module):
        self.original.exec_module(module)
        self.stack.enter_context(scoped(module, self.calls))
        original_verify = module.verify

        def verify(directory):
            check_metadata(directory / "manifest.json")
            return original_verify(directory)

        module.verify = verify


class ScopedUtil:
    def __init__(self, stack, calls):
        self.stack, self.calls = stack, calls

    def __getattr__(self, name):
        return getattr(importlib.util, name)

    def spec_from_file_location(self, name, path):
        require(
            Path(path).resolve() == ROOT / "scripts/quality/verify_vegetation_full_grid.py",
            "Scoped verifier import",
        )
        spec = importlib.util.spec_from_file_location(name, path)
        spec.loader = ScopedLoader(spec.loader, self.stack, self.calls)
        return spec


def entry(task, arguments):
    checked_base()
    require(task in {"prepare", "verify"}, "Vegetation task")
    calls = []
    module = load(
        "iso_month_entry",
        ROOT
        / (
            "scripts/landcover/prepare_vegetation_month.py"
            if task == "prepare"
            else "scripts/quality/verify_vegetation_month.py"
        ),
    )
    import wildfire_risk_prediction.vegetation as vegetation

    previous_argv = sys.argv
    with contextlib.ExitStack() as stack:
        stack.enter_context(scoped(vegetation, calls))
        stack.enter_context(scoped(module, calls))
        if task == "prepare":
            original_load = module.load_module

            def adapted_load(name, path):
                require(
                    Path(path).resolve().relative_to(ROOT).as_posix() in BASE,
                    "Prepared child module",
                )
                child = original_load(name, path)
                stack.enter_context(scoped(child, calls))
                if hasattr(child, "save"):
                    original_save = child.save

                    def save(path, value):
                        if path.name == "manifest.json":
                            require(not path.exists(), "Existing manifest retained")
                            value = {**value, "datetime_parser_adapter": identity()}
                        original_save(path, value)

                    child.save = save
                else:
                    original_verify = child.verify

                    def verify(directory):
                        check_metadata(directory / "manifest.json")
                        return original_verify(directory)

                    child.verify = verify
                return child

            module.load_module = adapted_load
        else:
            from types import SimpleNamespace

            module.importlib = SimpleNamespace(util=ScopedUtil(stack, calls))
            original_write = module.write_report

            def write(path, report):
                original_write(
                    path,
                    {
                        **report,
                        "datetime_parser_adapter": identity(),
                        "datetime_parser_calls": calls.copy(),
                    },
                )

            module.write_report = write
        try:
            sys.argv = ["vegetation_iso_entry", *arguments]
            module.main()
        finally:
            sys.argv = previous_argv
    checked_base()


def prove(output):
    checked_base()
    target = ROOT / "data/interim/vegetation/full_grid_v1/2019-03-22_b64"
    manifest_path = target / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    paths = [manifest_path, ROOT / manifest["table"], *[ROOT / n for n in manifest["raw_sha256"]]]
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    failed, total = [], 0
    for name, checksum in manifest["raw_sha256"].items():
        path = ROOT / name
        require(sha(path) == checksum, "Retained raw hash")
        raw = json.loads(path.read_text())
        values = raw["scene_acquisition_utc"]
        total += len(values)
        parsed = PandasScope([]).to_datetime(values, utc=True)
        scalar = pd.DatetimeIndex([pd.Timestamp(v) for v in values]).as_unit("ns")
        require(parsed.equals(scalar), "ISO/scalar timestamps differ")
        try:
            pd.to_datetime(values, utc=True)
        except ValueError:
            failed.append(path.name)
    checker = load("proof_full_checker", ROOT / "scripts/quality/verify_vegetation_full_grid.py")
    try:
        checker.verify(target)
    except ValueError as error:
        import traceback

        origin = [
            (Path(t.filename).name, t.lineno, t.name)
            for t in traceback.extract_tb(error.__traceback__)
        ]
        require(
            any(n == "verify_vegetation_full_grid.py" and fn == "verify" for n, _, fn in origin),
            "Original replay origin",
        )
    else:
        raise ValueError("Original mixed-format failure not reproduced")
    calls = []
    with scoped(checker, calls):
        checked = checker.verify(target)
    require(
        checker.pd is pd and pd.to_datetime.__module__.startswith("pandas"),
        "Parser namespace restored",
    )
    require(
        before == {p.relative_to(ROOT).as_posix(): sha(p) for p in paths},
        "Proof modified retained data",
    )
    result = {
        "protocol": PROTOCOL,
        **identity(),
        "base_source_sha256": checked_base(),
        "original_failure_reproduced": True,
        "default_failed_batches": failed,
        "scene_timestamp_rows": total,
        "strict_iso_equals_scalar": True,
        "snapshot_readback": checked,
        "input_sha256": before,
        "parser_namespace_restored": True,
        "network_requests": 0,
        "production_writes": 0,
    }
    require(not output.exists(), "Proof report retained")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return result
