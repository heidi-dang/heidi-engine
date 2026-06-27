## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-06-27 - [Parallelized Unit Test Gate and Regex Optimization]
**Learning:** Parallelizing subprocess-heavy tasks with `ThreadPoolExecutor` and pre-compiling regex patterns significantly reduces pipeline duration. Python's `re.finditer` with combined patterns is more efficient than sequential `re.findall` calls for extracting multiple groups.
**Action:** Always look for parallelization opportunities in scripts that execute external processes or heavy I/O. Pre-compile regex at the module level for performance.
