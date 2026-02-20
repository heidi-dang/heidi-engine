"""
Kernel Bridge Configuration

Feature flags and connection settings for kernel bridge.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field, validator


class KernelBridgeConfig(BaseModel):
    """Configuration for kernel bridge communication."""
    
    # Feature flags
    enabled: bool = Field(
        default=False,
        description="Enable kernel bridge communication"
    )
    
    required: bool = Field(
        default=False,
        description="If true, pipeline stops when bridge unavailable"
    )
    
    # Connection settings
    endpoint: str = Field(
        default="unix:///tmp/heidi-kernel.sock",
        description="Kernel daemon endpoint (unix socket or HTTP URL)"
    )
    
    timeout_ms: int = Field(
        default=5000,
        ge=100,
        le=30000,
        description="Request timeout in milliseconds"
    )
    
    max_inflight: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum concurrent requests"
    )
    
    retry_attempts: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Number of retry attempts"
    )
    
    retry_delay_ms: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Delay between retries in milliseconds"
    )
    
    @validator('endpoint')
    def validate_endpoint(cls, v):
        """Validate endpoint format."""
        if v.startswith('unix://'):
            # Unix socket path
            path = v[7:]  # Remove 'unix://' prefix
            if not path.startswith('/'):
                raise ValueError('Unix socket path must be absolute')
        elif v.startswith('http://') or v.startswith('https://'):
            # HTTP URL
            if not v.startswith(('http://127.0.0.1', 'http://localhost', 'https://127.0.0.1', 'https://localhost')):
                raise ValueError('HTTP endpoint must be localhost only for security')
        else:
            raise ValueError('Endpoint must be unix:// or http(s)://')
        return v
    
    @classmethod
    def from_env(cls) -> 'KernelBridgeConfig':
        """Load configuration from environment variables."""
        return cls(
            enabled=os.getenv('HEIDI_KERNEL_ENABLED', 'false').lower() == 'true',
            required=os.getenv('HEIDI_KERNEL_REQUIRED', 'false').lower() == 'true',
            endpoint=os.getenv('HEIDI_KERNEL_ENDPOINT', 'unix:///tmp/heidi-kernel.sock'),
            timeout_ms=int(os.getenv('HEIDI_KERNEL_TIMEOUT_MS', '5000')),
            max_inflight=int(os.getenv('HEIDI_KERNEL_MAX_INFLIGHT', '3')),
            retry_attempts=int(os.getenv('HEIDI_KERNEL_RETRY_ATTEMPTS', '2')),
            retry_delay_ms=int(os.getenv('HEIDI_KERNEL_RETRY_DELAY_MS', '100'))
        )
