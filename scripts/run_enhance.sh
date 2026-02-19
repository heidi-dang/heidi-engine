#!/usr/bin/env bash
set -e
set -u
set -o pipefail

die(){ echo "ERROR: $*" >&2; exit 1; }
need_cmd(){ command -v "$1" >/dev/null 2>&1 || die "Missing command: $1"; }
timestamp(){ date -u +"%Y-%m-%dT%H:%M:%SZ"; }

# -------- tiny progress UI (no extra deps) --------
progress_bar() {
  if [[ "${HEIDI_PROGRESS:-1}" -eq 0 ]]; then return 0; fi
  local cur="$1" total="$2" repo="${3:-}" stage="${4:-}" start_time="${5:-$(date +%s)}"
  local now; now=$(date +%s)
  local elapsed=$(( now - start_time ))
  (( total > 0 )) || total=1
  (( cur < 0 )) && cur=0
  (( cur > total )) && cur=$total
  local pct=$(( cur * 100 / total ))
  if [[ -t 2 ]]; then
    printf "\r[PROG] %d/%d (%d%%) | %s | %s | %ds    " "$cur" "$total" "$pct" "$repo" "$stage" "$elapsed" >&2
  else
    if (( cur % (total / 20 + 1) == 0 )) || (( cur == total )); then
      echo "[PROG] $cur/$total ($pct%) | $repo | $stage | ${elapsed}s" >&2
    fi
  fi
}

# Retry helper with timeout
# Usage: with_retry <label> <command...>
with_retry() {
  local label="$1"
  shift
  local cmd=("$@")
  local attempt=1
  local max_retries="${HEIDI_MAX_RETRIES:-3}"
  local timeout_sec="${HEIDI_CALL_TIMEOUT_SEC:-60}"

  while (( attempt <= max_retries )); do
    echo "[retry] $label (attempt $attempt/$max_retries, timeout ${timeout_sec}s)..." >&2
    if timeout "${timeout_sec}s" "${cmd[@]}"; then
      return 0
    fi
    echo "[fail] $label failed (attempt $attempt)" >&2
    (( attempt++ ))
    sleep 2
  done

  echo "[error] $label failed after $max_retries attempts." >&2
  return 1
}

SCRIPT_DIR_INTERNAL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR_INTERNAL/.." && pwd)"

# Source common configurations if available
if [ -f "$SCRIPT_DIR_INTERNAL/common.sh" ]; then
    source "$SCRIPT_DIR_INTERNAL/common.sh"
    # Ensure apply_git_optimizations is available and called
    if command -v apply_git_optimizations >/dev/null 2>&1; then
      apply_git_optimizations
    fi
fi

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

install_gh_cli_if_missing() {
  if command -v gh >/dev/null 2>&1; then return 0; fi
  curl -fsSL --compressed https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg >/dev/null
  sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null
  sudo apt-get update -y
  sudo apt-get install -y gh
}

install_copilot_ext() {
  # Modern Copilot Path: Prefer built-in 'gh copilot'
  # First, remove conflicting alias if present (safe attempt)
  if gh alias list 2>/dev/null | awk '{print $1}' | grep -qx "copilot"; then
    echo "[copilot] removing conflicting 'copilot' alias..."
    gh alias delete copilot || true
  fi

  # Detect and use built-in gh copilot only
  if gh copilot --help >/dev/null 2>&1; then
    echo "  ✓ GitHub Copilot built-in command detected"
    return 0
  fi

  # Fail-open: If gh copilot --help fails, we skip copilot enhance for this run
  echo "[WARN] gh copilot built-in command not found or not working." >&2
  return 1
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
  if [[ -n "${OPENAI_API_KEY:-}" && "${HEIDI_USE_OPENAI:-1}" -eq 1 ]]; then
    local resp
    local tmp_resp; tmp_resp=$(mktemp)
    if with_retry "OpenAI API" curl -fsSL --connect-timeout 30 \
      -X POST "https://api.openai.com/v1/chat/completions" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${OPENAI_API_KEY}" \
      -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":$(
        python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$prompt"
      )}],\"temperature\":$temperature,\"max_tokens\":$max_tokens}" -o "$tmp_resp"; then
      resp=$(cat "$tmp_resp")
      rm -f "$tmp_resp"
    else
      rm -f "$tmp_resp"
      return 1
    fi

    if echo "$resp" | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get('choices') else 1)" 2>/dev/null; then
      local content
      content="$(echo "$resp" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('choices',[{}])[0].get('message',{}).get('content',''))" 2>/dev/null)"
      if [[ -n "$content" ]]; then
        echo "$content"
        return 0
      fi
    fi
    echo "call_ai_api: OpenAI API failed - ${resp:0:200}" >&2
    return 1
  fi

  # Use Azure OpenAI if configured
  if [[ -n "${AZURE_OPENAI_ENDPOINT:-}" && -n "${AZURE_OPENAI_API_KEY:-}" ]]; then
    local azure_endpoint="${AZURE_OPENAI_ENDPOINT}"
    local azure_deployment="${AZURE_OPENAI_DEPLOYMENT:-gpt-4.1}"
    local resp
    local tmp_resp; tmp_resp=$(mktemp)
    if with_retry "Azure OpenAI API" curl -fsSL --connect-timeout 30 \
      -X POST "${azure_endpoint}openai/deployments/${azure_deployment}/chat/completions?api-version=2024-02-15-preview" \
      -H "Content-Type: application/json" \
      -H "api-key: ${AZURE_OPENAI_API_KEY}" \
      -d "{\"messages\":[{\"role\":\"user\",\"content\":$(
        python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$prompt"
      )}],\"temperature\":$temperature,\"max_tokens\":$max_tokens}" -o "$tmp_resp"; then
      resp=$(cat "$tmp_resp")
      rm -f "$tmp_resp"
    else
      rm -f "$tmp_resp"
      return 1
    fi

    if echo "$resp" | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get('choices') else 1)" 2>/dev/null; then
      local content
      content="$(echo "$resp" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('choices',[{}])[0].get('message',{}).get('content',''))" 2>/dev/null)"
      if [[ -n "$content" ]]; then
        echo "$content"
        return 0
      fi
    fi
    echo "call_ai_api: Azure API failed - ${resp:0:200}" >&2
    return 1
  fi

  # Fallback: Use Python Copilot SDK Wrapper if available
  local sdk_wrapper="/home/heidi/heidi-training/copilot_sdk_wrapper.py"
  if [[ -f "$sdk_wrapper" ]]; then
    local resp
    export COPILOT_MODEL="$model"
    resp="$(python3 "$sdk_wrapper" "$prompt" 2>&1)" || true

    # Check if we got a valid JSON response with content
    if echo "$resp" | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get('choices') else 1)" 2>/dev/null; then
       local content
       content="$(echo "$resp" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('choices',[{}])[0].get('message',{}).get('content',''))" 2>/dev/null)"
       if [[ -n "$content" ]]; then
         echo "$content"
         return 0
       fi
    fi
    # Only logging error if SDK was attempted and failed significantly
    # echo "call_ai_api: SDK wrapper failed - ${resp:0:200}" >&2
  fi

  # Fallback: Use GitHub PAT with copilot-api.github.com
  if [[ -z "$api_key" ]]; then
    echo "call_ai_api: no API key" >&2
    return 1
  fi

  local copilot_url="https://copilot-api.github.com/v1/chat/completions"
  local resp
  local tmp_resp; tmp_resp=$(mktemp)
  if with_retry "Copilot API" curl -fsSL --connect-timeout 30 \
    -X POST "$copilot_url" \
    -H "Authorization: Bearer $api_key" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -H "x-initiator: user" \
    -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":$(
      python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$prompt"
    )}],\"temperature\":$temperature,\"max_tokens\":$max_tokens}" -o "$tmp_resp"; then
    resp=$(cat "$tmp_resp")
    rm -f "$tmp_resp"
  else
    rm -f "$tmp_resp"
    return 1
  fi

  if [[ -z "$resp" ]]; then
    echo "call_ai_api: empty response" >&2
    return 1
  fi

  if echo "$resp" | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get('choices') else 1)" 2>/dev/null; then
    local content
    content="$(echo "$resp" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('choices',[{}])[0].get('message',{}).get('content',''))" 2>/dev/null)"
    if [[ -n "$content" ]]; then
      echo "$content"
      return 0
    fi
  fi

  echo "call_ai_api: API call failed - ${resp:0:200}" >&2
  return 1
}

# -------- GitHub Search helpers (faster + rate-limit aware) --------
gh_search_page() {
  local token="$1" q="$2" sort="$3" page="$4"

  local attempt
  for attempt in 1 2 3 4 5; do
    local resp
    resp="$(GH_TOKEN="$token" gh api -X GET search/repositories \
      -f q="$q" -f sort="$sort" -f order=desc -f per_page=100 -f page="$page" 2>&1)" || true

    if echo "$resp" | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get('total_count') else 1)" 2>/dev/null; then
      echo "$resp"
      return 0
    fi

    if echo "$resp" | grep -q "rate limit"; then
      echo "Rate limited. Sleeping 30s..." >&2
      sleep 30
      continue
    fi

    echo "GitHub search failed (attempt=$attempt): ${resp:0:100}" >&2
    sleep 3
  done

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
  gh_search_page "$token" "$q_base" "stars" 1 | jq -r '.items[].full_name' >> "$out_file.pool" || true

  sort -u "$out_file.pool" | shuf -n "$n" > "$out_file"
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
  elif [[ "${HEIDI_USE_COPILOT:-1}" -eq 1 ]]; then
    local tmp_resp; tmp_resp=$(mktemp)
    if with_retry "gh copilot" gh copilot -p "$prompt" --model "$model_to_use" --allow-all > "$tmp_resp" 2>&1; then
      resp=$(cat "$tmp_resp")
      rm -f "$tmp_resp"
    else
      resp=$(cat "$tmp_resp")
      rm -f "$tmp_resp"
      printf "%s\n" "$resp" > "$raw_out"
      echo "copilot error: $repo_full" >&2
      update_state_count "teacher_failed"
      log_event "generating" "Copilot error for $repo_full: ${resp:0:100}..."
      return 1
    fi
  else
    echo "copilot skipped: $repo_full" >&2
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
  if [[ "${HEIDI_ENHANCE:-1}" -eq 0 ]]; then
    echo "[INFO] HEIDI_ENHANCE=0, skipping enhancement stage."
    return 0
  fi

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

  # Initialize paths and output directories after argument parsing
  init_paths "$N"

  # Start watchdog
  start_watchdog "Enhancement Stage (Rig: $rig)" "/tmp/heidi_run.log"

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

  echo "[4/8] Authenticate GitHub CLI (OAuth) for Copilot..."
  local copilot_ready=1
  if gh auth status >/dev/null 2>&1; then
    echo "  ✓ GitHub CLI already authenticated"
  elif [[ -n "${GITHUB_PAT:-}" ]]; then
    if echo "$GITHUB_PAT" | gh auth login --with-token 2>/dev/null; then
       echo "  ✓ GitHub CLI authenticated via PAT"
    else
       echo "[WARN] GitHub CLI authentication failed." >&2
       copilot_ready=0
    fi
  else
    echo "[WARN] GitHub CLI not authenticated." >&2
    copilot_ready=0
  fi

  echo "[5/8] Checking Copilot availability..."
  if [[ "$copilot_ready" -eq 1 ]]; then
    if ! install_copilot_ext; then
      copilot_ready=0
    fi
  fi

  if [[ "$copilot_ready" -eq 0 ]]; then
    echo "[WARN] Copilot not available (auth fail or command missing). Enhancement will be skipped." >&2
    export HEIDI_USE_COPILOT=0
  else
    echo "  ✓ Copilot is ready"
    export HEIDI_USE_COPILOT=1
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
export -f die need_cmd timestamp progress_bar heartbeat with_retry with_heartbeat prompt_hidden safe_mkdir detect_repo_hints bucket_repo_ok json_is_valid write_jsonl extract_first_json_obj run_copilot_bucket setup_proxy log_event update_state_count update_state_stage call_ai_api
  export GIT_HTTP_EXTRA_HEADER="AUTHORIZATION: basic $(printf "x-access-token:%s" "$PAT" | base64 -w0)"
  export GIT_TERMINAL_PROMPT=0
  export out rig PAT TEACHER_MODEL N AUTOTRAIN_DIR NO_AI

  # We use a helper function to wrap the logic for a single repo
  pipeline_worker() {
    local bucket="$1" out_dir="$2" repo_full="$3" base_dir="$4" pat="$5"
    local name="${repo_full##*/}"
    local target="$base_dir/$name"
    local worker_start=$(date +%s)

    # Setup proxy for this specific worker task
    setup_proxy || true

    # 1. Clone
    if [[ ! -d "$target/.git" ]]; then
      heartbeat
      progress_bar 0 1 "$repo_full" "cloning" "$worker_start"
      log_event "generating" "Cloning $repo_full..."
      # Use the proxy if configured
      # Wrap in with_retry and with_heartbeat
      if ! with_heartbeat with_retry "git clone $repo_full" git ${GIT_CONF_PROXY:-} clone --depth 1 --filter=blob:none --no-tags --single-branch \
        "https://github.com/$repo_full.git" "$target" >/dev/null 2>&1; then
          log_event "generating" "Clone failed for $repo_full"
          echo "[fail] clone $repo_full" >&2;
          return 1;
      fi
      log_event "generating" "Clone success: $repo_full"
      # increment cloned repo counter so dashboard can show progress
      update_state_count "repos_cloned"
    fi

    # 2. Process
    (
      cd "$target"
      if [[ "${NO_AI:-0}" -eq 1 ]]; then
        log_event "generating" "Skipping Copilot generation for $repo_full (no-ai)"
        echo "[skip] generation disabled for $repo_full"
      else
        heartbeat
        progress_bar 0 1 "$repo_full" "enhancing" "$worker_start"
        if with_heartbeat run_copilot_bucket "$bucket" "$out_dir" "$repo_full" "$name"; then
          echo "[ok] processed $repo_full"
          progress_bar 1 1 "$repo_full" "done" "$worker_start"
        else
          echo "[fail] process $repo_full" >&2
          progress_bar 0 1 "$repo_full" "failed" "$worker_start"
        fi
      fi
    )
    echo "" >&2

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

  stop_watchdog
  unset GIT_HTTP_EXTRA_HEADER
}

main "$@"
