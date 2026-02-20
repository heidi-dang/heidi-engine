"""
Unit tests for kernel bridge telemetry.
"""

import pytest
from unittest.mock import patch, MagicMock
from heidi_engine.kernel_bridge.bridge import KernelBridge
from heidi_engine.kernel_bridge.config import KernelBridgeConfig
from heidi_engine.kernel_bridge.result import KernelBridgeResult, KernelBridgeStatus


class TestKernelBridgeTelemetry:
    """Test kernel bridge telemetry emission."""
    
    def test_telemetry_emitted_on_success(self):
        """Test telemetry is emitted on successful call."""
        config = KernelBridgeConfig(enabled=False)  # Use null transport
        bridge = KernelBridge(config)
        
        with patch('heidi_engine.kernel_bridge.bridge.emit_event') as mock_emit:
            result = bridge.call("PING", {})
            
            assert result.success is True
            mock_emit.assert_called_once()
            
            # Check event data
            call_args = mock_emit.call_args
            assert call_args[0][0] == "kernel_bridge"
            event_data = call_args[0][1]
            
            assert event_data["op"] == "kernel_bridge.call"
            assert event_data["method"] == "PING"
            assert event_data["success"] is True
            assert event_data["status"] == "ok"
            assert "latency_ms" in event_data
            assert event_data["retry_count"] == 0
    
    def test_telemetry_emitted_on_error(self):
        """Test telemetry is emitted on error."""
        config = KernelBridgeConfig(enabled=False)
        bridge = KernelBridge(config)
        
        # Mock null transport to return error
        with patch('heidi_engine.kernel_bridge.bridge.NullTransport.call') as mock_call:
            mock_call.return_value = KernelBridgeResult.error_result(
                reason="Test error",
                error_code="TEST_ERROR"
            )
            
            with patch('heidi_engine.kernel_bridge.bridge.emit_event') as mock_emit:
                result = bridge.call("INVALID_METHOD", {})
                
                assert result.success is False
                mock_emit.assert_called_once()
                
                # Check event data
                call_args = mock_emit.call_args
                event_data = call_args[0][1]
                
                assert event_data["op"] == "kernel_bridge.call"
                assert event_data["method"] == "INVALID_METHOD"
                assert event_data["success"] is False
                assert event_data["status"] == "error"
                assert event_data["reason"] == "Test error"
                assert event_data["error_code"] == "TEST_ERROR"
    
    def test_telemetry_emitted_on_timeout(self):
        """Test telemetry is emitted on timeout."""
        config = KernelBridgeConfig(enabled=False)
        bridge = KernelBridge(config)
        
        with patch('heidi_engine.kernel_bridge.bridge.NullTransport.call') as mock_call:
            mock_call.return_value = KernelBridgeResult.timeout_result(
                latency_ms=5000,
                retry_count=2
            )
            
            with patch('heidi_engine.kernel_bridge.bridge.emit_event') as mock_emit:
                result = bridge.call("SLOW_METHOD", {})
                
                assert result.success is False
                assert result.status == KernelBridgeStatus.TIMEOUT
                mock_emit.assert_called_once()
                
                # Check event data
                call_args = mock_emit.call_args
                event_data = call_args[0][1]
                
                assert event_data["status"] == "timeout"
                assert event_data["retry_count"] == 2
                assert event_data["latency_ms"] == 5000
    
    def test_telemetry_includes_payload_size(self):
        """Test telemetry includes payload size information."""
        config = KernelBridgeConfig(enabled=False)
        bridge = KernelBridge(config)
        
        payload = {"data": "x" * 100}  # 100 characters
        result = KernelBridgeResult.success_result(payload=payload)
        
        with patch('heidi_engine.kernel_bridge.bridge.NullTransport.call') as mock_call:
            mock_call.return_value = result
            
            with patch('heidi_engine.kernel_bridge.bridge.emit_event') as mock_emit:
                bridge.call("TEST_METHOD", {})
                
                call_args = mock_emit.call_args
                event_data = call_args[0][1]
                
                assert event_data["payload_size"] == len(str(payload).encode())
    
    def test_telemetry_no_payload_size_for_none(self):
        """Test telemetry handles None payload gracefully."""
        config = KernelBridgeConfig(enabled=False)
        bridge = KernelBridge(config)
        
        result = KernelBridgeResult.success_result(payload=None)
        
        with patch('heidi_engine.kernel_bridge.bridge.NullTransport.call') as mock_call:
            mock_call.return_value = result
            
            with patch('heidi_engine.kernel_bridge.bridge.emit_event') as mock_emit:
                bridge.call("TEST_METHOD", {})
                
                call_args = mock_emit.call_args
                event_data = call_args[0][1]
                
                assert event_data["payload_size"] == 0
