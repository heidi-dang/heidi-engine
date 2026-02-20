#pragma once

#include <string>

namespace heidi {
namespace core {

// transport_post performs an HTTP POST and returns the response body.
// It sets response_code to the HTTP status code.
// Implementations live in provider_transport_curl.cpp or provider_transport_stub.cpp
std::string transport_post(const std::string& url, const std::string& auth_header, const std::string& json_body, int& response_code);

} // namespace core
} // namespace heidi
