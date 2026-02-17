#!/usr/bin/env python3
"""
================================================================================
04_train_qlora.py - QLoRA Fine-tuning Script
================================================================================

PURPOSE:
    Fine-tune a base model using QLoRA (Quantized LoRA) for efficient
    parameter-efficient training. Uses 4-bit quantization to reduce VRAM.

HOW IT WORKS:
    1. Loads base model with 4-bit quantization
    2. Applies LoRA adapters to attention layers
    3. Loads training data in instruction-following format
    4. Trains with SFTTrainer (from TRL library)
    5. Saves adapter weights for later evaluation/merging

TUNABLE PARAMETERS (via environment variables):
    - BASE_MODEL: Base model to fine-tune (default: microsoft/phi-2)
    - SEQ_LEN: Max sequence length (default: 2048)
    - BATCH_SIZE: Per-device batch size (default: 1)
    - GRAD_ACCUM: Gradient accumulation steps (default: 8)
    - TRAIN_STEPS: Total training steps (default: 500)
    - SAVE_STEPS: Save checkpoint every N steps (default: 100)
    - LR: Learning rate (default: 2e-4)
    - LORA_R: LoRA rank (default: 64)
    - LORA_ALPHA: LoRA alpha (default: 128)
    - LORA_DROPOUT: LoRA dropout (default: 0.1)
    - QUANTIZATION_BITS: Bits for quantization (default: 4)

VRAM-SAFE DEFAULTS (RTX 2080 Ti - 11GB):
    - SEQ_LEN=2048, BATCH_SIZE=1, GRAD_ACCUM=8, 4-bit load, LORA_R=64

OUTPUT:
    - LoRA adapter weights in output directory
    - Training logs and metrics
    - Final adapter: {output_dir}/final/

SAFETY:
    - Uses bitsandbytes for 4-bit quantization (memory efficient)
    - Includes OOM detection and fallback strategy
    - Checkpoints allow resumption on failure

REQUIREMENTS:
    pip install transformers accelerate bitsandbytes trl peft

================================================================================
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    TUNABLE:
        Most parameters can also be set via environment variables.
        CLI args take precedence over env vars.
    """
    parser = argparse.ArgumentParser(
        description="Fine-tune model with QLoRA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic training with defaults
  python 04_train_qlora.py --data data/clean.jsonl --output out_lora/

  # Custom settings for different VRAM
  python 04_train_qlora.py --data data/clean.jsonl --output out_lora/ \\
      --seq-len 1024 --batch-size 2 --lora-r 32
  
  # Resume from checkpoint
  python 04_train_qlora.py --data data/clean.jsonl --output out_lora/ \\
      --resume-from-checkpoint out_lora/checkpoint-100
        """,
    )

    # Data arguments
    parser.add_argument("--data", "-d", type=str, required=True, help="Training data JSONL file")
    parser.add_argument(
        "--output", "-o", type=str, required=True, help="Output directory for LoRA adapter"
    )
    parser.add_argument(
        "--val-data", type=str, default=None, help="Validation data JSONL file (optional)"
    )

    # Model arguments
    parser.add_argument(
        "--base-model",
        type=str,
        default=os.environ.get("BASE_MODEL", "microsoft/phi-2"),
        help="Base model to fine-tune",
    )
    parser.add_argument("--model-revision", type=str, default=None, help="Model revision to use")

    # Training arguments - VRAM knobs
    parser.add_argument(
        "--seq-len",
        type=int,
        default=int(os.environ.get("SEQ_LEN", 2048)),
        help="Max sequence length (default: 2048)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=int(os.environ.get("BATCH_SIZE", 1)),
        help="Per-device batch size (default: 1)",
    )
    parser.add_argument(
        "--grad-accum",
        type=int,
        default=int(os.environ.get("GRAD_ACCUM", 8)),
        help="Gradient accumulation steps (default: 8)",
    )
    parser.add_argument(
        "--train-steps",
        type=int,
        default=int(os.environ.get("TRAIN_STEPS", 500)),
        help="Total training steps (default: 500)",
    )
    parser.add_argument(
        "--save-steps",
        type=int,
        default=int(os.environ.get("SAVE_STEPS", 100)),
        help="Save checkpoint every N steps (default: 100)",
    )
    parser.add_argument(
        "--eval-steps",
        type=int,
        default=int(os.environ.get("EVAL_STEPS", 50)),
        help="Run evaluation every N steps (default: 50)",
    )
    parser.add_argument(
        "--logging-steps", type=int, default=10, help="Log every N steps (default: 10)"
    )
    parser.add_argument("--warmup-steps", type=int, default=50, help="Warmup steps (default: 50)")

    # LoRA arguments
    parser.add_argument(
        "--lora-r",
        type=int,
        default=int(os.environ.get("LORA_R", 64)),
        help="LoRA rank (default: 64)",
    )
    parser.add_argument(
        "--lora-alpha",
        type=int,
        default=int(os.environ.get("LORA_ALPHA", 128)),
        help="LoRA alpha (default: 128)",
    )
    parser.add_argument(
        "--lora-dropout",
        type=float,
        default=float(os.environ.get("LORA_DROPOUT", 0.1)),
        help="LoRA dropout (default: 0.1)",
    )
    parser.add_argument(
        "--lora-target-modules",
        type=str,
        default="q_proj,v_proj,k_proj,o_proj,gate_proj,up_proj,down_proj",
        help="LoRA target modules (comma-separated)",
    )

    # Quantization arguments
    parser.add_argument(
        "--quant-bits",
        type=int,
        default=int(os.environ.get("QUANTIZATION_BITS", 4)),
        help="Quantization bits (default: 4)",
    )
    parser.add_argument(
        "--quant-type",
        type=str,
        default="nf4",
        choices=["nf4", "fp4"],
        help="Quantization type (default: nf4)",
    )

    # Optimizer arguments
    parser.add_argument(
        "--lr",
        type=float,
        default=float(os.environ.get("LR", 2e-4)),
        help="Learning rate (default: 2e-4)",
    )
    parser.add_argument(
        "--lr-scheduler",
        type=str,
        default="cosine",
        choices=["linear", "cosine", "constant"],
        help="Learning rate scheduler",
    )
    parser.add_argument(
        "--weight-decay", type=float, default=0.01, help="Weight decay (default: 0.01)"
    )

    # Other arguments
    parser.add_argument(
        "--seed",
        type=int,
        default=int(os.environ.get("SEED", 42)),
        help="Random seed (default: 42)",
    )
    parser.add_argument(
        "--resume-from-checkpoint", type=str, default=None, help="Resume from checkpoint path"
    )
    parser.add_argument(
        "--no-gradient-checkpointing",
        action="store_true",
        help="Disable gradient checkpointing (uses more VRAM)",
    )
    parser.add_argument(
        "--trust-remote-code", action="store_true", help="Trust remote code in model"
    )

    return parser.parse_args()


def load_training_data(data_path: str) -> List[Dict[str, Any]]:
    """
    Load training data from JSONL file.

    HOW IT WORKS:
        - Reads JSONL with instruction/input/output format
        - Converts to instruction-following format for training

    TUNABLE:
        - Modify format_instruction() for different prompt formats
        - Add more fields to the output format
    """
    samples = []

    with open(data_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                sample = json.loads(line)
                samples.append(sample)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON line: {e}")
                continue

    logger.info(f"Loaded {len(samples)} training samples")
    return samples


def format_instruction(sample: Dict[str, Any]) -> str:
    """
    Format sample for instruction-following training.

    HOW IT WORKS:
        - Formats as: Instruction: ... Input: ... Output: ...

    TUNABLE:
        - Change template for different model formats
        - Some models need different prompt templates
    """
    instruction = sample.get("instruction", "")
    input_text = sample.get("input", "")
    output = sample.get("output", "")

    # Template: Can be customized for different models
    if input_text:
        formatted = f"""Instruction: {instruction}

Input: {input_text}

Output: {output}"""
    else:
        formatted = f"""Instruction: {instruction}

Output: {output}"""

    return formatted


def setup_model_and_tokenizer(args: argparse.Namespace):
    """
    Setup model with QLoRA quantization and tokenizer.

    HOW IT WORKS:
        1. Load tokenizer with appropriate settings
        2. Configure 4-bit quantization using BitsAndBytes
        3. Load model with quantization config
        4. Apply LoRA adapters

    TUNABLE:
        - quant_bits: 4-bit is standard, can try 8-bit for better quality
        - quant_type: nf4 is better for LLMs, fp4 is faster
        - target_modules: Adjust based on model architecture

    OOM STRATEGY:
        If OOM: reduce seq_len, batch_size, or lora_r
    """
    try:
        from peft import LoraConfig, TaskType, get_peft_model
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    except ImportError:
        logger.error("Missing required packages. Install with:")
        logger.error("  pip install transformers accelerate bitsandbytes peft trl")
        sys.exit(1)

    # Configure quantization
    # TUNABLE: Adjust quantization settings for your GPU
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=(args.quant_bits == 4),
        load_in_8bit=(args.quant_bits == 8),
        bnb_4bit_compute_dtype="float16",  # Use float16 for compute
        bnb_4bit_quant_type=args.quant_type,  # nf4 or fp4
        bnb_4bit_use_double_quant=True,  # Further reduce memory
    )

    logger.info(f"Loading base model: {args.base_model}")
    logger.info(f"Using {args.quant_bits}-bit quantization")

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        args.base_model,
        trust_remote_code=args.trust_remote_code,
        padding_side="right",  # Important for generation
    )

    # Add padding token if not present
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load model with quantization
    model_kwargs = {
        "quantization_config": quantization_config,
        "device_map": "auto",  # Auto distribute across devices
        "trust_remote_code": args.trust_remote_code,
        "low_cpu_mem_usage": True,
    }

    if args.model_revision:
        model_kwargs["revision"] = args.model_revision

    try:
        model = AutoModelForCausalLM.from_pretrained(args.base_model, **model_kwargs)
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        logger.info("Trying without quantization...")

        # Fallback: load without quantization
        model_kwargs.pop("quantization_config", None)
        model = AutoModelForCausalLM.from_pretrained(args.base_model, **model_kwargs)

    # Configure LoRA
    # TUNABLE: Adjust LoRA parameters
    # Higher R = more capacity but more memory
    # Alpha controls how much to mix
    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=args.lora_target_modules.split(","),
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )

    # Apply LoRA to model
    logger.info(f"Applying LoRA (R={args.lora_r}, Alpha={args.lora_alpha})")
    model = get_peft_model(model, lora_config)

    # Print trainable parameters
    model.print_trainable_parameters()

    return model, tokenizer


def setup_trainer(
    args: argparse.Namespace,
    model,
    tokenizer,
    train_data,
    val_data: Optional[List[Dict[str, Any]]] = None,
):
    """
    Setup SFTTrainer for supervised fine-tuning.

    HOW IT WORKS:
        - Uses TRL's SFTTrainer for efficient fine-tuning
        - Configures all training parameters
        - Sets up checkpointing and logging

    TUNABLE:
        - Adjust all training hyperparameters
        - Change dataset formatting
        - Configure callbacks

    REQUIREMENTS:
        pip install trl
    """
    try:
        from transformers import DataCollatorForLanguageModeling, TrainingArguments
        from trl import SFTTrainer
    except ImportError:
        logger.error("TRL not installed. Install with: pip install trl")
        sys.exit(1)

    # Prepare datasets
    # TUNABLE: Use different dataset format if needed
    from datasets import Dataset

    def format_for_training(sample):
        """Format sample for training."""
        text = format_instruction(sample)
        return {"text": text}

    # Create datasets (pre-tokenize with truncation/padding to avoid batching errors)
    train_dataset = Dataset.from_list([format_for_training(s) for s in train_data])
    train_dataset = train_dataset.map(
        lambda batch: tokenizer(
            batch["text"], truncation=True, padding="longest", max_length=args.seq_len
        ),
        batched=True,
    )
    # copy input_ids to labels for causal LM training
    train_dataset = train_dataset.map(lambda batch: {"labels": batch["input_ids"]}, batched=True)

    if val_data:
        val_dataset = Dataset.from_list([format_for_training(s) for s in val_data])
        val_dataset = val_dataset.map(
            lambda batch: tokenizer(
                batch["text"], truncation=True, padding="longest", max_length=args.seq_len
            ),
            batched=True,
        )
        val_dataset = val_dataset.map(lambda batch: {"labels": batch["input_ids"]}, batched=True)
    else:
        val_dataset = None

    # Data collator
    # TUNABLE: mlm=False for causal language models (like GPT)
    from transformers import default_data_collator

    data_collator = default_data_collator

    # Training arguments
    # TUNABLE: All hyperparameters can be adjusted
    training_args = TrainingArguments(
        output_dir=args.output,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        num_train_epochs=1,  # Use steps instead
        max_steps=args.train_steps,
        # Save settings
        save_steps=args.save_steps,
        save_total_limit=3,  # Keep only last 3 checkpoints
        save_strategy="steps",
        # Eval settings
        eval_strategy="steps" if val_data else "no",
        eval_steps=args.eval_steps if val_data else None,
        # Logging
        logging_steps=args.logging_steps,
        logging_dir=f"{args.output}/logs",
        # Optimization
        optim=(
            "paged_adamw_32bit"
            if __import__("importlib").util.find_spec("bitsandbytes")
            else "adamw_torch"
        ),  # Prefer bnb when available
        weight_decay=args.weight_decay,
        max_grad_norm=0.3,  # Gradient clipping
        # Scheduler
        lr_scheduler_type=args.lr_scheduler,
        warmup_steps=args.warmup_steps,
        # Memory optimization
        gradient_checkpointing=not args.no_gradient_checkpointing,
        remove_unused_columns=False,
        # Reproducibility
        seed=args.seed,
        # Misc
        report_to="none",  # Disable wandb/tensorboard
        # Enable bf16 only when supported by the runtime/GPU (safe default: CPU -> False)
        bf16=(
            lambda: (
                __import__("torch").cuda.is_available()
                and getattr(__import__("torch").cuda, "is_bf16_supported", lambda: False)()
            )
        )(),
        fp16=False,  # Use fp16 if bf16 not available
        ddp_find_unused_parameters=False,
    )

    # Create trainer (TRL v0.28+ expects different constructor args)
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        processing_class=tokenizer,
    )

    return trainer


def check_oom_and_suggest():
    """
    Check for OOM in system logs and suggest fixes.

    HOW IT WORKS:
        - Checks dmesg for OOM killer messages
        - Prints suggestions for VRAM reduction
    """
    try:
        import subprocess

        result = subprocess.run(["dmesg"], capture_output=True, text=True, timeout=5)

        if "out of memory" in result.stdout.lower() or "oom" in result.stdout.lower():
            logger.warning("OOM detected in system logs!")
            logger.warning("=" * 50)
            logger.warning("SUGGESTED FIXES:")
            logger.warning("1. Reduce SEQ_LEN: --seq-len 1024")
            logger.warning("2. Reduce batch size: --batch-size 1")
            logger.warning("3. Reduce LoRA rank: --lora-r 32")
            logger.warning("4. Increase grad accum: --grad-accum 16")
            logger.warning("5. Use CPU offloading: add --use-4bit-quantization")
            logger.warning("=" * 50)
    except Exception:
        pass


def main():
    """
    Main entry point for QLoRA training.
    """
    args = parse_args()

    # Setup output directory
    os.makedirs(args.output, exist_ok=True)

    # Log configuration
    logger.info("=" * 50)
    logger.info("QLoRA Training Configuration")
    logger.info("=" * 50)
    logger.info(f"Base model: {args.base_model}")
    logger.info(f"Data: {args.data}")
    logger.info(f"Output: {args.output}")
    logger.info(f"Seq len: {args.seq_len}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Grad accum: {args.grad_accum}")
    logger.info(f"Train steps: {args.train_steps}")
    logger.info(f"LoRA R: {args.lora_r}")
    logger.info(f"Learning rate: {args.lr}")
    logger.info(f"Quantization: {args.quant_bits}-bit")
    logger.info("=" * 50)

    # Load training data
    logger.info("Loading training data...")
    train_data = load_training_data(args.data)

    # Load validation data if provided
    val_data = None
    if args.val_data:
        logger.info("Loading validation data...")
        val_data = load_training_data(args.val_data)

    # Setup model and tokenizer
    logger.info("Setting up model and tokenizer...")
    model, tokenizer = setup_model_and_tokenizer(args)

    # Setup trainer
    logger.info("Setting up trainer...")
    trainer = setup_trainer(args, model, tokenizer, train_data, val_data)

    # Train
    logger.info("Starting training...")
    try:
        train_result = trainer.train()
    except Exception as e:
        logger.error(f"Training failed: {e}")
        check_oom_and_suggest()
        sys.exit(1)

    # Save final model
    logger.info("Saving final adapter...")
    final_path = os.path.join(args.output, "final")
    trainer.save_model(final_path)
    tokenizer.save_pretrained(final_path)

    # Save training metrics
    metrics_path = os.path.join(args.output, "metrics.json")
    metrics = {
        "train_steps": args.train_steps,
        "train_loss": train_result.training_loss
        if hasattr(train_result, "training_loss")
        else None,
        "base_model": args.base_model,
        "lora_r": args.lora_r,
        "lora_alpha": args.lora_alpha,
        "seq_len": args.seq_len,
        "batch_size": args.batch_size,
        "grad_accum": args.grad_accum,
        "lr": args.lr,
    }

    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info("=" * 50)
    logger.info("Training complete!")
    logger.info(f"Adapter saved to: {final_path}")
    logger.info(f"Metrics saved to: {metrics_path}")
    logger.info("=" * 50)

    return 0


if __name__ == "__main__":
    sys.exit(main())
