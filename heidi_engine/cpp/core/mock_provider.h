#pragma once

#include <string>
#include <future>

namespace heidi {
namespace core {

// A deterministic mock provider for testing the pipeline locally without network I/O
class MockProvider {
public:
    MockProvider(int simulated_delay_ms = 10);
    ~MockProvider();

    std::string generate(const std::string& prompt);
    std::future<std::string> generate_async(const std::string& prompt);

private:
    int delay_ms_;
};

} // namespace core
} // namespace heidi
