import os
import sys
from heidi_engine import telemetry

try:
    telemetry.init_telemetry("test_run")
    state = telemetry.get_state("test_run")
    print("Successfully got state")
except Exception as e:
    print(f"Error: {e}")
