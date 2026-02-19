#include "engine_daemon.h"
#include <iostream>
#include <string>

int main(int argc, char* argv[]) {
    std::string config_path = "engine_config.yaml";
    
    if (argc > 1) {
        for (int i = 1; i < argc; ++i) {
            std::string arg = argv[i];
            if (arg == "--help" || arg == "-h") {
                std::cout << "Usage: heidid [--config path/to/config.yaml] [--provider provider_name]" << std::endl;
                return 0;
            }
            if (i + 1 < argc && arg == "--config") {
                config_path = argv[i + 1];
                i++;
            } else if (i + 1 < argc && arg == "--provider") {
                std::string provider = argv[i + 1];
                setenv("HEIDI_PROVIDER", provider.c_str(), 1);
                i++;
            }
        }
    }

    try {
        heidi::EngineDaemon daemon(config_path);
        daemon.run();
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "[FATAL] Daemon error: " << e.what() << std::endl;
        return 1;
    }
}
