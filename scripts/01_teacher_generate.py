#!/usr/bin/env python3
"""Teacher dataset generation.

Outputs JSONL records with keys:
  - id
  - instruction
  - input
  - output
  - metadata

Backends:
  - legacy (default): safe synthetic output
  - openhei: calls `openhei run --format json` via heidi_engine.teacher
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

PROMPT_TEMPLATES: List[Dict[str, str]] = [
    {
        "task_type": "code_completion",
        "instruction": "Complete the following function:",
        "template": "Complete this function:\n\n```{language}\n{code}\n```\n",
    },
    {
        "task_type": "bug_fixing",
        "instruction": "Fix the bugs in this code:",
        "template": "Fix bugs in:\n\n```{language}\n{code}\n```\n",
    },
    {
        "task_type": "refactoring",
        "instruction": "Refactor this code for quality:",
        "template": "Refactor:\n\n```{language}\n{code}\n```\n",
    },
]


SYNTHETIC_CODE_SAMPLES = [
    "def calculate_sum(numbers):\n    \"\"\"Return sum of numbers.\"\"\"\n    # TODO\n",
    "def find_max(values):\n    \"\"\"Return max value in a list.\"\"\"\n    # TODO\n",
    "def fibonacci(n):\n    \"\"\"Return nth Fibonacci number.\"\"\"\n    # TODO\n",
]


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate teacher dataset JSONL")
    p.add_argument(
        "--samples",
        "-n",
        type=int,
        default=int(os.environ.get("SAMPLES_PER_ROUND", "50")),
        help="Number of samples to generate",
    )
    p.add_argument("--output", "-o", required=True, help="Output JSONL path")
    p.add_argument(
        "--teacher",
        default=os.environ.get("TEACHER_MODEL", "gpt-4o-mini"),
        help="Teacher model identifier",
    )
    p.add_argument(
        "--backend",
        default=os.environ.get("TEACHER_BACKEND", "legacy"),
        choices=["legacy", "openhei"],
        help="Teacher backend",
    )
    p.add_argument("--round", type=int, default=1)
    p.add_argument("--language", default=os.environ.get("LANGUAGE", "python"))
    p.add_argument(
        "--repo-dir",
        default=os.environ.get("OUT_DIR", ""),
        help="Repo dir passed to OpenHei (--dir). Defaults to OUT_DIR.",
    )
    p.add_argument("--seed", type=int, default=int(os.environ.get("SEED", "42")))
    return p.parse_args()


def build_prompt(template: Dict[str, str], code: str, language: str) -> str:
    return template["template"].format(code=code, language=language)


def build_openhei_request(*, instruction: str, input_text: str) -> str:
    return (
        "Return ONLY strict JSON (no markdown) with keys instruction,input,output.\n"
        "instruction must exactly match the provided instruction.\n"
        "input must exactly match the provided input.\n\n"
        f"instruction: {instruction}\n\n"
        f"input: {input_text}\n"
    )


def legacy_synthetic_output(instruction: str, input_text: str) -> str:
    return f"{instruction}\n\n{input_text}\n\n# (synthetic legacy backend)"


def generate_one(
    *,
    idx: int,
    round_num: int,
    backend: str,
    teacher_model: str,
    language: str,
    repo_dir: str,
) -> Dict[str, Any]:
    template = random.choice(PROMPT_TEMPLATES)
    code = random.choice(SYNTHETIC_CODE_SAMPLES)
    instruction = template["instruction"]
    input_text = build_prompt(template, code, language)

    if backend == "openhei":
        if not repo_dir:
            raise SystemExit("TEACHER_BACKEND=openhei requires --repo-dir (or OUT_DIR)")
        if "/" not in teacher_model:
            raise SystemExit(
                "TEACHER_BACKEND=openhei requires TEACHER_MODEL like 'provider/model' "
                f"(got {teacher_model!r})"
            )

        from heidi_engine.teacher.base import TeacherRegistry

        teacher = TeacherRegistry.from_env().get("openhei")
        prompt = build_openhei_request(instruction=instruction, input_text=input_text)
        assistant_text = teacher.run(
            repo_dir=repo_dir,
            prompt=prompt,
            model_id=teacher_model,
            agent=os.environ.get("OPENHEI_AGENT", "general"),
            attach_url=os.environ.get("OPENHEI_ATTACH") or None,
        )

        try:
            payload = json.loads(assistant_text)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"OpenHei teacher output was not valid JSON: {e}")

        for key in ("instruction", "input", "output"):
            if key not in payload or not isinstance(payload[key], str):
                raise RuntimeError(f"OpenHei teacher output missing/invalid key: {key}")

        instruction_out = payload["instruction"]
        input_out = payload["input"]
        output_out = payload["output"]
    else:
        instruction_out = instruction
        input_out = input_text
        output_out = legacy_synthetic_output(instruction, input_text)

    return {
        "id": f"round_{round_num}_{idx:04d}",
        "instruction": instruction_out,
        "input": input_out,
        "output": output_out,
        "metadata": {
            "task_type": template["task_type"],
            "round": round_num,
            "timestamp": _utc_now_z(),
            "teacher_model": teacher_model,
            "teacher_backend": backend,
        },
    }


def write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    args = parse_args()
    random.seed(args.seed)

    rows: List[Dict[str, Any]] = []
    for i in range(args.samples):
        rows.append(
            generate_one(
                idx=i,
                round_num=args.round,
                backend=args.backend,
                teacher_model=args.teacher,
                language=args.language,
                repo_dir=args.repo_dir,
            )
        )
        if (i + 1) % 10 == 0:
            print(f"[INFO] Generated {i + 1}/{args.samples}", file=sys.stderr)

    write_jsonl(args.output, rows)
    print(f"[OK] Wrote {len(rows)} samples to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
