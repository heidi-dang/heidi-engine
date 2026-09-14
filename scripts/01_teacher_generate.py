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
import concurrent.futures
import json
import os
import random
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _ensure_repo_root_on_sys_path() -> None:
    # Allow running this script directly from a source checkout.
    repo_root = Path(__file__).resolve().parents[1]
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)

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
    p.add_argument(
        "--workers",
        type=int,
        default=int(os.environ.get("TEACHER_WORKERS", "1")),
        help="Number of in-process worker threads (OpenAI teacher is network-bound)",
    )
    p.add_argument(
        "--batch-size",
        type=int,
        default=int(os.environ.get("TEACHER_BATCH_SIZE", "1")),
        help="Number of samples per teacher request (reduces overhead)",
    )
    return p.parse_args()


def build_prompt(template: Dict[str, str], code: str, language: str) -> str:
    return template["template"].format(code=code, language=language)


def build_openhei_request(*, instruction: str, input_text: str) -> str:
    max_tokens = int(os.environ.get("TEACHER_MAX_TOKENS", "256"))
    return (
        "Return ONLY strict JSON (no markdown) with keys instruction,input,output.\n"
        "instruction must exactly match the provided instruction.\n"
        "input must exactly match the provided input.\n\n"
        f"Constraints: output must be concise and <= {max_tokens} tokens.\n\n"
        f"instruction: {instruction}\n\n"
        f"input: {input_text}\n"
    )


def build_openhei_batch_request(*, items: List[Tuple[str, str, str]]) -> str:
    """Build a single prompt that asks for a JSON array of (id,instruction,input,output)."""
    max_tokens = int(os.environ.get("TEACHER_MAX_TOKENS", "256"))
    lines: List[str] = []
    for sid, instruction, input_text in items:
        lines.append(f"id: {sid}\ninstruction: {instruction}\ninput: {input_text}")
    joined = "\n\n---\n\n".join(lines)
    return (
        "Return ONLY strict JSON (no markdown).\n"
        "Output must be a JSON array where each element has keys id,instruction,input,output.\n"
        "id must exactly match the provided id.\n"
        "instruction must exactly match the provided instruction.\n"
        "input must exactly match the provided input.\n"
        f"Constraints: each output must be concise and <= {max_tokens} tokens.\n\n"
        + joined
        + "\n"
    )


def legacy_synthetic_output(instruction: str, input_text: str) -> str:
    return f"{instruction}\n\n{input_text}\n\n# (synthetic legacy backend)"


class SampleSpec:
    __slots__ = (
        "idx",
        "round_num",
        "teacher_model",
        "backend",
        "task_type",
        "instruction",
        "input_text",
    )

    def __init__(
        self,
        *,
        idx: int,
        round_num: int,
        teacher_model: str,
        backend: str,
        task_type: str,
        instruction: str,
        input_text: str,
    ) -> None:
        self.idx = idx
        self.round_num = round_num
        self.teacher_model = teacher_model
        self.backend = backend
        self.task_type = task_type
        self.instruction = instruction
        self.input_text = input_text


def _truncate(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return text
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 1)] + "…"


def _cap_output(text: str) -> str:
    # Hard-ish cap to keep runaway generations from exploding dataset size.
    max_tokens = int(os.environ.get("TEACHER_MAX_TOKENS", "256"))
    max_chars = int(os.environ.get("TEACHER_MAX_OUTPUT_CHARS", str(max(512, max_tokens * 8))))
    return _truncate(text, max_chars)


def _pctl(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = int(round((len(s) - 1) * p))
    return float(s[max(0, min(len(s) - 1, k))])


def _now() -> float:
    return time.monotonic()


def _row_from_spec(spec: SampleSpec, *, instruction_out: str, input_out: str, output_out: str) -> Dict[str, Any]:
    return {
        "id": f"round_{spec.round_num}_{spec.idx:04d}",
        "instruction": instruction_out,
        "input": input_out,
        "output": output_out,
        "metadata": {
            "task_type": spec.task_type,
            "round": spec.round_num,
            "timestamp": _utc_now_z(),
            "teacher_model": spec.teacher_model,
            "teacher_backend": spec.backend,
        },
    }


def _generate_specs(*, samples: int, seed: int, round_num: int, backend: str, teacher_model: str, language: str) -> List[SampleSpec]:
    rng = random.Random(seed)
    specs: List[SampleSpec] = []
    max_prompt_chars = int(os.environ.get("TEACHER_MAX_PROMPT_CHARS", "6000"))
    for idx in range(samples):
        template = rng.choice(PROMPT_TEMPLATES)
        code = rng.choice(SYNTHETIC_CODE_SAMPLES)
        instruction = template["instruction"]
        input_text = build_prompt(template, code, language)
        input_text = _truncate(input_text, max_prompt_chars)
        specs.append(
            SampleSpec(
                idx=idx,
                round_num=round_num,
                teacher_model=teacher_model,
                backend=backend,
                task_type=template["task_type"],
                instruction=instruction,
                input_text=input_text,
            )
        )
    return specs


def _openhei_call_batch(
    *,
    teacher: Any,
    repo_dir: str,
    model_id: str,
    agent: str,
    attach_url: Optional[str],
    batch: List[SampleSpec],
) -> Tuple[List[Dict[str, Any]], float, int, int]:
    """Return (rows, latency_sec, prompt_chars, output_chars)."""
    sid_items = [(f"round_{s.round_num}_{s.idx:04d}", s.instruction, s.input_text) for s in batch]
    prompt = build_openhei_batch_request(items=sid_items) if len(batch) > 1 else build_openhei_request(
        instruction=batch[0].instruction,
        input_text=batch[0].input_text,
    )

    t0 = _now()
    assistant_text = teacher.run(
        repo_dir=repo_dir,
        prompt=prompt,
        model_id=model_id,
        agent=agent,
        attach_url=attach_url,
    )
    dt = _now() - t0

    prompt_chars = len(prompt)
    output_chars = len(assistant_text or "")

    try:
        payload = json.loads(assistant_text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"OpenHei teacher output was not valid JSON: {e}")

    if len(batch) == 1:
        if not isinstance(payload, dict):
            raise RuntimeError("OpenHei teacher output was not a JSON object")
        for key in ("instruction", "input", "output"):
            if key not in payload or not isinstance(payload[key], str):
                raise RuntimeError(f"OpenHei teacher output missing/invalid key: {key}")
        s = batch[0]
        return (
            [
                _row_from_spec(
                    s,
                    instruction_out=payload["instruction"],
                    input_out=payload["input"],
                    output_out=_cap_output(payload["output"]),
                )
            ],
            dt,
            prompt_chars,
            output_chars,
        )

    if not isinstance(payload, list):
        raise RuntimeError("OpenHei teacher output was not a JSON array")

    by_id: Dict[str, Dict[str, Any]] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        if not isinstance(item.get("id"), str):
            continue
        by_id[item["id"]] = item

    rows: List[Dict[str, Any]] = []
    for s in batch:
        sid = f"round_{s.round_num}_{s.idx:04d}"
        item = by_id.get(sid)
        if not item:
            raise RuntimeError(f"OpenHei teacher output missing id: {sid}")
        for key in ("instruction", "input", "output"):
            if key not in item or not isinstance(item[key], str):
                raise RuntimeError(f"OpenHei teacher output missing/invalid key for {sid}: {key}")
        rows.append(
            _row_from_spec(
                s,
                instruction_out=item["instruction"],
                input_out=item["input"],
                output_out=_cap_output(item["output"]),
            )
        )

    return (rows, dt, prompt_chars, output_chars)


def write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    args = parse_args()
    random.seed(args.seed)

    verbose = os.environ.get("VERBOSE", "").strip().lower() in {"1", "true", "yes", "y", "on"}
    backend = args.backend

    progress = None
    progress_task_id = None
    use_rich = False
    if backend == "openhei":
        _ensure_repo_root_on_sys_path()

        from heidi_engine.teacher.openhei_teacher import OpenHeiTeacherError, validate_openhei_attach_url

        attach_url = (os.environ.get("OPENHEI_ATTACH") or "").strip()
        if attach_url:
            try:
                validate_openhei_attach_url(attach_url)
            except OpenHeiTeacherError as e:
                raise SystemExit(
                    "OPENHEI_ATTACH validation failed. "
                    "Ensure OPENHEI_ATTACH points at a running OpenHei serve API (not a stale instance). "
                    f"OPENHEI_ATTACH={attach_url!r}. Error: {e}"
                )
            print(f"[INFO] OpenHei attach: {attach_url} (OK)", file=sys.stderr)
        else:
            print("[INFO] OpenHei attach: (DISABLED)", file=sys.stderr)

    # Rich progress bar (TTY only); otherwise fall back to periodic text lines.
    if sys.stderr.isatty():
        try:
            from rich.progress import (
                BarColumn,
                MofNCompleteColumn,
                Progress,
                TaskProgressColumn,
                TextColumn,
                TimeElapsedColumn,
                TimeRemainingColumn,
            )

            progress = Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TaskProgressColumn(show_speed=True),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                transient=False,
                refresh_per_second=10,
            )
            progress_task_id = progress.add_task("Teacher generation", total=args.samples)
            use_rich = True
        except Exception:
            progress = None
            progress_task_id = None
            use_rich = False

    specs = _generate_specs(
        samples=args.samples,
        seed=args.seed,
        round_num=args.round,
        backend=args.backend,
        teacher_model=args.teacher,
        language=args.language,
    )
    rows_by_idx: Dict[int, Dict[str, Any]] = {}

    start = _now()

    # Performance knobs
    workers = max(1, int(args.workers or 1))
    batch_size = max(1, int(args.batch_size or 1))
    if args.backend != "openhei":
        workers = 1
        batch_size = 1

    if backend == "legacy":
        for s in specs:
            rows_by_idx[s.idx] = _row_from_spec(
                s,
                instruction_out=s.instruction,
                input_out=s.input_text,
                output_out=legacy_synthetic_output(s.instruction, s.input_text),
            )
        # Keep the progress line contract.
        print(f"[INFO] Generated {args.samples}/{args.samples} (100%) | 0.00 it/s | ETA 0s", file=sys.stderr)
    else:
        _ensure_repo_root_on_sys_path()
        if not args.repo_dir:
            raise SystemExit("TEACHER_BACKEND=openhei requires --repo-dir (or OUT_DIR)")
        if "/" not in args.teacher:
            raise SystemExit(
                "TEACHER_BACKEND=openhei requires TEACHER_MODEL like 'provider/model' " f"(got {args.teacher!r})"
            )

        from heidi_engine.teacher.base import TeacherRegistry

        teacher = TeacherRegistry.from_env().get("openhei")
        agent = os.environ.get("OPENHEI_AGENT", "")
        attach_url = os.environ.get("OPENHEI_ATTACH") or None

        # Split into batches to reduce overhead.
        batches: List[List[SampleSpec]] = [specs[i : i + batch_size] for i in range(0, len(specs), batch_size)]

        done = 0
        last_print_t = 0.0
        latencies: List[float] = []
        prompt_chars: List[int] = []
        output_chars: List[int] = []
        errors = 0

        def worker(batch: List[SampleSpec]) -> Tuple[List[Dict[str, Any]], float, int, int]:
            return _openhei_call_batch(
                teacher=teacher,
                repo_dir=args.repo_dir,
                model_id=args.teacher,
                agent=agent,
                attach_url=attach_url,
                batch=batch,
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(worker, b) for b in batches]

            if use_rich and progress is not None:
                with progress:
                    for fut in concurrent.futures.as_completed(futs):
                        batch_rows, dt_s, pchars, ochars = fut.result()
                        for r in batch_rows:
                            idx = int(str(r["id"]).split("_")[-1])  # round_X_0001 -> 0001
                            rows_by_idx[idx] = r
                        done = len(rows_by_idx)
                        latencies.append(dt_s)
                        prompt_chars.append(pchars)
                        output_chars.append(ochars)
                        progress.update(progress_task_id, completed=done)
            else:
                for fut in concurrent.futures.as_completed(futs):
                    try:
                        batch_rows, dt_s, pchars, ochars = fut.result()
                    except Exception as e:
                        errors += 1
                        raise
                    for r in batch_rows:
                        idx = int(str(r["id"]).split("_")[-1])
                        rows_by_idx[idx] = r
                    done = len(rows_by_idx)
                    latencies.append(dt_s)
                    prompt_chars.append(pchars)
                    output_chars.append(ochars)

                    now = _now()
                    should_print = verbose or (done % 10 == 0) or (now - last_print_t >= 15.0) or done == args.samples
                    if should_print:
                        elapsed = max(1e-6, now - start)
                        rate = done / elapsed
                        remaining = args.samples - done
                        eta = int(remaining / rate) if rate > 0 else 0
                        pct = (done / args.samples * 100.0) if args.samples else 100.0
                        print(
                            f"[INFO] Generated {done}/{args.samples} ({pct:.0f}%) | {rate:.2f} it/s | ETA {eta}s",
                            file=sys.stderr,
                        )

                        # Metrics line (optional, phone-friendly)
                        if latencies:
                            avg = statistics.mean(latencies)
                            p50 = _pctl(latencies, 0.50)
                            p95 = _pctl(latencies, 0.95)
                            avg_out = int(statistics.mean(output_chars)) if output_chars else 0
                            approx_tokens = avg_out // 4
                            print(
                                f"[METRIC] workers={workers} batch={batch_size} avg={avg:.2f}s p50={p50:.2f}s p95={p95:.2f}s out~{approx_tokens}tok err={errors}",
                                file=sys.stderr,
                            )
                        last_print_t = now

        # Ensure final progress line exists for SSE parsers.
        if done != args.samples:
            print(f"[INFO] Generated {done}/{args.samples} ({(done/args.samples*100.0):.0f}%) | 0.00 it/s | ETA 0s", file=sys.stderr)

    ordered = [rows_by_idx[i] for i in range(args.samples)]
    write_jsonl(args.output, ordered)
    print(f"[OK] Wrote {len(ordered)} samples to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
