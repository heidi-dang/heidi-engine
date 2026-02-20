#pragma once

#include <cstddef>

namespace heidi {
namespace core {

class RLimit {
public:
    // Apply default or custom resource limits
    static void apply_limits(size_t max_memory_mb = 0, size_t max_fds = 0, size_t max_cpu_sec = 0);
};

} // namespace core
} // namespace heidi
