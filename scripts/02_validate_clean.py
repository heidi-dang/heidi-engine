#!/usr/bin/env python3
"""
================================================================================
02_validate_clean.py - Validation, Deduplication, and Secret Scrubbing Script
================================================================================

PURPOSE:
    Clean and validate generated dataset:
    1. Validate JSONL schema (each line is valid JSON with required fields)
    2. Deduplicate samples (exact and fuzzy dedupe)
    3. Scrub potential secrets (API keys, passwords, tokens)
    4. Filter by length constraints
    5. Sanitize outputs

HOW IT WORKS:
    1. Reads raw JSONL from input
    2. Applies sequential filters:
       - Schema validation (required fields)
       - Secret pattern detection (fail-closed: drop if any found)
       - Length validation (min/max token counts)
       - Deduplication (exact + fuzzy)
    3. Writes cleaned JSONL to output

TUNABLE PARAMETERS (via environment variables):
    - MAX_INPUT_LENGTH: Max input tokens (default: 1800)
    - MAX_OUTPUT_LENGTH: Max output tokens (default: 2048)
    - MIN_INPUT_LENGTH: Min input tokens (default: 10)
    - MIN_OUTPUT_LENGTH: Min output tokens (default: 20)
    - MAX_DUPLICATE_RATIO: Max duplicate ratio to allow (default: 0.8)
    - SECRET_DROP_THRESHOLD: Drop if any secret pattern found (default: 1)

OUTPUT FORMAT (JSONL):
    {"id": "...", "instruction": "...", "input": "...", "output": "...",
     "metadata": {...}, "validation": {"reason": "...", "passed": true}}

SAFETY:
    - FAIL CLOSED: Any sample with potential secrets is dropped
    - Uses regex patterns to detect common secret formats
    - Logs all dropped samples with reasons

================================================================================
"""

import argparse
import hashlib
import os
import re
import sys
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple

# Add project root to sys.path to allow importing heidi_engine
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from heidi_engine.validation.semantic_validator import validate_semantic

    HAS_SEMANTIC_VALIDATOR = True
except ImportError:
    HAS_SEMANTIC_VALIDATOR = False

try:
    from heidi_engine.security import verify_record

    HAS_SECURITY_VALIDATOR = True
except ImportError:
    HAS_SECURITY_VALIDATOR = False

from heidi_engine.utils.io_jsonl import load_jsonl, save_jsonl
from heidi_engine.utils.security_util import enforce_containment

# Lane B: Boundary Control
ALLOWED_BASE = os.getcwd() # Or explicitly verified/pending via config

SKIP_PROVENANCE = os.environ.get("SKIP_PROVENANCE_CHECK", "").lower() in ("1", "true", "yes")

if SKIP_PROVENANCE:
    import warnings

    warnings.warn(
        "SKIP_PROVENANCE_CHECK=1: Provenance verification is DISABLED. This is insecure for production use."
    )

# =============================================================================
# CONFIGURATION - Adjust these for your needs
# =============================================================================

# Required fields in each JSON sample
REQUIRED_FIELDS = ["id", "instruction", "input", "output", "metadata"]

# Secret detection patterns - FAIL CLOSED: any match drops the sample
# TUNABLE: Add more patterns for your use case
SECRET_PATTERNS = [
    # Generic API keys and tokens
    (r'(?i)(api[_-]?key|apikey|secret[_-]?key)\s*[:=]\s*["\']?[\w\-]{20,}', "api_key"),
    (r"(?i)bearer\s+[\w\-]{20,}", "bearer_token"),
    (r'(?i)token\s*[:=]\s*["\']?[\w\-]{20,}', "token"),
    # AWS credentials
    (r"AKIA[0-9A-Z]{16}", "aws_access_key"),
    (r'(?i)aws[_-]?secret[_-]?access[_-]?key\s*[:=]\s*["\']?[\w\/+]{40}', "aws_secret"),
    # Private keys
    (r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----", "private_key"),
    (r"-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----", "ssh_private_key"),
    # Database connection strings
    (r"(?i)(mongodb|postgres|mysql|redis):\/\/[\w:@\/.-]+", "db_url"),
    (r"(?i)postgresql://[\w:@\/.-]+", "postgres_url"),
    # GitHub/GitLab tokens
    (r"ghp_[a-zA-Z0-9]{36}", "github_token"),
    (r"glpat-[a-zA-Z0-9\-]{20,}", "gitlab_token"),
    # OpenAI API keys
    (r"sk-[a-zA-Z0-9]{48,}", "openai_key"),
    # Generic high-entropy strings that look like secrets
    (r'["\'][\w+\/]{40,}["\']', "high_entropy"),
    # Passwords in config-like patterns
    (r'(?i)password\s*[:=]\s*["\'][^"\']{8,}["\']', "password"),
    (r'(?i)pwd\s*[:=]\s*["\'][^"\']{8,}["\']', "password"),
]

# Fields to check for secrets
# TUNABLE: Add/remove fields based on your data structure
SECRET_CHECK_FIELDS = ["instruction", "input", "output", "response", "completion"]


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    TUNABLE:
        --input: Input JSONL file (raw data)
        --output: Output JSONL file (cleaned data)
        --max-input: Max input length in tokens
        --max-output: Max output length in tokens
        --min-input: Min input length in tokens
        --min-output: Min output length in tokens
        --dedupe: Enable deduplication
        --seed: Random seed
    """
    parser = argparse.ArgumentParser(
        description="Validate, deduplicate, and scrub secrets from dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic validation
  python 02_validate_clean.py --input data/raw.jsonl --output data/clean.jsonl

  # With custom length limits
  python 02_validate_clean.py --input data/raw.jsonl --output data/clean.jsonl \\
      --max-input 1500 --max-output 1024
        """,
    )
    parser.add_argument(
        "--input", "-i", type=str, required=True, help="Input JSONL file (raw data)"
    )
    parser.add_argument(
        "--output", "-o", type=str, required=True, help="Output JSONL file (cleaned data)"
    )
    parser.add_argument(
        "--max-input",
        type=int,
        default=int(os.environ.get("MAX_INPUT_LENGTH", 1800)),
        help="Max input length in characters (default: 1800)",
    )
    parser.add_argument(
        "--max-output",
        type=int,
        default=int(os.environ.get("MAX_OUTPUT_LENGTH", 2048)),
        help="Max output length in characters (default: 2048)",
    )
    parser.add_argument(
        "--min-input",
        type=int,
        default=int(os.environ.get("MIN_INPUT_LENGTH", 10)),
        help="Min input length in characters (default: 10)",
    )
    parser.add_argument(
        "--min-output",
        type=int,
        default=int(os.environ.get("MIN_OUTPUT_LENGTH", 20)),
        help="Min output length in characters (default: 20)",
    )
    parser.add_argument("--no-dedupe", action="store_true", help="Skip deduplication step")
    parser.add_argument(
        "--seed",
        type=int,
        default=int(os.environ.get("SEED", 42)),
        help="Random seed (default: 42)",
    )

    return parser.parse_args()


def validate_schema(sample: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate that sample has all required fields.
    """
    for field in REQUIRED_FIELDS:
        if field not in sample:
            return False, f"missing field: {field}"
    return True, "ok"


def enforce_strict_clean_schema(sample: Dict[str, Any]):
    """Lane D: Strict Schema enforcement."""
    REQUIRED = {"id", "instruction", "input", "output", "metadata"}
    missing = REQUIRED - set(sample.keys())
    if missing:
        raise ValueError(f"Missing required keys: {missing}")
    unknown = set(sample.keys()) - REQUIRED
    if unknown:
        raise ValueError(f"Unknown keys: {unknown}")


def detect_secrets(sample: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Detect potential secrets in sample.

    HOW IT WORKS:
        - Checks all specified fields against secret patterns
        - FAIL CLOSED: Returns True (has secrets) if ANY pattern matches

    TUNABLE:
        - Add more SECRET_PATTERNS for your use case
        - Adjust SECRET_CHECK_FIELDS to check more/less fields

    SAFETY:
        - This is a heuristic - may have false positives/negatives
        - For production, consider using dedicated secret scanning tools
    """
    found_secrets = []

    for field in SECRET_CHECK_FIELDS:
        if field not in sample:
            continue

        text = str(sample[field])

        for pattern, secret_type in SECRET_PATTERNS:
            if re.search(pattern, text):
                found_secrets.append(f"{field}:{secret_type}")

    return len(found_secrets) > 0, found_secrets


def check_length_constraints(
    sample: Dict[str, Any], max_input: int, max_output: int, min_input: int, min_output: int
) -> Tuple[bool, str]:
    """
    Check length constraints for input and output.

    HOW IT WORKS:
        - Uses character count as proxy for token count
        - TUNABLE: For more accuracy, use actual token counting

    TUNABLE:
        - Adjust thresholds based on your model's context window
        - For seq_len=2048, keep input under 1800 to leave room for output
    """
    input_text = sample.get("input", "")
    output_text = sample.get("output", "")

    input_len = len(input_text)
    output_len = len(output_text)

    if input_len > max_input:
        return False, f"input too long: {input_len} > {max_input}"

    if output_len > max_output:
        return False, f"output too long: {output_len} > {max_output}"

    if input_len < min_input:
        return False, f"input too short: {input_len} < {min_input}"

    if output_len < min_output:
        return False, f"output too short: {output_len} < {min_output}"

    return True, "ok"


def compute_hash(sample: Dict[str, Any]) -> str:
    """
    Compute hash for deduplication.

    HOW IT WORKS:
        - Hashes the instruction + output combination
        - Ignores metadata for dedupe purposes
    """
    content = sample.get("instruction", "") + sample.get("output", "")
    return hashlib.sha256(content.encode()).hexdigest()


def fuzzy_hash(sample: Dict[str, Any], n: int = 5) -> str:
    """
    Compute fuzzy hash for near-duplicate detection.

    HOW IT WORKS:
        - Uses character n-grams for fuzzy matching
        - Useful for catching samples that are nearly identical

    TUNABLE:
        - Adjust n for sensitivity (lower = more sensitive)
        - n=5 is a good balance for code data
    """
    text = (sample.get("instruction", "") + sample.get("output", "")).lower()
    # Remove whitespace for more robust matching
    text = re.sub(r"\s+", "", text)

    if len(text) < n:
        return text

    ngrams = [text[i : i + n] for i in range(len(text) - n + 1)]
    # Use top 10 most common ngrams as fingerprint
    counter = Counter(ngrams)
    fingerprint = "".join(sorted([ng for ng, _ in counter.most_common(10)]))

    return hashlib.sha256(fingerprint.encode()).hexdigest()


def deduplicate_samples(
    samples: List[Dict[str, Any]], max_dup_ratio: float = 0.8
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Remove duplicate samples.

    HOW IT WORKS:
        1. Exact dedupe: Remove samples with identical instruction+output
        2. Fuzzy dedupe: Remove samples with similar n-gram fingerprints

    TUNABLE:
        - max_dup_ratio: Maximum ratio of duplicates to allow per fuzzy group
        - Set to 0.0 for strict dedupe (keep only 1 per group)
        - Set to 1.0 to disable fuzzy dedupe

    NOTE: We keep samples with unique outputs to maintain diversity
    """
    seen_hashes: Set[str] = set()
    seen_fuzzy: Set[str] = set()
    unique_samples = []
    duplicates = 0

    for sample in samples:
        # Exact hash
        exact_hash = compute_hash(sample)

        if exact_hash in seen_hashes:
            duplicates += 1
            continue

        # Fuzzy hash
        fuzzy = fuzzy_hash(sample)

        if fuzzy in seen_fuzzy:
            # Check if this is a near-duplicate
            duplicates += 1
            continue

        seen_hashes.add(exact_hash)
        seen_fuzzy.add(fuzzy)
        unique_samples.append(sample)

    return unique_samples, duplicates


def process_sample(
    sample: Dict[str, Any],
    max_input: int,
    max_output: int,
    min_input: int,
    min_output: int,
    strict_secrets: bool = True,
) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Process a single sample through all validation steps.

    HOW IT WORKS:
        1. Schema validation
        2. Secret detection (fail-closed)
        3. Length constraints

    RETURNS:
        - Tuple of (processed_sample or None, reason)
    """
    # Step 1: Schema validation
    valid, reason = validate_schema(sample)
    if not valid:
        return None, f"schema: {reason}"

    # Step 2: Secret detection (FAIL CLOSED)
    if strict_secrets:
        has_secrets, secrets = detect_secrets(sample)
        if has_secrets:
            return None, f"secrets: {secrets}"

    # Step 3: Provenance Verification
    if HAS_SECURITY_VALIDATOR and not SKIP_PROVENANCE:
        if not verify_record(sample):
            return None, "provenance: invalid_signature"

    # Step 4: Semantic validation
    if HAS_SEMANTIC_VALIDATOR:
        (s_valid, s_reason), _ = validate_semantic(sample)
        if not s_valid:
            sample["validation"] = {
                "passed": False,
                "reason": "semantic_validation_failed",
                "details": s_reason,
            }
            return None, f"semantic: {s_reason}"

    # Step 4: Length constraints
    valid, reason = check_length_constraints(sample, max_input, max_output, min_input, min_output)
    if not valid:
        return None, f"length: {reason}"

    # Add validation metadata
    sample["validation"] = {"passed": True, "reason": "ok"}

    return sample, "ok"


def main():
    """
    Main entry point for validation and cleaning.
    """
    args = parse_args()

    print(f"[INFO] Loading samples from: {args.input}")
    enforce_containment(args.input, os.getcwd())
    enforce_containment(args.output, os.getcwd())

    # Load raw samples
    raw_samples = load_jsonl(args.input, validate_telemetry=False)
    print(f"[INFO] Loaded {len(raw_samples)} raw samples")

    # Process samples
    valid_samples = []
    dropped_reasons: dict = {}

    for sample in raw_samples:
        try:
            enforce_strict_clean_schema(sample)
        except ValueError as e:
            print(f"[FATAL] Schema violation: {e}", file=sys.stderr)
            sys.exit(1)

        processed, reason = process_sample(
            sample,
            max_input=args.max_input,
            max_output=args.max_output,
            min_input=args.min_input,
            min_output=args.min_output,
            strict_secrets=True,
        )

        if processed is not None:
            valid_samples.append(processed)
        else:
            reason_type = reason.split(":")[0]
            dropped_reasons[reason_type] = dropped_reasons.get(reason_type, 0) + 1

    print(f"[INFO] After validation: {len(valid_samples)} samples")

    # Report dropped samples
    if dropped_reasons:
        print("[INFO] Dropped samples by reason:")
        for reason, count in sorted(dropped_reasons.items()):
            print(f"  - {reason}: {count}")

    # Deduplication (optional)
    if not args.no_dedupe:
        print("[INFO] Running deduplication...")
        max_dup_ratio = float(os.environ.get("MAX_DUPLICATE_RATIO", 0.8))

        valid_samples, num_dupes = deduplicate_samples(valid_samples, max_dup_ratio)
        print(f"[INFO] Removed {num_dupes} duplicate samples")
        print(f"[INFO] After dedupe: {len(valid_samples)} samples")

    # Save cleaned samples
    save_jsonl(valid_samples, args.output)

    # Summary
    print("[OK] Cleaning complete!")
    print(f"  - Input: {len(raw_samples)} samples")
    print(f"  - Output: {len(valid_samples)} samples")
    print(f"  - Dropped: {len(raw_samples) - len(valid_samples)} samples")

    return 0


if __name__ == "__main__":
    sys.exit(main())
