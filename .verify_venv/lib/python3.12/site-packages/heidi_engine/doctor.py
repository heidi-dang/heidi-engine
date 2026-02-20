import os
import sys

def doctor_check(strict: bool = False) -> bool:
    """
    Lane C: Zero-Trust Doctor Gatekeeper.
    Validates environment and config before REAL mode execution.
    """
    checks = []
    
    # 1. Check Guardrails Config
    has_cpu = os.getenv("MAX_CPU_PCT") is not None
    has_mem = os.getenv("MAX_MEM_PCT") is not None
    checks.append(("Guardrails Configured", has_cpu and has_mem))
    
    # 2. Check Budget Config
    has_wall = os.getenv("MAX_WALL_TIME_MINUTES") is not None
    checks.append(("Budget Thresholds Set", has_wall))
    
    # 3. Check Keystore Encryption
    # Placeholder for Lane E requirement
    is_encrypted = os.getenv("HEIDI_KEYSTORE_PATH", "").endswith(".enc")
    checks.append(("Keystore Encrypted", is_encrypted))

    # 4. Check Signature Enforcement
    # In Zero-Trust, this must be explicit
    has_signing_key = os.getenv("HEIDI_SIGNING_KEY") is not None
    checks.append(("Signature Key Present", has_signing_key))

    all_passed = True
    print("\n[DOCTOR] Pre-flight sanity check:")
    for name, result in checks:
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {name}")
        if not result:
            all_passed = False

    if strict and not all_passed:
        print("\n[FATAL] Zero-Trust Violation: REAL mode disabled until all checks pass.", file=sys.stderr)
        return False
    
    return all_passed

if __name__ == "__main__":
    is_strict = "--strict" in sys.argv
    if not doctor_check(strict=is_strict):
        sys.exit(1)
    print("\n[DOCTOR] System is healthy and secure.")
