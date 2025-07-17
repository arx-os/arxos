"""
SVGX Compiler Module

Handles compilation and export of SVGX files to various formats
including SVG, IFC, JSON, and GLTF.
"""

from svgx_engine.compiler.svgx_to_svg import SVGXToSVGCompiler
from svgx_engine.compiler.svgx_to_ifc import SVGXToIFCCompiler
from svgx_engine.compiler.svgx_to_json import SVGXToJSONCompiler
from svgx_engine.compiler.svgx_to_gltf import SVGXToGLTFCompiler

__all__ = [
    "SVGXCompiler",
    "SVGXToSVGCompiler",
    "SVGXToIFCCompiler", 
    "SVGXToJSONCompiler",
    "SVGXToGLTFCompiler",
]

class SVGXCompiler:
    """Main compiler class that orchestrates format conversions."""
    
    def __init__(self):
        self.svg_compiler = SVGXToSVGCompiler()
        self.ifc_compiler = SVGXToIFCCompiler()
        self.json_compiler = SVGXToJSONCompiler()
        self.gltf_compiler = SVGXToGLTFCompiler()
    
    def compile(self, svgx_content, target_format="svg"):
        """Compile SVGX content to target format."""
        if target_format == "svg":
            return self.svg_compiler.compile(svgx_content)
        elif target_format == "ifc":
            return self.ifc_compiler.compile(svgx_content)
        elif target_format == "json":
            return self.json_compiler.compile(svgx_content)
        elif target_format == "gltf":
            return self.gltf_compiler.compile(svgx_content)
        else:
            raise ValueError(f"Unsupported target format: {target_format}") 