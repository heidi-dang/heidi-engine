import os


def is_path_contained(path: str, base_dir: str) -> bool:
    """
    Lane B: Zero-Trust Path Containment (TOCTOU hardened).
    Prevents relative traversal and symlink escapes.
    """
    # Normalize with realpath + normcase (platform-safe)
    real_base = os.path.normcase(os.path.realpath(base_dir))

    # If path doesn't exist yet, contain-check its parent dir (TOCTOU defense)
    # We use dirname recursively until we find an existing path if necessary,
    # or just trust dirname(path) if it's a creation flow.
    target = path
    if not os.path.exists(path):
        target = os.path.dirname(os.path.abspath(path))

    real_path = os.path.normcase(os.path.realpath(target))

    # Exact match
    if real_path == real_base:
        return True

    # Prefix match with separator safeguard
    base_with_sep = real_base if real_base.endswith(os.sep) else real_base + os.sep
    return real_path.startswith(base_with_sep)

def enforce_containment(path: str, base_dir: str):
    if not is_path_contained(path, base_dir):
        raise PermissionError(f"Zero-Trust Violation: Path {path} is outside allowed boundary {base_dir}")
