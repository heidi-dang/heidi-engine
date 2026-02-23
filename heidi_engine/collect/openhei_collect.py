from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from heidi_engine.teacher.base import TeacherRegistry


def _validate_strict_sample(obj: Dict[str, Any]) -> Dict[str, str]:
    for key in ("instruction", "input", "output"):
        if key not in obj or not isinstance(obj[key], str):
            raise ValueError(f"Invalid sample: missing/invalid {key}")
    return {"instruction": obj["instruction"], "input": obj["input"], "output": obj["output"]}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Collect supervised samples via OpenHei")
    p.add_argument("--repo-dir", required=True, help="Repository directory")
    p.add_argument("--prompt-file", required=True, help="Text file with one prompt per line")
    p.add_argument("--output", required=True, help="Output JSONL path")
    p.add_argument(
        "--model",
        default=os.environ.get("TEACHER_MODEL", ""),
        help="Model id in provider/model format (or TEACHER_MODEL env var)",
    )
    p.add_argument("--agent", default=os.environ.get("OPENHEI_AGENT", "general"))
    p.add_argument("--attach", default=os.environ.get("OPENHEI_ATTACH"))
    return p.parse_args()


def main() -> int:
    args = parse_args()
    repo_dir = str(Path(args.repo_dir).resolve())
    model_id = args.model
    if not model_id:
        raise SystemExit("--model (or TEACHER_MODEL) is required")

    teacher = TeacherRegistry.from_env().get("openhei")
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    prompts = [
        line.strip()
        for line in Path(args.prompt_file).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    rows: List[Dict[str, Any]] = []
    for i, prompt in enumerate(prompts):
        assistant_text = teacher.run(
            repo_dir=repo_dir,
            prompt=prompt,
            model_id=model_id,
            agent=args.agent,
            attach_url=args.attach,
        )
        payload = _validate_strict_sample(json.loads(assistant_text))
        payload["id"] = f"openhei_{i:06d}"
        payload["metadata"] = {
            "teacher_backend": "openhei",
            "teacher_model": model_id,
        }
        rows.append(payload)

    with out_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
