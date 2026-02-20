import pytest

heidi_cpp = pytest.importorskip(
    "heidi_cpp",
    reason="C++ extension not built/installed in this environment",
)
