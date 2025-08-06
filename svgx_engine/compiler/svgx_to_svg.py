"""
SVGX to SVG Compiler for backward compatibility.

This module compiles SVGX content back to standard SVG format,
removing arx: extensions while preserving visual elements.
"""

import xml.etree.ElementTree as ET
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class SVGXToSVGCompiler:
    """Compiler for converting SVGX to standard SVG."""

    def __init__(self):
        self.arx_namespace = "http://arxos.io/svgx"
        self.svg_namespace = "http://www.w3.org/2000/svg"

    def compile(self, svgx_content: str) -> str:
        """
        Compile SVGX content to standard SVG.

        Args:
            svgx_content: SVGX content as string

        Returns:
            Standard SVG content
        """
        try:
            # Register namespaces
            ET.register_namespace("arx", self.arx_namespace)
            ET.register_namespace("svg", self.svg_namespace)

            # Parse SVGX content
            root = ET.fromstring(svgx_content)

            # Remove arx namespace declaration
            self._remove_arx_namespace(root)

            # Clean arx: attributes from all elements
            self._clean_arx_attributes(root)

            # Remove arx: elements
            self._remove_arx_elements(root)

            # Convert back to string
            result = ET.tostring(root, encoding="unicode", method="xml")

            return result

        except Exception as e:
            logger.error(f"Failed to compile SVGX to SVG: {e}")
            raise ValueError(f"Compilation failed: {e}")

    def _remove_arx_namespace(self, element: ET.Element):
        """Remove arx namespace declaration from element."""
        # Remove xmlns:arx attribute
        if "xmlns:arx" in element.attrib:
            del element.attrib["xmlns:arx"]

    def _clean_arx_attributes(self, element: ET.Element):
        """Remove all arx: attributes from element and its children."""
        # Remove arx: attributes from current element
        arx_attrs = [attr for attr in element.attrib.keys() if attr.startswith("arx:")]
        for attr in arx_attrs:
            del element.attrib[attr]

        # Recursively clean children
        for child in element:
            self._clean_arx_attributes(child)

    def _remove_arx_elements(self, element: ET.Element):
        """Remove arx: elements from the tree."""
        # Find and remove arx: elements
        arx_elements = []
        for child in element:
            if child.tag.startswith("arx:"):
                arx_elements.append(child)
            else:
                # Recursively process non-arx elements
                self._remove_arx_elements(child)

        # Remove arx elements
        for arx_elem in arx_elements:
            element.remove(arx_elem)

    def compile_file(self, input_file: str, output_file: str):
        """
        Compile SVGX file to SVG file.

        Args:
            input_file: Path to input SVGX file
            output_file: Path to output SVG file
        """
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                svgx_content = f.read()

            svg_content = self.compile(svgx_content)

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(svg_content)

            logger.info(f"Compiled {input_file} to {output_file}")

        except Exception as e:
            logger.error(f"Failed to compile file {input_file}: {e}")
            raise
