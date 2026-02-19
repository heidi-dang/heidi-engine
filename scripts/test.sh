#!/usr/bin/env bash
set -euo pipefail

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
MAX_REQUESTS=50
ROUNDS=1
PIPELINE_MODE="collect"
SORT=""
ORDER=""
DO_RANDOM=false
UNTIL_SAMPLES=0
GENERATOR_MODE=false

print_usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --repos-file FILE    File with one repo URL or local path per line
  --gh-query QUERY     GitHub search query (uses Search API)
  --token TOKEN        GitHub token (or set GITHUB_TOKEN env var)
  --max N              Max repos to process (default: $MAX_REPOS)
  --out-dir DIR        Base output directory (default: $OUT_BASE)
  --samples N          Samples per round (default: $SAMPLES)
  --rounds N           Rounds per repo (default: $ROUNDS)
  --collect            Run in collect mode (skip training)
  --sort FIELD         GitHub sort (stars, forks, updated, help-wanted-issues)
  --order DIR          Sort direction (desc: highest to lowest, asc: lowest to highest)
  --random             Shuffle repos for random selection
  --until-samples N    Loop until total cleaned samples >= N (requires --gh-query)
  --generator          Run in generator mode (uses generator RUN_ID)
  --help               Show this help

Examples:
  $0 --repos-file my_repos.txt --samples 10 --rounds 1
  $0 --gh-query "language:python stars:>500" --max 5 --token <token> --sort stars --order desc
  $0 --gh-query "language:python" --random --until-samples 1000
EOF
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --repos-file)
            REPOS_FILE="$2"; shift 2;;
        --gh-query)
            GH_QUERY="$2"; shift 2;;
        --token)
            GITHUB_TOKEN="$2"; shift 2;;
        --max)
            MAX_REPOS="$2"; shift 2;;
        --out-dir)
            OUT_BASE="$2"; shift 2;;
        --samples)
            SAMPLES="$2"; shift 2;;
        --rounds)
            ROUNDS="$2"; shift 2;;
        --max-requests)
            MAX_REQUESTS="$2"; shift 2;;
        --collect)
            PIPELINE_MODE="collect"; shift;;
        --sort)
            SORT="$2"; shift 2;;
        --order)
            ORDER="$2"; shift 2;;
        --random)
            DO_RANDOM=true; shift;;
        --until-samples)
            UNTIL_SAMPLES="$2"; shift 2;;
        --generator)
            GENERATOR_MODE=true; shift;;
        --help|-h)
            print_usage; exit 0;;
        *)
            echo "Unknown option: $1"; print_usage; exit 1;;
    esac
done

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

# Function to fetch next batch of repos from GitHub
fetch_repos() {
    local per_page=30
    if $DO_RANDOM; then per_page=100; fi  # Larger pool for shuffling

    resp=$(curl -s -G "https://api.github.com/search/repositories" \
        --data-urlencode "q=$GH_QUERY" \
        --data-urlencode "per_page=$per_page" \
        --data-urlencode "page=$page" \
        --data-urlencode "sort=$SORT" \
        --data-urlencode "order=$ORDER" \
        ${GITHUB_TOKEN:+-H "Authorization: token $GITHUB_TOKEN"})

    local items=$(echo "$resp" | jq -r '.items[]?.clone_url')
    if [ -z "$items" ]; then return 1; fi

    if $DO_RANDOM; then
        items=$(echo "$items" | shuf)
    fi

    while IFS= read -r url; do
        repos+=("$url")
    done <<< "$items"

    page=$((page + 1))
    return 0
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
while true; do
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

    echo "\n--- ($idx) Processing: $repo -> $target_dir ---"

    if [[ "$repo" =~ ^https?:// ]] || [[ "$repo" =~ \.git$ ]]; then
        # clone shallow
        if [ -d "$target_dir/.git" ]; then
            echo "Repository already cloned: $target_dir (pulling latest)"
            git -C "$target_dir" pull --quiet || true
        else
            git clone --depth 1 "$repo" "$target_dir" || { echo "Clone failed: $repo" >&2; continue; }
        fi
    else
        # assume local path
        if [ -d "$repo" ]; then
            target_dir="$repo"
        else
            echo "Local path not found: $repo" >&2
            continue
        fi
    fi

    # Run pipeline for this repo (collect by default)
    if [ "$GENERATOR_MODE" = true ]; then
        RUN_ID="generator"
    else
        RUN_ID="run_${safe_name}_$(date +%s)"
    fi
    export RUN_ID
    export OUT_DIR="$OUT_BASE/$safe_name"
    export PIPELINE_MODE="$PIPELINE_MODE"

    mkdir -p "$OUT_DIR"

    echo "Running pipeline for $safe_name (RUN_ID=$RUN_ID, OUT_DIR=$OUT_DIR)"

    bash "$SCRIPT_DIR/loop.sh" --rounds "$ROUNDS" --samples "$SAMPLES" $( [ "$PIPELINE_MODE" = "collect" ] && echo --collect ) || echo "Pipeline failed for $safe_name"

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

if [ $UNTIL_SAMPLES -gt 0 ] && [ -z "$GH_QUERY" ]; then
    echo "[WARN] --until-samples used without --gh-query; cannot fetch more repos dynamically."
fi

echo "All done. Outputs available under: $OUT_BASE"