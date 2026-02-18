cmake_minimum_required(VERSION 3.22)
project(heidi-engine VERSION 0.2.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find zlib
find_package(ZLIB REQUIRED)

# Add heidi-kernel as a subdirectory
add_subdirectory(submodules/heidi-kernel)

# Include directories
include_directories(
    heidi_engine/cpp/include
    submodules/heidi-kernel/include
)

# Build heidid daemon
add_executable(heidid
    heidi_engine/cpp/daemon/main.cpp
    heidi_engine/cpp/daemon/engine_daemon.cpp
)

target_link_libraries(heidid
    PRIVATE
        heidi-ipc
        heidi-metrics
        heidi-kernel-job
        heidi-kernel-governor
        heidi-kernel-lib
        ZLIB::ZLIB
)

# Optional: Build Python extension using CMake if desired, 
# but we'll stick to a standalone binary for now as requested.

# Output binary to bin directory
set_target_properties(heidid PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")
