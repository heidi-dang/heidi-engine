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
        agent=os.environ.get("OPENHEI_AGENT", "general"),
        attach_url=os.environ.get("OPENHEI_ATTACH"),
    )
    assert "instruction" in text and "output" in text
