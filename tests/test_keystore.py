import pytest
import os
from heidi_engine.keystore import Keystore

def test_keystore_roundtrip():
    pwd = "correct-passphrase"
    ks = Keystore(pwd)
    secret = "sk-abc-123"
    
    encrypted = ks.encrypt_gate(secret)
    decrypted = ks.decrypt_gate(encrypted)
    assert decrypted == secret

def test_keystore_invalid_passphrase():
    ks = Keystore("correct")
    encrypted = ks.encrypt_gate("secret")
    
    ks_bad = Keystore("wrong")
    with pytest.raises(ValueError, match="Keystore: Decryption failed"):
        ks_bad.decrypt_gate(encrypted)

def test_keystore_tamper_detection():
    ks = Keystore("pwd")
    encrypted = ks.encrypt_gate("secret")
    
    # Tamper with the raw base64 string
    import base64
    raw = base64.b64decode(encrypted)
    tampered_raw = raw[:-1] + (b'\x00' if raw[-1] != 0 else b'\x01')
    tampered_b64 = base64.b64encode(tampered_raw).decode()
    
    with pytest.raises(ValueError, match="Keystore: Decryption failed"):
        ks.decrypt_gate(tampered_b64)
