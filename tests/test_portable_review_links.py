import shutil

import pytest

from wildfire_risk_prediction.portable_review_links import local_target, verify_html


def sample(root):
    (root / "interface").mkdir(parents=True)
    (root / "documents").mkdir()
    (root / "documents/card.md").write_text("Research card", encoding="utf-8")
    (root / "interface/data.js").write_text("const data = [];", encoding="utf-8")
    (root / "interface/inceleme.html").write_text(
        '<h1 id="scope">Scope</h1><a href="../documents/card.md">Card</a>'
        '<a href="#scope">Scope</a><script src="data.js"></script>',
        encoding="utf-8",
    )


def test_linked_review_remains_self_contained_after_relocation(tmp_path):
    sample(tmp_path / "original")
    relocated = tmp_path / "different" / "portable"
    shutil.copytree(tmp_path / "original", relocated)
    assert verify_html(relocated, "interface/inceleme.html") == 3


@pytest.mark.parametrize(
    "reference",
    [
        "https://example.com/a",
        "//example.com/a",
        "../../../a",
        "%2e%2e/%2e%2e/a",
        "C:/data/a",
        "../documents/missing.md",
    ],
)
def test_external_escaped_and_missing_targets_are_rejected(tmp_path, reference):
    sample(tmp_path)
    with pytest.raises(ValueError):
        local_target(tmp_path, "interface/inceleme.html", reference)


def test_fragment_must_resolve_to_a_real_html_section(tmp_path):
    sample(tmp_path)
    with pytest.raises(ValueError, match="HTML section"):
        local_target(tmp_path, "interface/inceleme.html", "#missing")
