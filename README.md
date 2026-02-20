# Heidi Engine

Autonomous Data Collection and Training Orchestration Engine

## Overview

Heidi Engine is a production-grade orchestration system designed to collect, validate, and train high-quality datasets for fine-tuning large language models.

The system enforces a zero-trust lifecycle:
raw -> clean -> verified -> train

It includes:
- Local dashboard (TUI)
- HTTP control surface (localhost-only)
- Dataset validation and provenance verification
- Signed receipt verification
- Deterministic event journal with replay
- Manual or programmatic training triggers
- Strict security gating before training

Heidi Engine is designed to run locally (WSL/Linux-first) and is suitable for QLoRA-based workflows and autonomous coding agent pipelines.

## Architecture

Core components:
- Dashboard: Interactive runtime monitoring
- HTTP Server: Local control API
- Runtime Engine: State management and orchestration
- Dataset Lifecycle Manager
- Trainer Firewall (verified-only enforcement)
- Event Journal (hash-chained)
- Security Validation Layer

Runtime path:
`~/.local/heidi-engine`

## Supported Environment

- WSL Ubuntu 22.04+
- Python 3.10+
- Optional NVIDIA GPU (CUDA-compatible)
- Linux-first deployment model

## Installation

```bash
git clone https://github.com/heidi-dang/heidi-engine.git
cd heidi-engine
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Verify installation:
```bash
python -m heidi_engine.dashboard --help
python -m heidi_engine.http --help
```

## Running the Engine

### Start Dashboard
```bash
python -m heidi_engine.dashboard
```

### Start HTTP Server
```bash
python -m heidi_engine.http
```

HTTP binds to: `127.0.0.1` only.

## Collect Mode (Overnight Workflow)

Collects and validates data without triggering training.

```bash
python -m heidi_engine.collect --mode collect
```

If available:
```bash
./scripts/night_run.sh
```

This mode:
- Generates samples
- Validates samples
- Stores verified results
- Does not train until explicitly triggered

## Trigger Training

From dashboard:
Press: `f`

Or via HTTP:
```bash
curl -X POST http://127.0.0.1:<port>/actions/train-now
```

## Runtime Directory

Default runtime path: `~/.local/heidi-engine`

Contains:
- `state.json`
- `datasets/`
- `logs/`
- `receipts/`
- `journal/`

## Security Model

- HTTP server binds to localhost only
- Verified-only training gate
- Signed receipts required
- Hash-chain journal
- No plaintext secret storage
- Strict configuration validation

## CI & Governance

- No direct pushes to main
- PR required
- Green CI required before merge
- Linear history enforced
- Security checks required

## Ecosystem

Related repositories:
- [heidi-kernel](https://github.com/heidi-dang/heidi-kernel)
- [chatgpt-github-workflow](https://github.com/heidi-dang/chatgpt-github-workflow)

Additional components may be linked here as ecosystem expands.
