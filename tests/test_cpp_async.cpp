#include <gtest/gtest.h>
<<<<<<< HEAD
#include "../heidi_engine/cpp/core/mock_provider.h"
=======
>>>>>>> origin/main
#include "../heidi_engine/cpp/core/async_collector.h"
#include <chrono>

using namespace heidi::core;

<<<<<<< HEAD

=======
>>>>>>> origin/main
TEST(AsyncCollectorTest, GenerateParallel) {
    auto start_time = std::chrono::steady_clock::now();

    // 100ms delay for each call simulated
<<<<<<< HEAD
    auto provider = std::make_shared<heidi::core::MockProvider>(100);
    heidi::core::AsyncCollector collector(provider);
=======
    auto provider = std::make_shared<MockProvider>(100);
    AsyncCollector collector(provider);
>>>>>>> origin/main

    // Give it 10 prompts
    std::vector<std::string> prompts;
    for (int i = 0; i < 10; ++i) {
        prompts.push_back("Prompt " + std::to_string(i));
    }

    auto results = collector.generate_batch(prompts);
    
    auto end_time = std::chrono::steady_clock::now();
    auto duration_ms = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time).count();

    EXPECT_EQ(results.size(), 10);
    
    // Total duration should be close to 100ms (due to parallelism), not 1000ms.
    // Give some leeway for thread spawn overhead. We assert it runs much faster than completely sequential.
    EXPECT_LT(duration_ms, 500); 

    // Output correctness
    EXPECT_TRUE(results[0].find("Prompt 0") != std::string::npos);
    EXPECT_TRUE(results[9].find("Prompt 9") != std::string::npos);
}

TEST(AsyncCollectorTest, GenerateN) {
    auto provider = std::make_shared<MockProvider>(0); // 0ms for fast test
    AsyncCollector collector(provider);
    
    auto results = collector.generate_n("Write me a poem", 50);
    EXPECT_EQ(results.size(), 50);
    EXPECT_TRUE(results[0].find("[Sample 0]") != std::string::npos);
    EXPECT_TRUE(results[49].find("[Sample 49]") != std::string::npos);
}
