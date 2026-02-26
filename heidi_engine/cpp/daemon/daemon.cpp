#include "daemon.h"
#include <iostream>
#include <fstream>
#include <unistd.h>
#include <csignal>
#include <sys/types.h>
#include <sys/stat.h>
#include <cstdlib>
#include <nlohmann/json.hpp>
#include <chrono>
#include <filesystem>

namespace heidi {
namespace daemon {

Daemon::Daemon(const DaemonConfig& config)
    : config_(config), 
      svr_(std::make_unique<httplib::Server>()),
      core_(std::make_unique<heidi::core::Core>()),
      rpc_server_(std::make_unique<RPCServer>()) {
}

Daemon::~Daemon() {
    stop();
}

void Daemon::init() {
    core_->init();
    setup_routes();
}

void Daemon::setup_routes() {
    // Basic status endpoint serving JSON representation of Core state
    svr_->Get("/api/v1/status", [this](const httplib::Request&, httplib::Response& res) {
        std::string status_json = core_->get_status_json();
        res.set_content(status_json, "application/json");
    });

    // An endpoint to arbitrarily begin training early
    svr_->Post("/api/v1/action/train_now", [this](const httplib::Request&, httplib::Response& res) {
        core_->action_train_now();
        res.set_content("{\"status\":\"train initiated\"}", "application/json");
    });
}

void Daemon::daemonize() {
    pid_t pid = fork();

    if (pid < 0) {
        exit(EXIT_FAILURE);
    }
    if (pid > 0) {
        // We are the parent process (exit)
        exit(EXIT_SUCCESS);
    }
    
    // We are the child process.
    // Create a new session and process group.
    if (setsid() < 0) {
        exit(EXIT_FAILURE);
    }
    
    // Catch, ignore and handle signals
    std::signal(SIGCHLD, SIG_IGN);
    std::signal(SIGHUP, SIG_IGN);

    // Fork off for the second time to ensure daemon cannot acquire terminal terminal
    pid = fork();
    if (pid < 0) {
        exit(EXIT_FAILURE);
    }
    if (pid > 0) {
        exit(EXIT_SUCCESS);
    }

    // Set new file permissions
    umask(027);

    // Change working directory to root / or specific dir
    if ((chdir("/")) < 0) {
        exit(EXIT_FAILURE);
    }

    // Close all open file descriptors
    for (int x = sysconf(_SC_OPEN_MAX); x >= 0; x--) {
        close(x);
    }

    // Create pid file if needed/configured here...
}

void Daemon::start() {
    if (config_.detach) {
        daemonize();
    }
    
    // For Phase 4 simplification, we start in 'collect' mode so the daemon sits IDLE
    // and tests can trigger transitions like action_train_now.
    core_->start("collect");
    
    // Start the Core engine loop asynchronously
    std::thread engine_thread([this]() {
        while (true) {
            core_->tick();
            // Sleep briefly to avoid 100% CPU lock when idle
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    });
    engine_thread.detach();

    // Determine RPC socket path
    const char* home = std::getenv("HEIDI_HOME");
    std::string runtime_dir = home ? std::string(home) + "/runtime" : [&]() {
        const char* u_home = std::getenv("HOME");
        return u_home ? std::string(u_home) + "/.local/heidi-engine/runtime" : std::string("/tmp/heidi-engine/runtime");
    }();
    
    // Ensure runtime directory exists
    std::error_code ec;
    std::filesystem::create_directories(runtime_dir, ec);
    if (ec) {
        std::cerr << "Warning: Failed to create runtime directory: " << ec.message() << std::endl;
    }
    
    std::string sock_path = runtime_dir + "/heidid.sock";
    
    auto dispatch = [this](const std::string& req_json) -> std::string {
        return this->rpc_dispatch(req_json);
    };
    
    if (!rpc_server_->start(sock_path, dispatch)) {
        throw std::runtime_error("RPCServer failed to start on " + sock_path);
    }

    std::cout << "Starting heidid listening on " << config_.host << ":" << config_.port << std::endl;
    if (!svr_->listen(config_.host.c_str(), config_.port)) {
        std::cerr << "Failed to start HTTP server." << std::endl;
    }
}

std::string Daemon::rpc_dispatch(const std::string& req_json) {
    using json = nlohmann::json;
    try {
        json req = json::parse(req_json);
        if (!req.contains("method") || !req.contains("id")) {
            return "{\"jsonrpc\":\"2.0\",\"error\":{\"code\":-32600,\"message\":\"Invalid Request\"},\"id\":null}";
        }
        std::string method = req["method"];
        auto id = req["id"];
        if (method != "provider.generate") {
            json resp = {{"jsonrpc", "2.0"}, {"error", {{"code", -32601}, {"message", "Method not found"}}}, {"id", id}};
            return resp.dump();
        }
        
        json params = req.value("params", json::object());
        
        bool wants_real = params.value("real_network_enabled", false);
#ifndef HAVE_CURL
        if (wants_real) {
            json resp = {{"jsonrpc", "2.0"}, {"error", {{"code", -32001}, {"message", "E_TRANSPORT_UNAVAILABLE: curl not built"}}}, {"id", id}};
            return resp.dump();
        }
#endif
        
        std::string model = params.value("model", "dummy");
        
        if (!provider_ || provider_->name() != params.value("provider", "openai")) {
            heidi::core::ProviderConfig pcfg;
            pcfg.type = heidi::core::parseProviderType(params.value("provider", "openai"));
            pcfg.model = model;
            pcfg.api_key = "dummy";
            pcfg.real_network_enabled = wants_real;
            provider_ = heidi::core::createProvider(pcfg);
        }
        
        heidi::core::GenerationParams gparams;
        gparams.temperature = params.value("temperature", 0.7);
        gparams.max_tokens = params.value("max_tokens", 512);
        
        std::vector<heidi::core::Message> msgs;
        if (params.contains("messages") && params["messages"].is_array()) {
            for (const auto& m : params["messages"]) {
                msgs.push_back({m.value("role", "user"), m.value("content", "")});
            }
        }
        
        auto start_t = std::chrono::steady_clock::now();
        heidi::core::ApiResponse api_resp = provider_->generate(msgs, gparams);
        auto end_t = std::chrono::steady_clock::now();
        int latency = std::chrono::duration_cast<std::chrono::milliseconds>(end_t - start_t).count();
        
        json result = {
            {"output", api_resp.content},
            {"usage", {
                {"prompt_tokens", api_resp.usage_prompt_tokens},
                {"completion_tokens", api_resp.usage_completion_tokens},
                {"total_tokens", api_resp.usage_total_tokens}
            }},
            {"provider_latency_ms", latency},
            {"transport_status", "OK"}
        };
        
        json resp = {{"jsonrpc", "2.0"}, {"result", result}, {"id", id}};
        return resp.dump();

    } catch (const std::exception& e) {
        json resp = {{"jsonrpc", "2.0"}, {"error", {{"code", -32603}, {"message", std::string("Internal error: ") + e.what()}}}, {"id", nullptr}};
        return resp.dump();
    }
}

void Daemon::stop() {
    if (svr_) {
        svr_->stop();
    }
    if (rpc_server_) {
        rpc_server_->stop();
    }
    if (core_) {
        core_->shutdown();
    }
}

} // namespace daemon
} // namespace heidi
