import time
import json
import threading
from pathlib import Path
from heidi_engine import telemetry

def test_state_cache_hits():
    run_id = "test_run_cache"
    telemetry.init_telemetry(run_id=run_id, force=True)

    # Warm up / populate cache
    telemetry.get_state(run_id)

    # Measure average hit time
    iterations = 100
    start = time.monotonic()
    for _ in range(iterations):
        telemetry.get_state(run_id)
    avg_hit_time = (time.monotonic() - start) / iterations

    # Measure miss time (invalidate first)
    telemetry._state_cache.invalidate()
    start = time.monotonic()
    telemetry.get_state(run_id)
    miss_time = time.monotonic() - start

    print(f"Average hit time: {avg_hit_time*1000:.4f}ms, Miss time: {miss_time*1000:.4f}ms")
    assert avg_hit_time < miss_time

def test_state_cache_invalidation():
    run_id = "test_run_invalid"
    telemetry.init_telemetry(run_id=run_id, force=True)

    state = telemetry.get_state(run_id)
    state["counters"]["teacher_generated"] = 10

    # save_state should update cache
    telemetry.save_state(state, run_id)

    cached_state = telemetry.get_state(run_id)
    assert cached_state["counters"]["teacher_generated"] == 10

    # Directly modify file to simulate external change (cache should still return old value until TTL)
    state_file = telemetry.get_state_path(run_id)
    state["counters"]["teacher_generated"] = 20
    with open(state_file, "w") as f:
        json.dump(state, f)

    # Should still be 10 from cache
    cached_state = telemetry.get_state(run_id)
    assert cached_state["counters"]["teacher_generated"] == 10

    # Wait for TTL (0.5s)
    time.sleep(0.6)

    # Should now be 20 from disk
    new_state = telemetry.get_state(run_id)
    assert new_state["counters"]["teacher_generated"] == 20

def test_gpu_cache():
    # Warm up
    telemetry.get_gpu_summary()

    start = time.monotonic()
    telemetry.get_gpu_summary()
    duration = time.monotonic() - start
    print(f"GPU summary cached duration: {duration*1000:.4f}ms")
    assert duration < 0.005 # Should be sub-millisecond

if __name__ == "__main__":
    test_state_cache_hits()
    test_state_cache_invalidation()
    test_gpu_cache()
    print("All cache tests passed!")
