# CI & Release Process

## Continuous Integration
Every PR must pass:
- Unit tests (`pytest`)
- Linting (`ruff`)
- C++ build validation
- Secret scanning

## Release Workflow
1. Freeze branch: `release/vX.Y.Z`.
2. Run full matrix CI.
3. Perform manual smoke tests of dashboard and HTTP server.
4. Tag release:
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin vX.Y.Z
   ```
