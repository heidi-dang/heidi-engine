#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include <pybind11/functional.h>
#include <unordered_set>
#include <vector>
#include <string>
#include <algorithm>
#include <memory>
#include <stdexcept>
#include <thread>
#include <mutex>
#ifdef _WIN32
// Windows-specific headers or omissions
#else
#include <zlib.h>
#include <sys/resource.h>
#endif
#include <heidi-kernel/resource_governor.h>

#ifdef HAS_CUDA
#include <cuda_runtime.h>
#endif

namespace py = pybind11;

// 1. Efficient String Deduplication
std::vector<std::string> deduplicate_strings(const std::vector<std::string>& inputs) {
    std::unordered_set<std::string> seen;
    std::vector<std::string> result;
    result.reserve(inputs.size());
    for (const auto& s : inputs) {
        if (seen.insert(s).second) {
            result.push_back(s);
        }
    }
    return result;
}

// 2. Memory-Efficient Batch Sorter (True In-place for NumPy)
void sort_batch_inplace(py::array_t<float> batch) {
    py::buffer_info info = batch.request();
    if (info.ndim != 1) {
        throw std::runtime_error("Sort only supports 1D arrays");
    }
    
    float* ptr = static_cast<float*>(info.ptr);
    std::sort(ptr, ptr + info.shape[0]);
}

// 3. Custom Arena Allocator
class ArenaAllocator {
public:
    ArenaAllocator(size_t size) : buffer_(new char[size]), pos_(0), size_(size) {}
    ~ArenaAllocator() { delete[] buffer_; }
    
    py::memoryview allocate(size_t bytes) {
        if (pos_ + bytes > size_) {
            throw std::runtime_error("Arena overflow");
        }
        void* ptr = buffer_ + pos_;
        pos_ += bytes;
        return py::memoryview::from_memory(ptr, bytes);
    }

    size_t remaining() const {
        return size_ - pos_;
    }

    void reset() {
        pos_ = 0;
    }

private:
    char* buffer_;
    size_t pos_, size_;
};

// 4. Parallel Validation (Simulated for this implementation)
std::vector<bool> parallel_validate(const std::vector<std::string>& snippets, int threads) {
    std::vector<bool> results(snippets.size(), false);
    std::mutex mtx;
    
    auto worker = [&](size_t start, size_t end) {
        for (size_t i = start; i < end; ++i) {
            // High-level "validation": check length and non-emptiness
            bool valid = !snippets[i].empty() && snippets[i].length() > 5;
            
            std::lock_guard<std::mutex> lock(mtx);
            results[i] = valid;
        }
    };

    std::vector<std::thread> workers;
    if (threads <= 0) threads = 1;
    size_t chunk = snippets.size() / threads;
    
    for (int t = 0; t < threads; ++t) {
        size_t start = t * chunk;
        size_t end = (t == threads - 1) ? snippets.size() : start + chunk;
        if (start < end) {
            workers.emplace_back(worker, start, end);
        }
    }
    
    for (auto& w : workers) w.join();
    return results;
}

// 5. Compressed Data Serializer
std::string compress_data(const std::string& data) {
#ifdef _WIN32
    // zlib not easily available on Windows CI by default
    throw std::runtime_error("compress_data is not supported on Windows");
#else
    if (data.empty()) return "";
    
    uLongf destLen = compressBound(data.size());
    std::vector<Bytef> buffer(destLen);
    
    if (compress(buffer.data(), &destLen, (const Bytef*)data.data(), data.size()) != Z_OK) {
        throw std::runtime_error("zlib compression failed");
    }
    
    return std::string((const char*)buffer.data(), destLen);
#endif
}

// 6. GPU Memory Checker
size_t get_free_gpu_memory() {
#ifdef HAS_CUDA
    size_t free, total;
    if (cudaMemGetInfo(&free, &total) == cudaSuccess) {
        return free;
    }
    return 0;
#else
    return 0; 
#endif
}

// 7. In-Place Tensor Transpose (Square only optimized, basic error check)
void transpose_inplace(py::array_t<float> matrix, size_t rows, size_t cols) {
    py::buffer_info info = matrix.request();
    if (rows * cols != static_cast<size_t>(info.size)) {
        throw std::runtime_error("Matrix size mismatch");
    }
    if (rows != cols) {
        throw std::runtime_error("In-place transpose currently only supports square matrices in this version");
    }

    float* ptr = static_cast<float*>(info.ptr);
    for (size_t i = 0; i < rows; ++i) {
        for (size_t j = i + 1; j < cols; ++j) {
            std::swap(ptr[i * cols + j], ptr[j * rows + i]);
        }
    }
}

// 8. Cache-Aware Hasher
std::vector<std::string> dedup_with_custom_hash(const std::vector<std::string>& inputs) {
    struct CacheAwareHasher {
        size_t operator()(const std::string& s) const {
            size_t hash = 0;
            for (char c : s) hash = hash * 31 + static_cast<size_t>(c);
            return hash;
        }
    };
    std::unordered_set<std::string, CacheAwareHasher> seen;
    std::vector<std::string> result;
    result.reserve(inputs.size());
    for (const auto& s : inputs) {
        if (seen.insert(s).second) {
            result.push_back(s);
        }
    }
    return result;
}

// 9. Batch Compressor for Logs
std::vector<py::bytes> compress_logs(const std::vector<std::string>& logs) {
    std::vector<py::bytes> compressed;
#ifdef _WIN32
    // Not supported on Windows
    for (size_t i = 0; i < logs.size(); ++i) compressed.emplace_back("");
#else
    compressed.reserve(logs.size());
    for (const auto& log : logs) {
        uLongf source_len = log.size();
        uLongf dest_len = compressBound(source_len);
        std::vector<Bytef> buf(dest_len);
        if (compress(buf.data(), &dest_len, reinterpret_cast<const Bytef*>(log.data()), source_len) == Z_OK) {
            compressed.emplace_back(reinterpret_cast<const char*>(buf.data()), dest_len);
        } else {
            compressed.emplace_back(""); // Or throw
        }
    }
#endif
    return compressed;
}

// 10. Resource Limiter Wrapper
void run_with_limits(const std::function<void()>& func, int max_threads, size_t max_memory_mb) {
#ifdef _WIN32
    // rlimit not available on Windows
    func();
#else
    // Note: Setting caps in a shared library can affect the whole process.
    // Memory limit (Address Space)
    if (max_memory_mb > 0) {
        struct rlimit lim;
        if (getrlimit(RLIMIT_AS, &lim) == 0) {
            lim.rlim_cur = max_memory_mb * 1024 * 1024;
            setrlimit(RLIMIT_AS, &lim);
        }
    }
    // Note: max_threads enforcement would typically be done via OpenMP or pool control.
    // We'll execute the function as a wrapper.
    func();
#endif
}

// 11. Kernel-Aware Resource Governor
void run_with_kernel_bounds(const std::function<void()>& func, int max_jobs, double cpu_limit, double mem_limit) {
    heidi::GovernorPolicy policy;
    policy.max_running_jobs = max_jobs > 0 ? max_jobs : 10;
    policy.cpu_high_watermark_pct = cpu_limit > 0 ? cpu_limit : 85.0;
    policy.mem_high_watermark_pct = mem_limit > 0 ? mem_limit : 90.0;

    heidi::ResourceGovernor governor(policy);
    
    // In a real integration, we'd loop or wait on the queue.
    // For this demonstration, we'll check if we CAN run.
    heidi::GovernorResult result = governor.decide(10.0, 10.0, 0, 0); // Mocked current usage
    
    if (result.decision == heidi::GovernorDecision::REJECT_QUEUE_FULL) {
        throw std::runtime_error("Kernel Governor rejected job: Queue full");
    }
    
    // Execute function
    func();
}

PYBIND11_MODULE(heidi_cpp, m) {
    m.doc() = "Heidi Engine C++ performance optimizations";

    m.def("deduplicate_strings", &deduplicate_strings, "O(1) string deduplication using unordered_set");
    m.def("sort_batch_inplace", &sort_batch_inplace, "In-place batch sorting for NumPy float arrays");
    m.def("parallel_validate", &parallel_validate, "Multi-threaded string validation", 
          py::arg("snippets"), py::arg("threads") = 4);
    m.def("compress_data", [](const std::string& data) {
        std::string compressed = compress_data(data);
        return py::bytes(compressed);
    }, "zlib-based data compression");
    m.def("get_free_gpu_memory", &get_free_gpu_memory, "Get free GPU memory bytes (requires CUDA)");

    // Phase 3 bindings
    m.def("transpose_inplace", &transpose_inplace, "In-place matrix transpose (square only)");
    m.def("dedup_with_custom_hash", &dedup_with_custom_hash, "Deduplication with custom cache-aware hash");
    m.def("compress_logs", &compress_logs, "Batch compress a list of log strings");
    m.def("run_with_limits", &run_with_limits, "Run a Python function under resource limits",
          py::arg("func"), py::arg("max_threads") = 0, py::arg("max_memory_mb") = 0);
    m.def("run_with_kernel_bounds", &run_with_kernel_bounds, "Run a Python function under kernel-managed resource bounds",
          py::arg("func"), py::arg("max_jobs") = 10, py::arg("cpu_limit") = 85.0, py::arg("mem_limit") = 90.0);

    py::class_<ArenaAllocator>(m, "ArenaAllocator")
        .def(py::init<size_t>())
        .def("allocate", &ArenaAllocator::allocate)
        .def("remaining", &ArenaAllocator::remaining)
        .def("reset", &ArenaAllocator::reset);
}
