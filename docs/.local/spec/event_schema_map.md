# Heidi Engine Event Schema Mapping

## Overview

In Phase 1, the C++ core will replace the `telemetry.py` event flushing logic with a native C++ `JournalWriter`. To ensure compatibility with the existing dashboard and log viewers, the C++ core **MUST** emit JSON lines structurally identical to the Python implementation.

## Schema Definition (v1.0)

Every event appended to `events.jsonl` must be a single-line JSON object adhering strictly to this schema:

```json
{
  "event_version": "1.0",
  "ts": "2026-02-20T18:32:00.000Z",
  "run_id": "run_20260220_183200",
  "round": 1,
  "stage": "generate",
  "level": "info",
  "event_type": "stage_start",
  "message": "Starting teacher generation",
  "counters_delta": {},
  "usage_delta": {},
  "artifact_paths": [],
  "error": null 
}
```

### Field Constraints

1. **`event_version`**: Must be the literal string `"1.0"`.
2. **`ts`**: ISO8601 UTC timestamp string.
3. **`run_id`**: String matching the current run identifier.
4. **`round`**: Integer `[0, ROUNDS]`. `0` is used for pipeline-level events.
5. **`stage`**: String Enum. Valid values: 
   - `"initializing"`, `"generate"`, `"validate"`, `"test"`, `"train"`, `"eval"`, `"pipeline"`, `"round"`
6. **`level`**: String Enum. Valid values:
   - `"info"`, `"warn"`, `"error"`, `"success"`
7. **`event_type`**: String Enum. Valid values:
   - `"pipeline_start"`, `"pipeline_stop"`, `"pipeline_complete"`, `"pipeline_error"`
   - `"round_start"`, `"stage_start"`, `"stage_end"`, `"stage_skip"`
   - `"train_now_trigger"`, `"train_now_complete"`
8. **`message`**: String (Max 500 characters). Must be scrubbed of ANSI escape codes and secrets.
9. **`counters_delta`**: Optional Key-Value object of integers. E.g. `{"teacher_generated": 50}`
10. **`usage_delta`**: Optional Key-Value object of integers. E.g. `{"input_tokens": 1200}`
11. **`artifact_paths`**: Array of string absolute paths. Length <= 100 chars per path.
12. **`error`**: Optional String (Max 200 chars), present if `level=="error"`.

## Secret Redaction

The C++ `JournalWriter` or the logging pipeline **MUST** run all `message` and `error` strings through a secret redactor matching `telemetry.redact_secrets()` before serializing to JSON.

### Required Regex Patterns to Redact:
- `ghp_[a-zA-Z0-9]{36}` -> `[GITHUB_TOKEN]`
- `sk-[a-zA-Z0-9]{20,}` -> `[OPENAI_KEY]`
- `Bearer\s+[\w\-]{20,}` -> `[BEARER_TOKEN]`

## Hash Chaining (C++ Addition)

To support the zero-trust deliverable, the C++ `JournalWriter` will add **one new field** that Python did not have:

```json
  "prev_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
```
- **`prev_hash`**: The SHA256 hex string of the exact line (including newline) of the previous event. The first event in a run gets the SHA256 of the `run_id`.
