#!/usr/bin/env bash
# coldopen.sh — the fourteen seconds in front of the finished demo.
#
#   VIDEO_DIR=$PWD/video bash video/coldopen.sh
#
# Writes $VIDEO_DIR/out/demo-coldopen.mp4 and demo-coldopen.en.srt. It never
# touches out/demo.mp4: the verified deliverable stays on disk, and the way back
# from a cold open nobody likes is to not use the new file.
#
# The synthetic pipeline knows nothing about a cold open — build-video.sh,
# build-audio.sh and fit-to-audio.py never mention `hook`, only the own-voice
# scripts do. So nothing puts the audio in front of the narration, nothing shifts
# the captions, and nothing counts these seconds against the 300 s cap. All three
# happen here instead. And build-audio.sh must never run again: it does
# `rm -rf out`, which is where narration.wav, demo.mp4 and the hook all live.
#
# Every source it needs is in git, this script included, so the cold open rebuilds
# from a clean clone. Shot 1 is a frame of a real incoming call, mirrored from the
# phone with Vysor and captured with `screencapture -o -l <CGWindowID>`: a still and
# not the recording, because an iOS lock screen does not move while it rings, and
# `zoompan` emits its frames per INPUT frame — over a clip the push would have
# frozen the shot on its first frame. Re-shooting it is in docs/video-script.md
# § *0 · the phone ringing*.
set -euo pipefail

VIDEO_DIR="${VIDEO_DIR:-$PWD/video}"
ROOT="$(cd "$VIDEO_DIR/.." && pwd)"
OUT="$VIDEO_DIR/out"
SKILL="${SKILL:-$HOME/.claude/skills/personal-record-video}"
# the default brew ffmpeg 8 has no drawtext, and hook.py prepends this for itself only
export PATH="/opt/homebrew/opt/ffmpeg@7/bin:$PATH"

RING_LEVEL="${RING_LEVEL:-0.30}"
LOUDNESS="${LOUDNESS:--17.0}"
PEAK="${PEAK:--2.0}"
CAP="${CAP:-300}"

DEMO="$OUT/demo.mp4"
[ -f "$DEMO" ] || { echo "ERROR: $DEMO not found — build the demo first"; exit 1; }
command -v ffmpeg >/dev/null || { echo "ERROR: no ffmpeg on PATH"; exit 1; }

dur() { ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$1"; }

echo "==> stills"
ffmpeg -y -v error -i "$ROOT/docs/assets/memory-chain.png" \
  -vf "crop=1200:500:0:0,scale=1920:800:flags=lanczos,pad=1920:1080:0:30:white" \
  "$VIDEO_DIR/shots/hook-memory.png"
ffmpeg -y -v error -i "$VIDEO_DIR/shots/escalated.png" \
  -vf "scale=1920:-1:flags=lanczos,pad=1920:1080:0:120:black" \
  "$VIDEO_DIR/shots/hook-escalated.png"

echo "==> hook"
# hook.py caches against out/hook.plan, so a changed image with an unchanged
# hook.json would silently return the previous render.
rm -f "$OUT/hook.plan"
VIDEO_DIR="$VIDEO_DIR" python3 "$SKILL/scripts/hook.py"

TOTAL=$(dur "$OUT/hook.mov")

echo "==> ring"
# 440 + 480 Hz is the North American ringback: a spec, not a work, so it needs no
# licence and no asset. One 2 s tone and the silence after it — the cadence is
# 2 on / 4 off, and the cut lands in the gap, which is what "nobody answered" sounds like.
ffmpeg -y -v error \
  -f lavfi -i "sine=frequency=440:duration=2:sample_rate=48000" \
  -f lavfi -i "sine=frequency=480:duration=2:sample_rate=48000" \
  -filter_complex "[0][1]amix=inputs=2:normalize=0,volume=$RING_LEVEL,\
afade=t=in:st=0:d=0.03,afade=t=out:st=1.9:d=0.1,adelay=200,apad=whole_dur=$TOTAL" \
  -c:a pcm_f32le -ar 48000 -ac 1 "$OUT/hook/ring.wav"

# Mixed over the PRE-master mix hook.py leaves behind, not over hook.wav: mixing
# over the mastered file would put a second alimiter pass on top of the first.
ffmpeg -y -v error -i "$OUT/hook/mix.wav" -i "$OUT/hook/ring.wav" \
  -filter_complex "[0][1]amix=inputs=2:normalize=0,atrim=0:$TOTAL" \
  -c:a pcm_f32le -ar 48000 -ac 1 "$OUT/hook/mix-ring.wav"

MEASURED=$(ffmpeg -hide_banner -nostats -i "$OUT/hook/mix-ring.wav" \
  -af ebur128=peak=true -f null - 2>&1 | awk '/^ *I: /{v=$2} END{print v}')
read -r GAIN LIMIT <<EOF
$(python3 -c "print(f'{$LOUDNESS - ($MEASURED):.2f} {10 ** (($PEAK - 1.0) / 20):.4f}')")
EOF
echo "    mix $MEASURED LUFS -> ${GAIN} dB to reach $LOUDNESS"

# One measured gain, never loudnorm: loudnorm reaches the same number by
# compressing, and the compression is what flattens the hits.
ffmpeg -y -v error -i "$OUT/hook/mix-ring.wav" \
  -af "volume=${GAIN}dB,alimiter=limit=${LIMIT}:level=false:attack=4:release=60" \
  -c:a pcm_s16le -ar 48000 -ac 1 "$OUT/hook.wav"

echo "==> encode"
# Matched to demo.mp4 as ffprobe reports it, so the join below copies both halves.
ffmpeg -y -v error -i "$OUT/hook.mov" -i "$OUT/hook.wav" \
  -c:v libx264 -preset slow -crf 18 -profile:v high -level 4.0 -pix_fmt yuv420p -r 30 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
  -c:a aac -b:a 128k -ar 48000 -ac 1 -shortest "$OUT/hook.mp4"

echo "==> join"
# Through MPEG-TS rather than the concat demuxer: in Annex-B the SPS/PPS travels
# in band with every keyframe, so the two halves keep their own encoder parameters.
# The demuxer writes ONE avcC, taken from the first input, and the 270 s that follow
# would be decoded with the hook's.
for f in hook demo; do
  ffmpeg -y -v error -i "$OUT/$f.mp4" -c copy -bsf:v h264_mp4toannexb -f mpegts "$OUT/$f.ts"
done
ffmpeg -y -v error -i "concat:$OUT/hook.ts|$OUT/demo.ts" -c copy \
  -movflags +faststart "$OUT/demo-coldopen.mp4"
rm -f "$OUT/hook.ts" "$OUT/demo.ts"

echo "==> captions"
LEAD="$TOTAL" python3 - "$OUT/demo.en.srt" "$OUT/demo-coldopen.en.srt" <<'PY'
import os, re, sys
lead = float(os.environ["LEAD"])


def shift(stamp):
    h, m, rest = stamp.split(":")
    s, ms = rest.split(",")
    t = int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000 + lead
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{round(s % 1 * 1000):03d}"


src, dest = sys.argv[1], sys.argv[2]
cue = re.compile(r"^(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\s*$")
out, n = [], 0
for line in open(src, encoding="utf-8"):
    hit = cue.match(line)
    if hit:
        n += 1
        out.append(f"{shift(hit[1])} --> {shift(hit[2])}\n")
    else:
        out.append(line)
open(dest, "w", encoding="utf-8").writelines(out)
print(f"    {n} cues shifted +{lead:.1f} s")
PY

FINAL=$(dur "$OUT/demo-coldopen.mp4")
python3 -c "
f=$FINAL
print(f'\n  cold open  {$TOTAL:.1f} s   +   demo  $(dur "$DEMO") s')
print(f'  demo-coldopen.mp4  {f:.3f} s  =  {int(f//60)}:{f%60:04.1f}   cap $CAP s   {\"OK\" if f <= $CAP else \"OVER\"}')
print(f'  -> out/demo-coldopen.mp4, out/demo-coldopen.en.srt\n')
"
