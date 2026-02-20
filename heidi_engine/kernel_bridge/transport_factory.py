"""
Transport Factory

Lazy loading of transport modules to avoid import issues on unsupported platforms.
"""

from typing import Optional
from .config import KernelBridgeConfig
from .transport import Transport
from .null_transport import NullTransport


def create_transport(config: KernelBridgeConfig) -> Transport:
    """Create transport instance based on configuration."""
    if not config.enabled:
        return NullTransport(config)
    
    if config.endpoint.startswith('unix://'):
        # Lazy import to avoid platform-specific issues
        from .transports.unix_socket import UnixSocketTransport
        return UnixSocketTransport(config)
    
    elif config.endpoint.startswith(('http://', 'https://')):
        # Lazy import to avoid HTTP dependencies when not needed
        from .transports.http_transport import HttpTransport
        return HttpTransport(config)
    
    else:
        raise ValueError(f"Unsupported endpoint: {config.endpoint}")
