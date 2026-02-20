"""
Kernel Bridge Result Types

Result types and status enums for kernel bridge operations.
"""

from enum import Enum
from typing import Any, Dict, Optional


class KernelBridgeStatus(Enum):
    """Status of kernel bridge operation."""
    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    INVALID_REQUEST = "invalid_request"


class KernelBridgeResult:
    """Result from kernel bridge operation."""
    
    def __init__(self, status: KernelBridgeStatus, success: bool, **kwargs):
        self.status = status
        self.success = success
        self.reason = kwargs.get('reason')
        self.latency_ms = kwargs.get('latency_ms')
        self.payload_size = kwargs.get('payload_size')
        self.payload = kwargs.get('payload')
        self.error_code = kwargs.get('error_code')
        self.retry_count = kwargs.get('retry_count', 0)
    
    @classmethod
    def success_result(cls, payload: Optional[Dict[str, Any]] = None, 
                       latency_ms: Optional[int] = None) -> 'KernelBridgeResult':
        """Create a successful result."""
        payload_size = len(str(payload).encode()) if payload else 0
        return cls(
            status=KernelBridgeStatus.OK,
            success=True,
            payload=payload,
            latency_ms=latency_ms,
            payload_size=payload_size
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
    
    def dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'status': self.status.value,
            'success': self.success,
            'reason': self.reason,
            'latency_ms': self.latency_ms,
            'payload_size': self.payload_size,
            'payload': self.payload,
            'error_code': self.error_code,
            'retry_count': self.retry_count
        }
