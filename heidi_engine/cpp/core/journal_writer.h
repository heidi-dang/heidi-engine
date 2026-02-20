#pragma once

#include <string>
#include <map>
#include <vector>

namespace heidi {
namespace core {

struct Event {
    std::string ts;
    std::string run_id;
    int round = 0;
    std::string stage;
    std::string level;
    std::string event_type;
    std::string message;
    
    std::map<std::string, int> counters_delta;
    std::map<std::string, int> usage_delta;
    std::vector<std::string> artifact_paths;
    std::string error;

    std::string to_json(const std::string& prev_hash) const;
    static constexpr const char* SCHEMA_VERSION = "1.0";
    static constexpr size_t MAX_PAYLOAD_BYTES = 1024 * 1024; // 1MB limit for safety
};

class JournalWriter {
public:
    JournalWriter(const std::string& journal_path, const std::string& initial_hash);
    ~JournalWriter();

    void write(const Event& event);
    std::string current_hash() const { return last_hash_; }
    std::string sanitize(const std::string& input) const;
    
    /**
     * @brief Strict schema validation for incoming event strings.
     * Implements Phase 6 Lane D: Reject unknown, missing, or oversized fields.
     */
    static void validate_strict(const std::string& json_line);

private:
    std::string compute_sha256(const std::string& data) const;
    
    std::string journal_path_;
    std::string last_hash_;
};

} // namespace core
} // namespace heidi
