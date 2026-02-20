#pragma once

#include <string>
#include <fstream>
#include <cstdio>
#include <unistd.h>
#include <stdexcept>
#include <filesystem>

namespace heidi {
namespace utils {

/**
 * @brief Atomic file writer utility.
 * 
 * Implements Workstream 11 requirements:
 * - Writes to temp file first.
 * - fsync to ensure data hit disk.
 * - Rename to destination (atomic on POSIX).
 * - Preserves/sets permissions.
 */
class AtomicFileWriter {
public:
    static void write(const std::string& path, const std::string& content, mode_t mode = 0644) {
        std::string temp_path = path + ".tmp." + std::to_string(getpid());
        
        {
            std::ofstream ofs(temp_path, std::ios::binary);
            if (!ofs) {
                throw std::runtime_error("AtomicFileWriter: Could not open temp file " + temp_path);
            }
            ofs.write(content.data(), content.size());
            ofs.flush();
            if (!ofs.good()) {
                throw std::runtime_error("AtomicFileWriter: Failed to write content to " + temp_path);
            }
        }

        // Ensure fsync
        int fd = open(temp_path.c_str(), O_RDWR);
        if (fd == -1) {
            throw std::runtime_error("AtomicFileWriter: Could not re-open temp file for fsync");
        }
        if (fsync(fd) != 0) {
            close(fd);
            throw std::runtime_error("AtomicFileWriter: fsync failed for " + temp_path);
        }
        close(fd);

        // Set permissions
        if (chmod(temp_path.c_str(), mode) != 0) {
            throw std::runtime_error("AtomicFileWriter: chmod failed for " + temp_path);
        }

        // Atomic rename
        if (std::rename(temp_path.c_str(), path.c_str()) != 0) {
            std::filesystem::remove(temp_path);
            throw std::runtime_error("AtomicFileWriter: rename failed from " + temp_path + " to " + path);
        }
    }
};

/**
 * @brief Multi-replace utility with strict validation.
 * 
 * Implements Workstream 11 requirements:
 * - Each replacement must match >= 1 occurrence.
 * - Fails with context if 0 matches found.
 */
class MultiReplace {
public:
    struct Replacement {
        std::string target;
        std::string replacement;
    };

    static std::string apply(const std::string& original, const std::vector<Replacement>& replacements) {
        std::string result = original;
        for (const auto& r : replacements) {
            size_t pos = result.find(r.target);
            if (pos == std::string::npos) {
                throw std::runtime_error("MultiReplace: Target pattern not found: " + r.target);
            }
            
            while (pos != std::string::npos) {
                result.replace(pos, r.target.length(), r.replacement);
                pos = result.find(r.target, pos + r.replacement.length());
            }
        }
        return result;
    }
};

} // namespace utils
} // namespace heidi
