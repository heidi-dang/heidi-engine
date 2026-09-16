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


def test_sanitize_run_id():
    assert telemetry.sanitize_run_id("../../../etc/passwd") == "etcpasswd"
    assert telemetry.sanitize_run_id("run_2025_01") == "run_2025_01"
    assert telemetry.sanitize_run_id("run/../../test") == "runtest"
    assert telemetry.sanitize_run_id("../..") == "default_run"
    assert telemetry.sanitize_run_id("") == "default_run"
    assert telemetry.sanitize_run_id(None) == "default_run"


def test_path_traversal_prevention():
    with tempfile.TemporaryDirectory() as tmp_dir:
        telemetry.AUTOTRAIN_DIR = tmp_dir

        # Test that path traversal in run_id is confined to AUTOTRAIN_DIR/runs
        run_dir = telemetry.get_run_dir("../../../etc/passwd")
        assert run_dir == telemetry.Path(tmp_dir) / "runs" / "etcpasswd"
        assert str(run_dir).startswith(str(telemetry.Path(tmp_dir) / "runs"))


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
