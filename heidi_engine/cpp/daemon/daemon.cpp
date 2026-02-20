#include "daemon.h"
#include <iostream>
#include <fstream>
#include <unistd.h>
#include <csignal>
#include <sys/types.h>
#include <sys/stat.h>
#include <cstdlib>

namespace heidi {
namespace daemon {

static std::function<void()> g_shutdown_callback;

static void signal_handler(int sig) {
    if (sig == SIGTERM || sig == SIGINT) {
        std::cout << "Received signal " << sig << ", initiating graceful shutdown..." << std::endl;
        if (g_shutdown_callback) {
            g_shutdown_callback();
        }
        // Note: We don't call exit(0) here to allow normal cleanup in main
    }
}

Daemon::Daemon(const DaemonConfig& config)
    : config_(config),
      svr_(std::make_unique<httplib::Server>()),
      core_(std::make_unique<heidi::core::Core>()) {
}

Daemon::~Daemon() {
    stop();
}

void Daemon::init() {
    core_->init();
    setup_routes();

    // Register signal handlers for graceful shutdown
    g_shutdown_callback = [this]() { this->stop(); };
    std::signal(SIGTERM, signal_handler);
    std::signal(SIGINT, signal_handler);
}

void Daemon::setup_routes() {
    // Health check endpoint
    svr_->Get("/health", [](const httplib::Request&, httplib::Response& res) {
        res.set_content("{\"status\":\"ok\"}", "application/json");
    });

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
    running_ = true;

    // Start the Core engine loop asynchronously
    engine_thread_ = std::thread([this]() {
        while (running_) {
            core_->tick();
            // Sleep briefly to avoid 100% CPU lock when idle
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    });

    std::cout << "Starting heidid listening on " << config_.host << ":" << config_.port << std::endl;
    if (!svr_->listen(config_.host.c_str(), config_.port)) {
        std::cerr << "Failed to start HTTP server." << std::endl;
    }
}

void Daemon::stop() {
    running_ = false;
    if (svr_) {
        svr_->stop();
    }
    if (engine_thread_.joinable()) {
        engine_thread_.join();
    }
    if (core_) {
        core_->shutdown();
    }
}

} // namespace daemon
} // namespace heidi
