# Heidi Engine C++ Rewrite: Phases 1 to 4 Architecture

This document outlines the architectural changes and implementations completed during the first four phases of converting the Heidi Engine from Python to a native C++ core.

## Phase 1: C++ Core Skeleton and Journaling
**Objective:** Establish the foundational C++ types and logging mechanics that the Python orchestrator can bind to.

- **`Config`**: Replaced dynamic Python dictionary configs with a strongly typed `Config` struct loaded via environment variables (e.g., `HEIDI_MOCK_SUBPROCESSES`).
- **`Clock` & `MockClock`**: Abstracted time generation to support strictly deterministic tests and reproducible ISO8601 timestamps.
- **`RunId`**: Unified the execution ID generation (`run_YYYYMMDD_HHMMSS`) in C++.
- **`JournalWriter`**: Centralized all event logging. Enforces our strict JSONL event schema and implements SHA-256 cryptographic hashing to chain events securely, ensuring log integrity.
- **`StatusWriter`**: Handles atomic temporary file swaps (`state.json.tmp` -> `state.json`) to prevent the dashboard from reading half-written states.

## Phase 2: Porting the Loop State Machine
**Objective:** Move the orchestration logic out of the Python `LoopRunner` and into the C++ `Core`.

- **`Core` Engine**: Created the `heidi::core::Core` class acting as the master state machine. It manages the `IDLE` -> `COLLECTING` -> `VALIDATING` -> `TESTING` -> `FINALIZING` -> `EVALUATING` transitions natively.
- **Subprocess Management**: Built a C++ `Subprocess::execute` utility using `fork`/`execvp`/`poll` to launch the heavy Python scripts (like QLoRA training) and capture stdout/err robustly.
- **Fail-Closed Security**: The C++ core strictly catches sub-script failures and halts in an `ERROR` state, preventing cascading failures.
- **Python Bindings (`pybind11`)**: Exposed `heidi_cpp.Core` to Python, allowing the legacy test suites to parameterize and run against the C++ engine flawlessly.

## Phase 3: Provider Abstraction and Async I/O
**Objective:** Implement native C++ concurrency to handle parallel LLM request generation without blocking the Global Interpreter Lock (GIL).

- **`MockProvider`**: Built a lightweight mock inference generator simulating a 100ms LLM response latency.
- **`AsyncCollector`**: Replaced Python synchronous loops with `std::async` and `std::future` to dispatch and collect multiple provider requests on separate native threads. Test integration confirmed 10 requests completed concurrently in ~120ms rather than 1000ms.

## Phase 4: Daemonization and Dashboard API
**Objective:** Detach the C++ core into a standalone binary capable of running headlessly and serving requests via HTTP.

- **`cpp-httplib`**: Embedded a lightweight, header-only C++ HTTP server.
- **`Daemon`**: Built `heidi::daemon::Daemon` which wraps the `Core` and starts an asynchronous C++ engine `std::thread` executing `Core::tick()`.
- **Standalone `heidid` Executable**: Created `main.cpp` providing a robust POSIX double-fork `daemonize()` routine to run the engine in the background indefinitely.
- **REST Endpoints**: Exposes `GET /api/v1/status` (live state fetching) and `POST /api/v1/action/train_now` (interrupt triggers), completely bypassing Python for status resolution.

## Next Steps
With the core state machine natively isolated, daemonized, and running true multi-threading for generation, **Phase 5** will focus on hardening the subprocess bounds (timeouts/SIGKILL) and wiring natively harvested telemetry metrics into the event timeline.
