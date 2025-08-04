"""
Intent Detection Package

This package provides intent detection functionality with confidence scoring
and pattern matching for building operations.
"""

from .intent_detector import IntentDetector, detect_intent

__all__ = [
    "IntentDetector",
    "detect_intent"
] 