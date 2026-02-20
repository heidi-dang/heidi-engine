#include "mock_provider.h"
#include <chrono>
#include <thread>
#include <sstream>

namespace heidi {
namespace core {

MockProvider::MockProvider(int simulated_delay_ms) : delay_ms_(simulated_delay_ms) {
}

MockProvider::~MockProvider() = default;

std::string MockProvider::generate(const std::string& prompt) {
    if (delay_ms_ > 0) {
        std::this_thread::sleep_for(std::chrono::milliseconds(delay_ms_));
    }
    
    // Return a mocked JSON-lines compatible sample representing a generated sample
    std::ostringstream ss;
    ss << "{\"prompt\":\"" << prompt << "\", \"completion\":\"Mock generation completed.\"}";
    return ss.str();
}

std::future<std::string> MockProvider::generate_async(const std::string& prompt) {
    // We launch a dedicated async task using std::async to simulate future work
    return std::async(std::launch::async, [this, prompt]() {
        return this->generate(prompt);
    });
}

} // namespace core
} // namespace heidi
