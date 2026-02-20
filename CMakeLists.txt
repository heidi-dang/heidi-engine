cmake_minimum_required(VERSION 3.22)
project(heidi-engine VERSION 0.2.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Prefer find_package(CURL) and fall back to pkg-config / find_library
find_package(CURL QUIET)

set(CURL_LIB_TARGET "")
if(TARGET CURL::libcurl)
    set(CURL_LIB_TARGET CURL::libcurl)
    message(STATUS "Using libcurl target: CURL::libcurl")
elseif(CURL_FOUND AND DEFINED CURL_LIBRARY)
    set(CURL_LIB_TARGET ${CURL_LIBRARY})
    message(STATUS "Using libcurl from find_package: ${CURL_LIB_TARGET}")
else()
    find_package(PkgConfig QUIET)
    if(PkgConfig_FOUND)
        pkg_check_modules(PC_CURL libcurl QUIET)
    endif()
    if(DEFINED PC_CURL_LIBRARIES AND PC_CURL_LIBRARIES)
        set(CURL_LIB_TARGET ${PC_CURL_LIBRARIES})
        include_directories(${PC_CURL_INCLUDE_DIRS})
        message(STATUS "Using libcurl from pkg-config: ${CURL_LIB_TARGET}")
    else()
        find_library(CURL_LIB_ARBITRARY NAMES curl libcurl libcurl.so.4 libcurl4 PATHS /usr/lib/x86_64-linux-gnu /usr/lib /usr/local/lib)
        if(CURL_LIB_ARBITRARY)
            set(CURL_LIB_TARGET ${CURL_LIB_ARBITRARY})
            message(STATUS "Using libcurl from find_library: ${CURL_LIB_TARGET}")
        else()
            message(WARNING "libcurl not found. Network providers may fail to link or run.")
        endif()
    endif()
endif()

# Try to locate curl headers if we don't have a CURL:: target or pkg-config info
if(NOT TARGET CURL::libcurl AND NOT DEFINED PC_CURL_INCLUDE_DIRS)
    find_path(CURL_INCLUDE_DIR NAMES curl/curl.h PATHS /usr/include /usr/local/include NO_DEFAULT_PATH)
    if(CURL_INCLUDE_DIR)
        message(STATUS "Found curl headers at: ${CURL_INCLUDE_DIR}")
        include_directories(${CURL_INCLUDE_DIR})
    else()
        message(STATUS "curl headers not found in standard include paths; builds that include <curl/curl.h> may fail")
    endif()
endif()

# Add heidi-kernel as a subdirectory

add_subdirectory(submodules/heidi-kernel)

# Include directories (for sources not in a target yet)
include_directories(
    heidi_engine/cpp/include
    heidi_engine/cpp/core
    submodules/heidi-kernel/include
    deps/include
)

## Create a reusable core library so tests and binaries link against
## a single authoritative set of object files. This prevents symbol
## drift when tests list source files manually.


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
    heidi_engine/cpp/core/manifest.cpp
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
        $<$<BOOL:${CURL_LIB_TARGET}>:${CURL_LIB_TARGET}>
)

# Create a feature gate HEIDI_HAS_CURL only when both library and headers
# are available. This prevents linking against libcurl without headers.
set(HEIDI_HAS_CURL OFF)
if((CURL_LIB_TARGET) AND (CURL_INCLUDE_DIR))
    set(HEIDI_HAS_CURL ON)
endif()

if(HEIDI_HAS_CURL)
    message(STATUS "HEIDI_HAS_CURL=ON (lib + headers present)")
    target_compile_definitions(heidid PRIVATE HAVE_CURL)
    target_include_directories(heidid PRIVATE ${CURL_INCLUDE_DIR})
else()
    message(STATUS "HEIDI_HAS_CURL=OFF (curl library and headers not both present). Using stub transport.")
endif()

# Optional: Build Python extension using CMake if desired, 
# but we'll stick to a standalone binary for now as requested.

# Output binary to bin directory
set_target_properties(heidid PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")

# heidi_core: single static library containing core implementation
add_library(heidi_core STATIC
    heidi_engine/cpp/core/core.cpp
    heidi_engine/cpp/core/clock.cpp
    heidi_engine/cpp/core/config.cpp
    heidi_engine/cpp/core/journal_writer.cpp
    heidi_engine/cpp/core/run_id.cpp
    heidi_engine/cpp/core/status_writer.cpp
    heidi_engine/cpp/core/subprocess.cpp
    heidi_engine/cpp/core/mock_provider.cpp
    heidi_engine/cpp/core/async_collector.cpp
    heidi_engine/cpp/core/manifest.cpp
    heidi_engine/cpp/core/provider.cpp
)

target_include_directories(heidi_core PUBLIC
    heidi_engine/cpp
)

target_link_libraries(heidi_core
    PUBLIC
        heidi-kernel-lib
        heidi-metrics
        heidi-kernel-governor
        heidi-kernel-job
        z
        crypto
        pthread
)

# Propagate HAVE_CURL into heidi_core when available and conditionally
# compile/link the real curl transport. The provider transport files
# are part of heidi_core; we only add HAVE_CURL if headers+lib are present.
if(HEIDI_HAS_CURL)
    target_compile_definitions(heidi_core PUBLIC HAVE_CURL)
    target_include_directories(heidi_core PUBLIC ${CURL_INCLUDE_DIR})
    target_link_libraries(heidi_core PUBLIC ${CURL_LIB_TARGET})
endif()

# Link heidid against heidi_core instead of duplicating sources
target_link_libraries(heidid PRIVATE heidi_core)

# Add Tests
enable_testing()
# C++ Core Unit Tests
add_executable(cpp_core_tests
    tests/test_cpp_core.cpp
    tests/test_cpp_async.cpp
    # Tests should compile only test sources; link core implementation via heidi_core
)

target_include_directories(cpp_core_tests PRIVATE heidi_engine/cpp)
if(HEIDI_HAS_CURL)
    target_compile_definitions(cpp_core_tests PRIVATE HAVE_CURL)
    target_include_directories(cpp_core_tests PRIVATE ${CURL_INCLUDE_DIR})
    target_link_libraries(cpp_core_tests PRIVATE gtest_main heidi_core ${CURL_LIB_TARGET})
else()
    target_link_libraries(cpp_core_tests PRIVATE gtest_main heidi_core)
endif()
add_test(NAME CoreTest COMMAND cpp_core_tests)
