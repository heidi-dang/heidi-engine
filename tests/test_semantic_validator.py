import sys
import os
import unittest

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from heidi_engine.validation.semantic_validator import validate_semantic

class TestSemanticValidator(unittest.TestCase):
    def test_placeholder_rejection(self):
        record = {
            "metadata": {"task_type": "bug_fixing", "teacher_model": "real-gpt"},
            "input": "def my_func(): return 1",
            "output": "Here is the solution: class Handler: return 1"
        }
        (valid, reason), _ = validate_semantic(record)
        self.assertFalse(valid)
        self.assertIn("contains_placeholder", reason)

    def test_bug_fixing_missing_function(self):
        record = {
            "metadata": {"task_type": "bug_fixing", "teacher_model": "real-gpt"},
            "input": "def target_func(): return False",
            "output": "I fixed it: ```python\ndef wrong_func(): return True\n```"
        }
        (valid, reason), _ = validate_semantic(record)
        self.assertFalse(valid)
        self.assertIn("missing_original_function", reason)

    def test_bug_fixing_success(self):
        record = {
            "metadata": {"task_type": "bug_fixing", "teacher_model": "real-gpt"},
            "input": "def target_func(): return 0",
            "output": "I fixed the bug in target_func. Here is the code: ```python\ndef target_func(): return True\n```"
        }
        (valid, reason), _ = validate_semantic(record)
        self.assertTrue(valid)

    def test_unit_test_success(self):
        record = {
            "metadata": {"task_type": "unit_test_generation", "teacher_model": "real-gpt"},
            "input": "def target_func(): return 0",
            "output": "Import pytest\ndef test_target_func():\n    import pytest\n    assert True"
        }
        (valid, reason), _ = validate_semantic(record)
        self.assertTrue(valid)

    def test_unit_test_failure_no_pytest(self):
        record = {
            "metadata": {"task_type": "unit_test_generation", "teacher_model": "real-gpt"},
            "input": "def target_func(): return 1",
            "output": "def test_func(): assert True"
        }
        (valid, reason), _ = validate_semantic(record)
        self.assertFalse(valid)
        self.assertIn("missing_pytest", reason)

if __name__ == "__main__":
    unittest.main()
