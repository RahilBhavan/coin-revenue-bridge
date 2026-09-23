#!/usr/bin/env bash
# Encode the captioned demo frames into the published videos.
# Needs ffmpeg with libvpx and libx264, Python 3 with Pillow, and the frames
# from `python3 scripts/render_demo_frames.py` in work/demo-frames/.
# Writes demo.webm (180 s), social-cut.webm and social-cut.mp4 (30 s),
# all 1280x720 yuv420p at 1 fps, to outputs/final-package/ (override with OUT=dir).
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${OUT:-outputs/final-package}"
mkdir -p "$OUT"

python3 scripts/stream_demo_frames.py | ffmpeg -y -loglevel error -f image2pipe -framerate 1 -c:v mjpeg -i - \
  -c:v libvpx -b:v 0 -crf 10 -vf scale=1280:720:out_range=tv,format=yuv420p "$OUT/demo.webm"

python3 scripts/stream_social_frames.py | ffmpeg -y -loglevel error -f image2pipe -framerate 1 -c:v mjpeg -i - \
  -c:v libvpx -b:v 0 -crf 10 -vf scale=1280:720:out_range=tv,format=yuv420p "$OUT/social-cut.webm"

python3 scripts/stream_social_frames.py | ffmpeg -y -loglevel error -f image2pipe -framerate 1 -c:v mjpeg -i - \
  -c:v libx264 -profile:v high -crf 23 -vf scale=1280:720:out_range=tv,format=yuv420p -movflags +faststart "$OUT/social-cut.mp4"

echo "encoded demo.webm, social-cut.webm, social-cut.mp4 in $OUT"
