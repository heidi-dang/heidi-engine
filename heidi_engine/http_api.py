from __future__ import annotations

from dataclasses import asdict
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

# Keep imports narrow and explicit to avoid circulars.
# Adjust these imports to match your actual module function names.
from heidi_engine.pipeline import get_status as pipeline_get_status
from heidi_engine.pipeline import check_health as pipeline_check_health

from heidi_engine.pipeline.receipt import (
    verify_receipt,
    export_receipt,
)

from heidi_engine.pipeline.trainer_firewall import VerificationStatus


MAX_RECEIPT_BYTES = 256 * 1024  # 256KB hard cap


class RateLimiter:
    """
    Tiny in-memory token bucket (per-process).
    Good enough for localhost to prevent accidental hammering.
    """

    def __init__(self, rate_per_sec: float = 5.0, burst: int = 10) -> None:
        import time

        self._time = time.monotonic
        self._rate = float(rate_per_sec)
        self._burst = int(burst)
        self._tokens = float(burst)
        self._last = self._time()

    def allow(self) -> bool:
        now = self._time()
        elapsed = max(0.0, now - self._last)
        self._last = now
        self._tokens = min(float(self._burst), self._tokens + elapsed * self._rate)
        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return True
        return False


limiter = RateLimiter()
app = FastAPI(title="heidi-engine verification API", version="0.2.x")


def _deny(status_code: int, reason: str, extra: Optional[dict[str, Any]] = None) -> JSONResponse:
    payload: dict[str, Any] = {"ok": False, "reason": reason}
    if extra:
        payload.update(extra)
    return JSONResponse(status_code=status_code, content=payload)


def _ok(payload: dict[str, Any]) -> JSONResponse:
    payload = {"ok": True, **payload}
    return JSONResponse(status_code=200, content=payload)


@app.middleware("http")
async def _rate_limit(request: Request, call_next):
    # Only rate-limit API routes (skip docs)
    if request.url.path.startswith("/v1/"):
        if not limiter.allow():
            return _deny(429, "rate_limited")
    return await call_next(request)


@app.get("/v1/health")
def health() -> dict[str, Any]:
    # Lightweight health probe
    return {"ok": True, "health": pipeline_check_health()}


@app.get("/v1/status")
def status() -> dict[str, Any]:
    # General engine status (includes firewall info via pipeline status if you added it)
    return {"ok": True, "status": pipeline_get_status()}


@app.get("/v1/runs/{run_id}/status")
def run_status(run_id: str) -> dict[str, Any]:
    # If you already have a run status accessor, call it here.
    # For now, return global status + firewall summary + requested run_id.
    return {
        "ok": True,
        "run_id": run_id,
        "status": pipeline_get_status(),
        "firewall": "firewall status placeholder",  # TODO: This is a placeholder implementation intentionally minimal for safety. Create an issue to fully implement and verify behavior.,
    }


@app.post("/v1/receipt/verify")
async def receipt_verify(
    request: Request,
    allow_unknown: bool = False,
    root: Optional[str] = None,
) -> JSONResponse:
    raw = await request.body()
    if len(raw) > MAX_RECEIPT_BYTES:
        return _deny(413, "payload_too_large")

    try:
        receipt_json = await request.json()
    except Exception:
        return _deny(400, "invalid_json")

    try:
        success, reason = verify_receipt(receipt_file=receipt_json, allow_unknown=allow_unknown)
    except HTTPException:
        raise
    except Exception as e:
        return _deny(400, "verification_error", {"detail": str(e)})

    if not success:
        return _deny(400, reason)

    return _ok({"message": reason})


@app.get("/v1/runs/{run_id}/receipt")
def run_receipt(
    run_id: str,
    persist: bool = False,
) -> JSONResponse:
    """
    Generate a signed receipt for a run_id.
    By default returns JSON only; persist=true may write to disk if your receipt module supports it.
    """
    try:
        success, message, receipt = export_receipt(
            output_dir=f"/data/runs/{run_id}", out_file=f"/data/receipts/{run_id}.receipt.json"
        )
        if not success:
            return _deny(400, "receipt_export_failed", {"detail": message})

        receipt_json = receipt.to_dict() if receipt else ""
    except Exception as e:
        return _deny(400, "receipt_export_failed", {"detail": str(e)})

    return _ok({"receipt": receipt_json})
