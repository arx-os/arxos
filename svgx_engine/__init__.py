"""
SVGX Engine - A programmable spatial markup format and simulation engine
for CAD-grade infrastructure modeling.

This package extends SVG with geometric precision, object semantics,
programmable behavior, and spatial simulation capabilities.
"""

__version__ = "0.1.0"
__author__ = "Arxos Team"
__email__ = "team@arxos.com"

# Core imports
from .parser import SVGXParser
from .runtime import SVGXRuntime
from .compiler import SVGXCompiler

__all__ = [
    "SVGXParser",
    "SVGXRuntime", 
    "SVGXCompiler",
    "__version__",
] 