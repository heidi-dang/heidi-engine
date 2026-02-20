#pragma once

#include <string>
#include <memory>
#include <thread>
#include <atomic>
#include "httplib.h"
#include "../core/core.h"

namespace heidi {
namespace daemon {

struct DaemonConfig {
    int port = 8080;
    std::string host = "127.0.0.1";
    bool detach = false;
    std::string pid_file = "/var/run/heidid.pid"; // Optional
};

class Daemon {
public:
    Daemon(const DaemonConfig& config);
    ~Daemon();

    // Initializes the core and sets up HTTP routes
    void init();

    // Starts the HTTP server (blocks if attach, detaches if daemonized)
    void start();

    // Request graceful shutdown
    void stop();

private:
    void daemonize();
    void setup_routes();

    DaemonConfig config_;
    std::unique_ptr<httplib::Server> svr_;
    std::unique_ptr<heidi::core::Core> core_;
    std::thread engine_thread_;
    std::atomic<bool> running_{false};
};

} // namespace daemon
} // namespace heidi
