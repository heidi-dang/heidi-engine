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
  local filled=$(( pct * width / 100 ))
  local empty=$(( width - filled ))
  printf "\r│ Progress: %d/%d (%s%%) │ %s" \
    "$cur" "$total" "$pct" "$label"
}

progress_done(){ printf " │ Complete\n"; }

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

install_gh_cli_if_missing() {
  if command -v gh >/dev/null 2>&1; then return 0; fi
  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg >/dev/null
  sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null
  sudo apt-get update -y
  sudo apt-get install -y gh
}

install_copilot_ext() {
  if gh extension list 2>/dev/null | awk '{print $1}' | grep -qx "gh-copilot"; then return 0; fi
  gh extension install github/gh-copilot
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

# write a JSONL record (NOT the copilot JSON) for provenance/debug
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

# extract the first JSON object from arbitrary text (best-effort, non-recursive)
extract_first_json_obj() {
  python3 - <<'PY'
import sys, json
s=sys.stdin.read()
# Find first '{' and then attempt to balance braces ignoring strings.
start=s.find('{')
if start==-1:
  sys.exit(1)
i=start
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

# -------- GitHub Search helpers (rate-limit aware) --------
gh_search_page() {
  local token="$1" q="$2" sort="$3" page="$4"

  local url="https://api.github.com/search/repositories?q=$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))' "$q")&sort=$sort&order=desc&per_page=100&page=$page"
  local attempt status remaining reset_at now sleep_for

  for attempt in 1 2 3 4 5; do
    rm -f /tmp/gh_headers.$$ || true
    local resp=""
    resp="$(curl -fsSL -D /tmp/gh_headers.$$ \
      -H "Authorization: Bearer $token" \
      -H "Accept: application/vnd.github+json" \
      "$url" 2>/dev/null || true)"

    status="$(head -n 1 /tmp/gh_headers.$$ 2>/dev/null | awk '{print $2}' || true)"
    remaining="$(grep -i '^x-ratelimit-remaining:' /tmp/gh_headers.$$ 2>/dev/null | awk '{print $2}' | tr -d '\r' || true)"
    reset_at="$(grep -i '^x-ratelimit-reset:' /tmp/gh_headers.$$ 2>/dev/null | awk '{print $2}' | tr -d '\r' || true)"

    if [[ "$status" == "200" && -n "$resp" ]]; then
      echo "$resp"
      rm -f /tmp/gh_headers.$$ || true
      return 0
    fi

    # Secondary rate limits can also return 403 with message content.
    if [[ "$status" == "403" || "${remaining:-1}" == "0" ]]; then
      now="$(date +%s)"
      if [[ -n "${reset_at:-}" && "${reset_at:-0}" -gt "$now" ]]; then
        sleep_for=$(( reset_at - now + 2 ))
        (( sleep_for > 120 )) && sleep_for=120
      else
        sleep_for=30
      fi
      echo "Rate limited (status=$status remaining=${remaining:-?}). Sleeping ${sleep_for}s..." >&2
      sleep "$sleep_for"
      continue
    fi

    echo "GitHub search failed (status=${status:-?}) attempt=$attempt; retrying in 5s..." >&2
    sleep 5
  done

  rm -f /tmp/gh_headers.$$ || true
  return 1
}

build_repo_pool() {
  local token="$1" n="$2" q_lang="$3" out="$4"
  local target_pool=$(( n * 12 ))
  (( target_pool < 600 )) && target_pool=600
  (( target_pool > 2400 )) && target_pool=2400
  local pages=$(( (target_pool + 99) / 100 ))
  (( pages < 3 )) && pages=3
  (( pages > 10 )) && pages=10

  local q_base="stars:>50 fork:false archived:false"
  [[ -n "$q_lang" ]] && q_base="$q_base language:$q_lang"

  : > "$out.pool"
  local total_steps=$(( pages * 2 ))
  local step=0
  for p in $(seq 1 "$pages"); do
    step=$((step+1))
    progress_bar "$step" "$total_steps" "pool: page $p/$pages (sort=stars)"
    gh_search_page "$token" "$q_base" "stars" "$p" | jq -r '.items[].full_name' >> "$out.pool" || true
  done
  for p in $(seq 1 "$pages"); do
    step=$((step+1))
    progress_bar "$step" "$total_steps" "pool: page $p/$pages (sort=forks)"
    gh_search_page "$token" "$q_base" "forks" "$p" | jq -r '.items[].full_name' >> "$out.pool" || true
  done
  progress_done

  progress_bar 1 1 "pool: dedupe+shuffle"
  sort -u "$out.pool" | shuf -n "$n" > "$out"
  progress_done
  rm -f "$out.pool"
}

# -------- Copilot bucket runner --------
run_copilot_bucket() {
  local bucket="$1" out_dir="$2" repo_full="$3" repo_dir="$4"

  local samples="$out_dir/samples.jsonl"
  local hashes="$out_dir/hashes.txt"
  local raw_dir="$out_dir/raw/$repo_dir"
  safe_mkdir "$raw_dir"
  touch "$samples" "$hashes"

  # Bucket sanity filter to reduce noisy samples.
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

  # Capture stderr too (Copilot sometimes prints useful errors there).
  local resp=""
  if ! resp="$(gh copilot suggest -t shell "$prompt" 2>&1)"; then
    printf "%s\n" "$resp" > "$raw_out"
    echo "copilot error: $repo_full" >&2
    return 1
  fi
  printf "%s\n" "$resp" > "$raw_out"

  # Best-effort: extract first valid JSON object from copilot output.
  local json=""
  if ! json="$(printf "%s" "$resp" | extract_first_json_obj 2>/dev/null || true)"; then
    # still store provenance record for debugging, but mark response as raw
    write_jsonl "$samples" "$bucket" "$repo_full" "$repo_dir" "$prompt" "$resp"
    echo "invalid json (no parsable object): $repo_full" >&2
    return 1
  fi

  if ! json_is_valid "$json"; then
    write_jsonl "$samples" "$bucket" "$repo_full" "$repo_dir" "$prompt" "$resp"
    echo "invalid json (parse fail): $repo_full" >&2
    return 1
  fi

  # Deduplicate by content hash (prevents entropy collapse).
  local h
  h="$(printf "%s" "$json" | sha256sum | awk '{print $1}')"
  if grep -qx "$h" "$hashes" 2>/dev/null; then
    echo "dup sample (hash): $repo_full" >&2
    return 0
  fi
  echo "$h" >> "$hashes"

  # Store a structured record (prompt+raw response) for provenance.
  write_jsonl "$samples" "$bucket" "$repo_full" "$repo_dir" "$prompt" "$resp"
  # Also store the extracted clean JSON alongside for easy training ingestion.
  printf "%s\n" "$json" >> "$out_dir/clean_samples.jsonl"

  return 0
}

usage() {
  cat <<EOF
Usage: $0 [--repos N] [--reclone] [--parallel P] [--fresh] [--nice]

Options:
  --repos N       repos per bucket (default: 50)
  --reclone       force delete+reclone existing repo dirs (default: skip existing)
  --parallel P    parallel workers per bucket (default: 4)
  --fresh         wipe outputs for this rig (default: resume/append)
  --nice          run with lower CPU/IO priority (nice + ionice if available)
EOF
}

main() {
  local N=50
  local RECLONE=0
  local PAR=4
  local FRESH=0
  local DO_NICE=0

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --repos) shift; [[ $# -gt 0 ]] || die "--repos requires N"; N="$1";;
      --reclone) RECLONE=1;;
      --parallel) shift; [[ $# -gt 0 ]] || die "--parallel requires P"; PAR="$1";;
      --fresh) FRESH=1;;
      --nice) DO_NICE=1;;
      -h|--help) usage; exit 0;;
      *) die "Unknown arg: $1";;
    esac
    shift || true
  done

  need_cmd sudo
  need_cmd sha256sum
  echo "=== Local Copilot training rig (language-filtered) ==="
  echo "Repos per bucket: $N   Reclone: $RECLONE   Parallel: $PAR   Fresh: $FRESH"

  if [[ "$DO_NICE" -eq 1 ]]; then
    nice -n 10 true 2>/dev/null || true
    if command -v ionice >/dev/null 2>&1; then
      ionice -c2 -n7 -p $$ >/dev/null 2>&1 || true
    fi
  fi

  echo "[1/7] Install base dependencies..."
  apt_install_base

  echo "[2/7] Install GitHub CLI if missing..."
  install_gh_cli_if_missing

  echo "[3/7] Authenticate GitHub CLI (OAuth) for Copilot..."
  gh auth status >/dev/null 2>&1 || gh auth login --web

  echo "[4/7] Install Copilot extension..."
  install_copilot_ext
  gh copilot --help >/dev/null 2>&1 || die "gh copilot not working. Check Copilot entitlement."

  echo
  local rig=""
  read -r -p "Enter your rig name (folder under model_training_output/): " rig
  [[ -n "$rig" ]] || die "rig name cannot be empty"

  local base="$HOME/heidi_repos"
  safe_mkdir "$base"
  cd "$base"

  local out="model_training_output/$rig"
  safe_mkdir "$out"
  for b in python cpp github; do
    safe_mkdir "$out/$b"
    safe_mkdir "$out/$b/raw"
    touch "$out/$b/samples.jsonl"
    touch "$out/$b/clean_samples.jsonl"
    touch "$out/$b/hashes.txt"
  done

  if [[ "$FRESH" -eq 1 ]]; then
    echo "Fresh mode: wiping rig outputs under $out"
    for b in python cpp github; do
      : > "$out/$b/samples.jsonl"
      : > "$out/$b/clean_samples.jsonl"
      : > "$out/$b/hashes.txt"
      rm -rf "$out/$b/raw" && safe_mkdir "$out/$b/raw"
    done
  fi

  echo
  echo "[5/7] GitHub PAT for Search API + cloning (hidden input, not stored)..."
  local PAT=""
  prompt_hidden PAT "GITHUB PAT: "

  echo "[6/7] Selecting repos (stars+forks sorted pools -> shuffle -> take N)"
  echo "  - python: language:Python"
  build_repo_pool "$PAT" "$N" "Python" "repos_python.txt"
  echo "  - cpp: language:C++"
  build_repo_pool "$PAT" "$N" "C++" "repos_cpp.txt"
  echo "  - github: no language filter (popular repos)"
  build_repo_pool "$PAT" "$N" "" "repos_github.txt"

  echo "Cloning repos (depth=1, blobless, no-tags)..."
  # Maximise clone resilience on slow/spotty links:
  # - disable low-speed aborts
  # - large HTTP buffers
  # - keep progress visible
  # - bounded retries
  clone_repo() {
    local repo_full="$1" dir="$2"
    local url="https://github.com/$repo_full.git"
    local attempt
    for attempt in 1 2 3; do
      rm -rf "$dir"/.git 2>/dev/null || true
      # Note: --filter=blob:none requires partial clone support (GitHub supports it)
      if git \
        -c http.lowSpeedLimit=0 \
        -c http.lowSpeedTime=999999 \
        -c http.postBuffer=524288000 \
        -c http.maxRequestBuffer=100M \
        clone --progress --depth 1 --filter=blob:none --no-tags "$url" "$dir"; then
        return 0
      fi
      echo "clone retry $attempt/3 failed: $repo_full" >&2
      rm -rf "$dir" 2>/dev/null || true
      sleep $(( attempt * 2 ))
    done
    return 1
  }

  export GIT_HTTP_EXTRA_HEADER="AUTHORIZATION: basic $(printf "x-access-token:%s" "$PAT" | base64 -w0)"

  local total_repos=0
  total_repos=$(( $(wc -l < repos_python.txt 2>/dev/null || echo 0) + $(wc -l < repos_cpp.txt 2>/dev/null || echo 0) + $(wc -l < repos_github.txt 2>/dev/null || echo 0) ))
  (( total_repos > 0 )) || total_repos=1

  local done_repos=0
  local clone_ok=0
  local clone_fail=0

  for list in repos_python.txt repos_cpp.txt repos_github.txt; do
    while read -r repo; do
      [[ -n "$repo" ]] || continue
      local dir="${repo##*/}"
      if [[ -d "$dir/.git" ]]; then
        if [[ "$RECLONE" -eq 1 ]]; then
          echo "reclone $repo"
          rm -rf "$dir"
        else
          done_repos=$((done_repos+1))
          progress_bar "$done_repos" "$total_repos" "clone: skip existing ($repo)"
          continue
        fi
      fi
      done_repos=$((done_repos+1))
      progress_bar "$done_repos" "$total_repos" "clone: $repo"
      if clone_repo "$repo" "$dir" >/dev/null 2>&1; then
        clone_ok=$((clone_ok+1))
      else
        clone_fail=$((clone_fail+1))
        echo "\nclone failed (after retries): $repo" >&2
      fi
    done < "$list"
  done
  progress_done
  echo "Clone summary: ok=$clone_ok failed=$clone_fail total=$total_repos"
  unset GIT_HTTP_EXTRA_HEADER
  unset PAT

  echo "[7/7] Running Copilot loops..."
  local SUCCESS=0
  local FAIL=0

  run_list_parallel() {
    local bucket="$1" out_dir="$2" list_file="$3"
    export -f die need_cmd timestamp prompt_hidden safe_mkdir detect_repo_hints bucket_repo_ok json_is_valid write_jsonl extract_first_json_obj run_copilot_bucket
    export bucket out_dir
    cat "$list_file" | xargs -P "$PAR" -I{} bash -c '
      repo="{}"
      dir="${repo##*/}"
      [[ -d "$dir" ]] || exit 0
      echo "==== $repo ===="
      if (cd "$dir" && run_copilot_bucket "'"$bucket"'" "'"$out_dir"'" "$repo" "$dir"); then
        exit 0
      else
        exit 1
      fi
    '
  }

  echo "  - python bucket over repos_python.txt"
  if run_list_parallel "python" "$out/python" "repos_python.txt"; then SUCCESS=$((SUCCESS+1)); else FAIL=$((FAIL+1)); fi

  echo "  - cpp bucket over repos_cpp.txt"
  if run_list_parallel "cpp" "$out/cpp" "repos_cpp.txt"; then SUCCESS=$((SUCCESS+1)); else FAIL=$((FAIL+1)); fi

  echo "  - github bucket over repos_github.txt"
  if run_list_parallel "github" "$out/github" "repos_github.txt"; then SUCCESS=$((SUCCESS+1)); else FAIL=$((FAIL+1)); fi

  echo
  echo "DONE. Outputs:"
  echo "  $base/$out/python/samples.jsonl        (provenance records)"
  echo "  $base/$out/python/clean_samples.jsonl  (extracted JSON objects)"
  echo "  $base/$out/cpp/samples.jsonl"
  echo "  $base/$out/cpp/clean_samples.jsonl"
  echo "  $base/$out/github/samples.jsonl"
  echo "  $base/$out/github/clean_samples.jsonl"
  echo
  echo "Repo lists saved:"
  echo "  $base/repos_python.txt"
  echo "  $base/repos_cpp.txt"
  echo "  $base/repos_github.txt"
  echo
  echo "Rig summary:"
  echo "  Buckets ok: $SUCCESS"
  echo "  Buckets with errors: $FAIL"
}

main "$@"
