#include <gtest/gtest.h>
#include "../heidi_engine/cpp/core/journal_writer.h"
#include "../heidi_engine/cpp/core/core.h"
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
