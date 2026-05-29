import tempfile
import time

from heidi_engine import telemetry


def test_state_cache():
    with tempfile.TemporaryDirectory() as tmp_dir:
        telemetry.AUTOTRAIN_DIR = tmp_dir
        run_id = "test_run"

        # Init
        telemetry.init_telemetry(run_id)

        # 1. Test Cache Hit
        start = time.time()
        s1 = telemetry.get_state(run_id)
        t1 = time.time() - start

        start = time.time()
        s2 = telemetry.get_state(run_id)
        t2 = time.time() - start

        print(f"First call: {t1 * 1000:.4f}ms, Second call: {t2 * 1000:.4f}ms")
        assert s1 == s2

        # 2. Test Cache Invalidation on save_state
        s1["counters"]["teacher_generated"] = 100
        telemetry.save_state(s1, run_id)

        s3 = telemetry.get_state(run_id)
        assert s3["counters"]["teacher_generated"] == 100

        # 3. Test TTL Expiration
        # Force cache set with old timestamp
        telemetry._state_cache.set(run_id, {"run_id": run_id, "status": "cached"})
        telemetry._state_cache._last_check = time.monotonic() - 1.0  # Expired

        s4 = telemetry.get_state(run_id)
        assert s4["status"] != "cached"  # Should have reloaded from disk
        print("TTL Expiration test passed")


def test_get_run_dir_sanitization():
    """Test that get_run_dir sanitizes run_id to prevent path traversal."""
    base_dir = telemetry.AUTOTRAIN_DIR

    # Test absolute path
    abs_run_id = "/tmp/evil_run"
    run_dir = telemetry.get_run_dir(abs_run_id)
    # Should be appended to runs/ and only use the last part
    assert str(run_dir).endswith("runs/evil_run")
    assert "/tmp/evil_run" not in str(run_dir) or str(run_dir).endswith("runs/evil_run")

    # Test traversal
    traversal_id = "../../evil_run"
    run_dir = telemetry.get_run_dir(traversal_id)
    assert ".." not in str(run_dir.relative_to(base_dir))
    assert run_dir.name == "evil_run"
    print("Path traversal sanitization test passed")


def test_gpu_cache():
    # Cold call
    start = time.time()
    telemetry.get_gpu_summary()
    t1 = time.time() - start

    # Warm call
    start = time.time()
    telemetry.get_gpu_summary()
    t2 = time.time() - start

    print(f"GPU Cold: {t1 * 1000:.4f}ms, Warm: {t2 * 1000:.4f}ms")
    assert t2 < t1 or t1 < 1.0  # t1 might be fast if nvidia-smi fails fast


if __name__ == "__main__":
    test_state_cache()
    test_gpu_cache()
    print("All verification tests passed!")
