from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, List, Optional

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from heidi_engine.telemetry import redact_secrets


class OpenHeiTeacherError(RuntimeError):
    pass


def _bool_env(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "y", "on"}


def _contains_session_not_found(text: str) -> bool:
    return "session not found" in (text or "").lower()


def _doc_url(attach_url: str) -> str:
    url = (attach_url or "").strip().rstrip("/")
    if not url:
        return ""
    if url.endswith("/doc"):
        return url
    return url + "/doc"


@lru_cache(maxsize=32)
def validate_openhei_attach_url(attach_url: str, *, timeout_sec: float = 2.5) -> None:
    """Fail-fast if OPENHEI_ATTACH doesn't look reachable.

    Contract: GET {OPENHEI_ATTACH}/doc returns HTTP 200.
    This is cached per-process to avoid per-sample network calls.
    """

    doc = _doc_url(attach_url)
    if not doc:
        raise OpenHeiTeacherError("OPENHEI_ATTACH is empty")

    req = Request(doc, method="GET")
    try:
        with urlopen(req, timeout=timeout_sec) as resp:  # nosec - URL comes from env
            status = getattr(resp, "status", None) or 200
            if int(status) != 200:
                raise OpenHeiTeacherError(
                    f"OPENHEI_ATTACH validation failed: GET {doc} returned HTTP {status}"
                )
    except HTTPError as e:
        raise OpenHeiTeacherError(
            f"OPENHEI_ATTACH validation failed: GET {doc} returned HTTP {e.code}"
        ) from e
    except URLError as e:
        raise OpenHeiTeacherError(
            f"OPENHEI_ATTACH validation failed: GET {doc} failed ({e.reason})"
        ) from e
    except TimeoutError as e:
        raise OpenHeiTeacherError(f"OPENHEI_ATTACH validation failed: GET {doc} timed out") from e


def _iter_jsonl_lines(text: str) -> Iterable[dict]:
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            # Fail-closed: JSON output is a contract.
            raise OpenHeiTeacherError("openhei --format json emitted non-JSON line")


def parse_openhei_jsonl_events(stdout: str) -> str:
    """Parse `openhei run --format json` JSONL and return final text.

Rules (Path B contract):
  - Collect events where `type == 'text'` and `part.time.end` exists.
  - Concatenate `part.text` in order.
  - If any error event is present, fail-closed.
  - If no completed text parts exist, fail-closed.
  """

    parts: List[str] = []
    errors: List[str] = []

    for event in _iter_jsonl_lines(stdout):
        event_type = event.get("type")

        if event_type == "error":
            msg = event.get("message") or event.get("error") or "openhei error"
            errors.append(str(msg))
            continue

        # Some versions wrap errors inside a session object.
        if event_type == "session":
            sess = event.get("session") or {}
            if isinstance(sess, dict) and sess.get("error"):
                errors.append(str(sess.get("error")))
            continue

        if event_type != "text":
            continue

        part = event.get("part")
        if not isinstance(part, dict):
            continue

        time_obj = part.get("time")
        if not isinstance(time_obj, dict) or not time_obj.get("end"):
            continue

        text = part.get("text")
        if isinstance(text, str) and text:
            parts.append(text)

    if errors:
        raise OpenHeiTeacherError("openhei stream error: " + " | ".join(errors[:3]))

    if not parts:
        raise OpenHeiTeacherError("openhei stream contained no completed text parts")

    return "".join(parts).strip()


@dataclass
class OpenHeiTeacher:
    name: str = "openhei"
    timeout_sec: int = 600
    max_stdout_chars: int = 5_000_000
    retries: int = 2
    retry_backoff_sec: float = 2.0

    def run(
        self,
        *,
        repo_dir: str,
        prompt: str,
        model_id: str,
        agent: str,
        attach_url: Optional[str] = None,
    ) -> str:
        strict_attach = _bool_env("OPENHEI_ATTACH_STRICT", "0")
        attach_url = (attach_url or "").strip() or None
        if attach_url:
            validate_openhei_attach_url(attach_url)

        # OpenHei Path-B: prompt is provided via stdin (no --prompt flag).
        stdin_text = prompt if prompt.endswith("\n") else (prompt + "\n")

        env = os.environ.copy()
        env.setdefault("NO_COLOR", "1")
        env.setdefault("OPENHEI_NO_TUI", "1")

        def build_cmd(maybe_attach: Optional[str]) -> list[str]:
            cmd = [
                "openhei",
                "run",
                "--format",
                "json",
                "--dir",
                repo_dir,
                "--model",
                model_id,
            ]

            # OpenHei distinguishes primary agents vs subagents. Subagents like
            # "general" can trigger failures when using `--attach`, so treat them
            # as "use default primary agent" by omitting the flag.
            if agent and agent not in {"general", "explore"}:
                cmd.extend(["--agent", agent])
            if maybe_attach:
                cmd.extend(["--attach", maybe_attach])
            return cmd

        def run_cmd(cmd: list[str], *, retries: int) -> str:
            last_err: Optional[str] = None
            for attempt in range(retries + 1):
                try:
                    res = subprocess.run(
                        cmd,
                        input=stdin_text,
                        capture_output=True,
                        text=True,
                        timeout=self.timeout_sec,
                        env=env,
                    )
                except FileNotFoundError as e:
                    raise OpenHeiTeacherError("openhei binary not found in PATH") from e
                except subprocess.TimeoutExpired as e:
                    last_err = f"openhei timeout after {self.timeout_sec}s"
                    if attempt < retries:
                        time.sleep(self.retry_backoff_sec * (attempt + 1))
                        continue
                    raise OpenHeiTeacherError(last_err) from e

                stdout = res.stdout or ""
                stderr = redact_secrets(res.stderr or "")

                if len(stdout) > self.max_stdout_chars:
                    raise OpenHeiTeacherError(
                        f"openhei stdout exceeded limit ({len(stdout)} chars > {self.max_stdout_chars})"
                    )

                if res.returncode != 0:
                    last_err = (stderr.strip() or "openhei run failed")[:2000]
                    # Session-not-found indicates attach context is invalid; do not keep retrying blindly.
                    if _contains_session_not_found(last_err):
                        raise OpenHeiTeacherError(last_err)
                    if attempt < retries:
                        time.sleep(self.retry_backoff_sec * (attempt + 1))
                        continue
                    raise OpenHeiTeacherError(last_err)

                try:
                    return parse_openhei_jsonl_events(stdout)
                except OpenHeiTeacherError as e:
                    last_err = str(e)
                    if _contains_session_not_found(last_err):
                        raise
                    if attempt < retries:
                        time.sleep(self.retry_backoff_sec * (attempt + 1))
                        continue
                    raise

            raise OpenHeiTeacherError(last_err or "openhei run failed")

        # Attach-first, with specific recovery for stale attach sessions.
        if attach_url:
            cmd_attach = build_cmd(attach_url)
            try:
                return run_cmd(cmd_attach, retries=self.retries)
            except OpenHeiTeacherError as e:
                if not _contains_session_not_found(str(e)):
                    raise
                if strict_attach:
                    raise

                print(
                    "[WARN] OpenHei attach failed with 'Session not found'; retrying once...",
                    file=sys.stderr,
                )
                try:
                    return run_cmd(cmd_attach, retries=0)
                except OpenHeiTeacherError as e2:
                    if not _contains_session_not_found(str(e2)):
                        raise

                    print(
                        "[WARN] OpenHei attach still failing; falling back to non-attach mode.",
                        file=sys.stderr,
                    )
                    cmd_no_attach = build_cmd(None)
                    return run_cmd(cmd_no_attach, retries=self.retries)

        # Non-attach mode.
        return run_cmd(build_cmd(None), retries=self.retries)
