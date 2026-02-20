import pytest

pytest.importorskip("heidi_cpp")
import time
import json
import os
import shutil


def test_cxx_engine_stress_polling_latency():
    """
    Stress-test the C++ orchestration layer by forcing it through 100 epochs
    of state transitions in mocked subprocess mode. We measure the purely
    synchronous C++ Core overhead for dispatching bounds to ensure it
    never exceeds ~1 millisecond.
    """
    # Create an isolated test directory
    test_dir = "build/test_perf_run"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)

    # Set mock environment
    os.environ["HEIDI_MOCK_SUBPROCESSES"] = "1"
    os.environ["RUN_ID"] = "perf_001"
    os.environ["OUT_DIR"] = test_dir
    os.environ["ROUNDS"] = "100"
    os.environ["MAX_CPU_PCT"] = "80"
    os.environ["MAX_MEM_PCT"] = "90"
    os.environ["MAX_WALL_TIME_MINUTES"] = "60"
    os.environ["HEIDI_SIGNING_KEY"] = "test-key"
    os.environ["HEIDI_KEYSTORE_PATH"] = "test.enc"

    engine = heidi_cpp.Core()
    engine.init("mock_config.yaml")

    # Start training exactly like Daemon does
    engine.start("full")

    start_time = time.time()
    ticks_executed = 0

    # Pump the core manually
    while True:
        status_json = engine.tick(1)
        state_dict = json.loads(status_json)
        ticks_executed += 1

        if state_dict["state"] == "IDLE" or state_dict["state"] == "ERROR":
            # The pipeline naturally transitioned to IDLE because rounds expired
            break

    end_time = time.time()

    # Calculate execution time natively for the full 100 epochs + 4 scripts per epoch
    # Meaning at least 400 total state transitions and subprocess dispatches.
    total_time_ms = (end_time - start_time) * 1000
    average_tick_ms = total_time_ms / ticks_executed

    # Verify Journal contains our telemetry
    journal_path = os.path.join(test_dir, "events.jsonl")
    assert os.path.exists(journal_path), "Journal was not written!"

    telemetry_verified = False
    with open(journal_path, "r") as f:
        for line in f:
            evt = json.loads(line)
            if evt["event_type"] == "script_success" and "usage_delta" in evt:
                usage = evt["usage_delta"]
                assert "system_mem_available_kb_delta" in usage, (
                    "Telemetry missing memory footprint"
                )
                assert "system_cpu_pct" in usage, "Telemetry missing CPU footprint"
                telemetry_verified = True
                break

    assert telemetry_verified, "No script_success events recorded telemetry payload."
    print(f"\n[PERF] 100 Epochs (400 stages) executed across {ticks_executed} C++ Core ticks.")
    print(f"[PERF] Total time elapsed: {total_time_ms:.2f}ms")
    print(f"[PERF] Average Tick overhead: {average_tick_ms:.3f}ms (Target: <1.0ms)")

    # Performance assertions
    assert average_tick_ms < 1.0, (
        f"Performance regression! The C++ pipeline overhead ({average_tick_ms:.3f}ms) exceeded 1ms threshold."
    )

    # Verify the test reached round 100
    end_state = json.loads(engine.get_status_json())
    assert end_state["round"] == 100, f"Pipeline ended prematurely at round {end_state['round']}"

    # Cleanup
    shutil.rmtree(test_dir)
