# Getting Started with Heidi Engine

This guide will help you get up and running with Heidi Engine in under 5 minutes.

## Prerequisites

- Python 3.8 or higher
- Git
- (Optional) NVIDIA GPU with CUDA for training

## Quick Start

### 1. Install Heidi Engine

```bash
# Clone the repository
git clone https://github.com/heidi-dang/heidi-engine.git
cd heidi-engine

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
pip install -e .
```

### 2. Run the Dashboard

The dashboard provides a real-time view of your training pipeline:

```bash
# Start the dashboard (interactive mode)
python -m heidi_engine.dashboard

# Or use the CLI entrypoint
autotrain-dashboard
```

### 3. Run ML Recommendations

Get ML configuration recommendations for your hardware:

```bash
# Get recommendations (JSON output)
python -m heidi_engine.telemetry status --json

# Or use the HTTP status server
autotrain-serve --port 7779
# Then visit http://127.0.0.1:7779/status
```

### 4. Run the Training Loop

Start a minimal training run:

```bash
# Minimal test run (1 round, 10 samples, 50 training steps)
./scripts/loop.sh --rounds 1 --samples 10 --train-steps 50

# Or use the interactive menu
python scripts/menu.py
```

## Next Steps

- **Configuration**: Edit `heidi_engine/config.yaml` or use `python scripts/menu.py` to configure training parameters
- **Monitoring**: Run `python -m heidi_engine.dashboard` in a separate terminal to monitor progress
- **Fine-tuning**: See [Fine-tuning Guide](.local/ml/fine_tuning_guide.md) for detailed ML setup

## Common Commands

| Command | Description |
|---------|-------------|
| `python -m heidi_engine.dashboard` | Launch real-time dashboard |
| `python -m heidi_engine.http --port 7779` | Start HTTP status server |
| `python -m heidi_engine.telemetry status` | Show current run status |
| `python scripts/menu.py` | Interactive menu controller |
| `./scripts/loop.sh --help` | Show training loop options |

## Environment Variables

All parameters can be configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ROUNDS` | 3 | Number of training rounds |
| `SAMPLES_PER_ROUND` | 50 | Samples generated per round |
| `BASE_MODEL` | mistralai/Mistral-7B-Instruct-v0.2 | Base model for fine-tuning |
| `SEQ_LEN` | 2048 | Maximum sequence length |
| `TRAIN_STEPS` | 500 | Training steps per round |
| `AUTOTRAIN_DIR` | ~/.local/heidi_engine | Output directory |

## Troubleshooting

### Dashboard not updating?

```bash
# Verify the package is installed
pip install -e .

# Check for active runs
python scripts/menu.py --status
```

### Out of memory during training?

Reduce memory usage with these settings:

```bash
./scripts/loop.sh --seq-len 1024 --lora-r 32 --grad-accum 16
```

### HTTP server not accessible?

The HTTP server binds to `127.0.0.1` only for security. It will not be accessible from other machines.

## Need Help?

- [Dashboard Documentation](docs/dashboard.md)
- [Dataset Card](docs/dataset_card.md)
- [License Policy](docs/license_policy.md)
- [Fine-tuning Guide](.local/ml/fine_tuning_guide.md)
