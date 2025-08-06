"""
SVGX Schema Validator for XML schema validation.
"""

import logging
from typing import Dict, Any, List, Optional
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class SVGXSchemaValidator:
    """Validator for SVGX schema compliance."""

    def __init__(self):
        self.required_namespaces = {
            "svg": "http://www.w3.org/2000/svg",
            "arx": "http://arxos.io/svgx",
        }
        self.valid_object_types = [
            "electrical.light_fixture",
            "electrical.panel",
            "electrical.outlet",
            "electrical.switch",
            "mechanical.hvac",
            "mechanical.duct",
            "plumbing.pipe",
            "plumbing.fixture",
            "architecture.room",
            "architecture.wall",
            "architecture.door",
            "architecture.window",
        ]

    def validate_schema(self, content: str) -> Dict[str, Any]:
        """
        Validate SVGX content against schema.

        Args:
            content: SVGX content as string

        Returns:
            Validation results
        """
        results = {"valid": True, "errors": [], "warnings": [], "info": []}

        try:
            # Parse XML
            root = ET.fromstring(content)

            # Validate namespaces
            self._validate_namespaces(root, results)

            # Validate structure
            self._validate_structure(root, results)

            # Validate elements
            self._validate_elements(root, results)

            # Update valid flag
            results["valid"] = len(results["errors"]) == 0

        except ET.ParseError as e:
            results["errors"].append(f"XML parsing error: {e}")
            results["valid"] = False
        except Exception as e:
            results["errors"].append(f"Validation error: {e}")
            results["valid"] = False

        return results

    def _validate_namespaces(self, root: ET.Element, results: Dict[str, Any]):
        """Validate namespace declarations."""
        namespaces = root.attrib

        # Check for SVG namespace
        if "xmlns" not in namespaces:
            results["errors"].append("Missing SVG namespace declaration")

        # Check for arx namespace
        if "xmlns:arx" not in namespaces:
            results["errors"].append("Missing arx namespace declaration")
        elif namespaces["xmlns:arx"] != self.required_namespaces["arx"]:
            results["warnings"].append(
                f"Unexpected arx namespace: {namespaces['xmlns:arx']}"
            )

    def _validate_structure(self, root: ET.Element, results: Dict[str, Any]):
        """Validate document structure."""
        if root.tag != "svg":
            results["errors"].append("Root element must be 'svg'")

        # Check for at least one arx:object
        arx_objects = root.findall(".//arx:object")
        if not arx_objects:
            results["warnings"].append("No arx:object elements found")

    def _validate_elements(self, root: ET.Element, results: Dict[str, Any]):
        """Validate individual elements."""
        # Validate arx:object elements
        for obj in root.findall(".//arx:object"):
            self._validate_arx_object(obj, results)

        # Validate arx:behavior elements
        for behavior in root.findall(".//arx:behavior"):
            self._validate_arx_behavior(behavior, results)

        # Validate arx:physics elements
        for physics in root.findall(".//arx:physics"):
            self._validate_arx_physics(physics, results)

    def _validate_arx_object(self, obj: ET.Element, results: Dict[str, Any]):
        """Validate arx:object element."""
        # Check required attributes
        if not obj.get("id"):
            results["errors"].append("arx:object missing required 'id' attribute")

        if not obj.get("type"):
            results["errors"].append("arx:object missing required 'type' attribute")
        else:
            obj_type = obj.get("type")
            if obj_type not in self.valid_object_types:
                results["warnings"].append(f"Unknown object type: {obj_type}")

        # Check for valid system attribute
        system = obj.get("system")
        if system and system not in [
            "electrical",
            "mechanical",
            "plumbing",
            "architecture",
        ]:
            results["warnings"].append(f"Unknown system: {system}")

    def _validate_arx_behavior(self, behavior: ET.Element, results: Dict[str, Any]):
        """Validate arx:behavior element."""
        # Check variables
        variables = behavior.find("variables")
        if variables is not None:
            for var in variables.findall("variable"):
                if not var.get("name"):
                    results["errors"].append("Variable missing 'name' attribute")
                if not var.text:
                    results["warnings"].append("Variable has no value")

        # Check calculations
        calculations = behavior.find("calculations")
        if calculations is not None:
            for calc in calculations.findall("calculation"):
                if not calc.get("name"):
                    results["errors"].append("Calculation missing 'name' attribute")
                if not calc.get("formula"):
                    results["errors"].append("Calculation missing 'formula' attribute")

    def _validate_arx_physics(self, physics: ET.Element, results: Dict[str, Any]):
        """Validate arx:physics element."""
        # Check mass
        mass = physics.find("mass")
        if mass is not None:
            if not mass.text:
                results["errors"].append("Mass element has no value")
            else:
                try:
                    float(mass.text)
                except ValueError:
                    results["errors"].append("Mass value must be numeric")

        # Check forces
        forces = physics.find("forces")
        if forces is not None:
            for force in forces.findall("force"):
                if not force.get("type"):
                    results["errors"].append("Force missing 'type' attribute")
                if force.get("value"):
                    try:
                        float(force.get("value"))
                    except ValueError:
                        results["errors"].append("Force value must be numeric")

    def is_valid(self, content: str) -> bool:
        """
        Quick validation check.

        Args:
            content: SVGX content as string

        Returns:
            True if valid, False otherwise
        """
        results = self.validate_schema(content)
        return results["valid"]
