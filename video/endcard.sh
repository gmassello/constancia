#!/usr/bin/env bash
# endcard.sh — the last frame of the video: name, URL, repo, licence.
#
#   PUBLIC_URL=constancia-voice.onrender.com bash video/endcard.sh
#
# No scheme: the card shows a bare domain. The default is the hostname
# render.yaml claims; `constancia` itself belongs to an unrelated app.
#
# Renders video/endcard.html at 1280x800 with headless Chrome, so the card uses
# the project's own tokens instead of a second palette written in ffmpeg.
# Writes $VIDEO_DIR/out/endcard.png.
set -euo pipefail

VIDEO_DIR="${VIDEO_DIR:-$PWD/video}"
PUBLIC_URL="${PUBLIC_URL:-constancia-voice.onrender.com}"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
OUT="$VIDEO_DIR/out/endcard.png"

[ -x "$CHROME" ] || { echo "ERROR: Chrome not at $CHROME — set CHROME=..."; exit 1; }

mkdir -p "$VIDEO_DIR/out"
# the copy stays beside the original: the page links tokens.css by relative path.
page="$VIDEO_DIR/.endcard.rendered.html"
sed "s|PUBLIC_URL|$PUBLIC_URL|" "$VIDEO_DIR/endcard.html" > "$page"

"$CHROME" --headless --disable-gpu --hide-scrollbars --window-size=1280,800 \
  --screenshot="$OUT" "file://$page" 2>/dev/null

rm -f "$page"
echo "wrote $OUT"
