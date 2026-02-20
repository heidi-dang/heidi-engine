# Runtime Modes

Heidi Engine supports several operational modes to accommodate different workflows.

## Collect Mode
In this mode, the engine focus only on data collection and validation.
- Triggered by: `python -m heidi_engine.collect --mode collect`
- Behavior: Generates and validates samples, then waits.
- Use Case: Overnight data accumulation without immediate training costs.

## Train Mode (Full Mode)
The complete autonomous loop.
- Triggered by: `python -m heidi_engine.collect --mode full`
- Behavior: Collects, validates, trains, evaluates, and repeats.

## Debug/Mock Mode
Used for system testing without calling expensive LLM APIs.
- Triggered by: Setting `HEIDI_MOCK_SUBPROCESSES=1` environment variable.

## Production Gating
Training is only allowed if the dataset passes all validation checks and provenance is verified.
