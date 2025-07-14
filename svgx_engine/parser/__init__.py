"""
SVGX Parser Module

Handles parsing of SVGX files with extended SVG syntax including
object semantics, behavior profiles, and spatial awareness.
"""

from .parser import SVGXParser
from .symbol_manager import SVGXSymbolManager
from .geometry import SVGXGeometry

__all__ = [
    "SVGXParser",
    "SVGXSymbolManager", 
    "SVGXGeometry",
] 