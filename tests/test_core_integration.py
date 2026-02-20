import platform
import time

import pytest

# These tests require the C++ extension module.
# Keep collection safe on non-Linux runners and on Linux where the extension isn't built.
if platform.system() != "Linux":
    pytest.skip("C++ integration tests only run on Linux", allow_module_level=True)

heidi_cpp = pytest.importorskip("heidi_cpp", reason="C++ extension not built/available")


def test_async_collector_parallelism() -> None:
    """
    Verifies AsyncCollector runs requests concurrently.
    If sequential: 10 * 100ms = 1.0s. We enforce < 0.5s to confirm parallelism.
    """
    provider = heidi_cpp.MockProvider(100)  # 100ms per sample
    collector = heidi_cpp.AsyncCollector(provider)

    start_time = time.time()
    results = collector.generate_n("Write me a Python script", 10)
    duration = time.time() - start_time

    assert len(results) == 10
    assert "Mock generation completed." in results[0]
    assert duration < 0.5
