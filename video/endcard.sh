#!/usr/bin/env bash
# endcard.sh — the last frame of the video: name, URL, repo, licence.
#
#   bash video/endcard.sh                                      # repo only
#   PUBLIC_URL=constancia-voice.onrender.com bash video/endcard.sh   # once it answers
#
# No scheme: the card shows a bare domain. The default is EMPTY on purpose, and an
# empty PUBLIC_URL drops the line instead of printing a placeholder: the last frame of
# the video is the worst place to publish an address that 404s, and the repo line below
# it is already a working one. Pass the hostname only after `curl .../health` answers.
#
# Renders video/endcard.html at 1280x800 with headless Chrome, so the card uses
# the project's own tokens instead of a second palette written in ffmpeg.
# Writes $VIDEO_DIR/out/endcard.png.
set -euo pipefail

VIDEO_DIR="${VIDEO_DIR:-$PWD/video}"
PUBLIC_URL="${PUBLIC_URL:-}"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
OUT="$VIDEO_DIR/out/endcard.png"

[ -x "$CHROME" ] || { echo "ERROR: Chrome not at $CHROME — set CHROME=..."; exit 1; }

mkdir -p "$VIDEO_DIR/out"
# the copy stays beside the original: the page links tokens.css by relative path.
page="$VIDEO_DIR/.endcard.rendered.html"
if [ -n "$PUBLIC_URL" ]; then
  sed "s|PUBLIC_URL|$PUBLIC_URL|" "$VIDEO_DIR/endcard.html" > "$page"
else
  sed "/PUBLIC_URL/d" "$VIDEO_DIR/endcard.html" > "$page"
fi

# --virtual-time-budget: without it the shot is taken before the Google Fonts request
# lands, and the card renders the display face in the system fallback. The title is the
# last frame of the video, so that is the one place the typeface has to be right.
"$CHROME" --headless --disable-gpu --hide-scrollbars --window-size=1280,800 \
  --virtual-time-budget=4000 --screenshot="$OUT" "file://$page" 2>/dev/null

rm -f "$page"
echo "wrote $OUT"
