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
};

class JournalWriter {
public:
    JournalWriter(const std::string& journal_path, const std::string& initial_hash);
    ~JournalWriter();

    void write(const Event& event);
    std::string current_hash() const { return last_hash_; }

private:
    std::string compute_sha256(const std::string& data) const;
    std::string sanitize(const std::string& input) const;
    
    std::string journal_path_;
    std::string last_hash_;
};

} // namespace core
} // namespace heidi
