import time
import re
import hashlib
from collections import Counter
from typing import Any, Dict, List, Tuple

# Mocking the original functions from scripts/02_validate_clean.py
def detect_secrets_baseline(sample: Dict[str, Any], secret_patterns, secret_check_fields) -> Tuple[bool, List[str]]:
    found_secrets = []
    for field in secret_check_fields:
        if field not in sample:
            continue
        text = str(sample[field])
        for pattern, secret_type in secret_patterns:
            if re.search(pattern, text):
                found_secrets.append(f"{field}:{secret_type}")
    return len(found_secrets) > 0, found_secrets

def fuzzy_hash_baseline(sample: Dict[str, Any], n: int = 5) -> str:
    text = (sample.get("instruction", "") + sample.get("output", "")).lower()
    text = re.sub(r"\s+", "", text)
    if len(text) < n:
        return text
    ngrams = [text[i : i + n] for i in range(len(text) - n + 1)]
    counter = Counter(ngrams)
    fingerprint = "".join(sorted([ng for ng, _ in counter.most_common(10)]))
    return hashlib.sha256(fingerprint.encode()).hexdigest()

# Mocking the original functions from scripts/03_unit_test_gate.py
def extract_python_code_baseline(text: str, code_block_patterns) -> List[str]:
    code_blocks = []
    for pattern in code_block_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        code_blocks.extend(matches)
    python_code = []
    for code in code_blocks:
        if len(code.strip()) < 20:
            continue
        if not any(kw in code for kw in ["def ", "class ", "import ", "return ", "if ", "for ", "while "]):
            continue
        python_code.append(code)
    return python_code

def check_dangerous_code_baseline(code: str, dangerous_patterns) -> Tuple[bool, List[str]]:
    found = []
    for pattern in dangerous_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            found.append(pattern)
    return len(found) > 0, found

# Optimized versions (to be implemented)
def fuzzy_hash_optimized(sample: Dict[str, Any], n: int = 5) -> str:
    text = (sample.get("instruction", "") + sample.get("output", "")).lower()
    text = "".join(text.split()) # Faster than re.sub
    if len(text) < n:
        return text
    ngrams = [text[i : i + n] for i in range(len(text) - n + 1)]
    counter = Counter(ngrams)
    fingerprint = "".join(sorted([ng for ng, _ in counter.most_common(10)]))
    return hashlib.sha256(fingerprint.encode()).hexdigest()

# Setup patterns
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
SECRET_CHECK_FIELDS = ["instruction", "input", "output", "response", "completion"]

CODE_BLOCK_PATTERNS = [
    r"```python\n(.*?)```",
    r"```\n(.*?)```",
    r"`([^`\n]+)`",
]

DANGEROUS_PATTERNS = [
    r"\bimport\s+[^#\n]*\b(os|subprocess|sys|shutil|socket|requests|urllib|pathlib|pickle|pty|code|bdb|pdb|multiprocessing|threading|tempfile|ftplib|smtplib|telnetlib|http|xmlrpc)\b",
    r"\bfrom\s+(os|subprocess|sys|shutil|socket|requests|urllib|pathlib|pickle|pty|code|bdb|pdb|multiprocessing|threading|tempfile|ftplib|smtplib|telnetlib|http|xmlrpc)\b",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"\b__import__\s*\(",
    r"\bgetattr\s*\(",
    r"\bsetattr\s*\(",
    r"\bbreakpoint\s*\(",
    r"\bos\.(system|popen|spawn|remove|unlink|rmdir|mkdir|chmod|chown|kill|exec|fork|pipe)\b",
    r"\bsubprocess\.(run|call|check_call|check_output|Popen)\b",
    r"\bshutil\.(rmtree|move|copy|copy2|copyfile|copymode|copystat|chown)\b",
    r"\bpickle\.(load|loads)\b",
    r"\bshelve\.open\b",
    r"\bopen\s*\([^)]*,\s*(mode\s*=\s*)?['\"][^'\"r]*[wa+x]",
]

COMPILED_SECRET_PATTERNS = [(re.compile(p), t) for p, t in SECRET_PATTERNS]
SECRET_KEYWORDS = [
    "key", "api", "secret", "bearer", "token", "akia", "private", "openssh",
    "mongodb", "postgres", "mysql", "redis", "ghp_", "glpat-", "sk-", "password", "pwd",
    '"', "'"
]

COMPILED_CODE_BLOCK_PATTERNS = [re.compile(p, re.DOTALL) for p in CODE_BLOCK_PATTERNS]
COMPILED_DANGEROUS_PATTERNS = [re.compile(p, re.IGNORECASE) for p in DANGEROUS_PATTERNS]

def detect_secrets_optimized(sample: Dict[str, Any]) -> Tuple[bool, List[str]]:
    found_secrets = []
    for field in SECRET_CHECK_FIELDS:
        if field not in sample:
            continue
        text = str(sample[field])
        if not any(kw in text.lower() for kw in SECRET_KEYWORDS):
            continue
        for pattern, secret_type in COMPILED_SECRET_PATTERNS:
            if pattern.search(text):
                found_secrets.append(f"{field}:{secret_type}")
    return len(found_secrets) > 0, found_secrets

def extract_python_code_optimized(text: str) -> List[str]:
    code_blocks = []
    for pattern in COMPILED_CODE_BLOCK_PATTERNS:
        matches = pattern.findall(text)
        code_blocks.extend(matches)
    python_code = []
    for code in code_blocks:
        if len(code.strip()) < 20:
            continue
        if not any(kw in code for kw in ["def ", "class ", "import ", "return ", "if ", "for ", "while "]):
            continue
        python_code.append(code)
    return python_code

def check_dangerous_code_optimized(code: str) -> Tuple[bool, List[str]]:
    found = []
    for pattern in COMPILED_DANGEROUS_PATTERNS:
        if pattern.search(code):
            found.append(pattern.pattern)
    return len(found) > 0, found

# Benchmark execution
def benchmark():
    clean_sample = {
        "instruction": "Write a function to add two numbers.",
        "input": "",
        "output": "def add(a, b):\n    return a + b",
    }
    problematic_sample = {
        "instruction": "Explain how to use this AWS key: AKIA1234567890ABCDEF",
        "input": "-----BEGIN RSA PRIVATE KEY-----\nABCDEF\n-----END RSA PRIVATE KEY-----",
        "output": "```python\nimport os\nos.system('rm -rf /')\n```",
    }

    iterations = 10000

    print(f"Running benchmarks with {iterations} iterations...")

    # 1. detect_secrets (clean)
    start = time.time()
    for _ in range(iterations):
        detect_secrets_baseline(clean_sample, SECRET_PATTERNS, SECRET_CHECK_FIELDS)
    baseline_time = time.time() - start

    start = time.time()
    for _ in range(iterations):
        detect_secrets_optimized(clean_sample)
    optimized_time = time.time() - start
    print(f"detect_secrets (clean): Baseline={baseline_time:.4f}s, Optimized={optimized_time:.4f}s (Speedup: {baseline_time/optimized_time:.2f}x)")

    # 1.5 detect_secrets (problematic)
    # This verifies correctness - should return True
    found_baseline, _ = detect_secrets_baseline(problematic_sample, SECRET_PATTERNS, SECRET_CHECK_FIELDS)
    found_optimized, _ = detect_secrets_optimized(problematic_sample)
    if found_baseline != found_optimized:
        print(f"[FAIL] Correctness mismatch in detect_secrets! Baseline={found_baseline}, Optimized={found_optimized}")
    else:
        print("[OK] detect_secrets (problematic) correctly caught by optimized version")

    # 2. fuzzy_hash
    start = time.time()
    for _ in range(iterations):
        fuzzy_hash_baseline(clean_sample)
    baseline_time = time.time() - start

    start = time.time()
    for _ in range(iterations):
        fuzzy_hash_optimized(clean_sample)
    optimized_time = time.time() - start
    print(f"fuzzy_hash: Baseline={baseline_time:.4f}s, Optimized={optimized_time:.4f}s (Speedup: {baseline_time/optimized_time:.2f}x)")

    # 3. extract_python_code
    text = "Here is some code:\n" + problematic_sample["output"]
    start = time.time()
    for _ in range(iterations):
        extract_python_code_baseline(text, CODE_BLOCK_PATTERNS)
    baseline_time = time.time() - start

    start = time.time()
    for _ in range(iterations):
        extract_python_code_optimized(text)
    optimized_time = time.time() - start
    print(f"extract_python_code: Baseline={baseline_time:.4f}s, Optimized={optimized_time:.4f}s (Speedup: {baseline_time/optimized_time:.2f}x)")

    # 4. check_dangerous_code
    code = "import os\nos.system('ls')"
    start = time.time()
    for _ in range(iterations):
        check_dangerous_code_baseline(code, DANGEROUS_PATTERNS)
    baseline_time = time.time() - start

    start = time.time()
    for _ in range(iterations):
        check_dangerous_code_optimized(code)
    optimized_time = time.time() - start
    print(f"check_dangerous_code: Baseline={baseline_time:.4f}s, Optimized={optimized_time:.4f}s (Speedup: {baseline_time/optimized_time:.2f}x)")

if __name__ == "__main__":
    benchmark()
