#!/usr/bin/env python3
"""
heidi_engine/state_machine.py - Finite State Machine for AutoTraining Pipeline

PURPOSE:
    Explicit FSM with legal transitions, persisted state, and single writer.
    Replaces ad-hoc state mutations with structured event-driven transitions.

AUTOTRAIN_DIR: ~/.local/heidi-engine (canonical path - MUST NOT default to ./heidi_engine)
"""

import json
import os
import stat
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, Optional, Set
from datetime import datetime, timezone


CANONICAL_AUTOTRAIN_DIR = Path("~/.local/heidi-engine").expanduser()


class Mode(Enum):
    """Operating mode of the pipeline."""

    IDLE = auto()
    COLLECT = auto()
    TRAIN = auto()


class Phase(Enum):
    """Pipeline phase/stage."""

    INITIALIZING = auto()
    GENERATING = auto()
    VALIDATING = auto()
    TESTING = auto()
    TRAINING = auto()
    EVALUATING = auto()
    COMPLETE = auto()
    ERROR = auto()


class Status(Enum):
    """Run status."""

    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    STOPPED = auto()
    COMPLETED = auto()
    ERROR = auto()


class Event(Enum):
    """State machine events."""

    START_FULL = auto()
    START_COLLECT = auto()
    TRAIN_NOW = auto()
    REQUEST_PAUSE = auto()
    REQUEST_RESUME = auto()
    REQUEST_STOP = auto()
    STAGE_COMPLETE = auto()
    ROUND_COMPLETE = auto()
    PIPELINE_COMPLETE = auto()
    ERROR = auto()


PHASE_TRANSITIONS: Dict[Phase, Dict[Event, Phase]] = {
    Phase.INITIALIZING: {
        Event.START_FULL: Phase.GENERATING,
        Event.START_COLLECT: Phase.GENERATING,
    },
    Phase.GENERATING: {
        Event.STAGE_COMPLETE: Phase.VALIDATING,
        Event.REQUEST_STOP: Phase.COMPLETE,
    },
    Phase.VALIDATING: {
        Event.STAGE_COMPLETE: Phase.TESTING,
        Event.REQUEST_STOP: Phase.COMPLETE,
    },
    Phase.TESTING: {
        Event.STAGE_COMPLETE: Phase.TRAINING,
        Event.REQUEST_STOP: Phase.COMPLETE,
    },
    Phase.TRAINING: {
        Event.STAGE_COMPLETE: Phase.EVALUATING,
        Event.REQUEST_STOP: Phase.COMPLETE,
    },
    Phase.EVALUATING: {
        Event.STAGE_COMPLETE: Phase.COMPLETE,  # Final round complete
        Event.ROUND_COMPLETE: Phase.GENERATING,  # More rounds to go
        Event.PIPELINE_COMPLETE: Phase.COMPLETE,
        Event.REQUEST_STOP: Phase.COMPLETE,
    },
    Phase.COMPLETE: {
        Event.START_FULL: Phase.INITIALIZING,
        Event.START_COLLECT: Phase.INITIALIZING,
        Event.TRAIN_NOW: Phase.TRAINING,  # Train now with collected data
    },
    Phase.ERROR: {
        Event.START_FULL: Phase.INITIALIZING,
        Event.START_COLLECT: Phase.INITIALIZING,
    },
}


COLLECT_MODE_GATES: Set[Phase] = {
    Phase.TRAINING,
}


class StateMachine:
    """
    Finite State Machine with persisted state.

    Single writer for all state mutations - telemetry.py should call this,
    not mutate state directly.
    """

    def __init__(self, run_id: Optional[str] = None, autotrain_dir: Optional[Path] = None):
        self.autotrain_dir = autotrain_dir or CANONICAL_AUTOTRAIN_DIR
        self.run_id = run_id or self._generate_run_id()

        self._state: Dict[str, Any] = {}
        self._load_or_init()

    def _generate_run_id(self) -> str:
        import uuid

        return f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

    def _get_run_dir(self) -> Path:
        return self.autotrain_dir / "runs" / self.run_id

    def _get_state_path(self) -> Path:
        return self._get_run_dir() / "state.json"

    def _load_or_init(self) -> None:
        state_file = self._get_state_path()
        if state_file.exists():
            try:
                with open(state_file) as f:
                    self._state = json.load(f)
                self.run_id = self._state.get("run_id", self.run_id)
            except (json.JSONDecodeError, IOError):
                self._initialize_default()
        else:
            self._initialize_default()

    def _initialize_default(self) -> None:
        self._state = {
            "run_id": self.run_id,
            "mode": Mode.IDLE.name,
            "phase": Phase.INITIALIZING.name,
            "status": Status.IDLE.name,
            "current_round": 0,
            "stop_requested": False,
            "pause_requested": False,
            "counters": self._default_counters(),
            "usage": self._default_usage(),
            "last_event": None,
            "last_transition": None,
            "started_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        }
        self._persist()

    def _default_counters(self) -> Dict[str, Any]:
        return {
            "teacher_generated": 0,
            "teacher_failed": 0,
            "raw_written": 0,
            "validated_ok": 0,
            "rejected_schema": 0,
            "rejected_secret": 0,
            "rejected_dedupe": 0,
            "test_pass": 0,
            "test_fail": 0,
            "train_step": 0,
            "train_loss": 0.0,
            "eval_json_parse_rate": 0.0,
            "eval_format_rate": 0.0,
        }

    def _default_usage(self) -> Dict[str, Any]:
        return {
            "requests_sent": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "rate_limits_hit": 0,
            "retries": 0,
            "estimated_cost_usd": 0.0,
        }

    def _persist(self) -> None:
        state_file = self._get_state_path()
        state_file.parent.mkdir(parents=True, exist_ok=True)

        temp_file = state_file.with_suffix(".tmp")
        self._state["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        with open(temp_file, "w") as f:
            json.dump(self._state, f, indent=2)

        os.replace(temp_file, state_file)
        os.chmod(state_file, stat.S_IRUSR | stat.S_IWUSR)

    def get_phase(self) -> Phase:
        return Phase[self._state.get("phase", Phase.INITIALIZING.name)]

    def get_status(self) -> Status:
        return Status[self._state.get("status", Status.IDLE.name)]

    def get_mode(self) -> Mode:
        return Mode[self._state.get("mode", Mode.IDLE.name)]

    def get_state(self) -> Dict[str, Any]:
        return self._state.copy()

    def apply(self, event: Event, **kwargs) -> Phase:
        """
        Apply an event and transition to new phase.

        Returns new phase or raises ValueError if transition is illegal.
        """
        current_phase = self.get_phase()

        if event == Event.TRAIN_NOW:
            mode = self.get_mode()
            if mode == Mode.COLLECT and current_phase not in {Phase.COMPLETE, Phase.INITIALIZING}:
                if current_phase in COLLECT_MODE_GATES:
                    raise ValueError(f"Cannot TRAIN_NOW from {current_phase.name} in COLLECT mode")

        if event == Event.REQUEST_STOP:
            self._state["stop_requested"] = True
            self._state["status"] = Status.STOPPED.name
            self._persist()
            return current_phase

        if event == Event.REQUEST_PAUSE:
            self._state["pause_requested"] = True
            self._state["status"] = Status.PAUSED.name
            self._persist()
            return current_phase

        if event == Event.REQUEST_RESUME:
            self._state["pause_requested"] = False
            self._state["status"] = Status.RUNNING.name
            self._persist()
            return current_phase

        if event == Event.ERROR:
            self._state["phase"] = Phase.ERROR.name
            self._state["status"] = Status.ERROR.name
            self._persist()
            return Phase.ERROR

        transitions = PHASE_TRANSITIONS.get(current_phase, {})
        new_phase = transitions.get(event)

        if new_phase is None:
            raise ValueError(f"Illegal transition: {event.name} from {current_phase.name}")

        self._state["phase"] = new_phase.name
        self._state["last_event"] = event.name
        self._state["last_transition"] = f"{current_phase.name} -> {new_phase.name}"

        if new_phase == Phase.COMPLETE:
            self._state["status"] = Status.COMPLETED.name
        elif new_phase == Phase.ERROR:
            self._state["status"] = Status.ERROR.name
        else:
            self._state["status"] = Status.RUNNING.name

        self._persist()
        return new_phase

    def set_mode(self, mode: Mode) -> None:
        self._state["mode"] = mode.name
        self._persist()

    def increment_round(self) -> int:
        self._state["current_round"] = self._state.get("current_round", 0) + 1
        self._persist()
        return self._state["current_round"]

    def update_counters(self, delta: Dict[str, Any]) -> None:
        counters = self._state.get("counters", self._default_counters())
        for key, value in delta.items():
            if key in counters:
                if key == "train_loss":
                    counters[key] = float(value)
                else:
                    counters[key] += int(value)
        self._state["counters"] = counters
        self._persist()

    def update_usage(self, delta: Dict[str, Any]) -> None:
        usage = self._state.get("usage", self._default_usage())
        for key, value in delta.items():
            if key in usage:
                usage[key] += int(value) if isinstance(usage[key], int) else float(value)
        self._state["usage"] = usage
        self._persist()

    def can_train(self) -> bool:
        """Check if training is allowed in current mode/phase."""
        mode = self.get_mode()
        phase = self.get_phase()

        if mode == Mode.TRAIN:
            return True
        if mode == Mode.COLLECT:
            return phase in {Phase.COMPLETE, Phase.INITIALIZING}
        return False

    def validate(self) -> bool:
        """Validate state schema."""
        required = {"run_id", "mode", "phase", "status", "current_round"}
        return required.issubset(self._state.keys())


def get_autotrain_dir() -> Path:
    """Get canonical AUTOTRAIN_DIR."""
    return CANONICAL_AUTOTRAIN_DIR


def resolve_path(rel_path: str) -> Path:
    """Resolve relative path against canonical AUTOTRAIN_DIR."""
    return CANONICAL_AUTOTRAIN_DIR / rel_path
