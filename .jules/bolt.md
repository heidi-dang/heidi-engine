## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-05-02 - [Batching Event Writes and Fast-Path Whitespace Removal]
**Learning:** `f.writelines()` with a generator is more memory-efficient than `f.write("".join(...))` for batching I/O while still reducing syscall overhead. For string manipulation, `"".join(text.split())` is significantly faster than `re.sub(r"\s+", "", text)`.
**Action:** Use `f.writelines()` for efficient batch writing of log lines and prefer built-in string methods over regex for simple character/whitespace removal.
