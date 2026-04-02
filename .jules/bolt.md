## 2025-05-22 - Regex Pre-compilation and String Optimization

**Learning:** Combining multiple complex regex patterns into a single "fast-path" indicator regex can improve performance on clean inputs, but risks false negatives if the indicator list is not perfectly in sync with the actual patterns. Simple string operations like `"".join(text.split())` are significantly faster than `re.sub(r"\s+", "", text)` for whitespace removal in Python.

**Action:** Prefer pre-compiling individual regex patterns for a balance of speed and safety. Use `"".join(text.split())` for bulk whitespace removal tasks.
