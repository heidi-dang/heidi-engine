## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-20 - [Pricing Cache and Telemetry Bug Fix]
**Learning:** Redundant cache checks can lead to maintenance hazards if they fall out of sync or use undefined variables. In `heidi_engine/telemetry.py`, a secondary broken cache check was causing a `NameError` while providing no additional performance benefit over the primary check at the function entry.
**Action:** Use a single, well-placed cache check at the beginning of expensive functions. If multiple checks are needed, ensure they use consistent, validated logic and variables. Implement TTL caching for I/O-bound configuration lookups to significantly reduce latency in hot paths like event emission.
