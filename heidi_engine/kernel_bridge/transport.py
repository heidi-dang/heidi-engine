"""
Transport Interface

Abstract base class for kernel bridge transports.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from .result import KernelBridgeResult


class Transport(ABC):
    """Abstract base class for kernel bridge transports."""
    
    def __init__(self, config):
        self.config = config
    
    @abstractmethod
    def call(self, method: str, params: Dict[str, Any]) -> KernelBridgeResult:
        """Make a call to the kernel daemon."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the transport is available."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the transport and cleanup resources."""
        pass
