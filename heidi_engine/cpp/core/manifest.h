#pragma once

#include <string>
#include <vector>
#include <map>

namespace heidi {
namespace core {

struct Manifest {
    // Exactly 12 keys for Lane D Hard-Lock
    std::string run_id;            // 1
    std::string engine_version;    // 2
    std::string created_at;        // 3
    std::string schema_version;    // 4
    std::string dataset_hash;      // 5
    int record_count = 0;          // 6
    std::string replay_hash;       // 7
    std::string signing_key_id;    // 8
    std::string final_state;       // 9
    int total_runtime_sec = 0;     // 10
    int event_count = 0;           // 11
    std::map<std::string, std::string> guardrail_snapshot; // 12

    /**
     * @brief Serializes the manifest to a canonical JSON string.
     * Required for HMAC signature stability.
     */
    std::string to_canonical_json() const;
};

class SignatureUtil {
public:
    /**
     * @brief Computes HMAC-SHA256 over input data given a key.
     */
    static std::string hmac_sha256(const std::string& data, const std::string& key);

    /**
     * @brief Verifies a signature against data and key.
     */
    static bool verify(const std::string& data, const std::string& signature, const std::string& key);
};

} // namespace core
} // namespace heidi
