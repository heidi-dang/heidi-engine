#include "status_writer.h"
#include <fstream>
#include <cstdio>
#include <stdexcept>

namespace heidi {
namespace core {

StatusWriter::StatusWriter(const std::string& status_path) 
    : status_path_(status_path) {
}

void StatusWriter::write(const std::string& json_content) {
    std::string tmp_path = status_path_ + ".tmp";
    
    // Write to tmp file
    std::ofstream ofs(tmp_path);
    if (!ofs.is_open()) {
        throw std::runtime_error("Could not open tmp status file " + tmp_path);
    }
    ofs << json_content;
    ofs.flush();
    ofs.close();
    
    // Atomic rename
    if (std::rename(tmp_path.c_str(), status_path_.c_str()) != 0) {
        throw std::runtime_error("Failed to rename tmp status file " + tmp_path);
    }
}

} // namespace core
} // namespace heidi
