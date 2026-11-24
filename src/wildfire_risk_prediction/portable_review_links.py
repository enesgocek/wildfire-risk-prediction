"""Validate local navigation without opening a browser or following network URLs."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if "id" in values:
            self.ids.add(values["id"])
        if tag == "base":
            raise ValueError("A portable review must not override its base location")
        for key in ("href", "src"):
            if values.get(key):
                self.references.append(values[key])


def local_target(package, owner, reference):
    parsed = urlsplit(reference)
    if parsed.scheme or parsed.netloc or parsed.query or "\\" in reference:
        raise ValueError("Only relative local review links")
    root = Path(package).resolve()
    source = (root / owner).resolve()
    target = (source.parent / unquote(parsed.path)).resolve() if parsed.path else source
    if not target.is_relative_to(root):
        raise ValueError("Review link leaves package")
    if not target.is_file():
        raise ValueError("Missing packaged review file: " + reference)
    if parsed.fragment and target.suffix == ".html":
        document = References()
        document.feed(target.read_text(encoding="utf-8"))
        if unquote(parsed.fragment) not in document.ids:
            raise ValueError("Missing packaged HTML section")
    return target


def verify_html(package, relative):
    document = References()
    document.feed((Path(package) / relative).read_text(encoding="utf-8"))
    for reference in document.references:
        local_target(package, relative, reference)
    return len(document.references)
