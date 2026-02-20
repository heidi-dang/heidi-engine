#pragma once

#include <string>
#include <memory>
#include "httplib.h"
#include "../core/core.h"
#include "rpc_server.h"
#include "provider.h"
#include <memory>

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
    std::unique_ptr<RPCServer> rpc_server_;
    std::shared_ptr<heidi::core::AIApiProvider> provider_;
    
    std::string rpc_dispatch(const std::string& req_json);
};

} // namespace daemon
} // namespace heidi
