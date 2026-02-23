# OpenHei Teacher Backend

Heidi Engine can use OpenHei as a "teacher" to generate supervised samples by running:

`openhei run --format json ...`

and parsing the JSONL event stream.

## Install + auth

- Install OpenHei and ensure `openhei` is on `PATH`.
- Log in with: `openhei auth login`

## Optional: headless server attach

If you want a persistent server:

- Start server: `openhei serve --hostname 127.0.0.1 --port 4096`
- Set attach URL: `export OPENHEI_ATTACH='http://127.0.0.1:4096'`

## Run the repo loop using OpenHei

Environment:

- `export TEACHER_BACKEND=openhei`
- `export TEACHER_MODEL='openai/gpt-5-mini'`  (must be `provider/model`)
- Optional: `export OPENHEI_AGENT=build`  (must be a primary agent; do not use subagents like `general`)

Example (collect mode across repos):

`./scripts/loop_repos.sh --stack python --max 50 --rounds 2 --samples 25 --collect --resume --dedupe`

Notes:

- No API keys are required in the heidi-engine environment; OpenHei manages credentials.
- The teacher must return strict JSON with keys `instruction`, `input`, `output`.
- `--samples` is per repo per round (it is not a global total).

## Local smoke

Single run inside a repo directory (uses `OUT_DIR` as repo dir):

`OUT_DIR="$PWD" TEACHER_BACKEND=openhei TEACHER_MODEL='openai/gpt-5-mini' python3 scripts/01_teacher_generate.py --samples 1 --output /tmp/out.jsonl`
