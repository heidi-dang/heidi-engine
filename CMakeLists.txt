cmake_minimum_required(VERSION 3.22)
project(heidi-engine VERSION 0.2.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find system libcurl using pkg-config (portable)
find_package(PkgConfig QUIET)
if(PkgConfig_FOUND)
    pkg_check_modules(CURL QUIET IMPORTED_TARGET libcurl)
endif()
# Fallback to find_library
if(NOT CURL_FOUND)
    find_library(CURL_LIBRARY NAMES curl libcurl-4 libcurl4 libcurl.so.4 PATHS /usr/lib/x86_64-linux-gnu /usr/lib /usr/local/lib NO_DEFAULT_PATH)
    if(CURL_LIBRARY)
        set(CURL_FOUND TRUE)
        set(CURL_LIBRARIES ${CURL_LIBRARY})
    endif()
endif()
if(NOT CURL_FOUND)
    message(FATAL_ERROR "libcurl not found. Install libcurl4-openssl-dev or libcurl4-gnutls-dev")
endif()
message(STATUS "Found libcurl: ${CURL_LIBRARIES}")

# Add heidi-kernel as a subdirectory
add_subdirectory(submodules/heidi-kernel)

# Include directories
include_directories(
    heidi_engine/cpp/include
    heidi_engine/cpp/core
    submodules/heidi-kernel/include
    deps/include
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
        z
        ${CURL_LIBRARY}
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
    heidi_engine/cpp/core/provider.cpp
    heidi_engine/cpp/core/mock_provider.cpp
    heidi_engine/cpp/core/async_collector.cpp
    heidi_engine/cpp/core/core.cpp
)

target_include_directories(cpp_core_tests PRIVATE heidi_engine/cpp)
target_link_libraries(cpp_core_tests PRIVATE gtest_main crypto pthread ${CURL_LIBRARY})
add_test(NAME CoreTest COMMAND cpp_core_tests)
