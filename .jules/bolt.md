## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-20 - [Pre-compiling Code Block and Security Regexes in Unit Test Gate]
**Learning:** In security and validation gates (`03_unit_test_gate.py`), pre-compiling pattern sets (`CODE_BLOCK_PATTERNS`, `DANGEROUS_PATTERNS`) at the module level avoids compiling dozens of regexes per sample. A fast-path backtick guard (`if "`" not in text: return []`) skips regex evaluation entirely for text without code blocks, while full pre-compiled regex pattern matching ensures complete safety without false negatives.
**Action:** Always pre-compile static regex arrays at the module level in loop-heavy validation scripts and pair them with simple string guards for non-matching payloads.
