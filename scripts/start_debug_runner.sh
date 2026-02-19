#!/usr/bin/env bash
set -euo pipefail

# Safely run start.sh under trace with a fake heidid to inspect logic and env
# Usage: ./scripts/start_debug_runner.sh [output_log]

OUT=${1:-start_debug_run.log}
SRCDIR=$(pwd)
HEIDID_PATH="$SRCDIR/build/bin/heidid"
BACKUP_PATH="$HEIDID_PATH.real"

if [ ! -f start.sh ]; then
  echo "start.sh not found in cwd" >&2
  exit 1
fi

echo "Preparing fake heidid and running start.sh (trace) -> $OUT"

# Backup real heidid if present
if [ -f "$HEIDID_PATH" ] && [ ! -f "$BACKUP_PATH" ]; then
  mv "$HEIDID_PATH" "$BACKUP_PATH"
  chmod +x "$BACKUP_PATH" || true
fi

# Create a fake heidid to capture invocation and exit successfully
cat > "$HEIDID_PATH" <<'SH'
#!/usr/bin/env bash
echo "[FAKE-HEIDID] Invoked: $0 $@" >&2
echo "ARGS: $@" >&2
# Simulate initialization delay
sleep 1
exit 0
SH
chmod +x "$HEIDID_PATH"

# Run start.sh with tracing. Provide non-interactive answers (empty = defaults).
# Provide a dummy GitHub PAT to avoid gh prompts.
TRACEFILE="$OUT.trace"
rm -f "$OUT" "$TRACEFILE"

env -i PATH="$PATH" HOME="$HOME" SHELL="$SHELL" bash -x start.sh >"$OUT" 2>"$TRACEFILE" <<'INPUT'





INPUT

echo "--- STDOUT (start.sh) ---" > "$OUT"
cat "$OUT" >> "$OUT"
echo "--- TRACE (stderr) ---" >> "$OUT"
cat "$TRACEFILE" >> "$OUT"

# Restore original heidid
if [ -f "$BACKUP_PATH" ]; then
  mv -f "$BACKUP_PATH" "$HEIDID_PATH"
fi

echo "Debug run complete. Output: $OUT"
