#include "provider_transport.h"
#include <stdexcept>

namespace heidi {
namespace core {

std::string transport_post(const std::string& /*url*/, const std::string& /*auth_header*/, const std::string& /*json_body*/, int& response_code) {
    (void)response_code;
    throw std::runtime_error("libcurl headers not available; install libcurl dev headers or configure build with network disabled");
}

} // namespace core
} // namespace heidi
