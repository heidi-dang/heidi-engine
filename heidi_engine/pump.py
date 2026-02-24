from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
import signal
import shutil
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Sequence, TextIO


def _project_root() -> Optional[Path]:
    env = (os.environ.get("HEIDI_ENGINE_PROJECT_ROOT") or "").strip()
    if env:
        p = Path(env).expanduser().resolve()
        if (p / "scripts").is_dir():
            return p

    # In editable installs, pump.py lives under <repo>/heidi_engine/pump.py.
    try:
        repo = Path(__file__).resolve().parents[1]
        if (repo / "scripts").is_dir():
            return repo
    except Exception:
        pass

    return None


def _lock(f: TextIO, *, block: bool) -> None:
    if os.name == "nt":
        import msvcrt

        # msvcrt.locking locks from current file position.
        f.seek(0)
        if f.tell() == 0:
            f.write("0")
            f.flush()
        f.seek(0)
        mode = msvcrt.LK_LOCK if block else msvcrt.LK_NBLCK
        msvcrt.locking(f.fileno(), mode, 1)
        return

    import fcntl

    flags = fcntl.LOCK_EX
    if not block:
        flags |= fcntl.LOCK_NB
    fcntl.flock(f.fileno(), flags)


def _unlock(f: TextIO) -> None:
    if os.name == "nt":
        import msvcrt

        f.seek(0)
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        return

    import fcntl

    fcntl.flock(f.fileno(), fcntl.LOCK_UN)


@dataclass(frozen=True)
class PumpPaths:
    run_dir: Path

    @property
    def lock_file(self) -> Path:
        return self.run_dir / ".lock"

    @property
    def running_marker(self) -> Path:
        return self.run_dir / "RUNNING.json"

    @property
    def ready_marker(self) -> Path:
        return self.run_dir / "READY.json"

    @property
    def status_file(self) -> Path:
        return self.run_dir / "status.json"

    @property
    def log_file(self) -> Path:
        return self.run_dir / "pump.log"

    @property
    def repos_dir(self) -> Path:
        return self.run_dir / "repos"

    @property
    def merged_dataset(self) -> Path:
        return self.run_dir / "merged_dataset.jsonl"

    @property
    def train_dataset(self) -> Path:
        return self.run_dir / "train.jsonl"

    @property
    def val_dataset(self) -> Path:
        return self.run_dir / "val.jsonl"

    @property
    def adapter_dir(self) -> Path:
        return self.run_dir / "adapter"

    @property
    def eval_dir(self) -> Path:
        return self.run_dir / "eval"

    @property
    def eval_report(self) -> Path:
        return self.eval_dir / "report.json"


def _utc_now_z() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _default_run_id() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("run_%Y%m%d_%H%M%S")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, obj: Dict[str, Any]) -> None:
    _write_text(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def _sum_clean_lines(repos_dir: Path) -> int:
    total = 0
    for p in repos_dir.rglob("clean_round_*.jsonl"):
        total += _count_lines(p)
    return total


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _bool_env(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "y", "on"}


def _tail_follow(path: Path, *, from_start: bool = False) -> None:
    if not path.exists():
        raise SystemExit(f"Log file not found: {path}")

    with path.open("r", encoding="utf-8", errors="replace") as f:
        if not from_start:
            f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if line:
                sys.stdout.write(line)
                sys.stdout.flush()
                continue
            time.sleep(0.25)


@contextlib.contextmanager
def _acquire_lock(paths: PumpPaths, *, force: bool) -> Iterator[TextIO]:
    paths.run_dir.mkdir(parents=True, exist_ok=True)
    f = paths.lock_file.open("a+", encoding="utf-8")
    try:
        try:
            _lock(f, block=False)
        except (BlockingIOError, OSError):
            if not force:
                raise SystemExit(
                    f"Run is already active (lock held): {paths.run_dir}. "
                    "Use --force to terminate the previous run."
                )

            f.seek(0)
            lock_text = f.read().strip()
            old_pid = None
            try:
                if lock_text:
                    old_pid = int(lock_text.splitlines()[0].strip())
            except Exception:
                old_pid = None

            if old_pid:
                try:
                    os.kill(old_pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                except PermissionError:
                    raise SystemExit(
                        f"--force requested but cannot signal PID {old_pid}."
                    )

                # Wait briefly; then try again.
                time.sleep(1)

            _lock(f, block=True)

        f.seek(0)
        f.truncate(0)
        f.write(str(os.getpid()) + "\n")
        f.flush()
        yield f
    finally:
        try:
            _unlock(f)
        except Exception:
            pass
        f.close()


def _update_status(paths: PumpPaths, **updates: Any) -> None:
    status: Dict[str, Any] = {}
    if paths.status_file.exists():
        try:
            status = json.loads(_read_text(paths.status_file))
        except Exception:
            status = {}

    status.update(updates)
    status["updated_at"] = _utc_now_z()
    _write_json(paths.status_file, status)


def _print_status(paths: PumpPaths) -> int:
    if not paths.status_file.exists():
        print("No status found.")
        print(f"Run dir: {paths.run_dir}")
        return 1

    data = json.loads(_read_text(paths.status_file))
    stage = data.get("stage", "unknown")
    print(f"Run dir: {paths.run_dir}")
    print(f"Stage: {stage}")
    for key in ("dataset_lines", "unique_lines", "dedupe_ratio", "train_steps", "eval_summary"):
        if key in data:
            print(f"{key}: {data[key]}")
    return 0


def _run_and_tee(
    cmd: Sequence[str],
    *,
    env: Dict[str, str],
    log_fp: TextIO,
    cwd: Optional[Path] = None,
) -> None:
    log_fp.write("\n$ " + " ".join(cmd) + "\n")
    log_fp.flush()
    proc = subprocess.Popen(
        list(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        cwd=str(cwd) if cwd else None,
        bufsize=1,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        log_fp.write(line)
    code = proc.wait()
    if code != 0:
        raise SystemExit(f"Command failed ({code}): {' '.join(cmd)}")


def _collect_without_git(*, root: Path, paths: PumpPaths, args: argparse.Namespace, env: Dict[str, str], log_fp: TextIO) -> None:
    out_dir = paths.repos_dir / "local"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Use the existing teacher generator script, but write directly to clean_round_*.jsonl
    # so downstream dedupe can merge as usual.
    lang = args.stack
    for r in range(1, int(args.rounds) + 1):
        cmd = [
            sys.executable,
            str(root / "scripts" / "01_teacher_generate.py"),
            "--samples",
            str(args.samples_per_run),
            "--output",
            str(out_dir / f"clean_round_{r}.jsonl"),
            "--backend",
            args.teacher_backend,
            "--teacher",
            args.teacher_model,
            "--round",
            str(r),
            "--language",
            lang,
            "--repo-dir",
            str(paths.run_dir),
            "--seed",
            "42",
        ]
        _run_and_tee(cmd, env=env, log_fp=log_fp, cwd=root)


def _maybe_start_openhei_serve(
    *,
    host: str,
    port: int,
    log_fp: TextIO,
    timeout_sec: float = 20.0,
) -> str:
    from heidi_engine.teacher.openhei_teacher import OpenHeiTeacherError, validate_openhei_attach_url

    attach = f"http://{host}:{port}"
    try:
        validate_openhei_attach_url(attach, timeout_sec=2.5)
        print(f"[INFO] OpenHei attach: {attach} (OK)", file=sys.stderr)
        return attach
    except OpenHeiTeacherError:
        pass

    log_fp.write(f"\n[INFO] Starting openhei serve on {attach}\n")
    log_fp.flush()
    cli_raw = (os.environ.get("OPENHEI_CLI") or "openhei").strip() or "openhei"
    try:
        cli_parts = shlex.split(cli_raw)
    except ValueError:
        cli_parts = ["openhei"]
    if not cli_parts:
        cli_parts = ["openhei"]
    proc = subprocess.Popen(
        [*cli_parts, "serve", "--hostname", host, "--port", str(port)],
        stdout=log_fp,
        stderr=subprocess.STDOUT,
        text=True,
    )

    start = time.monotonic()
    while time.monotonic() - start < timeout_sec:
        try:
            validate_openhei_attach_url(attach, timeout_sec=1.0)
            print(f"[INFO] OpenHei attach: {attach} (OK)", file=sys.stderr)
            return attach
        except OpenHeiTeacherError:
            time.sleep(0.25)

    with contextlib.suppress(Exception):
        proc.terminate()
    raise SystemExit(f"OpenHei serve did not become ready at {attach}/doc")


def _split_train_val(
    *,
    merged: Path,
    train_out: Path,
    val_out: Path,
    val_ratio: float,
) -> tuple[int, int]:
    total = _count_lines(merged)
    if total <= 0:
        raise SystemExit(f"Merged dataset is empty: {merged}")

    if total < 2:
        val_count = 0
    else:
        val_count = int(total * val_ratio)
        if val_count < 1:
            val_count = 1
    train_count = total - val_count
    if train_count < 0:
        train_count = 0

    train_out.parent.mkdir(parents=True, exist_ok=True)
    val_out.parent.mkdir(parents=True, exist_ok=True)

    with merged.open("r", encoding="utf-8") as src, train_out.open(
        "w", encoding="utf-8"
    ) as train_fp, val_out.open("w", encoding="utf-8") as val_fp:
        for i, line in enumerate(src):
            if i < train_count:
                train_fp.write(line)
            else:
                val_fp.write(line)

    return train_count, val_count


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="One-click pump: collect -> dedupe -> train -> eval")
    p.add_argument("--run-id", default=_default_run_id(), help="Run identifier")
    p.add_argument("--runs-dir", default="runs", help="Base runs directory")
    p.add_argument("--force", action="store_true", help="Terminate an already-running run")

    p.add_argument("--status", action="store_true", help="Print status and exit")
    p.add_argument("--tail", action="store_true", help="Tail run log and exit")
    p.add_argument("--tail-from-start", action="store_true", help="Tail log from start")

    p.add_argument("--stack", default=os.environ.get("STACK", "python"))
    p.add_argument("--max-repos", type=int, default=int(os.environ.get("MAX_REPOS", "50")))
    p.add_argument("--rounds", type=int, default=int(os.environ.get("ROUNDS", "2")))
    p.add_argument(
        "--samples-per-run",
        type=int,
        default=int(os.environ.get("SAMPLES_PER_RUN", "100")),
    )
    p.add_argument("--max-requests", type=int, default=int(os.environ.get("MAX_REQUESTS", "10000")))

    p.add_argument(
        "--teacher-backend",
        default=os.environ.get("TEACHER_BACKEND", "openhei"),
        choices=["legacy", "openhei"],
    )
    p.add_argument("--teacher-model", default=os.environ.get("TEACHER_MODEL", "openai/gpt-5.2"))
    p.add_argument("--openhei-attach", default=os.environ.get("OPENHEI_ATTACH", ""))
    p.add_argument("--openhei-agent", default=os.environ.get("OPENHEI_AGENT", ""))
    p.add_argument("--openhei-start", action="store_true", help="Auto-start openhei serve if needed")
    p.add_argument("--openhei-host", default=os.environ.get("OPENHEI_HOST", "127.0.0.1"))
    p.add_argument("--openhei-port", type=int, default=int(os.environ.get("OPENHEI_PORT", "4100")))
    p.add_argument(
        "--openhei-attach-strict",
        action="store_true",
        help="Fail closed on attach errors (no fallback)",
    )

    p.add_argument("--base-model", default=os.environ.get("BASE_MODEL", "mistralai/Mistral-7B-Instruct-v0.2"))
    p.add_argument("--train-steps", type=int, default=int(os.environ.get("TRAIN_STEPS", "1200")))
    p.add_argument("--save-steps", type=int, default=int(os.environ.get("SAVE_STEPS", "100")))
    p.add_argument("--eval-steps", type=int, default=int(os.environ.get("EVAL_STEPS", "200")))
    p.add_argument("--val-ratio", type=float, default=float(os.environ.get("VAL_RATIO", "0.05")))

    p.add_argument("--rerun-eval", action="store_true", help="Re-run evaluation even if report exists")
    p.add_argument(
        "--bench",
        default="quick",
        choices=["quick", "full"],
        help="Evaluation mode (default: quick)",
    )

    return p.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    paths = PumpPaths(run_dir=Path(args.runs_dir) / args.run_id)
    root = _project_root()

    if args.status:
        return _print_status(paths)
    if args.tail:
        _tail_follow(paths.log_file, from_start=args.tail_from_start)
        return 0

    paths.run_dir.mkdir(parents=True, exist_ok=True)
    log_fp = paths.log_file.open("a", encoding="utf-8")

    with _acquire_lock(paths, force=args.force):
        _update_status(paths, stage="starting", run_id=args.run_id, run_dir=str(paths.run_dir), started_at=_utc_now_z())
        _write_json(
            paths.running_marker,
            {
                "run_id": args.run_id,
                "pid": os.getpid(),
                "started_at": _utc_now_z(),
            },
        )

        env = os.environ.copy()
        env["TEACHER_BACKEND"] = args.teacher_backend
        env["TEACHER_MODEL"] = args.teacher_model
        env["STACK"] = args.stack
        env["MAX_REQUESTS"] = str(args.max_requests)

        if args.openhei_attach_strict:
            env["OPENHEI_ATTACH_STRICT"] = "1"

        if args.teacher_backend == "openhei":
            env.setdefault("TEACHER_WORKERS", "1")
            env["OPENHEI_AGENT"] = args.openhei_agent

            attach = (args.openhei_attach or "").strip()
            if attach:
                from heidi_engine.teacher.openhei_teacher import OpenHeiTeacherError, validate_openhei_attach_url

                try:
                    validate_openhei_attach_url(attach)
                    print(f"[INFO] OpenHei attach: {attach} (OK)", file=sys.stderr)
                except OpenHeiTeacherError as e:
                    if args.openhei_start:
                        attach = _maybe_start_openhei_serve(
                            host=args.openhei_host, port=args.openhei_port, log_fp=log_fp
                        )
                    else:
                        raise SystemExit(
                            "OpenHei attach is not reachable. "
                            f"OPENHEI_ATTACH={attach!r}. Error: {e}. "
                            "Fix OPENHEI_ATTACH or pass --openhei-start."
                        )
            else:
                if args.openhei_start:
                    attach = _maybe_start_openhei_serve(
                        host=args.openhei_host, port=args.openhei_port, log_fp=log_fp
                    )
                else:
                    print("[INFO] OpenHei attach: (DISABLED)", file=sys.stderr)

            if attach:
                env["OPENHEI_ATTACH"] = attach

        # ------------------------------------------------------------------
        # COLLECT
        # ------------------------------------------------------------------
        if paths.merged_dataset.exists() and paths.merged_dataset.stat().st_size > 0:
            _update_status(paths, stage="collect_skipped", merged_dataset=str(paths.merged_dataset))
        else:
            _update_status(paths, stage="collecting", repos_dir=str(paths.repos_dir))
            if not root:
                raise SystemExit(
                    "Heidi Engine scripts directory not found. "
                    "Install from a source checkout (editable) or set HEIDI_ENGINE_PROJECT_ROOT."
                )

            if not shutil.which("git"):
                log_fp.write("[WARN] git not found in PATH; collecting without repo cloning.\n")
                log_fp.flush()
                _collect_without_git(root=root, paths=paths, args=args, env=env, log_fp=log_fp)
            else:
                cmd = [
                    "bash",
                    str(root / "scripts" / "loop_repos.sh"),
                    "--stack",
                    args.stack,
                    "--max",
                    str(args.max_repos),
                    "--rounds",
                    str(args.rounds),
                    "--samples",
                    str(args.samples_per_run),
                    "--out-dir",
                    str(paths.repos_dir),
                    "--collect",
                    "--resume",
                    "--sort",
                    "stars",
                    "--order",
                    "desc",
                ]
                _run_and_tee(cmd, env=env, log_fp=log_fp, cwd=root)

        # ------------------------------------------------------------------
        # DEDUPE
        # ------------------------------------------------------------------
        if not paths.merged_dataset.exists() or paths.merged_dataset.stat().st_size == 0:
            _update_status(paths, stage="deduping")
            total_before = _sum_clean_lines(paths.repos_dir)
            if not root:
                raise SystemExit(
                    "Heidi Engine scripts directory not found. "
                    "Install from a source checkout (editable) or set HEIDI_ENGINE_PROJECT_ROOT."
                )
            cmd = [
                sys.executable,
                str(root / "scripts" / "global_dedupe.py"),
                "--data-dir",
                str(paths.repos_dir),
                "--output",
                str(paths.merged_dataset),
            ]
            _run_and_tee(cmd, env=env, log_fp=log_fp, cwd=root)
            unique_after = _count_lines(paths.merged_dataset)
            dedupe_ratio = (unique_after / total_before) if total_before else 1.0
            _update_status(
                paths,
                unique_lines=unique_after,
                total_lines_before_dedupe=total_before,
                dedupe_ratio=dedupe_ratio,
            )

        dataset_lines = _count_lines(paths.merged_dataset)
        dataset_hash = _sha256_file(paths.merged_dataset)
        _update_status(paths, stage="dataset_ready", dataset_lines=dataset_lines, dataset_hash=dataset_hash)

        # ------------------------------------------------------------------
        # SPLIT
        # ------------------------------------------------------------------
        if not paths.train_dataset.exists() or not paths.val_dataset.exists():
            _update_status(paths, stage="splitting")
            train_n, val_n = _split_train_val(
                merged=paths.merged_dataset,
                train_out=paths.train_dataset,
                val_out=paths.val_dataset,
                val_ratio=args.val_ratio,
            )
            _update_status(paths, stage="split_ready", train_lines=train_n, val_lines=val_n)

        # ------------------------------------------------------------------
        # TRAIN
        # ------------------------------------------------------------------
        final_adapter = paths.adapter_dir / "final"
        if final_adapter.exists():
            _update_status(paths, stage="train_skipped", adapter=str(final_adapter))
        else:
            _update_status(paths, stage="training", base_model=args.base_model)
            ckpts = sorted(paths.adapter_dir.glob("checkpoint-*"), key=lambda p: p.name)
            resume_args: list[str] = []
            if ckpts:
                resume_args = ["--resume-from-checkpoint", str(ckpts[-1])]

            if not root:
                raise SystemExit(
                    "Heidi Engine scripts directory not found. "
                    "Install from a source checkout (editable) or set HEIDI_ENGINE_PROJECT_ROOT."
                )

            cmd = [
                sys.executable,
                str(root / "scripts" / "04_train_qlora.py"),
                "--data",
                str(paths.train_dataset),
                "--val-data",
                str(paths.val_dataset),
                "--output",
                str(paths.adapter_dir),
                "--base-model",
                args.base_model,
                "--train-steps",
                str(args.train_steps),
                "--save-steps",
                str(args.save_steps),
                "--eval-steps",
                str(args.eval_steps),
            ] + resume_args
            _run_and_tee(cmd, env=env, log_fp=log_fp, cwd=root)
            _update_status(paths, stage="trained", adapter=str(final_adapter), train_steps=args.train_steps)

        # ------------------------------------------------------------------
        # EVAL
        # ------------------------------------------------------------------
        if paths.eval_report.exists() and not args.rerun_eval:
            _update_status(paths, stage="eval_skipped", eval_report=str(paths.eval_report))
            eval_report_data = json.loads(_read_text(paths.eval_report))
        else:
            _update_status(paths, stage="evaluating")
            paths.eval_dir.mkdir(parents=True, exist_ok=True)
            if not root:
                raise SystemExit(
                    "Heidi Engine scripts directory not found. "
                    "Install from a source checkout (editable) or set HEIDI_ENGINE_PROJECT_ROOT."
                )
            cmd = [
                sys.executable,
                str(root / "scripts" / "05_eval.py"),
                "--adapter",
                str(final_adapter),
                "--data",
                str(paths.val_dataset),
                "--output",
                str(paths.eval_report),
                "--base-model",
                args.base_model,
            ]
            if args.bench == "full":
                # Heavier mode: evaluate full validation set.
                # (quick mode relies on 05_eval.py defaults, which already evaluate all lines
                # unless --num-samples is passed).
                pass
            _run_and_tee(cmd, env=env, log_fp=log_fp, cwd=root)
            eval_report_data = json.loads(_read_text(paths.eval_report))

        eval_summary = (eval_report_data.get("metrics") if isinstance(eval_report_data, dict) else None) or {}
        _update_status(paths, stage="eval_ready", eval_summary=eval_summary)

        # ------------------------------------------------------------------
        # READY
        # ------------------------------------------------------------------
        ready_obj = {
            "run_id": args.run_id,
            "created_at": _utc_now_z(),
            "base_model": args.base_model,
            "teacher_backend": args.teacher_backend,
            "teacher_model": args.teacher_model,
            "adapter_path": str(final_adapter),
            "dataset_path": str(paths.merged_dataset),
            "dataset_lines": dataset_lines,
            "dataset_hash": dataset_hash,
            "eval_report": str(paths.eval_report),
            "eval_summary": eval_summary,
        }
        _write_json(paths.ready_marker, ready_obj)
        _update_status(paths, stage="ready", ready=str(paths.ready_marker))

        with contextlib.suppress(Exception):
            paths.running_marker.unlink()

        print("\n=== PUMP SUMMARY ===")
        print(f"Run dir: {paths.run_dir}")
        dedupe_ratio = json.loads(_read_text(paths.status_file)).get("dedupe_ratio") if paths.status_file.exists() else None
        if isinstance(dedupe_ratio, (int, float)):
            print(f"Dataset: {paths.merged_dataset} ({dataset_lines} lines, dedupe_ratio={dedupe_ratio:.2f})")
        else:
            print(f"Dataset: {paths.merged_dataset} ({dataset_lines} lines)")
        print(f"Adapter: {final_adapter}")
        print(f"Eval:    {paths.eval_report}")
        if eval_summary:
            print(f"Eval metrics: {eval_summary}")
        print(f"READY:   {paths.ready_marker}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
