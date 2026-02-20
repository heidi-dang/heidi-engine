cmake_minimum_required(VERSION 3.22)
project(heidi-engine VERSION 0.2.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

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
    heidi_engine/cpp/daemon/daemon.cpp
    heidi_engine/cpp/core/core.cpp
    heidi_engine/cpp/core/clock.cpp
    heidi_engine/cpp/core/config.cpp
    heidi_engine/cpp/core/journal_writer.cpp
    heidi_engine/cpp/core/run_id.cpp
    heidi_engine/cpp/core/status_writer.cpp
    heidi_engine/cpp/core/subprocess.cpp
    heidi_engine/cpp/core/mock_provider.cpp
    heidi_engine/cpp/core/async_collector.cpp
)

target_link_libraries(heidid
    PRIVATE
        heidi-ipc
        heidi-metrics
        heidi-kernel-job
        heidi-kernel-governor
        heidi-kernel-lib
        z
        crypto
        pthread
)

# Optional: Build Python extension using CMake if desired, 
# but we'll stick to a standalone binary for now as requested.

# Output binary to bin directory
set_target_properties(heidid PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")

# Add Tests
enable_testing()
# C++ Core Unit Tests
add_executable(cpp_core_tests
    tests/test_cpp_core.cpp
    tests/test_cpp_async.cpp
    heidi_engine/cpp/core/clock.cpp
    heidi_engine/cpp/core/run_id.cpp
    heidi_engine/cpp/core/config.cpp
    heidi_engine/cpp/core/journal_writer.cpp
    heidi_engine/cpp/core/status_writer.cpp
    heidi_engine/cpp/core/subprocess.cpp
    heidi_engine/cpp/core/mock_provider.cpp
    heidi_engine/cpp/core/async_collector.cpp
    heidi_engine/cpp/core/core.cpp
)

target_include_directories(cpp_core_tests PRIVATE heidi_engine/cpp)
target_link_libraries(cpp_core_tests PRIVATE gtest_main crypto pthread)
add_test(NAME CoreTest COMMAND cpp_core_tests)
