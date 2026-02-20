#include "daemon.h"
#include <iostream>
#include <string>
#include <vector>

void print_usage() {
    std::cout << "Usage: heidid [options]\n"
              << "Options:\n"
              << "  -d, --daemon     Run in the background (detach from terminal)\n"
              << "  -p, --port       Specify HTTP port (default 8080)\n"
              << "  -h, --host       Specify HTTP host (default 127.0.0.1)\n"
              << "  --help           Show this useage message\n";
}

int main(int argc, char* argv[]) {
    heidi::daemon::DaemonConfig config;

    // Really simple argument parsing
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "-d" || arg == "--daemon") {
            config.detach = true;
        } else if ((arg == "-p" || arg == "--port") && i + 1 < argc) {
            config.port = std::stoi(argv[++i]);
        } else if ((arg == "-h" || arg == "--host") && i + 1 < argc) {
            config.host = argv[++i];
        } else if (arg == "--help") {
            print_usage();
            return 0;
        } else {
            std::cerr << "Unknown argument: " << arg << "\n";
            print_usage();
            return 1;
        }
    }

    // Create and start the Daemon
    heidi::daemon::Daemon daemon(config);
    daemon.init();
    daemon.start();

    return 0;
}
