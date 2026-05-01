import unittest
import re
import sys
import os
import importlib.util

# Load the module
spec = importlib.util.spec_from_file_location("validate_clean", "scripts/02_validate_clean.py")
vc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vc)

class TestBoltOptimizations(unittest.TestCase):
    def test_detect_secrets_high_entropy(self):
        # This string should be caught by high_entropy pattern
        high_entropy_str = '"' + "a" * 40 + '"'
        sample = {"id": "1", "instruction": "test", "input": high_entropy_str, "output": "test", "metadata": {}}
        has_secrets, secrets = vc.detect_secrets(sample)
        self.assertTrue(has_secrets)
        self.assertIn("input:high_entropy", secrets)

    def test_detect_secrets_clean(self):
        sample = {"id": "1", "instruction": "hello", "input": "world", "output": "test", "metadata": {}}
        has_secrets, secrets = vc.detect_secrets(sample)
        self.assertFalse(has_secrets)

    def test_fuzzy_hash_whitespace(self):
        sample1 = {"instruction": "  hello  world  ", "output": "  test  "}
        sample2 = {"instruction": "helloworld", "output": "test"}
        self.assertEqual(vc.fuzzy_hash(sample1), vc.fuzzy_hash(sample2))

if __name__ == "__main__":
    unittest.main()
