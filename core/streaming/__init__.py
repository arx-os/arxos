"""
Arxos 14KB Streaming Architecture.

Ultra-lightweight streaming system for Building-Infrastructure-as-Code
that enables 14KB initial bundle with progressive enhancement and
on-demand loading of building components.
"""

__version__ = "1.0.0"
__author__ = "Arxos BIM Team"

from .streaming_engine import StreamingEngine, UserRole, StreamingConfig
from .progressive_disclosure import ProgressiveDisclosure, LODLevel
from .differential_compression import DifferentialCompression, ObjectDelta
from .viewport_manager import ViewportManager, ViewportBounds
from .cache_strategy import SmartCache, CacheLevel
try:
    from .binary_optimization import BinaryOptimizer, TypedArrayEncoder
except ImportError:
    # Fallback if numpy is not available
    BinaryOptimizer = None
    TypedArrayEncoder = None

__all__ = [
    'StreamingEngine',
    'UserRole',
    'StreamingConfig',
    'ProgressiveDisclosure',
    'LODLevel', 
    'DifferentialCompression',
    'ObjectDelta',
    'ViewportManager',
    'ViewportBounds',
    'SmartCache',
    'CacheLevel',
    'BinaryOptimizer',
    'TypedArrayEncoder'
]