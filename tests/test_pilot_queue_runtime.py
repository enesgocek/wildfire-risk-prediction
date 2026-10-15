import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SPEC = importlib.util.spec_from_file_location(
    "pilot_runtime", Path(__file__).parents[1] / "scripts/firms/run_observation_pilot_queue.py"
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


@pytest.mark.parametrize("successful", [False, True])
def test_private_login_restores_environment_and_never_persists(monkeypatch, capsys, successful):
    monkeypatch.setattr(module.sys, "stdin", SimpleNamespace(isatty=lambda: True))
    answers = iter(["test-private-user", "test-private-password"])
    monkeypatch.setattr(module.getpass, "getpass", lambda text: next(answers))
    for name in ("EARTHDATA_USERNAME", "EARTHDATA_PASSWORD", "EARTHDATA_TOKEN"):
        monkeypatch.setenv(name, "original-value")

    def login(**kwargs):
        assert kwargs == {"strategy": "environment", "persist": False}
        assert module.os.environ["EARTHDATA_USERNAME"] == "test-private-user"
        assert module.os.environ["EARTHDATA_PASSWORD"] == "test-private-password"
        assert "EARTHDATA_TOKEN" not in module.os.environ
        print("simulated sensitive auth output")
        return SimpleNamespace(
            authenticated=successful, token={"access_token": "test-private-token"}
        )

    monkeypatch.setitem(sys.modules, "earthaccess", SimpleNamespace(login=login))
    if successful:
        assert module.private_token() == "test-private-token"
    else:
        with pytest.raises(ValueError, match="Private Earthdata"):
            module.private_token()
    assert all(
        module.os.environ[n] == "original-value"
        for n in ("EARTHDATA_USERNAME", "EARTHDATA_PASSWORD", "EARTHDATA_TOKEN")
    )
    captured = capsys.readouterr()
    assert not captured.out and not captured.err


def test_noninteractive_login_stops_before_requesting_secrets(monkeypatch):
    monkeypatch.setattr(module.sys, "stdin", SimpleNamespace(isatty=lambda: False))
    monkeypatch.setattr(module.getpass, "getpass", lambda _: pytest.fail("Must not ask here"))
    with pytest.raises(ValueError, match="interactive terminal"):
        module.private_token()


def test_time_limit_preserves_outputs_and_reports_lock_review(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "RUNS", tmp_path / "attempts")
    monkeypatch.setattr(module, "load_queue", lambda _: {"hard_runtime_seconds": 14400})
    plan = tmp_path / "queue_plan.json"
    plan.write_text("{}")

    def expired(command, **kwargs):
        assert kwargs["timeout"] == 14400
        assert "EARTHDATA_TOKEN" not in kwargs["env"]
        assert "--allow-transfer" not in command
        kwargs["stdout"].write("retained progress\n")
        raise module.subprocess.TimeoutExpired(command, 14400)

    monkeypatch.setattr(module.subprocess, "run", expired)
    assert module.run(plan, False) == 1
    out = next((tmp_path / "attempts").iterdir())
    receipt = json.loads((out / "launcher_receipt.json").read_text())
    assert receipt["status"] == "hard_timeout_outputs_and_writer_lock_retained"
    assert not receipt["credentials_written"]
    assert (out / "worker.log").read_text() == "retained progress\n"
    assert not (out / "completion_readback.json").exists()


def test_zero_exit_without_receipt_cannot_be_reported_as_completed(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "RUNS", tmp_path / "attempts")
    monkeypatch.setattr(module, "load_queue", lambda _: {"hard_runtime_seconds": 14400})
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0))
    plan = tmp_path / "queue_plan.json"
    plan.write_text("{}")
    with pytest.raises(FileNotFoundError):
        module.run(plan, False)
    out = next((tmp_path / "attempts").iterdir())
    receipt = json.loads((out / "launcher_receipt.json").read_text())
    assert receipt["status"] == "child_failed_outputs_retained"
