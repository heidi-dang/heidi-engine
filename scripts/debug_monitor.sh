#!/usr/bin/env bash
set -euo pipefail

# Debug monitor for Heidi runs.
# Usage: ./scripts/debug_monitor.sh [RUN_DIR] [INTERVAL_SEC] [DAEMON_LOG]
# Example: ./scripts/debug_monitor.sh ./autotrain_repos/runs/heidi 5 ./daemon_output.log

RUN_DIR="${1:-./autotrain_repos/runs/heidi}"
INTERVAL="${2:-5}"
DAEMON_LOG="${3:-./daemon_output.log}"

printf "Starting debug monitor for %s (interval=%ss).\n" "$RUN_DIR" "$INTERVAL"
printf "Press Ctrl-C to stop.\n\n"

trap 'echo; echo "Exiting monitor."; exit 0' INT TERM

while true; do
  echo "============================================================"
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  echo "-- State Summary --"
  if [ -f "$RUN_DIR/state.json" ]; then
    if command -v jq >/dev/null 2>&1; then
      jq -r '["run_id: "+(.run_id // "-"), "status: "+(.status // "-"), "stage: "+(.current_stage // "-"), ("round: "+(.current_round|tostring)+" / target_repos: "+(.target_repos|tostring)), ("counters: "+(.counters|to_entries|map("\(.key)=\(.value)" )|join(", "))), ("last_update: "+(.last_update // "-"))] | .[]' "$RUN_DIR/state.json" || cat "$RUN_DIR/state.json"
    else
      echo "(jq not found) state.json content:"; cat "$RUN_DIR/state.json"
    fi
  else
    echo "state.json not found at $RUN_DIR"
  fi

  echo "-- Recent Events (last 15 lines) --"
  if [ -f "$RUN_DIR/events.jsonl" ]; then
    tail -n 15 "$RUN_DIR/events.jsonl"
  else
    echo "events.jsonl not found"
  fi

  echo "-- Daemon Log (tail 30) --"
  if [ -f "$DAEMON_LOG" ]; then
    tail -n 30 "$DAEMON_LOG"
  else
    echo "daemon log not found at $DAEMON_LOG"
  fi

  echo "-- Relevant Processes --"
  ps aux | egrep 'run_enhanced|run_enchance|git clone|git |python3|gh copilot|gh ' | egrep -v 'egrep' || echo 'no matching processes'

  echo "-- Stopped (T) Processes --"
  ps -eo pid,ppid,stat,tty,user,time,cmd | awk '$3 ~ /T/ {print}' || true

  echo "-- Disk usage for run dir --"
  du -sh "$RUN_DIR" 2>/dev/null || true

  echo; sleep "$INTERVAL"
done
