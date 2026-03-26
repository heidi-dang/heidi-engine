## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Regex Pre-compilation and Pythonic String Operations]
**Learning:** Pre-compiling regex patterns (re.compile) at the module level provides a measurable speedup (10-60%) for hot-path loops in data processing. For simple string operations like whitespace removal, Pythonic idioms like `"".join(text.split())` are significantly faster (up to 6x) than equivalent `re.sub` calls. Additionally, wrapping generated code for execution requires explicit indentation (using `textwrap.indent`) to maintain syntactic correctness.
**Action:** Use pre-compiled regex for high-frequency matching. Favor string methods over regex for simple transformations. Always ensure proper indentation when dynamically generating/wrapping Python code.
