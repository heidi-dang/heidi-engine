## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-05-29 - [Optimized Validation Script and Fixed Telemetry Bug]
**Learning:** Pre-compiling regex patterns at the module level avoids repeated overhead in tight loops. `"".join(text.split())` is a fast alternative to `re.sub` for total whitespace removal. However, "fast-path" guards for security-sensitive logic (like secret detection) must be carefully designed to avoid false negatives; simple keyword-based guards are often too risky for such paths.
**Action:** Prioritize module-level regex pre-compilation for repetitive tasks. Use split/join for simple whitespace removal. Avoid heuristic guards on critical security paths unless they can be proven exhaustive.
