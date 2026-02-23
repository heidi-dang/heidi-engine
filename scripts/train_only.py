import argparse
import json
import os
import random
import subprocess
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import optuna
    HAS_OPTUNA = True
except ImportError:
    HAS_OPTUNA = False

try:
    import heidi_cpp
    HAS_HEIDI_CPP = True
except ImportError:
    HAS_HEIDI_CPP = False

import heidi_engine.telemetry as tel  # noqa: E402

# Defaults
DEFAULT_BASE_MODEL = "microsoft/phi-2"
DEFAULT_STEPS = 500
DEFAULT_LR = 2e-4
DEFAULT_VAL_RATIO = 0.1
DEFAULT_BATCH_SIZE = 1
DEFAULT_GRAD_ACCUM = 8
DEFAULT_LORA_R = 64
DEFAULT_SEQ_LEN = 2048
DEFAULT_SEED = 42
DEFAULT_VRAM_THRESHOLD_MB = 1000 # 1GB minimum free

def run_trial(trial, args, script_dir, out_dir, train_file, val_file):
    """Optuna objective function."""
    trial_idx = trial.number

    # Resource Check: Skip trial if VRAM is too low
    if HAS_HEIDI_CPP:
        try:
            free_mem_bytes = heidi_cpp.get_free_gpu_memory()
            if free_mem_bytes > 0:
                free_mem_mb = free_mem_bytes / (1024 * 1024)
                if free_mem_mb < DEFAULT_VRAM_THRESHOLD_MB:
                    print(f"[HPO] Trial {trial_idx} skipped: Low VRAM ({free_mem_mb:.0f}MB < {DEFAULT_VRAM_THRESHOLD_MB}MB)")
                    raise optuna.TrialPruned()
        except Exception as e:
            if isinstance(e, optuna.TrialPruned):
                raise
            print(f"[HPO] GPU check failed: {e}")

    trial_out = out_dir / f"trial_{trial_idx}"
    trial_out.mkdir(parents=True, exist_ok=True)

    # Suggest parameters
    lr = trial.suggest_float("lr", 1e-5, 1e-3, log=True)
    batch_size = trial.suggest_categorical("batch_size", [1, 2, 4])
    lora_r = trial.suggest_int("lora_r", 8, 64, step=8)

    # Gradient accumulation adjustment (keep total batch size similar if possible)
    # Target effective batch size ~8
    grad_accum = max(1, 8 // batch_size)

    print(f"\n[HPO] Trial {trial_idx}: lr={lr:.6f}, batch_size={batch_size}, lora_r={lora_r}, grad_accum={grad_accum}")

    train_cmd = [
        "python3", str(script_dir / "04_train_qlora.py"),
        "--data", str(train_file),
        "--val-data", str(val_file),
        "--output", str(trial_out / "adapter"),
        "--base-model", args.base_model,
        "--seq-len", str(args.seq_len),
        "--batch-size", str(batch_size),
        "--grad-accum", str(grad_accum),
        "--train-steps", str(args.steps),
        "--save-steps", str(args.steps + 1), # Don't save intermediate checkpoints for HPO
        "--eval-steps", str(args.steps),
        "--lora-r", str(lora_r),
        "--lr", str(lr),
        "--seed", str(args.seed)
    ]

    try:
        subprocess.run(train_cmd, check=True, capture_output=True)

        metrics_file = trial_out / "adapter" / "metrics.json"
        if metrics_file.exists():
            with open(metrics_file, "r") as f:
                metrics = json.load(f)
                eval_loss = metrics.get("eval_loss")
                if eval_loss is not None:
                    return eval_loss
    except Exception as e:
        print(f"[HPO] Trial {trial_idx} failed: {e}")

    return float("inf")

def hpo_callback(study, trial):
    """Report best so far to telemetry."""
    if study.best_trial.number == trial.number:
        tel.emit_event(
            event_type="hpo_best",
            message=f"New best params found! Trial {trial.number}, Loss: {trial.value:.4f}",
            level="success",
            # We use trial.value as the latest best loss
        )

def main():
    parser = argparse.ArgumentParser(description="Launch QLoRA training on a specific dataset.")
    parser.add_argument("--data", required=True, help="Path to JSONL dataset")
    parser.add_argument("--out-dir", default="./trained_output", help="Output directory")
    parser.add_argument("--base-model", default=DEFAULT_BASE_MODEL, help="Base model")
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS, help="Training steps")
    parser.add_argument("--lr", type=float, default=DEFAULT_LR, help="Learning rate (ignored if --optuna)")
    parser.add_argument("--val-ratio", type=float, default=DEFAULT_VAL_RATIO, help="Validation ratio")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Batch size (ignored if --optuna)")
    parser.add_argument("--grad-accum", type=int, default=DEFAULT_GRAD_ACCUM, help="Gradient accumulation")
    parser.add_argument("--lora-r", type=int, default=DEFAULT_LORA_R, help="LoRA rank (ignored if --optuna)")
    parser.add_argument("--seq-len", type=int, default=DEFAULT_SEQ_LEN, help="Sequence length")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed")

    # HPO Arguments
    parser.add_argument("--optuna", action="store_true", help="Enable Hyperparameter Optimization")
    parser.add_argument("--n-trials", type=int, default=10, help="Number of HPO trials")

    args = parser.parse_args()

    if args.optuna and not HAS_OPTUNA:
        print("[ERROR] Optuna not found. Install with: pip install optuna")
        sys.exit(1)

    # Paths
    script_dir = Path(__file__).parent.absolute()
    data_path = Path(args.data).absolute()
    out_dir = Path(args.out_dir).absolute()

    # Initialize Telemetry (Filter to only pass fields in telemetry schema)
    # The schema expects uppercase keys, but we can also just pass what it needs.
    tel_config = {
        "BASE_MODEL": args.base_model,
        "SEQ_LEN": args.seq_len,
        "BATCH_SIZE": args.batch_size,
        "GRAD_ACCUM": args.grad_accum,
        "TRAIN_STEPS": args.steps,
        "LORA_R": args.lora_r,
        "LR": str(args.lr),
        "SEED": args.seed,
        "VAL_RATIO": args.val_ratio,
        "OUT_DIR": str(out_dir)
    }
    # Add HPO specific if desired, but telemetry schema might need update first.
    tel.init_telemetry(config=tel_config)

    if not data_path.exists():
        print(f"[ERROR] Data file not found: {data_path}")
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Split Train/Val
    print(f"[INFO] Preparing dataset: {data_path}")
    with open(data_path, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    random.seed(args.seed)
    random.shuffle(lines)

    total = len(lines)
    val_size = max(1, int(total * args.val_ratio))
    train_size = total - val_size

    train_lines = lines[:train_size]
    val_lines = lines[train_size:]

    train_file = out_dir / "train.jsonl"
    val_file = out_dir / "val.jsonl"

    with open(train_file, 'w') as f:
        f.write('\n'.join(train_lines) + '\n')
    with open(val_file, 'w') as f:
        f.write('\n'.join(val_lines) + '\n')

    print(f"       Train: {len(train_lines)} samples, Val: {len(val_lines)} samples")

    # 2. Run Training or HPO
    if args.optuna:
        print(f"\n[INFO] Starting Hyperparameter Optimization ({args.n_trials} trials)...")
        study = optuna.create_study(direction="minimize")
        study.optimize(
            lambda t: run_trial(t, args, script_dir, out_dir, train_file, val_file),
            n_trials=args.n_trials,
            callbacks=[hpo_callback]
        )

        print("\n[SUCCESS] HPO Sweep Complete!")
        print(f"          Best Value:  {study.best_value:.4f}")
        print(f"          Best Params: {json.dumps(study.best_params, indent=2)}")

        # Save best params
        with open(out_dir / "best_params.json", "w") as f:
            json.dump(study.best_params, f, indent=2)

        # Symlink best trial's adapter 'final' directory to the expected 'final' location
        best_trial_dir = out_dir / f"trial_{study.best_trial.number}"
        best_adapter_src = best_trial_dir / "adapter" / "final"
        adapter_dest = out_dir / "final"

        if adapter_dest.exists() or adapter_dest.is_symlink():
            if adapter_dest.is_dir() and not adapter_dest.is_symlink():
                import shutil
                shutil.rmtree(adapter_dest)
            else:
                adapter_dest.unlink()

        try:
            # Create parent if it doesn't exist (it should, but just in case)
            adapter_dest.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(best_adapter_src, adapter_dest)
            print(f"[INFO] Symlinked best trial ({study.best_trial.number}) adapter to {adapter_dest}")
        except Exception as e:
            print(f"[WARN] Failed to symlink best trial: {e}")

        # Optional: Run final training with best params
        print("\n[INFO] Final training with best parameters skipped (manual override recommended).")
        return
    else:
        print("\n[INFO] Starting Single Training Run...")
        train_cmd = [
            "python3", str(script_dir / "04_train_qlora.py"),
            "--data", str(train_file),
            "--val-data", str(val_file),
            "--output", str(out_dir / "adapter"),
            "--base-model", args.base_model,
            "--seq-len", str(args.seq_len),
            "--batch-size", str(args.batch_size),
            "--grad-accum", str(args.grad_accum),
            "--train-steps", str(args.steps),
            "--save-steps", str(max(50, args.steps // 5)),
            "--eval-steps", str(max(50, args.steps // 5)),
            "--lora-r", str(args.lora_r),
            "--lr", str(args.lr),
            "--seed", str(args.seed)
        ]

        try:
            subprocess.run(train_cmd, check=True)
        except subprocess.CalledProcessError:
            print("[ERROR] Training failed.")
            sys.exit(1)

    # 3. Run Evaluation
    print("\n[INFO] Starting Final Evaluation...")
    eval_out = out_dir / "eval_report.json"
    eval_cmd = [
        "python3", str(script_dir / "05_eval.py"),
        "--adapter", str(out_dir / "adapter" / "final"),
        "--data", str(val_file),
        "--output", str(eval_out),
        "--base-model", args.base_model,
        "--seq-len", str(args.seq_len),
        "--temperature", "0.1",
        "--max-new-tokens", "512"
    ]

    try:
        subprocess.run(eval_cmd, check=True)
    except subprocess.CalledProcessError:
        print("[WARN] Evaluation failed.")

    print("\n[SUCCESS] Training pipeline complete!")
    print(f"          Adapter: {out_dir / 'adapter' / 'final'}")
    print(f"          Report:  {eval_out}")

if __name__ == "__main__":
    main()
