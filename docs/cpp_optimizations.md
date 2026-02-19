# C++ Performance Optimizations

The Heidi Engine utilizes a high-performance C++ extension module (`heidi_cpp`) to accelerate data preparation, validation, and resource management.

## Core Modules

1.  **Deduplication**: O(1) string deduplication using `std::unordered_set`.
2.  **In-place Sort**: Fast, memory-efficient sorting for NumPy arrays.
3.  **Arena Allocator**: Pooled memory management to reduce allocation overhead.
4.  **Parallel Validation**: Multi-threaded snippet verification.
5.  **Compression**: Vectorized `zlib` compression for logs and data.
6.  **GPU Monitor**: Real-time CUDA VRAM tracking.
7.  **In-place Transpose**: Cache-aware matrix rotation.
8.  **Cache-Aware Hasher**: Performance-tuned string hashing.
9.  **Batch Compressor**: Efficient processing of log sequences.
10. **Resource Limiter**: POSIX rlimit-based process capping.

## 🏮 heidi-kernel Integration

For advanced resource management and deterministic scheduling, we integrate with [heidi-kernel](https://github.com/heidi-dang/heidi-kernel) as a Git submodule.

### Features
- **Resource Bounding**: Uses the kernel's `ResourceGovernor` for queue-based backpressure.
- **Observability**: Ready for integration with kernel-managed Unix sockets and dashboards.
- **Deterministic Scheduling**: Reducing variability in multi-threaded training loops.

### Usage in Python
```python
import heidi_cpp

def my_training_logic():
    # ...
    pass

# Run under kernel-managed bounds
heidi_cpp.run_with_kernel_bounds(
    my_training_logic, 
    max_jobs=5, 
    cpu_limit=80.0, 
    mem_limit=90.0
)
```

### Build Requirements
- **Submodules**: Ensure submodules are initialized: `git submodule update --init --recursive`.
- **Compiler**: Requires `g++` and `zlib` headers.
- **Installation**: Run `python3 setup_cpp.py build_ext --inplace`.
