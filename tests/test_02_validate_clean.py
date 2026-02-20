import pytest
import os
import sys
from pathlib import Path

# Add project root to sys.path to allow importing from scripts
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import the function from the script
# We use importlib because the script name starts with a number
import importlib.util
spec = importlib.util.spec_from_file_location("validate_clean", PROJECT_ROOT / "scripts" / "02_validate_clean.py")
validate_clean = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_clean)

def test_validate_schema_regression():
    """
    Regression test for validate_schema in 02_validate_clean.py.
    Verifies that it correctly identifies valid and invalid samples.
    """
    # Valid sample
    valid_sample = {
        "id": "1",
        "instruction": "test",
        "input": "test",
        "output": "test",
        "metadata": {}
    }
    valid, reason = validate_clean.validate_schema(valid_sample)
    assert valid is True
    assert reason == "ok"

    # Missing field
    for field in ["id", "instruction", "input", "output", "metadata"]:
        invalid_sample = valid_sample.copy()
        del invalid_sample[field]
        valid, reason = validate_clean.validate_schema(invalid_sample)
        assert valid is False
        assert f"missing field: {field}" in reason

def test_enforce_strict_clean_schema_regression():
    """
    Verifies that enforce_strict_clean_schema correctly enforces only required keys.
    """
    valid_sample = {
        "id": "1",
        "instruction": "test",
        "input": "test",
        "output": "test",
        "metadata": {}
    }
    # Should not raise
    validate_clean.enforce_strict_clean_schema(valid_sample)

    # Missing field
    invalid_sample = valid_sample.copy()
    del invalid_sample["id"]
    with pytest.raises(ValueError, match="Missing required keys"):
        validate_clean.enforce_strict_clean_schema(invalid_sample)

    # Extra field
    extra_sample = valid_sample.copy()
    extra_sample["extra"] = "field"
    with pytest.raises(ValueError, match="Unknown keys"):
        validate_clean.enforce_strict_clean_schema(extra_sample)
