# Local LoRA fine-tuning guide — Heidi-engine (local)

## Purpose 🎯
Concise instructions and helper scripts to run local LoRA/QLoRA fine-tuning for the Heidi coding-agent. Covers repository layout, environment bootstrap, data pipeline requirements, recommended Python stacks, and quick run steps.

---

## Repo layout (local staging)
The repository keeps training artifacts and pipelines under `.local/ml` for *local-only* workflows (this folder is ignored by git):

- `.local/ml/fine_tuning_guide.md` — (this file)
- `.local/ml/data/raw/` — raw generated JSONL
- `.local/ml/data/clean/` — validated & scrubbed JSONL
- `.local/ml/data/train/` — training split
- `.local/ml/data/eval/` — validation / holdout split
- `.local/ml/runs/` — training run outputs (LoRA adapters, logs)
- `.local/ml/scripts/` — helper wrappers

---

## System packages (Ubuntu 24.04) ⚙️
Run as root / with sudo on a fresh machine:

```bash
sudo apt update
sudo apt install -y git git-lfs build-essential python3-venv python3-pip
```

Note: install CUDA drivers and NVIDIA toolkit according to your GPU before installing CUDA-enabled PyTorch.

---

## Create Python environment (recommended) 🐍

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip wheel setuptools
```

---

## PyTorch install (pick correct wheel) 🔧
Use the PyTorch official selector at https://pytorch.org to get the exact wheel for your CUDA. Example installs:

- CUDA example (change CUDA index as appropriate):
  pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

- CPU-only example:
  pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

> Always prefer the official PyTorch site for the right CUDA/CPU wheel.

---

## Recommended Python stacks

- Unsloth (convenience stack):
  - Install: `pip install -r .local/ml/requirements-unsloth.txt`
  - Packages: unsloth, transformers==5.2.0, peft==0.18.1, trl==0.28.0, accelerate==1.12.0, datasets, safetensors

- Transformers-only (if using bitsandbytes):
  - Install: `pip install -r .local/ml/requirements-transformers-only.txt`
  - Packages: transformers==5.2.0, peft==0.18.1, trl==0.28.0, accelerate==1.12.0, datasets, bitsandbytes, safetensors

---

## Data pipeline must-haves ✅
The pipeline enforces these checks before training (implemented in `scripts/02_validate_clean.py`):

- Secret redaction / fail-closed for high-risk patterns (ghp_, sk-, private keys, URLs)
- Deduplication (exact + fuzzy)
- Holdout split (5–10% recommended)
- Reject low-quality samples (empty, vague, invalid schema)

Always inspect `./.local/ml/data/clean/*.jsonl` before training.

---

## Training defaults (recommended) 🔬
- Method: QLoRA (4-bit) + LoRA adapters (adapter-only saved by default)
- Starter base models: `Qwen2.5-Coder-7B-Instruct` (starter) or `Qwen3-Coder-Next` (agentic)
- Save: adapter-only (LoRA); merging checkpoint optional
- Eval: small repo-specific fixed task suite + format validation + unit tests

The repo's existing trainer `scripts/04_train_qlora.py` follows these defaults and is the recommended entry point.

---

## Quick workflow — minimal example

1) Prepare data (validate, dedupe, split):

```bash
# copy raw JSONL into .local/ml/data/raw/
.local/ml/scripts/prepare_data.sh path/to/raw.jsonl
```

2) Create venv + install recommended stack:

```bash
source .venv/bin/activate
pip install -r .local/ml/requirements-transformers-only.txt
# or for unsloth stack
pip install -r .local/ml/requirements-unsloth.txt
```

3) Train LoRA adapter (example):

```bash
.local/ml/scripts/train_adapter.sh \
  --base-model qwen2.5-coder-7b-instruct \
  --out-dir .local/ml/runs/run-1
```

4) Run evaluation and unit-test gate:

```bash
python scripts/05_eval.py --preds .local/ml/runs/run-1/final/preds.jsonl
```

---

## Files & scripts added (helpers)
- `.local/ml/scripts/prepare_data.sh` — validate + split wrapper
- `.local/ml/scripts/split_holdout.py` — deterministic train/val split
- `.local/ml/scripts/train_adapter.sh` — wrapper for `scripts/04_train_qlora.py`
- `.local/ml/requirements-*.txt` — recommended pip stacks

---

## Validation & evaluation (where to look)
- Data validation: `scripts/02_validate_clean.py`
- QLoRA training: `scripts/04_train_qlora.py`
- Evaluation: `scripts/05_eval.py` + unit test gate `scripts/03_unit_test_gate.py`

---

## Checklist before a full run ✅
1. Secrets scan and manual spot-check of `/.local/ml/data/clean` ✅
2. Holdout split present in `/.local/ml/data/eval/` ✅
3. Venv active and correct PyTorch installed (GPU wheel) ✅
4. Run a short smoke training (TRAIN_STEPS=50) and verify adapter saved ✅

---

## Troubleshooting & tips 💡
- OOM: reduce `--seq-len`, `--batch-size`, or `--lora-r`.
- Use `device_map='auto'` where supported to distribute across GPUs.
- For reproducibility, set `SEED` and `--train-steps` for smoke-tests.

---

If you want, I can: add CI checks for the data pipeline, wire a `make` target, or add a short tutorial notebook showing a full local round.
