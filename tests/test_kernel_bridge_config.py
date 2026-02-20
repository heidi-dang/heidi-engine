"""
Unit tests for kernel bridge configuration.
"""

import pytest
import os
from heidi_engine.kernel_bridge.config import KernelBridgeConfig


class TestKernelBridgeConfig:
    """Test kernel bridge configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = KernelBridgeConfig()
        
        assert config.enabled is False
        assert config.required is False
        assert config.endpoint == "unix:///tmp/heidi-kernel.sock"
        assert config.timeout_ms == 5000
        assert config.max_inflight == 3
        assert config.retry_attempts == 2
        assert config.retry_delay_ms == 100
    
    def test_from_env_defaults(self):
        """Test loading defaults from environment."""
        # Clear any existing env vars
        for key in list(os.environ.keys()):
            if key.startswith('HEIDI_KERNEL_'):
                del os.environ[key]
        
        config = KernelBridgeConfig.from_env()
        
        assert config.enabled is False
        assert config.required is False
        assert config.endpoint == "unix:///tmp/heidi-kernel.sock"
    
    def test_from_env_enabled(self):
        """Test loading enabled flag from environment."""
        os.environ['HEIDI_KERNEL_ENABLED'] = 'true'
        try:
            config = KernelBridgeConfig.from_env()
            assert config.enabled is True
        finally:
            del os.environ['HEIDI_KERNEL_ENABLED']
    
    def test_from_env_required(self):
        """Test loading required flag from environment."""
        os.environ['HEIDI_KERNEL_REQUIRED'] = 'true'
        try:
            config = KernelBridgeConfig.from_env()
            assert config.required is True
        finally:
            del os.environ['HEIDI_KERNEL_REQUIRED']
    
    def test_unix_socket_endpoint(self):
        """Test unix socket endpoint validation."""
        config = KernelBridgeConfig(endpoint="unix:///var/run/heidi.sock")
        assert config.endpoint == "unix:///var/run/heidi.sock"
    
    def test_unix_socket_endpoint_invalid(self):
        """Test invalid unix socket endpoint."""
        with pytest.raises(ValueError, match="Unix socket path must be absolute"):
            KernelBridgeConfig(endpoint="unix://relative/path.sock")
    
    def test_http_endpoint_localhost(self):
        """Test localhost HTTP endpoint validation."""
        config = KernelBridgeConfig(endpoint="http://127.0.0.1:8080")
        assert config.endpoint == "http://127.0.0.1:8080"
        
        config = KernelBridgeConfig(endpoint="https://localhost:8443")
        assert config.endpoint == "https://localhost:8443"
    
    def test_http_endpoint_invalid(self):
        """Test invalid HTTP endpoint."""
        with pytest.raises(ValueError, match="HTTP endpoint must be localhost only"):
            KernelBridgeConfig(endpoint="http://example.com:8080")
    
    def test_invalid_endpoint_format(self):
        """Test invalid endpoint format."""
        with pytest.raises(ValueError, match="Endpoint must be unix:// or http"):
            KernelBridgeConfig(endpoint="invalid://endpoint")
    
    def test_timeout_bounds(self):
        """Test timeout bounds validation."""
        # Valid bounds
        KernelBridgeConfig(timeout_ms=100)
        KernelBridgeConfig(timeout_ms=30000)
        
        # Invalid bounds
        with pytest.raises(ValueError):
            KernelBridgeConfig(timeout_ms=50)  # Too low
        
        with pytest.raises(ValueError):
            KernelBridgeConfig(timeout_ms=50000)  # Too high
    
    def test_max_inflight_bounds(self):
        """Test max_inflight bounds validation."""
        # Valid bounds
        KernelBridgeConfig(max_inflight=1)
        KernelBridgeConfig(max_inflight=10)
        
        # Invalid bounds
        with pytest.raises(ValueError):
            KernelBridgeConfig(max_inflight=0)  # Too low
        
        with pytest.raises(ValueError):
            KernelBridgeConfig(max_inflight=20)  # Too high
