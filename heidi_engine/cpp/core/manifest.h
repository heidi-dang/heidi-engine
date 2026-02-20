#pragma once

#include <string>
#include <vector>
#include <map>

namespace heidi {
namespace core {

struct Manifest {
    std::string dataset_hash;
    int record_count = 0;
    std::string created_at;
    std::string schema_version = "1.0";
    std::map<std::string, std::string> guardrail_snapshot;
    std::string replay_hash;

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
