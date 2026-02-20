#include "manifest.h"
#include <sstream>
#include <iomanip>
#include <openssl/hmac.h>
#include <openssl/evp.h>

namespace heidi {
namespace core {

std::string Manifest::to_canonical_json() const {
    std::ostringstream ss;
    ss << "{";
    ss << "\"created_at\":\"" << created_at << "\",";
    ss << "\"dataset_hash\":\"" << dataset_hash << "\",";
    
    // Sorted keys for guardrail_snapshot
    ss << "\"guardrail_snapshot\":{";
    bool first = true;
    for (const auto& kv : guardrail_snapshot) {
        if (!first) ss << ",";
        ss << "\"" << kv.first << "\":\"" << kv.second << "\"";
        first = false;
    }
    ss << "},";
    
    ss << "\"record_count\":" << record_count << ",";
    ss << "\"replay_hash\":\"" << replay_hash << "\",";
    ss << "\"schema_version\":\"" << schema_version << "\"";
    ss << "}";
    return ss.str();
}

std::string SignatureUtil::hmac_sha256(const std::string& data, const std::string& key) {
    unsigned char hash[EVP_MAX_MD_SIZE];
    unsigned int len = 0;

    HMAC(EVP_sha256(), key.c_str(), key.length(), 
         reinterpret_cast<const unsigned char*>(data.c_str()), data.length(), 
         hash, &len);

    std::stringstream ss;
    ss << std::hex << std::setfill('0');
    for (unsigned int i = 0; i < len; i++) {
        ss << std::setw(2) << static_cast<int>(hash[i]);
    }
    return ss.str();
}

bool SignatureUtil::verify(const std::string& data, const std::string& signature, const std::string& key) {
    std::string expected = hmac_sha256(data, key);
    // Timing-safe comparison would be better, but standard string comparison for now.
    return expected == signature;
}

} // namespace core
} // namespace heidi
