import time
import re

pattern = r'(?i)(api[_-]?key|apikey|secret[_-]?key)\s*[:=]\s*["\']?[\w\-]{20,}'
compiled = re.compile(pattern)
text = "clean text " * 100

start = time.time()
for _ in range(100000):
    re.search(pattern, text)
print(f"Raw: {time.time() - start:.4f}s")

start = time.time()
for _ in range(100000):
    compiled.search(text)
print(f"Compiled: {time.time() - start:.4f}s")
