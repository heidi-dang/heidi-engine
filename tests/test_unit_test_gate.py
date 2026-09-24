import importlib
import tempfile
import concurrent.futures
import os

gate = importlib.import_module("scripts.03_unit_test_gate")


def test_python_code_indentation():
    with tempfile.TemporaryDirectory() as tmp_dir:
        code = (
            "def calculate_val(x):\n"
            "    val = x * 10\n"
            "    return val\n\n"
            "res = calculate_val(5)\n"
            "print(f'VAL:{res}')"
        )
        passed, stdout, stderr = gate.test_python_code(code, tmp_dir)
        assert passed is True
        assert "VAL:50" in stdout


def test_unit_test_gate_parallel():
    with tempfile.TemporaryDirectory() as base_temp_dir:
        samples = [
            {
                "id": f"sample_{i}",
                "output": (
                    "Here is the implementation:\n\n"
                    "```python\n"
                    "def process_data(val):\n"
                    f"    res = val + {i}\n"
                    "    return res\n\n"
                    "print(process_data(10))\n"
                    "```"
                ),
            }
            for i in range(10)
        ]

        def _worker(item):
            idx, sample_item = item
            sample_temp_dir = os.path.join(base_temp_dir, f"sample_{idx}")
            os.makedirs(sample_temp_dir, exist_ok=True)
            res = gate.test_sample(sample_item, sample_temp_dir, 5)
            return idx, res

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(_worker, enumerate(samples)))

        results.sort(key=lambda x: x[0])
        tested_samples = [res[1] for res in results]

        assert len(tested_samples) == 10
        for i, sample in enumerate(tested_samples):
            assert sample["id"] == f"sample_{i}"
            assert sample["test_result"]["passed"] is True
            assert sample["test_result"]["blocks_tested"] == 1
