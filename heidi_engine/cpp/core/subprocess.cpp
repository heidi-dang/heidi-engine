#include "subprocess.h"
#include <unistd.h>
#include <sys/wait.h>
#include <stdexcept>
#include <array>
#include <cstring>
#include <poll.h>
#include <signal.h>
#include <chrono>
#include <thread> // Required for std::this_thread::sleep_for
#include <errno.h> // Required for errno

namespace heidi {
namespace core {

int Subprocess::execute(const std::vector<std::string>& args, std::string& output, int timeout_seconds) {
    if (args.empty()) {
        throw std::invalid_argument("args cannot be empty");
    }

    int pipefd[2];
    if (pipe(pipefd) == -1) {
        throw std::runtime_error("failed to create pipe");
    }

    pid_t pid = fork();
    if (pid == -1) {
        close(pipefd[0]);
        close(pipefd[1]);
        throw std::runtime_error("failed to fork");
    }

    if (pid == 0) {
        // Child process
        close(pipefd[0]);
        dup2(pipefd[1], STDOUT_FILENO);
        dup2(pipefd[1], STDERR_FILENO);
        close(pipefd[1]);

        std::vector<char*> c_args;
        for (const auto& arg : args) {
            c_args.push_back(const_cast<char*>(arg.c_str()));
        }
        c_args.push_back(nullptr);

        execvp(c_args[0], c_args.data());
        // If execvp returns, it must have failed
        // Use _exit() to avoid flushing parent buffers in child
        _exit(127);
    } else {
        // Parent process
        close(pipefd[1]);

        char buffer[4096];
        struct pollfd pfd;
        pfd.fd = pipefd[0];
        pfd.events = POLLIN;

        auto start_time = std::chrono::steady_clock::now();
        bool timed_out = false;

        while (true) {
            int poll_timeout_ms = -1; // Block indefinitely by default
            
            if (timeout_seconds > 0) {
                auto now = std::chrono::steady_clock::now();
                auto elapsed_seconds = std::chrono::duration_cast<std::chrono::seconds>(now - start_time).count();
                if (elapsed_seconds >= timeout_seconds) {
                    timed_out = true;
                    break;
                }
                // Calculate remaining time for poll, or use a small interval
                // to check overall timeout more frequently.
                long long remaining_ms = (timeout_seconds - elapsed_seconds) * 1000;
                poll_timeout_ms = std::min((long long)100, remaining_ms); // Poll for max 100ms
                if (poll_timeout_ms <= 0) { // If remaining time is very small or negative
                    timed_out = true;
                    break;
                }
            }

            int ret = poll(&pfd, 1, poll_timeout_ms);
            if (ret > 0 && (pfd.revents & POLLIN)) {
                ssize_t bytes_read = read(pipefd[0], buffer, sizeof(buffer) - 1);
                if (bytes_read > 0) {
                    output.append(buffer, bytes_read);
                } else if (bytes_read == 0) {
                    // EOF, pipe closed by child
                    break; 
                } else {
                    if (errno == EINTR) continue; // Interrupted by signal, retry
                    // Other read error
                    break;
                }
            } else if (ret == 0) {
                // poll timed out, loop continues and checks overall timeout_seconds
            } else if (ret < 0 && errno == EINTR) {
                continue; // Interrupted by signal, retry
            } else if (pfd.revents & (POLLERR | POLLHUP)) {
                // Pipe error or hung up (closed by writer)
                break;
            }
        }

        close(pipefd[0]);

        if (timed_out) {
            // Hardening: Graceful termination attempt using killpg for process trees
            killpg(pid, SIGTERM);
            
            // Give it 2 seconds to shut down gracefully
            for (int i = 0; i < 20; ++i) { // 20 * 100ms = 2 seconds
                int status;
                pid_t res = waitpid(pid, &status, WNOHANG);
                if (res == pid) {
                    output += "\n[HEIDI-CORE] Process terminated after SIGTERM timeout.";
                    if (WIFEXITED(status)) {
                        return WEXITSTATUS(status);
                    } else if (WIFSIGNALED(status)) {
                        return 128 + WTERMSIG(status);
                    }
                    return -1; // Should not happen if WIFEXITED or WIFSIGNALED
                } else if (res == -1 && errno == ECHILD) {
                    // Child already reaped by another waitpid or handler
                    output += "\n[HEIDI-CORE] Process was already reaped.";
                    return -1; // Indicate abnormal termination
                }
                std::this_thread::sleep_for(std::chrono::milliseconds(100));
            }
            
            // Hardening: Absolute enforcement using killpg for process trees
            killpg(pid, SIGKILL);
            int status;
            waitpid(pid, &status, 0); // Blocking wait for SIGKILLed process
            output += "\n[HEIDI-CORE] Process hung and was forcefully SIGKILLed.";
            return -1; // Killed execution
        }

        // Normal exit waiting (if not timed out)
        int status;
        waitpid(pid, &status, 0);

        if (WIFEXITED(status)) {
            return WEXITSTATUS(status);
        } else if (WIFSIGNALED(status)) {
            return 128 + WTERMSIG(status);
        }
    }

    return -1; // Should ideally be covered by WIFEXITED or WIFSIGNALED
}

} // namespace core
} // namespace heidi
