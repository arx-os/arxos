"""
SVGX Parser Module

Handles parsing of SVGX files with extended SVG syntax including
object semantics, behavior profiles, and spatial awareness.
"""

from svgx_engine.parser.parser import SVGXParser, SVGXElement
from svgx_engine.parser.symbol_manager import SVGXSymbolManager
from svgx_engine.parser.geometry import SVGXGeometry

__all__ = [
    "SVGXParser",
    "SVGXElement",
    "SVGXSymbolManager",
    "SVGXGeometry",
]
