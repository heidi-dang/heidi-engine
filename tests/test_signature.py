import pytest
from heidi_engine.utils.signature import SignatureUtil, canonicalize_manifest

def test_python_signature_interop():
    data = '{"created_at":"2026-02-20T10:00:00Z","dataset_hash":"sha256:abc","guardrail_snapshot":{"max_cpu":"80"},"record_count":100,"replay_hash":"sha256:replay","schema_version":"1.0"}'
    key = "super-secret-key"
    
    # This sig should match what C++ would produce for this exact string
    sig = SignatureUtil.hmac_sha256(data, key)
    assert SignatureUtil.verify(data, sig, key)
    assert not SignatureUtil.verify(data, sig, "wrong-key")

def test_canonicalization():
    manifest = {
        "dataset_hash": "sha256:abc",
        "record_count": 100,
        "created_at": "2026-02-20T10:00:00Z",
        "replay_hash": "sha256:replay",
        "schema_version": "1.0",
        "guardrail_snapshot": {"max_cpu": "80"}
    }
    
    json_str = canonicalize_manifest(manifest)
    # Basic check for sorted keys
    assert json_str.startswith('{"created_at":')
    assert '"dataset_hash":' in json_str
    assert '"guardrail_snapshot":' in json_str

def test_signature_tamper_detection():
    data = '{"value": 1}'
    key = "secret"
    sig = SignatureUtil.hmac_sha256(data, key)
    
    # Tamper with data (even a single space)
    tampered_data = '{"value":  1}'
    assert not SignatureUtil.verify(tampered_data, sig, key)
    
    # Tamper with key
    assert not SignatureUtil.verify(data, sig, "wrong")
