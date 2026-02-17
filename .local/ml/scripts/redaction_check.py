#!/usr/bin/env python3
"""
Simple redaction/secret scanner for JSONL datasets.
Exits non-zero if any potential secret is found.
"""
import re
import json
import argparse
import sys
from pathlib import Path

PATTERNS = [
    (re.compile(r'ghp_[A-Za-z0-9]{36}'), "github_token_ghp"),
    (re.compile(r'github_pat_[A-Za-z0-9_]{20,}'), "github_pat"),
    (re.compile(r'sk-[A-Za-z0-9]{48,}'), "openai_key"),
    (re.compile(r'glpat-[A-Za-z0-9\-]{20,}'), "gitlab_token"),
    (re.compile(r'AKIA[0-9A-Z]{16}'), "aws_access_key"),
    (re.compile(r'-----BEGIN (RSA )?PRIVATE KEY-----'), "private_key"),
    (re.compile(r'-----BEGIN OPENSSH PRIVATE KEY-----'), "ssh_private_key"),
    (re.compile(r'[_A-Z0-9]+_TOKEN'), "env_token_like"),
    (re.compile(r'[_A-Z0-9]+_KEY'), "env_key_like"),
    (re.compile(r'(?i)password\s*[:=]\s*[^\s]{8,}'), "password_like"),
    (re.compile(r'["\'][A-Za-z0-9+/]{40,}["\']'), "high_entropy_string"),
]

CHECK_FIELDS = ["instruction", "input", "output", "response", "completion"]


def scan_file(path: str) -> int:
    p = Path(path)
    if not p.exists():
        print(f"File not found: {p}", file=sys.stderr)
        return 1

    issues = []
    with p.open() as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            for field in CHECK_FIELDS:
                if field not in obj:
                    continue
                text = str(obj[field])
                for pat, name in PATTERNS:
                    if pat.search(text):
                        issues.append((lineno, field, name, text[:200]))

    if issues:
        print(f"Found {len(issues)} potential secret matches in {p}:")
        for lineno, field, name, snippet in issues[:100]:
            print(f"  line {lineno}: field={field} type={name} snippet={snippet!r}")
        return 2

    print(f"No secrets detected in {p}")
    return 0


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--file", "-f", action="append", required=True, help="JSONL file to scan (can specify multiple)")
    return p.parse_args()


def main():
    args = parse_args()
    exit_code = 0
    for fp in args.file:
        rc = scan_file(fp)
        if rc != 0:
            exit_code = rc
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
