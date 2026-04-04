import sys
import os
try:
    from heidi_engine.telemetry import get_state, load_pricing_config, init_telemetry
    print("Imports successful")

    # Test get_state
    run_id = "test_run_final"
    init_telemetry(run_id)
    state = get_state(run_id)
    print(f"get_state successful: {state['run_id']}")

    # Test pricing cache
    config = load_pricing_config()
    print(f"load_pricing_config successful: {len(config)} models")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
