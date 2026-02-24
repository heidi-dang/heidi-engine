# AGENTS.md (instructions for coding agents)

Heidi Engine is primarily a Python package (`heidi_engine/`) with:
- CLI scripts in `scripts/`
- pytest suite in `tests/`
- optional C++ (daemon + Python extension) in `heidi_engine/cpp/`
- optional ML tooling in `.local/ml/`

Keep diffs small and avoid generated outputs.

## Don’t edit / don’t commit

Skip machine-local or huge dirs:
`autotrain_repos/`, `.venv/`/`venv/`, `.local/ml/data/`, `.local/ml/runs/`,
`.pytest_cache/`, `.ruff_cache/`, `__pycache__/`, `build/`, `*.so`.

When searching, prefer `heidi_engine/`, `scripts/`, `tests/`, `docs/`.

## Setup

Python: `>=3.9` (source of truth: `pyproject.toml`; some docs mention 3.8).

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -U pip
python3 -m pip install -e ".[dev]"
```

Optional extras:
- HTTP: `python3 -m pip install -e ".[http]"`
- ML (heavy): see `.local/ml/requirements-*.txt`

## Lint

Ruff config (in `pyproject.toml`): line length `100`, target `py39`, rules `E,F,W,I`, ignore `E501`.

```bash
ruff check heidi_engine scripts
ruff check --fix heidi_engine scripts
```

Note: `tool.ruff.exclude` includes `tests/`; run `ruff check tests` explicitly if needed.

## Tests

```bash
pytest -v
pytest -v tests/test_openhei_teacher_parse.py
pytest -v tests/test_openhei_teacher_parse.py::test_parse_openhei_jsonl_events_fails_closed_on_error_event
pytest -v -k openhei
```

Many tests skip unless optional components/toolchains exist (`heidi_cpp`, `g++`, `node`, `go`).

## Common commands

Sanity checks:

```bash
python3 -m compileall -q .
python3 -m heidi_engine.dashboard --help
python3 -m heidi_engine.http --help
python3 -m heidi_engine.telemetry status --json
./scripts/loop.sh --help
python3 scripts/menu.py --help
autotrain-dashboard --help
autotrain-serve --help
heidi-telemetry status --json
```

Useful env vars (selected):
- `RUN_ID`: current run identifier (telemetry/state)
- `AUTOTRAIN_DIR`: run/output root (defaults to `~/.local/heidi-engine`)
- `HEIDI_TELEMETRY=0`: disable telemetry emission in scripts that support it
- `OPENHEI_ATTACH`, `OPENHEI_AGENT`, `OPENHEI_CLI`: OpenHei teacher/attach controls

Note: some scripts/docs mention `~/.local/heidi_engine` (underscore); canonical path is `~/.local/heidi-engine`.

## Build (optional C++)

Python extension (`heidi_cpp`):

```bash
python3 -m pip install -U pybind11
python3 setup_cpp.py build_ext --inplace
```

Daemon + C++ unit tests:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j"$(nproc)"
./build/cpp_core_tests
./build/bin/heidid --help
```

Full local gate: `./scripts/ci_gate.sh` (compileall + CMake + gtests + selected pytest).

## ML smoke (optional)

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -U pip
python3 -m pip install -r .local/ml/requirements-ci.txt
python3 -m pip install -e .
.local/ml/scripts/prepare_data.sh .local/ml/data/raw_sample.jsonl
.local/ml/scripts/train_adapter.sh --smoke-cpu --train-steps 2 --train .local/ml/data/train/train.jsonl --eval .local/ml/data/eval/val.jsonl
python3 .local/ml/scripts/redaction_check.py --file .local/ml/data/train/train.jsonl --file .local/ml/data/eval/val.jsonl
```

Bootstrap helper: `.local/ml/scripts/setup_python_env.sh`.

## Repo hygiene / security (CI-enforced)

From `.github/workflows/repo-hygiene.yml`:
- Never commit virtualenv artifacts (`.venv/`, `site-packages/`, `*.dist-info/`).
- Never introduce hidden/bidi Unicode control characters.
- Never introduce secret-like tokens in `scripts/` (GitHub/AWS/private keys/Slack).

Operational guidance:
- Redact subprocess output before logging (`heidi_engine.telemetry.redact_secrets`).
- Enforce path containment for user-supplied paths (`heidi_engine/utils/security_util.py`).

## Code style

Imports:
- Keep imports explicit; avoid `from x import *`.
- Group stdlib / third-party / local; let Ruff (`I`) sort.

Formatting:
- Keep new code ~<= 100 cols; wrap docstrings reasonably.

Types:
- Type public APIs and non-trivial helpers.
- File-by-file style varies (`typing.List` vs `list[str]`); match the file.
- Keep `from __future__ import annotations` first when used.

Naming:
- `snake_case` for modules/functions/vars; `PascalCase` for classes; `UPPER_SNAKE_CASE` for constants.
- Custom exceptions should be `SomethingError` and usually inherit `RuntimeError`.

Error handling:
- Prefer fail-fast/fail-closed for contracts (e.g. strict JSONL parsing).
- Raise actionable errors; don’t silently swallow exceptions.
- Optional deps: `try/except ImportError` with clear fallbacks.

Testing:
- Use `pytest.importorskip` for optional modules and `pytest.mark.skipif` for toolchain gates.
- Gate integration tests via env vars (example: `OPENHEI_INTEGRATION=1`).

## Cursor / Copilot rules

No Cursor rules found (`.cursor/rules/` or `.cursorrules`).
No Copilot instructions found (`.github/copilot-instructions.md`).
