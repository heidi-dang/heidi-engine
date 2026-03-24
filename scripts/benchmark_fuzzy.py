import time
import re

def fuzzy_hash_original(text, n=5):
    text = text.lower()
    text = re.sub(r"\s+", "", text)
    if len(text) < n:
        return text
    # ... (rest of function omitted for brevity, we focus on re.sub)
    return text

def fuzzy_hash_optimized(text, n=5):
    text = text.lower()
    text = "".join(text.split())
    if len(text) < n:
        return text
    return text

test_text = "def hello_world():\n    print('Hello, world!')\n" * 100

start = time.time()
for _ in range(10000):
    fuzzy_hash_original(test_text)
print(f"Original: {time.time() - start:.4f}s")

start = time.time()
for _ in range(10000):
    fuzzy_hash_optimized(test_text)
print(f"Optimized: {time.time() - start:.4f}s")
