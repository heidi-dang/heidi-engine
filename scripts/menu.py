#!/usr/bin/env python3
"""
================================================================================
scripts/menu.py - Interactive Menu Controller for AutoTraining Pipeline
================================================================================

PURPOSE:
    Provides an interactive text-based menu for controlling the training
    pipeline without editing configuration files. Users can:
    1. Start new runs with custom configuration
    2. Resume interrupted runs
    3. Pause/Stop running pipelines gracefully
    4. View run status and logs
    5. Configure parameters interactively

HOW IT WORKS:
    1. Menu displays options and prompts for user input
    2. Configuration is saved to config.yaml
    3. Pipeline scripts read config.yaml instead of environment
    4. Stop/Pause requests set flags in state.json
    5. Dashboard shows real-time progress

TUNABLE PARAMETERS:
    - AUTOTRAIN_DIR: Base directory for heidi_engine outputs
    - CONFIG_FILE: Path to configuration file (default: heidi_engine/config.yaml)
    - MENU_TIMEOUT: Input timeout in seconds

CONFIGURABLE OPTIONS:
    - BASE_MODEL: Base model to fine-tune
    - TEACHER_MODEL: Teacher model for generation
    - SAMPLES_PER_ROUND: Samples to generate per round
    - ROUNDS: Number of training rounds
    - VAL_RATIO: Validation split ratio
    - SEQ_LEN: Sequence length
    - LORA_R: LoRA rank
    - GRAD_ACCUM: Gradient accumulation steps
    - TRAIN_STEPS: Training steps per round
    - RUN_UNIT_TESTS: Enable unit test gate (0/1)

KEYBOARD SHORTCUTS IN MENU:
    - Arrow keys: Navigate options
    - Enter: Select option
    - Space: Toggle checkbox
    - Esc: Go back/Cancel

EXTENDING THIS MODULE:
    - Add new menu options in show_main_menu()
    - Add new config options in configure_parameters()
    - Add new actions in handle_selection()

REQUIREMENTS:
    - PyYAML: pip install pyyaml
    - (Optional) readline for better terminal input

================================================================================
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Try to import yaml, fall back to json if not available
try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    print("[WARN] PyYAML not installed, using JSON config", file=sys.stderr)


# =============================================================================
# CONFIGURATION - Adjust these for your needs
# =============================================================================

# Base directory for heidi_engine outputs
# TUNABLE: Change if heidi_engine is in different location
AUTOTRAIN_DIR = os.environ.get("AUTOTRAIN_DIR", "./heidi_engine")

# Configuration file path
# TUNABLE: Change to use different config file
CONFIG_FILE = os.environ.get("MENU_CONFIG_FILE", f"{AUTOTRAIN_DIR}/config.yaml")

# Menu input timeout in seconds
# TUNABLE: Increase for slower terminals
MENU_TIMEOUT = 30

# PID file for running pipeline
# TUNABLE: N/A
PID_FILE = f"{AUTOTRAIN_DIR}/pipeline.pid"

# HTTP status server port (same as telemetry)
HTTP_STATUS_PORT = int(os.environ.get("HTTP_STATUS_PORT", "7779"))


# =============================================================================
# DEFAULT CONFIGURATION
# =============================================================================

DEFAULT_CONFIG = {
    # Model configuration
    "BASE_MODEL": "microsoft/phi-2",
    "TEACHER_MODEL": "gpt-4o-mini",
    # Dataset configuration
    "SAMPLES_PER_ROUND": 50,
    "ROUNDS": 3,
    "VAL_RATIO": 0.1,
    # Training configuration - VRAM-safe defaults
    "SEQ_LEN": 2048,
    "BATCH_SIZE": 1,
    "GRAD_ACCUM": 8,
    "TRAIN_STEPS": 500,
    "SAVE_STEPS": 100,
    "EVAL_STEPS": 50,
    "LORA_R": 64,
    "LORA_ALPHA": 128,
    "LORA_DROPOUT": 0.1,
    "LR": "2e-4",
    # Other options
    "RUN_UNIT_TESTS": "0",
    "SEED": "42",
    "OUT_DIR": AUTOTRAIN_DIR,
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def get_runs_dir() -> Path:
    """Get runs directory path."""
    return Path(AUTOTRAIN_DIR) / "runs"


def get_config_path() -> Path:
    """Get config file path."""
    return Path(CONFIG_FILE)


def load_config() -> Dict[str, Any]:
    """
    Load configuration from file.

    HOW IT WORKS:
        - First tries YAML, then JSON
        - Falls back to defaults if file doesn't exist

    TUNABLE:
        - N/A

    RETURNS:
        Configuration dictionary
    """
    config_file = get_config_path()

    if not config_file.exists():
        return DEFAULT_CONFIG.copy()

    try:
        if HAS_YAML and config_file.suffix in [".yaml", ".yml"]:
            with open(config_file) as f:
                config = yaml.safe_load(f)
                return {**DEFAULT_CONFIG, **(config or {})}
        else:
            # Try JSON
            with open(config_file) as f:
                config = json.load(f)
                return {**DEFAULT_CONFIG, **config}
    except Exception as e:
        print(f"[WARN] Failed to load config: {e}", file=sys.stderr)
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> None:
    """
    Save configuration to file.

    HOW IT WORKS:
        - Saves as YAML if available, otherwise JSON
        - Creates parent directory if needed

    TUNABLE:
        - N/A

    ARGS:
        config: Configuration dictionary to save
    """
    config_file = get_config_path()
    config_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        if HAS_YAML and config_file.suffix in [".yaml", ".yml"]:
            with open(config_file, "w") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        else:
            with open(config_file.with_suffix(".json"), "w") as f:
                json.dump(config, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to save config: {e}", file=sys.stderr)
        raise


def get_run_state(run_id: str) -> Dict[str, Any]:
    """
    Get state for a run.

    HOW IT WORKS:
        - Reads state.json from run directory
        - Returns empty dict if not found

    TUNABLE:
        - N/A

    ARGS:
        run_id: Run ID

    RETURNS:
        State dictionary
    """
    state_file = get_runs_dir() / run_id / "state.json"

    if not state_file.exists():
        return {}

    try:
        with open(state_file) as f:
            return json.load(f)
    except Exception:
        return {}


def list_runs() -> List[Dict[str, Any]]:
    """
    List all runs with their status.

    HOW IT WORKS:
        - Scans runs directory
        - Returns list of run info

    TUNABLE:
        - N/A

    RETURNS:
        List of run info dictionaries
    """
    runs_dir = get_runs_dir()

    if not runs_dir.exists():
        return []

    runs = []
    for run_path in sorted(runs_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not run_path.is_dir():
            continue

        state = get_run_state(run_path.name)
        if state:
            runs.append(
                {
                    "run_id": run_path.name,
                    "status": state.get("status", "unknown"),
                    "current_round": state.get("current_round", 0),
                    "current_stage": state.get("current_stage", "unknown"),
                    "stop_requested": state.get("stop_requested", False),
                    "pause_requested": state.get("pause_requested", False),
                }
            )

    return runs


def get_running_pid() -> Optional[int]:
    """
    Get PID of running pipeline.

    HOW IT WORKS:
        - Reads PID from file
        - Checks if process is still running

    TUNABLE:
        - N/A

    RETURNS:
        PID if running, None otherwise
    """
    pid_file = Path(PID_FILE)

    if not pid_file.exists():
        return None

    try:
        with open(pid_file) as f:
            pid = int(f.read().strip())

        # Check if process is running
        try:
            os.kill(pid, 0)
            return pid
        except OSError:
            # Process not running
            return None
    except Exception:
        return None


def save_pid(pid: int) -> None:
    """Save pipeline PID to file."""
    Path(PID_FILE).write_text(str(pid))


def clear_pid() -> None:
    """Clear pipeline PID file."""
    Path(PID_FILE).unlink(missing_ok=True)


# =============================================================================
# PIPELINE CONTROL
# =============================================================================


def start_pipeline(config: Dict[str, Any], background: bool = False) -> Optional[int]:
    """
    Start a new pipeline run.

    HOW IT WORKS:
        1. Creates new run ID
        2. Initializes telemetry
        3. Saves config to config.yaml
        4. Starts loop.sh as subprocess
        5. Optionally runs in background

    TUNABLE:
        - N/A

    ARGS:
        config: Configuration dictionary
        background: Run in background

    RETURNS:
        PID if background=True, None otherwise
    """
    # Allow user to specify a run_id or use default
    print(f"\nDefault Run ID: run_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    print("Type 'code-assistant' for agent mode (no API key required).")
    custom_run_id = input("Enter Run ID (or press Enter for default): ").strip()

    if custom_run_id:
        run_id = custom_run_id
    else:
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Save config
    save_config(config)

    # Build environment
    env = os.environ.copy()
    env["RUN_ID"] = run_id
    env["AUTOTRAIN_DIR"] = AUTOTRAIN_DIR

    # Export config as env vars
    for key, value in config.items():
        if isinstance(value, str):
            env[key] = value
        else:
            env[key] = str(value)

    # Start pipeline
    script_dir = Path(__file__).parent
    loop_script = script_dir / "loop.sh"

    if not loop_script.exists():
        print(f"[ERROR] loop.sh not found at {loop_script}", file=sys.stderr)
        return None

    if background:
        # Start in background
        proc = subprocess.Popen(
            [str(loop_script)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        save_pid(proc.pid)
        print(f"[INFO] Pipeline started in background (PID: {proc.pid})")
        return proc.pid
    else:
        # Run in foreground
        print("[INFO] Starting pipeline in foreground...")
        print("[INFO] Press Ctrl+C to stop (will save state)")
        try:
            proc = subprocess.run(
                [str(loop_script)],
                env=env,
            )
            clear_pid()
            return None
        except KeyboardInterrupt:
            print("\n[INFO] Interrupted - pipeline will stop gracefully")
            return None


def stop_pipeline() -> bool:
    """
    Request pipeline to stop gracefully.

    HOW IT WORKS:
        1. Gets running pipeline PID
        2. Sends SIGINT to request graceful stop
        3. Pipeline checks stop_requested in state.json
        4. Exits at stage boundary

    TUNABLE:
        - N/A

    RETURNS:
        True if stop requested successfully
    """
    pid = get_running_pid()

    if not pid:
        # Try to find by status
        runs = list_runs()
        for run in runs:
            if run["status"] == "running":
                # Import here to avoid circular imports
                sys.path.insert(0, str(Path(__file__).parent.parent))
                from heidi_engine.telemetry import request_stop

                request_stop(run["run_id"])
                print(f"[INFO] Stop requested for run: {run['run_id']}")
                return True

        print("[WARN] No running pipeline found")
        return False

    try:
        # Send SIGINT for graceful stop
        os.kill(pid, signal.SIGINT)
        print(f"[INFO] Sent stop signal to PID {pid}")
        print("[INFO] Pipeline will stop at next stage boundary")
        clear_pid()
        return True
    except OSError as e:
        print(f"[ERROR] Failed to stop pipeline: {e}", file=sys.stderr)
        return False


def pause_pipeline() -> bool:
    """
    Request pipeline to pause.

    HOW IT WORKS:
        - Sets pause_requested flag in state.json
        - Pipeline pauses at safe boundaries

    TUNABLE:
        - N/A

    RETURNS:
        True if pause requested successfully
    """
    pid = get_running_pid()

    if not pid:
        print("[WARN] No running pipeline found")
        return False

    # Import here to avoid circular imports
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from heidi_engine.telemetry import request_pause

    # Find the run
    runs = list_runs()
    for run in runs:
        if run["status"] == "running":
            request_pause(run["run_id"])
            print(f"[INFO] Pause requested for run: {run['run_id']}")
            return True

    print("[WARN] Could not find running run to pause")
    return False


def resume_pipeline() -> bool:
    """
    Resume a paused pipeline.

    HOW IT WORKS:
        - Clears pause_requested flag in state.json
        - Pipeline continues

    TUNABLE:
        - N/A

    RETURNS:
        True if resume successful
    """
    # Import here to avoid circular imports
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from heidi_engine.telemetry import clear_pause

    runs = list_runs()
    for run in runs:
        if run.get("pause_requested"):
            clear_pause(run["run_id"])
            print(f"[INFO] Resumed run: {run['run_id']}")
            return True

    print("[WARN] No paused run found to resume")
    return False


def start_dashboard(run_id: Optional[str] = None) -> None:
    """
    Start the dashboard in a new terminal/background.

    HOW IT WORKS:
        - Runs dashboard.py in background
        - Optionally specifies run ID

    TUNABLE:
        - N/A

    ARGS:
        run_id: Run to monitor (latest if not specified)
    """
    # Import here to avoid circular imports
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from heidi_engine.dashboard import run_dashboard, select_run

    if not run_id:
        run_id = select_run()

    if not run_id:
        print("[ERROR] No run selected")
        return

    print(f"[INFO] Starting dashboard for run: {run_id}")

    # Run dashboard (this will block)
    try:
        run_dashboard(run_id)
    except Exception as e:
        print(f"[ERROR] Dashboard error: {e}", file=sys.stderr)


def start_http_server() -> None:
    """
    Start HTTP status server.

    HOW IT WORKS:
        - Starts telemetry HTTP server
        - Serves state JSON on localhost:7779

    TUNABLE:
        - Change port via HTTP_STATUS_PORT env var
    """
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from heidi_engine.telemetry import get_latest_run, start_http_server

    run_id = get_latest_run()
    if run_id:
        print(f"[INFO] Starting HTTP server for run: {run_id}")
    else:
        print("[INFO] Starting HTTP server (no run selected)")

    start_http_server(HTTP_STATUS_PORT)

    # Keep running
    while True:
        time.sleep(60)


# =============================================================================
# INTERACTIVE MENU
# =============================================================================


def print_header():
    """Print menu header."""
    print("\n" + "=" * 60)
    print("     Heidi AutoTrain - Interactive Controller")
    print("=" * 60)


def print_runs():
    """Print list of runs."""
    runs = list_runs()

    if not runs:
        print("\n  No runs found")
        return

    print("\n  Recent Runs:")
    print("  " + "-" * 50)

    for i, run in enumerate(runs, 1):
        status = run.get("status", "unknown")
        round_num = run.get("current_round", 0)
        stage = run.get("current_stage", "")

        status_str = status.upper()
        if run.get("stop_requested"):
            status_str += " (stopping)"
        elif run.get("pause_requested"):
            status_str += " (paused)"

        print(f"  {i}. {run['run_id']}")
        print(f"     Status: {status_str} | Round: {round_num} | Stage: {stage}")
        print()


def print_status():
    """Print current pipeline status."""
    pid = get_running_pid()

    if pid:
        print(f"\n  Pipeline running (PID: {pid})")
    else:
        print("\n  Pipeline not running")

    print_runs()


def get_input(prompt: str, default: str = "", options: Optional[List[str]] = None) -> str:
    """
    Get user input with default and validation.

    HOW IT WORKS:
        - Shows prompt with default value
        - Validates against options if provided

    TUNABLE:
        - N/A

    ARGS:
        prompt: Prompt message
        default: Default value
        options: List of valid options

    RETURNS:
        User input (or default)
    """
    if options:
        prompt = f"{prompt} [{'/'.join(options)}]"
        if default:
            prompt = f"{prompt} (default: {default})"
    elif default:
        prompt = f"{prompt} (default: {default})"

    prompt += ": "

    while True:
        try:
            value = input(prompt).strip()
            if not value:
                return default
            if options and value not in options:
                print(f"  Invalid option. Choose from: {', '.join(options)}")
                continue
            return value
        except EOFError:
            return default
        except KeyboardInterrupt:
            print("\n")
            raise


def configure_parameters(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Interactive parameter configuration.

    HOW IT WORKS:
        1. Shows current values
        2. Prompts for new values
        3. Returns updated config

    TUNABLE:
        - Add new parameters here
        - Customize prompts

    ARGS:
        config: Current configuration

    RETURNS:
        Updated configuration
    """
    print("\n" + "=" * 60)
    print("  Configure Parameters")
    print("=" * 60)
    print("  Press Enter to keep current value")
    print("=" * 60)

    # Model configuration
    print("\n  --- Model Configuration ---")
    config["BASE_MODEL"] = get_input("  Base model", config.get("BASE_MODEL", "microsoft/phi-2"))
    config["TEACHER_MODEL"] = get_input(
        "  Teacher model", config.get("TEACHER_MODEL", "gpt-4o-mini")
    )

    # Dataset configuration
    print("\n  --- Dataset Configuration ---")
    config["SAMPLES_PER_ROUND"] = get_input(
        "  Samples per round", str(config.get("SAMPLES_PER_ROUND", 50))
    )
    config["ROUNDS"] = get_input("  Number of rounds", str(config.get("ROUNDS", 3)))
    config["VAL_RATIO"] = get_input("  Validation ratio", str(config.get("VAL_RATIO", 0.1)))

    # Training configuration
    print("\n  --- Training Configuration ---")
    config["SEQ_LEN"] = get_input("  Sequence length", str(config.get("SEQ_LEN", 2048)))
    config["LORA_R"] = get_input("  LoRA rank", str(config.get("LORA_R", 64)))
    config["GRAD_ACCUM"] = get_input("  Gradient accumulation", str(config.get("GRAD_ACCUM", 8)))
    config["TRAIN_STEPS"] = get_input("  Training steps", str(config.get("TRAIN_STEPS", 500)))
    config["LR"] = get_input("  Learning rate", str(config.get("LR", "2e-4")))

    # Options
    print("\n  --- Options ---")
    unit_tests = get_input(
        "  Run unit tests (0/1)", str(config.get("RUN_UNIT_TESTS", "0")), ["0", "1"]
    )
    config["RUN_UNIT_TESTS"] = unit_tests

    config["SEED"] = get_input("  Random seed", str(config.get("SEED", "42")))

    # Convert to proper types
    for key in [
        "SAMPLES_PER_ROUND",
        "ROUNDS",
        "SEQ_LEN",
        "LORA_R",
        "GRAD_ACCUM",
        "TRAIN_STEPS",
        "BATCH_SIZE",
        "SAVE_STEPS",
        "EVAL_STEPS",
    ]:
        if key in config:
            try:
                config[key] = int(config[key])
            except ValueError:
                pass

    for key in ["VAL_RATIO", "LORA_ALPHA", "LORA_DROPOUT"]:
        if key in config:
            try:
                config[key] = float(config[key])
            except ValueError:
                pass

    return config


def show_main_menu() -> int:
    """
    Show main menu and get user selection.

    HOW IT WORKS:
        1. Displays available options
        2. Prompts for selection
        3. Returns selection index

    TUNABLE:
        - Add/remove menu options

    RETURNS:
        Selected menu index
    """
    print_header()
    print_status()

    options = [
        "Start New Run",
        "Resume Last Run",
        "Stop Pipeline",
        "Pause Pipeline",
        "Resume Pipeline",
        "Configure Parameters",
        "View Dashboard",
        "Start HTTP Server",
        "Exit",
    ]

    print("\n  Main Menu:")
    for i, option in enumerate(options, 1):
        print(f"    {i}. {option}")

    print()

    while True:
        try:
            choice = input("  Select option [1-{}]: ".format(len(options))).strip()
            if not choice:
                continue
            idx = int(choice)
            if 1 <= idx <= len(options):
                return idx
            print("  Invalid selection")
        except ValueError:
            pass
        except KeyboardInterrupt:
            return len(options)  # Exit


def handle_selection(selection: int, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Handle menu selection.

    HOW IT WORKS:
        - Executes action based on selection
        - Returns updated config if changed

    TUNABLE:
        - Add new menu handlers

    ARGS:
        selection: Menu selection index
        config: Current configuration

    RETURNS:
        Updated configuration or None
    """
    # Import here to avoid circular imports at module level
    sys.path.insert(0, str(Path(__file__).parent.parent))

    if selection == 1:  # Start New Run
        # Check if pipeline already running
        if get_running_pid():
            print("\n  Pipeline already running!")
            confirm = get_input("  Start anyway?", "n", ["y", "n"])
            if confirm.lower() != "y":
                return config

        # Configure parameters first
        config = configure_parameters(config.copy())

        # Ask about background
        bg = get_input("  Run in background?", "y", ["y", "n"])

        start_pipeline(config, background=(bg.lower() == "y"))
        return config

    elif selection == 2:  # Resume Last Run
        runs = list_runs()
        if not runs:
            print("\n  No runs to resume")
            return config

        # Find most recent paused or stopped run
        for run in runs:
            if run.get("status") in ["paused", "stopped"] or run.get("pause_requested"):
                print(f"\n  Resuming run: {run['run_id']}")
                # Resume if paused
                if run.get("pause_requested"):
                    resume_pipeline()

                # Start pipeline again
                start_pipeline(config, background=True)
                return config

        print("\n  No resumable run found")
        return config

    elif selection == 3:  # Stop Pipeline
        stop_pipeline()
        return config

    elif selection == 4:  # Pause Pipeline
        pause_pipeline()
        return config

    elif selection == 5:  # Resume Pipeline
        resume_pipeline()
        return config

    elif selection == 6:  # Configure Parameters
        return configure_parameters(config.copy())

    elif selection == 7:  # View Dashboard
        print("\n  Starting dashboard (press q to quit)...")
        start_dashboard()
        return config

    elif selection == 8:  # Start HTTP Server
        print("\n  Starting HTTP server on port {}...".format(HTTP_STATUS_PORT))
        print("  Press Ctrl+C to stop")
        try:
            start_http_server()
        except KeyboardInterrupt:
            print("\n  HTTP server stopped")
        return config

    elif selection == 9:  # Exit
        print("\n  Goodbye!")
        sys.exit(0)

    return config


def interactive_loop():
    """
    Main interactive menu loop.

    HOW IT WORKS:
        1. Shows main menu
        2. Handles user selection
        3. Repeats until exit

    TUNABLE:
        - N/A
    """
    config = load_config()

    while True:
        try:
            selection = show_main_menu()
            config = handle_selection(selection, config) or config

            # Save config after changes
            save_config(config)

            # Small delay before showing menu again
            if selection not in [7, 8]:  # Not dashboard or HTTP server
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n  Use 'Exit' menu option to quit properly")
            continue
        except Exception as e:
            print(f"\n  Error: {e}")
            time.sleep(2)


# =============================================================================
# CLI
# =============================================================================


def is_interactive() -> bool:
    """Check if running in interactive terminal."""
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except Exception:
        return False


def main():
    """
    CLI for menu controller.

    NON-INTERACTIVE MODE:
        - In CI/systemd/docker, detects non-TTY and shows helpful message
        - Use CLI flags for all operations in non-interactive mode
        - Exit with clear error if interactive mode required but not available

    COMMANDS:
        python scripts/menu.py                  # Interactive menu (requires TTY)
        python scripts/menu.py --start         # Start new run
        python scripts/menu.py --stop          # Stop running pipeline
        python scripts/menu.py --status         # Show status
        python scripts/menu.py --dashboard     # Start dashboard
        python scripts/menu.py --http          # Start HTTP server
    """
    parser = argparse.ArgumentParser(description="AutoTrain Menu Controller")
    parser.add_argument("--start", action="store_true", help="Start new run")
    parser.add_argument("--stop", action="store_true", help="Stop running pipeline")
    parser.add_argument("--pause", action="store_true", help="Pause running pipeline")
    parser.add_argument("--resume", action="store_true", help="Resume paused pipeline")
    parser.add_argument("--status", "-s", action="store_true", help="Show status")
    parser.add_argument("--dashboard", "-d", action="store_true", help="Start dashboard")
    parser.add_argument("--http", action="store_true", help="Start HTTP server")
    parser.add_argument("--configure", "-c", action="store_true", help="Configure parameters")
    parser.add_argument("--background", "-b", action="store_true", help="Run in background")
    parser.add_argument("--list", "-l", action="store_true", help="List runs")
    args = parser.parse_args()

    # Add parent to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent))

    # Check for interactive-only operations
    interactive_only = not any(
        [
            args.status,
            args.list,
            args.start,
            args.stop,
            args.pause,
            args.resume,
            args.dashboard,
            args.http,
        ]
    )

    if interactive_only:
        # No CLI flags provided - check if interactive
        if not is_interactive():
            print("Error: Interactive menu requires a terminal (TTY).")
            print("")
            print("Usage in non-interactive environments:")
            print("  python scripts/menu.py --status              # Show status")
            print("  python scripts/menu.py --list                 # List runs")
            print("  python scripts/menu.py --start                # Start new run")
            print("  python scripts/menu.py --stop                 # Stop pipeline")
            print("  python scripts/menu.py --dashboard            # Start dashboard")
            print("  python scripts/menu.py --http                 # Start HTTP server")
            print("")
            print("For full interactive menu, run in a terminal.")
            sys.exit(1)

    # Handle commands
    if args.status:
        print_status()

    elif args.list:
        print_runs()

    elif args.start:
        config = load_config()
        if args.configure:
            config = configure_parameters(config)
        start_pipeline(config, background=args.background)

    elif args.stop:
        stop_pipeline()

    elif args.pause:
        pause_pipeline()

    elif args.resume:
        resume_pipeline()

    elif args.dashboard:
        start_dashboard()

    elif args.http:
        start_http_server()

    elif args.configure:
        config = load_config()
        config = configure_parameters(config)
        save_config(config)
        print("\nConfiguration saved!")

    else:
        # Interactive mode
        interactive_loop()


if __name__ == "__main__":
    main()
