#include "rlimit.h"
#include <sys/resource.h>
#include <stdexcept>

namespace heidi {
namespace core {

void RLimit::apply_limits(size_t max_memory_mb, size_t max_fds, size_t max_cpu_sec) {
    struct rlimit lim;
    
    if (max_memory_mb > 0) {
        if (getrlimit(RLIMIT_AS, &lim) == 0) {
            lim.rlim_cur = max_memory_mb * 1024 * 1024;
            setrlimit(RLIMIT_AS, &lim);
        }
    }
    
    if (max_fds > 0) {
        if (getrlimit(RLIMIT_NOFILE, &lim) == 0) {
            lim.rlim_cur = max_fds;
            setrlimit(RLIMIT_NOFILE, &lim);
        }
    }
    
    if (max_cpu_sec > 0) {
        if (getrlimit(RLIMIT_CPU, &lim) == 0) {
            lim.rlim_cur = max_cpu_sec;
            setrlimit(RLIMIT_CPU, &lim);
        }
    }
}

} // namespace core
} // namespace heidi
