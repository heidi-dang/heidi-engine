# Heidi Engine: Autonomous Coding Agent

Heidi Engine is a research project focused on building an autonomous coding agent through iterative self-improvement, leveraging teacher-student distillation and advanced data pipelines.

---

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Data Collection Pipeline](#data-collection-pipeline)
4. [Model Training](#model-training)
5. [Monitoring & Dashboard](#monitoring--dashboard)
6. [C++ Core Optimizations](#c-core-optimizations)
7. [Hyperparameter Optimization (HPO)](#hyperparameter-optimization-hpo)
8. [System Requirements](#system-requirements)
9. [Troubleshooting](#troubleshooting)

---

## Overview

Heidi Engine automates the process of collecting, cleaning, and validating code data, then trains and evaluates models in a closed loop. It supports multi-language validation, distributed monitoring, and high-performance C++ extensions for efficiency.

---

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/heidi-dang/heidi-engine.git
cd heidi-engine
pip install -e .
```

---

## Data Collection Pipeline

The core data pipeline is managed by `loop_repos.sh`, which automates:

- Scraping GitHub repositories
- Generating and validating synthetic training data
- Filtering and deduplication

**Key Features:**

- **Stack Presets:**
  - `--stack python` (Python: `.py`, `.ipynb`)
  - `--stack cpp` (C++: `.cpp`, `.h`)
  - `--stack vite` (Modern frontend: `.ts`, `.tsx`, `.vue`, `.svelte`)
  - `--stack web` (Web: `.js`, `.ts`)
  - `--stack go` (Go: `.go`)
- **Smart Filtering:** Excludes homework-like repos, checks for permissive licenses, and limits file sizes.
- **Golden Repos:** Add curated, high-quality repos with `--golden`.
- **Resume Support:** Continue previous runs with `--resume`.
- **Global Deduplication:** Merge and deduplicate with `--dedupe`.

**Default:** Each round processes up to 33 samples. Override with `--rounds` and `--samples`.

**Example:**

```bash
./scripts/loop_repos.sh \
  --stack python \
  --max 100 \
  --rounds 1 \
  --samples 1000 \
  --resume \
  --golden \
  --dedupe
```

**Upload to Hugging Face:**

```bash
./scripts/loop_repos.sh --stack python --max 100 --push-to-hub my-org/my-dataset
```

---

## Model Training

Train models as part of the data loop (`--full`), or standalone for more control:

```bash
./scripts/train_only.py \
  --data ./autotrain_repos/merged_dataset.jsonl \
  --base-model mistralai/Mistral-7B-Instruct-v0.2 \
  --steps 1000 \
  --out-dir ./my_model_output
```

---

## Monitoring & Dashboard

Track progress in real time with two dashboard options:

### 1. Terminal Dashboard (Recommended)

```bash
./scripts/dashboard.sh
```

### 2. Web Dashboard

Start the telemetry server:

```bash
python3 -m heidi_engine.telemetry init --server
```
Access at: [http://127.0.0.1:7779/](http://127.0.0.1:7779/)

**Features:**

- Real-time stats: generation, validation, failure rates
- Training metrics: loss, steps
- GPU VRAM monitoring
- API cost estimates
- Dark mode

### Multi-Machine Monitoring

Monitor distributed training from a single dashboard:

**On Dashboard Machine:**

```bash
python3 -m heidi_engine.telemetry init --server
```
View at [http://127.0.0.1:7779/](http://127.0.0.1:7779/)

**On Worker Machines:**

```bash
./scripts/loop_repos.sh --stack python --monitor http://<dashboard-ip>:7779
```

---

## C++ Core Optimizations

High-performance C++ extensions accelerate data processing and resource management:

- **Speed:** Deduplication and transpose up to 3.4x faster than Python
- **Efficiency:** Arena allocation, vectorized compression
- **Kernel Integration:** Submodule linking with [heidi-kernel](https://github.com/heidi-dang/heidi-kernel)
- **Monitoring:** Real-time GPU VRAM tracking via CUDA

See [docs/cpp_optimizations.md](docs/cpp_optimizations.md) for details.

---

## Hyperparameter Optimization (HPO)

Integrated Optuna-powered sweeps for optimal training parameters:

- **Automated Search:** Explores `learning_rate`, `batch_size`, `lora_r`
- **Resource Awareness:** Skips trials if GPU VRAM <1GB
- **Dashboard Integration:** Broadcasts best params in real time
- **Fail-Safe:** Infinite-loss fallback for OOM or script crashes

**Example:**

```bash
./scripts/train_only.py --data dataset.jsonl --optuna --n-trials 20
```

---

## System Requirements

**Compiler Requirements for Validation:**

- `g++` (C++)
- `node` (JavaScript/TypeScript)
- `go` (Go)

---

## Troubleshooting

- **Connection Issues:** Check firewall and telemetry server status
- **Authentication Errors:** Set `TELEMETRY_PASS` environment variable
- **Validation Failures:** Ensure compilers are installed; fallback logging is enabled

For more, see [docs/walkthrough_v1.md](docs/walkthrough_v1.md).

