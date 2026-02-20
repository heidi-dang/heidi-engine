"""
Unit tests for kernel bridge main interface.
"""

import pytest
from unittest.mock import patch, MagicMock
from heidi_engine.kernel_bridge.bridge import KernelBridge
from heidi_engine.kernel_bridge.config import KernelBridgeConfig
from heidi_engine.kernel_bridge.result import KernelBridgeResult, KernelBridgeStatus
from heidi_engine.kernel_bridge.null_transport import NullTransport


class TestKernelBridge:
    """Test kernel bridge main interface."""
    
    def test_bridge_disabled_by_default(self):
        """Test bridge is disabled by default."""
        bridge = KernelBridge()
        
        assert bridge.config.enabled is False
        assert isinstance(bridge._transport, NullTransport)
        assert bridge.is_available() is True
    
    def test_bridge_enabled_with_config(self):
        """Test bridge can be enabled with config."""
        config = KernelBridgeConfig(enabled=True)
        
        # Mock transport initialization
        with patch('heidi_engine.kernel_bridge.bridge.KernelBridge._init_transport'):
            bridge = KernelBridge(config)
            
            assert bridge.config.enabled is True
            bridge._init_transport.assert_called_once()
    
    def test_bridge_enabled_with_env(self):
        """Test bridge can be enabled via environment."""
        with patch.dict('os.environ', {'HEIDI_KERNEL_ENABLED': 'true'}):
            with patch('heidi_engine.kernel_bridge.bridge.KernelBridge._init_transport'):
                bridge = KernelBridge()
                
                assert bridge.config.enabled is True
                bridge._init_transport.assert_called_once()
    
    def test_null_transport_call(self):
        """Test call with null transport."""
        bridge = KernelBridge()  # Disabled by default
        
        result = bridge.call("PING", {})
        
        assert result.success is True
        assert result.status == KernelBridgeStatus.OK
        assert result.payload is not None
        assert result.payload["method"] == "PING"
        assert result.payload["mock"] is True
    
    def test_null_transport_is_available(self):
        """Test null transport availability."""
        bridge = KernelBridge()
        
        assert bridge.is_available() is True
    
    def test_null_transport_close(self):
        """Test null transport close."""
        bridge = KernelBridge()
        
        # Should not raise exception
        bridge.close()
        assert bridge._transport is None
    
    def test_ping_method(self):
        """Test ping method."""
        bridge = KernelBridge()
        
        result = bridge.ping()
        
        assert result.success is True
        assert result.payload["method"] == "PING"
    
    def test_get_status_method(self):
        """Test get_status method."""
        bridge = KernelBridge()
        
        result = bridge.get_status()
        
        assert result.success is True
        assert result.payload["method"] == "STATUS"
    
    def test_apply_policy_method(self):
        """Test apply_policy method."""
        bridge = KernelBridge()
        policy = {"test": "policy"}
        
        result = bridge.apply_policy(policy)
        
        assert result.success is True
        assert result.payload["method"] == "APPLY_POLICY"
        assert result.payload["params"]["policy"] == policy
    
    def test_call_with_params(self):
        """Test call with parameters."""
        bridge = KernelBridge()
        params = {"param1": "value1", "param2": 42}
        
        result = bridge.call("TEST", params)
        
        assert result.success is True
        assert result.payload["params"] == params
    
    def test_call_with_empty_params(self):
        """Test call with empty parameters."""
        bridge = KernelBridge()
        
        result = bridge.call("TEST")
        
        assert result.success is True
        assert result.payload["params"] == {}
    
    def test_required_flag_unavailable(self):
        """Test required flag when bridge unavailable."""
        config = KernelBridgeConfig(enabled=True, required=True)
        
        # Mock transport as unavailable
        with patch('heidi_engine.kernel_bridge.bridge.KernelBridge._init_transport'):
            bridge = KernelBridge(config)
            bridge._transport = None
            
            result = bridge.call("PING", {})
            
            assert result.success is False
            assert result.status == KernelBridgeStatus.UNAVAILABLE
    
    def test_concurrent_limiting(self):
        """Test concurrent request limiting."""
        config = KernelBridgeConfig(max_inflight=2)
        bridge = KernelBridge(config)
        
        # Test semaphore limit
        assert bridge._semaphore._value == 2
        
        # Acquire semaphore to test limiting
        with bridge._semaphore:
            assert bridge._semaphore._value == 1
    
    def test_thread_safety(self):
        """Test thread safety of bridge operations."""
        bridge = KernelBridge()
        
        # Multiple threads should be able to call safely
        import threading
        
        results = []
        
        def worker():
            result = bridge.call("PING", {})
            results.append(result)
        
        threads = [threading.Thread(target=worker) for _ in range(5)]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(results) == 5
        assert all(r.success for r in results)
