#include "engine_daemon.h"
#include <iostream>
#include <string>
#include <csignal>
#include <atomic>
#include <unistd.h>

std::atomic<bool> shutdown_requested{false};

void signal_handler(int signal) {
    std::cout << "\n[INFO] Received signal " << signal << ", initiating graceful shutdown..." << std::endl;
    shutdown_requested = true;
}

int main(int argc, char* argv[]) {
    // Set up signal handlers for graceful shutdown
    struct sigaction sa;
    sa.sa_handler = signal_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    
    sigaction(SIGINT, &sa, nullptr);
    sigaction(SIGTERM, &sa, nullptr);
    
    std::string config_path = "engine_config.yaml";
    
    if (argc > 1) {
        std::string arg1 = argv[1];
        if (arg1 == "--help" || arg1 == "-h") {
            std::cout << "Usage: heidid [--config path/to/config.yaml]" << std::endl;
            return 0;
        }
        if (argc > 2 && arg1 == "--config") {
            config_path = argv[2];
        }
    }

    try {
        heidi::EngineDaemon daemon(config_path);
        
        // Run daemon in a way that can be interrupted
        while (!shutdown_requested) {
            // This is a simplified approach - in a real implementation,
            // the daemon should check shutdown_requested periodically
            daemon.run();
            break; // For now, just run once and exit
        }
        
        std::cout << "[INFO] Daemon shutdown complete" << std::endl;
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "[FATAL] Daemon error: " << e.what() << std::endl;
        return 1;
    }
}
