#include "run_id.h"
#include <chrono>
#include <iomanip>
#include <sstream>

namespace heidi {
namespace core {

std::string RunId::generate() {
    auto now = std::chrono::system_clock::now();
    auto timer = std::chrono::system_clock::to_time_t(now);
    std::tm bt = *std::localtime(&timer); // loop.sh used local time logic

    std::ostringstream oss;
    oss << "run_";
    oss << std::put_time(&bt, "%Y%m%d_%H%M%S");
    return oss.str();
}

} // namespace core
} // namespace heidi
