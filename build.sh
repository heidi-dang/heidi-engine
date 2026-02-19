#!/bin/bash
# build.sh - Main build script for Heidi Engine
# Builds C++ daemon, Python extension, and installs dependencies
# Usage: ./build.sh [OPTIONS]

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="Heidi Engine"
BUILD_HEIDID=true
BUILD_PYTHON_EXT=true
INSTALL_DEPS=true
RUN_TESTS=false
CLEAN_BUILD=false
VERBOSE=false

# Logging
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

show_help() {
    cat <<EOF
${PROJECT_NAME} Build Script

Usage: ./build.sh [OPTIONS]

Options:
  --heidid-only       Build only the C++ daemon (skip Python extension)
  --python-only       Build only the Python extension (skip C++ daemon)
  --no-deps           Skip installing Python dependencies
  --test              Run tests after building
  --clean             Clean build directories before building
  --verbose           Verbose output
  --help              Show this help message

Examples:
  ./build.sh                    # Full build (daemon + Python ext + deps)
  ./build.sh --heidid-only      # Build only heidid daemon
  ./build.sh --python-only      # Build only Python extension
  ./build.sh --test             # Build and run tests
  ./build.sh --clean            # Clean rebuild everything

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --heidid-only)
            BUILD_PYTHON_EXT=false
            shift
            ;;
        --python-only)
            BUILD_HEIDID=false
            INSTALL_DEPS=false
            shift
            ;;
        --no-deps)
            INSTALL_DEPS=false
            shift
            ;;
        --test)
            RUN_TESTS=true
            shift
            ;;
        --clean)
            CLEAN_BUILD=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
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

# Print banner
print_banner() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║                 ${PROJECT_NAME} Build System                  ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    local missing=()
    
    if ! command_exists python3; then
        missing+=("python3")
    fi
    
    if ! command_exists pip3 && ! command_exists pip; then
        missing+=("pip")
    fi
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing[*]}"
        log_error "Please install Python 3.9+ and pip"
        exit 1
    fi
    
    log_info "Python version: $(python3 --version)"
    
    if command_exists cmake; then
        log_info "CMake version: $(cmake --version | head -1)"
    else
        log_warn "CMake not found - C++ components will not be built"
        BUILD_HEIDID=false
    fi
}

# Install Python dependencies
install_python_deps() {
    if [[ "$INSTALL_DEPS" == false ]]; then
        log_info "Skipping Python dependencies installation (--no-deps)"
        return
    fi
    
    log_step "Installing Python dependencies..."
    
    if [[ -f "requirements.txt" ]]; then
        log_info "Installing from requirements.txt..."
        pip install -r requirements.txt
    elif [[ -f ".local/ml/requirements-ci.txt" ]]; then
        log_info "Installing from requirements-ci.txt..."
        pip install -r .local/ml/requirements-ci.txt
    fi
    
    log_info "Installing Heidi Engine package..."
    pip install -e . 2>&1 | grep -v "already satisfied" || true
    
    log_info "Python dependencies installed"
}

# Build C++ daemon
build_heidid() {
    if [[ "$BUILD_HEIDID" == false ]]; then
        log_info "Skipping heidid build (--python-only or no cmake)"
        return
    fi
    
    log_step "Building heidid C++ daemon..."
    
    local build_args=""
    if [[ "$CLEAN_BUILD" == true ]]; then
        build_args="$build_args --clean"
    fi
    
    if [[ "$VERBOSE" == true ]]; then
        build_args="$build_args --verbose"
    fi
    
    if [[ -f "scripts/build-heidid.sh" ]]; then
        ./scripts/build-heidid.sh $build_args
    else
        log_error "build-heidid.sh not found!"
        exit 1
    fi
    
    log_info "heidid built successfully"
}

# Build Python C++ extension
build_python_extension() {
    if [[ "$BUILD_PYTHON_EXT" == false ]]; then
        log_info "Skipping Python C++ extension build (--heidid-only)"
        return
    fi
    
    log_step "Building Python C++ extension..."
    
    if [[ ! -f "setup_cpp.py" ]]; then
        log_warn "setup_cpp.py not found - skipping Python extension"
        return
    fi
    
    # Clean previous builds if requested
    if [[ "$CLEAN_BUILD" == true ]]; then
        log_info "Cleaning Python extension build..."
        rm -rf build/temp.* build/lib.* *.so 2>/dev/null || true
    fi
    
    # Check for submodules
    if [[ ! -d "submodules/heidi-kernel/.git" ]]; then
        log_info "Initializing git submodules..."
        git submodule update --init --recursive
    fi
    
    log_info "Building extension module..."
    python setup_cpp.py build_ext --inplace
    
    # Find the built extension
    local ext_file=$(find . -name "heidi_cpp*.so" -type f 2>/dev/null | head -1)
    if [[ -n "$ext_file" ]]; then
        log_info "Python extension built: $ext_file"
    else
        log_warn "Python extension file not found after build"
    fi
}

# Run tests
run_tests() {
    if [[ "$RUN_TESTS" == false ]]; then
        return
    fi
    
    log_step "Running tests..."
    
    if command_exists pytest; then
        pytest -v --tb=short
    else
        log_warn "pytest not found - skipping tests"
        log_info "Install with: pip install pytest"
    fi
}

# Print build summary
print_summary() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                    BUILD COMPLETE                          ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    
    if [[ "$BUILD_HEIDID" == true ]]; then
        echo "  ${GREEN}✓${NC} heidid daemon: build/bin/heidid"
        if [[ -f "build/bin/heidid" ]]; then
            ls -lh build/bin/heidid | awk '{print "    Size: " $5 "  Modified: " $6 " " $7 " " $8}'
        fi
    fi
    
    if [[ "$BUILD_PYTHON_EXT" == true ]]; then
        local ext_file=$(find . -name "heidi_cpp*.so" -type f 2>/dev/null | head -1)
        if [[ -n "$ext_file" ]]; then
            echo "  ${GREEN}✓${NC} Python extension: $ext_file"
        fi
    fi
    
    echo ""
    echo "  Usage:"
    echo "    ./build/bin/heidid --help"
    echo "    python -m heidi_engine.dashboard --help"
    echo "    python -m heidi_engine.telemetry status"
    echo ""
    
    if [[ "$RUN_TESTS" == true ]]; then
        echo "  ${GREEN}✓${NC} Tests executed"
    fi
    
    echo ""
    log_info "Build completed successfully!"
}

# Main execution
main() {
    print_banner
    
    cd "$SCRIPT_DIR"
    
    check_prerequisites
    install_python_deps
    build_heidid
    build_python_extension
    run_tests
    print_summary
}

# Run main
main
