
import re
import time
import timeit
from collections import Counter
import hashlib

# Mock data
text_with_whitespace = "  This is a   test string with \t a lot of \n whitespace. " * 100
text_with_secrets = "My secret is sk-123456789012345678901234567890123456789012345678"
clean_text = "This is a clean text with no secrets at all." * 10

# Regex patterns from 02_validate_clean.py
SECRET_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey|secret[_-]?key)\s*[:=]\s*["\']?[\w\-]{20,}', "api_key"),
    (r"(?i)bearer\s+[\w\-]{20,}", "bearer_token"),
    (r'(?i)token\s*[:=]\s*["\']?[\w\-]{20,}', "token"),
    (r"AKIA[0-9A-Z]{16}", "aws_access_key"),
    (r'(?i)aws[_-]?secret[_-]?access[_-]?key\s*[:=]\s*["\']?[\w\/+]{40}', "aws_secret"),
    (r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----", "private_key"),
    (r"-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----", "ssh_private_key"),
    (r"(?i)(mongodb|postgres|mysql|redis):\/\/[\w:@\/.-]+", "db_url"),
    (r"(?i)postgresql://[\w:@\/.-]+", "postgres_url"),
    (r"ghp_[a-zA-Z0-9]{36}", "github_token"),
    (r"glpat-[a-zA-Z0-9\-]{20,}", "gitlab_token"),
    (r"sk-[a-zA-Z0-9]{48,}", "openai_key"),
    (r'["\'][\w+\/]{40,}["\']', "high_entropy"),
    (r'(?i)password\s*[:=]\s*["\'][^"\']{8,}["\']', "password"),
    (r'(?i)pwd\s*[:=]\s*["\'][^"\']{8,}["\']', "password"),
]

COMPILED_SECRET_PATTERNS = [(re.compile(p), t) for p, t in SECRET_PATTERNS]

_SECRET_INDICATORS_SIMPLE = re.compile(
    r"ghp_|glpat-|sk-|Bearer|api|secret|AKIA|PRIVATE|OPENSSH|TOKEN|AWS_SECRET|mongodb|postgres|mysql|redis|password|pwd",
    re.IGNORECASE,
)

def original_detect_secrets(text):
    found_secrets = []
    for pattern, secret_type in SECRET_PATTERNS:
        if re.search(pattern, text):
            found_secrets.append(secret_type)
    return found_secrets

def optimized_detect_secrets_compiled_only(text):
    found_secrets = []
    for pattern, secret_type in COMPILED_SECRET_PATTERNS:
        if pattern.search(text):
            found_secrets.append(secret_type)
    return found_secrets

def optimized_detect_secrets_with_fastpath(text):
    if not _SECRET_INDICATORS_SIMPLE.search(text):
        return []
    found_secrets = []
    for pattern, secret_type in COMPILED_SECRET_PATTERNS:
        if pattern.search(text):
            found_secrets.append(secret_type)
    return found_secrets

def original_whitespace_removal(text):
    return re.sub(r"\s+", "", text)

def optimized_whitespace_removal(text):
    return "".join(text.split())

def benchmark():
    print("--- Whitespace Removal Benchmark ---")
    n = 10000
    t1 = timeit.timeit(lambda: original_whitespace_removal(text_with_whitespace), number=n)
    t2 = timeit.timeit(lambda: optimized_whitespace_removal(text_with_whitespace), number=n)
    print(f"Original: {t1:.4f}s")
    print(f"Optimized: {t2:.4f}s")
    print(f"Speedup: {t1/t2:.2f}x")

    print("\n--- Secret Detection Benchmark (Clean Text) ---")
    n = 10000
    t1 = timeit.timeit(lambda: original_detect_secrets(clean_text), number=n)
    t2 = timeit.timeit(lambda: optimized_detect_secrets_compiled_only(clean_text), number=n)
    t3 = timeit.timeit(lambda: optimized_detect_secrets_with_fastpath(clean_text), number=n)
    print(f"Original: {t1:.4f}s")
    print(f"Compiled only: {t2:.4f}s")
    print(f"With fastpath: {t3:.4f}s")
    print(f"Speedup (Compiled only vs Original): {t1/t2:.2f}x")
    print(f"Speedup (Fastpath vs Original): {t1/t3:.2f}x")

    print("\n--- Secret Detection Benchmark (Text with Secret) ---")
    n = 10000
    t1 = timeit.timeit(lambda: original_detect_secrets(text_with_secrets), number=n)
    t2 = timeit.timeit(lambda: optimized_detect_secrets_compiled_only(text_with_secrets), number=n)
    t3 = timeit.timeit(lambda: optimized_detect_secrets_with_fastpath(text_with_secrets), number=n)
    print(f"Original: {t1:.4f}s")
    print(f"Compiled only: {t2:.4f}s")
    print(f"With fastpath: {t3:.4f}s")
    print(f"Speedup (Compiled only vs Original): {t1/t2:.2f}x")
    print(f"Speedup (Fastpath vs Original): {t1/t3:.2f}x")

if __name__ == "__main__":
    benchmark()
