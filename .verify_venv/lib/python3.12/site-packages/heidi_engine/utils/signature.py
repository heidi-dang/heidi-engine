import hmac
import hashlib
import json
from typing import Dict, Any

class SignatureUtil:
    @staticmethod
    def hmac_sha256(data: str, key: str) -> str:
        """
        Compute HMAC-SHA256 over input string given a key.
        Matches C++ SignatureUtil implementation.
        """
        return hmac.new(
            key.encode("utf-8"),
            data.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    def verify(data: str, signature: str, key: str) -> bool:
        """
        Verify a signature against data and key.
        """
        expected = SignatureUtil.hmac_sha256(data, key)
        return hmac.compare_digest(expected, signature)

def canonicalize_manifest(manifest: Dict[str, Any]) -> str:
    """
    Serializes manifest to a canonical JSON string (sorted keys).
    Matches C++ Manifest::to_canonical_json implementation.
    """
    # Lane A/D: Strict Schema + Types
    EXPECTED_KEYS = 12
    if len(manifest) != EXPECTED_KEYS:
        raise ValueError(f"Manifest Hard-Lock: Expected {EXPECTED_KEYS} keys, got {len(manifest)}")

    # Lane A: Ban all floating point values to ensure cross-platform deterministic hashing
    for k, v in manifest.items():
        if isinstance(v, float):
            raise TypeError(f"Manifest Hard-Lock: Floating point value detected for key '{k}'. Use integers or strings.")
        if isinstance(v, dict):
            for sub_k, sub_v in v.items():
                if isinstance(sub_v, float):
                    raise TypeError(f"Manifest Hard-Lock: Floating point value detected in nested key '{k}.{sub_k}'.")

    # Phase 6 Requirement: Sorted keys, stable formatting, allow_nan=False for fail-closed safety
    return json.dumps(manifest, sort_keys=True, separators=(",", ":"), allow_nan=False)
