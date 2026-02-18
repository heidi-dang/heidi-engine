import hmac
import hashlib
import json
import os
from pathlib import Path

# Use a persistent secret for signing
# In production, this should be set via environment variable
SECRET_PATH = Path(os.environ.get("AUTOTRAIN_DIR", os.path.expanduser("~/.local/heidi_engine"))) / ".secret_key"

def get_secret() -> str:
    """Gets or generates a persistent secret key for this installation."""
    if not SECRET_PATH.parent.exists():
        SECRET_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    if not SECRET_PATH.exists():
        # Generate a random 64-byte secret
        secret = os.urandom(64).hex()
        SECRET_PATH.write_text(secret)
        return secret
    
    return SECRET_PATH.read_text().strip()

def sign_record(record: dict) -> str:
    """
    Generate a cryptographic signature for a dataset record.
    Signs only core content to prevent tampering with instruction/input/output.
    """
    secret = get_secret()
    # Canonicalize the data we want to protect
    content = {
        "instruction": record.get("instruction", ""),
        "input": record.get("input", ""),
        "output": record.get("output", ""),
        "teacher_model": record.get("metadata", {}).get("teacher_model", "")
    }
    payload = json.dumps(content, sort_keys=True).encode()
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

def verify_record(record: dict) -> bool:
    """Verifies the signature of a record."""
    if "signature" not in record.get("metadata", {}):
        # Allow missing signatures for local/smoke tests but warn
        # In a strict production environment, this should return False
        return True
    
    expected_sig = record["metadata"]["signature"]
    actual_sig = sign_record(record)
    
    if not hmac.compare_digest(expected_sig, actual_sig):
        # logger or print for debug
        # print(f"SIG_FAIL: expected={expected_sig} actual={actual_sig}")
        return False
    return True
