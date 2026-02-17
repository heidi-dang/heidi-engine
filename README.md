# Heidi Autonomous Coding Agent - AutoTraining Pipeline

An end-to-end automated pipeline for training a coding agent using QLoRA (Quantized LoRA). This pipeline generates synthetic training data, validates it, fine-tunes a base model, and evaluates the results - all in a fully automated loop.

## Features

- **Synthetic-first dataset generation** - No real code used, fully public-safe
- **Automatic validation & cleaning** - Schema validation, deduplication, secret scrubbing
- **Optional unit test gate** - Verify generated code is syntactically valid
- **QLoRA fine-tuning** - Memory-efficient training with 4-bit quantization
- **Comprehensive evaluation** - JSON parse rate, format compliance, quality metrics
- **Automatic best model selection** - Tracks metrics across rounds
- **VRAM-safe defaults** - Works on RTX 2080 Ti (11GB)

## Quick Start

5-line quickstart — minimal local smoke:
1) python3 -m venv .venv && source .venv/bin/activate
2) pip install -r .local/ml/requirements-transformers-only.txt
3) .local/ml/scripts/prepare_data.sh path/to/raw.jsonl
4) .local/ml/scripts/train_adapter.sh --smoke-cpu --train-steps 50
5) See `.local/ml/fine_tuning_guide.md` for full workflow

```bash
# Run with default settings (RTX 2080 Ti safe)
./scripts/loop.sh

# Custom configuration
./scripts/loop.sh --rounds 3 --samples 50 --base-model microsoft/phi-2

# Minimal test run
./scripts/loop.sh --rounds 1 --samples 10 --train-steps 50
```

## Requirements

### Hardware
- NVIDIA GPU with CUDA support
- Minimum 12GB VRAM (RTX 2080 Ti compatible)
- Recommended 16GB+ for larger models

### Software
```bash
# Python dependencies
pip install python-dotenv rich pyyaml

# Core ML libraries (install in order)
pip install transformers accelerate bitsandbytes

# Training and evaluation
pip install peft trl datasets

# Optional: for teacher model API calls
pip install openai

# For evaluation (optional)
pip install json5
```

## Environment Variables

All parameters can be set via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ROUNDS` | 3 | Number of training rounds |
| `SAMPLES_PER_ROUND` | 50 | Samples per round |
| `BASE_MODEL` | microsoft/phi-2 | Base model |
| `TEACHER_MODEL` | gpt-4o-mini | Teacher model |
| `VAL_RATIO` | 0.1 | Validation split |
| `OUT_DIR` | ./autotrain | Output directory |
| `SEQ_LEN` | 2048 | Sequence length |
| `BATCH_SIZE` | 1 | Batch size |
| `GRAD_ACCUM` | 8 | Gradient accumulation |
| `TRAIN_STEPS` | 500 | Training steps |
| `LORA_R` | 64 | LoRA rank |
| `LR` | 2e-4 | Learning rate |
| `RUN_UNIT_TESTS` | 0 | Enable unit test gate |
| `SEED` | 42 | Random seed |

## VRAM Optimization

### RTX 2080 Ti (11GB) - Default Settings
```bash
export SEQ_LEN=2048
export BATCH_SIZE=1
export GRAD_ACCUM=8
export LORA_R=64
export QUANTIZATION_BITS=4
```

### RTX 3060 (6GB) - Reduced
```bash
export SEQ_LEN=1024
export BATCH_SIZE=1
export GRAD_ACCUM=16
export LORA_R=32
```

### RTX 3090/4090 (24GB) - Higher Settings
```bash
export SEQ_LEN=4096
export BATCH_SIZE=2
export GRAD_ACCUM=4
export LORA_R=128
```

## Pipeline Stages

1. **Teacher Generation** - Generate synthetic data using teacher model
2. **Validation** - Clean, deduplicate, scrub secrets
3. **Unit Test Gate** - Verify code validity (optional)
4. **Training** - QLoRA fine-tuning
5. **Evaluation** - Measure quality metrics
6. **Loop** - Repeat with best model

## Output Structure

```
autotrain/
├── runs/<run_id>/
│   ├── state.json          # Current run state
│   ├── events.jsonl        # Event stream (for dashboard)
│   └── config.json         # Configuration snapshot
├── data/
│   ├── raw_round_1.jsonl      # Generated data
│   ├── clean_round_1.jsonl    # Validated data
│   └── train/val splits
├── out_lora_round_1/
│   ├── final/                 # Trained adapter
│   └── checkpoints/
├── eval/
│   └── report_round_1.json    # Metrics
├── best_adapter -> round_X/   # Best model
├── config.yaml               # Configuration file
└── pipeline.pid              # Running pipeline PID
```

## Real-Time Dashboard

Monitor your training progress in real-time:

```bash
# Install dashboard dependency
pip install rich

# Start a training run (in background)
./scripts/loop.sh &

# In another terminal, start the dashboard
python -m autotrain.dashboard
```

### Dashboard Features
- Live counters: samples generated, validated, trained, etc.
- Teacher API usage: requests, tokens, rate limits, cost
- Training metrics: loss, steps, VRAM usage
- Event log with timestamps
- Multiple views (Overview, Teacher, Trainer, Events)

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| `q` | Quit |
| `r` | Refresh |
| `1-5` | Switch views |

See [Dashboard Documentation](docs/dashboard.md) for details.

## Interactive Menu Controller

Control the pipeline without editing files:

```bash
# Start interactive menu
python scripts/menu.py
```

### Menu Options
1. Start New Run - Configure and start training
2. Resume Last Run - Continue interrupted run
3. Stop Pipeline - Graceful stop at stage boundary
4. Pause Pipeline - Pause at safe point
5. Resume Pipeline - Continue from pause
6. Configure Parameters - Interactive setup
7. View Dashboard - Launch dashboard
8. Exit

See [Dashboard Documentation](docs/dashboard.md) for details.

## API Keys

For teacher model generation, set your API key:

```bash
export OPENAI_API_KEY=your-key-here
```

The pipeline also supports other OpenAI-compatible APIs by modifying `01_teacher_generate.py`.

## Safety & Privacy

- **Synthetic data only** - No real code or proprietary data used
- **Fail-closed secret detection** - Any potential secret triggers sample drop
- **No secrets committed** - All outputs go to `./autotrain/` (gitignored)
- **Public-safe outputs** - Datasets can be shared publicly

## Documentation

- [Dashboard & Menu Controller](docs/dashboard.md) - Real-time monitoring and control
- [Dataset Card](docs/dataset_card.md) - Dataset documentation
- [Fine-tuning guide](.local/ml/fine_tuning_guide.md) - Local LoRA / QLoRA setup and workflows
- [License Policy](docs/license_policy.md) - Legal and licensing info
- [Troubleshooting](docs/troubleshooting.md) - Common issues and fixes

## License

See [LICENSE](LICENSE) for details. This project uses permissive licensing for generated artifacts.

## Citation

If you use this pipeline in your research, please cite:

```bibtex
@software{heidi_autotrain,
  title={Heidi Autonomous Coding Agent - AutoTraining Pipeline},
  author={Heidi AI Team},
  year={2024},
  url={https://github.com/heidi-ai/autotrain}
}
```
