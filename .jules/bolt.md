## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-04-23 - [Pricing Config Cache and Fast Whitespace Removal]
**Learning:** High-frequency telemetry paths that perform disk I/O for configuration (like pricing) create significant overhead. Additionally, using "".join(text.split()) is consistently ~5.8x faster than re.sub(r"\s+", "", text) for bulk whitespace removal in Python.
**Action:** Use thread-safe TTL caches for configuration files on hot paths and prefer native string methods over regex for simple character/whitespace manipulations.
