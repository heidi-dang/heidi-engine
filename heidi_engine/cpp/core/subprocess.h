#pragma once

#include <string>
#include <vector>

namespace heidi {
namespace core {

class Subprocess {
public:
    // Executes a command and captures its standard output and standard error.
    // Returns the exit code of the process. Throws runtime_error on fork/exec failure.
    // If timeout_seconds > 0, the process will be sent SIGTERM and then SIGKILL if it exceeds the limit.
    static int execute(const std::vector<std::string>& args, std::string& output, int timeout_seconds = 0);
};

} // namespace core
} // namespace heidi
