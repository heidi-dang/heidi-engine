import re
import sys
import importlib.util
from pathlib import Path


def test_teacher_generate_non_tty_progress_line(tmp_path, capsys, monkeypatch):
    # Run legacy backend to avoid OpenHei dependency.
    monkeypatch.setenv("TEACHER_BACKEND", "legacy")
    monkeypatch.delenv("VERBOSE", raising=False)

    out = tmp_path / "out.jsonl"

    script_path = Path(__file__).resolve().parents[1] / "scripts" / "01_teacher_generate.py"
    spec = importlib.util.spec_from_file_location("teacher_generate", script_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    argv = [
        "01_teacher_generate.py",
        "--samples",
        "10",
        "--output",
        str(out),
        "--backend",
        "legacy",
        "--teacher",
        "gpt-4o-mini",
        "--round",
        "1",
        "--language",
        "python",
        "--repo-dir",
        str(tmp_path),
        "--seed",
        "42",
    ]

    monkeypatch.setattr(sys, "argv", argv)
    rc = mod.main()
    assert rc == 0

    err = capsys.readouterr().err
    assert re.search(r"\[INFO\] Generated 10/10 \(100%\) \| .* ETA \d+s", err)
    assert out.exists()
