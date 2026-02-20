#include "clock.h"
#include <chrono>
#include <iomanip>
#include <sstream>

namespace heidi {
namespace core {

std::string Clock::now_iso8601() const {
    auto now = std::chrono::system_clock::now();
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()) % 1000;
    auto timer = std::chrono::system_clock::to_time_t(now);
    std::tm bt = *std::gmtime(&timer);

    std::ostringstream oss;
    oss << std::put_time(&bt, "%Y-%m-%dT%H:%M:%S");
    oss << '.' << std::setfill('0') << std::setw(3) << ms.count() << 'Z';

    return oss.str();
}

uint64_t Clock::now_epoch_sec() const {
    auto now = std::chrono::system_clock::now();
    return std::chrono::duration_cast<std::chrono::seconds>(now.time_since_epoch()).count();
}

std::string MockClock::now_iso8601() const {
    return iso_;
}

uint64_t MockClock::now_epoch_sec() const {
    return epoch_;
}

void MockClock::set_time(std::string iso, uint64_t epoch) {
    iso_ = iso;
    epoch_ = epoch;
}

} // namespace core
} // namespace heidi
