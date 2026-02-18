import os
import sys
import shutil
from setuptools import setup

try:
    from pybind11.setup_helpers import Pybind11Extension, build_ext
except ImportError:
    print("[ERROR] pybind11 not found. Please install it with: pip install pybind11")
    sys.exit(1)

# Check for CUDA
cuda_home = os.environ.get("CUDA_HOME") or os.environ.get("CUDA_PATH")
if not cuda_home and os.path.exists("/usr/local/cuda"):
    cuda_home = "/usr/local/cuda"

include_dirs = [
    os.path.abspath("submodules/heidi-kernel/include"),
]
library_dirs = []
libraries = []
macros = []

# Check for zlib
has_zlib = False
if os.name == "nt":
    # On Windows CI, we might need to point to zlib
    # Try to see if it's available in standard paths
    # For now, we'll try to link it, but we'll check if it exists
    # A better way is to use find_library or similar
    # But for robustness, let's check if we can find zlib.h
    if shutil.which("cl.exe"): # Check if we are using MSVC
         # Simple check for zlib.h in include paths? Hard to do without a compiler.
         # Let's assume it's NOT there unless we install it.
         pass

    # We'll try to use zlib if it's explicitly provided or found
    if os.environ.get("ZLIB_ROOT"):
        include_dirs.append(os.path.join(os.environ["ZLIB_ROOT"], "include"))
        library_dirs.append(os.path.join(os.environ["ZLIB_ROOT"], "lib"))
        libraries.append("zlib")
        has_zlib = True
    else:
        # Default attempt
        libraries.append("zlib")
        # We won't set HAS_ZLIB yet, we'll try a small check
        has_zlib = False # Default to false on Windows unless found
else:
    libraries.append("z")
    has_zlib = True

if has_zlib:
    macros.append(("HAS_ZLIB", "1"))

if cuda_home and os.path.exists(os.path.join(cuda_home, "include/cuda_runtime.h")):
    include_dirs.append(os.path.join(cuda_home, "include"))
    library_dirs.append(os.path.join(cuda_home, "lib64"))
    libraries.append("cudart")
    macros.append(("HAS_CUDA", "1"))
    print(f"[INFO] CUDA detected at {cuda_home}")

# Handle C++ standard for MSVC
cxx_std = 23
extra_compile_args = []
if os.name == "nt":
    # If pybind11 fails to map 23, we can help it
    # MSVC uses /std:c++20 or /std:c++latest
    # We'll try to use /std:c++20 as a fallback if 23 is too new for the compiler
    # Actually, heidi-kernel uses C++23 features?
    # Resource governor seems to use pretty standard C++.
    cxx_std = 20 # Use 20 for better compatibility on Windows
    extra_compile_args.append("/EHsc")
    extra_compile_args.append("/bigobj")

ext_modules = [
    Pybind11Extension(
        "heidi_cpp",
        [
            "heidi_engine/cpp/heidi_cpp.cpp",
            "submodules/heidi-kernel/src/governor/resource_governor.cpp"
        ],
        include_dirs=include_dirs,
        library_dirs=library_dirs,
        libraries=libraries if has_zlib else [],
        define_macros=macros,
        cxx_std=cxx_std,
        extra_compile_args=extra_compile_args,
    ),
]

setup(
    name="heidi_cpp",
    version="0.2.0",
    author="Heidi Team",
    description="C++ performance optimizations for Heidi Engine (V2)",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.7",
)
