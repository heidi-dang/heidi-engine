from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from typing import Iterable, List, Optional

from heidi_engine.telemetry import redact_secrets


class OpenHeiTeacherError(RuntimeError):
    pass


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
        cmd = [
            "openhei",
            "run",
            "--format",
            "json",
            "--dir",
            repo_dir,
            "--model",
            model_id,
            "--agent",
            agent,
            "--prompt",
            prompt,
        ]
        if attach_url:
            cmd.extend(["--attach", attach_url])

        env = os.environ.copy()
        env.setdefault("NO_COLOR", "1")
        env.setdefault("OPENHEI_NO_TUI", "1")

        last_err: Optional[str] = None
        for attempt in range(self.retries + 1):
            try:
                res = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_sec,
                    env=env,
                )
            except FileNotFoundError as e:
                raise OpenHeiTeacherError("openhei binary not found in PATH") from e
            except subprocess.TimeoutExpired as e:
                last_err = f"openhei timeout after {self.timeout_sec}s"
                if attempt < self.retries:
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
                if attempt < self.retries:
                    time.sleep(self.retry_backoff_sec * (attempt + 1))
                    continue
                raise OpenHeiTeacherError(last_err)

            try:
                return parse_openhei_jsonl_events(stdout)
            except OpenHeiTeacherError as e:
                last_err = str(e)
                if attempt < self.retries:
                    time.sleep(self.retry_backoff_sec * (attempt + 1))
                    continue
                raise

        raise OpenHeiTeacherError(last_err or "openhei run failed")
