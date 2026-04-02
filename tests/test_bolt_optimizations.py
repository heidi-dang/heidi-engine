
import unittest
import sys
import os
import importlib.util

# Load scripts/02_validate_clean.py dynamically
spec = importlib.util.spec_from_file_location("validate_clean", "scripts/02_validate_clean.py")
validate_clean = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_clean)

class TestBoltOptimizations(unittest.TestCase):
    def test_detect_secrets(self):
        # Test sample with no secrets
        clean_sample = {
            "instruction": "Explain Python list comprehensions",
            "input": "",
            "output": "They are a concise way to create lists.",
            "metadata": {}
        }
        has_secrets, found = validate_clean.detect_secrets(clean_sample)
        self.assertFalse(has_secrets)
        self.assertEqual(len(found), 0)

        # Test sample with OpenAI secret
        secret_sample = {
            "instruction": "Write code to use OpenAI",
            "input": "",
            "output": "Use sk-123456789012345678901234567890123456789012345678 as your key.",
            "metadata": {}
        }
        has_secrets, found = validate_clean.detect_secrets(secret_sample)
        self.assertTrue(has_secrets)
        self.assertIn("output:openai_key", found)

        # Test sample with multiple secrets in different fields
        multi_secret_sample = {
            "instruction": "API key ghp_123456789012345678901234567890123456",
            "input": "Bearer 123456789012345678901234567890",
            "output": "Nothing here",
            "metadata": {}
        }
        has_secrets, found = validate_clean.detect_secrets(multi_secret_sample)
        self.assertTrue(has_secrets)
        self.assertIn("instruction:github_token", found)
        self.assertIn("input:bearer_token", found)

    def test_fuzzy_hash_identity(self):
        # Samples with same content but different whitespace should have same fuzzy hash
        sample1 = {"instruction": "Hello world", "output": "Python is great"}
        sample2 = {"instruction": "  Hello\nworld  ", "output": "\tPython is great\n"}

        hash1 = validate_clean.fuzzy_hash(sample1)
        hash2 = validate_clean.fuzzy_hash(sample2)

        self.assertEqual(hash1, hash2)

    def test_fuzzy_hash_difference(self):
        # Samples with different content should have different fuzzy hashes
        sample1 = {"instruction": "Hello world", "output": "Python is great"}
        sample2 = {"instruction": "Hello world", "output": "Java is okay"}

        hash1 = validate_clean.fuzzy_hash(sample1)
        hash2 = validate_clean.fuzzy_hash(sample2)

        self.assertNotEqual(hash1, hash2)

    def test_fuzzy_hash_short_text(self):
        # Very short text should be handled correctly
        sample = {"instruction": "a", "output": "b"}
        fuzzy_hash = validate_clean.fuzzy_hash(sample, n=5)
        # Should return the combined normalized text "ab"
        self.assertEqual(fuzzy_hash, "ab")

if __name__ == "__main__":
    unittest.main()
