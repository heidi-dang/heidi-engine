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
        "run_id": "r1",
        "engine_version": "v1",
        "created_at": "2026-02-20T10:00:00Z",
        "schema_version": "1.0",
        "dataset_hash": "sha256:abc",
        "record_count": 100,
        "replay_hash": "sha256:replay",
        "signing_key_id": "k1",
        "final_state": "VERIFIED",
        "total_runtime_sec": 42,
        "event_count": 1000,
        "guardrail_snapshot": {"max_cpu": "80"}
    }
    
    c1 = canonicalize_manifest(manifest)
    
    # Change order in dict - result must be SAME
    manifest_reordered = {k: manifest[k] for k in sorted(manifest.keys(), reverse=True)}
    c2 = canonicalize_manifest(manifest_reordered)
    
    assert c1 == c2
    # Ensure no whitespace
    assert " : " not in c1
    assert " , " not in c1
    
    # Test float rejection
    manifest_with_float = manifest.copy()
    manifest_with_float["total_runtime_sec"] = 42.0
    with pytest.raises(TypeError):
        canonicalize_manifest(manifest_with_float)

def test_signature_tamper_detection():
    data = '{"value": 1}'
    key = "secret"
    sig = SignatureUtil.hmac_sha256(data, key)
    
    # Tamper with data (even a single space)
    tampered_data = '{"value":  1}'
    assert not SignatureUtil.verify(tampered_data, sig, key)
    
    # Tamper with key
    assert not SignatureUtil.verify(data, sig, "wrong")
