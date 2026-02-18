import os
import subprocess
from setuptools import setup, Extension
from pybind11.setup_helpers import Pybind11Extension, build_ext

# Check for CUDA
cuda_home = os.environ.get("CUDA_HOME") or os.environ.get("CUDA_PATH")
if not cuda_home and os.path.exists("/usr/local/cuda"):
    cuda_home = "/usr/local/cuda"

include_dirs = [
    os.path.abspath("submodules/heidi-kernel/include"),
]
library_dirs = []
libraries = []
if os.name != "nt":
    libraries.append("z") # link zlib on non-Windows
macros = []

if cuda_home and os.path.exists(os.path.join(cuda_home, "include/cuda_runtime.h")):
    include_dirs.append(os.path.join(cuda_home, "include"))
    library_dirs.append(os.path.join(cuda_home, "lib64"))
    libraries.append("cudart")
    macros.append(("HAS_CUDA", "1"))
    print(f"[INFO] CUDA detected at {cuda_home}")

ext_modules = [
    Pybind11Extension(
        "heidi_cpp",
        [
            "heidi_engine/cpp/heidi_cpp.cpp",
            "submodules/heidi-kernel/src/governor/resource_governor.cpp"
        ],
        include_dirs=include_dirs,
        library_dirs=library_dirs,
        libraries=libraries,
        define_macros=macros,
        cxx_std=20,
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
