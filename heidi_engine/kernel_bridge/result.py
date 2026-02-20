"""
Kernel Bridge Result Types

Result types and status enums for kernel bridge operations.
"""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel


class KernelBridgeStatus(Enum):
    """Status of kernel bridge operation."""
    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    INVALID_REQUEST = "invalid_request"


class KernelBridgeResult(BaseModel):
    """Result from kernel bridge operation."""
    
    status: KernelBridgeStatus
    success: bool
    reason: Optional[str] = None
    latency_ms: Optional[int] = None
    payload_size: Optional[int] = None
    payload: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    retry_count: int = 0
    
    @classmethod
    def success_result(cls, payload: Optional[Dict[str, Any]] = None, 
                       latency_ms: Optional[int] = None) -> 'KernelBridgeResult':
        """Create a successful result."""
        return cls(
            status=KernelBridgeStatus.OK,
            success=True,
            payload=payload,
            latency_ms=latency_ms,
            payload_size=len(str(payload).encode()) if payload else 0
        )
    
    @classmethod
    def error_result(cls, reason: str, error_code: Optional[str] = None,
                     latency_ms: Optional[int] = None,
                     retry_count: int = 0) -> 'KernelBridgeResult':
        """Create an error result."""
        return cls(
            status=KernelBridgeStatus.ERROR,
            success=False,
            reason=reason,
            error_code=error_code,
            latency_ms=latency_ms,
            retry_count=retry_count
        )
    
    @classmethod
    def timeout_result(cls, latency_ms: Optional[int] = None,
                       retry_count: int = 0) -> 'KernelBridgeResult':
        """Create a timeout result."""
        return cls(
            status=KernelBridgeStatus.TIMEOUT,
            success=False,
            reason="Request timed out",
            latency_ms=latency_ms,
            retry_count=retry_count
        )
    
    @classmethod
    def unavailable_result(cls, reason: str = "Kernel bridge unavailable") -> 'KernelBridgeResult':
        """Create an unavailable result."""
        return cls(
            status=KernelBridgeStatus.UNAVAILABLE,
            success=False,
            reason=reason
        )
