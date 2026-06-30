from pathlib import Path

from heidi_engine.dashboard import get_run_dir as dash_get_run_dir
from heidi_engine.telemetry import get_run_dir as tel_get_run_dir


def test_path_traversal():
    dangerous_ids = [
        "../../etc/passwd",
        "../secrets",
        "..",
        ".",
        "run_1/../../etc",
    ]

    for rid in dangerous_ids:
        # Check telemetry
        tel_dir = tel_get_run_dir(rid)
        print(f"Telemetry Run ID: {rid} -> Path: {tel_dir}")
        assert ".." not in tel_dir.parts
        assert tel_dir.name == "invalid_run_id" or tel_dir.name == Path(rid).name

        # Check dashboard
        dash_dir = dash_get_run_dir(rid)
        print(f"Dashboard Run ID: {rid} -> Path: {dash_dir}")
        assert ".." not in dash_dir.parts
        assert dash_dir.name == "invalid_run_id" or dash_dir.name == Path(rid).name

    print("Path traversal tests passed!")

if __name__ == "__main__":
    test_path_traversal()
