## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Safe Secret Detection Fast-Paths]
**Learning:** Keyword-based fast-paths for secret detection can cause functional regressions if they skip "high-entropy" patterns that don't rely on keywords (e.g. raw hashes/keys).
**Action:** Ensure fast-path regexes for secret detection include a check for long high-entropy character sequences (e.g. `[\w+/]{40,}`) to maintain detection coverage while retaining performance gains.
