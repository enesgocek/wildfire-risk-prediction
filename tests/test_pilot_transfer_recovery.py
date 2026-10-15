import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "pilot_recovery",
    Path(__file__).parents[1] / "scripts/quality/recover_observation_pilot_transfer.py",
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_partial_is_preserved_byte_for_byte_and_only_active_name_is_released(tmp_path):
    partial = tmp_path / "source.nc.part"
    partial.write_bytes(b"partial")
    destination = tmp_path / "review" / partial.name
    result = module.quarantine_partial(
        partial, destination, {"filename": "source.nc", "bytes": 20}, tmp_path
    )
    assert not partial.exists() and destination.read_bytes() == b"partial"
    assert result["retained_bytes"] == 7 and not result["partial_accepted_as_native_source"]
    assert result["raw_files_deleted"] == 0


@pytest.mark.parametrize(
    "kind", ["wrong_name", "full_size", "empty", "existing_destination", "full_source"]
)
def test_unreviewed_or_conflicting_file_cannot_be_moved(tmp_path, kind):
    partial = tmp_path / "source.nc.part"
    partial.write_bytes(b"partial" if kind != "empty" else b"")
    destination = tmp_path / "review" / partial.name
    source = {
        "filename": "other.nc" if kind == "wrong_name" else "source.nc",
        "bytes": 7 if kind == "full_size" else 20,
    }
    if kind == "existing_destination":
        destination.parent.mkdir()
        destination.write_bytes(b"previous")
    elif kind == "full_source":
        (tmp_path / "source.nc").write_bytes(b"previous")
    with pytest.raises(ValueError):
        module.quarantine_partial(partial, destination, source, tmp_path)
    assert partial.exists()


def test_recovery_cannot_move_to_a_location_outside_project(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    partial = root / "source.nc.part"
    partial.write_bytes(b"partial")
    with pytest.raises(ValueError, match="Contained"):
        module.quarantine_partial(
            partial,
            tmp_path / "outside" / partial.name,
            {"filename": "source.nc", "bytes": 20},
            root,
        )
    assert partial.exists()
