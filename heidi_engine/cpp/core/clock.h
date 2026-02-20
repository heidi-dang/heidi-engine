#pragma once

#include <string>
#include <cstdint>

namespace heidi {
namespace core {

class Clock {
public:
    virtual ~Clock() = default;
    
    // Returns current time in ISO8601 UTC format, e.g. "2026-02-20T18:32:00.000Z"
    virtual std::string now_iso8601() const;
    
    // Returns current time as epoch seconds
    virtual uint64_t now_epoch_sec() const;
};

// A mockable clock for deterministic tests
class MockClock : public Clock {
public:
    std::string now_iso8601() const override;
    uint64_t now_epoch_sec() const override;
    
    void set_time(std::string iso, uint64_t epoch);
private:
    std::string iso_;
    uint64_t epoch_ = 0;
};

} // namespace core
} // namespace heidi
