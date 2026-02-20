"""
Unix Socket Transport Implementation

Unix socket transport for kernel bridge communication.
"""

import socket
import time
import struct
import threading
import json
from typing import Dict, Any, Optional
from ..result import KernelBridgeResult, KernelBridgeStatus
from ..transport import Transport


class UnixSocketTransport(Transport):
    """Unix socket transport for kernel bridge communication."""
    
    def __init__(self, config):
        self.config = config
        self._socket: Optional[socket.socket] = None
        self._lock = threading.Lock()
        self._socket_path = config.endpoint[7:]  # Remove 'unix://' prefix
    
    def _create_socket(self) -> socket.socket:
        """Create a new unix socket."""
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.config.timeout_ms / 1000)
        return sock
    
    def _connect(self) -> socket.socket:
        """Connect to unix socket."""
        sock = self._create_socket()
        
        try:
            sock.connect(self._socket_path)
            return sock
        except (socket.timeout, ConnectionRefusedError, FileNotFoundError) as e:
            sock.close()
            raise ConnectionError(f"Failed to connect to {self._socket_path}: {e}")
    
    def _send_request(self, sock: socket.socket, data: bytes) -> None:
        """Send request to socket."""
        # Send length-prefixed data
        length = len(data)
        header = struct.pack('!I', length)
        
        sock.sendall(header + data)
    
    def _receive_response(self, sock: socket.socket) -> bytes:
        """Receive response from socket."""
        # Read length header
        header = sock.recv(4)
        if len(header) != 4:
            raise ConnectionError("Failed to read response header")
        
        length = struct.unpack('!I', header)[0]
        
        # Validate length to prevent hanging reads
        if length > 1024 * 1024:  # 1MB max
            raise ConnectionError(f"Response too large: {length} bytes")
        
        # Read response data
        response = b''
        while len(response) < length:
            chunk = sock.recv(min(length - len(response), 4096))
            if not chunk:
                raise ConnectionError("Connection closed while reading response")
            response += chunk
        
        return response
    
    def call(self, method: str, params: Dict[str, Any]) -> KernelBridgeResult:
        """Make a call to the kernel daemon via unix socket."""
        start_time = time.time()
        retry_count = 0
        
        while retry_count <= self.config.retry_attempts:
            sock = None
            try:
                with self._lock:
                    sock = self._connect()
                    
                    # Prepare request
                    request = {
                        "method": method,
                        "params": params,
                        "timestamp": time.time()
                    }
                    
                    # Convert to JSON bytes
                    data = json.dumps(request).encode('utf-8')
                    
                    # Send request and receive response
                    self._send_request(sock, data)
                    response_data = self._receive_response(sock)
                    
                    # Parse response
                    try:
                        response = json.loads(response_data.decode('utf-8'))
                    except json.JSONDecodeError as e:
                        return KernelBridgeResult.error_result(
                            reason=f"Invalid JSON response: {e}",
                            latency_ms=int((time.time() - start_time) * 1000),
                            retry_count=retry_count
                        )
                    
                    # Check for error response
                    if response.get('error'):
                        return KernelBridgeResult.error_result(
                            reason=response.get('message', 'Unknown error'),
                            error_code=response.get('code'),
                            latency_ms=int((time.time() - start_time) * 1000),
                            retry_count=retry_count
                        )
                    
                    # Success
                    latency_ms = int((time.time() - start_time) * 1000)
                    return KernelBridgeResult.success_result(
                        payload=response,
                        latency_ms=latency_ms
                    )
                    
            except ConnectionError as e:
                retry_count += 1
                if sock:
                    try:
                        sock.close()
                    except:
                        pass
                
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
            
            except socket.timeout:
                if sock:
                    try:
                        sock.close()
                    except:
                        pass
                
                retry_count += 1
                if retry_count <= self.config.retry_attempts:
                    time.sleep(self.config.retry_delay_ms / 1000)
                    continue
                
                # Final timeout
                latency_ms = int((time.time() - start_time) * 1000)
                return KernelBridgeResult.timeout_result(
                    latency_ms=latency_ms,
                    retry_count=retry_count
                )
            
            except Exception as e:
                if sock:
                    try:
                        sock.close()
                    except:
                        pass
                
                # Unexpected error
                latency_ms = int((time.time() - start_time) * 1000)
                return KernelBridgeResult.error_result(
                    reason=f"Unexpected error: {e}",
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
        """Check if unix socket transport is available."""
        if not self.config.enabled:
            return True  # Null transport handles this
        
        try:
            # Test socket creation and path existence
            sock = self._create_socket()
            sock.close()
            
            # Check if socket file exists and is a socket
            import os
            return os.path.exists(self._socket_path) and os.stat.S_ISSOCK(os.stat(self._socket_path).st_mode)
            
        except (OSError, AttributeError):
            return False
    
    def close(self) -> None:
        """Close the unix socket transport."""
        with self._lock:
            if self._socket:
                try:
                    self._socket.close()
                except:
                    pass
                self._socket = None
