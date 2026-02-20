import pytest
import os
import shutil
from heidi_engine.finalizer import Finalizer

def test_finalizer_flow(tmp_path):
    pending = tmp_path / "pending"
    verified = tmp_path / "verified"
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
    assert (run_verified / "signature.sig").exists()

    # Verify permissions (0o444/0o555 bits)
    assert oct(os.stat(str(run_verified / "dataset.jsonl")).st_mode & 0o777) == '0o444'

def test_finalizer_bypass_prevention(tmp_path):
    # Test that finalizer fails if dataset is missing
    f = Finalizer(str(tmp_path / "missing"), str(tmp_path / "v"), "key")
    with pytest.raises(FileNotFoundError):
        f.finalize("run1")
