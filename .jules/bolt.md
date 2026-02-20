## 2025-01-24 - [Truncation-first Sanitization]
**Learning:** Redacting secrets from large strings (e.g., prompt templates or raw data blobs) before truncating them results in O(N) regex scanning of data that is discarded anyway. Truncating to a safe buffer (e.g., 2x max_length) before redaction can yield a ~40x speedup for large payloads.
**Action:** Always truncate large strings to a reasonable buffer before performing complex regex redaction/scanning.

## 2025-01-24 - [Fast-path Guards for Regex]
**Learning:** Simple string checks (`"\x1b" in text`) or a lightweight "indicators" regex can skip expensive sequential `re.sub` calls. For typical logs, this saves significant CPU by avoiding unnecessary scans for patterns that aren't there.
**Action:** Implement fast-path guards for expensive string processing pipelines.
