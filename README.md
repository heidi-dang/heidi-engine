# Heidi Engine - Autonomous Coding Agent

Heidi Engine is a research project for building an autonomous coding agent through iterative self-improvement (Teacher-Student distillation).

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/heidi-dang/heidi-engine.git
cd heidi-engine

# Install dependencies
pip install -e .
```

### 2. Data Collection (The Loop)

Use `loop_repos.sh` to scrape GitHub repositories, generate synthetic training data, and validate it.

**New Powerful Features:**

*   **Stack Presets**: Easily target your tech stack.
    *   `--stack python`: Python projects (`.py`, `.ipynb`)
    *   `--stack cpp`: C++ projects (`.cpp`, `.h`, etc.)
    *   `--stack vite`: Modern frontend (`.ts`, `.tsx`, `.vue`, `.svelte`)
    *   `--stack web`: General web (`.js`, `.ts`)
*   **Smart Filtering**: automatically skips "homework/assignments", checks licenses (MIT/Apache 2.0), and filters by file size.
*   **Golden Repos**: Inject high-quality curated repos (e.g., Flask, React, PyTorch) with `--golden`.
*   **Resume Mode**: Resume interrupted runs with `--resume`.
*   **Global Deduplication**: Merge all data at the end with `--dedupe`.

**Example Command:**

```bash
# Collect high-quality Python data from 100 repos
./scripts/loop_repos.sh \
  --stack python \
  --max 100 \
  --rounds 1 \
  --samples 1000 \
  --resume \
  --golden \
  --dedupe
```

**Push to Hub:**
You can also automatically push the final dataset to Hugging Face:

```bash
./scripts/loop_repos.sh --stack python --max 100 --push-to-hub my-org/my-dataset
```

### 3. Training

You can train in the loop (using `--full` in `loop_repos.sh`) or use the **dedicated training script** for more control.

**Standalone Training:**

```bash
# Train on the deduplicated dataset from step 2
./scripts/train_only.py \
  --data ./autotrain_repos/merged_dataset.jsonl \
  --base-model microsoft/phi-2 \
  --steps 1000 \
  --out-dir ./my_model_output
```

### 4. Monitoring (New!)

A premium, real-time dashboard is available to track your progress.

**1. One-Click TUI Dashboard (Recommended):**
```bash
./scripts/dashboard.sh
```

**2. Web Dashboard:**
Start the telemetry server:
```bash
python3 -m heidi_engine.telemetry init --server
```
Then open **[http://127.0.0.1:7779/](http://127.0.0.1:7779/)**.

Features:
*   Real-time counters (generated, validated, failed)
*   Live training metrics (loss, steps)
*   GPU VRAM monitoring
*   API cost estimation
*   Dark Mode UI

*   Dark Mode UI

### 5. Multi-Machine Monitoring (New!)

Monitor multiple training machines from a single dashboard.

1.  **On the Dashboard Machine**:
    Start the server:
    ```bash
    python3 -m heidi_engine.telemetry init --server
    ```
    Open **[http://127.0.0.1:7779/](http://127.0.0.1:7779/)**.

2.  **On Worker Machines**:
    Run `loop_repos.sh` with `--monitor`:
    ```bash
    ./scripts/loop_repos.sh --stack python --monitor http://<dashboard-ip>:7779
    ```

3.  **View All Runs**:
    Use the dropdown menu in the dashboard header to switch between active runs.

### 6. Multi-Language Support

The engine now supports generating data for multiple programming languages.

*   **Supported Languages**: Python, JavaScript, Go, C++.
*   **Templates**: customizable YAML files in `heidi_engine/templates/`.
*   **Usage**:
    ```bash
    # Generate Python data (default)
    ./scripts/loop_repos.sh --stack python
    
    # Generate JavaScript data
    ./scripts/loop_repos.sh --stack web
    
    # Generate Go data
    ./scripts/loop_repos.sh --stack go
    
    # Generate C++ data
    ./scripts/loop_repos.sh --stack cpp
    ```

## 📂 Project Structure

*   `heidi_engine/`: Core Python package.
*   `scripts/`: Automation scripts.
    *   `loop_repos.sh`: Main data collection entry point.
    *   `train_only.py`: Dedicated QLoRA training script.
    *   `global_dedupe.py`: Data aggregation and deduplication tool.
    *   `01_teacher_generate.py`: Synthetic data generation.
    *   `04_train_qlora.py`: Low-level training script.

## 🛠️ Advanced Usage

### Environment Variables

*   `OPENAI_API_KEY`: Required for the teacher model (GPT-4o).
*   `HF_TOKEN`: Required for pushing to Hugging Face Hub.
*   `SAMPLES_PER_ROUND`: Default samples to generate (default: 50).

### Customizing the Loop

You can tweak `scripts/loop_repos.sh` to change:
*   `VAL_RATIO`: Validation split (default: 0.05)
*   `SLEEP_BETWEEN_REQUESTS`: Rate limiting (default: 0)


## 🌐 Multi-Machine Setup Guide

Heidi Engine is designed to scale across multiple workers reporting to a central dashboard.

### 1. Central Dashboard Machine
On the machine that will host the dashboard:
```bash
# Set a password for security
export TELEMETRY_PASS="your_secure_password"
python3 -m heidi_engine.telemetry_server
```

### 2. Worker Machines
On each worker machine, point to the central dashboard:
```bash
export DASHBOARD_HOST="http://<dashboard-ip>:7779"
export TELEMETRY_PASS="your_secure_password" # Must match server
./scripts/loop_repos.sh --stack python --monitor
```

### 3. Using Docker Compose (Recommended)
You can launch a complete multi-machine environment locally or on a server using Docker:
```bash
docker-compose up --build
```
This starts one telemetry server and one worker by default.

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| **"No runs found"** | Check that `AUTOTRAIN_DIR` is consistent. The default is `~/.local/heidi_engine`. Ensure yours doesn't have a typo (e.g., `heidi-engine`). |
| **Connection Refused** | Ensure the telemetry server is running and the port `7779` is open in your firewall. |
| **Authentication Failed** | Verify that `TELEMETRY_PASS` matches on both the server and the worker. |
| **Validation Failed** | If code validation is skipping too many samples, ensure you have `g++`, `node`, and `go` installed on the worker machine. |

## 🧪 Testing

Run the test suite to verify your installation:
```bash
pytest tests/
```

## 📄 License

MIT License.
