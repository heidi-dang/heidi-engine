import pytest
import os
import json
import shutil
from pathlib import Path
from heidi_engine.finalizer import Finalizer

def make_writable(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for d in dirs: os.chmod(os.path.join(root, d), 0o777)
        for f in files: os.chmod(os.path.join(root, f), 0o777)
    os.chmod(path, 0o777)

def test_finalizer_flow():
    base = Path("build/test_finalizer")
    if base.exists(): make_writable(base); shutil.rmtree(base)
    base.mkdir(parents=True)
    
    pending = base / "pending"
    verified = base / "verified"
    pending.mkdir()
    verified.mkdir()

    dataset = pending / "dataset.jsonl"
    dataset.write_text('{"event_version":"1.0","ts":"now","run_id":"run1","round":1,"stage":"s","level":"i","event_type":"e","message":"m","counters_delta":{},"usage_delta":{},"artifact_paths":[],"prev_hash":"h"}\n')

    key = "secret"
    f = Finalizer(str(pending), str(verified), key)
    f.finalize("run1")

    run_verified = verified / "run1"
    assert run_verified.exists()
    assert (run_verified / "dataset.jsonl").exists()
    assert (run_verified / "manifest.json").exists()
    # 3. Verify manifest
    with open(run_verified / "manifest.json", "r") as f_man:
        manifest = json.load(f_man)
        assert len(manifest) == 12
        assert manifest["run_id"] == "run1"
        assert manifest["final_state"] == "VERIFIED"
        assert "engine_version" in manifest
    assert (run_verified / "signature.sig").exists()

    # Verify permissions (0o444/0o555 bits)
    assert oct(os.stat(str(run_verified / "dataset.jsonl")).st_mode & 0o777) == '0o444'
    
    # Cleanup
    make_writable(base)
    shutil.rmtree(base)

def test_finalizer_bypass_prevention():
    base = Path("build/test_finalizer_bypass")
    if base.exists(): make_writable(base); shutil.rmtree(base)
    base.mkdir(parents=True)
    # Test that finalizer fails if dataset is missing
    f = Finalizer(str(base / "missing"), str(base / "v"), "key")
    with pytest.raises(FileNotFoundError):
        f.finalize("run1")
    
    make_writable(base)
    shutil.rmtree(base)
