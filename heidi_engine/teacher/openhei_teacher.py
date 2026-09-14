from __future__ import annotations

import json
import os
import random
import socket
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Optional, Tuple

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import quote

from heidi_engine.telemetry import redact_secrets


class OpenHeiTeacherError(RuntimeError):
    pass


def _bool_env(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "y", "on"}


def _contains_session_not_found(text: str) -> bool:
    return "session not found" in (text or "").lower()


def _is_retryable_error(text: str) -> bool:
    lower = (text or "").lower()
    if not lower:
        return False
    if "429" in lower or "too many requests" in lower or "rate limit" in lower:
        return True
    if "usage limit" in lower:
        return True
    if "timeout" in lower or "timed out" in lower or "temporarily unavailable" in lower:
        return True
    if "502" in lower or "503" in lower or "504" in lower or "bad gateway" in lower:
        return True
    return False


def _sleep_backoff(base: float, attempt: int) -> None:
    # Exponential backoff with jitter to avoid synchronized retry storms.
    delay = base * (2**attempt)
    delay = min(delay, 60.0)
    delay += random.uniform(0.0, base)
    time.sleep(delay)


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


def _api_url(base: str, path: str) -> str:
    b = (base or "").strip().rstrip("/")
    p = (path or "").strip()
    if not p.startswith("/"):
        p = "/" + p
    return b + p


def _http_json(method: str, url: str, payload: Optional[dict], *, timeout_sec: float) -> Any:
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = Request(url, method=method)
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urlopen(req, data=data, timeout=timeout_sec) as resp:  # nosec
            text = resp.read().decode("utf-8", errors="replace")
    except HTTPError as e:
        text = (e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else "")
        raise OpenHeiTeacherError(f"OpenHei API error: {e.code} {text[:500]}") from e
    except URLError as e:
        raise OpenHeiTeacherError(f"OpenHei API request failed: {e.reason}") from e
    except TimeoutError as e:
        raise OpenHeiTeacherError(f"OpenHei API request timed out: {url}") from e

    try:
        return json.loads(text) if text else {}
    except json.JSONDecodeError as e:
        raise OpenHeiTeacherError(f"OpenHei API returned non-JSON: {text[:500]}") from e


def _http_stream(method: str, url: str, *, timeout_sec: float):
    req = Request(url, method=method)
    req.add_header("Accept", "text/event-stream")
    try:
        return urlopen(req, timeout=timeout_sec)  # nosec - URL comes from env
    except HTTPError as e:
        text = (e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else "")
        raise OpenHeiTeacherError(f"OpenHei API error: {e.code} {text[:500]}") from e
    except URLError as e:
        raise OpenHeiTeacherError(f"OpenHei API request failed: {e.reason}") from e
    except TimeoutError as e:
        raise OpenHeiTeacherError(f"OpenHei API request timed out: {url}") from e


def _iter_sse_data_messages(lines: Iterable[bytes]) -> Iterable[str]:
    """Yield SSE `data:` payloads (joined by \n) per event."""

    data_lines: List[str] = []
    for raw in lines:
        try:
            line = raw.decode("utf-8", errors="replace")
        except Exception:
            line = str(raw)
        line = line.rstrip("\r\n")

        # Blank line delimits an event.
        if line == "":
            if data_lines:
                yield "\n".join(data_lines)
                data_lines = []
            continue

        if line.startswith(":"):
            # Comment / keepalive.
            continue
        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
            continue

        # Ignore other SSE fields: event:, id:, retry:

    if data_lines:
        yield "\n".join(data_lines)


def _iter_sse_json_events(lines: Iterable[bytes]) -> Iterable[Dict[str, Any]]:
    for payload in _iter_sse_data_messages(lines):
        payload = payload.strip()
        if not payload:
            continue
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            yield event


def _format_openhei_error(err: Any) -> str:
    if isinstance(err, dict):
        # Common patterns include {type, message} or {code, message}.
        msg = err.get("message") or err.get("error") or ""
        if isinstance(msg, str) and msg.strip():
            return redact_secrets(msg.strip())
    return redact_secrets(json.dumps(err, ensure_ascii=False)[:2000])


class _AssistantTextCollector:
    def __init__(self, *, session_id: str, message_id: Optional[str] = None) -> None:
        self.session_id = session_id
        self.message_id = message_id
        self._part_order: List[str] = []
        self._text_by_part: Dict[str, str] = {}
        self._completed = False
        self._last_relevant_t = time.monotonic()
        self._error: Optional[str] = None

    @property
    def completed(self) -> bool:
        return self._completed

    @property
    def last_relevant_t(self) -> float:
        return self._last_relevant_t

    @property
    def error(self) -> Optional[str]:
        return self._error

    def _set_message_id_if_needed(self, message_id: Optional[str]) -> None:
        if self.message_id or not message_id:
            return
        self.message_id = message_id

    def feed(self, event: Dict[str, Any]) -> None:
        et = event.get("type")
        # OpenHei event shapes vary between transports/versions. Newer SSE events
        # carry a `properties` object. Older/alternate shapes may put fields at
        # the top-level. Accept both by normalizing `props` to a dict view of
        # event properties.
        props = event.get("properties")
        if not isinstance(props, dict):
            # Fallback to using the event dict itself (excluding `type`). This
            # keeps compatibility with non-wrapped events that include sessionID,
            # messageID, part, info, etc. as top-level keys.
            props = {k: v for k, v in event.items() if k != "type"}

        if et in {"session.status", "session.idle"}:
            sess = props.get("sessionID")
            if sess == self.session_id:
                # Keep-alive progress; useful when providers are rate-limiting.
                self._last_relevant_t = time.monotonic()
                status = props.get("status")
                if et == "session.status" and isinstance(status, dict) and status.get("type") == "retry":
                    msg = status.get("message")
                    if isinstance(msg, str) and _is_retryable_error(msg):
                        self._error = redact_secrets(msg.strip())
            return

        if et == "session.error":
            sess = props.get("sessionID")
            if sess == self.session_id:
                self._error = _format_openhei_error(props.get("error"))
            return

        if et == "message.updated":
            # `info` may be nested or at top-level depending on server version.
            info = props.get("info") if isinstance(props.get("info"), dict) else event.get("info") or props
            if not isinstance(info, dict):
                return
            if info.get("sessionID") != self.session_id:
                return
            if info.get("role") != "assistant":
                return
            mid = info.get("id")
            if isinstance(mid, str) and mid:
                self._set_message_id_if_needed(mid)
            if self.message_id and mid != self.message_id:
                return

            self._last_relevant_t = time.monotonic()
            time_obj = info.get("time")
            if isinstance(time_obj, dict) and time_obj.get("completed") is not None:
                self._completed = True
            return

        if et == "message.part.delta":
            # support both nested `properties` and flat event shapes
            sess = props.get("sessionID")
            if sess != self.session_id:
                return
            mid = props.get("messageID")
            if isinstance(mid, str) and mid:
                self._set_message_id_if_needed(mid)
            if self.message_id and mid != self.message_id:
                return
            if props.get("field") != "text":
                return

            part_id = props.get("partID")
            delta = props.get("delta")
            if not isinstance(part_id, str) or not part_id:
                return
            if not isinstance(delta, str) or not delta:
                return
            if part_id not in self._text_by_part:
                self._part_order.append(part_id)
                self._text_by_part[part_id] = ""
            self._text_by_part[part_id] += delta
            self._last_relevant_t = time.monotonic()
            return

        if et == "message.part.updated":
            # `part` may be nested or provided at top-level.
            part = props.get("part") if isinstance(props.get("part"), dict) else event.get("part") or props
            if not isinstance(part, dict):
                return
            if part.get("sessionID") != self.session_id:
                return
            mid = part.get("messageID")
            if isinstance(mid, str) and mid:
                self._set_message_id_if_needed(mid)
            if self.message_id and mid != self.message_id:
                return

            ptype = part.get("type")
            part_id = part.get("id")
            if not isinstance(part_id, str) or not part_id:
                return

            if ptype == "text":
                text = part.get("text")
                if isinstance(text, str):
                    if part_id not in self._text_by_part:
                        self._part_order.append(part_id)
                    self._text_by_part[part_id] = text
                    self._last_relevant_t = time.monotonic()
                time_obj = part.get("time")
                if isinstance(time_obj, dict) and time_obj.get("end") is not None:
                    self._completed = True
                return

            if ptype == "step-finish":
                self._last_relevant_t = time.monotonic()
                self._completed = True
                return

    def text(self) -> str:
        if not self._part_order:
            return ""
        return "".join(self._text_by_part.get(pid, "") for pid in self._part_order).strip()


def _api_run_once(
    *,
    attach_url: str,
    repo_dir: str,
    prompt: str,
    model_id: str,
    agent: str,
    timeout_sec: float,
) -> str:
    if "/" not in model_id:
        raise OpenHeiTeacherError(f"Invalid model id (expected provider/model): {model_id!r}")
    provider_id, model_name = model_id.split("/", 1)

    session = _http_json(
        "POST",
        _api_url(attach_url, f"/session?directory={quote(repo_dir)}"),
        {"title": "heidi-engine teacher"},
        timeout_sec=min(10.0, timeout_sec),
    )
    session_id = session.get("id")
    if not isinstance(session_id, str) or not session_id:
        raise OpenHeiTeacherError("OpenHei API did not return a session id")

    msg_id = f"msg_heidi_{int(time.time()*1000)}_{os.getpid()}"

    # Subscribe to the directory event stream and reconstruct assistant output.
    # This avoids relying on the non-streaming message list (which can lag or omit parts).
    stream_url = _api_url(attach_url, f"/event?directory={quote(repo_dir)}")
    collector = _AssistantTextCollector(session_id=session_id)

    # Use a short socket timeout so we can enforce inactivity/overall timeouts.
    overall_deadline = time.monotonic() + float(timeout_sec)
    inactivity_timeout = min(30.0, max(5.0, float(timeout_sec) / 10.0))

    message_sent = False
    read_timeout = min(60.0, max(5.0, float(timeout_sec) / 5.0))

    while True:
        now = time.monotonic()
        if now >= overall_deadline:
            raise OpenHeiTeacherError("OpenHei SSE timed out waiting for assistant output")
        if collector.error:
            raise OpenHeiTeacherError(f"OpenHei SSE error: {collector.error}")
        if collector.message_id and (now - collector.last_relevant_t) > inactivity_timeout:
            raise OpenHeiTeacherError("OpenHei SSE inactive while waiting for completion")

        with _http_stream("GET", stream_url, timeout_sec=read_timeout) as resp:
            if not message_sent:
                # Send message after stream is connected to avoid missing early deltas.
                # Include directory query parameter for API parity with OpenHei clients.
                _http_json(
                    "POST",
                    _api_url(attach_url, f"/session/{quote(session_id)}/message?directory={quote(repo_dir)}"),
                    {
                        "messageID": msg_id,
                        "model": {"providerID": provider_id, "modelID": model_name},
                        "agent": agent or "",
                        "parts": [{"type": "text", "text": prompt}],
                    },
                    timeout_sec=timeout_sec,
                )
                message_sent = True

            try:
                for event in _iter_sse_json_events(resp):
                    collector.feed(event)
                    if collector.error:
                        raise OpenHeiTeacherError(f"OpenHei SSE error: {collector.error}")
                    if collector.completed:
                        text = collector.text()
                        if not text:
                            raise OpenHeiTeacherError("OpenHei SSE contained no completed assistant text")
                        return text
                    if time.monotonic() >= overall_deadline:
                        raise OpenHeiTeacherError("OpenHei SSE timed out waiting for assistant output")
            except (socket.timeout, OSError) as e:
                # urllib/httpclient can raise OSError("cannot read from timed out object") after a timeout.
                msg = str(e).lower()
                if "timed out" in msg or "timeout" in msg:
                    continue
                raise


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

        # Prefer HTTP attach API when available (no need for openhei CLI).
        use_http = attach_url and _bool_env("OPENHEI_ATTACH_HTTP", "1")
        if use_http and attach_url:
            last_err: Optional[str] = None
            for attempt in range(self.retries + 1):
                try:
                    return _api_run_once(
                        attach_url=attach_url,
                        repo_dir=repo_dir,
                        prompt=prompt,
                        model_id=model_id,
                        agent=agent,
                        timeout_sec=float(self.timeout_sec),
                    )
                except OpenHeiTeacherError as e:
                    last_err = str(e)
                    if strict_attach:
                        raise
                    # Stale attach contexts should be retried once, then fall back to non-attach mode.
                    if _contains_session_not_found(last_err):
                        if attempt == 0:
                            continue
                        break
                    if attempt < self.retries and _is_retryable_error(last_err):
                        _sleep_backoff(self.retry_backoff_sec, attempt)
                        continue
                    raise

            # Non-strict attach fallback: try non-attach mode (CLI) after a stale session.
            # This matches the attach semantics even if the environment lacks the CLI.
            use_http = False

        # OpenHei Path-B: prompt is provided via stdin (no --prompt flag).
        stdin_text = prompt if prompt.endswith("\n") else (prompt + "\n")

        env = os.environ.copy()
        env.setdefault("NO_COLOR", "1")
        env.setdefault("OPENHEI_NO_TUI", "1")

        cli_raw = (os.environ.get("OPENHEI_CLI") or "openhei").strip() or "openhei"
        try:
            cli_parts = shlex.split(cli_raw)
        except ValueError:
            cli_parts = ["openhei"]
        if not cli_parts:
            cli_parts = ["openhei"]

        def build_cmd(maybe_attach: Optional[str]) -> list[str]:
            cmd = [
                *cli_parts,
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
                        _sleep_backoff(self.retry_backoff_sec, attempt)
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
                        if _is_retryable_error(last_err):
                            _sleep_backoff(self.retry_backoff_sec, attempt)
                        else:
                            _sleep_backoff(self.retry_backoff_sec / 2.0, attempt)
                        continue
                    raise OpenHeiTeacherError(last_err)

                try:
                    return parse_openhei_jsonl_events(stdout)
                except OpenHeiTeacherError as e:
                    last_err = str(e)
                    if _contains_session_not_found(last_err):
                        raise
                    if attempt < retries:
                        if _is_retryable_error(last_err):
                            _sleep_backoff(self.retry_backoff_sec, attempt)
                        else:
                            _sleep_backoff(self.retry_backoff_sec / 2.0, attempt)
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
