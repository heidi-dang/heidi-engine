"""
Kernel Bridge Module

Provides abstraction layer for communicating with heidi-kernel daemon.
Supports multiple transports (null, unix socket, http) with feature flags.
"""

from .bridge import KernelBridge
from .config import KernelBridgeConfig
from .result import KernelBridgeResult, KernelBridgeStatus

__all__ = [
    'KernelBridge',
    'KernelBridgeConfig', 
    'KernelBridgeResult',
    'KernelBridgeStatus'
]
