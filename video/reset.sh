#!/usr/bin/env bash
# reset.sh — put the demo back where a take expects it, or just report.
#
#   bash video/reset.sh --check    reports, changes nothing. Run it before every take.
#   bash video/reset.sh            makes the state be this, then reports.
#
# Either way it ends by censing what fails in silence on camera: a dead
# Gemini or AssemblyAI quota, and a PUBLIC_BASE_URL that is not the ngrok
# that is running. Gemini costs one request; AssemblyAI opens the streaming
# socket instead of spending a transcript; neither prints a key.
#
# Every invariant is read through the API, so it works the same against the
# in-memory seed and against Postgres.
#
# Env:  BASE   the running service   (default: http://localhost:8001)
set -uo pipefail

BASE="${BASE:-http://localhost:8001}"
PATIENT="8c9d0e1f-2a3b-4c5d-6e7f-8091a2b3c4d5"
CHECK_ONLY=0
[ "${1:-}" = "--check" ] && CHECK_ONLY=1

fails=0
green() { printf '  \033[32mok\033[0m    %s\n' "$1"; }
red()   { printf '  \033[31mFAIL\033[0m  %s\n' "$1"; fails=$((fails + 1)); }

get() { curl -sf --max-time 5 "$BASE$1"; }

health=$(get /health) || { echo "no service at $BASE — run 'make dev' first"; exit 2; }
store=$(printf '%s' "$health" | python3 -c 'import json,sys;print(json.load(sys.stdin)["store"])')

if [ "$CHECK_ONLY" -eq 0 ]; then
  echo "resetting ($store)"
  if [ "$store" = "postgres" ]; then
    uv run python scripts/seed.py || exit 2
  else
    curl -sf -X POST "$BASE/reset" >/dev/null || exit 2
  fi
  health=$(get /health)
fi

echo "demo state at $BASE"

printf '%s' "$health" | python3 -c '
import json, sys
h = json.load(sys.stdin)
print("STORE", h["store"])
print("CALLS", h["calls"])
print("LIVE", h["live"])
print("DIALABLE", h["dialable"])
' > /tmp/constancia-health.$$

calls_registered=$(awk '/^CALLS/{print $2}' /tmp/constancia-health.$$)
live=$(awk '/^LIVE/{print $2}' /tmp/constancia-health.$$)
dialable=$(awk '/^DIALABLE/{print $2}' /tmp/constancia-health.$$)
rm -f /tmp/constancia-health.$$

green "service answers, store is $store"

if [ "$calls_registered" = "0" ]; then
  green "no calls registered from a previous take"
else
  red "$calls_registered call(s) still registered in the process — reset, or restart the service"
fi

patients=$(get /patients)
name=$(printf '%s' "$patients" | python3 -c '
import json, sys
rows = json.load(sys.stdin)
print(rows[0]["name"] if len(rows) == 1 else f"{len(rows)} patients")
')
if [ "$name" = "Ana" ]; then
  green "one patient, Ana"
else
  red "expected exactly one patient named Ana, found: $name"
fi

chain=$(get "/patients/$PATIENT/chain")
report=$(printf '%s' "$chain" | python3 -c '
import json, sys
facts = json.load(sys.stdin)
want = ["right knee", "home exercises", "daily exercises", "stiffness", "bathroom fall"]
got = [f["term"] for f in facts]
retired = [f["term"] for f in facts if f["superseded"]]
print("COUNT", len(facts))
print("TERMS", "|".join(sorted(got)))
print("WANT", "|".join(sorted(want)))
print("RETIRED", "|".join(retired) or "-")
')
count=$(awk '/^COUNT/{print $2}' <<<"$report")
got=$(awk '/^TERMS/{$1=""; print substr($0,2)}' <<<"$report")
want=$(awk '/^WANT/{$1=""; print substr($0,2)}' <<<"$report")
retired=$(awk '/^RETIRED/{$1=""; print substr($0,2)}' <<<"$report")

if [ "$got" = "$want" ]; then
  green "$count week-1 facts, exactly the seeded ones"
else
  red "the file is not the seeded one: $got"
fi

if [ "$retired" = "-" ]; then
  green "nothing retired yet — the 7/10 is still current"
else
  red "already superseded by a previous take: $retired"
fi

rows=$(get "/patients/$PATIENT/calls" | python3 -c 'import json,sys;print(len(json.load(sys.stdin)))')
if [ "$rows" = "1" ]; then
  green "one call on file, the seeded week-1 one"
else
  red "$rows calls on file — a previous take left rows behind"
fi

if [ "$live" = "True" ]; then
  green "credentials loaded: the live path is available"
else
  red "no credentials: beats 3, 4 and 5 are live (docs/video-script.md)"
fi

if [ "$dialable" = "True" ]; then
  green "the service has a demo number: the panel offers the live buttons (number not printed)"
else
  red "no demo number on the running service — the panel hides the live buttons, and beats 3, 4 and 5 need them"
fi

envval() { sed -n "s/^$1=//p" .env 2>/dev/null | head -1; }

gemini_key=$(envval GEMINI_API_KEY)
gemini_model=$(envval GEMINI_MODEL)
: "${gemini_model:=gemini-3.8-flash}"
if [ -z "$gemini_key" ]; then
  red "GEMINI_API_KEY is empty in .env — every reply falls back to the scripted LLM"
else
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 \
    -X POST "https://generativelanguage.googleapis.com/v1beta/models/$gemini_model:generateContent" \
    -H "x-goog-api-key: $gemini_key" -H 'content-type: application/json' \
    -d '{"contents":[{"parts":[{"text":"hi"}]}],"generationConfig":{"maxOutputTokens":1}}')
  case "$code" in
    200) green "Gemini quota alive ($gemini_model answered 200)" ;;
    429) red "Gemini answered 429 — the daily quota is gone. On camera this is a generic agent error, not a visible rate limit" ;;
    *)   red "Gemini answered $code — not a quota failure, but every agent turn dies on camera just the same" ;;
  esac
fi

aai_key=$(envval ASSEMBLYAI_API_KEY)
if [ -z "$aai_key" ]; then
  red "ASSEMBLYAI_API_KEY is empty in .env — nothing transcribes the call"
else
  if out=$(uv run python scripts/smoke_stt.py 2>&1); then
    green "AssemblyAI streaming socket opens and greets (the socket the call uses)"
  else
    red "AssemblyAI streaming socket did not open — nothing transcribes the call: $(printf '%s' "$out" | tail -1)"
  fi
fi

configured=$(envval PUBLIC_BASE_URL)
running=$(curl -sf --max-time 3 http://localhost:4040/api/tunnels 2>/dev/null | python3 -c '
import json, sys
tunnels = json.load(sys.stdin)["tunnels"]
https = [t["public_url"] for t in tunnels if t["public_url"].startswith("https")]
print(https[0] if https else "")
' 2>/dev/null)
if [ -z "$running" ]; then
  red "no ngrok tunnel on localhost:4040 — every Twilio webhook 403s in twilio_form() and the phone rings, then goes silent"
elif [ "$running" = "$configured" ]; then
  green "PUBLIC_BASE_URL is the tunnel that is running"
else
  red "PUBLIC_BASE_URL is stale: the service expects $configured, ngrok is serving $running (403 in twilio_form())"
fi

echo

if [ "$fails" -gt 0 ]; then
  echo "$fails invariant(s) red — do not record. Run: bash video/reset.sh"
  exit 1
fi
echo "all green."
exit 0
