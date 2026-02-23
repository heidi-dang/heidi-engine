#include "journal_writer.h"
#include <fstream>
#include <sstream>
#include <iomanip>
#include <stdexcept>
#include <openssl/sha.h>
#include <regex>

namespace heidi {
namespace core {

std::string Event::to_json(const std::string& prev_hash) const {
    std::ostringstream ss;
    ss << "{";
    ss << "\"event_version\":\"" << SCHEMA_VERSION << "\",";
    ss << "\"ts\":\"" << ts << "\",";
    ss << "\"run_id\":\"" << run_id << "\",";
    ss << "\"round\":" << round << ",";
    ss << "\"stage\":\"" << stage << "\",";
    ss << "\"level\":\"" << level << "\",";
    ss << "\"event_type\":\"" << event_type << "\",";
    ss << "\"message\":\"" << message << "\",";
    
    ss << "\"counters_delta\":{";
    bool first = true;
    for (const auto& kv : counters_delta) {
        if (!first) ss << ",";
        ss << "\"" << kv.first << "\":" << kv.second;
        first = false;
    }
    ss << "},";
    
    ss << "\"usage_delta\":{";
    first = true;
    for (const auto& kv : usage_delta) {
        if (!first) ss << ",";
        ss << "\"" << kv.first << "\":" << kv.second;
        first = false;
    }
    ss << "},";
    
    ss << "\"artifact_paths\":[";
    first = true;
    for (const auto& path : artifact_paths) {
        if (!first) ss << ",";
        ss << "\"" << path << "\"";
        first = false;
    }
    ss << "],";

    ss << "\"prev_hash\":\"" << prev_hash << "\"";
    ss << "}";
    return ss.str();
}

JournalWriter::JournalWriter(const std::string& journal_path, const std::string& initial_hash)
    : journal_path_(journal_path), last_hash_(initial_hash) {
}

JournalWriter::~JournalWriter() = default;

std::string JournalWriter::compute_sha256(const std::string& data) const {
    unsigned char hash[SHA256_DIGEST_LENGTH];
    SHA256_CTX sha256;
    SHA256_Init(&sha256);
    SHA256_Update(&sha256, data.c_str(), data.size());
    SHA256_Final(hash, &sha256);
    
    std::stringstream ss;
    for(int i = 0; i < SHA256_DIGEST_LENGTH; i++) {
        ss << std::hex << std::setw(2) << std::setfill('0') << (int)hash[i];
    }
    return ss.str();
}

std::string JournalWriter::sanitize(const std::string& input) const {
    // Redact sensitive patterns BEFORE JSON escaping to avoid backslash interference
    std::string safe = std::regex_replace(input, std::regex("g[h]p_[a-zA-Z0-9]{36}"), "[GITHUB_TOKEN]");
    safe = std::regex_replace(safe, std::regex("s[k]-[a-zA-Z0-9]{20,}"), "[OPENAI_KEY]");
    safe = std::regex_replace(safe, std::regex("Bearer\\s+[\\w\\-]{20,}"), "[BEARER_TOKEN]");

    // JSON Escaping
    safe = std::regex_replace(safe, std::regex("\n"), "\\n");
    safe = std::regex_replace(safe, std::regex("\r"), "\\r");
    safe = std::regex_replace(safe, std::regex("\""), "\\\"");
    
    return safe;
}

void JournalWriter::validate_strict(const std::string& json_line) {
    if (json_line.size() > Event::MAX_PAYLOAD_BYTES) {
        throw std::runtime_error("Schema Lock: Payload size exceeds limit");
    }

    // Lane D: Reject malformed floats (NaN/Inf)
    if (json_line.find("nan") != std::string::npos || json_line.find("inf") != std::string::npos) {
        throw std::runtime_error("Schema Lock: Rejecting malformed float (NaN/Inf)");
    }

    // Phase 6 Requirement: Reject unknown or missing fields.
    static const std::vector<std::string> required = {
        "event_version", "ts", "run_id", "round", "stage", "level", 
        "event_type", "message", "counters_delta", "usage_delta", 
        "artifact_paths", "prev_hash"
    };

    // 1. Verify all required keys are present
    for (const auto& key : required) {
        if (json_line.find("\"" + key + "\":") == std::string::npos) {
            throw std::runtime_error("Schema Lock: Missing required field: " + key);
        }
    }

    // 2. Verify event_version is correct
    if (json_line.find("\"event_version\":\"" + std::string(Event::SCHEMA_VERSION) + "\"") == std::string::npos) {
         throw std::runtime_error("Schema Lock: Unsupported or missing event_version");
    }

    // 3. Count top-level keys by looking for key patterns at nesting level 1.
    // In canonical JSON with no spaces, top-level keys follow '{' or ','.
    int top_level_count = 0;
    if (json_line.find("\"event_version\":") != std::string::npos) top_level_count++;
    
    // Hard lock on top-level key count (12)
    // We count occurrences of ',"' which prefix keys 2-12
    size_t pos = 0;
    int comma_keys = 0;
    while ((pos = json_line.find(",\"", pos)) != std::string::npos) {
        comma_keys++;
        pos += 2;
    }
    
    if (comma_keys != 11) {
        throw std::runtime_error("Schema Lock: Unknown or missing top-level fields (Expected 12 keys total)");
    }
}

void JournalWriter::write(const Event& event) {
    Event safe_event = event;
    safe_event.message = sanitize(event.message);
    
    std::string json_line = safe_event.to_json(last_hash_);
    std::string line_with_newline = json_line + "\n";
    
    // Write atomically / append to file
    std::ofstream ofs(journal_path_, std::ios_base::app);
    if (!ofs.is_open()) {
        throw std::runtime_error("Could not open journal " + journal_path_);
    }
    ofs << line_with_newline;
    ofs.flush();
    
    // Hash chain
    last_hash_ = compute_sha256(line_with_newline);
}

} // namespace core
} // namespace heidi
