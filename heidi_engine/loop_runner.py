import os
import sys
import json
import time
import subprocess
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from heidi_engine import telemetry


class LoopRunner(ABC):
    """
    Abstract interface for the Heidi Engine autonomous loop.
    This defines the contract that both the Python and C++ implementations must fulfill.
    """

    @abstractmethod
    def start(self, mode: str = "full") -> None:
        """Start the loop in the given mode ('full' or 'collect')."""
        pass

    @abstractmethod
    def tick(self, max_steps: int = 1) -> Dict[str, Any]:
        """Perform one state machine transition or step."""
        pass

    @abstractmethod
    def pause(self) -> None:
        """Request the loop to pause at the next boundary."""
        pass

    @abstractmethod
    def resume(self) -> None:
        """Resume a paused loop."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Gracefully shut down the loop."""
        pass

    @abstractmethod
    def action_train_now(self) -> None:
        """Trigger an immediate training run (if in collect mode)."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get the current state machine status."""
        pass


class PythonLoopRunner(LoopRunner):
    """
    Python implementation of the LoopRunner, orchestrating the existing CLI scripts.
    """

    def __init__(self, config_path: Optional[str] = None):
        # We simulate reading from config or environment variables
        self.config_path = config_path
        self.out_dir = Path(os.environ.get("OUT_DIR", os.path.expanduser("~/.local/heidi_engine")))
        self.rounds = int(os.environ.get("ROUNDS", 3))
        self.samples_per_round = int(os.environ.get("SAMPLES_PER_ROUND", 50))
        self.run_unit_tests = os.environ.get("RUN_UNIT_TESTS", "0") == "1"

        self.current_state = "IDLE"
        self.current_round = 0
        self.run_id = os.environ.get("RUN_ID")

        self.stop_requested = False
        self.pause_requested = False
        self.mode = "full"

        # Initialize telemetry if run_id is provided or via init_telemetry logic
        if self.run_id:
            telemetry.init_telemetry(self.run_id)

    def _set_state(self, new_state: str, stage: str = ""):
        self.current_state = new_state
        if new_state != "IDLE" and new_state != "ERROR":
            telemetry.set_status("running", stage, self.current_round)
        elif new_state == "IDLE":
            telemetry.set_status("completed", "complete", self.current_round)

    def _check_interrupts(self) -> bool:
        """Return True if we should stop."""
        if self.stop_requested or telemetry.check_stop_requested(self.run_id):
            telemetry.emit_event("pipeline_stop", "Stop requested by user", "pipeline", self.current_round)
            telemetry.set_status("stopped", self.current_state, self.current_round)
            self.current_state = "IDLE"
            return True

        while self.pause_requested or telemetry.check_pause_requested(self.run_id):
            time.sleep(1)

        return False

    def start(self, mode: str = "full") -> None:
        self.mode = mode
        self.current_round = 1
        self.stop_requested = False
        self.pause_requested = False
        telemetry.emit_event("pipeline_start", "Starting training pipeline", "pipeline", 0)
        self._set_state("COLLECTING", stage="initializing")

    def tick(self, max_steps: int = 1) -> Dict[str, Any]:
        if self.current_state == "IDLE" or self.current_state == "ERROR":
            return self.get_status()

        if self._check_interrupts():
            return self.get_status()

        if self.current_state == "COLLECTING":
            telemetry.emit_event("round_start", f"Starting round {self.current_round}", "round", self.current_round)
            telemetry.emit_event("stage_start", "Starting teacher generation", "generate", self.current_round)
            
            # Here we simulate the bash script calling 01_teacher_generate.py
            output_file = self.out_dir / "data" / f"raw_round_{self.current_round}.jsonl"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            cmd = [
                sys.executable, str(Path(__file__).parent.parent / "scripts" / "01_teacher_generate.py"),
                "--samples", str(self.samples_per_round),
                "--output", str(output_file),
                "--round", str(self.current_round)
            ]
            self._run_cmd(cmd, "Teacher generation failed")

            telemetry.emit_event("stage_end", f"Generated {self.samples_per_round} samples", "generate", self.current_round)
            self._set_state("VALIDATING", stage="validate")

        elif self.current_state == "VALIDATING":
            telemetry.emit_event("stage_start", "Starting validation", "validate", self.current_round)
            
            input_file = self.out_dir / "data" / f"raw_round_{self.current_round}.jsonl"
            output_file = self.out_dir / "data" / f"clean_round_{self.current_round}.jsonl"
            
            cmd = [
                sys.executable, str(Path(__file__).parent.parent / "scripts" / "02_validate_clean.py"),
                "--input", str(input_file),
                "--output", str(output_file)
            ]
            self._run_cmd(cmd, "Validation failed")
            
            telemetry.emit_event("stage_end", "Validated samples", "validate", self.current_round)
            
            if self.run_unit_tests:
                self._set_state("TESTING", stage="test")
            else:
                if self.mode == "full":
                    self._set_state("FINALIZING", stage="train")
                else:
                    self._set_state("IDLE") # Wait for train-now or next step

        elif self.current_state == "TESTING":
            telemetry.emit_event("stage_start", "Starting unit tests", "test", self.current_round)
            
            input_file = self.out_dir / "data" / f"clean_round_{self.current_round}.jsonl"
            output_file = self.out_dir / "data" / f"tested_round_{self.current_round}.jsonl"
            
            cmd = [
                sys.executable, str(Path(__file__).parent.parent / "scripts" / "03_unit_test_gate.py"),
                "--input", str(input_file),
                "--output", str(output_file)
            ]
            self._run_cmd(cmd, "Unit test gate failed")
            
            telemetry.emit_event("stage_end", "Completed unit tests", "test", self.current_round)
            
            if self.mode == "full":
                self._set_state("FINALIZING", stage="train")
            else:
                self._set_state("IDLE")

        elif self.current_state == "FINALIZING":
            telemetry.emit_event("stage_start", "Starting training", "train", self.current_round)
            
            # Simplification: split logic and training script simulation
            train_file = self.out_dir / "data" / f"train_round_{self.current_round}.jsonl"
            val_file = self.out_dir / "data" / f"val_round_{self.current_round}.jsonl"
            output_dir = self.out_dir / f"out_lora_round_{self.current_round}"
            
            # In a real run, split occurs here, and then 04_train_qlora.py is called. 
            # We assume it succeeds for the sake of orchestrating.
            # In tests, we mock this.
            self._mock_split(train_file, val_file)
            
            cmd = [
                sys.executable, str(Path(__file__).parent.parent / "scripts" / "04_train_qlora.py"),
                "--data", str(train_file),
                "--val-data", str(val_file),
                "--output", str(output_dir)
            ]
            self._run_cmd(cmd, "Training failed")
            
            telemetry.emit_event("stage_end", "Training complete", "train", self.current_round)
            self._set_state("EVALUATING", stage="eval")

        elif self.current_state == "EVALUATING":
            telemetry.emit_event("stage_start", "Starting evaluation", "eval", self.current_round)
            
            val_file = self.out_dir / "data" / f"val_round_{self.current_round}.jsonl"
            adapter_dir = self.out_dir / f"out_lora_round_{self.current_round}" / "final"
            report_file = self.out_dir / "eval" / f"report_round_{self.current_round}.json"
            
            cmd = [
                sys.executable, str(Path(__file__).parent.parent / "scripts" / "05_eval.py"),
                "--adapter", str(adapter_dir),
                "--data", str(val_file),
                "--output", str(report_file)
            ]
            self._run_cmd(cmd, "Evaluation failed", check=False) # Eval can fail gracefully
            
            telemetry.emit_event("stage_end", "Evaluation complete", "eval", self.current_round)
            
            if self.current_round < self.rounds:
                self.current_round += 1
                self._set_state("COLLECTING", stage="generate")
            else:
                telemetry.emit_event("pipeline_complete", "Training pipeline finished", "pipeline", self.rounds)
                self._set_state("IDLE", stage="complete")

        return self.get_status()

    def _run_cmd(self, cmd: list, err_msg: str, check: bool = True):
        # We allow tests to mock subprocess.run, but here is the real invocation
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=check)
            return res
        except subprocess.CalledProcessError as e:
            msg = f"{err_msg}: {e.stderr}"
            telemetry.emit_event("pipeline_error", msg, "pipeline", self.current_round)
            self.current_state = "ERROR"
            raise RuntimeError(msg)
            
    def _mock_split(self, train_file: Path, val_file: Path):
        """Simplistic split for the orchestrator simulation if files don't exist"""
        if not train_file.exists():
            train_file.parent.mkdir(parents=True, exist_ok=True)
            train_file.touch()
        if not val_file.exists():
            val_file.parent.mkdir(parents=True, exist_ok=True)
            val_file.touch()

    def pause(self) -> None:
        self.pause_requested = True

    def resume(self) -> None:
        self.pause_requested = False

    def shutdown(self) -> None:
        self.stop_requested = True

    def action_train_now(self) -> None:
        if self.mode == "collect" and self.current_state == "IDLE":
            # Jump to training with the current data
            self._set_state("FINALIZING", stage="train")

    def get_status(self) -> Dict[str, Any]:
        return {
            "state": self.current_state,
            "round": self.current_round,
            "mode": self.mode,
            "run_id": self.run_id
        }

try:
    import heidi_cpp

    class CppLoopRunner(LoopRunner):
        """
        C++ implementation of the LoopRunner, wrapping the heidi_cpp.Core extension.
        """
        def __init__(self, config_path: Optional[str] = None):
            self.config_path = config_path
            self.core = heidi_cpp.Core()
            self.core.init(config_path or "")

        def start(self, mode: str = "full") -> None:
            self.core.start(mode)

        def tick(self, max_steps: int = 1) -> Dict[str, Any]:
            status_json = self.core.tick(max_steps)
            return json.loads(status_json)

        def pause(self) -> None:
            pass # P2 does not have pause yet natively 

        def resume(self) -> None:
            pass

        def shutdown(self) -> None:
            self.core.shutdown()

        def action_train_now(self) -> None:
            self.core.action_train_now()

        def get_status(self) -> Dict[str, Any]:
            status_json = self.core.get_status_json()
            return json.loads(status_json)

except ImportError:
    # In Lane F, we make this explicit rather than silent. 
    # Python-only environments are allowed, but CppLoopRunner usage should fail hard if missing.
    class CppLoopRunner(LoopRunner):
        def __init__(self, *args, **kwargs):
            raise ImportError("heidi_cpp extension not found. C++ Hot-Path disabled.")
        def start(self, *args, **kwargs): pass
        def tick(self, *args, **kwargs): return {}
        def pause(self): pass
        def resume(self): pass
        def shutdown(self): pass
        def action_train_now(self): pass
        def get_status(self): return {}


if __name__ == "__main__":
    runner = PythonLoopRunner()
    runner.start()
    while runner.get_status()["state"] not in ["IDLE", "ERROR"]:
        runner.tick()
        time.sleep(0.1)
