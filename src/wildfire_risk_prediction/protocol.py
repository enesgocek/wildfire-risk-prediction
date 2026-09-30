"""Explicit final-test guard for future pipeline entry points.

This is a programming guard, not filesystem security or a finished data loader.
"""

from pathlib import Path


def split_directory(root: Path, split: str, *, allow_final_test: bool = False) -> Path:
    if split not in {"train", "validation", "final_test"}:
        raise ValueError(f"Unknown split: {split}")
    if split == "final_test" and not allow_final_test:
        raise PermissionError("Final test is sealed; explicit final-evaluation access is required.")
    return root / "data" / "processed" / split
