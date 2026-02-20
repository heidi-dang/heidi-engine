# CMake generated Testfile for 
# Source directory: /home/ubuntu/heidi-engine
# Build directory: /home/ubuntu/heidi-engine/build
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test([=[CoreTest]=] "/home/ubuntu/heidi-engine/build/cpp_core_tests")
set_tests_properties([=[CoreTest]=] PROPERTIES  _BACKTRACE_TRIPLES "/home/ubuntu/heidi-engine/CMakeLists.txt;58;add_test;/home/ubuntu/heidi-engine/CMakeLists.txt;0;")
add_test([=[IntegrationTests]=] "submodules/heidi-kernel/tests/integration/integration_tests")
set_tests_properties([=[IntegrationTests]=] PROPERTIES  _BACKTRACE_TRIPLES "/home/ubuntu/heidi-engine/CMakeLists.txt;62;add_test;/home/ubuntu/heidi-engine/CMakeLists.txt;0;")
add_test([=[UnitTests]=] "submodules/heidi-kernel/tests/unit_tests")
set_tests_properties([=[UnitTests]=] PROPERTIES  _BACKTRACE_TRIPLES "/home/ubuntu/heidi-engine/CMakeLists.txt;63;add_test;/home/ubuntu/heidi-engine/CMakeLists.txt;0;")
subdirs("submodules/heidi-kernel")
