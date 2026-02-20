"""
Kernel Bridge Configuration

Feature flags and connection settings for kernel bridge.
"""

import os
from typing import Optional


class KernelBridgeConfig:
    """Configuration for kernel bridge communication."""
    
    def __init__(self, **kwargs):
        # Feature flags
        self.enabled = kwargs.get('enabled', False)
        self.required = kwargs.get('required', False)
        
        # Connection settings
        default_endpoint = f"unix://{os.path.expanduser('~/.local/heidi-engine/run/kernel.sock')}"
        self.endpoint = kwargs.get('endpoint', default_endpoint)
        
        # Timeout and retry settings
        self.timeout_ms = kwargs.get('timeout_ms', 5000)
        self.max_inflight = kwargs.get('max_inflight', 3)
        self.retry_attempts = kwargs.get('retry_attempts', 2)
        self.retry_delay_ms = kwargs.get('retry_delay_ms', 100)
        
        # Validate configuration
        self._validate()
    
    def _validate(self):
        """Validate configuration values."""
        # Validate timeout bounds
        if not (100 <= self.timeout_ms <= 30000):
            raise ValueError(f"timeout_ms must be between 100 and 30000, got {self.timeout_ms}")
        
        # Validate max_inflight bounds
        if not (1 <= self.max_inflight <= 10):
            raise ValueError(f"max_inflight must be between 1 and 10, got {self.max_inflight}")
        
        # Validate retry attempts bounds
        if not (0 <= self.retry_attempts <= 5):
            raise ValueError(f"retry_attempts must be between 0 and 5, got {self.retry_attempts}")
        
        # Validate retry delay bounds
        if not (10 <= self.retry_delay_ms <= 1000):
            raise ValueError(f"retry_delay_ms must be between 10 and 1000, got {self.retry_delay_ms}")
        
        # Validate endpoint format
        if self.endpoint.startswith('unix://'):
            # Unix socket path
            path = self.endpoint[7:]  # Remove 'unix://' prefix
            if not path.startswith('/'):
                raise ValueError('Unix socket path must be absolute')
        elif self.endpoint.startswith('http://') or self.endpoint.startswith('https://'):
            # HTTP URL
            if not self.endpoint.startswith(('http://127.0.0.1', 'http://localhost', 'https://127.0.0.1', 'https://localhost')):
                raise ValueError('HTTP endpoint must be localhost only for security')
        else:
            raise ValueError('Endpoint must be unix:// or http(s)://')
    
    @classmethod
    def from_env(cls) -> 'KernelBridgeConfig':
        """Load configuration from environment variables."""
        default_endpoint = f"unix://{os.path.expanduser('~/.local/heidi-engine/run/kernel.sock')}"
        return cls(
            enabled=os.getenv('HEIDI_KERNEL_ENABLED', 'false').lower() == 'true',
            required=os.getenv('HEIDI_KERNEL_REQUIRED', 'false').lower() == 'true',
            endpoint=os.getenv('HEIDI_KERNEL_ENDPOINT', default_endpoint),
            timeout_ms=int(os.getenv('HEIDI_KERNEL_TIMEOUT_MS', '5000')),
            max_inflight=int(os.getenv('HEIDI_KERNEL_MAX_INFLIGHT', '3')),
            retry_attempts=int(os.getenv('HEIDI_KERNEL_RETRY_ATTEMPTS', '2')),
            retry_delay_ms=int(os.getenv('HEIDI_KERNEL_RETRY_DELAY_MS', '100'))
        )
