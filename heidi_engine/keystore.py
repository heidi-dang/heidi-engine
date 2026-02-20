import os
import sys
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

class Keystore:
    """
    Lane E: Zero-Trust Encrypted Keystore.
    Uses AES-256-GCM with scrypt KDF. No plaintext fallbacks.
    """
    def __init__(self, passphrase: str):
        self.passphrase = passphrase

    def _derive_key(self, salt: bytes) -> bytes:
        kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1)
        return kdf.derive(self.passphrase.encode())

    def encrypt_gate(self, data: str) -> str:
        salt = os.urandom(16)
        nonce = os.urandom(12)
        key = self._derive_key(salt)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, data.encode(), None)
        
        # Format: salt(16) | nonce(12) | ciphertext
        combined = salt + nonce + ciphertext
        return base64.b64encode(combined).decode()

    def decrypt_gate(self, encrypted_b64: str) -> str:
        combined = base64.b64decode(encrypted_b64)
        salt = combined[:16]
        nonce = combined[16:28]
        ciphertext = combined[28:]
        
        try:
            key = self._derive_key(salt)
            aesgcm = AESGCM(key)
            data = aesgcm.decrypt(nonce, ciphertext, None)
            return data.decode()
        except Exception:
            raise ValueError("Keystore: Decryption failed (invalid passphrase or tampered data)")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: keystore.py <encrypt|decrypt> <data|b64>")
        sys.exit(1)
        
    pwd = os.getenv("HEIDI_KEYSTORE_PWD")
    if not pwd:
        print("[FATAL] HEIDI_KEYSTORE_PWD must be set.", file=sys.stderr)
        sys.exit(1)
        
    ks = Keystore(pwd)
    if sys.argv[1] == "encrypt":
        print(ks.encrypt_gate(sys.argv[2]))
    else:
        print(ks.decrypt_gate(sys.argv[2]))
