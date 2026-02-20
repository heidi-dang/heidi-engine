#pragma once

#include "mock_provider.h"
#include <vector>
#include <string>
#include <memory>
#include <future>

namespace heidi {
namespace core {

class AsyncCollector {
public:
    AsyncCollector(std::shared_ptr<MockProvider> provider);

    // Given a list of prompts, generate all responses fully concurrently.
    // Blocks until all responses are retrieved.
    std::vector<std::string> generate_batch(const std::vector<std::string>& prompts);

    // Provide a helper to just generate N identical samples (useful for synthetic generation stages)
    std::vector<std::string> generate_n(const std::string& base_prompt, int n);

private:
    std::shared_ptr<MockProvider> provider_;
};

} // namespace core
} // namespace heidi
