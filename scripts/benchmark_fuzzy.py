import re
import time
import hashlib
from collections import Counter

def old_fuzzy_hash(text, n=5):
    text = text.lower()
    text = re.sub(r"\s+", "", text)
    if len(text) < n:
        return text
    ngrams = [text[i : i + n] for i in range(len(text) - n + 1)]
    counter = Counter(ngrams)
    fingerprint = "".join(sorted([ng for ng, _ in counter.most_common(10)]))
    return hashlib.sha256(fingerprint.encode()).hexdigest()

def new_fuzzy_hash(text, n=5):
    text = text.lower()
    text = "".join(text.split())
    if len(text) < n:
        return text
    ngrams = [text[i : i + n] for i in range(len(text) - n + 1)]
    counter = Counter(ngrams)
    fingerprint = "".join(sorted([ng for ng, _ in counter.most_common(10)]))
    return hashlib.sha256(fingerprint.encode()).hexdigest()

def benchmark():
    text = "  This is a   long string with   lots of   whitespace   " * 100
    iterations = 10000

    start = time.perf_counter()
    for _ in range(iterations):
        old_fuzzy_hash(text)
    end = time.perf_counter()
    print(f"Old fuzzy_hash (regex): {(end - start) * 1000 / iterations:.4f} ms")

    start = time.perf_counter()
    for _ in range(iterations):
        new_fuzzy_hash(text)
    end = time.perf_counter()
    print(f"New fuzzy_hash (split): {(end - start) * 1000 / iterations:.4f} ms")

if __name__ == "__main__":
    benchmark()
