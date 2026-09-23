#!/usr/bin/env python3
"""Stream the captioned demo PNGs at one frame per second for video encoding."""

from io import BytesIO
from pathlib import Path
import sys

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DURATIONS = (15, 23, 27, 27, 33, 23, 21, 11)  # Total: 180 seconds.


def main() -> int:
    if sum(DURATIONS) != 180:
        raise ValueError("demo durations must total 180 seconds")
    output = sys.stdout.buffer
    for index, duration in enumerate(DURATIONS, 1):
        buffer = BytesIO()
        with Image.open(ROOT / "work" / "demo-frames" / f"slide-{index:02d}.png") as image:
            image.save(buffer, format="JPEG", quality=94, optimize=True)
        frame = buffer.getvalue()
        for _ in range(duration):
            output.write(frame)
    output.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
