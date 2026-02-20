# Development Guide

## Contribution Rules
- Branch naming: `feat/`, `fix/`, `refactor/`, `chore/`.
- Always rebase on `main` before submitting.
- No direct pushes to `main`.
- Professional tone required (no emojis).

## Testing Requirements
- New features must include unit tests in the `tests/` directory.
- Integration tests are required for changes to the state machine or IPC.
- Run `pytest` and `ruff check .` before every commit.
