#pragma once

#include <string>

namespace heidi {
namespace core {

class StatusWriter {
public:
    StatusWriter(const std::string& status_path);

    // Write a JSON string atomically
    void write(const std::string& json_content);

private:
    std::string status_path_;
};

} // namespace core
} // namespace heidi
