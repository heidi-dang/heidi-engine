# Bolt's Journal ⚡

## 2024-05-22 - Combined Regex vs Sequential re.sub
**Learning:** For a small set of secret patterns (~10), using a combined regex (`(P<p0>...)|(P<p1>...)...`) with a replacement callback in Python is surprisingly SLOWER than multiple sequential `re.sub` calls with string replacements. This is because Python's `re.sub` with strings is highly optimized in C, whereas the combined regex with a Python callback incurs significant overhead for every match and the complex branching in the regex engine.

**Action:** Prefer sequential `re.sub` calls with pre-compiled regexes for small pattern sets. Only use combined regexes if the pattern set is very large or if a single-pass scan is strictly required for correctness.

## 2024-05-22 - Sanitization Truncation Order
**Learning:** Logging large payloads (e.g., raw API outputs or large datasets) can create a "performance cliff" if sanitization (secret redaction) is performed on the entire string before truncation. Redacting a 1MB string with 10+ regexes and then truncating to 500 chars is ~1500x slower than truncating first and then redacting the remainder.

**Action:** Always truncate log messages to their maximum allowed length BEFORE performing expensive operations like secret redaction or complex regex scanning.
