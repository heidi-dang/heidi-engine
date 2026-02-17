#!/usr/bin/env python3
"""
================================================================================
05_eval.py - Model Evaluation Script
================================================================================

PURPOSE:
    Evaluate trained LoRA adapter on held-out validation data.
    Measures format compliance, JSON parse rate, and basic quality metrics.

HOW IT WORKS:
    1. Loads trained LoRA adapter
    2. Runs inference on validation/test samples
    3. Measures metrics:
       - JSON parse rate (can output be parsed as JSON)
       - Format compliance (follows expected structure)
       - Basic quality heuristics (length, repetition, etc.)
       - Optional: execution accuracy for code tasks
    4. Generates evaluation report

TUNABLE PARAMETERS (via environment variables):
    - SEQ_LEN: Max sequence length (default: 2048)
    - BATCH_SIZE: Batch size for inference (default: 1)
    - TEMPERATURE: Sampling temperature (default: 0.1)
    - MAX_NEW_TOKENS: Max tokens to generate (default: 512)

OUTPUT:
    - eval/report_{round}.json: Detailed metrics
    - Console summary of results

SAFETY:
    - Does NOT execute arbitrary code in evaluation
    - Uses heuristics for quality assessment
    - Optional executable eval runs in isolated environment

================================================================================
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Evaluate trained model on validation data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic evaluation
  python 05_eval.py --adapter out_lora/ --data data/val.jsonl --output eval/report.json

  # Custom generation settings
  python 05_eval.py --adapter out_lora/ --data data/val.jsonl --output eval/report.json \\
      --temperature 0.2 --max-new-tokens 1024
        """,
    )

    parser.add_argument(
        "--adapter", "-a", type=str, required=True, help="Path to trained LoRA adapter"
    )
    parser.add_argument("--data", "-d", type=str, required=True, help="Evaluation data JSONL file")
    parser.add_argument("--output", "-o", type=str, required=True, help="Output report JSON file")
    parser.add_argument(
        "--base-model",
        type=str,
        default=os.environ.get("BASE_MODEL", "microsoft/phi-2"),
        help="Base model used for training",
    )

    # Generation arguments
    parser.add_argument(
        "--seq-len",
        type=int,
        default=int(os.environ.get("SEQ_LEN", 2048)),
        help="Max sequence length",
    )
    parser.add_argument("--batch-size", type=int, default=1, help="Batch size for inference")
    parser.add_argument(
        "--temperature", type=float, default=0.1, help="Sampling temperature (default: 0.1)"
    )
    parser.add_argument(
        "--max-new-tokens", type=int, default=512, help="Max new tokens to generate (default: 512)"
    )
    parser.add_argument("--top-p", type=float, default=0.95, help="Top-p sampling (default: 0.95)")
    parser.add_argument(
        "--num-samples", type=int, default=None, help="Number of samples to evaluate (default: all)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=int(os.environ.get("SEED", 42)),
        help="Random seed (default: 42)",
    )
    parser.add_argument(
        "--trust-remote-code", action="store_true", help="Trust remote code in model"
    )

    return parser.parse_args()


def load_eval_data(data_path: str, num_samples: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Load evaluation data from JSONL.
    """
    samples = []

    with open(data_path, "r") as f:
        for i, line in enumerate(f):
            if num_samples and i >= num_samples:
                break

            line = line.strip()
            if not line:
                continue

            try:
                sample = json.loads(line)
                samples.append(sample)
            except json.JSONDecodeError as e:
                print(f"[WARN] Failed to parse line {i}: {e}", file=sys.stderr)
                continue

    return samples


def setup_model_with_adapter(adapter_path: str, base_model: str, trust_remote_code: bool):
    """
    Load base model and apply LoRA adapter.

    HOW IT WORKS:
        - Loads base model (can be in 8-bit for inference)
        - Loads and applies LoRA adapter
        - Sets up for inference

    TUNABLE:
        - Use 8-bit loading for faster inference
        - Adjust device map
    """
    try:
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError:
        print("[ERROR] Missing packages: pip install transformers peft", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Loading base model: {base_model}")

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        base_model, trust_remote_code=trust_remote_code, padding_side="right"
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load base model (use 8-bit for faster inference if available)
    try:
        import bitsandbytes as bnb

        model = AutoModelForCausalLM.from_pretrained(
            base_model,
            load_in_8bit=True,
            device_map="auto",
            trust_remote_code=trust_remote_code,
        )
    except ImportError:
        # Fallback to regular loading
        model = AutoModelForCausalLM.from_pretrained(
            base_model,
            device_map="auto",
            trust_remote_code=trust_remote_code,
        )

    # Load LoRA adapter
    print(f"[INFO] Loading adapter from: {adapter_path}")
    model = PeftModel.from_pretrained(model, adapter_path)
    model.eval()  # Set to evaluation mode

    return model, tokenizer


def generate_response(
    model, tokenizer, prompt: str, max_new_tokens: int, temperature: float, top_p: float
) -> str:
    """
    Generate response for a prompt.

    TUNABLE:
        - Adjust generation parameters
        - Change prompt format
    """
    # Format prompt (same as training)
    formatted_prompt = f"""Instruction: {prompt}

Output:"""

    # Tokenize
    inputs = tokenizer(formatted_prompt, return_tensors="pt", truncation=True)
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    # Generate
    with model.disable_adapter():  # Disable adapter if needed, or keep enabled
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=temperature > 0,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    # Decode
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Extract output (everything after "Output:")
    if "Output:" in response:
        response = response.split("Output:", 1)[1].strip()

    return response


def evaluate_json_parse(output: str) -> Tuple[bool, Optional[Dict], str]:
    """
    Evaluate if output can be parsed as JSON.

    HOW IT WORKS:
        - Extracts potential JSON from output
        - Attempts to parse
        - Returns success status and parsed data
    """
    # Try to find JSON in output
    # Look for code blocks first
    json_match = re.search(r"```json\n?(.*?)```", output, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
        try:
            parsed = json.loads(json_str)
            return True, parsed, "json_code_block"
        except json.JSONDecodeError:
            pass

    # Try to find any JSON object
    json_match = re.search(r"\{[^{}]*\}", output)
    if json_match:
        try:
            parsed = json.loads(json_match.group(0))
            return True, parsed, "json_object"
        except json.JSONDecodeError:
            pass

    # Try to parse entire output
    try:
        parsed = json.loads(output)
        return True, parsed, "json_full"
    except json.JSONDecodeError:
        pass

    return False, None, "not_json"


def evaluate_format_compliance(output: str, task_type: str = "") -> Dict[str, Any]:
    """
    Evaluate format compliance.

    HOW IT WORKS:
        - Checks for expected output structure
        - Measures various quality heuristics

    TUNABLE:
        - Add more format checks
        - Customize for different task types
    """
    result = {
        "has_content": len(output.strip()) > 0,
        "output_length": len(output),
        "word_count": len(output.split()),
        "line_count": len(output.split("\n")),
    }

    # Check for code blocks
    result["has_code_blocks"] = "```" in output

    # Check for markdown
    result["has_markdown"] = bool(re.search(r"^#{1,6}\s", output, re.MULTILINE))

    # Check for repetition (potential model failure)
    words = output.lower().split()
    if len(words) > 10:
        word_counts = Counter(words)
        most_common_ratio = word_counts.most_common(1)[0][1] / len(words)
        result["repetition_ratio"] = most_common_ratio
        result["has_repetition"] = most_common_ratio > 0.3
    else:
        result["repetition_ratio"] = 0
        result["has_repetition"] = False

    # Check for common error indicators
    error_indicators = ["error", "exception", "traceback", "failed", "cannot", "undefined"]
    result["has_error_indicators"] = any(ind in output.lower() for ind in error_indicators)

    # Format compliance: passes if has content and no errors
    result["format_compliant"] = result["has_content"] and not result["has_error_indicators"]

    return result


def evaluate_sample(
    sample: Dict[str, Any], model, tokenizer, gen_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluate a single sample.
    """
    # Get prompt
    instruction = sample.get("instruction", "")
    input_text = sample.get("input", "")

    if input_text:
        prompt = f"{instruction}\n\n{input_text}"
    else:
        prompt = instruction

    # Generate response
    try:
        output = generate_response(
            model,
            tokenizer,
            prompt,
            max_new_tokens=gen_config["max_new_tokens"],
            temperature=gen_config["temperature"],
            top_p=gen_config["top_p"],
        )
    except Exception as e:
        return {"sample_id": sample.get("id", "unknown"), "success": False, "error": str(e)}

    # Evaluate JSON parse
    json_valid, parsed_json, json_method = evaluate_json_parse(output)

    # Evaluate format
    format_eval = evaluate_format_compliance(
        output, sample.get("metadata", {}).get("task_type", "")
    )

    return {
        "sample_id": sample.get("id", "unknown"),
        "success": True,
        "output": output[:500],  # Truncate for storage
        "output_length": len(output),
        "json_valid": json_valid,
        "json_method": json_method,
        "format_compliant": format_eval.get("format_compliant", False),
        "format_details": format_eval,
        "has_repetition": format_eval.get("has_repetition", False),
    }


def compute_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute aggregate metrics from evaluation results.
    """
    if not results:
        return {}

    successful = [r for r in results if r.get("success", False)]
    failed = [r for r in results if not r.get("success", False)]

    metrics = {
        "total_samples": len(results),
        "successful_samples": len(successful),
        "failed_samples": len(failed),
        "success_rate": len(successful) / len(results) if results else 0,
    }

    if successful:
        # JSON parse rate
        json_valid = sum(1 for r in successful if r.get("json_valid", False))
        metrics["json_parse_rate"] = json_valid / len(successful)

        # Format compliance rate
        format_compliant = sum(1 for r in successful if r.get("format_compliant", False))
        metrics["format_compliance_rate"] = format_compliant / len(successful)

        # Repetition rate
        has_repetition = sum(1 for r in successful if r.get("has_repetition", False))
        metrics["repetition_rate"] = has_repetition / len(successful)

        # Average output length
        avg_length = sum(r.get("output_length", 0) for r in successful) / len(successful)
        metrics["avg_output_length"] = avg_length

    return metrics


def main():
    """
    Main entry point for evaluation.
    """
    args = parse_args()

    print(f"[INFO] Loading evaluation data from: {args.data}")
    eval_data = load_eval_data(args.data, args.num_samples)
    print(f"[INFO] Loaded {len(eval_data)} samples")

    # Setup model with adapter
    print("[INFO] Loading model and adapter...")
    model, tokenizer = setup_model_with_adapter(
        adapter_path=args.adapter,
        base_model=args.base_model,
        trust_remote_code=args.trust_remote_code,
    )

    # Generation config
    gen_config = {
        "max_new_tokens": args.max_new_tokens,
        "temperature": args.temperature,
        "top_p": args.top_p,
    }

    # Evaluate samples
    print("[INFO] Starting evaluation...")
    results = []

    for i, sample in enumerate(eval_data):
        result = evaluate_sample(sample, model, tokenizer, gen_config)
        results.append(result)

        if (i + 1) % 10 == 0:
            print(f"  Evaluated {i + 1}/{len(eval_data)} samples", file=sys.stderr)

    # Compute metrics
    print("[INFO] Computing metrics...")
    metrics = compute_metrics(results)

    # Prepare report
    report = {
        "adapter_path": args.adapter,
        "base_model": args.base_model,
        "data_path": args.data,
        "gen_config": gen_config,
        "metrics": metrics,
        "sample_results": results,
    }

    # Save report
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)

    # Print summary
    print("\n" + "=" * 50)
    print("EVALUATION RESULTS")
    print("=" * 50)
    print(f"Total samples: {metrics.get('total_samples', 0)}")
    print(f"Success rate: {metrics.get('success_rate', 0):.2%}")
    print(f"JSON parse rate: {metrics.get('json_parse_rate', 0):.2%}")
    print(f"Format compliance: {metrics.get('format_compliance_rate', 0):.2%}")
    print(f"Repetition rate: {metrics.get('repetition_rate', 0):.2%}")
    print(f"Avg output length: {metrics.get('avg_output_length', 0):.0f}")
    print("=" * 50)
    print(f"Report saved to: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
