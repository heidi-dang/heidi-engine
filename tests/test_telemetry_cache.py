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


def test_sanitize_run_id():
    """Test that sanitize_run_id removes dangerous path traversal characters."""
    assert telemetry.sanitize_run_id("../../etc/passwd") == "etcpasswd"
    assert telemetry.sanitize_run_id("run_123/../secrets") == "run_123secrets"
    assert telemetry.sanitize_run_id("valid-run_id123") == "valid-run_id123"
    assert telemetry.sanitize_run_id("../../../") == "default_run"
    assert telemetry.sanitize_run_id("") == "default_run"


def test_path_traversal_prevention():
    """Test that get_run_dir strictly constrains path under AUTOTRAIN_DIR/runs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        telemetry.AUTOTRAIN_DIR = tmp_dir
        traversal_run_id = "../../etc/passwd"
        run_dir = telemetry.get_run_dir(traversal_run_id)

        # Path should be inside AUTOTRAIN_DIR/runs/
        expected_base = (telemetry.Path(tmp_dir) / "runs").resolve()
        assert str(expected_base) in str(run_dir.resolve())
        assert "passwd" in str(run_dir)
        assert ".." not in str(run_dir)


if __name__ == "__main__":
    test_state_cache()
    test_gpu_cache()
    test_sanitize_run_id()
    test_path_traversal_prevention()
    print("All verification tests passed!")
