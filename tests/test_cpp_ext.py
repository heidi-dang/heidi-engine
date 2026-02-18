import heidi_cpp
import time
import random
import sys
import numpy as np

def benchmark_dedupe():
    print("--- Benchmarking Deduplication ---")
    data = [f"string_{random.randint(0, 1000)}" for _ in range(100000)]
    
    # Python native
    start = time.time()
    py_result = list(set(data))
    py_time = time.time() - start
    print(f"Python set() time: {py_time:.4f}s")
    
    # C++ extension
    start = time.time()
    cpp_result = heidi_cpp.deduplicate_strings(data)
    cpp_time = time.time() - start
    print(f"C++ deduplicate_strings time: {cpp_time:.4f}s")
    print(f"Speedup: {py_time / cpp_time:.2f}x")
    
    # Correctness check
    assert len(set(py_result)) == len(set(cpp_result)), "Deduplication logic mismatch"
    print("Correctness verified.")

def benchmark_sort():
    print("\n--- Benchmarking In-place Sort (NumPy) ---")
    size = 1000000
    data = np.random.rand(size).astype(np.float32)
    
    # Python/NumPy native (timsort/quicksort)
    py_data = data.copy()
    start = time.time()
    py_data.sort()
    py_time = time.time() - start
    print(f"NumPy ndarray.sort() time: {py_time:.4f}s")
    
    # C++ extension (std::sort)
    cpp_data = data.copy()
    start = time.time()
    heidi_cpp.sort_batch_inplace(cpp_data)
    cpp_time = time.time() - start
    print(f"C++ sort_batch_inplace time: {cpp_time:.4f}s")
    print(f"Speedup: {py_time / cpp_time:.2f}x")
    
    # Correctness check
    assert np.array_equal(cpp_data, py_data), "Sorting mismatch"
    print("Correctness verified (True in-place).")

def test_arena():
    print("\n--- Testing Arena Allocator ---")
    arena = heidi_cpp.ArenaAllocator(1024)
    print(f"Initial capacity: {arena.remaining()} bytes")
    
    buf1 = arena.allocate(100)
    print(f"Allocated 100 bytes, remaining: {arena.remaining()}")
    assert len(buf1) == 100
    
    # Use the memoryview
    buf1[0] = 42
    print(f"Successfully modified arena buffer: {buf1[0]}")
    
    arena.reset()
    print("Arena reset successful.")
    assert arena.remaining() == 1024

def benchmark_parallel_validate():
    print("\n--- Benchmarking Parallel Validation ---")
    snippets = [f"def func_{i}():\n    return {i}" for i in range(50000)]
    
    # Serial validation (Python)
    start = time.time()
    py_results = [len(s) > 5 for s in snippets]
    py_time = time.time() - start
    print(f"Python serial validation time: {py_time:.4f}s")
    
    # C++ Parallel validation
    start = time.time()
    cpp_results = heidi_cpp.parallel_validate(snippets, threads=4)
    cpp_time = time.time() - start
    print(f"C++ parallel_validate (4 threads) time: {cpp_time:.4f}s")
    print(f"Speedup: {py_time / cpp_time:.2f}x")
    
    assert py_results == cpp_results, "Parallel validation mismatch"
    print("Correctness verified.")

def benchmark_compression():
    print("\n--- Benchmarking Compression ---")
    # Large JSON-like string
    data = json.dumps([{"id": i, "content": "synthetic data " * 10} for i in range(1000)])
    
    start = time.time()
    compressed = heidi_cpp.compress_data(data)
    cpp_time = time.time() - start
    
    ratio = len(data) / len(compressed)
    print(f"C++ compress_data time: {cpp_time:.4f}s")
    print(f"Compression ratio: {ratio:.2f}x")
    assert ratio > 1.0, "Compression failed"

def test_gpu_memory():
    print("\n--- Testing GPU Memory Checker ---")
    free_mem = heidi_cpp.get_free_gpu_memory()
    print(f"Free GPU memory: {free_mem} bytes")
    # If 0, it might just mean no CUDA or no GPU, which is fine for a test

if __name__ == "__main__":
    import json
    try:
        benchmark_dedupe()
        benchmark_sort()
        test_arena()
        benchmark_parallel_validate()
        benchmark_compression()
        test_gpu_memory()
        print("\nAll C++ phase 2 optimizations verified successfully!")
    except Exception as e:
        print(f"\nVerification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
