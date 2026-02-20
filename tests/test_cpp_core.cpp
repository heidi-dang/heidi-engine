#include <gtest/gtest.h>
#include "../heidi_engine/cpp/core/journal_writer.h"
#include "../heidi_engine/cpp/core/core.h"
<<<<<<< HEAD
#include "../heidi_engine/cpp/core/manifest.h"
#include <heidi-kernel/resource_governor.h>
=======
>>>>>>> origin/main
#include <fstream>
#include <cstdio>
#include <regex>

using namespace heidi::core;

TEST(JournalWriterTest, HashChaining) {
    std::string tmp_journal = "/tmp/test_journal.jsonl";
    std::remove(tmp_journal.c_str());

    JournalWriter writer(tmp_journal, "init_hash");
    
    Event e1;
    e1.ts = "2026-02-20T00:00:00.000Z";
    e1.run_id = "run_1";
    e1.stage = "generate";
    e1.event_type = "stage_start";
    e1.level = "info";
    e1.message = "Hello World";
    
    writer.write(e1);
    
    std::string h1 = writer.current_hash();
    EXPECT_NE(h1, "init_hash");
    EXPECT_EQ(h1.length(), 64); // SHA256 hex length
    
    Event e2 = e1;
    e2.message = "Second";
    writer.write(e2);
    
    std::string h2 = writer.current_hash();
    EXPECT_NE(h2, h1);

    // Verify it was actually written
    std::ifstream ifs(tmp_journal);
    std::string line;
    std::getline(ifs, line);
    EXPECT_TRUE(line.find("Hello World") != std::string::npos);
    EXPECT_TRUE(line.find("init_hash") != std::string::npos);
    
    std::getline(ifs, line);
    EXPECT_TRUE(line.find("Second") != std::string::npos);
    EXPECT_TRUE(line.find(h1) != std::string::npos);

    std::remove(tmp_journal.c_str());
}

TEST(JournalWriterTest, Redaction) {
    std::string tmp_journal = "/tmp/test_journal_redact.jsonl";
    std::remove(tmp_journal.c_str());

    JournalWriter writer(tmp_journal, "hash");
    Event e;
    e.message = "My key is sk-12345678901234567890 and token is ghp_123456789012345678901234567890123456!";
    writer.write(e);

    std::ifstream ifs(tmp_journal);
    std::string line;
    std::getline(ifs, line);
    
    EXPECT_TRUE(line.find("sk-12345678901234567890") == std::string::npos);
    EXPECT_TRUE(line.find("[OPENAI_KEY]") != std::string::npos);
    
    EXPECT_TRUE(line.find("ghp_123456789012345678901234567890123456") == std::string::npos);
    EXPECT_TRUE(line.find("[GITHUB_TOKEN]") != std::string::npos);

    std::remove(tmp_journal.c_str());
}

TEST(CoreTest, StateTransitions) {
    Core core;
    // We can't fully run init() without setting OUT_DIR env var, 
    // so we will test what we can or rely on Python testing.
}
<<<<<<< HEAD

TEST(GovernorTest, HighWatermarks) {
    heidi::GovernorPolicy policy;
    policy.cpu_high_watermark_pct = 80.0;
    policy.mem_high_watermark_pct = 90.0;
    policy.cooldown_ms = 1000;

    heidi::ResourceGovernor gov(policy);

    // 1. Under limits
    auto r1 = gov.decide(50.0, 80.0, 1, 0);
    EXPECT_EQ(r1.decision, heidi::GovernorDecision::START_NOW);
    EXPECT_EQ(r1.reason, heidi::BlockReason::NONE);

    // 2. CPU Over
    auto r2 = gov.decide(85.0, 80.0, 1, 0);
    EXPECT_EQ(r2.decision, heidi::GovernorDecision::HOLD_QUEUE);
    EXPECT_EQ(r2.reason, heidi::BlockReason::CPU_HIGH);
    EXPECT_EQ(r2.retry_after_ms, 1000);

    // 3. MEM Over
    auto r3 = gov.decide(50.0, 95.0, 1, 0);
    EXPECT_EQ(r3.decision, heidi::GovernorDecision::HOLD_QUEUE);
    EXPECT_EQ(r3.reason, heidi::BlockReason::MEM_HIGH);

    // 4. Multiple jobs (policy limit is default 10)
    auto r4 = gov.decide(50.0, 50.0, 11, 0);
    EXPECT_EQ(r4.decision, heidi::GovernorDecision::HOLD_QUEUE);
    EXPECT_EQ(r4.reason, heidi::BlockReason::RUNNING_LIMIT);
}

TEST(JournalWriterTest, StrictSchemaValidation) {
    // 1. Missing keys
    std::string bad_json = "{\"event_version\":\"1.0\",\"ts\":\"now\"}";
    EXPECT_THROW(heidi::core::JournalWriter::validate_strict(bad_json), std::runtime_error);

    // 2. Bad version
    std::string bad_version = "{\"event_version\":\"2.0\",\"ts\":\"now\",\"run_id\":\"123\",\"round\":1,\"stage\":\"s\",\"level\":\"i\",\"event_type\":\"e\",\"message\":\"m\",\"counters_delta\":{},\"usage_delta\":{},\"artifact_paths\":[],\"prev_hash\":\"h\"}";
    EXPECT_THROW(heidi::core::JournalWriter::validate_strict(bad_version), std::runtime_error);

    // 3. Oversized
    std::string oversized(2 * 1024 * 1024, 'a');
    EXPECT_THROW(heidi::core::JournalWriter::validate_strict(oversized), std::runtime_error);

    // 4. Correct schema
    std::string good_json = "{\"event_version\":\"1.0\",\"ts\":\"now\",\"run_id\":\"123\",\"round\":1,\"stage\":\"s\",\"level\":\"i\",\"event_type\":\"e\",\"message\":\"m\",\"counters_delta\":{},\"usage_delta\":{},\"artifact_paths\":[],\"prev_hash\":\"h\"}";
    EXPECT_NO_THROW(heidi::core::JournalWriter::validate_strict(good_json));
}

TEST(ManifestTest, CanonicalSerialization) {
    heidi::core::Manifest m;
    m.run_id = "r1";
    m.engine_version = "v1";
    m.created_at = "2026-02-20T10:00:00Z";
    m.schema_version = "1.0";
    m.dataset_hash = "sha256:abc";
    m.record_count = 100;
    m.replay_hash = "sha256:replay";
    m.signing_key_id = "k1";
    m.final_state = "VERIFIED";
    m.total_runtime_sec = 42;
    m.event_count = 1000;
    m.guardrail_snapshot["max_cpu"] = "80";

    std::string json = m.to_canonical_json();
    // Verify sorted alphabetical order of keys for top-level
    EXPECT_TRUE(json.find("\"created_at\"") < json.find("\"dataset_hash\""));
    EXPECT_TRUE(json.find("\"dataset_hash\"") < json.find("\"engine_version\""));
    EXPECT_TRUE(json.find("\"engine_version\"") < json.find("\"event_count\""));
    EXPECT_TRUE(json.find("\"event_count\"") < json.find("\"final_state\""));
    EXPECT_TRUE(json.find("\"final_state\"") < json.find("\"guardrail_snapshot\""));
    EXPECT_TRUE(json.find("\"guardrail_snapshot\"") < json.find("\"record_count\""));
}

TEST(SignatureTest, HMACVerification) {
    std::string data = "{\"test\":true}";
    std::string key = "super-secret-key";
    
    std::string sig = heidi::core::SignatureUtil::hmac_sha256(data, key);
    EXPECT_FALSE(sig.empty());
    EXPECT_TRUE(heidi::core::SignatureUtil::verify(data, sig, key));
    
    // Negative test: wrong key
    EXPECT_FALSE(heidi::core::SignatureUtil::verify(data, sig, "wrong-key"));
    
    // Negative test: tampered data
    EXPECT_FALSE(heidi::core::SignatureUtil::verify(data + " ", sig, key));
}
=======
>>>>>>> origin/main
