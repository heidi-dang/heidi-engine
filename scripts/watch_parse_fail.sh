#!/usr/bin/env bash
set -euo pipefail

# Watch events.jsonl for JSON parse failures and print saved diagnostics.
# Usage: ./scripts/watch_parse_fail.sh [run_id]

RUN_ID="${1:-heidi}"
RUN_DIR="autotrain_repos/runs/${RUN_ID}"
EVENTS="$RUN_DIR/events.jsonl"

if [ ! -f "$EVENTS" ]; then
  echo "Events file not found: $EVENTS" >&2
  exit 1
fi

echo "Watching $EVENTS for parse failures (run: $RUN_ID)"

tail -n0 -F "$EVENTS" | while read -r line; do
  msg=$(python3 - <<'PY'
import sys, json
s = sys.stdin.read()
try:
    j = json.loads(s)
    print(j.get('message',''))
except Exception:
    print(s.strip())
PY
  <<<"$line")

  if echo "$msg" | grep -qi "invalid json (parse fail)" || echo "$msg" | grep -qi "no parsable object"; then
    echo "[$(date -u +%FT%TZ)] Parse-failure event:";
    echo "$line";
    # extract diag path if present: look for 'raw: <path>' inside the message
    diag=$(echo "$msg" | sed -n "s/.*raw: \(.*\)).*/\1/p") || true
    if [ -n "$diag" ] && [ -f "$diag" ]; then
      echo "---- DIAGNOSTIC FILE: $diag ----"
      sed -n '1,500p' "$diag"
      echo "---- END DIAGNOSTIC ----"
    else
      echo "No diagnostic file found (parsed path: '$diag')"
    fi
  fi
done
