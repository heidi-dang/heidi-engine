# Sentinel Journal

## 2024-05-24 - Environment Leak and Weak Filtering in Unit Test Gate
**Vulnerability:** The unit test gate executes model-generated code while passing the full environment (including API keys) and uses weak regex filters for dangerous imports.
**Learning:** Model-generated code execution is a high-risk activity that requires strict environment isolation and robust input validation.
**Prevention:** Always use a clean environment for subprocess execution of untrusted code and use comprehensive patterns or AST analysis for filtering.
