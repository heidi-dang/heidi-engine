#!/bin/bash
# build-heidid.sh - Cross-platform build script for heidid C++ daemon
# Usage: ./scripts/build-heidid.sh [OPTIONS]
# Options:
#   --clean           Clean build directory before building
#   --release         Build in Release mode (default)
#   --debug           Build in Debug mode
#   --install         Install binary to /usr/local/bin (requires sudo)
#   --jobs N          Number of parallel build jobs (default: auto)
#   --help            Show this help message

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BUILD_TYPE="Release"
CLEAN_BUILD=false
INSTALL_BINARY=false
JOBS=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build"

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

OS=$(detect_os)
log_info "Detected OS: $OS"

# Show help
show_help() {
    cat <<EOF
build-heidid.sh - Cross-platform build script for heidid C++ daemon

Usage: $0 [OPTIONS]

Options:
  --clean           Clean build directory before building
  --release         Build in Release mode (default)
  --debug           Build in Debug mode
  --install         Install binary to /usr/local/bin (requires sudo)
  --jobs N          Number of parallel build jobs (default: auto-detected: $JOBS)
  --help            Show this help message

Examples:
  $0                    # Build in release mode
  $0 --clean            # Clean and rebuild
  $0 --debug            # Build in debug mode
  $0 --install          # Build and install to /usr/local/bin
  $0 --jobs 8           # Use 8 parallel jobs

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN_BUILD=true
            shift
            ;;
        --release)
            BUILD_TYPE="Release"
            shift
            ;;
        --debug)
            BUILD_TYPE="Debug"
            shift
            ;;
        --install)
            INSTALL_BINARY=true
            shift
            ;;
        --jobs)
            JOBS="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install dependencies for Linux
install_deps_linux() {
    log_info "Installing dependencies for Linux..."
    
    if command_exists apt-get; then
        # Debian/Ubuntu
        log_info "Detected Debian/Ubuntu system"
        sudo apt-get update
        sudo apt-get install -y \
            build-essential \
            cmake \
            git \
            zlib1g-dev \
            libstdc++-13-dev \
            g++-13
    elif command_exists yum; then
        # RHEL/CentOS/Fedora
        log_info "Detected RHEL/CentOS/Fedora system"
        sudo yum groupinstall -y "Development Tools"
        sudo yum install -y \
            cmake3 \
            git \
            zlib-devel \
            libstdc++-devel \
            gcc-c++
    elif command_exists pacman; then
        # Arch Linux
        log_info "Detected Arch Linux system"
        sudo pacman -S --needed --noconfirm \
            base-devel \
            cmake \
            git \
            zlib
    elif command_exists zypper; then
        # openSUSE
        log_info "Detected openSUSE system"
        sudo zypper install -y \
            patterns-devel-base-devel_basis \
            cmake \
            git \
            zlib-devel \
            gcc-c++
    else
        log_error "Unsupported Linux distribution. Please install manually:"
        log_error "  - cmake (>= 3.22)"
        log_error "  - g++ (>= 13) or clang++ (>= 16) with C++23 support"
        log_error "  - git"
        log_error "  - zlib-dev"
        exit 1
    fi
}

# Install dependencies for macOS
install_deps_macos() {
    log_info "Installing dependencies for macOS..."
    
    if ! command_exists brew; then
        log_info "Homebrew not found. Installing..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    brew install \
        cmake \
        git \
        zlib
    
    # Ensure Xcode Command Line Tools are installed
    if ! xcode-select -p >/dev/null 2>&1; then
        log_info "Installing Xcode Command Line Tools..."
        xcode-select --install
    fi
}

# Install dependencies for Windows (MSYS2/MinGW)
install_deps_windows() {
    log_info "Installing dependencies for Windows (MSYS2)..."
    
    if command_exists pacman; then
        # MSYS2/MinGW environment
        pacman -S --needed --noconfirm \
            mingw-w64-x86_64-gcc \
            mingw-w64-x86_64-cmake \
            mingw-w64-x86_64-zlib \
            git \
            make
    else
        log_error "Please install MSYS2 from https://www.msys2.org/"
        log_error "Then run this script from the MSYS2 terminal"
        exit 1
    fi
}

# Main installation function
install_dependencies() {
    log_info "Checking and installing dependencies..."
    
    case $OS in
        linux)
            install_deps_linux
            ;;
        macos)
            install_deps_macos
            ;;
        windows)
            install_deps_windows
            ;;
        *)
            log_warn "Unknown OS. Assuming dependencies are already installed."
            log_warn "Required: cmake (>=3.22), C++23 compiler (g++>=13 or clang++>=16), git, zlib"
            ;;
    esac
}

# Check minimum versions
check_versions() {
    log_info "Checking tool versions..."
    
    # Check CMake
    if command_exists cmake; then
        CMAKE_VERSION=$(cmake --version | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        log_info "CMake version: $CMAKE_VERSION"
        if [[ $(printf '%s\n' "3.22" "$CMAKE_VERSION" | sort -V | head -n1) != "3.22" ]]; then
            log_error "CMake >= 3.22 required, found $CMAKE_VERSION"
            exit 1
        fi
    else
        log_error "CMake not found"
        exit 1
    fi
    
    # Check compiler
    if command_exists g++; then
        CXX_COMPILER="g++"
        CXX_VERSION=$(g++ --version | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        log_info "g++ version: $CXX_VERSION"
    elif command_exists clang++; then
        CXX_COMPILER="clang++"
        CXX_VERSION=$(clang++ --version | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        log_info "clang++ version: $CXX_VERSION"
    else
        log_error "No C++ compiler found (need g++ >= 13 or clang++ >= 16)"
        exit 1
    fi
    
    # Check Git
    if command_exists git; then
        GIT_VERSION=$(git --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        log_info "Git version: $GIT_VERSION"
    else
        log_error "Git not found"
        exit 1
    fi
}

# Initialize git submodules
init_submodules() {
    log_info "Initializing git submodules..."
    cd "${PROJECT_ROOT}"
    
    if [[ -d "submodules/heidi-kernel/.git" ]]; then
        log_info "Submodules already initialized"
    else
        git submodule update --init --recursive
    fi
}

# Build the project
build_project() {
    log_info "Building heidid in ${BUILD_TYPE} mode with ${JOBS} parallel jobs..."
    
    # Clean if requested
    if [[ "$CLEAN_BUILD" == true ]]; then
        log_info "Cleaning build directory..."
        rm -rf "${BUILD_DIR}"
    fi
    
    # Create build directory
    mkdir -p "${BUILD_DIR}"
    cd "${BUILD_DIR}"
    
    # Configure with CMake
    log_info "Configuring with CMake..."
    cmake .. \
        -DCMAKE_BUILD_TYPE="${BUILD_TYPE}" \
        -DCMAKE_CXX_STANDARD=23 \
        -DCMAKE_CXX_STANDARD_REQUIRED=ON
    
    # Build
    log_info "Compiling..."
    make -j"${JOBS}"
    
    # Check if binary was created
    if [[ -f "bin/heidid" ]]; then
        log_info "Build successful!"
        log_info "Binary location: ${BUILD_DIR}/bin/heidid"
        ls -lh "bin/heidid"
        
        # Test binary
        log_info "Testing binary..."
        ./bin/heidid --help
    else
        log_error "Build failed - binary not found"
        exit 1
    fi
}

# Install binary
install_binary() {
    if [[ "$INSTALL_BINARY" == true ]]; then
        log_info "Installing heidid to /usr/local/bin..."
        sudo cp "${BUILD_DIR}/bin/heidid" /usr/local/bin/heidid
        sudo chmod +x /usr/local/bin/heidid
        log_info "Installation complete. You can now run: heidid --help"
        
        # Verify installation
        if command_exists heidid; then
            log_info "heidid is now in PATH"
            heidid --help
        else
            log_warn "heidid installed but not found in PATH. Try: /usr/local/bin/heidid --help"
        fi
    fi
}

# Print summary
print_summary() {
    echo ""
    log_info "Build Summary:"
    echo "  OS:             $OS"
    echo "  Build Type:     $BUILD_TYPE"
    echo "  Build Directory: ${BUILD_DIR}"
    echo "  Binary:         ${BUILD_DIR}/bin/heidid"
    
    if [[ "$INSTALL_BINARY" == true ]]; then
        echo "  Installed to:   /usr/local/bin/heidid"
    fi
    
    echo ""
    log_info "Usage:"
    echo "  ${BUILD_DIR}/bin/heidid --help"
    echo "  ${BUILD_DIR}/bin/heidid --config engine_config.yaml"
    
    if [[ "$OS" == "linux" ]]; then
        echo ""
        log_info "Systemd service setup:"
        echo "  sudo cp scripts/heidid.service /etc/systemd/system/"
        echo "  sudo systemctl daemon-reload"
        echo "  sudo systemctl enable heidid"
        echo "  sudo systemctl start heidid"
    fi
}

# Main execution
main() {
    log_info "Building heidid C++ daemon..."
    log_info "Project root: ${PROJECT_ROOT}"
    
    # Install dependencies
    install_dependencies
    
    # Check versions
    check_versions
    
    # Initialize submodules
    init_submodules
    
    # Build project
    build_project
    
    # Install if requested
    install_binary
    
    # Print summary
    print_summary
    
    log_info "Build completed successfully!"
}

# Run main
main
