# Dataset Card - Heidi AutoTrain Generated Data

## Dataset Overview

- **Name**: heidi-autotrain-synthetic
- **Version**: 1.0
- **Generated**: Automatically via teacher model synthesis
- **License**: CC-BY-4.0 (see license_policy.md)

## Dataset Description

This dataset is synthetically generated for training coding agents. It contains input-output pairs where the input is a coding task instruction and the output is a generated code solution.

### Generation Method

- **Teacher Model**: OpenAI GPT-4o-mini (configurable)
- **Templates**: 8 distinct task types (completion, bug fixing, explanation, refactoring, testing, review, documentation, algorithm implementation)
- **Code Samples**: Synthetic code snippets (no real code from external sources)

### Task Distribution

| Task Type | Description |
|-----------|-------------|
| code_completion | Complete partially written functions |
| bug_fixing | Identify and fix bugs in code |
| code_explanation | Explain what code does |
| refactoring | Improve code quality |
| unit_test_generation | Write unit tests |
| code_review | Review and suggest improvements |
| documentation | Add docstrings and comments |
| algorithm_implementation | Implement algorithms |

## Data Format

Each sample is a JSON object with the following fields:

```json
{
  "id": "round_N_XXXX",
  "instruction": "Task instruction",
  "input": "Full prompt with context",
  "output": "Generated solution",
  "metadata": {
    "task_type": "code_completion",
    "round": 1,
    "timestamp": "2024-01-01T00:00:00",
    "teacher_model": "gpt-4o-mini"
  }
}
```

## Validation & Cleaning

The dataset undergoes rigorous cleaning:

1. **Schema Validation**: All required fields must be present
2. **Secret Detection**: Fail-closed detection of API keys, tokens, passwords
3. **Length Limits**: Input ≤1800 chars, Output ≤2048 chars
4. **Deduplication**: Exact and fuzzy deduplication

### Dropped Sample Reasons

- Missing required fields
- Detected secrets (API keys, tokens, etc.)
- Exceeds length limits
- Duplicate content
- Unit test failures (if enabled)

## Quality Metrics

| Metric | Target |
|--------|--------|
| JSON parse rate | > Format compliance | >90% |
| Repetition rate |95% |
| <10% |
| Secret detection | 100% |

## Usage

This dataset is intended for:
- Fine-tuning coding assistants
- Training code generation models
- Research on synthetic data generation

### Recommended Use

```python
from datasets import load_dataset

dataset = load_dataset("json", data_files="clean_round_1.jsonl")
```

## Limitations

- Synthetic data may not cover all real-world coding scenarios
- Code solutions are generated, not human-written
- May contain logical errors or suboptimal solutions

## Bias & Safety

- **No real code**: All samples are synthetically generated
- **No secrets**: Strict secret detection prevents leakage
- **Public-safe**: Can be shared without privacy concerns
- **No copyrighted content**: Generated independently

## Maintenance

- Auto-generated each training round
- Validated automatically before use
- Version tracked by round number

## Contact

For issues or questions about the dataset, please open an issue on the project repository.
