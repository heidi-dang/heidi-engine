import sys
import asyncio
import json
import logging
import os
import subprocess
import warnings
from typing import Optional

# Suppress deprecation warnings from SDK/dependencies
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Setup basic logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

try:
    from copilot import CopilotClient
except ImportError:
    print(json.dumps({"error": "copilot SDK not found"}))
    sys.exit(1)


async def generate(prompt: str, token: str = None, model: str = None):
    # Get token
    if not token:
        token = (
            os.environ.get("GITHUB_COPILOT_TOKEN")
            or os.environ.get("GH_TOKEN")
            or os.environ.get("GITHUB_PAT")
        )

    if not token:
        try:
            result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
            if result.returncode == 0:
                token = result.stdout.strip()
        except Exception:
            pass

    if not token:
        print(json.dumps({"error": "No GitHub token found."}))
        return

    # Debug print to stderr to avoid polluting stdout json
    # sys.stderr.write(f"DEBUG: Token present: {bool(token)}\n")

    options = {
        "github_token": token,
        "cli_path": "/home/heidi/.local/lib/python3.12/site-packages/copilot/bin/copilot"
    }
    
    # sys.stderr.write(f"DEBUG: ENV: {os.environ.keys()}\n")

    client = CopilotClient(options)

    try:
        # sys.stderr.write("DEBUG: Starting client...\n")
        await client.start()

        # sys.stderr.write("DEBUG: Creating session...\n")
        session = await client.create_session()

        # Important: use 'immediate' mode based on git-sdk.py behavior
        payload = {"prompt": prompt, "mode": "immediate"}

        # sys.stderr.write("DEBUG: Sending payload...\n")
        response = await session.send_and_wait(payload)

        content = ""
        if hasattr(response, "message"):
            content = response.message.content
        elif isinstance(response, dict):
            if "message" in response:
                content = response["message"].get("content", "")
            elif "content" in response:
                content = response["content"]
            else:
                content = str(response)  # fallback
        else:
            content = str(response)

        print(json.dumps({"content": content}))

    except Exception as e:
        print(json.dumps({"error": str(e)}))
    finally:
        try:
            await client.stop()
        except:
            pass


if __name__ == "__main__":
    if len(sys.argv) > 1:
        PROMPT = sys.argv[1]
    elif not sys.stdin.isatty():
        PROMPT = sys.stdin.read()
    else:
        PROMPT = "Hello"

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(generate(PROMPT))
    finally:
        loop.close()
