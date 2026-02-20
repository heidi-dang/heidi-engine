"""
Null Transport Implementation

No-op transport for testing and disabled bridge.
"""

import time
from typing import Dict, Any
from .result import KernelBridgeResult, KernelBridgeStatus
from .transport import Transport


class NullTransport(Transport):
    """No-op transport that always returns success."""
    
    def __init__(self, config):
        self.config = config
    
    def call(self, method: str, params: Dict[str, Any]) -> KernelBridgeResult:
        """Simulate a successful call."""
        start_time = time.time()
        
        # Simulate minimal latency
        time.sleep(0.001)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Return a mock success result
        mock_payload = {
            "method": method,
            "params": params,
            "mock": True,
            "timestamp": time.time()
        }
        
        return KernelBridgeResult.success_result(
            payload=mock_payload,
            latency_ms=latency_ms
        )
    
    def is_available(self) -> bool:
        """Null transport is always available."""
        return True
    
    def close(self) -> None:
        """No cleanup needed for null transport."""
        pass
