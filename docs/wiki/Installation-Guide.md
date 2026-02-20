# Installation Guide

## Environment Requirements
- WSL Ubuntu 22.04+
- Python 3.10+
- NVIDIA GPU with CUDA (optional, but recommended for training)

## Step-by-Step Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/heidi-dang/heidi-engine.git
   cd heidi-engine
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Install the package in editable mode:
   ```bash
   pip install -e .
   ```

4. Verify GPU visibility:
   ```bash
   nvidia-smi
   ```

## Troubleshooting
- **Missing Compilers**: Ensure g++, node, and go are installed for dataset validation.
- **VRAM Issues**: Adjust batch size or sequence length in config if OOM occurs.
