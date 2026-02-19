#!/usr/bin/env bash
set -euo pipefail

die(){ echo "ERROR: $*" >&2; exit 1; }
need_cmd(){ command -v "$1" >/dev/null 2>&1 || die "Missing command: $1"; }
timestamp(){ date -u +"%Y-%m-%dT%H:%M:%SZ"; }

# -------- tiny progress UI (no extra deps) --------
progress_bar() {
  # usage: progress_bar CURRENT TOTAL "label"
  local cur="$1" total="$2" label="${3:-}" width=28
  (( total > 0 )) || total=1
  (( cur < 0 )) && cur=0
  (( cur > total )) && cur=$total
  local pct=$(awk "BEGIN {printf \"%.1f\", ($cur / $total) * 100}")
  local filled=$(awk "BEGIN {printf \"%d\", $pct * $width / 100}")
  local empty=$(( width - filled ))
  printf "\r│ Progress: %d/%d (%s%%) │ %s" \
    "$cur" "$total" "$pct" "$label"
}

progress_done(){ printf " │ Complete\n"; }

# -------- Background Watchdog --------
start_watchdog() {
  local state_file="$1"
  local timeout_min="${HEIDI_WATCHDOG_MIN:-10}"
  local log_file="/tmp/heidi_run.log"
  local parent_pid=$$

  (
    echo "[WATCHDOG] Started (timeout=${timeout_min}m, parent=${parent_pid})" >&2
    while true; do
      sleep 60
      [[ -f "$state_file" ]] || continue

      local now; now=$(date +%s)
      local last_ts; last_ts=$(python3 -c "import json,os,datetime; f='$state_file'; d=json.load(open(f)) if os.path.exists(f) else {}; ts=d.get('last_update', ''); print(int(datetime.datetime.strptime(ts, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc).timestamp()) if ts else 0)" 2>/dev/null || echo 0)

      if (( last_ts > 0 && (now - last_ts) > (timeout_min * 60) )); then
        echo -e "\n\n[WATCHDOG] !!! NO PROGRESS FOR ${timeout_min} MINUTES !!!" >&2
        echo "[WATCHDOG] Last update was at: $(date -d "@$last_ts" -u +"%Y-%m-%dT%H:%M:%SZ")" >&2
        echo "[WATCHDOG] Dumping diagnostics..." >&2
        echo "--- State ---" >&2
        cat "$state_file" >&2
        echo "--- Active Processes ---" >&2
        ps aux | grep -E 'run_enhanced|git clone|gh copilot|python3' | grep -v grep >&2
        echo "--- Last 20 log lines ---" >&2
        [[ -f "$log_file" ]] && tail -n 20 "$log_file" >&2

        if [[ "${HEIDI_FAIL_MODE:-open}" == "closed" ]]; then
          echo "[WATCHDOG] FAIL_MODE=closed. Terminating parent $parent_pid" >&2
          kill -9 "$parent_pid" 2>/dev/null || true
          exit 1
        else
          echo "[WATCHDOG] FAIL_MODE=open. Moving on (simulated by updating last_update)..." >&2
          # Force an update so we don't trigger again immediately
          local new_ts; new_ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
          python3 - "$state_file" "$new_ts" <<'PY'
import sys, json, os, fcntl
f, ts = sys.argv[1:3]
if os.path.exists(f):
    with open(f, "r+") as j:
        try:
            fcntl.flock(j, fcntl.LOCK_EX)
            d = json.load(j)
            d["last_update"] = ts
            j.seek(0); json.dump(d, j, indent=2); j.truncate()
        except: pass
        finally:
            fcntl.flock(j, fcntl.LOCK_UN)
PY
        fi
      fi
    done
  ) &
  WATCHDOG_PID=$!
  trap 'kill $WATCHDOG_PID 2>/dev/null || true' EXIT
}

# -------- Helper: Timeout + Retries --------
# Usage: call_with_timeout_retry LABEL COMMAND...
call_with_timeout_retry() {
  local label="$1"; shift
  local max_retries="${HEIDI_MAX_RETRIES:-3}"
  local timeout_sec="${HEIDI_CALL_TIMEOUT_SEC:-60}"
  local attempt=0
  local exit_code=0

  while (( attempt < max_retries )); do
    attempt=$(( attempt + 1 ))
    if timeout "${timeout_sec}s" "$@"; then
      return 0
    else
      exit_code=$?
      if (( exit_code == 124 )); then
        echo "[$label] Timed out after ${timeout_sec}s (attempt $attempt/$max_retries)" >&2
      else
        echo "[$label] Failed with exit code $exit_code (attempt $attempt/$max_retries)" >&2
      fi
      sleep $(( attempt * 2 ))
    fi
  done

  echo "[$label] All $max_retries attempts failed." >&2
  return "$exit_code"
}

SCRIPT_DIR_INTERNAL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR_INTERNAL/.." && pwd)"

setup_proxy() {
  local p_script="$PROJECT_ROOT/proxy/get_proxy.sh"
  if [[ -x "$p_script" ]]; then
    local p_url; p_url=$("$p_script" 2>/dev/null || true)
    if [[ -n "$p_url" ]]; then
      export http_proxy="$p_url"
      export https_proxy="$p_url"
      export all_proxy="$p_url"
      export HTTP_PROXY="$p_url"
      export HTTPS_PROXY="$p_url"
      export ALL_PROXY="$p_url"
      # Ensure git uses the proxy for this operation
      export GIT_CONF_PROXY="-c http.proxy=$p_url -c https.proxy=$p_url"
      return 0
    fi
  fi
  export GIT_CONF_PROXY=""
  return 1
}
export -f setup_proxy
# GLOBAL PATHS (Initialized in main)
export rig="${RIG_NAME:-heidi}"
export autotrain_base="${AUTOTRAIN_DIR:-$HOME/heidi-training/autotrain_repos}"
export out=""

init_paths() {
  local target_n="${1:-50}"
  # Validate that target_n is a positive integer
  if ! [[ "$target_n" =~ ^[0-9]+$ ]]; then
    target_n=50
  fi
  out="$autotrain_base/runs/$rig"
  mkdir -p "$out"
  chmod 700 "$out" 2>/dev/null || true
  for b in python cpp github; do
    mkdir -p "$out/$b/raw"
    touch "$out/$b/samples.jsonl" "$out/$b/clean_samples.jsonl" "$out/$b/hashes.txt"
  done

  # Create state.json for dashboard detection
  cat <<EOF > "$out/state.json"
{
  "run_id": "$rig",
  "status": "running",
  "current_round": 1,
  "current_stage": "discovery",
  "target_repos": $(( target_n * 3 )),
  "counters": {
    "teacher_generated": 0,
    "teacher_failed": 0,
    "validated_ok": 0
  },
  "teacher_model": "${TEACHER_MODEL:-gpt-5-mini}",
  "last_update": "$(timestamp)"
}
EOF
}

log_event() {
  local stage="$1"
  local msg="$2"
  [[ -z "$out" ]] && return 0
  local ef="$out/events.jsonl"
  local sf="$out/state.json"
  local ts; ts="$(timestamp)"
  # JSON escape message
  local escaped_msg; escaped_msg=$(python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$msg")
  echo "{\"ts\": \"$ts\", \"stage\": \"$stage\", \"message\": $escaped_msg}" >> "$ef"
  
  # Update last_update in state.json so health monitor sees activity
  python3 - "$sf" "$ts" <<'PY'
import sys, json, os, fcntl
f, ts = sys.argv[1:3]
if os.path.exists(f):
    with open(f, "r+") as j:
        try:
            fcntl.flock(j, fcntl.LOCK_EX)
            d = json.load(j)
            d["last_update"] = ts
            j.seek(0); json.dump(d, j, indent=2); j.truncate()
        except: pass
        finally:
            fcntl.flock(j, fcntl.LOCK_UN)
PY
}

update_state_count() {
  local sf="$out/state.json"
  local key="${1:-teacher_generated}"
  python3 - "$sf" "$key" <<'PY'
import sys, json, os, datetime, fcntl
f, key = sys.argv[1:3]
if os.path.exists(f):
    with open(f, "r+") as j:
        try:
            fcntl.flock(j, fcntl.LOCK_EX)
            d = json.load(j)
            if "counters" not in d: d["counters"] = {}
            d["counters"][key] = d["counters"].get(key, 0) + 1
            d["last_update"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            j.seek(0); json.dump(d, j, indent=2); j.truncate()
        except Exception as e:
            sys.stderr.write(f"State update failed: {e}\n")
        finally:
            fcntl.flock(j, fcntl.LOCK_UN)
PY
}

update_state_stage() {
  local sf="$out/state.json"
  local stage="$1"
  python3 - "$sf" "$stage" <<'PY'
import sys, json, os, fcntl
f, stage = sys.argv[1:3]
if os.path.exists(f):
    with open(f, "r+") as j:
        try:
            fcntl.flock(j, fcntl.LOCK_EX)
            d = json.load(j)
            d["current_stage"] = stage
            j.seek(0); json.dump(d, j, indent=2); j.truncate()
        except: pass
        finally:
            fcntl.flock(j, fcntl.LOCK_UN)
PY
}

prompt_hidden() {
  local __var="$1" __prompt="$2" __val=""
  read -r -s -p "$__prompt" __val; echo
  [[ -n "$__val" ]] || die "Empty input"
  printf -v "$__var" "%s" "$__val"
}

safe_mkdir(){ mkdir -p "$1"; chmod 700 "$1" 2>/dev/null || true; }

apt_install_base() {
  sudo apt-get update -y
  sudo apt-get install -y \
    git jq ripgrep unzip ca-certificates curl \
    build-essential pkg-config \
    python3 python3-venv python3-pip
}

ensure_python_rich() {
  # Install Rich in user site-packages (no venv required for this script).
  python3 - <<'PY' >/dev/null 2>&1 || python3 -m pip install --user -U rich >/dev/null
import rich
PY
}

check_copilot_availability() {
  # Ensure gh CLI is present
  if ! command -v gh >/dev/null 2>&1; then
    echo "[copilot] gh CLI not found" >&2
    return 1
  fi

  # Delete conflicting alias if present (safe attempt)
  gh alias delete copilot >/dev/null 2>&1 || true

  # Check for built-in gh copilot
  if ! gh copilot --help >/dev/null 2>&1; then
    echo "[copilot] gh copilot built-in command NOT detected" >&2
    return 1
  fi

  # Check authentication status
  if ! gh auth status >/dev/null 2>&1; then
    echo "[copilot] gh auth status is NOT OK" >&2
    return 1
  fi

  return 0
}

detect_repo_hints() {
  local s=""
  [[ -f "pyproject.toml" || -f "requirements.txt" || -d "tests" ]] && s+="python_signals=1 "
  (compgen -G "*.cpp" >/dev/null || compgen -G "*.cc" >/dev/null || compgen -G "*.cxx" >/dev/null || [[ -f "CMakeLists.txt" || -f "Makefile" ]]) && s+="cpp_signals=1 "
  [[ -d ".github/workflows" ]] && s+="github_workflows=1 "
  [[ -f "package.json" ]] && s+="node_signals=1 "
  echo "${s:-signals=none}"
}

bucket_repo_ok() {
  local bucket="$1"
  case "$bucket" in
    python) [[ -f "pyproject.toml" || -f "requirements.txt" || -d "tests" ]] ;;
    cpp) [[ -f "CMakeLists.txt" || -f "Makefile" ]] || compgen -G "*.cpp" >/dev/null || compgen -G "*.cc" >/dev/null || compgen -G "*.cxx" >/dev/null ;;
    github) [[ -d ".github/workflows" || -f ".github/dependabot.yml" || -f ".github/CODEOWNERS" ]] ;;
    *) return 1 ;;
  esac
}

json_is_valid() {
  local data="$1"
  python3 - "$data" <<'PY'
import json,sys
s=sys.argv[1]
try:
  json.loads(s)
except Exception:
  raise SystemExit(1)
PY
}

write_jsonl() {
  local out_file="$1" bucket="$2" repo_full="$3" repo_dir="$4" prompt="$5" response="$6"
  local ts; ts="$(timestamp)"
  python3 - "$out_file" "$ts" "$bucket" "$repo_full" "$repo_dir" "$prompt" "$response" <<'PY'
import json,sys
out,ts,bucket,repo,repo_dir,prompt,response = sys.argv[1:]
rec={"ts":ts,"bucket":bucket,"repo":repo,"repo_dir":repo_dir,"prompt":prompt,"response":response}
with open(out,"a",encoding="utf-8") as f:
  f.write(json.dumps(rec,ensure_ascii=False)+"\n")
PY
}

extract_first_json_obj() {
  python3 - <<'PY'
import sys, json
s=sys.stdin.read()
start=s.find('{')
if start==-1:
  sys.exit(1)
depth=0
in_str=False
esc=False
for j,ch in enumerate(s[start:], start=start):
  if in_str:
    if esc: esc=False
    elif ch=='\\': esc=True
    elif ch=='"': in_str=False
    continue
  else:
    if ch=='"': in_str=True; continue
    if ch=='{': depth+=1
    elif ch=='}':
      depth-=1
      if depth==0:
        cand=s[start:j+1]
        try:
          json.loads(cand)
        except Exception:
          sys.exit(2)
        sys.stdout.write(cand)
        sys.exit(0)
sys.exit(3)
PY
}

# -------- HTTP AI API (Azure OpenAI / OpenAI / GitHub Copilot fallback) --------
call_ai_api() {
  local prompt="$1"
  local model="${2:-gpt-5-mini}"
  local api_key="${GITHUB_PAT:-}"
  
  local temperature=0.7
  local max_tokens=4000

  # Use OpenAI API if OPENAI_API_KEY is set
  if [[ "${HEIDI_USE_OPENAI:-1}" -eq 1 && -n "${OPENAI_API_KEY:-}" ]]; then
    local resp
    if resp=$(call_with_timeout_retry "openai" curl -fsSL \
      -X POST "https://api.openai.com/v1/chat/completions" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${OPENAI_API_KEY}" \
      -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":$(
        python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$prompt"
      )}],\"temperature\":$temperature,\"max_tokens\":$max_tokens}" 2>&1); then

      if echo "$resp" | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get('choices') else 1)" 2>/dev/null; then
        local content
        content="$(echo "$resp" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('choices',[{}])[0].get('message',{}).get('content',''))" 2>/dev/null)"
        if [[ -n "$content" ]]; then
          echo "$content"
          return 0
        fi
      fi
      echo "call_ai_api: OpenAI API response invalid - ${resp:0:200}" >&2
    else
      echo "call_ai_api: OpenAI API call failed" >&2
    fi
  fi

  # Use Azure OpenAI if configured
  if [[ -n "${AZURE_OPENAI_ENDPOINT:-}" && -n "${AZURE_OPENAI_API_KEY:-}" ]]; then
    local azure_endpoint="${AZURE_OPENAI_ENDPOINT}"
    local azure_deployment="${AZURE_OPENAI_DEPLOYMENT:-gpt-4.1}"
    local resp
    if resp=$(call_with_timeout_retry "azure" curl -fsSL \
      -X POST "${azure_endpoint}openai/deployments/${azure_deployment}/chat/completions?api-version=2024-02-15-preview" \
      -H "Content-Type: application/json" \
      -H "api-key: ${AZURE_OPENAI_API_KEY}" \
      -d "{\"messages\":[{\"role\":\"user\",\"content\":$(
        python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$prompt"
      )}],\"temperature\":$temperature,\"max_tokens\":$max_tokens}" 2>&1); then

      if echo "$resp" | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get('choices') else 1)" 2>/dev/null; then
        local content
        content="$(echo "$resp" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('choices',[{}])[0].get('message',{}).get('content',''))" 2>/dev/null)"
        if [[ -n "$content" ]]; then
          echo "$content"
          return 0
        fi
      fi
      echo "call_ai_api: Azure API response invalid - ${resp:0:200}" >&2
    else
      echo "call_ai_api: Azure API call failed" >&2
    fi
  fi

  # Fallback: Use Python Copilot SDK Wrapper if available
  local sdk_wrapper="/home/heidi/heidi-training/copilot_sdk_wrapper.py"
  if [[ "${HEIDI_USE_COPILOT:-1}" -eq 1 && -f "$sdk_wrapper" ]]; then
    local resp
    export COPILOT_MODEL="$model"
    if resp=$(call_with_timeout_retry "sdk_wrapper" python3 "$sdk_wrapper" "$prompt" 2>&1); then
      # Check if we got a valid JSON response with content
      if echo "$resp" | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get('choices') else 1)" 2>/dev/null; then
         local content
         content="$(echo "$resp" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('choices',[{}])[0].get('message',{}).get('content',''))" 2>/dev/null)"
         if [[ -n "$content" ]]; then
           echo "$content"
           return 0
         fi
      fi
    fi
  fi

  # Fallback: Use GitHub PAT with copilot-api.github.com
  if [[ "${HEIDI_USE_COPILOT:-1}" -eq 1 && -n "$api_key" ]]; then
    local copilot_url="https://copilot-api.github.com/v1/chat/completions"
    local resp
    if resp=$(call_with_timeout_retry "copilot_api" curl -fsSL \
      -X POST "$copilot_url" \
      -H "Authorization: Bearer $api_key" \
      -H "Content-Type: application/json" \
      -H "Accept: application/json" \
      -H "x-initiator: user" \
      -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":$(
        python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$prompt"
      )}],\"temperature\":$temperature,\"max_tokens\":$max_tokens}" 2>&1); then

      if [[ -n "$resp" ]]; then
        if echo "$resp" | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get('choices') else 1)" 2>/dev/null; then
          local content
          content="$(echo "$resp" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('choices',[{}])[0].get('message',{}).get('content',''))" 2>/dev/null)"
          if [[ -n "$content" ]]; then
            echo "$content"
            return 0
          fi
        fi
      fi
    fi
  fi

  echo "call_ai_api: AI API unavailable or all fallbacks failed" >&2
  return 1
}

# -------- GitHub Search helpers (faster + rate-limit aware) --------
gh_search_page() {
  local token="$1" q="$2" sort="$3" page="$4"

  local resp
  if resp=$(call_with_timeout_retry "gh_api_search" bash -c "GH_TOKEN='$token' gh api -X GET search/repositories \
    -f q='$q' -f sort='$sort' -f order=desc -f per_page=100 -f page='$page'"); then

    if echo "$resp" | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get('total_count') else 1)" 2>/dev/null; then
      echo "$resp"
      return 0
    fi

    if echo "$resp" | grep -q "rate limit"; then
      echo "Rate limited. Sleeping 30s..." >&2
      sleep 30
      return 1 # retry will handle it if we wrap it differently, but call_with_timeout_retry doesn't know about rate limits
    fi
  fi

  return 1
}

build_repo_pool() {
  local token="$1" n="$2" q_lang="$3" out_file="$4" bucket_name="$5"
  
  # Robustness: Redo search if file is empty or suspiciously small
  if [[ -f "$out_file" && -s "$out_file" ]]; then
    local line_count; line_count=$(wc -l < "$out_file")
    if [[ "$line_count" -ge 10 ]]; then
      log_event "discovery" "Using existing repo list: $out_file ($line_count repos)"
      return 0
    fi
  fi

  local pages=1  # Maximum speed: only search 1 page (100 repos)
  
  log_event "discovery" "Building repo pool for $bucket_name..."
  local q_base="stars:>50 fork:false archived:false"
  [[ -n "$q_lang" ]] && q_base="$q_base language:$q_lang"

  : > "$out_file.pool"
  log_event "discovery" "  [$bucket_name] Searching GitHub 'stars'..."
  progress_bar 0 1 "pool [$bucket_name]: searching"
  gh_search_page "$token" "$q_base" "stars" 1 | jq -r '.items[].full_name' >> "$out_file.pool" || true
  
  progress_bar 1 1 "pool [$bucket_name]: shuffling"
  sort -u "$out_file.pool" | shuf -n "$n" > "$out_file"
  progress_done
  rm -f "$out_file.pool"
}

# -------- Copilot bucket runner --------
run_copilot_bucket() {
  local bucket="$1" out_dir="$2" repo_full="$3" repo_dir="$4"

  local samples="$out_dir/samples.jsonl"
  local hashes="$out_dir/hashes.txt"
  local raw_dir="$out_dir/raw/$repo_dir"
  safe_mkdir "$raw_dir"
  touch "$samples" "$hashes"

  if ! bucket_repo_ok "$bucket"; then
    echo "skip (bucket filter): $repo_full" >&2
    return 0
  fi

  local hints; hints="$(detect_repo_hints)"
  local filelist; filelist="$( (rg -n --hidden --no-ignore-vcs -S "TODO|FIXME" -g'!*node_modules/*' -g'!*dist/*' -g'!*build/*' . 2>/dev/null | head -n 60) || true )"
  local topfiles; topfiles="$( (ls -la 2>/dev/null | head -n 40) || true )"

  local prompt=""
  case "$bucket" in
    python) prompt=$(cat <<EOF
You are generating a high-quality training sample for a local Python model.

Repo: $repo_full
Repo hints: $hints

Top-level listing:
$topfiles

TODO/FIXME matches (if any):
$filelist

Task:
- Identify ONE safe, minimal improvement or bug fix suitable for a quick PR in a Python repo.
- Prefer: tests, lint, packaging, deterministic behavior, small refactor, or doc fix tied to code.
- Provide exact verification commands (pytest/ruff/etc) if applicable.

Return EXACTLY one JSON object with keys:
- instruction
- input
- output (unified diff if feasible + verification commands)

JSON only. No markdown.
EOF
);;
    cpp) prompt=$(cat <<EOF
You are generating a high-quality training sample for a local C++ model.

Repo: $repo_full
Repo hints: $hints

Top-level listing:
$topfiles

TODO/FIXME matches (if any):
$filelist

Task:
- Identify ONE safe, minimal improvement or bug fix suitable for a quick PR in a C/C++ repo.
- Prefer: build fixes, CMake, warnings cleanup, deterministic tests, small refactor, docs tied to code.
- Provide exact build/test commands (cmake/ctest/make/etc) if applicable.

Return EXACTLY one JSON object with keys:
- instruction
- input
- output (unified diff if feasible + verification commands)

JSON only. No markdown.
EOF
);;
    github) prompt=$(cat <<EOF
You are generating a high-quality training sample for a local GitHub/CI model.

Repo: $repo_full
Repo hints: $hints

Top-level listing:
$topfiles

Task:
- Identify ONE safe, minimal improvement to GitHub workflows / CI / repo hygiene.
- Prefer: fix CI flake, caching, tighten permissions, add missing triggers, improve lint/test job, security hardening.
- Reference files under .github/workflows if present.

Return EXACTLY one JSON object with keys:
- instruction
- input
- output (unified diff if feasible + verification steps)

JSON only. No markdown.
EOF
);;
    *) die "unknown bucket: $bucket";;
  esac

  local raw_out="$raw_dir/copilot_$(date -u +'%Y%m%dT%H%M%SZ').txt"

  local resp=""
  local model_to_use="${TEACHER_MODEL:-gpt-5-mini}"

  # Use HTTP API for code generation (gh copilot fallback)
  if resp="$(call_ai_api "$prompt" "$model_to_use" 2>&1)"; then
    :
  elif [[ "${HEIDI_USE_COPILOT:-1}" -eq 1 ]] && resp="$(call_with_timeout_retry "gh_copilot" gh copilot -p "$prompt" --model "$model_to_use" --allow-all 2>&1)"; then
    :
  else
    printf "%s\n" "$resp" > "$raw_out"
    echo "copilot error: $repo_full" >&2
    update_state_count "teacher_failed"
    log_event "generating" "Copilot error for $repo_full: ${resp:0:100}..."
    return 1
  fi
  printf "%s\n" "$resp" > "$raw_out"

  local json=""
  if ! json="$(printf "%s" "$resp" | extract_first_json_obj 2>/dev/null || true)"; then
    write_jsonl "$samples" "$bucket" "$repo_full" "$repo_dir" "$prompt" "$resp"
    # Preserve raw failing response for diagnostics
    diag_dir="$out/diagnostics"
    mkdir -p "$diag_dir"
    diag_file="$diag_dir/${repo_dir}_$(date -u +'%Y%m%dT%H%M%SZ')_noobj.txt"
    printf "%s\n" "$resp" > "$diag_file"
    chmod 600 "$diag_file" 2>/dev/null || true
    echo "invalid json (no parsable object): $repo_full (raw saved: $diag_file)" >&2
    update_state_count "teacher_failed"
    log_event "generating" "Invalid JSON (no object) for $repo_full (raw: $diag_file)"
    return 1
  fi

  if ! json_is_valid "$json"; then
    write_jsonl "$samples" "$bucket" "$repo_full" "$repo_dir" "$prompt" "$resp"
    # Preserve raw failing response for diagnostics
    diag_dir="$out/diagnostics"
    mkdir -p "$diag_dir"
    diag_file="$diag_dir/${repo_dir}_$(date -u +'%Y%m%dT%H%M%SZ')_parsefail.txt"
    printf "%s\n" "$resp" > "$diag_file"
    chmod 600 "$diag_file" 2>/dev/null || true
    echo "invalid json (parse fail): $repo_full (raw saved: $diag_file)" >&2
    update_state_count "teacher_failed"
    log_event "generating" "Invalid JSON (parse fail) for $repo_full (raw: $diag_file)"
    return 1
  fi

  local h
  h="$(printf "%s" "$json" | sha256sum | awk '{print $1}')"
  if grep -qx "$h" "$hashes" 2>/dev/null; then
    echo "dup sample (hash): $repo_full" >&2
    return 0
  fi
  echo "$h" >> "$hashes"

  write_jsonl "$samples" "$bucket" "$repo_full" "$repo_dir" "$prompt" "$resp"
  update_state_count "teacher_generated"
  printf "%s\n" "$json" >> "$out_dir/clean_samples.jsonl"
  update_state_count "validated_ok"
  log_event "generating" "Sample generated for $repo_full"
  return 0
}

usage() {
  cat <<EOF
Usage: $0 [--repos N] [--reclone] [--parallel P] [--clone-parallel C] [--fresh] [--nice]

Options:
  --repos N           repos per bucket (default: 50)
  --reclone           force delete+reclone existing repo dirs (default: skip existing)
  --parallel P        parallel Copilot workers per bucket (default: 4)
  --clone-parallel C  parallel git clone workers (default: 16)
  --fresh             wipe outputs for this rig (default: resume/append)
  --nice              run with lower CPU/IO priority (nice + ionice if available)
  --no-ai             skip Copilot / AI calls and only clone repos
EOF
}

main() {
  local N=50
  local RECLONE=0
  local PAR=16
  local CLONE_PAR=16
  local FRESH=0
  local NO_AI=0
  local DO_NICE=0
  
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --repos) shift; [[ $# -gt 0 ]] || die "--repos requires N"; N="$1";;
      --reclone) RECLONE=1;;
      --parallel) shift; [[ $# -gt 0 ]] || die "--parallel requires P"; PAR="$1";;
      --clone-parallel) shift; [[ $# -gt 0 ]] || die "--clone-parallel requires C"; CLONE_PAR="$1";;
      --no-ai) NO_AI=1;;
      --fresh) FRESH=1;;
      --nice) DO_NICE=1;;
      -h|--help) usage; exit 0;;
      *) die "Unknown arg: $1";;
    esac
    shift
  done

  # Support HEIDI_ENHANCE=0 to skip the whole thing
  if [[ "${HEIDI_ENHANCE:-1}" -eq 0 ]]; then
    echo "HEIDI_ENHANCE=0, exiting."
    exit 0
  fi

  # Initialize paths and output directories after argument parsing
  init_paths "$N"

  # Start watchdog
  start_watchdog "$out/state.json"

  need_cmd sudo
  need_cmd sha256sum
  need_cmd jq
  need_cmd git
  need_cmd curl

  echo "=== Local Copilot training rig (language-filtered) ==="
  echo "Repos per bucket: $N   Reclone: $RECLONE   Copilot parallel: $PAR   Clone parallel: $CLONE_PAR   Fresh: $FRESH   No-AI: $NO_AI"

  if [[ "$DO_NICE" -eq 1 ]]; then
    nice -n 10 true 2>/dev/null || true
    if command -v ionice >/dev/null 2>&1; then
      ionice -c2 -n7 -p $$ >/dev/null 2>&1 || true
    fi
  fi

  # echo "[1/8] Install base dependencies..."
  # apt_install_base

  echo "[2/8] Ensure Rich for progress UI..."
  ensure_python_rich

  # echo "[3/8] Install GitHub CLI if missing..."
  # install_gh_cli_if_missing

  echo "[3/8] Configure Git for resilience..."
  git config --global http.lowSpeedLimit 0
  git config --global http.lowSpeedTime 999999
  git config --global http.postBuffer 524288000

  echo "[4/8] Check GitHub CLI and Copilot..."
  if check_copilot_availability; then
    echo "  ✓ GitHub CLI and Copilot ready"
    export HEIDI_USE_COPILOT=${HEIDI_USE_COPILOT:-1}
  else
    echo "  ! Copilot not available or not authenticated. Fail-open: skipping Copilot enhance."
    export HEIDI_USE_COPILOT=0
  fi

  local base="$HOME/heidi_repos"
  safe_mkdir "$base"
  cd "$base"

  echo
  echo "[6/8] GitHub PAT for Search API + cloning (hidden input, not stored)..."
  local PAT="${GITHUB_PAT:-}"
  if [[ -z "$PAT" ]]; then
    if gh auth status >/dev/null 2>&1; then
      PAT=$(gh auth token 2>/dev/null || true)
      [[ -n "$PAT" ]] && echo "  ✓ Using GitHub CLI authenticated token"
    fi
  fi
  if [[ -z "$PAT" ]]; then
    prompt_hidden PAT "GITHUB PAT: "
  fi
  # Ensure the resolved PAT is exported as GITHUB_PAT for call_ai_api() fallback
  export GITHUB_PAT="$PAT"

  update_state_stage "discovery"
  log_event "discovery" "Building repo pools..."
  echo "[7/8] Building combined repo pool (stars+forks pools)..."
  # build pools in parallel to reduce wall time
  ( build_repo_pool "$PAT" "$N" "Python" "repos_python.txt" "Python" ) &
  pid_py=$!
  ( build_repo_pool "$PAT" "$N" "C++" "repos_cpp.txt" "C++" ) &
  pid_cpp=$!
  ( build_repo_pool "$PAT" "$N" "" "repos_github.txt" "Generic-GitHub" ) &
  pid_gh=$!
  wait "$pid_py" "$pid_cpp" "$pid_gh"

  local total_repos; total_repos=$(cat repos_python.txt repos_cpp.txt repos_github.txt | sort -u | wc -l)
  export N_TOTAL_REPOS="$total_repos"
  log_event "discovery" "Found $total_repos unique repos in pools."
  # If the discovered pool is smaller than the requested target, adjust
  # the runtime `target_repos` so dashboard and progress counters reflect reality.
  if [[ -n "$out" ]]; then
    python3 - "$out/state.json" "$total_repos" <<'PY'
import sys, json, fcntl, os
f, tot = sys.argv[1:3]
if os.path.exists(f):
    with open(f, 'r+') as j:
        try:
            fcntl.flock(j, fcntl.LOCK_EX)
            d = json.load(j)
            d['target_repos'] = int(tot)
            d['last_update'] = __import__('datetime').datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            j.seek(0); json.dump(d, j, indent=2); j.truncate()
        except Exception:
            pass
        finally:
            fcntl.flock(j, fcntl.LOCK_UN)
PY
    log_event "discovery" "Adjusted target_repos to $total_repos (pool size)"
  fi
  if [[ "$total_repos" -eq 0 ]]; then
    log_event "error" "CRITICAL: Repo pools are empty! Check your GITHUB_PAT and search queries."
    echo "ERROR: Repo pools are empty. Check your GITHUB_PAT." >&2
    exit 1
  fi

  echo
  # Countdown before starting generation so dashboard can show time-to-start
  COUNTDOWN=${COUNTDOWN:-10}
  # compute generation start timestamp (UTC ISO)
  generation_start_ts=$(date -u -d "+${COUNTDOWN} seconds" +"%Y-%m-%dT%H:%M:%SZ")
  # write generation_start_ts into state.json so dashboard can compute countdown
  python3 - "$out/state.json" "$generation_start_ts" <<'PY'
import sys, json, fcntl, os
f, ts = sys.argv[1:3]
if os.path.exists(f):
    with open(f, 'r+') as j:
        try:
            fcntl.flock(j, fcntl.LOCK_EX)
            d = json.load(j)
            d['generation_start_ts'] = ts
            d['last_update'] = ts
            j.seek(0); json.dump(d, j, indent=2); j.truncate()
        except: pass
        finally:
            fcntl.flock(j, fcntl.LOCK_UN)
PY

  update_state_stage "generating"
  log_event "generating" "Starting Pipelined Clone + Generate workers..."
  echo "[8/8] Running Pipelined Clone + Generate (Workers: $PAR)"
  
  # Function to process a single repo: clone -> run copilot bucket -> cleanup
  # This allows us to start generating as soon as the FIRST repo is cloned.
  export -f die need_cmd timestamp prompt_hidden safe_mkdir detect_repo_hints bucket_repo_ok json_is_valid write_jsonl extract_first_json_obj run_copilot_bucket setup_proxy log_event update_state_count update_state_stage call_ai_api call_with_timeout_retry
  export GIT_HTTP_EXTRA_HEADER="AUTHORIZATION: basic $(printf "x-access-token:%s" "$PAT" | base64 -w0)"
  export GIT_TERMINAL_PROMPT=0
  export out rig PAT TEACHER_MODEL N AUTOTRAIN_DIR NO_AI HEIDI_MAX_RETRIES HEIDI_CALL_TIMEOUT_SEC HEIDI_USE_COPILOT HEIDI_USE_OPENAI N_TOTAL_REPOS

  # We use a helper function to wrap the logic for a single repo
  pipeline_worker() {
    local bucket="$1" out_dir="$2" repo_full="$3" base_dir="$4" pat="$5"
    local name="${repo_full##*/}"
    local target="$base_dir/$name"

    # Setup proxy for this specific worker task
    setup_proxy || true

    # 1. Clone
    if [[ ! -d "$target/.git" ]]; then
      log_event "generating" "Cloning $repo_full..."
      # Use the proxy if configured
      # We preserve git --progress output as requested
      if ! call_with_timeout_retry "git_clone" git ${GIT_CONF_PROXY:-} clone --progress --depth 1 --filter=blob:none --no-tags --single-branch \
        "https://github.com/$repo_full.git" "$target"; then
          log_event "generating" "Clone failed for $repo_full"
          echo "[fail] clone $repo_full" >&2; 
          return 1; 
      fi
      log_event "generating" "Clone success: $repo_full"
      # increment cloned repo counter so dashboard can show progress
      update_state_count "repos_cloned"

      # Report progress for cloning stage
      local cloned_count; cloned_count=$(python3 -c "import json,os; f='$out/state.json'; d=json.load(open(f)) if os.path.exists(f) else {}; print(d.get('counters', {}).get('repos_cloned', 0))" 2>/dev/null || echo 0)
      progress_bar "$cloned_count" "${N_TOTAL_REPOS:-150}" "cloning: $repo_full"
    fi

    # 2. Process
    (
      cd "$target"
      if [[ "${NO_AI:-0}" -eq 1 ]]; then
        log_event "generating" "Skipping Copilot generation for $repo_full (no-ai)"
        echo "[skip] generation disabled for $repo_full"
      else
        if run_copilot_bucket "$bucket" "$out_dir" "$repo_full" "$name"; then
          echo "[ok] processed $repo_full"
        else
          echo "[fail] process $repo_full" >&2
        fi
      fi
    )

    # 3. Cleanup (optional, uncomment to save space)
    # rm -rf "$target"
  }
  export -f pipeline_worker

  # Function to run the pipeline for a bucket
  run_bucket_pipeline() {
    local bucket="$1" out_dir="$2" list_file="$3" base_dir="$4"
    echo "  - Starting pipeline for bucket: $bucket"
    # Ensure call_ai_api and other functions are visible to xargs bash
    cat "$list_file" | xargs -P "$PAR" -I{} bash -c "setup_proxy >/dev/null 2>&1; pipeline_worker '$bucket' '$out_dir' '{}' '$base_dir'"
  }

  local success_count=0
  local start_time; start_time=$(date +%s)

  run_bucket_pipeline "python" "$out/python" "repos_python.txt" "$base" &
  pid_p=$!
  run_bucket_pipeline "cpp" "$out/cpp" "repos_cpp.txt" "$base" &
  pid_c=$!
  run_bucket_pipeline "github" "$out/github" "repos_github.txt" "$base" &
  pid_g=$!
  
  wait "$pid_p" "$pid_c" "$pid_g"

  local end_time; end_time=$(date +%s)
  local duration=$((end_time - start_time))

  echo
  echo "DONE. Pipelined execution completed in ${duration}s."
  echo "Outputs available in: $base/$out"
  
  unset GIT_HTTP_EXTRA_HEADER
}

main "$@"
