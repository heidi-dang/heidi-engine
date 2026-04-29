
import unittest
import os
import sys
import importlib.util

spec = importlib.util.spec_from_file_location("vc", "scripts/02_validate_clean.py")
vc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vc)

class TestValidateCleanBolt(unittest.TestCase):
    def test_detect_secrets_positive(self):
        # Standard keys
        samples = [
            {"instruction": "test", "input": "", "output": "sk-123456789012345678901234567890123456789012345678"},
            {"instruction": "test", "input": "", "output": "ghp_123456789012345678901234567890123456"},
            {"instruction": "test", "input": "", "output": "AKIA1234567890123456"},
            {"instruction": "test", "input": "", "output": "api_key = 'abcdef1234567890abcdef1234567890'"},
        ]
        for s in samples:
            has_secrets, _ = vc.detect_secrets(s)
            self.assertTrue(has_secrets, f"Failed to detect secret in: {s['output']}")

    def test_detect_secrets_negative(self):
        # Clean strings
        samples = [
            {"instruction": "test", "input": "", "output": "This is a normal sentence."},
            {"instruction": "test", "input": "", "output": "The word secret is here but no key."},
            {"instruction": "test", "input": "", "output": "short-key"},
        ]
        for s in samples:
            has_secrets, _ = vc.detect_secrets(s)
            self.assertFalse(has_secrets, f"False positive in: {s['output']}")

    def test_fuzzy_hash_consistency(self):
        s1 = {"instruction": "Hello world", "output": "This is a test."}
        s2 = {"instruction": "HELLO WORLD", "output": "this is a test."}

        h1 = vc.fuzzy_hash(s1)
        h2 = vc.fuzzy_hash(s2)

        self.assertEqual(h1, h2)

    def test_fuzzy_hash_differentiation(self):
        # Need enough difference to affect top 10 ngrams
        s1 = {"instruction": "A" * 100, "output": "B" * 100}
        s2 = {"instruction": "X" * 100, "output": "Y" * 100}

        h1 = vc.fuzzy_hash(s1)
        h2 = vc.fuzzy_hash(s2)

        self.assertNotEqual(h1, h2)

if __name__ == "__main__":
    unittest.main()
