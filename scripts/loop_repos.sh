#!/usr/bin/env bash
set -e
set -u
set -o pipefail

# loop_repos.sh - Run the pipeline across multiple repositories
#
# Usage examples:
#  # Run on repos listed in a file (one URL or local path per line)
#  ./scripts/loop_repos.sh --repos-file repos.txt --samples 10 --rounds 1
#
#  # Search GitHub and run on top 5 results (requires GITHUB_TOKEN if rate-limited)
#  ./scripts/loop_repos.sh --gh-query "language:python stars:>100" --max 5 --samples 10
#
# New features:
#  --sort FIELD    GitHub sort field (stars, forks, updated, help-wanted-issues)
#  --order DIR     Sort direction (desc for highest to lowest, asc for lowest to highest)
#  --random        Shuffle fetched repos for random selection
#  --until-samples N  Loop fetching/processing more repos until total cleaned samples >= N

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

REPOS_FILE=""
GH_QUERY=""
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
MAX_REPOS=10
OUT_BASE="./autotrain_repos"
SAMPLES=50
MAX_REQUESTS="${MAX_REQUESTS:-1000}"
ROUNDS=1
PIPELINE_MODE="collect"
SORT=""
ORDER=""
DO_RANDOM=false
UNTIL_SAMPLES=0
ASSISTANT_MODE=false
RESUME=false
STACK=""
VAL_RATIO="${VAL_RATIO:-0.05}"
SLEEP_BETWEEN_REQUESTS="${SLEEP_BETWEEN_REQUESTS:-0}"
OPTUNA=false
N_TRIALS=10
DO_DEDUPE=false
PUSH_TO_HUB=""
USE_GOLDEN=false
TEACHER_BACKEND="${TEACHER_BACKEND:-}"
TEACHER_MODEL_OVERRIDE="${TEACHER_MODEL:-}"
OPENHEI_ATTACH_OVERRIDE="${OPENHEI_ATTACH:-}"
OPENHEI_AGENT_OVERRIDE="${OPENHEI_AGENT:-}"

print_usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --repos-file FILE    File with one repo URL or local path per line
  --gh-query QUERY     GitHub search query (uses Search API)
  --stack STACK        Preset stack to query (python, cpp, vite, web)
  --token TOKEN        GitHub token (or set GITHUB_TOKEN env var)
  --max N              Max repos to process (default: $MAX_REPOS)
  --out-dir DIR        Base output directory (default: $OUT_BASE)
  --samples N          Samples per round (default: $SAMPLES)
  --rounds N           Rounds per repo (default: $ROUNDS)
  --collect            Run in collect mode (skip training)
  --full               Run in full mode (include training)
  --sort FIELD         GitHub sort (stars, forks, updated, help-wanted-issues)
  --order DIR          Sort direction (desc: highest to lowest, asc: lowest to highest)
  --random             Shuffle repos for random selection
  --until-samples N    Loop until total cleaned samples >= N (requires --gh-query)
  --resume             Skip repositories that have already been processed
  --golden             Inject curated "golden" repositories for the selected stack
  --dedupe             Run global deduplication after processing
  --push-to-hub REPO   Run deduplication and push merged dataset to Hugging Face Hub (implies --dedupe)
  --val-ratio RATIO    Validation split ratio (default: $VAL_RATIO)
  --sleep SECONDS      Sleep between API requests (default: $SLEEP_BETWEEN_REQUESTS)
  --monitor URL        Stream status to central dashboard (e.g. http://192.168.1.10:7779)
  --assistant          Run in assistant mode (uses code-assistant RUN_ID)
  --teacher-backend B  Teacher backend (legacy|openhei)
  --teacher-model M    Teacher model (for openhei: provider/model)
  --openhei-attach U   Attach URL (e.g. http://127.0.0.1:4096)
  --openhei-agent A    OpenHei agent name (default: general)
  --optuna             Enable Hyperparameter Optimization for training
  --n-trials N         Number of HPO trials (default: 10)
  --help               Show this help

Examples:
  $0 --stack python --max 5 --samples 10
  $0 --repos-file my_repos.txt --samples 10 --rounds 1
  $0 --gh-query "language:python stars:>500" --max 5 --token <token> --sort stars --order desc
  $0 --gh-query "language:python" --random --until-samples 1000
EOF
}

# Helper to ensure argument value exists
check_arg() {
    if [ -z "${2:-}" ] || [[ "${2:-}" == --* ]]; then
        echo "Error: Argument $1 requires a value." >&2
        exit 1
    fi
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --repos-file)
            check_arg "$1" "$2"; REPOS_FILE="$2"; shift 2;;
        --gh-query)
            check_arg "$1" "$2"; GH_QUERY="$2"; shift 2;;
        --stack)
            check_arg "$1" "$2"; STACK="$2"; shift 2;;
        --token)
            check_arg "$1" "$2"; GITHUB_TOKEN="$2"; shift 2;;
        --max)
            check_arg "$1" "$2"; MAX_REPOS="$2"; shift 2;;
        --out-dir)
            check_arg "$1" "$2"; OUT_BASE="$2"; shift 2;;
        --samples)
            check_arg "$1" "$2"; SAMPLES="$2"; shift 2;;
        --rounds)
            check_arg "$1" "$2"; ROUNDS="$2"; shift 2;;
        --max-requests)
            check_arg "$1" "$2"; MAX_REQUESTS="$2"; shift 2;;
        --collect)
            PIPELINE_MODE="collect"; shift;;
        --full)
            PIPELINE_MODE="full"; shift;;
        --sort)
            check_arg "$1" "$2"; SORT="$2"; shift 2;;
        --order)
            check_arg "$1" "$2"; ORDER="$2"; shift 2;;
        --random)
            DO_RANDOM=true; shift;;
        --until-samples)
            check_arg "$1" "$2"; UNTIL_SAMPLES="$2"; shift 2;;
        --resume)
            RESUME=true; shift;;
        --golden)
            USE_GOLDEN=true; shift;;
        --dedupe)
            DO_DEDUPE=true; shift;;
        --push-to-hub)
            check_arg "$1" "$2"; PUSH_TO_HUB="$2"; shift 2;;
        --val-ratio)
            check_arg "$1" "$2"; export VAL_RATIO="$2"; shift 2;;
        --sleep)
            check_arg "$1" "$2"; export SLEEP_BETWEEN_REQUESTS="$2"; shift 2;;
        --monitor)
            check_arg "$1" "$2"; export DASHBOARD_URL="$2"; shift 2;;
        --assistant)
            ASSISTANT_MODE=true; shift;;
        --teacher-backend)
            check_arg "$1" "$2"; TEACHER_BACKEND="$2"; shift 2;;
        --teacher-model)
            check_arg "$1" "$2"; TEACHER_MODEL_OVERRIDE="$2"; shift 2;;
        --openhei-attach)
            check_arg "$1" "$2"; OPENHEI_ATTACH_OVERRIDE="$2"; shift 2;;
        --openhei-agent)
            check_arg "$1" "$2"; OPENHEI_AGENT_OVERRIDE="$2"; shift 2;;
        --optuna)
            OPTUNA=true; shift;;
        --n-trials)
            check_arg "$1" "$2"; N_TRIALS="$2"; shift 2;;
        --help|-h)
            print_usage; exit 0;;
        *)
            echo "Unknown option: $1"; print_usage; exit 1;;
    esac
done

# Source common configurations if available
if [ -f "$SCRIPT_DIR/common.sh" ]; then
    source "$SCRIPT_DIR/common.sh"
    apply_git_optimizations
fi

# Auto-discovery for Docker/Multi-machine
if [ -z "${DASHBOARD_URL:-}" ] && [ -n "${DASHBOARD_HOST:-}" ]; then
    export DASHBOARD_URL="$DASHBOARD_HOST"
    echo "[INFO] Auto-discovered dashboard at: $DASHBOARD_URL"
fi

if [ -n "$STACK" ]; then
    # Default license filter for stacks
    license_filter="license:mit"
    
    case "$STACK" in
        python)
            stack_query="language:python stars:>100 $license_filter"
            export LANGUAGE="python"
            ;;
        cpp)
            stack_query="language:cpp stars:>100 $license_filter"
            export LANGUAGE="cpp"
            ;;
        go)
            stack_query="language:go stars:>100 $license_filter"
            export LANGUAGE="go"
            ;;
        vite)
            stack_query="vite in:name,description,readme stars:>100 $license_filter"
            export LANGUAGE="javascript"
            ;;
        web)
            # broad web query
            stack_query="(language:typescript OR language:javascript) stars:>100 $license_filter"
            export LANGUAGE="javascript"
            ;;
        *)
            echo "Error: Unknown stack '$STACK'. Supported: python, cpp, go, vite, web" >&2
            exit 1
            ;;
    esac

    if [ "$USE_GOLDEN" = true ]; then
        case "$STACK" in
            python) golden_repos=("pallets/flask" "psf/requests" "numpy/numpy" "pandas-dev/pandas" "django/django") ;;
            cpp)    golden_repos=("pytorch/pytorch" "tensorflow/tensorflow" "bitcoin/bitcoin" "opencv/opencv") ;;
            vite)   golden_repos=("vitejs/vite" "vitest-dev/vitest" "vuejs/core" "sveltejs/svelte") ;;
            web)    golden_repos=("facebook/react" "vuejs/vue" "angular/angular" "vercel/next.js") ;;
        esac
        if [ -n "${golden_repos:-}" ]; then
            echo "[INFO] Adding golden repos: ${golden_repos[*]}"
            for r in "${golden_repos[@]}"; do
                repo_url="https://github.com/$r.git"
                repos+=("$repo_url")
            done
        fi
    fi

    if [ -n "$GH_QUERY" ]; then
        GH_QUERY="$stack_query $GH_QUERY"
    else
        GH_QUERY="$stack_query"
    fi
fi

if [ -n "$GH_QUERY" ]; then
    echo "Using GitHub Query: $GH_QUERY"
fi

mkdir -p "$OUT_BASE"

repos=()

if [ -n "$REPOS_FILE" ]; then
    if [ ! -f "$REPOS_FILE" ]; then
        echo "Repos file not found: $REPOS_FILE" >&2
        exit 1
    fi
    while IFS= read -r line || [ -n "$line" ]; do
        line_trimmed="$(echo "$line" | sed -e 's/^\s*//' -e 's/\s*$//')"
        [ -z "$line_trimmed" ] && continue
        repos+=("$line_trimmed")
    done < "$REPOS_FILE"
fi

# -------- tiny progress UI (no extra deps) --------
# Displays a single-line progress indicator
progress_bar() {
  if [[ "${HEIDI_PROGRESS:-1}" -eq 0 ]]; then return 0; fi

  local cur="$1" total="$2" repo="${3:-}" stage="${4:-}" start_time="${5:-$(date +%s)}"
  local now; now=$(date +%s)
  local elapsed=$(( now - start_time ))

  (( total > 0 )) || total=1
  (( cur < 0 )) && cur=0
  (( cur > total )) && cur=$total

  local pct=$(( cur * 100 / total ))

  # Detect if stdout is a TTY for \r usage
  if [[ -t 2 ]]; then
    printf "\r[PROG] %d/%d (%d%%) | %s | %s | %ds    " "$cur" "$total" "$pct" "$repo" "$stage" "$elapsed" >&2
  else
    # Non-interactive: print plain log line every 5% or if finished
    if (( cur % (total / 20 + 1) == 0 )) || (( cur == total )); then
      echo "[PROG] $cur/$total ($pct%) | $repo | $stage | ${elapsed}s" >&2
    fi
  fi
}

# Function to fetch next batch of repos from GitHub
fetch_repos() {
    local per_page=30
    if $DO_RANDOM; then per_page=100; fi  # Larger pool for shuffling
    local max_retries=3
    local retry_delay=60
    
    for ((i=0; i<max_retries; i++)); do
        resp=$(curl -s -G "https://api.github.com/search/repositories" \
            --data-urlencode "q=$GH_QUERY" \
            --data-urlencode "per_page=$per_page" \
            --data-urlencode "page=$page" \
            --data-urlencode "sort=$SORT" \
            --data-urlencode "order=$ORDER" \
            ${GITHUB_TOKEN:+-H "Authorization: token $GITHUB_TOKEN"})
        
        # Check for rate limit message or empty response
        if echo "$resp" | grep -q "API rate limit exceeded"; then
             echo "[WARN] GitHub API rate limit exceeded. Sleeping ${retry_delay}s..." >&2
             sleep "$retry_delay"
             continue
        fi
        
        local items=$(echo "$resp" | jq -r '.items[]?.clone_url' 2>/dev/null)
        if [ $? -eq 0 ]; then
             if [ -z "$items" ]; then
                 # Could be end of results or error
                 message=$(echo "$resp" | jq -r '.message' 2>/dev/null)
                 if [ -n "$message" ] && [ "$message" != "null" ]; then
                     echo "[WARN] GitHub API error: $message" >&2
                     # If error is not rate limit but client error, maybe break? 
                     # But for robustness, we return 1 to stop fetching.
                 fi
                 return 1
             fi
             
             # Success
             if $DO_RANDOM; then
                 items=$(echo "$items" | shuf)
             fi

             while IFS= read -r url; do
                 repos+=("$url")
             done <<< "$items"

             page=$((page + 1))
             return 0
        else
             echo "[WARN] Failed to parse GitHub response. Retrying..." >&2
             sleep 5
        fi
    done
    
    echo "[ERROR] Failed to fetch repos after $max_retries attempts." >&2
    return 1
}

if [ -n "$GH_QUERY" ]; then
    if ! command -v curl >/dev/null 2>&1 || ! command -v jq >/dev/null 2>&1; then
        echo "curl and jq are required for GitHub search" >&2
        exit 1
    fi

    page=1
    if [ $UNTIL_SAMPLES -eq 0 ]; then
        # Fetch all at once up to max
        while [ ${#repos[@]} -lt "$MAX_REPOS" ] && fetch_repos; do :; done
    fi  # For until, fetch incrementally in the loop below
fi

if [ ${#repos[@]} -eq 0 ] && [ $UNTIL_SAMPLES -eq 0 ]; then
    echo "No repositories found. Provide --repos-file or --gh-query." >&2
    exit 1
fi

# Limit initial repos if not until
if [ $UNTIL_SAMPLES -eq 0 ]; then
    repos=("${repos[@]:0:$MAX_REPOS}")
fi

repos_count=${#repos[@]}
echo "Initial repos: ${repos_count}"

# Compute safe samples per repo so total requests <= MAX_REQUESTS
if [ -n "$MAX_REQUESTS" ] && [ "$MAX_REQUESTS" -gt 0 ]; then
    # Use estimated repos_count (or MAX_REPOS if until)
    est_repos=$([ $UNTIL_SAMPLES -gt 0 ] && echo $MAX_REPOS || echo $repos_count)
    denom=$(( est_repos * ROUNDS ))
    if [ $denom -le 0 ]; then denom=1; fi
    safe_samples=$(( MAX_REQUESTS / denom ))
    if [ $safe_samples -lt 1 ]; then
        safe_samples=1
        echo "[WARN] MAX_REQUESTS too small; using 1 sample per round" >&2
    fi
    echo "[INFO] Adjusting samples to $safe_samples to respect MAX_REQUESTS=$MAX_REQUESTS" >&2
    SAMPLES=$safe_samples
fi

# Main processing loop
idx=0
processed=0
start_time=$(date +%s)

# Start global watchdog
start_watchdog "Initial pool creation" "/tmp/heidi_run.log"

while true; do
    heartbeat
    progress_bar "$processed" "$repos_count" "${repo:-}" "running" "$start_time"
    # If until and no more repos fetched, fetch more
    if [ $UNTIL_SAMPLES -gt 0 ] && [ $processed -ge ${#repos[@]} ] && [ -n "$GH_QUERY" ]; then
        if ! fetch_repos; then
            echo "[INFO] No more repos available from GitHub."
            break
        fi
    fi

    # Process next repo
    if [ $processed -ge ${#repos[@]} ]; then
        # No more to process
        break
    fi

    repo="${repos[$processed]}"
    processed=$((processed + 1))
    idx=$((idx + 1))
    if [ $UNTIL_SAMPLES -eq 0 ] && [ $idx -gt $MAX_REPOS ]; then break; fi

    # Normalize name
    name=$(basename "$repo" .git)
    owner=$(basename "$(dirname "$repo")") || owner="local"
    safe_name="${owner}_${name}"
    target_dir="$OUT_BASE/$safe_name"

    # Resume check
    if [ "$RESUME" = true ]; then
        if [ -d "$target_dir" ] && [ -f "$target_dir/.done" ]; then
             echo "[RESUME] Skipping processed repo: $safe_name"
             continue
        fi
    fi

    echo "\n--- ($idx) Processing: $repo -> $target_dir ---"
    echo "[INFO] Repo $idx/$repos_count: $safe_name (rounds=$ROUNDS)"

    if [[ "$repo" =~ ^https?:// ]] || [[ "$repo" =~ \.git$ ]]; then
        # Resilient Cloning: partial + shallow + progress
        if [ -d "$target_dir/.git" ]; then
            echo "Repository already cloned: $target_dir (pulling latest)"
            # For existing clones, we try to pull but don't fail if it doesn't work
            git -C "$target_dir" pull --quiet || true
        else
            echo "Cloning repository: $repo"
            heartbeat
            progress_bar "$processed" "$repos_count" "$repo" "cloning" "$start_time"
            # Switch to partial + shallow clone by default
            # --filter=blob:none avoids downloading blobs until needed
            # --depth=1 keeps history minimal
            # --no-tags avoids extra overhead
            with_heartbeat git clone --filter=blob:none --depth=1 --no-tags --progress "$repo" "$target_dir" || {
              echo "[ERROR] Clone failed for $repo" >&2
              # Fail-open: continue to next repo
              continue
            }
        fi
    else
        # assume local path
        if [ -d "$repo" ]; then
            echo "Copying local repository: $repo -> $target_dir"
            mkdir -p "$target_dir"
            cp -r "$repo/." "$target_dir/"
        else
            echo "Local path not found: $repo" >&2
            continue
        fi
    fi

    # ... [Filters] ...

    # --- QUALITY FILTERS ---

    # 1. Homework/Assignment Check
    if [ -f "$target_dir/README.md" ]; then
        if grep -qiE "assignment|homework|course work|lab report|university|college|school project" "$target_dir/README.md"; then
             echo "[SKIP] Repo '$safe_name' looks like a homework assignment."
             rm -rf "$target_dir"
             continue
        fi
    fi

    # 2. File Filtering (Extensions & Size)
    # Define extensions based on stack if not set
    if [ -z "${EXTENSIONS:-}" ]; then
        case "$STACK" in
            python) EXTENSIONS="py,ipynb" ;;
            cpp)    EXTENSIONS="cpp,c,h,hpp,cc" ;;
            vite)   EXTENSIONS="ts,tsx,js,jsx,vue,svelte,css,html" ;;
            web)    EXTENSIONS="ts,tsx,js,jsx,html,css" ;;
            *)      EXTENSIONS="py,cpp,c,h,js,ts,tsx,jsx,java,go,rs" ;; # Default broad
        esac
    fi

    # Convert comma-separated extensions to find logic
    # e.g., py,cpp -> \( -name "*.py" -o -name "*.cpp" \)
    find_ext_args="\\( -name \"*.$(echo "$EXTENSIONS" | sed 's/,/" -o -name "*./g')\" \\)"
    
    MIN_SIZE_BYTES="${MIN_SIZE_BYTES:-100}"       # Skip empty/tiny files
    MAX_SIZE_BYTES="${MAX_SIZE_BYTES:-1048576}"   # Skip >1MB files
    
    echo "Cleaning '$target_dir' (keeping: $EXTENSIONS, size: $MIN_SIZE_BYTES-$MAX_SIZE_BYTES bytes)..."
    
    # We want to DELETE files that do NOT match the criteria
    # It's safer to find matching files and move them, OR find non-matching and delete.
    # Approach: Find ALL files. Loop and check. Slow but reliable in bash.
    # OR: Use 'find' to delete everything that is NOT a directory and NOT in the keep list.
    
    # Let's try to construct the 'keep' expression
    # find . -type f -not \( \( -name "*.py" -o -name "*.cpp" \) -a -size +100c -a -size -1M \) -delete
    
    # Construct extension clause: \( -name "*.py" -o -name "*.cpp" \)
    ext_clause="\\( -name \"*.${EXTENSIONS//,/\" -o -name \"*.}\" \\)"
    
    # Execute cleanup
    # We use 'eval' here because of the dynamic construction of args, watching out for injection (EXTENSIONS is internal/controlled)
    find_cmd="find \"$target_dir\" -type f -not \\( $ext_clause -a -size +${MIN_SIZE_BYTES}c -a -size -${MAX_SIZE_BYTES}c \\) -not -path \"*/.git/*\" -delete"
    
    # echo "Running: $find_cmd"
    eval "$find_cmd"
    
    # Remove empty directories
    find "$target_dir" -type d -empty -delete
    
    # Check if empty after cleanup
    if [ -z "$(ls -A "$target_dir")" ]; then
         echo "[SKIP] Repo '$safe_name' is empty after filtering."
         rm -rf "$target_dir"
         continue
    fi
    
    # --- END FILTERS ---

    # Run pipeline for this repo (collect by default)
    if [ "$ASSISTANT_MODE" = true ]; then
        RUN_ID="code-assistant"
    else
        RUN_ID="run_${safe_name}_$(date +%s)"
    fi
    export RUN_ID
    export OUT_DIR="$OUT_BASE/$safe_name"
    export PIPELINE_MODE="$PIPELINE_MODE"

    if [ -n "${TEACHER_BACKEND:-}" ]; then
        export TEACHER_BACKEND
    fi
    if [ -n "${TEACHER_MODEL_OVERRIDE:-}" ]; then
        export TEACHER_MODEL="$TEACHER_MODEL_OVERRIDE"
    fi
    if [ -n "${OPENHEI_ATTACH_OVERRIDE:-}" ]; then
        export OPENHEI_ATTACH="$OPENHEI_ATTACH_OVERRIDE"
    fi
    if [ -n "${OPENHEI_AGENT_OVERRIDE:-}" ]; then
        export OPENHEI_AGENT="$OPENHEI_AGENT_OVERRIDE"
    fi

    mkdir -p "$OUT_DIR"

    echo "Running pipeline for $safe_name (RUN_ID=$RUN_ID, OUT_DIR=$OUT_DIR)"

    if with_heartbeat bash "$SCRIPT_DIR/loop.sh" --rounds "$ROUNDS" --samples "$SAMPLES" \
        $( [ "$PIPELINE_MODE" = "collect" ] && echo --collect ) \
        $( [ "$OPTUNA" = true ] && echo --optuna ) \
        --n-trials "$N_TRIALS"; then
         touch "$OUT_DIR/.done"
    else
         echo "Pipeline failed for $safe_name"
    fi

    # Check condition if until-samples
    if [ $UNTIL_SAMPLES -gt 0 ]; then
        total_samples=$(find "$OUT_BASE" -name "clean_round_*.jsonl" -exec wc -l {} + | awk '{sum += $1} END {print sum}')
        echo "[INFO] Current total samples: $total_samples"
        if [ "$total_samples" -ge "$UNTIL_SAMPLES" ]; then
            echo "[SUCCESS] Reached target samples ($total_samples >= $UNTIL_SAMPLES). Stopping."
            break
        fi
        echo "[INFO] Target not met; continuing to next repo..."
    fi
done
progress_bar "$processed" "$repos_count" "done" "finished" "$start_time"
echo "" >&2

if [ $UNTIL_SAMPLES -gt 0 ] && [ -z "$GH_QUERY" ]; then
    echo "[WARN] --until-samples used without --gh-query; cannot fetch more repos dynamically."
fi

# --- POST PROCESSING ---

if [ "$DO_DEDUPE" = true ] || [ -n "${PUSH_TO_HUB:-}" ]; then
    echo ""
    echo "=== Running Global Deduplication ==="
    merged_file="$OUT_BASE/merged_dataset.jsonl"
    python3 "$SCRIPT_DIR/global_dedupe.py" --data-dir "$OUT_BASE" --output "$merged_file"
    
    if [ -n "${PUSH_TO_HUB:-}" ]; then
        if [ ! -f "$merged_file" ]; then
             echo "[ERROR] Deduplication failed, cannot push to hub."
        else
             echo ""
             echo "=== Pushing to Hugging Face Hub: $PUSH_TO_HUB ==="
             if ! command -v huggingface-cli >/dev/null; then
                 echo "[ERROR] huggingface-cli not found. Please install 'huggingface_hub'."
             else
                 # Check login?
                 # huggingface-cli upload [repo_id] [local_path] [path_in_repo] --repo-type dataset
                 huggingface-cli upload "$PUSH_TO_HUB" "$merged_file" "train.jsonl" --repo-type dataset
             fi
        fi
    fi
fi

stop_watchdog
echo "All done. Outputs available under: $OUT_BASE"
