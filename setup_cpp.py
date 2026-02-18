from setuptools import setup, Extension
from pybind11.setup_helpers import Pybind11Extension, build_ext

ext_modules = [
    Pybind11Extension(
        "heidi_cpp",
        ["heidi_engine/cpp/heidi_cpp.cpp"],
        # Example: optimize for speed
        cxx_std=11,
    ),
]

setup(
    name="heidi_cpp",
    version="0.1.0",
    author="Heidi Team",
    description="C++ performance optimizations for Heidi Engine",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.7",
)
