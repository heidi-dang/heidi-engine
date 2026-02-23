import json
from pathlib import Path


def test_pump_writes_ready_when_artifacts_exist(tmp_path, monkeypatch):
    # Arrange a run dir that already has the expensive artifacts.
    runs_dir = tmp_path / "runs"
    run_id = "run_test"
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    merged = run_dir / "merged_dataset.jsonl"
    merged.write_text(
        "{\"instruction\":\"a\",\"input\":\"b\",\"output\":\"c\"}\n"
        "{\"instruction\":\"d\",\"input\":\"e\",\"output\":\"f\"}\n",
        encoding="utf-8",
    )

    # adapter/final exists -> training skipped
    (run_dir / "adapter" / "final").mkdir(parents=True, exist_ok=True)

    # eval report exists -> eval skipped
    eval_dir = run_dir / "eval"
    eval_dir.mkdir(parents=True, exist_ok=True)
    report = eval_dir / "report.json"
    report.write_text(
        json.dumps({"metrics": {"success_rate": 1.0, "json_parse_rate": 1.0}}),
        encoding="utf-8",
    )

    from heidi_engine import pump

    rc = pump.main(
        [
            "--runs-dir",
            str(runs_dir),
            "--run-id",
            run_id,
            "--teacher-backend",
            "legacy",
        ]
    )
    assert rc == 0

    ready = run_dir / "READY.json"
    assert ready.exists()
    data = json.loads(ready.read_text(encoding="utf-8"))
    assert data["run_id"] == run_id
    assert Path(data["adapter_path"]).name == "final"
    assert data["dataset_lines"] == 2
