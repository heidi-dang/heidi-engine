#!/usr/bin/env bash
# =============================================================================
# loop.sh - Main Pipeline Loop Runner
# =============================================================================
# 
# PURPOSE:
#     Orchestrates the complete teacher->dataset->validate->train->eval->repeat
#     pipeline for building an autonomous coding agent.
#
# INTEGRATION:
#     This script integrates with autotrain/telemetry.py for:
#     - Real-time event emission (see --emit option)
#     - State management (run_id, counters, usage)
#     - Graceful stop/pause/resume support
#     - Live dashboard support
#
# USAGE:
#     ./scripts/loop.sh [OPTIONS]
#
# ENVIRONMENT VARIABLES (can also be set as args):
#     ROUNDS              Number of training rounds (default: 3)
#     SAMPLES_PER_ROUND   Samples to generate per round (default: 50)
#     BASE_MODEL          Base model to fine-tune (default: microsoft/phi-2)
#     TEACHER_MODEL       Teacher model for generation (default: gpt-4o-mini)
#     VAL_RATIO           Validation split ratio (default: 0.1)
#     OUT_DIR             Output directory (default: ./autotrain)
#     SEQ_LEN             Sequence length (default: 2048)
#     BATCH_SIZE          Batch size (default: 1)
#     GRAD_ACCUM          Gradient accumulation (default: 8)
#     TRAIN_STEPS         Training steps per round (default: 500)
#     LORA_R              LoRA rank (default: 64)
#     RUN_UNIT_TESTS      Enable unit test gate (default: 0)
#     SEED                Random seed (default: 42)
#     RUN_ID              Unique run identifier (auto-generated if not set)
#
# CONFIG FILE:
#     Configuration can also be saved to autotrain/config.yaml
#     Run ./scripts/menu.py to configure interactively
#
# HPO:
#     --optuna            Enable Hyperparameter Optimization
#     --n-trials N        Number of HPO trials (default: 10)
#
# GRACEFUL STOP/PAUSE:
#     - Stop: Sets stop_requested=true in state.json, exits at stage boundaries
#     - Pause: Sets pause_requested=true, pauses between batches
#     - Resume: Clears pause_requested, continues from last stage
#
# DASHBOARD:
#     Run 'python -m autotrain.dashboard' in another terminal to see live progress
#
# VRAM-SAFE DEFAULTS (RTX 2080 Ti - 11GB):
#     SEQ_LEN=2048, BATCH_SIZE=1, GRAD_ACCUM=8, LORA_R=64
#
# OUTPUT STRUCTURE:
#     autotrain/
#     ├── runs/<run_id>/
#     │   ├── state.json          # Current run state (counters, status)
#     │   ├── events.jsonl        # Event stream for dashboard
#     │   └── config.json         # Configuration snapshot
#     ├── data/
#     │   ├── raw_round_1.jsonl     # Raw generated data
#     │   ├── clean_round_1.jsonl   # Validated/cleaned data
#     │   ├── tested_round_1.jsonl  # After unit test gate (if enabled)
#     │   └── ...
#     ├── out_lora_round_1/         # Trained adapters
#     │   ├── final/               # Final adapter weights
#     │   └── checkpoints/
#     ├── eval/
#     │   ├── report_round_1.json   # Evaluation results
#     │   └── ...
#     └── best_adapter -> round_X/  # Symlink to best adapter
#
# =============================================================================

set -euo pipefail

# =============================================================================
# SCRIPT DIRECTORY RESOLUTION
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source common configuration
source "$SCRIPT_DIR/common.sh"

# Set default for HPO variables
OPTUNA=${OPTUNA:-false}
N_TRIALS=${N_TRIALS:-10}

# =============================================================================
# TELEMETRY INTEGRATION
# =============================================================================

# Check if Python telemetry module is available
TELEMETRY_AVAILABLE=false
if python3 -c "import heidi_engine.telemetry" 2>/dev/null; then
    TELEMETRY_AVAILABLE=true
fi

# Function to emit telemetry events
# Usage: emit_event <event_type> <message> [<stage>] [<round>] [<counters_delta>] [<usage_delta>]
emit_event() {
    local event_type="$1"
    local message="$2"
    local stage="${3:-}"
    local round="${4:-0}"
    local counters_delta="${5:-}"
    local usage_delta="${6:-}"
    
    if [ "$TELEMETRY_AVAILABLE" = true ]; then
        # Build Python command for counters
        local counters_arg="None"
        if [ -n "$counters_delta" ]; then
            counters_arg="$counters_delta"
        fi
        
        local usage_arg="None"
        if [ -n "$usage_delta" ]; then
            usage_arg="$usage_delta"
        fi
        
        python3 -c "
import heidi_engine.telemetry as tm
tm.emit_event(
    event_type='$event_type',
    message=\"$message\",
    stage='$stage',
    round_num=$round,
    counters_delta=$counters_arg,
    usage_delta=$usage_arg,
    model='$TEACHER_MODEL'
)
tm.flush_events()
" 2>/dev/null || true
    fi
}

# Function to check for stop/pause requests
check_stop_request() {
    if [ "$TELEMETRY_AVAILABLE" = true ]; then
        python3 -c "
import heidi_engine.telemetry as tm
if tm.check_stop_requested():
    exit(0)
exit(1)
" 2>/dev/null
        return $?
    fi
    return 1
}

check_pause_request() {
    if [ "$TELEMETRY_AVAILABLE" = true ]; then
        python3 -c "
import heidi_engine.telemetry as tm
if tm.check_pause_requested():
    exit(0)
exit(1)
" 2>/dev/null
        return $?
    fi
    return 1
}

# Initialize telemetry for this run
init_telemetry() {
    if [ "$TELEMETRY_AVAILABLE" = true ]; then
        # Build config dict
        local config_json="{
            \"BASE_MODEL\": \"$BASE_MODEL\",
            \"TEACHER_MODEL\": \"$TEACHER_MODEL\",
            \"SAMPLES_PER_ROUND\": $SAMPLES_PER_ROUND,
            \"ROUNDS\": $ROUNDS,
            \"VAL_RATIO\": $VAL_RATIO,
            \"SEQ_LEN\": $SEQ_LEN,
            \"LORA_R\": $LORA_R,
            \"GRAD_ACCUM\": $GRAD_ACCUM,
            \"TRAIN_STEPS\": $TRAIN_STEPS,
            \"RUN_UNIT_TESTS\": $RUN_UNIT_TESTS,
            \"SEED\": $SEED,
            \"OPTUNA\": \"$OPTUNA\",
            \"N_TRIALS\": $N_TRIALS
        }"
        
        python3 -c "
import heidi_engine.telemetry as tm
import os
os.environ['AUTOTRAIN_DIR'] = '$OUT_DIR'
run_id = tm.init_telemetry(
    run_id=os.environ.get('RUN_ID', None),
    config=$config_json
)
print(run_id)
" 2>/dev/null || echo "$RUN_ID"
    fi
    
    # Always set RUN_ID if not set
    if [ -z "${RUN_ID:-}" ]; then
        RUN_ID="run_$(date +%Y%m%d_%H%M%S)"
    fi
    
    # If RUN_ID is 'code-assistant', use it directly to signal agent mode
    if [ "$RUN_ID" = "code-assistant" ]; then
        echo "[INFO] Running in code-assistant mode"
        export TEACHER_MODEL="code-assistant"
    fi

    export RUN_ID
    echo "[INFO] Run ID: $RUN_ID"
}

# Update run status in telemetry
set_status() {
    local status="$1"
    local stage="${2:-}"
    local round="${3:-0}"
    
    if [ "$TELEMETRY_AVAILABLE" = true ]; then
        python3 -c "
import heidi_engine.telemetry as tm
tm.set_status('$status', '$stage', $round)
" 2>/dev/null || true
    fi
}

# Update counters
update_counters() {
    local delta="$1"  # JSON string like '{"teacher_generated": 10}'
    
    if [ "$TELEMETRY_AVAILABLE" = true ] && [ -n "$delta" ]; then
        python3 -c "
import heidi_engine.telemetry as tm
tm.update_counters($delta)
" 2>/dev/null || true
    fi
}

# Update usage
update_usage() {
    local delta="$1"  # JSON string
    
    if [ "$TELEMETRY_AVAILABLE" = true ] && [ -n "$delta" ]; then
        python3 -c "
import heidi_engine.telemetry as tm
tm.update_usage($delta, '$TEACHER_MODEL')
" 2>/dev/null || true
    fi
}

# =============================================================================
# PARSE ARGUMENTS
# =============================================================================

show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Run the complete training pipeline: generate -> validate -> train -> eval -> repeat

OPTIONS:
    --help, -h              Show this help message
    --rounds N              Number of training rounds (default: $ROUNDS)
    --samples N             Samples per round (default: $SAMPLES_PER_ROUND)
    --base-model MODEL      Base model (default: $BASE_MODEL)
    --teacher MODEL         Teacher model (default: $TEACHER_MODEL)
    --val-ratio RATIO       Validation ratio (default: $VAL_RATIO)
    --out-dir DIR           Output directory (default: $OUT_DIR)
    --seq-len N             Sequence length (default: $SEQ_LEN)
    --batch-size N          Batch size (default: $BATCH_SIZE)
    --grad-accum N          Gradient accumulation (default: $GRAD_ACCUM)
    --train-steps N         Training steps (default: $TRAIN_STEPS)
    --lora-r N              LoRA rank (default: $LORA_R)
    --run-tests             Enable unit test gate
    --seed N                Random seed (default: $SEED)
    --optuna                Enable Hyperparameter Optimization
    --n-trials N            Number of HPO trials (default: 10)

EXAMPLES:
    # Run with defaults (RTX 2080 Ti safe)
    $0

    # Custom configuration
    $0 --rounds 5 --samples 100 --base-model meta-llama/Llama-2-7b-hf

    # Minimal test run
    $0 --rounds 1 --samples 10 --train-steps 50

ENVIRONMENT VARIABLES:
    All options can be set via environment variables.
    See source script (common.sh) for full list.

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --rounds)
            ROUNDS="$2"
            shift 2
            ;;
        --samples)
            SAMPLES_PER_ROUND="$2"
            shift 2
            ;;
        --base-model)
            BASE_MODEL="$2"
            shift 2
            ;;
        --teacher)
            TEACHER_MODEL="$2"
            shift 2
            ;;
        --val-ratio)
            VAL_RATIO="$2"
            shift 2
            ;;
        --out-dir)
            OUT_DIR="$2"
            shift 2
            ;;
        --seq-len)
            SEQ_LEN="$2"
            shift 2
            ;;
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --grad-accum)
            GRAD_ACCUM="$2"
            shift 2
            ;;
        --train-steps)
            TRAIN_STEPS="$2"
            shift 2
            ;;
        --lora-r)
            LORA_R="$2"
            shift 2
            ;;
        --run-tests)
            RUN_UNIT_TESTS="1"
            shift
            ;;
        --seed)
            SEED="$2"
            shift 2
            ;;
        --optuna)
            OPTUNA=true
            shift
            ;;
        --n-trials)
            N_TRIALS="$2"
            shift 2
            ;;
        --collect)
            PIPELINE_MODE="collect"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# =============================================================================
# PIPELINE FUNCTIONS
# =============================================================================

log_step() {
    echo "" >&2
    echo "==============================================================================" >&2
    echo "STEP: $1" >&2
    echo "==============================================================================" >&2
}

run_teacher_generate() {
    local round_num=$1
    local output_file="$OUT_DIR/data/raw_round_${round_num}.jsonl"
    
    log_step "Teacher Dataset Generation (Round $round_num)"
    
    # Emit stage start
    emit_event "stage_start" "Starting teacher generation" "generate" "$round_num"
    set_status "running" "generate" "$round_num"
    
    log_info "Generating $SAMPLES_PER_ROUND samples with teacher model: $TEACHER_MODEL"
    
    # Run generation
    python3 "$SCRIPT_DIR/01_teacher_generate.py" \
        --samples "$SAMPLES_PER_ROUND" \
        --output "$output_file" \
        --teacher "$TEACHER_MODEL" \
        --round "$round_num" \
        --language "${LANGUAGE:-python}" \
        --seed "$SEED" 1>&2 || {
            echo "[ERROR] Teacher generation failed" >&2
            exit 1
        }
    
    # Count generated samples
    if [ -f "$output_file" ]; then
        local generated=$(wc -l < "$output_file")
        local failed=$((SAMPLES_PER_ROUND - generated))
        
        # Update counters
        update_counters "{\"teacher_generated\": $generated, \"teacher_failed\": $failed, \"raw_written\": $generated}"
        
        # Update usage (estimate based on samples)
        update_usage "{\"requests_sent\": $SAMPLES_PER_ROUND, \"input_tokens\": $((SAMPLES_PER_ROUND * 500)), \"output_tokens\": $((SAMPLES_PER_ROUND * 1500))}"
        
        emit_event "stage_end" "Generated $generated samples" "generate" "$round_num" "{\"teacher_generated\": $generated}"
    else
        emit_event "stage_end" "Generation failed" "generate" "$round_num" "" "{\"error\": \"Output file not created\"}"
    fi
    
    log_success "Generated dataset saved to: $output_file"
    echo "$output_file"
}

run_validation() {
    local input_file=$1
    local round_num=$2
    local output_file="$OUT_DIR/data/clean_round_${round_num}.jsonl"
    
    log_step "Validation + Deduplication + Secret Scrub (Round $round_num)"
    
    # Emit stage start
    emit_event "stage_start" "Starting validation" "validate" "$round_num"
    set_status "running" "validate" "$round_num"
    
    log_info "Validating and cleaning: $input_file"
    
    # Run validation
    python3 "$SCRIPT_DIR/02_validate_clean.py" \
        --input "$input_file" \
        --output "$output_file" \
        --max-input "$MAX_INPUT_LENGTH" \
        --max-output "$MAX_OUTPUT_LENGTH" \
        --min-input "$MIN_INPUT_LENGTH" \
        --min-output "$MIN_OUTPUT_LENGTH" 1>&2 || {
            echo "[ERROR] Validation failed" >&2
            exit 1
        }
    
    # Count validated samples
    if [ -f "$output_file" ]; then
        local validated=$(wc -l < "$output_file")
        local rejected=$((SAMPLES_PER_ROUND - validated))
        
        # Update counters
        update_counters "{\"validated_ok\": $validated, \"rejected_dedupe\": $rejected}"
        
        emit_event "stage_end" "Validated $validated samples" "validate" "$round_num" "{\"validated_ok\": $validated}"
    else
        emit_event "stage_end" "Validation failed" "validate" "$round_num"
    fi
    
    log_success "Cleaned dataset saved to: $output_file"
    echo "$output_file"
}

run_unit_tests() {
    local input_file=$1
    local round_num=$2
    local output_file="$OUT_DIR/data/tested_round_${round_num}.jsonl"
    
    log_step "Unit Test Gate (Round $round_num)"
    
    log_info "Running unit tests on: $input_file"
    
    python3 "$SCRIPT_DIR/03_unit_test_gate.py" \
        --input "$input_file" \
        --output "$output_file" \
        --timeout "$UNIT_TEST_TIMEOUT" 1>&2 || {
            echo "[ERROR] Unit test gate failed" >&2
            exit 1
        }
    
    log_success "Tested dataset saved to: $output_file"
    echo "$output_file"
}

split_train_val() {
    local input_file=$1
    local round_num=$2
    
    # Create temp files
    local train_file="$OUT_DIR/data/train_round_${round_num}.jsonl"
    local val_file="$OUT_DIR/data/val_round_${round_num}.jsonl"
    
    log_info "Splitting data: train=${train_file}, val=${val_file}" >&2
    
    # Calculate split point
    local total_lines=$(wc -l < "$input_file")
    local val_count=$(echo "($total_lines * $VAL_RATIO) / 1" | bc)
    local train_count=$((total_lines - val_count))
    
    if [ "$val_count" -lt 1 ]; then
        val_count=1
        train_count=$((total_lines - 1))
    fi
    
    # Split using head/tail
    head -n "$train_count" "$input_file" > "$train_file"
    tail -n +$((train_count + 1)) "$input_file" > "$val_file"
    
    log_info "Split complete: $train_count train, $val_count validation" >&2
    
    echo -e "$train_file\n$val_file"
}

run_training() {
    local train_file=$1
    local val_file=$2
    local round_num=$3
    local output_dir="$OUT_DIR/out_lora_round_${round_num}"
    
    log_step "QLoRA Training (Round $round_num)"
    
    # Emit stage start
    emit_event "stage_start" "Starting training" "train" "$round_num"
    set_status "running" "train" "$round_num"
    
    log_info "Training with data: $train_file"
    log_info "Output directory: $output_dir"
    
    # Create output directory
    mkdir -p "$output_dir"
       # Run training (use train_only.py if Optuna is enabled)
    if [ "${OPTUNA:-false}" = "true" ]; then
        log_info "Running with Optuna HPO ($N_TRIALS trials)"
        python3 "$SCRIPT_DIR/train_only.py" \
            --data "$train_file" \
            --out-dir "$output_dir" \
            --base-model "$BASE_MODEL" \
            --steps "$TRAIN_STEPS" \
            --seq-len "$SEQ_LEN" \
            --batch-size "$BATCH_SIZE" \
            --grad-accum "$GRAD_ACCUM" \
            --lora-r "$LORA_R" \
            --lr "$LR" \
            --seed "$SEED" \
            --val-ratio "$VAL_RATIO" \
            --optuna \
            --n-trials "$N_TRIALS" 1>&2 || {
                echo "[ERROR] HPO Training failed" >&2
                exit 1
            }
    else
        python3 "$SCRIPT_DIR/04_train_qlora.py" \
            --data "$train_file" \
            --val-data "$val_file" \
            --output "$output_dir" \
            --base-model "$BASE_MODEL" \
            --seq-len "$SEQ_LEN" \
            --batch-size "$BATCH_SIZE" \
            --grad-accum "$GRAD_ACCUM" \
            --train-steps "$TRAIN_STEPS" \
            --save-steps "$SAVE_STEPS" \
            --eval-steps "$EVAL_STEPS" \
            --lora-r "$LORA_R" \
            --lora-alpha "$LORA_ALPHA" \
            --lora-dropout "$LORA_DROPOUT" \
            --lr "$LR" \
            --seed "$SEED" 1>&2 || {
                echo "[ERROR] Training failed" >&2
                exit 1
            }
    fi
    
    # Update counters with training completion
    update_counters "{\"train_step\": $TRAIN_STEPS}"
    
    emit_event "stage_end" "Training complete" "train" "$round_num" "{\"train_step\": $TRAIN_STEPS}"
    
    log_success "Training complete. Adapter saved to: $output_dir/final"
    echo "$output_dir"
}

run_evaluation() {
    local adapter_path=$1
    local val_file=$2
    local round_num=$3
    local output_file="$OUT_DIR/eval/report_round_${round_num}.json"
    
    log_step "Evaluation (Round $round_num)"
    
    # Emit stage start
    emit_event "stage_start" "Starting evaluation" "eval" "$round_num"
    set_status "running" "eval" "$round_num"
    
    log_info "Evaluating adapter: $adapter_path"
    log_info "Using validation data: $val_file"
    
    # Create eval directory
    mkdir -p "$OUT_DIR/eval"
    
    # Run evaluation
    python3 "$SCRIPT_DIR/05_eval.py" \
        --adapter "$adapter_path" \
        --data "$val_file" \
        --output "$output_file" \
        --base-model "$BASE_MODEL" \
        --seq-len "$SEQ_LEN" \
        --temperature 0.1 \
        --max-new-tokens 512 1>&2 || {
            echo "[ERROR] Evaluation failed" >&2
            exit 1
        }
    
    # Extract and report metrics if available
    if [ -f "$output_file" ]; then
        local json_rate=$(extract_metric "$output_file" "metrics.json_parse_rate")
        local format_rate=$(extract_metric "$output_file" "metrics.format_compliance_rate")
        
        if [ -n "$json_rate" ] && [ "$json_rate" != "None" ]; then
            update_counters "{\"eval_json_parse_rate\": $json_rate}"
        fi
        if [ -n "$format_rate" ] && [ "$format_rate" != "None" ]; then
            update_counters "{\"eval_format_rate\": $format_rate}"
        fi
        
        emit_event "stage_end" "Evaluation complete" "eval" "$round_num"
    else
        emit_event "stage_end" "Evaluation failed" "eval" "$round_num"
    fi
    
    log_success "Evaluation report saved to: $output_file"
    echo "$output_file"
}

extract_metric() {
    local report_file=$1
    local metric_path=$2
    
    # Use python to extract nested JSON value
    python3 -c "
import json
import sys
try:
    with open('$report_file') as f:
        data = json.load(f)
    keys = '$metric_path'.split('.')
    val = data
    for k in keys:
        val = val.get(k, {})
    print(val if val is not None else 0)
except Exception as e:
    print(0)
" 2>/dev/null || echo "0"
}

update_best_adapter() {
    local round_num=$1
    local adapter_path=$2
    local eval_report=$3
    
    # Extract main metric (format compliance rate or success rate)
    local metric=$(extract_metric "$eval_report" "metrics.format_compliance_rate")
    if [ "$metric" = "None" ] || [ -z "$metric" ]; then
        metric=$(extract_metric "$eval_report" "metrics.success_rate")
    fi
    
    log_info "Round $round_num metric: $metric"
    
    # Track best
    local best_metric=0
    local best_round=0
    
    if [ -f "$OUT_DIR/best_metric.txt" ]; then
        best_metric=$(cat "$OUT_DIR/best_metric.txt")
    fi
    
    # Compare (higher is better)
    local is_better=$(python3 -c "print($metric > $best_metric)")
    
    if [ "$is_better" = "True" ]; then
        log_success "New best adapter! Metric: $metric (previous: $best_metric)"
        echo "$metric" > "$OUT_DIR/best_metric.txt"
        echo "$round_num" > "$OUT_DIR/best_round.txt"
        
        # Update symlink
        rm -f "$OUT_DIR/best_adapter"
        ln -s "$adapter_path" "$OUT_DIR/best_adapter"
        
        log_success "Best adapter updated: $adapter_path"
    else
        log_info "Round $round_num not better than current best ($best_metric)"
    fi
}

# =============================================================================
# MAIN PIPELINE
# =============================================================================

main() {
    echo ""
    echo "=============================================================================="
    echo "HEIDI AUTONOMOUS CODING AGENT - TRAINING PIPELINE"
    echo "=============================================================================="
    echo ""
    
    # Initialize telemetry
    init_telemetry
    
    # Print configuration
    print_config
    
    # Check dependencies
    check_dependencies || exit 1
    
    # Setup directories
    setup_directories "$OUT_DIR"
    
    # Set random seed
    set_seed "$SEED"
    
    # Emit pipeline start event
    emit_event "pipeline_start" "Starting training pipeline" "pipeline" 0
    
    # Set status
    set_status "running" "initializing" 0
    
    # =======================================================================
    # MAIN LOOP
    # =======================================================================
    
    for round_num in $(seq 1 "$ROUNDS"); do
        # Check for stop request before starting round
        if check_stop_request; then
            log_warn "Stop requested, exiting at round boundary"
            emit_event "pipeline_stop" "Stop requested by user" "pipeline" "$round_num"
            set_status "stopped" "round_boundary" "$round_num"
            exit 0
        fi
        
        echo ""
        echo "=============================================================================="
        echo "ROUND $round_num of $ROUNDS"
        echo "=============================================================================="
        
        # Update current round for signal handler
        current_round=$round_num
        
        # Update status
        set_status "running" "round_start" "$round_num"
        emit_event "round_start" "Starting round $round_num" "round" "$round_num"
        
        # Step 1: Generate dataset
        raw_file=$(run_teacher_generate "$round_num")
        
        # Check for stop after generation
        if check_stop_request; then
            log_warn "Stop requested, exiting after generation"
            emit_event "pipeline_stop" "Stop requested by user" "generate" "$round_num"
            set_status "stopped" "generate" "$round_num"
            exit 0
        fi
        
        # Step 2: Validate and clean
        clean_file=$(run_validation "$raw_file" "$round_num")
        
        # Check for stop after validation
        if check_stop_request; then
            log_warn "Stop requested, exiting after validation"
            emit_event "pipeline_stop" "Stop requested by user" "validate" "$round_num"
            set_status "stopped" "validate" "$round_num"
            exit 0
        fi
        
        # Step 3: Optional unit test gate
        if [ "$RUN_UNIT_TESTS" = "1" ]; then
            tested_file=$(run_unit_tests "$clean_file" "$round_num")
            final_file="$tested_file"
            
            # Check for stop after tests
            if check_stop_request; then
                log_warn "Stop requested, exiting after tests"
                emit_event "pipeline_stop" "Stop requested by user" "test" "$round_num"
                set_status "stopped" "test" "$round_num"
                exit 0
            fi
        else
            final_file="$clean_file"
        fi
        
        # Step 4: Split into train/val
        split_result=$(split_train_val "$final_file" "$round_num")
        train_file=$(echo "$split_result" | head -1)
        val_file=$(echo "$split_result" | tail -1)
        
        # Step 5/6/7: Train, evaluate, and track best adapter (skippable in collect mode)
        if [ "${PIPELINE_MODE:-full}" = "collect" ]; then
            log_info "PIPELINE_MODE=collect: skipping training and evaluation for round $round_num"
            emit_event "stage_skip" "Skipping train/eval in collect mode" "train" "$round_num"
            adapter_dir=""
            eval_report=""
        else
            # Step 5: Train with QLoRA
            adapter_dir=$(run_training "$train_file" "$val_file" "$round_num")

            # Step 6: Evaluate
            eval_report=$(run_evaluation "$adapter_dir/final" "$val_file" "$round_num")

            # Step 7: Track best adapter
            update_best_adapter "$round_num" "$adapter_dir" "$eval_report"
        fi
        
        # Small delay between rounds
        sleep 2
        
    done
    
    # =======================================================================
    # FINAL SUMMARY
    # =======================================================================
    
    echo ""
    echo "=============================================================================="
    echo "PIPELINE COMPLETE"
    echo "=============================================================================="
    
    # Emit pipeline complete event
    emit_event "pipeline_complete" "Training pipeline finished" "pipeline" "$ROUNDS"
    set_status "completed" "complete" "$ROUNDS"
    
    if [ -f "$OUT_DIR/best_round.txt" ]; then
        best_round=$(cat "$OUT_DIR/best_round.txt")
        best_metric=$(cat "$OUT_DIR/best_metric.txt")
        
        echo ""
        echo "BEST ADAPTER: Round $best_round"
        echo "Best metric: $best_metric"
        echo "Path: $OUT_DIR/best_adapter"
        echo ""
        
        log_success "Training complete! Best adapter available at: $OUT_DIR/best_adapter"
    else
        log_warn "No best adapter found - all rounds may have failed"
        emit_event "pipeline_error" "No successful rounds" "pipeline" "$ROUNDS"
    fi
    
    echo ""
    echo "Output structure:"
    echo "  Data:      $OUT_DIR/data/"
    echo "  Adapters: $OUT_DIR/out_lora_round_*/"
    echo "  Eval:     $OUT_DIR/eval/"
    echo "  Best:     $OUT_DIR/best_adapter ->"
    echo ""
}

# =============================================================================
# GRACEFUL STOP HANDLER
# =============================================================================

current_round=0

graceful_stop() {
    echo ""
    log_warn "Received stop signal - saving state and exiting gracefully..."
    
    # Emit stop event
    emit_event "pipeline_stop" "Interrupted by user" "pipeline" "$current_round"
    set_status "stopped" "interrupted" "$current_round"
    
    # Request stop in telemetry for menu.py to see
    if [ "$TELEMETRY_AVAILABLE" = true ]; then
        python3 -c "import heidi_engine.telemetry as tm; tm.request_stop()" 2>/dev/null || true
    fi
    
    exit 0
}

# Trap SIGINT and SIGTERM
trap graceful_stop INT TERM

# =============================================================================
# ENTRY POINT
# =============================================================================

main "$@"
