## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Path Object Overhead in Hot Paths]
**Learning:** On performance-critical paths in Python, constructing `Path` objects and calling `.absolute()` (or even `.exists()`) triggers significant syscall overhead when done thousands of times. Using environment variables or pre-computed strings for cache keys is noticeably faster.
**Action:** Use string-based cache keys derived from environment variables or global IDs instead of performing filesystem path resolutions on every call in high-frequency functions.
