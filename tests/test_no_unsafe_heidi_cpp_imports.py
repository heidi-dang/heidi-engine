from __future__ import annotations
import pathlib
import re

UNSAFE = re.compile(r"(^|\s)(import\s+heidi_cpp\b|from\s+heidi_cpp\s+import\b)")
SAFE = re.compile(r"importorskip\(['\"]heidi_cpp['\"]")


def test_no_unsafe_heidi_cpp_imports() -> None:
    bad: list[str] = []
    for p in pathlib.Path("tests").rglob("test_*.py"):
        s = p.read_text(encoding="utf-8")
        if UNSAFE.search(s) and not SAFE.search(s):
            bad.append(str(p))
    assert not bad, "Unsafe heidi_cpp imports (must use pytest.importorskip):\n" + "\n".join(bad)
