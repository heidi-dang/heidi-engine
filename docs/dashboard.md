# AutoTrain Dashboard & Menu Controller

Real-time monitoring and control for the AutoTraining pipeline.

## Quick Start

### Running the Dashboard

```bash
# Install dependencies
pip install rich pyyaml

# Start a training run first (in background or separate terminal)
./scripts/loop.sh --rounds 1 --samples 10 &

# In another terminal, start the dashboard
python -m heidi_engine.dashboard

# Or specify a run ID
python -m heidi_engine.dashboard --run <run_id>
```

### Running the Menu Controller

```bash
# Interactive menu
python scripts/menu.py

# Command-line options
python scripts/menu.py --start          # Start new run
python scripts/menu.py --status          # Show status
python scripts/menu.py --stop            # Stop running pipeline
python scripts/menu.py --dashboard        # Start dashboard
```

## Dashboard Features

### Views

1. **Overview** (default) - Shows counters, usage, trainer, and events
2. **Teacher** - Detailed API usage statistics
3. **Trainer** - Training metrics and GPU status
4. **Events** - Full event log
5. **Configuration** - Current run configuration

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit dashboard |
| `r` | Refresh now |
| `1` | Overview view |
| `2` | Teacher usage |
| `3` | Trainer metrics |
| `4` | Event log |
| `5` | Configuration |

### Displayed Metrics

#### Pipeline Counters
- Teacher Generated/Failed
- Validated OK
- Rejected (Schema/Secret/Dedup)
- Test Pass/Fail
- Training Steps/Loss
- Evaluation Rates

#### Teacher API Usage
- Requests Sent
- Input/Output Tokens
- Rate Limits Hit
- Retries
- Estimated Cost (if pricing configured)

#### Training Status
- Current Step / Progress
- Loss
- GPU VRAM Usage
- GPU Utilization

## Menu Controller Features

### Interactive Menu Options

1. **Start New Run** - Configure and start a new training run
2. **Resume Last Run** - Resume a paused or stopped run
3. **Stop Pipeline** - Gracefully stop (exits at stage boundary)
4. **Pause Pipeline** - Pause at safe boundary
5. **Resume Pipeline** - Resume from pause
6. **Configure Parameters** - Interactive parameter setup
7. **View Dashboard** - Launch dashboard
8. **Start HTTP Server** - Start REST API server

### Configurable Parameters

- BASE_MODEL - Base model to fine-tune
- TEACHER_MODEL - Teacher model for generation
- SAMPLES_PER_ROUND - Samples per round
- ROUNDS - Number of rounds
- VAL_RATIO - Validation split
- SEQ_LEN - Sequence length
- LORA_R - LoRA rank
- GRAD_ACCUM - Gradient accumulation
- TRAIN_STEPS - Training steps
- RUN_UNIT_TESTS - Enable test gate

## HTTP Status Server

The pipeline exposes a lightweight HTTP status endpoint:

```bash
# Start the server (port 7779)
python scripts/menu.py --http

# Query status
curl http://127.0.0.1:7779

# Response format:
{
  "run_id": "run_20240215_123456_abc12345",
  "status": "running",
  "current_round": 1,
  "current_stage": "generate",
  "counters": {...},
  "usage": {...}
}
```

## Graceful Stop/Pause/Resume

### Stop
- Press `Ctrl+C` in loop.sh terminal, OR
- Use menu: Stop Pipeline
- Pipeline exits at next stage boundary
- State is saved to `runs/<run_id>/state.json`

### Pause/Resume
- Use menu: Pause/Resume Pipeline
- Pause happens at safe boundaries (between batches)
- Resume continues from where it stopped

## File Locations

```
heidi_engine/
├── runs/<run_id>/
│   ├── state.json        # Current run state
│   ├── events.jsonl      # Event stream
│   ├── config.json       # Configuration snapshot
│   └── pricing.json      # Custom pricing (optional)
├── data/                 # Training data
├── out_lora_round_*/    # Trained adapters
├── eval/                 # Evaluation reports
├── config.yaml          # Main configuration
└── pipeline.pid         # Running pipeline PID
```

## Troubleshooting

### Dashboard not updating
- Check that telemetry module is installed: `pip install -e .`
- Verify run is active: `python scripts/menu.py --status`

### Menu can't start pipeline
- Make sure loop.sh is executable: `chmod +x scripts/loop.sh`
- Check dependencies are installed

### HTTP server not responding
- Verify port 7779 is available
- Check firewall settings

### Pipeline doesn't stop gracefully
- Check state.json for stop_requested flag
- Kill manually if needed: `kill -9 $(cat heidi_engine/pipeline.pid)`

## Event Schema (v1.0 - Frozen)

The event schema is versioned and frozen. All events follow this structure:

```json
{
    "event_version": "1.0",
    "ts": "ISO8601 timestamp",
    "run_id": "unique run identifier",
    "round": 1,
    "stage": "generate|validate|train|eval|round_start|round_end",
    "level": "info|warn|error|success",
    "event_type": "stage_start|stage_end|progress|error|pipeline_start|pipeline_stop|pipeline_complete",
    "message": "human-readable message (truncated to 500 chars)",
    "counters_delta": {},
    "usage_delta": {},
    "artifact_paths": [],
    "error": "error message if level=error (truncated)"
}
```

### Allowed Fields
- `event_version`: Schema version (currently "1.0")
- `ts`: ISO8601 timestamp
- `run_id`: Unique run identifier
- `round`: Current round number (0 for pre-round events)
- `stage`: Pipeline stage name
- `level`: Log level (info, warn, error, success)
- `event_type`: Type of event
- `message`: Human-readable message (max 500 chars)
- `counters_delta`: Counter increments
- `usage_delta`: Usage increments
- `artifact_paths`: Files created
- `error`: Error message (max 200 chars)

### Security
- All events are redacted before writing (secrets replaced with placeholders)
- ANSI escape sequences are stripped
- Long strings are truncated
- No API keys, tokens, or raw prompts in logs

## HTTP API

### Endpoints

#### GET /status
Returns redacted state (no secrets):

```json
{
    "run_id": "run_20240215_123456_abc12345",
    "status": "running",
    "current_round": 1,
    "current_stage": "generate",
    "stop_requested": false,
    "pause_requested": false,
    "counters": {...},
    "usage": {...},
    "gpu_summary": {"vram_used_mb": 2048, "vram_total_mb": 11264, "util_pct": 45},
    "last_event_ts": "2024-02-15T12:34:56.789Z",
    "health": "ok",
    "updated_at": "2024-02-15T12:34:56.789Z"
}
```

#### GET /health
Simple health check:

```json
{"health": "ok"}
```

### Security
- Binds to 127.0.0.1 only (never 0.0.0.0)
- Returns only allowed fields (no env vars, tokens)
- Redacts sensitive data

## Configuration Schema

Config must pass strict validation:

| Field | Type | Default | Constraints |
|-------|------|---------|-------------|
| BASE_MODEL | string | mistralai/Mistral-7B-Instruct-v0.2 | |
| TEACHER_MODEL | string | gpt-4o-mini | |
| SAMPLES_PER_ROUND | int | 50 | 1-10000 |
| ROUNDS | int | 3 | 1-100 |
| VAL_RATIO | float | 0.1 | 0.0-1.0 |
| SEQ_LEN | int | 2048 | 128-8192 |
| BATCH_SIZE | int | 1 | 1-64 |
| GRAD_ACCUM | int | 8 | 1-128 |
| TRAIN_STEPS | int | 500 | 1-100000 |
| LORA_R | int | 64 | 1-512 |
| RUN_UNIT_TESTS | string | "0" | "0" or "1" |

Invalid config fails fast with clear error messages.

## Log Rotation

Event logs rotate when they exceed 100MB (configurable via `EVENT_LOG_MAX_SIZE_MB`).
Keeps last 5 rotated files (configurable via `EVENT_LOG_RETENTION`).

File permissions are set to 0600 for security.
