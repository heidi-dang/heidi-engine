## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2024-05-15 - [Parallelized and Optimized Unit Test Gate]
**Learning:** Sequential execution of unit tests via subprocesses is a major bottleneck in the pipeline. Parallelizing using `ThreadPoolExecutor` and optimizing regex operations provides a significant speedup (~2.1x on 50 samples, expected to scale with dataset size). Properly indenting injected code using `textwrap.indent` is crucial for correctness when wrapping code blocks in try-except blocks.
**Action:** Use parallel execution for independent sample processing tasks. Always pre-compile regex patterns and use non-capturing groups for better performance and simpler results. Ensure robust path handling with `os.makedirs` by checking for empty directory names.
