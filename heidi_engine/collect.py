import argparse
import sys
import time

from heidi_engine.loop_runner import PythonLoopRunner


def main():
    parser = argparse.ArgumentParser(description="Heidi Engine - Data Collection and Orchestration")
    parser.add_argument("--mode", default="collect", choices=["collect", "full"],
                      help="Operation mode: 'collect' for generation/validation only, 'full' for complete pipeline.")
    parser.add_argument("--rounds", type=int, default=None, help="Number of rounds to run")
    parser.add_argument("--samples", type=int, default=None, help="Samples per round")

    args = parser.parse_args()

    # PythonLoopRunner reads from environment variables, but we can also set them or pass args if we modify it.
    # For now, we'll set the environment variables if provided.
    import os
    if args.rounds is not None:
        os.environ["ROUNDS"] = str(args.rounds)
    if args.samples is not None:
        os.environ["SAMPLES_PER_ROUND"] = str(args.samples)

    runner = PythonLoopRunner()

    print(f"[INFO] Starting Heidi Engine in {args.mode} mode...")
    runner.start(mode=args.mode)

    try:
        while True:
            status = runner.tick()
            if status["state"] in ["IDLE", "ERROR"]:
                if status["state"] == "ERROR":
                    print("[ERROR] Pipeline failed.")
                    sys.exit(1)
                break
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n[INFO] Shutdown requested...")
        runner.shutdown()
        sys.exit(0)

if __name__ == "__main__":
    main()
