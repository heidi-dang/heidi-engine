#pragma once

#include <string>
#include <vector>

namespace heidi {
namespace core {

class Subprocess {
public:
    // Executes a command and captures its merged stdout and stderr.
    // Returns the exit code of the process.
    static int execute(const std::vector<std::string>& args, std::string& output);
};

} // namespace core
} // namespace heidi
