import json
import os
import time
import subprocess
import tempfile

def create_mock_data(num_samples=100):
    samples = []
    for i in range(num_samples):
        # Alternate between passing and failing samples
        if i % 2 == 0:
            output = f"Here is some code:\n```python\ndef test_{i}():\n    return {i}\nprint(test_{i}())\n```"
        else:
            output = f"Here is some broken code:\n```python\ndef test_{i}():\n    return {i} + undefined_var\nprint(test_{i}())\n```"

        samples.append({
            "id": f"sample_{i}",
            "instruction": f"Instruction {i}",
            "input": f"Input {i}",
            "output": output,
            "metadata": {"task_type": "code_completion"}
        })
    return samples

def run_benchmark():
    num_samples = 100
    samples = create_mock_data(num_samples)

    with tempfile.TemporaryDirectory() as tmp_dir:
        input_path = os.path.join(tmp_dir, "input.jsonl")
        output_path = os.path.join(tmp_dir, "output.jsonl")

        with open(input_path, "w") as f:
            for s in samples:
                f.write(json.dumps(s) + "\n")

        print(f"Benchmarking 03_unit_test_gate.py with {num_samples} samples...")

        start_time = time.time()
        result = subprocess.run(
            ["python3", "scripts/03_unit_test_gate.py", "--input", input_path, "--output", output_path],
            capture_output=True,
            text=True
        )
        end_time = time.time()

        duration = end_time - start_time
        print(f"Duration: {duration:.2f} seconds")
        print(f"Throughput: {num_samples / duration:.2f} samples/sec")

        if result.returncode == 0:
            print("Execution successful")
            # Verify results
            with open(output_path, "r") as f:
                output_samples = [json.loads(line) for line in f]

            passed = sum(1 for s in output_samples if s["test_result"]["passed"])
            failed = sum(1 for s in output_samples if not s["test_result"]["passed"])
            print(f"Passed: {passed}, Failed: {failed}")

            if passed == 50 and failed == 50:
                print("Verification PASSED: Correct number of passed/failed samples.")
            else:
                print(f"Verification FAILED: Expected 50/50, got {passed}/{failed}")
        else:
            print("Execution FAILED")
            print(result.stderr)

if __name__ == "__main__":
    run_benchmark()
