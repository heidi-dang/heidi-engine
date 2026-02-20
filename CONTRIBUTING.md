# Contributing to Heidi Engine

Thank you for your interest in contributing. To maintain production-grade quality, we enforce the following guidelines.

## Branch Hygiene (Zero Chaos Rule)

- No direct pushes to `main`.
- All changes must be submitted via Pull Request.
- Linear history is enforced; use rebase instead of merge commits.
- Required naming convention:
    - `feat/<area>` for new features
    - `fix/<area>` for bug fixes
    - `refactor/<area>` for code refactoring
    - `chore/<area>` for maintenance tasks
    - `release/vX.Y.Z` for releases

## Pull Request Process

1. Sync your branch:
   ```bash
   git fetch origin
   git rebase origin/main
   ```
2. Run tests and linting:
   ```bash
   pytest
   ruff check .
   ```
3. Ensure CI is green before merging.
4. Provide a professional PR description (no emojis).

## Coding Standards

- Follow the existing architectural patterns.
- Ensure all HTTP binds are to `127.0.0.1` only.
- Do not commit plaintext secrets or `.env` files.
- Maintain professional tone in all documentation and comments.

## Security Responsibility

- Every PR must consider security impact.
- Training must be gated behind verification.
- Receipts must be signed and verified.
