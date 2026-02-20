#include "subprocess.h"
#include <unistd.h>
#include <sys/wait.h>
#include <stdexcept>
#include <array>
#include <cstring>

namespace heidi {
namespace core {

int Subprocess::execute(const std::vector<std::string>& args, std::string& output) {
    if (args.empty()) {
        throw std::invalid_argument("Cannot execute empty command");
    }

    int pipefd[2];
    if (pipe(pipefd) == -1) {
        throw std::runtime_error("pipe() failed");
    }

    pid_t pid = fork();
    if (pid == -1) {
        close(pipefd[0]);
        close(pipefd[1]);
        throw std::runtime_error("fork() failed");
    }

    if (pid == 0) {
        // Child process
        close(pipefd[0]); // Close read end

        // Redirect stdout and stderr to the pipe
        dup2(pipefd[1], STDOUT_FILENO);
        dup2(pipefd[1], STDERR_FILENO);
        close(pipefd[1]);

        std::vector<char*> c_args;
        for (const auto& arg : args) {
            c_args.push_back(const_cast<char*>(arg.c_str()));
        }
        c_args.push_back(nullptr);

        execvp(c_args[0], c_args.data());
        
        // If execvp fails
        fprintf(stderr, "execvp failed: %s\n", strerror(errno));
        _exit(127);
    } else {
        // Parent process
        close(pipefd[1]); // Close write end

        std::array<char, 4096> buffer;
        ssize_t bytes_read;
        while ((bytes_read = read(pipefd[0], buffer.data(), buffer.size())) > 0) {
            output.append(buffer.data(), bytes_read);
        }

        close(pipefd[0]);

        int status;
        waitpid(pid, &status, 0);

        if (WIFEXITED(status)) {
            return WEXITSTATUS(status);
        } else if (WIFSIGNALED(status)) {
            return 128 + WTERMSIG(status);
        }
    }

    return -1;
}

} // namespace core
} // namespace heidi
