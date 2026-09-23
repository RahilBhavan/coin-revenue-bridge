#!/usr/bin/env python3
"""Stream six captioned demo frames for a 30-second social cut."""

from io import BytesIO
from pathlib import Path
import sys

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SLIDES = (1, 2, 3, 5, 7, 8)


def main() -> int:
    output = sys.stdout.buffer
    for index in SLIDES:
        buffer = BytesIO()
        with Image.open(ROOT / "work" / "demo-frames" / f"slide-{index:02d}.png") as image:
            image.save(buffer, format="JPEG", quality=94, optimize=True)
        frame = buffer.getvalue()
        for _ in range(5):
            output.write(frame)
    output.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
