import importlib.util
import pytest

def _has_heidi_cpp() -> bool:
    return importlib.util.find_spec("heidi_cpp") is not None

def pytest_configure(config):
    config.addinivalue_line("markers", "requires_heidi_cpp: requires the heidi_cpp extension module")

def pytest_collection_modifyitems(config, items):
    if _has_heidi_cpp():
        return
    skip = pytest.mark.skip(reason="heidi_cpp extension not installed in this environment")
    for item in items:
        if "requires_heidi_cpp" in item.keywords:
            item.add_marker(skip)
