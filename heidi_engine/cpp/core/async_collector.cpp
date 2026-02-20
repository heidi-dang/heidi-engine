#include "async_collector.h"

namespace heidi {
namespace core {

AsyncCollector::AsyncCollector(std::shared_ptr<MockProvider> provider)
    : provider_(std::move(provider)) {
}

std::vector<std::string> AsyncCollector::generate_batch(const std::vector<std::string>& prompts) {
    if (!provider_) return {};

    std::vector<std::future<std::string>> futures;
    futures.reserve(prompts.size());
    
    // Dispatch all async
    for (const auto& prompt : prompts) {
        futures.push_back(provider_->generate_async(prompt));
    }
    
    // Join all
    std::vector<std::string> results;
    results.reserve(prompts.size());
    for (auto& fut : futures) {
        results.push_back(fut.get());
    }
    
    return results;
}

std::vector<std::string> AsyncCollector::generate_n(const std::string& base_prompt, int n) {
    std::vector<std::string> prompts;
    prompts.reserve(n);
    for (int i = 0; i < n; ++i) {
        prompts.push_back(base_prompt + " [Sample " + std::to_string(i) + "]");
    }
    return generate_batch(prompts);
}

} // namespace core
} // namespace heidi
