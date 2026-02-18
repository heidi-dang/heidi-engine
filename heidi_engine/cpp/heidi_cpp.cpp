#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include <unordered_set>
#include <vector>
#include <string>
#include <algorithm>
#include <memory>
#include <stdexcept>
#include <thread>
#include <mutex>
#include <zlib.h>

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
            // In real use, this could trigger sub-validators if thread-safe
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
    if (data.empty()) return "";
    
    uLongf destLen = compressBound(data.size());
    std::vector<Bytef> buffer(destLen);
    
    if (compress(buffer.data(), &destLen, (const Bytef*)data.data(), data.size()) != Z_OK) {
        throw std::runtime_error("zlib compression failed");
    }
    
    return std::string((const char*)buffer.data(), destLen);
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
    // Fallback or warning if CUDA not compiled in
    return 0; 
#endif
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

    py::class_<ArenaAllocator>(m, "ArenaAllocator")
        .def(py::init<size_t>())
        .def("allocate", &ArenaAllocator::allocate)
        .def("remaining", &ArenaAllocator::remaining)
        .def("reset", &ArenaAllocator::reset);
}
