## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-24 - [Whitespace Removal and Regex Pre-compilation]
**Learning:** Replacing `re.sub(r"\s+", "", text)` with `"".join(text.split())` for whitespace removal provides a ~6x speedup because `split()` is highly optimized in C. Also, adding a "fast-path" indicator regex can sometimes degrade performance if the overhead of the extra search outweighs the cost of the original loop, especially for small sets of patterns or mostly clean input.
**Action:** Use `"".join(text.split())` for universal whitespace removal. Always benchmark "fast-path" optimizations to ensure they actually provide a win for the expected data distribution.
