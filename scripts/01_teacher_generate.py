#!/usr/bin/env python3
"""
================================================================================
01_teacher_generate.py - Teacher Dataset Generation Script
================================================================================

PURPOSE:
    Generate synthetic training data using a teacher model. This creates
    input-output pairs suitable for fine-tuning a coding agent.

HOW IT WORKS:
    1. Defines prompt templates for various coding tasks (refactor, debug, etc.)
    2. Calls teacher model API to generate responses
    3. Saves raw output to JSONL for downstream processing

TUNABLE PARAMETERS (via environment variables):
    - SAMPLES_PER_ROUND: Number of samples to generate (default: 50)
    - TEACHER_MODEL: Model to use for generation (default: gpt-4o-mini)
    - MAX_OUTPUT_LENGTH: Max tokens in generated output (default: 2048)
    - SEED: Random seed for reproducibility (default: 42)

OUTPUT FORMAT (JSONL):
    {"id": "round_N_idx", "instruction": "...", "input": "...", "output": "...", "metadata": {...}}

SAFETY:
    - No real code is used - all prompts are synthetic templates
    - Generated outputs are not executed (unit test gate is separate)
    - API keys should be passed via environment variables, never hardcoded

================================================================================
"""

import argparse
import json
import os
import random
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# =============================================================================
# CONFIGURATION - Adjust these for your needs
# =============================================================================

# Prompt templates for generating diverse coding tasks
# Each template produces a specific type of coding task
PROMPT_TEMPLATES = [
    {
        "task_type": "code_completion",
        "instruction": "Complete the following Python function:",
        "template": "Complete this function:\n\n```python\n{code}\n```\n\nProvide the complete implementation.",
    },
    {
        "task_type": "bug_fixing",
        "instruction": "Fix the bugs in this Python code:",
        "template": "Find and fix all bugs in this code:\n\n```python\n{code}\n```\n\nExplain what was wrong and provide the corrected code.",
    },
    {
        "task_type": "code_explanation",
        "instruction": "Explain what this code does:",
        "template": "Explain this code in detail:\n\n```python\n{code}\n```\n\nProvide a line-by-line explanation.",
    },
    {
        "task_type": "refactoring",
        "instruction": "Refactor this code for better quality:",
        "template": "Refactor this code to be more efficient and readable:\n\n```python\n{code}\n```\n\nProvide the refactored version with explanations.",
    },
    {
        "task_type": "unit_test_generation",
        "instruction": "Write unit tests for this code:",
        "template": "Write comprehensive unit tests using pytest for:\n\n```python\n{code}\n```",
    },
    {
        "task_type": "code_review",
        "instruction": "Review this code and suggest improvements:",
        "template": "Perform a code review:\n\n```python\n{code}\n```\n\nIdentify issues and suggest improvements.",
    },
    {
        "task_type": "documentation",
        "instruction": "Add documentation to this code:",
        "template": "Add docstrings and comments to:\n\n```python\n{code}\n```\n\nInclude type hints where appropriate.",
    },
    {
        "task_type": "algorithm_implementation",
        "instruction": "Implement this algorithm:",
        "template": "Implement the {algorithm} algorithm in Python:\n\n{description}",
    },
]

# =============================================================================
# SYNTHETIC CODE SAMPLES - These are generic, public domain code snippets
# Used as seeds for generation. No copyrighted code included.
# =============================================================================

SYNTHETIC_CODE_SAMPLES = [
    # Simple function completion
    "def calculate_sum(numbers):\n    '''Calculate sum of a list'''\n    # TODO: implement",
    # Function with bugs
    "def find_max(lst):\n    for i in lst:\n        if i > max:\n            max = i\n    return max",
    # Class definition
    "class DataProcessor:\n    def __init__(self):\n        self.data = []\n    \n    def add(self, item):\n        # Add item to data",
    # Recursive function
    "def fibonacci(n):\n    if n <= 1:\n        return n\n    else:\n        # return fibonacci",
    # List comprehension
    "def filter_even(numbers):\n    # Return only even numbers",
    # Error handling
    "def parse_number(s):\n    # Convert string to number\n    # Handle errors",
    # File handling
    "def read_file(filename):\n    # Read and return file contents",
    # API handler
    "def handle_request(request):\n    # Process API request\n    return {'status': 'ok'}",
    # Data validation
    "def validate_email(email):\n    # Check if email is valid\n    return False",
    # Sorting
    "def sort_by_key(items, key):\n    # Sort items by key function",
]

ALGORITHMS = [
    ("binary search", "Implement binary search to find element in sorted array"),
    ("quick sort", "Implement quicksort algorithm"),
    ("merge sort", "Implement merge sort algorithm"),
    ("BFS", "Implement breadth-first search"),
    ("DFS", "Implement depth-first search"),
    ("Dijkstra", "Implement Dijkstra's shortest path"),
    ("dynamic programming fib", "Calculate nth fibonacci using dynamic programming"),
    ("two sum", "Find two numbers that add up to target"),
]


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    TUNABLE:
        --samples: Number of samples to generate (default: 50)
        --output: Output JSONL file path
        --teacher: Teacher model name
        --seed: Random seed
        --api-key: API key for teacher model (can use OPENAI_API_KEY env var)
    """
    parser = argparse.ArgumentParser(
        description="Generate synthetic training data using teacher model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 50 samples with default settings
  python 01_teacher_generate.py --output data.jsonl

  # Generate 100 samples with specific model
  python 01_teacher_generate.py --samples 100 --teacher gpt-4o --output data.jsonl

  # Generate with custom seed for reproducibility
  python 01_teacher_generate.py --seed 12345 --output data.jsonl
        """,
    )
    parser.add_argument(
        "--samples",
        "-n",
        type=int,
        default=int(os.environ.get("SAMPLES_PER_ROUND", 50)),
        help="Number of samples to generate (default: 50)",
    )
    parser.add_argument("--output", "-o", type=str, required=True, help="Output JSONL file path")
    parser.add_argument(
        "--teacher",
        type=str,
        default=os.environ.get("TEACHER_MODEL", "gpt-4o-mini"),
        help="Teacher model name (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=int(os.environ.get("SEED", 42)),
        help="Random seed (default: 42)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=os.environ.get("OPENAI_API_KEY", ""),
        help="API key for teacher model (can use OPENAI_API_KEY env var)",
    )
    parser.add_argument(
        "--round", type=int, default=1, help="Current round number (for ID generation)"
    )

    return parser.parse_args()


def generate_prompt(template: Dict[str, str], code_sample: str = "") -> str:
    """
    Generate a prompt from a template.

    HOW IT WORKS:
        - Fills in template with code sample or algorithm description
        - Returns formatted prompt for teacher model

    TUNABLE:
        - Add more template types for different tasks
        - Adjust template format for your needs
    """
    if "{code}" in template["template"]:
        return template["template"].format(code=code_sample)
    elif "{algorithm}" in template["template"]:
        algo_name, algo_desc = random.choice(ALGORITHMS)
        return template["template"].format(algorithm=algo_name, description=algo_desc)
    else:
        return template["template"]


def call_teacher_model(
    prompt: str, model: str, api_key: str, max_tokens: int = 2048
) -> Optional[str]:
    """
    Call the teacher model API to generate a response.

    HOW IT WORKS:
        - Uses OpenAI API (or compatible) to generate completion
        - Falls back to local model if API key not provided

    TUNABLE:
        - Change API endpoint for different providers
        - Adjust temperature, top_p for different creativity levels
        - Modify max_tokens based on expected output length

    SAFETY:
        - API key is passed via environment, never logged
        - Fail gracefully if API call fails
    """
    # Check if we have an API key
    if not api_key:
        print("[WARN] No API key provided, using synthetic fallback", file=sys.stderr)
        return generate_synthetic_response(prompt)

    try:
        # Import openai - install with: pip install openai
        import openai

        openai.api_key = api_key

        # For OpenAI compatible APIs, set base URL if needed
        # openai.api_base = "https://api.your-provider.com/v1"

        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful coding assistant that generates high-quality, well-documented code.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,  # Balance creativity and determinism
            max_tokens=max_tokens,  # Max response length
            top_p=0.95,  # Nucleus sampling
            frequency_penalty=0.0,  # Don't repeat similar phrases
            presence_penalty=0.0,  # Don't favor new topics
        )

        return response.choices[0].message.content

    except ImportError:
        print("[WARN] openai package not installed, using synthetic fallback", file=sys.stderr)
        return generate_synthetic_response(prompt)
    except Exception as e:
        print(f"[WARN] API call failed: {e}", file=sys.stderr)
        return generate_synthetic_response(prompt)


def generate_synthetic_response(prompt: str) -> str:
    """
    Generate a synthetic response when no API is available.

    HOW IT WORKS:
        - Creates a basic response based on prompt type
        - Ensures pipeline can run without external API

    TUNABLE:
        - Expand this with more sophisticated synthetic generation
        - Consider using a local model (e.g., llama.cpp) as fallback
    """
    # Simple synthetic responses for each task type
    responses = [
        """Here's the solution:

```python
def solution():
    # Your implementation here
    pass
```

This implements the requested functionality with proper error handling.""",
        """I'll help you with this coding task:

```python
def process_data(data):
    '''Process input data and return result'''
    result = []
    for item in data:
        if item:
            result.append(item.strip())
    return result
```

This provides a clean implementation with appropriate documentation.""",
        """Here's a complete solution:

```python
class Handler:
    def __init__(self):
        self.state = {}

    def execute(self, input_data):
        # Process the input
        return {"result": "success", "data": input_data}
```

The code handles the main use cases with proper structure.""",
    ]

    return random.choice(responses)


def generate_sample(
    idx: int,
    round_num: int,
    template: Dict[str, str],
    teacher_model: str,
    api_key: str,
    max_output: int,
) -> Dict[str, Any]:
    """
    Generate a single training sample.

    HOW IT WORKS:
        1. Selects a random template and code sample
        2. Generates prompt from template
        3. Calls teacher model for response
        4. Constructs sample with metadata

    TUNABLE:
        - Adjust template selection for different task distributions
        - Modify metadata fields as needed
    """
    # Select random code sample or algorithm
    if template["task_type"] in ["algorithm_implementation"]:
        algo_name, algo_desc = random.choice(ALGORITHMS)
        code_sample = f"Algorithm: {algo_name}\nDescription: {algo_desc}"
    else:
        code_sample = random.choice(SYNTHETIC_CODE_SAMPLES)

    # Generate prompt
    prompt = generate_prompt(template, code_sample)

    # Get response from teacher
    output = call_teacher_model(prompt, teacher_model, api_key, max_output)

    if output is None:
        output = generate_synthetic_response(prompt)

    # Construct sample
    sample = {
        "id": f"round_{round_num}_{idx:04d}",
        "instruction": template["instruction"],
        "input": prompt,
        "output": output,
        "metadata": {
            "task_type": template["task_type"],
            "round": round_num,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "teacher_model": teacher_model,
        },
    }

    return sample


def generate_dataset(
    num_samples: int, round_num: int, teacher_model: str, api_key: str, max_output: int, seed: int
) -> List[Dict[str, Any]]:
    """
    Generate the complete dataset for a round.

    HOW IT WORKS:
        1. Sets random seed for reproducibility
        2. Distributes samples across different task types
        3. Generates each sample individually

    TUNABLE:
        - Adjust task type distribution by modifying weights
        - Add more templates for coverage
    """
    random.seed(seed)

    samples = []

    # Distribute samples across task types evenly
    for i in range(num_samples):
        # Select template (could weight this for different distributions)
        template = random.choice(PROMPT_TEMPLATES)

        sample = generate_sample(
            idx=i,
            round_num=round_num,
            template=template,
            teacher_model=teacher_model,
            api_key=api_key,
            max_output=max_output,
        )

        samples.append(sample)

        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"  Generated {i + 1}/{num_samples} samples", file=sys.stderr)

    return samples


def save_jsonl(samples: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save samples to JSONL file.

    HOW IT WORKS:
        - Writes one JSON object per line
        - Creates parent directories if needed
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        for sample in samples:
            f.write(json.dumps(sample) + "\n")

    print(f"[OK] Saved {len(samples)} samples to {output_path}")


def main():
    """
    Main entry point for dataset generation.

    TUNABLE:
        - All parameters can be adjusted via CLI args or env vars
        - See parse_args() for full list of options
    """
    args = parse_args()

    print(f"[INFO] Generating {args.samples} samples (round {args.round})")
    print(f"[INFO] Teacher model: {args.teacher}")
    print(f"[INFO] Output file: {args.output}")
    print(f"[INFO] Seed: {args.seed}")

    # Generate dataset
    samples = generate_dataset(
        num_samples=args.samples,
        round_num=args.round,
        teacher_model=args.teacher,
        api_key=args.api_key,
        max_output=int(os.environ.get("MAX_OUTPUT_LENGTH", 2048)),
        seed=args.seed,
    )

    # Save to file
    save_jsonl(samples, args.output)

    print("[OK] Dataset generation complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
