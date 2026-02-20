"""
Unit tests for kernel bridge result types.
"""

import pytest
from heidi_engine.kernel_bridge.result import KernelBridgeResult, KernelBridgeStatus


class TestKernelBridgeResult:
    """Test kernel bridge result types."""
    
    def test_success_result(self):
        """Test creating a success result."""
        payload = {"status": "ok", "data": "test"}
        result = KernelBridgeResult.success_result(payload=payload, latency_ms=50)
        
        assert result.success is True
        assert result.status == KernelBridgeStatus.OK
        assert result.payload == payload
        assert result.latency_ms == 50
        assert result.payload_size == len(str(payload).encode())
        assert result.reason is None
        assert result.error_code is None
        assert result.retry_count == 0
    
    def test_success_result_no_payload(self):
        """Test creating a success result without payload."""
        result = KernelBridgeResult.success_result()
        
        assert result.success is True
        assert result.status == KernelBridgeStatus.OK
        assert result.payload is None
        assert result.payload_size == 0
    
    def test_error_result(self):
        """Test creating an error result."""
        result = KernelBridgeResult.error_result(
            reason="Connection failed",
            error_code="CONN_ERROR",
            latency_ms=100,
            retry_count=2
        )
        
        assert result.success is False
        assert result.status == KernelBridgeStatus.ERROR
        assert result.reason == "Connection failed"
        assert result.error_code == "CONN_ERROR"
        assert result.latency_ms == 100
        assert result.retry_count == 2
        assert result.payload is None
    
    def test_timeout_result(self):
        """Test creating a timeout result."""
        result = KernelBridgeResult.timeout_result(latency_ms=5000, retry_count=3)
        
        assert result.success is False
        assert result.status == KernelBridgeStatus.TIMEOUT
        assert result.reason == "Request timed out"
        assert result.latency_ms == 5000
        assert result.retry_count == 3
        assert result.error_code is None
    
    def test_unavailable_result(self):
        """Test creating an unavailable result."""
        result = KernelBridgeResult.unavailable_result()
        
        assert result.success is False
        assert result.status == KernelBridgeStatus.UNAVAILABLE
        assert result.reason == "Kernel bridge unavailable"
        assert result.latency_ms is None
        assert result.retry_count == 0
    
    def test_unavailable_result_custom_reason(self):
        """Test creating an unavailable result with custom reason."""
        result = KernelBridgeResult.unavailable_result("Custom reason")
        
        assert result.success is False
        assert result.status == KernelBridgeStatus.UNAVAILABLE
        assert result.reason == "Custom reason"
    
    def test_result_serialization(self):
        """Test result can be serialized."""
        result = KernelBridgeResult.success_result(
            payload={"test": "data"},
            latency_ms=42
        )
        
        # Should be serializable by pydantic
        data = result.dict()
        assert data["success"] is True
        assert data["status"] == "ok"
        assert data["payload"]["test"] == "data"
        assert data["latency_ms"] == 42
