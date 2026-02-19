## 2024-05-22 - [Regex Optimization Patterns]
**Learning:** In Python, combining many regex patterns into one large expression with `|` and using a `sub` callback can be significantly slower (up to 2-3x) than running multiple individual `re.sub` calls, especially if most patterns don't match. The overhead of the callback and the complexity of the combined NFA/DFA state machine outweigh the single-pass benefit for small numbers of patterns.
**Action:** Use fast-path string checks (`"substring" in text`) or a simple keyword-based `re.search` before running expensive redaction/stripping logic.

## 2024-05-22 - [ANSI Stripping Performance]
**Learning:** `ANSI_ESCAPE.sub("", text)` has measurable overhead even if no ANSI codes are present.
**Action:** Always wrap ANSI stripping in a `if "\x1b" in text:` check for a ~90% performance boost in the common case.
