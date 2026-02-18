#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include <unordered_set>
#include <vector>
#include <string>
#include <algorithm>
#include <memory>
#include <stdexcept>

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
        // Return a memoryview to the allocated chunk
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

PYBIND11_MODULE(heidi_cpp, m) {
    m.doc() = "Heidi Engine C++ performance optimizations";

    m.def("deduplicate_strings", &deduplicate_strings, "O(1) string deduplication using unordered_set");
    m.def("sort_batch_inplace", &sort_batch_inplace, "In-place batch sorting for NumPy float arrays");

    py::class_<ArenaAllocator>(m, "ArenaAllocator")
        .def(py::init<size_t>())
        .def("allocate", &ArenaAllocator::allocate)
        .def("remaining", &ArenaAllocator::remaining)
        .def("reset", &ArenaAllocator::reset);
}
