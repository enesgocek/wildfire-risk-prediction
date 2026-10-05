"""Protect fixed cloud pilot identity and stop on download/reference mismatches."""

import ast
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SPEC = importlib.util.spec_from_file_location(
    "cloud_pilot", Path(__file__).resolve().parents[1] / "scripts/cloud/run_l2_pilot.py"
)
pilot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pilot)


def test_bundle_source_change_stops_execution(tmp_path):
    (tmp_path / "pilot").mkdir()
    source = tmp_path / "code.py"
    source.write_bytes(b"reference")
    manifest = {
        "sample_id": "SNPP:2019013.0100",
        "sources": [{}, {}],
        "bundle_files": {"code.py": hashlib.sha256(b"reference").hexdigest()},
    }
    (tmp_path / "pilot/manifest.json").write_text(json.dumps(manifest))
    assert pilot.verify_bundle(tmp_path) == manifest
    source.write_bytes(b"changed")
    with pytest.raises(ValueError, match="Bundle changed"):
        pilot.verify_bundle(tmp_path)


def test_pilot_refuses_other_training_dates(tmp_path):
    (tmp_path / "pilot").mkdir()
    (tmp_path / "pilot/manifest.json").write_text(json.dumps({"sample_id": "SNPP:2020001.0100"}))
    with pytest.raises(ValueError, match="fixed training pilot"):
        pilot.verify_bundle(tmp_path)


@pytest.mark.parametrize(
    "case", ["wrong_host", "existing_changed", "wrong_payload", "valid", "valid_geolocation"]
)
@pytest.mark.parametrize("strategy", ["interactive", "environment"])
def test_download_integrity_and_no_replacement(monkeypatch, tmp_path, case, strategy):
    content = b"native-reference"
    source = {
        "url": "https://data.lpdaac.earthdatacloud.nasa.gov/sample.nc",
        "filename": "sample.nc",
        "bytes": len(content),
        "provider": "LPCLOUD",
        "sha256": hashlib.sha256(content).hexdigest(),
    }
    if case == "valid_geolocation":
        source["url"] = "https://data.laadsdaac.earthdatacloud.nasa.gov/sample.nc"
        source["provider"] = "LAADS"
    if case == "wrong_host":
        source["url"] = "https://example.org/sample.nc"
    if case == "existing_changed":
        (tmp_path / "sample.nc").write_bytes(b"changed")
    calls = []

    def download(urls, **kwargs):
        calls.append(urls)
        (tmp_path / "sample.nc").write_bytes(b"bad" if case == "wrong_payload" else content)

    def login(**kwargs):
        assert kwargs == {"strategy": strategy, "persist": False}
        return SimpleNamespace(authenticated=True)

    monkeypatch.setitem(sys.modules, "earthaccess", SimpleNamespace(login=login, download=download))
    if case in {"valid", "valid_geolocation"}:
        assert pilot.download_sources({"sources": [source]}, tmp_path, strategy) == len(content)
    else:
        with pytest.raises(ValueError):
            pilot.download_sources({"sources": [source]}, tmp_path, strategy)
    if case in {"wrong_host", "existing_changed"}:
        assert not calls
    if case == "existing_changed":
        assert (tmp_path / "sample.nc").read_bytes() == b"changed"


def notebook_cells():
    spec = importlib.util.spec_from_file_location(
        "builder", Path(__file__).resolve().parents[1] / "scripts/cloud/build_l2_pilot_bundle.py"
    )
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    notebook = builder.make_notebook("0" * 64)
    codes = ["".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "code"]
    for code in codes:
        ast.parse(code)
    return codes


def test_colab_setup_installs_only_into_isolated_interpreter(monkeypatch):
    import subprocess
    import venv

    calls, builders = [], []

    class FakeBuilder:
        def __init__(self, **kwargs):
            builders.append(kwargs)

        def create(self, path):
            pass

    monkeypatch.setattr(venv, "EnvBuilder", FakeBuilder)
    written_requirements = []
    monkeypatch.setattr(
        Path, "write_text", lambda path, text, **kwargs: written_requirements.append(text)
    )
    monkeypatch.setattr(
        subprocess, "run", lambda command, **kwargs: calls.append((command, kwargs))
    )
    namespace = {}
    exec(notebook_cells()[0], namespace)
    assert builders == [{"with_pip": False, "system_site_packages": False}]
    install, check, preflight = calls
    assert install[0][install[0].index("--python") + 1] == str(namespace["pilot_python"])
    assert check[0] == [str(namespace["pilot_python"]), "-m", "pip", "check"]
    assert "PYTHONPATH" not in install[1]["env"]
    assert install[1]["check"] and check[1]["check"]
    assert preflight[0][:2] == [str(namespace["pilot_python"]), "-c"]
    ast.parse(preflight[0][2])
    assert "HDF5" in preflight[0][2] and preflight[1]["check"]
    assert "numpy==2.5.3" in written_requirements[0]
    assert "google-colab" not in written_requirements[0]
    assert "numba==" not in written_requirements[0]


def test_cloud_credentials_stay_out_of_command_and_clear_on_failure(monkeypatch, tmp_path):
    import getpass
    import subprocess

    answers = iter(["fixture-user", "fixture-password"])
    monkeypatch.setattr(getpass, "getpass", lambda _: next(answers))
    captured = {}

    def fail(command, **kwargs):
        assert "fixture-password" not in command
        assert "fixture-user" not in command
        captured["environment"] = kwargs["env"]
        assert kwargs["env"]["EARTHDATA_PASSWORD"] == "fixture-password"
        assert "EARTHDATA_TOKEN" not in kwargs["env"]
        raise RuntimeError("fixture failure")

    monkeypatch.setattr(subprocess, "run", fail)
    namespace = {
        "root": tmp_path,
        "pilot_python": tmp_path / "bin/python",
        "clean_env": {"EARTHDATA_TOKEN": "ignored-old-token"},
    }
    with pytest.raises(RuntimeError, match="fixture failure"):
        exec(notebook_cells()[2], namespace)
    assert "auth_env" not in namespace
    assert captured["environment"] == {}
