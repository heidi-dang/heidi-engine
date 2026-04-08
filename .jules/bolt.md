## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-04-08 - [Optimized Whitespace Removal and Regex Matching]
**Learning:** `"".join(text.split())` is significantly faster (~6.6x) than `re.sub(r"\s+", "", text)` for removing all whitespace from a string in Python. Additionally, pre-compiling regex patterns outside of hot loops (like `detect_secrets`) yields a measurable (~13%) performance improvement by avoiding redundant recompilation.
**Action:** Prefer native string methods over regex for simple whitespace operations and always pre-compile regex patterns that are used repeatedly in loops.
