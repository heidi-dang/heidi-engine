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
    # Phase 6 Requirement: Sorted keys, stable formatting
    return json.dumps(manifest, sort_keys=True, separators=(",", ":"))
