import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from rich.panel import Panel
from rich.layout import Layout
from heidi_engine.dashboard import (
    get_run_dir,
    get_events_path,
    get_state_path,
    get_config_path,
    format_time,
    get_default_state,
    AUTOTRAIN_DIR,
    load_state,
    load_config,
    get_latest_data_file,
    poll_gpu_info,
    list_runs,
    create_header,
    create_counters_panel,
    create_usage_panel,
    create_trainer_panel,
    create_events_panel,
    create_data_panel,
    create_config_panel,
    create_keybindings_panel,
    create_overview_layout,
    create_teacher_layout,
    create_trainer_layout,
    create_events_layout,
    create_data_layout,
    create_config_layout,
    create_main_layout
)

def test_get_run_dir():
    run_id = "test_run"
    expected = Path(AUTOTRAIN_DIR) / "runs" / run_id
    assert get_run_dir(run_id) == expected

def test_get_events_path():
    run_id = "test_run"
    expected = Path(AUTOTRAIN_DIR) / "runs" / run_id / "events.jsonl"
    assert get_events_path(run_id) == expected

def test_get_state_path():
    run_id = "test_run"
    expected = Path(AUTOTRAIN_DIR) / "runs" / run_id / "state.json"
    assert get_state_path(run_id) == expected

def test_get_config_path():
    run_id = "test_run"
    expected = Path(AUTOTRAIN_DIR) / "runs" / run_id / "config.json"
    assert get_config_path(run_id) == expected

def test_format_time():
    # Valid ISO format
    ts = "2023-10-27T10:30:00Z"
    assert format_time(ts) == "10:30:00"

    # Invalid format should return first 8 chars or empty
    assert format_time("invalid-time") == "invalid-"
    assert format_time("") == ""

def test_get_default_state():
    state = get_default_state()
    assert isinstance(state, dict)
    assert "counters" in state
    assert "usage" in state
    assert state["status"] == "unknown"

def test_load_state_non_existent():
    with patch("heidi_engine.dashboard.get_state_path") as mock_path:
        mock_path.return_value.exists.return_value = False
        state = load_state("test_run")
        assert state["status"] == "unknown"

def test_load_state_valid():
    with patch("heidi_engine.dashboard.get_state_path") as mock_path:
        mock_path.return_value.exists.return_value = True
        with patch("builtins.open", MagicMock()):
            with patch("json.load") as mock_json:
                mock_json.return_value = {"status": "running", "run_id": "test_run"}
                state = load_state("test_run")
                assert state["status"] == "running"

def test_load_config():
    with patch("heidi_engine.dashboard.get_config_path") as mock_path:
        mock_path.return_value.exists.return_value = True
        with patch("builtins.open", MagicMock()):
            with patch("json.load") as mock_json:
                mock_json.return_value = {"TEACHER_MODEL": "gpt-4"}
                config = load_config("test_run")
                assert config["TEACHER_MODEL"] == "gpt-4"

def test_get_latest_data_file():
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = True
        with patch("pathlib.Path.glob") as mock_glob:
            mock_file = MagicMock(spec=Path)
            mock_file.stat.return_value.st_mtime = 100
            mock_glob.return_value = [mock_file]
            res = get_latest_data_file("test_run", Path("/tmp/data"), clean=True)
            assert res == mock_file

def test_poll_gpu_info_success():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "1000, 8000, 50"
        info = poll_gpu_info()
        assert info["available"] is True
        assert info["memory_used_mb"] == 1000
        assert info["memory_total_mb"] == 8000
        assert info["utilization_pct"] == 50

def test_poll_gpu_info_fail():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = Exception("error")
        info = poll_gpu_info()
        assert info["available"] is False

def test_list_runs():
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = True
        with patch("pathlib.Path.iterdir") as mock_iterdir:
            mock_run_dir = MagicMock(spec=Path)
            mock_run_dir.is_dir.return_value = True
            mock_run_dir.name = "run1"
            mock_run_dir.stat.return_value.st_mtime = 100
            (mock_run_dir / "state.json").exists.return_value = True

            mock_iterdir.return_value = [mock_run_dir]
            runs = list_runs()
            assert "run1" in runs

def test_create_header():
    state = get_default_state()
    panel = create_header(state)
    assert isinstance(panel, Panel)
    assert "Heidi AutoTrain Dashboard" in str(panel.title)

def test_create_counters_panel():
    state = get_default_state()
    panel = create_counters_panel(state)
    assert isinstance(panel, Panel)
    assert "Pipeline Progress" in str(panel.title)

def test_create_usage_panel():
    state = get_default_state()
    panel = create_usage_panel(state)
    assert isinstance(panel, Panel)
    assert "Teacher API Usage" in str(panel.title)

def test_create_trainer_panel():
    state = get_default_state()
    panel = create_trainer_panel(state)
    assert isinstance(panel, Panel)
    assert "Training Status" in str(panel.title)

def test_create_events_panel():
    panel = create_events_panel()
    assert isinstance(panel, Panel)
    assert "Recent Events" in str(panel.title)

def test_create_data_panel():
    # Test with no run_id
    panel = create_data_panel()
    assert isinstance(panel, Panel)
    assert "Data Tail" in str(panel.title)

def test_create_config_panel():
    state = get_default_state()
    panel = create_config_panel(state)
    assert isinstance(panel, Panel)
    assert "Configuration" in str(panel.title)

def test_create_keybindings_panel():
    panel = create_keybindings_panel()
    assert isinstance(panel, Panel)
    assert "Keyboard Shortcuts" in str(panel.title)

def test_layouts():
    state = get_default_state()

    # Test individual layouts
    assert isinstance(create_overview_layout(state), Layout)
    assert isinstance(create_teacher_layout(state), Layout)
    assert isinstance(create_trainer_layout(state), Layout)
    assert isinstance(create_events_layout(state), Layout)
    assert isinstance(create_data_layout(state), Layout)
    assert isinstance(create_config_layout(state), Layout)

    # Test create_main_layout
    layout, title = create_main_layout(state)
    assert isinstance(layout, Layout)
    assert isinstance(title, str)
