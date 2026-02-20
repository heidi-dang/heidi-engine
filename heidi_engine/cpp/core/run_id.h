#pragma once

#include <string>

namespace heidi {
namespace core {

class RunId {
public:
    static std::string generate();
};

} // namespace core
} // namespace heidi
