import os
import sys
import shutil
import hashlib
from typing import Dict, Any
from heidi_engine.utils.io_jsonl import load_jsonl
from heidi_engine.utils.signature import SignatureUtil, canonicalize_manifest

class Finalizer:
    """
    Lane B: Zero-Trust Finalizer.
    Validates pending data, signs manifest, and freezes verified/ directory.
    """
    def __init__(self, pending_dir: str, verified_dir: str, signing_key: str):
        self.pending_dir = pending_dir
        self.verified_dir = verified_dir
        self.signing_key = signing_key

    def finalize(self, run_id: str):
        dataset_path = os.path.join(self.pending_dir, "dataset.jsonl")
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Finalizer: Missing dataset at {dataset_path}")

        # 1. Compute Hash
        sha256 = hashlib.sha256()
        record_count = 0
        with open(dataset_path, "rb") as f:
            for line in f:
                sha256.update(line)
                record_count += 1
        
        digest = sha256.hexdigest()

        # 2. Create Manifest
        manifest = {
            "dataset_hash": f"sha256:{digest}",
            "record_count": record_count,
            "created_at": "2026-02-20T10:00:00Z", # Placeholder for actual TS
            "schema_version": "1.0",
            "guardrail_snapshot": {}, # Would be gathered from current config
            "replay_hash": "" # Computed during replay
        }

        # 3. Sign Manifest
        canonical_json = canonicalize_manifest(manifest)
        signature = SignatureUtil.hmac_sha256(canonical_json, self.signing_key)

        # 4. Move and Protect
        run_verified_dir = os.path.join(self.verified_dir, run_id)
        os.makedirs(run_verified_dir, exist_ok=True)

        target_dataset = os.path.join(run_verified_dir, "dataset.jsonl")
        shutil.move(dataset_path, target_dataset)

        manifest_path = os.path.join(run_verified_dir, "manifest.json")
        with open(manifest_path, "w") as f:
            f.write(canonical_json)

        sig_path = os.path.join(run_verified_dir, "signature.sig")
        with open(sig_path, "w") as f:
            f.write(signature)

        # 5. Freeze Permissions (Read-only for everyone)
        os.chmod(target_dataset, 0o444)
        os.chmod(manifest_path, 0o444)
        os.chmod(sig_path, 0o444)
        os.chmod(run_verified_dir, 0o555)

        print(f"[FINALIZER] Run {run_id} finalized and signed at {run_verified_dir}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: finalizer.py <pending_dir> <verified_dir> <run_id>")
        sys.exit(1)
    
    key = os.getenv("HEIDI_SIGNING_KEY", "default-dev-key")
    f = Finalizer(sys.argv[1], sys.argv[2], key)
    f.finalize(sys.argv[3])
