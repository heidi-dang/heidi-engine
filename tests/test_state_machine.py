#!/usr/bin/env python3
"""
Tests for heidi_engine/state_machine.py
"""

import os
import pytest
import tempfile
import shutil
import uuid
from pathlib import Path

# Set test directory BEFORE importing state_machine
TEST_DIR = tempfile.mkdtemp()
os.environ["AUTOTRAIN_DIR"] = TEST_DIR


def setup_module(module):
    pass


def teardown_module(module):
    shutil.rmtree(TEST_DIR, ignore_errors=True)


class TestStateMachineEnums:
    def test_mode_enum(self):
        from heidi_engine.state_machine import Mode

        assert Mode.IDLE.name == "IDLE"
        assert Mode.COLLECT.name == "COLLECT"
        assert Mode.TRAIN.name == "TRAIN"

    def test_phase_enum(self):
        from heidi_engine.state_machine import Phase

        assert Phase.INITIALIZING.name == "INITIALIZING"
        assert Phase.GENERATING.name == "GENERATING"
        assert Phase.COMPLETE.name == "COMPLETE"
        assert Phase.ERROR.name == "ERROR"

    def test_status_enum(self):
        from heidi_engine.state_machine import Status

        assert Status.IDLE.name == "IDLE"
        assert Status.RUNNING.name == "RUNNING"
        assert Status.COMPLETED.name == "COMPLETED"

    def test_event_enum(self):
        from heidi_engine.state_machine import Event

        assert Event.START_FULL.name == "START_FULL"
        assert Event.TRAIN_NOW.name == "TRAIN_NOW"
        assert Event.REQUEST_STOP.name == "REQUEST_STOP"


class TestStateMachineTransitions:
    def test_initial_to_generating(self):
        import uuid
        from heidi_engine.state_machine import StateMachine, Event

        sm = StateMachine(run_id=f"test-init-{uuid.uuid4().hex[:8]}")
        new_phase = sm.apply(Event.START_FULL)
        assert new_phase.name == "GENERATING"

    def test_generating_to_validating(self):
        import uuid
        from heidi_engine.state_machine import StateMachine, Event

        sm = StateMachine(run_id=f"test-gen-{uuid.uuid4().hex[:8]}")
        sm.apply(Event.START_FULL)
        new_phase = sm.apply(Event.STAGE_COMPLETE)
        assert new_phase.name == "VALIDATING"

    def test_illegal_transition(self):
        import uuid
        from heidi_engine.state_machine import StateMachine, Event

        sm = StateMachine(run_id=f"test-illegal-{uuid.uuid4().hex[:8]}")
        with pytest.raises(ValueError) as exc_info:
            sm.apply(Event.PIPELINE_COMPLETE)
        assert "Illegal transition" in str(exc_info.value)

    def test_stop_from_any_phase(self):
        import uuid
        from heidi_engine.state_machine import StateMachine, Event

        sm = StateMachine(run_id=f"test-stop-{uuid.uuid4().hex[:8]}")
        sm.apply(Event.START_FULL)
        sm.apply(Event.REQUEST_STOP)
        assert sm.get_state()["stop_requested"] is True


class TestCollectModeGating:
    def test_collect_mode_blocks_training(self):
        import uuid
        from heidi_engine.state_machine import StateMachine, Mode, Event

        sm = StateMachine(run_id=f"test-collect-{uuid.uuid4().hex[:8]}")
        sm.set_mode(Mode.COLLECT)
        sm.apply(Event.START_COLLECT)
        assert sm.can_train() is False

    def test_collect_mode_allows_training_at_complete(self):
        import uuid
        from heidi_engine.state_machine import StateMachine, Mode, Event

        sm = StateMachine(run_id=f"test-collect-{uuid.uuid4().hex[:8]}")
        sm.set_mode(Mode.COLLECT)
        sm.apply(Event.START_COLLECT)
        # Complete the pipeline
        for _ in range(5):
            sm.apply(Event.STAGE_COMPLETE)
        assert sm.can_train() is True

    def test_train_now_rejected_in_collect_mode(self):
        import uuid
        from heidi_engine.state_machine import StateMachine, Mode, Event

        sm = StateMachine(run_id=f"test-train-{uuid.uuid4().hex[:8]}")
        sm.set_mode(Mode.COLLECT)
        sm.apply(Event.START_COLLECT)
        with pytest.raises(ValueError) as exc_info:
            sm.apply(Event.TRAIN_NOW)
        assert "Illegal transition" in str(exc_info.value)


class TestCrashResume:
    def test_state_persisted(self):
        from heidi_engine.state_machine import StateMachine, Event

        run_id = f"test-persist-{uuid.uuid4().hex[:8]}"
        sm = StateMachine(run_id=run_id, autotrain_dir=Path(TEST_DIR))
        sm.apply(Event.START_FULL)
        sm.apply(Event.STAGE_COMPLETE)
        state = sm.get_state()

        # Verify file exists
        state_file = Path(TEST_DIR) / "runs" / run_id / "state.json"
        assert state_file.exists()

        # Resume and verify
        sm2 = StateMachine(run_id=run_id, autotrain_dir=Path(TEST_DIR))
        assert sm2.get_phase().name == sm.get_phase().name

    def test_crash_resume_idempotence(self):
        from heidi_engine.state_machine import StateMachine, Event

        run_id = f"test-idempotent-{uuid.uuid4().hex[:8]}"

        # First run
        sm = StateMachine(run_id=run_id, autotrain_dir=Path(TEST_DIR))
        sm.apply(Event.START_FULL)
        sm.apply(Event.STAGE_COMPLETE)
        phase_before = sm.get_phase().name
        round_before = sm.get_state()["current_round"]

        # Simulate crash - create new instance
        sm2 = StateMachine(run_id=run_id, autotrain_dir=Path(TEST_DIR))

        # Verify same state
        assert sm2.get_phase().name == phase_before
        assert sm2.get_state()["current_round"] == round_before


class TestCanonicalPath:
    def test_canonical_autotrain_dir(self):
        from heidi_engine.state_machine import CANONICAL_AUTOTRAIN_DIR

        assert str(CANONICAL_AUTOTRAIN_DIR) == str(Path.home() / ".local" / "heidi-engine")

    def test_resolve_path(self):
        from heidi_engine.state_machine import resolve_path, CANONICAL_AUTOTRAIN_DIR

        result = resolve_path("runs/test")
        assert result == CANONICAL_AUTOTRAIN_DIR / "runs" / "test"


class TestCountersAndUsage:
    def test_update_counters(self):
        import uuid
        from heidi_engine.state_machine import StateMachine

        sm = StateMachine(run_id=f"test-counters-{uuid.uuid4().hex[:8]}")
        sm.update_counters({"teacher_generated": 10, "raw_written": 5})
        counters = sm.get_state()["counters"]
        assert counters["teacher_generated"] == 10
        assert counters["raw_written"] == 5

    def test_update_counters_delta(self):
        import uuid
        from heidi_engine.state_machine import StateMachine

        sm = StateMachine(run_id=f"test-delta-{uuid.uuid4().hex[:8]}")
        sm.update_counters({"teacher_generated": 10})
        sm.update_counters({"teacher_generated": 5})
        counters = sm.get_state()["counters"]
        assert counters["teacher_generated"] == 15

    def test_update_usage(self):
        import uuid
        from heidi_engine.state_machine import StateMachine

        sm = StateMachine(run_id=f"test-usage-{uuid.uuid4().hex[:8]}")
        sm.update_usage({"requests_sent": 1, "input_tokens": 100})
        usage = sm.get_state()["usage"]
        assert usage["requests_sent"] == 1
        assert usage["input_tokens"] == 100
