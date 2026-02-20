import pytest
import time

pytestmark = pytest.mark.requires_heidi_cpp

@pytest.fixture(scope="session")
def heidi_cpp_mod():
    import heidi_cpp
    return heidi_cpp

def test_async_collector_parallelism(heidi_cpp_mod):
    # Provide a mock provider with 100ms delay per sample
    provider = heidi_cpp_mod.MockProvider(100)
    collector = heidi_cpp_mod.AsyncCollector(provider)
    
    start_time = time.time()
    results = collector.generate_n("Write me a Python script", 10)
    end_time = time.time()
    
    duration = end_time - start_time
    
    assert len(results) == 10
    assert "Mock generation completed." in results[0]
    
    # Assert they ran concurrently. If sequential, it would be 10 * 100ms = 1s.
    # Time should be ~0.1s + overhead. We enforce < 0.5s securely ensuring parallelism
    assert duration < 0.5
