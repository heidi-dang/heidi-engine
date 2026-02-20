# CMake generated Testfile for
# Source directory: /app
# Build directory: /app/build
#
# This file includes the relevant testing commands required for
# testing this directory and lists subdirectories to be tested as well.
add_test([=[CoreTest]=] "/app/build/cpp_core_tests")
set_tests_properties([=[CoreTest]=] PROPERTIES  _BACKTRACE_TRIPLES "/app/CMakeLists.txt;68;add_test;/app/CMakeLists.txt;0;")
subdirs("submodules/heidi-kernel")
