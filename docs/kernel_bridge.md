# Kernel Bridge

This module provides a bridge for communicating with the heidi-kernel daemon.

## Features

- **Multiple Transports**: Unix socket (preferred), HTTP, and null transport for testing
- **Feature Flags**: Enable/disable bridge, make it required for pipeline execution
- **Bounded Concurrency**: Limit concurrent requests to prevent overload
- **Retry Logic**: Configurable retry attempts with exponential backoff
- **Telemetry**: Emit events for all bridge operations
- **Thread Safety**: Safe concurrent access with proper locking

## Configuration

The bridge can be configured via environment variables:

```bash
HEIDI_KERNEL_ENABLED=true          # Enable kernel bridge
HEIDI_KERNEL_REQUIRED=false         # Fail if bridge unavailable
HEIDI_KERNEL_ENDPOINT=unix:///tmp/heidi-kernel.sock  # Socket path
HEIDI_KERNEL_TIMEOUT_MS=5000       # Request timeout
HEIDI_KERNEL_MAX_INFLIGHT=3       # Max concurrent requests
HEIDI_KERNEL_RETRY_ATTEMPTS=2     # Retry attempts
HEIDI_KERNEL_RETRY_DELAY_MS=100    # Retry delay
```

## Usage

```python
from heidi_engine.kernel_bridge import KernelBridge, KernelBridgeConfig

# Create bridge instance
bridge = KernelBridge()

# Check if bridge is available
if bridge.is_available():
    # Ping the kernel daemon
    result = bridge.ping()
    if result.success:
        print(f"Kernel daemon responded: {result.payload}")
    
    # Apply a policy
    policy = {"test": True}
    result = bridge.apply_policy(policy)
    if result.success:
        print("Policy applied successfully")
```

## Socket Path

The default socket path is `unix:///tmp/heidi-kernel.sock`. For production use, the recommended path is:

```
~/.local/heidi-engine/run/kernel.sock
```

This path is automatically created with proper permissions when using the systemd user service.

## Systemd User Service

Create a systemd user service for the kernel daemon:

```ini
[Unit]
Description=Heidi Kernel Daemon
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/heidi-kernel-daemon
RuntimeDirectory=%h/.local/heidi-engine
RuntimeDirectoryMode=0755
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default
```

The `RuntimeDirectory` ensures the socket directory exists with proper permissions.

## Methods

### KernelBridge

- `ping()` - Ping the kernel daemon
- `get_status()` - Get daemon status
- `apply_policy(policy)` - Apply a policy to the kernel daemon
- `call(method, params)` - Make a custom call

### KernelBridgeConfig

Configuration class with validation for all bridge settings.

### KernelBridgeResult

Result type containing:
- `status`: Operation status (ok, error, timeout, unavailable)
- `success`: Boolean success flag
- `reason`: Error message (if any)
- `latency_ms`: Request latency in milliseconds
- `payload_size`: Response payload size in bytes
- `payload`: Response payload (if success)
- `error_code`: Error code (if any)
- `retry_count`: Number of retry attempts

## Transport Types

### NullTransport
No-op transport for testing and when bridge is disabled. Always returns success.

### UnixSocketTransport
Unix socket transport with length-prefixed JSON messages. Preferred for production use.

### HttpTransport
HTTP transport for localhost connections. Useful for debugging.

## Telemetry

All bridge operations emit telemetry events:

```json
{
  "op": "kernel_bridge.call",
  "method": "PING",
  "endpoint": "unix:///tmp/heidi-kernel.sock",
  "latency_ms": 42,
  "success": true,
  "status": "ok",
  "retry_count": 0,
  "payload_size": 256,
  "error_code": null,
  "reason": null
}
```

## Testing

Unit tests run without requiring a kernel daemon:

```bash
python -m pytest tests/unit/test_kernel_bridge*.py
```

Integration tests require `HEIDI_KERNEL_IT=1` and a running kernel daemon:

```bash
HEIDI_KERNEL_IT=1 python -m pytest tests/integration/test_kernel_bridge_socket.py
```

## Error Handling

The bridge handles various error conditions gracefully:

- **Connection Errors**: Retry with exponential backoff
- **Timeouts**: Return timeout result with latency info
- **Invalid Responses**: Parse errors return error result
- **Size Limits**: Reject overly large responses to prevent hanging
- **Required Flag**: Fail fast if bridge is required but unavailable

## Thread Safety

The bridge is thread-safe and supports concurrent requests up to the configured limit. Each request acquires a semaphore to limit concurrency.

## Security Considerations

- Unix socket paths are validated to be absolute
- HTTP endpoints are restricted to localhost only
- Response size is limited to prevent memory exhaustion
- No secrets are logged in telemetry events
- All operations are bounded by timeout and retry limits
