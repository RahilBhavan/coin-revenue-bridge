#!/usr/bin/env python3
"""Normalize xlsx theme names to Office and document-property authorship to the project author."""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKBOOKS = [ROOT / "outputs" / "descriptive-bridge" / "descriptive-revenue-bridge.xlsx"]
AUTHOR = b"Rahil Bhavan"
THEME_NAME = re.compile(rb'(<a:(?:theme|clrScheme|fontScheme|fmtScheme)\b[^>]*?\bname=")[^"]*"')
PROPERTY = re.compile(rb"(<(Application|Company|dc:creator|cp:lastModifiedBy)>)[^<]*(</\2>)")


def scrub(path: Path) -> bool:
    """Rewrite theme and property members in place; every other member keeps its bytes and timestamp."""
    with zipfile.ZipFile(path) as source:
        members = [(info, source.read(info)) for info in source.infolist()]
    changed = False
    cleaned = []
    for info, data in members:
        if info.filename.startswith("xl/theme/"):
            updated = THEME_NAME.sub(rb'\1Office"', data)
        elif info.filename.startswith("docProps/"):
            updated = PROPERTY.sub(rb"\1" + AUTHOR + rb"\3", data)
        else:
            updated = data
        changed |= updated != data
        data = updated
        cleaned.append((info, data))
    if not changed:
        return False
    temporary = path.with_name(path.name + ".tmp")
    with zipfile.ZipFile(temporary, "w") as target:
        for info, data in cleaned:
            target.writestr(info, data)
    temporary.replace(path)
    return True


def main() -> int:
    paths = [Path(arg) for arg in sys.argv[1:]] or DEFAULT_WORKBOOKS
    for path in paths:
        print(f"{path}: {'scrubbed' if scrub(path) else 'clean'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
