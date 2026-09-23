#!/usr/bin/env python3
"""Copy the reviewed public case-study bundle into the Sites static directory."""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "outputs" / "public-case-study"
TARGET = ROOT / "dist"
SOCIAL_CARD = ROOT / "docs" / "social-card.png"


def main() -> int:
    if TARGET.exists():
        shutil.rmtree(TARGET)
    TARGET.mkdir()
    for source in sorted(SOURCE.iterdir()):
        if source.is_file():
            (TARGET / source.name).write_bytes(source.read_bytes())
    (TARGET / SOCIAL_CARD.name).write_bytes(SOCIAL_CARD.read_bytes())
    print(f"prepared {len(list(TARGET.iterdir()))} static files in {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
