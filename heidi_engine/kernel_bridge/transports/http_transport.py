"""
HTTP Transport Implementation

HTTP transport for kernel bridge communication (localhost only).
"""

import time
import threading
import json
from typing import Dict, Any, Optional
from ...result import KernelBridgeResult, KernelBridgeStatus
from ...transport import Transport


class HttpTransport(Transport):
    """HTTP transport for kernel bridge communication."""
    
    def __init__(self, config):
        self.config = config
        self._session = None
        self._lock = threading.Lock()
        self._base_url = config.endpoint
    
    def _get_session(self):
        """Get or create HTTP session."""
        if self._session is None:
            try:
                import requests
                self._session = requests.Session()
                self._session.timeout = self.config.timeout_ms / 1000
            except ImportError:
                raise RuntimeError("requests library not available for HTTP transport")
        return self._session
    
    def call(self, method: str, params: Dict[str, Any]) -> KernelBridgeResult:
        """Make a call to the kernel daemon via HTTP."""
        start_time = time.time()
        retry_count = 0
        
        while retry_count <= self.config.retry_attempts:
            try:
                session = self._get_session()
                
                # Prepare request
                request_data = {
                    "method": method,
                    "params": params,
                    "timestamp": time.time()
                }
                
                # Send HTTP POST request
                response = session.post(
                    f"{self._base_url}/api/call",
                    json=request_data,
                    timeout=self.config.timeout_ms / 1000
                )
                
                # Check response status
                if response.status_code == 200:
                    try:
                        result = response.json()
                        
                        # Check for error response
                        if result.get('error'):
                            return KernelBridgeResult.error_result(
                                reason=result.get('message', 'Unknown error'),
                                error_code=result.get('code'),
                                latency_ms=int((time.time() - start_time) * 1000),
                                retry_count=retry_count
                            )
                        
                        # Success
                        latency_ms = int((time.time() - start_time) * 1000)
                        return KernelBridgeResult.success_result(
                            payload=result,
                            latency_ms=latency_ms
                        )
                        
                    except json.JSONDecodeError as e:
                        return KernelBridgeResult.error_result(
                            reason=f"Invalid JSON response: {e}",
                            latency_ms=int((time.time() - start_time) * 1000),
                            retry_count=retry_count
                        )
                
                else:
                    # HTTP error
                    return KernelBridgeResult.error_result(
                        reason=f"HTTP {response.status_code}: {response.text}",
                        latency_ms=int((time.time() - start_time) * 1000),
                        retry_count=retry_count
                    )
                    
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
    
    def is_available(self) -> bool:
        """Check if HTTP transport is available."""
        if not self.config.enabled:
            return True  # Null transport handles this
        
        try:
            import requests
            session = requests.Session()
            session.timeout = 1.0  # Short timeout for availability check
            
            # Try to connect to the endpoint
            response = session.get(f"{self._base_url}/health", timeout=1.0)
            return response.status_code == 200
            
        except Exception:
            return False
    
    def close(self) -> None:
        """Close the HTTP transport."""
        with self._lock:
            if self._session:
                try:
                    self._session.close()
                except:
                    pass
                self._session = None
