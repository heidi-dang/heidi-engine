# Heidi Engine: Building an Autonomous Coding Agent

Heidi Engine is an innovative research project designed to create an autonomous coding agent through iterative self-improvement, leveraging a teacher-student distillation approach.

## Getting Started

### Installation
To get the project up and running:
```bash
# Clone the repository
git clone https://github.com/heidi-dang/heidi-engine.git
cd heidi-engine

# Install dependencies
pip install -e .
```

## Data Collection (The Core Loop)

The `loop_repos.sh` script manages the process of scraping GitHub repositories, generating synthetic training data, and validating it in a streamlined workflow.

### Key New Features:

- **Stack Presets**: Customize the process for specific tech stacks.
  - `--stack python`: Targets Python projects (`.py`, `.ipynb` files).
  - `--stack cpp`: Focuses on C++ projects (`.cpp`, `.h`, etc.).
  - `--stack vite`: Suited for modern frontend frameworks (`.ts`, `.tsx`, `.vue`, `.svelte`).
  - `--stack web`: Handles general web development (`.js`, `.ts`).
  - `--stack go`: Targets Go projects (`.go` files).

- **Smart Filtering**: Automatically excludes homework-like repositories, checks for permissive licenses (e.g., MIT or Apache 2.0), and caps file sizes for better efficiency.
- **Golden Repos**: Include curated, high-quality repositories (such as Flask, React, or PyTorch) with `--golden`.
- **Resume Support**: Continue from previous runs using `--resume`.
- **Global Deduplication**: Merge and deduplicate data at the end with `--dedupe`.

By default, the script uses a formula where each round processes up to 33 maximum samples (1 round = 33 max samples). You can override this with custom values for `--rounds` and `--samples`.

### Example Command:
```bash
# Collect high-quality Python data from up to 100 repositories
./scripts/loop_repos.sh \
  --stack python \
  --max 100 \
  --rounds 1 \
  --samples 1000 \
  --resume \
  --golden \
  --dedupe
```

### Uploading to Hugging Face:
Push your final dataset to Hugging Face for easy sharing:
```bash
./scripts/loop_repos.sh --stack python --max 100 --push-to-hub my-org/my-dataset
```

## Model Training

Integrate training into the data collection loop with `--full` in `loop_repos.sh`, or use the dedicated script for more control.

### Standalone Training Example:
```bash
# Train on the deduplicated dataset from data collection
./scripts/train_only.py \
  --data ./autotrain_repos/merged_dataset.jsonl \
  --base-model microsoft/phi-2 \
  --steps 1000 \
  --out-dir ./my_model_output
```

## Monitoring Progress

Track your runs in real time with our dashboard tools.

### Option 1: Simple TUI Dashboard (Recommended):
```bash
./scripts/dashboard.sh
```

### Option 2: Web-Based Dashboard:
Start the telemetry server:
```bash
python3 -m heidi_engine.telemetry init --server
```
Then access it at `http://127.0.0.1:7779/`.

**Highlights:**
- Real-time stats on generation, validation, and failure rates.
- Training metrics like loss and steps.
- GPU VRAM monitoring.
- API cost estimates.
- Dark mode for a modern look.

### Multi-Machine Monitoring
Monitor distributed training from a single dashboard.

1. **On the Dashboard Machine**:
   Launch the server:
   ```bash
   python3 -m heidi_engine.telemetry init --server
   ```
   View at `http://127.0.0.1:7779/`.

2. **On Worker Machines**:
   Include `--monitor` in your command, specifying the dashboard address:
   ```bash
   ./scripts/loop_repos.sh --stack python --monitor http://<dashboard-ip>:7779
   ```

## Performance Optimizations (C++ Extension)

Heidi Engine includes a high-performance C++ extension (`heidi_cpp`) for data-intensive operations, providing:
- **Fast Deduplication**: custom cache-aware hashing.
- **Efficient Transpose**: In-place square matrix transpose for QLoRA prep.
- **Batch Compression**: `zlib`-based vectorized log compression.
- **Resource Management**: `rlimit` wrappers for memory/thread capping.

### 7. Hyperparameter Optimization (HPO) 🔦
Integrated Optuna-powered sweep for finding optimal training parameters.

- **Automated Searches**: Explore `learning_rate`, `batch_size`, and `lora_r`.
- **Resource Aware**: Uses `heidi_cpp` to skip trials if GPU VRAM is low (<1GB).
- **Dashboard Integration**: Real-time broadcasting of "Best So Far" params to the telemetry dashboard.
- **Fail-Safe Trials**: Automated infinite-loss fallback for trials that encounter OOM or script crashes.

**Usage:**
```bash
./scripts/train_only.py --data dataset.jsonl --optuna --n-trials 20
```

---

## System Requirements

### Compiler Requirements for Validation
For full multi-language validation, ensure these compilers are installed:
- `g++` for C++.
- `node` for JavaScript/TypeScript.
- `go` for Go.

## Troubleshooting

- **Connection Issues**: Verify firewall settings and that the telemetry server is running.
- **Authentication Errors**: Set the `TELEMETRY_PASS` environment variable for secure access.
- **Validation Failures**: Check for missing compilers or unsupported languages; fallback logging is enabled.

For more details, see [walkthrough_v1.md](file:///home/heidi/work/heidi-engine-dev1/docs/walkthrough_v1.md).
