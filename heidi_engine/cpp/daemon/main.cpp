#include "engine_daemon.h"
#include <iostream>
#include <string>

int main(int argc, char* argv[]) {
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
        daemon.run();
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "[FATAL] Daemon error: " << e.what() << std::endl;
        return 1;
    }
}
