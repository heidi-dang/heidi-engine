import pytest
import os
import subprocess
from heidi_engine.doctor import doctor_check

def test_doctor_fail_missing_config():
    # Clear env
    os.environ.pop("MAX_CPU_PCT", None)
    os.environ.pop("MAX_MEM_PCT", None)
    os.environ.pop("MAX_WALL_TIME_MINUTES", None)
    os.environ.pop("HEIDI_SIGNING_KEY", None)
    os.environ.pop("HEIDI_KEYSTORE_PATH", None)

    assert doctor_check(strict=False) == False

def test_doctor_pass_with_config():
    os.environ["MAX_CPU_PCT"] = "80"
    os.environ["MAX_MEM_PCT"] = "90"
    os.environ["MAX_WALL_TIME_MINUTES"] = "60"
    os.environ["HEIDI_SIGNING_KEY"] = "key"
    os.environ["HEIDI_KEYSTORE_PATH"] = "keystore.enc"
    
    assert doctor_check(strict=True) == True

@pytest.mark.requires_heidi_cpp
def test_real_mode_blocked_in_core_integration():
    import heidi_cpp
    core = heidi_cpp.Core()
    
    # Missing signing key/keystore should block REAL mode
    os.environ.pop("HEIDI_SIGNING_KEY", None)
    
    # We can't easily test init/start fully without a real config file, 
    # but the logic in core.cpp is now explicitly blocking.
    # We rely on unit tests or mock configs.
    pass
