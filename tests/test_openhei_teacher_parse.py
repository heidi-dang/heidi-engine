import os
from pathlib import Path

import pytest

from heidi_engine.teacher.openhei_teacher import OpenHeiTeacherError, parse_openhei_jsonl_events


def test_parse_openhei_jsonl_events_joins_completed_text_parts():
    fixture = Path(__file__).parent / "fixtures" / "openhei_run_stream.jsonl"
    out = parse_openhei_jsonl_events(fixture.read_text(encoding="utf-8"))
    assert out == '{"instruction":"Do thing","input":"Some input","output":"Some output"}'


def test_parse_openhei_jsonl_events_fails_closed_on_error_event():
    stdout = (
        '{"type":"text","part":{"text":"hello","time":{"end":"t"}}}\n'
        '{"type":"error","message":"boom"}\n'
    )
    with pytest.raises(OpenHeiTeacherError):
        parse_openhei_jsonl_events(stdout)


def test_parse_openhei_jsonl_events_fails_closed_on_non_json_line():
    with pytest.raises(OpenHeiTeacherError):
        parse_openhei_jsonl_events("not json\n")


def test_openhei_teacher_sends_prompt_via_stdin(monkeypatch, tmp_path):
    from heidi_engine.teacher import openhei_teacher as mod

    seen = {}

    def fake_run(cmd, *, input, capture_output, text, timeout, env):
        seen["cmd"] = cmd
        seen["input"] = input
        seen["env"] = env

        class R:
            returncode = 0
            stdout = '{"type":"text","part":{"text":"{\\"instruction\\":\\"x\\",\\"input\\":\\"y\\",\\"output\\":\\"z\\"}","time":{"end":"t"}}}\n'
            stderr = ""

        return R()

    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    teacher = mod.OpenHeiTeacher(timeout_sec=5, retries=0)
    out = teacher.run(
        repo_dir=str(tmp_path),
        prompt="hello",
        model_id="openai/gpt-5-mini",
        agent="general",
        attach_url=None,
    )

    assert out == '{"instruction":"x","input":"y","output":"z"}'
    assert "--agent" not in seen["cmd"]
    assert "--prompt" not in seen["cmd"]
    assert seen["input"] == "hello\n"


def test_openhei_teacher_falls_back_when_attach_session_not_found(monkeypatch, tmp_path, capsys):
    from heidi_engine.teacher import openhei_teacher as mod

    # Avoid real network validation in unit tests.
    monkeypatch.setattr(mod, "validate_openhei_attach_url", lambda *_a, **_k: None)

    calls = {"n": 0, "cmds": []}

    class R:
        def __init__(self, *, returncode: int, stdout: str = "", stderr: str = ""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def fake_run(cmd, *, input, capture_output, text, timeout, env):
        calls["n"] += 1
        calls["cmds"].append(cmd)

        # First two attempts with attach fail with session-not-found.
        if "--attach" in cmd:
            return R(returncode=1, stdout="", stderr="OpenHeiTeacherError: Session not found")

        # Fallback without attach succeeds.
        return R(
            returncode=0,
            stdout='{"type":"text","part":{"text":"{\\"instruction\\":\\"x\\",\\"input\\":\\"y\\",\\"output\\":\\"z\\"}","time":{"end":"t"}}}\n',
            stderr="",
        )

    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    teacher = mod.OpenHeiTeacher(timeout_sec=5, retries=0)
    out = teacher.run(
        repo_dir=str(tmp_path),
        prompt="hello",
        model_id="openai/gpt-5-mini",
        agent="",
        attach_url="http://127.0.0.1:4100",
    )

    assert out == '{"instruction":"x","input":"y","output":"z"}'
    assert calls["n"] >= 3
    assert any("--attach" in c for c in calls["cmds"])
    assert any("--attach" not in c for c in calls["cmds"])

    err = capsys.readouterr().err
    assert "falling back to non-attach" in err.lower()


def test_openhei_teacher_strict_attach_fails_closed_on_session_not_found(monkeypatch, tmp_path):
    from heidi_engine.teacher import openhei_teacher as mod

    monkeypatch.setenv("OPENHEI_ATTACH_STRICT", "1")
    monkeypatch.setattr(mod, "validate_openhei_attach_url", lambda *_a, **_k: None)

    class R:
        returncode = 1
        stdout = ""
        stderr = "Session not found"

    def fake_run(cmd, *, input, capture_output, text, timeout, env):
        return R()

    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    teacher = mod.OpenHeiTeacher(timeout_sec=5, retries=0)
    with pytest.raises(mod.OpenHeiTeacherError):
        teacher.run(
            repo_dir=str(tmp_path),
            prompt="hello",
            model_id="openai/gpt-5-mini",
            agent="",
            attach_url="http://127.0.0.1:4100",
        )


@pytest.mark.skipif(os.environ.get("OPENHEI_INTEGRATION") != "1", reason="integration test")
def test_openhei_integration_smoke(tmp_path):
    # Requires local credentials and model availability.
    prompt = (
        "Return ONLY strict JSON with keys instruction,input,output. "
        "instruction must be 'x' and input must be 'y'. output can be 'z'.\n\n"
        "instruction: x\n\ninput: y\n"
    )

    from heidi_engine.teacher.openhei_teacher import OpenHeiTeacher

    teacher = OpenHeiTeacher(timeout_sec=180)
    text = teacher.run(
        repo_dir=str(tmp_path),
        prompt=prompt,
        model_id=os.environ.get("TEACHER_MODEL", "openai/gpt-5-mini"),
        agent=os.environ.get("OPENHEI_AGENT", ""),
        attach_url=os.environ.get("OPENHEI_ATTACH"),
    )
    assert "instruction" in text and "output" in text
