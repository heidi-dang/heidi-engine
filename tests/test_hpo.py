import os
import json
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.train_only import run_trial

class TestHPO(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path("./tmp_hpo_test")
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        self.train_file = self.tmp_dir / "train.jsonl"
        self.val_file = self.tmp_dir / "val.jsonl"
        
        with open(self.train_file, "w") as f:
            f.write('{"instruction": "test", "output": "test"}\n')
        with open(self.val_file, "w") as f:
            f.write('{"instruction": "test", "output": "test"}\n')

    def tearDown(self):
        import shutil
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)

    @patch("subprocess.run")
    @patch("heidi_engine.telemetry.emit_event")
    def test_run_trial_success(self, mock_emit, mock_run):
        # Mock trial object
        trial = MagicMock()
        trial.number = 0
        trial.suggest_float.return_value = 0.0001
        trial.suggest_categorical.return_value = 1
        trial.suggest_int.return_value = 32
        
        # Mock metrics file creation
        trial_out = self.tmp_dir / "trial_0"
        adapter_dir = trial_out / "adapter"
        adapter_dir.mkdir(parents=True, exist_ok=True)
        
        metrics = {"eval_loss": 0.5, "train_loss": 0.6}
        with open(adapter_dir / "metrics.json", "w") as f:
            json.dump(metrics, f)
            
        args = MagicMock()
        args.base_model = "test-model"
        args.steps = 10
        args.seq_len = 128
        args.seed = 42
        
        script_dir = Path(__file__).parent.parent / "scripts"
        
        loss = run_trial(trial, args, script_dir, self.tmp_dir, self.train_file, self.val_file)
        
        self.assertEqual(loss, 0.5)
        mock_run.assert_called_once()

    @patch("heidi_cpp.get_free_gpu_memory")
    def test_run_trial_low_vram(self, mock_gpu):
        # Mock low VRAM
        mock_gpu.return_value = 500 * 1024 * 1024 # 500MB
        
        trial = MagicMock()
        trial.number = 2
        
        args = MagicMock()
        script_dir = Path(__file__).parent.parent / "scripts"

        import optuna
        with self.assertRaises(optuna.TrialPruned):
            run_trial(trial, args, script_dir, self.tmp_dir, self.train_file, self.val_file)

    @patch("subprocess.run")
    def test_run_trial_failure(self, mock_run):
        trial = MagicMock()
        trial.number = 1
        trial.suggest_float.return_value = 0.0001
        trial.suggest_categorical.return_value = 1
        trial.suggest_int.return_value = 32
        
        # Simulate subprocess failure
        mock_run.side_effect = Exception("Crash")
        
        args = MagicMock()
        args.base_model = "test-model"
        args.steps = 10
        args.seq_len = 128
        args.seed = 42
        
        script_dir = Path(__file__).parent.parent / "scripts"
        
        loss = run_trial(trial, args, script_dir, self.tmp_dir, self.train_file, self.val_file)
        
        self.assertEqual(loss, float("inf"))

from scripts.train_only import hpo_callback

class TestHPOCallback(unittest.TestCase):
    @patch("heidi_engine.telemetry.emit_event")
    def test_hpo_callback(self, mock_emit):
        study = MagicMock()
        trial = MagicMock()
        
        # Case: New best trial
        study.best_trial = trial
        trial.number = 5
        trial.value = 0.42
        
        hpo_callback(study, trial)
        
        mock_emit.assert_called_once()
        args, kwargs = mock_emit.call_args
        self.assertEqual(kwargs["event_type"], "hpo_best")
        self.assertIn("0.4200", kwargs["message"])

if __name__ == "__main__":
    unittest.main()
