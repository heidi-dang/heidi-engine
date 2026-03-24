import time
import re

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

COMPILED_PATTERNS = [re.compile(p) for p, _ in SECRET_PATTERNS]
_SECRET_INDICATORS = re.compile(
    r"ghp_|glpat-|sk-|bearer|api[_-]?key|apikey|secret[_-]?key|AKIA|PRIVATE\s+KEY|OPENSSH|token|mongodb|postgres|mysql|redis|password|pwd",
    re.IGNORECASE,
)

def detect_secrets_original(text):
    for pattern, _ in SECRET_PATTERNS:
        if re.search(pattern, text):
            return True
    return False

def detect_secrets_optimized(text):
    if not _SECRET_INDICATORS.search(text):
        return False
    for pattern in COMPILED_PATTERNS:
        if pattern.search(text):
            return True
    return False

test_text = "This is a clean string without any secrets." * 10

start = time.time()
for _ in range(100000):
    detect_secrets_original(test_text)
print(f"Original Clean: {time.time() - start:.4f}s")

start = time.time()
for _ in range(100000):
    detect_secrets_optimized(test_text)
print(f"Optimized Clean: {time.time() - start:.4f}s")

secret_text = "This string contains an api_key: ghp_123456789012345678901234567890123456"

start = time.time()
for _ in range(100000):
    detect_secrets_original(secret_text)
print(f"Original Secret: {time.time() - start:.4f}s")

start = time.time()
for _ in range(100000):
    detect_secrets_optimized(secret_text)
print(f"Optimized Secret: {time.time() - start:.4f}s")
