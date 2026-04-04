import time
import os
import heidi_engine.telemetry as telemetry

def benchmark_pricing():
    n = 1000

    # Warm up cache
    telemetry.load_pricing_config()

    # Test cached
    start_time = time.time()
    for i in range(n):
        telemetry.load_pricing_config()
    end_time = time.time()
    avg_cached = (end_time - start_time) / n
    print(f"Average time per load_pricing_config (CACHED): {avg_cached*1000:.4f} ms")

    # Test uncached (force reload)
    start_time = time.time()
    for i in range(n):
        telemetry._pricing_last_check = 0 # Force reload
        telemetry.load_pricing_config()
    end_time = time.time()
    avg_uncached = (end_time - start_time) / n
    print(f"Average time per load_pricing_config (UNCACHED): {avg_uncached*1000:.4f} ms")

    improvement = (avg_uncached - avg_cached) / avg_uncached * 100
    print(f"Improvement: {improvement:.2f}%")

if __name__ == "__main__":
    benchmark_pricing()
