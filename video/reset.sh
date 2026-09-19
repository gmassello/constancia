#!/usr/bin/env bash
# reset.sh — put the demo back where a take expects it, or just report.
#
#   bash video/reset.sh --check    reports, changes nothing. Run it before every take.
#   bash video/reset.sh            makes the state be this, then reports.
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
warns=0
green() { printf '  \033[32mok\033[0m    %s\n' "$1"; }
red()   { printf '  \033[31mFAIL\033[0m  %s\n' "$1"; fails=$((fails + 1)); }
warn()  { printf '  \033[33mwarn\033[0m  %s\n' "$1"; warns=$((warns + 1)); }

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
' > /tmp/constancia-health.$$

calls_registered=$(awk '/^CALLS/{print $2}' /tmp/constancia-health.$$)
live=$(awk '/^LIVE/{print $2}' /tmp/constancia-health.$$)
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
want = ["rodilla derecha", "ejercicios en casa", "rigidez", "caída en el baño"]
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
  warn "no credentials: shoot the keyless path (docs/video-script.md)"
fi

echo
echo "  check the Gemini and AssemblyAI quotas in their consoles by hand:"
echo "  a rehearsal, a take and a verification run can exhaust a daily free tier."
echo

if [ "$fails" -gt 0 ]; then
  echo "$fails invariant(s) red — do not record. Run: bash video/reset.sh"
  exit 1
fi
[ "$warns" -gt 0 ] && echo "all green, $warns warning(s)." || echo "all green."
exit 0
