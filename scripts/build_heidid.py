#!/usr/bin/env python3
import argparse
import os
import platform
import shutil
import subprocess
import sys


def log_info(msg):
    print(f"\033[0;32m[INFO]\033[0m {msg}")

def log_error(msg):
    print(f"\033[0;31m[ERROR]\033[0m {msg}")

def log_warn(msg):
    print(f"\033[1;33m[WARN]\033[0m {msg}")

def run_command(cmd, cwd=None):
    log_info(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError as e:
        log_error(f"Command failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        log_error(f"Command not found: {cmd[0]}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Cross-platform build script for heidid C++ daemon")
    parser.add_argument("--clean", action="store_true", help="Clean build directory before building")
    parser.add_argument("--debug", action="store_true", help="Build in Debug mode")
    parser.add_argument("--jobs", type=int, default=os.cpu_count(), help="Number of parallel build jobs")
    parser.add_argument("--install", action="store_true", help="Install binary (requires appropriate permissions)")
    args = parser.parse_args()

    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    build_dir = os.path.join(project_root, "build")

    build_type = "Debug" if args.debug else "Release"

    log_info(f"Starting heidid build on {platform.system()}...")
    log_info(f"Project root: {project_root}")

    # Check for CMake
    try:
        subprocess.run(["cmake", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        log_error("CMake not found. Please install CMake (>= 3.22).")
        sys.exit(1)

    # Clean if requested
    if args.clean and os.path.exists(build_dir):
        log_info(f"Cleaning build directory: {build_dir}")
        shutil.rmtree(build_dir)

    # Create build directory
    os.makedirs(build_dir, exist_ok=True)

    # Configure
    log_info(f"Configuring with CMake ({build_type})...")

    # Downgrade C++ standard on Windows for better compatibility
    cxx_std = "23"
    if platform.system() == "Windows":
        cxx_std = "20"

    cmake_configure = [
        "cmake",
        "-S", project_root,
        "-B", build_dir,
        f"-DCMAKE_BUILD_TYPE={build_type}",
        f"-DCMAKE_CXX_STANDARD={cxx_std}",
        "-DCMAKE_CXX_STANDARD_REQUIRED=ON"
    ]

    # On Windows, we might need to specify the architecture
    if platform.system() == "Windows":
        # Check if using MSVC
        cmake_configure.extend(["-A", "x64"])

    run_command(cmake_configure)

    # Build
    log_info(f"Compiling with {args.jobs} jobs...")
    cmake_build = [
        "cmake",
        "--build", build_dir,
        "--config", build_type,
        "-j", str(args.jobs)
    ]
    run_command(cmake_build)

    # Locate binary
    bin_ext = ".exe" if platform.system() == "Windows" else ""
    bin_name = f"heidid{bin_ext}"

    # Potential locations for the binary
    # 1. Standard bin directory (if RUNTIME_OUTPUT_DIRECTORY is set correctly)
    # 2. Config-specific subdirectory (common with MSVC)
    possible_paths = [
        os.path.join(build_dir, "bin", bin_name),
        os.path.join(build_dir, build_type, "bin", bin_name),
        os.path.join(build_dir, "bin", build_type, bin_name),
    ]

    found_bin = None
    for p in possible_paths:
        if os.path.exists(p):
            found_bin = p
            break

    if found_bin:
        log_info(f"Build successful! Binary location: {found_bin}")

        if args.install:
            log_info("Installing binary...")
            install_dest = "/usr/local/bin" if platform.system() != "Windows" else "C:\\Program Files\\heidid"
            try:
                os.makedirs(install_dest, exist_ok=True)
                shutil.copy2(found_bin, os.path.join(install_dest, bin_name))
                log_info(f"Installed to {os.path.join(install_dest, bin_name)}")
            except PermissionError:
                log_error(f"Permission denied when installing to {install_dest}. Try running with sudo/administrator.")
    else:
        log_error("Build finished but heidid binary not found in expected locations.")
        # List files in build/bin to help debugging
        bin_dir = os.path.join(build_dir, "bin")
        if os.path.exists(bin_dir):
            log_info(f"Contents of {bin_dir}: {os.listdir(bin_dir)}")
        sys.exit(1)

    log_info("Build completed successfully!")

if __name__ == "__main__":
    main()
