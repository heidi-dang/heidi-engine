## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-20 - [Script Performance and Environment Quirks]
**Learning:** Pre-compiling regex patterns in data-processing scripts (like `02_validate_clean.py`) and replacing expensive regex whitespace removal with `"".join(text.split())` yielded significant measurable speedups (~10-20% overall script time). Also discovered that `os.makedirs('', exist_ok=True)` unexpectedly raises `FileNotFoundError` in this environment, unlike some other Unix-like environments where it might be a no-op.
**Action:** Move regex compilation to module-level globals in scripts and always validate `os.path.dirname(path)` before calling `os.makedirs`.
