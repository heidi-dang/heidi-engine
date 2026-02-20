# HTTP API Reference

The engine exposes a local API for programmatic control.

## Endpoints

### GET /status
Returns the current state machine status.
**Response:**
```json
{
  "state": "COLLECTING",
  "round": 1,
  "mode": "collect",
  "run_id": "run_20240101_120000"
}
```

### POST /actions/train-now
Triggers an immediate training run using currently available verified data.
**Response:**
```json
{
  "status": "ok",
  "action": "train_now_triggered"
}
```
