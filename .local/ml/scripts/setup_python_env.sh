#!/usr/bin/env bash
# Minimal environment bootstrap for local fine-tuning
set -euo pipefail

echo "Creating virtual environment at .venv (if not present)"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip wheel setuptools

cat <<'EOF'
Next steps:
 1) Install PyTorch (choose correct CUDA wheel from https://pytorch.org)
    Example (CUDA): pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
    Example (CPU):    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

 2) Install training stack (choose one):
    pip install -r .local/ml/requirements-transformers-only.txt
    # or
    pip install -r .local/ml/requirements-unsloth.txt
EOF
