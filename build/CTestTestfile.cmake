# CMake generated Testfile for 
# Source directory: /home/heidi/heidi-engine
# Build directory: /home/heidi/heidi-engine/build
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test([=[CoreTest]=] "/home/heidi/heidi-engine/build/cpp_core_tests")
set_tests_properties([=[CoreTest]=] PROPERTIES  _BACKTRACE_TRIPLES "/home/heidi/heidi-engine/CMakeLists.txt;68;add_test;/home/heidi/heidi-engine/CMakeLists.txt;0;")
subdirs("submodules/heidi-kernel")
