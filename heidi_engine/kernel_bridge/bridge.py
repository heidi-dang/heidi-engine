"""
Kernel Bridge Main Interface

Main entry point for kernel bridge communication.
"""

import time
import threading
from typing import Dict, Any, Optional
from .config import KernelBridgeConfig
from .result import KernelBridgeResult, KernelBridgeStatus
from .transport import Transport
from .null_transport import NullTransport
from ..telemetry import emit_event


class KernelBridge:
    """Main kernel bridge interface."""
    
    def __init__(self, config: Optional[KernelBridgeConfig] = None):
        self.config = config or KernelBridgeConfig.from_env()
        self._transport: Optional[Transport] = None
        self._lock = threading.Lock()
        self._semaphore = threading.Semaphore(self.config.max_inflight)
        
        # Initialize transport based on configuration
        if self.config.enabled:
            self._init_transport()
        else:
            self._transport = NullTransport(self.config)
    
    def _init_transport(self) -> None:
        """Initialize the appropriate transport."""
        if self.config.endpoint.startswith('unix://'):
            from .unix_transport import UnixSocketTransport
            self._transport = UnixSocketTransport(self.config)
        elif self.config.endpoint.startswith(('http://', 'https://')):
            from .http_transport import HttpTransport
            self._transport = HttpTransport(self.config)
        else:
            raise ValueError(f"Unsupported endpoint: {self.config.endpoint}")
    
    def is_available(self) -> bool:
        """Check if kernel bridge is available."""
        if not self.config.enabled:
            return True  # Null transport is always available
        
        if not self._transport:
            return False
        
        return self._transport.is_available()
    
    def call(self, method: str, params: Optional[Dict[str, Any]] = None) -> KernelBridgeResult:
        """Make a call to the kernel daemon."""
        if not self.config.enabled:
            # Use null transport
            return NullTransport(self.config).call(method, params or {})
        
        if not self._transport:
            return KernelBridgeResult.unavailable_result("Transport not initialized")
        
        params = params or {}
        start_time = time.time()
        retry_count = 0
        
        # Acquire semaphore to limit concurrent requests
        with self._semaphore:
            while retry_count <= self.config.retry_attempts:
                try:
                    result = self._transport.call(method, params)
                    
                    # Emit telemetry event
                    self._emit_telemetry(method, result, retry_count)
                    
                    # If successful or unretryable error, return result
                    if result.success or result.status in [
                        KernelBridgeStatus.INVALID_REQUEST,
                        KernelBridgeStatus.UNAVAILABLE
                    ]:
                        return result
                    
                    # Retry on timeout or transient errors
                    if retry_count < self.config.retry_attempts:
                        retry_count += 1
                        time.sleep(self.config.retry_delay_ms / 1000)
                        continue
                    
                    return result
                    
                except Exception as e:
                    retry_count += 1
                    if retry_count <= self.config.retry_attempts:
                        time.sleep(self.config.retry_delay_ms / 1000)
                        continue
                    
                    # Final retry failed
                    latency_ms = int((time.time() - start_time) * 1000)
                    return KernelBridgeResult.error_result(
                        reason=str(e),
                        latency_ms=latency_ms,
                        retry_count=retry_count
                    )
        
        # Should not reach here
        latency_ms = int((time.time() - start_time) * 1000)
        return KernelBridgeResult.error_result(
            reason="Max retries exceeded",
            latency_ms=latency_ms,
            retry_count=retry_count
        )
    
    def _emit_telemetry(self, method: str, result: KernelBridgeResult, retry_count: int) -> None:
        """Emit telemetry event for the call."""
        event_data = {
            "op": "kernel_bridge.call",
            "method": method,
            "endpoint": self.config.endpoint,
            "latency_ms": result.latency_ms,
            "success": result.success,
            "status": result.status.value,
            "retry_count": retry_count,
            "payload_size": result.payload_size
        }
        
        if result.error_code:
            event_data["error_code"] = result.error_code
        
        if result.reason:
            event_data["reason"] = result.reason
        
        emit_event("kernel_bridge", event_data)
    
    def ping(self) -> KernelBridgeResult:
        """Ping the kernel daemon."""
        return self.call("PING", {})
    
    def get_status(self) -> KernelBridgeResult:
        """Get kernel daemon status."""
        return self.call("STATUS", {})
    
    def apply_policy(self, policy: Dict[str, Any]) -> KernelBridgeResult:
        """Apply a policy to the kernel daemon."""
        return self.call("APPLY_POLICY", {"policy": policy})
    
    def close(self) -> None:
        """Close the kernel bridge and cleanup resources."""
        with self._lock:
            if self._transport:
                self._transport.close()
                self._transport = None
