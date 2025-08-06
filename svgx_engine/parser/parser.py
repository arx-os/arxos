"""
SVGX Parser for parsing SVGX files with extended SVG syntax.

This parser handles the arx:object, arx:system, arx:behavior elements
and attributes that extend standard SVG with semantic markup and
programmable behavior.
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SVGXElement:
    """Represents an SVGX element with extended attributes."""

    def __init__(
        self,
        tag: str,
        attributes: Dict[str, str],
        content: str = "",
        position: List[float] = None,
    ):
        self.tag = tag
        self.attributes = attributes
        self.content = content
        self.position = position or [0, 0]
        self.children = []
        self.arx_object = None
        self.arx_behavior = None
        self.arx_physics = None

    def add_child(self, child: "SVGXElement"):
        """Add a child element."""
        self.children.append(child)

    def get_arx_attribute(self, name: str) -> Optional[str]:
        """Get an arx: namespace attribute."""
        return self.attributes.get(f"arx:{name}")

    def has_arx_object(self) -> bool:
        """Check if element has arx:object data."""
        return any(key.startswith("arx:") for key in self.attributes.keys())


class ArxObject:
    """Represents an arx:object with semantic data."""

    def __init__(self, object_id: str, object_type: str, system: str = None):
        self.object_id = object_id
        self.object_type = object_type
        self.system = system
        self.properties = {}
        self.geometry = None
        self.behavior = None
        self.physics = None

    def add_property(self, key: str, value: Any):
        """Add a property to the object."""
        self.properties[key] = value


class ArxBehavior:
    """Represents arx:behavior with programmable logic."""

    def __init__(self):
        self.variables = {}
        self.calculations = {}
        self.triggers = []

    def add_variable(self, name: str, value: float, unit: str = None):
        """Add a variable to the behavior."""
        self.variables[name] = {"value": value, "unit": unit}

    def add_calculation(self, name: str, formula: str):
        """Add a calculation to the behavior."""
        self.calculations[name] = formula

    def add_trigger(self, event: str, action: str):
        """Add a trigger to the behavior."""
        self.triggers.append({"event": event, "action": action})


class ArxPhysics:
    """Represents arx:physics with physical properties."""

    def __init__(self):
        self.mass = None
        self.anchor = None
        self.forces = []

    def set_mass(self, mass: float, unit: str = "kg"):
        """Set the mass of the object."""
        self.mass = {"value": mass, "unit": unit}

    def set_anchor(self, anchor: str):
        """Set the anchor point."""
        self.anchor = anchor

    def add_force(self, force_type: str, direction: str = None, value: float = None):
        """Add a force to the physics."""
        self.forces.append({"type": force_type, "direction": direction, "value": value})


class SVGXParser:
    """Parser for SVGX files with extended SVG syntax."""

    def __init__(self):
        self.supported_elements = {
            "rect",
            "circle",
            "ellipse",
            "line",
            "polyline",
            "polygon",
            "path",
            "text",
            "g",
            "svg",
            "arx:object",
            "arx:system",
            "arx:behavior",
        }
        self.arx_namespace = "http://arxos.io/svgx"

    def parse(self, svgx_content: str) -> List[SVGXElement]:
        """
        Parse SVGX content and extract elements with arx extensions.

        Args:
            svgx_content: SVGX content as string

        Returns:
            List of parsed SVGX elements
        """
        try:
            # Register the arx namespace
            ET.register_namespace("arx", self.arx_namespace)

            root = ET.fromstring(svgx_content)
            elements = []

            # Parse root SVG element
            svg_attrs = self._extract_attributes(root)
            svg_element = SVGXElement("svg", svg_attrs, "", [0, 0])
            elements.append(svg_element)

            # Parse child elements
            for child in root.iter():
                if child.tag in self.supported_elements and child != root:
                    element = self._parse_element(child)
                    if element:
                        elements.append(element)
                        svg_element.add_child(element)

            return elements

        except ET.ParseError as e:
            raise ValueError(f"Invalid SVGX content: {e}")
        except Exception as e:
            logger.error(f"Failed to parse SVGX: {e}")
            raise ValueError(f"Failed to parse SVGX: {e}")

    def _parse_element(self, element: ET.Element) -> Optional[SVGXElement]:
        """Parse individual SVGX element with arx extensions."""
        try:
            tag = element.tag
            attributes = self._extract_attributes(element)
            content = element.text or ""
            position = self._extract_position(attributes)

            svgx_element = SVGXElement(tag, attributes, content, position)

            # Parse arx:object data
            if self._has_arx_object_data(element):
                svgx_element.arx_object = self._parse_arx_object(element)

            # Parse arx:behavior data
            if self._has_arx_behavior_data(element):
                svgx_element.arx_behavior = self._parse_arx_behavior(element)

            # Parse arx:physics data
            if self._has_arx_physics_data(element):
                svgx_element.arx_physics = self._parse_arx_physics(element)

            return svgx_element

        except Exception as e:
            logger.warning(f"Failed to parse element {element.tag}: {e}")
            return None

    def _extract_attributes(self, element: ET.Element) -> Dict[str, str]:
        """Extract attributes from SVGX element."""
        attributes = {}
        for key, value in element.attrib.items():
            attributes[key] = value
        return attributes

    def _extract_position(self, attributes: Dict[str, str]) -> List[float]:
        """Extract position from element attributes."""
        x = float(attributes.get("x", 0))
        y = float(attributes.get("y", 0))
        return [x, y]

    def _has_arx_object_data(self, element: ET.Element) -> bool:
        """Check if element has arx:object data."""
        return any(key.startswith("arx:") for key in element.attrib.keys())

    def _has_arx_behavior_data(self, element: ET.Element) -> bool:
        """Check if element has arx:behavior data."""
        return element.find("arx:behavior") is not None

    def _has_arx_physics_data(self, element: ET.Element) -> bool:
        """Check if element has arx:physics data."""
        return element.find("arx:physics") is not None

    def _parse_arx_object(self, element: ET.Element) -> ArxObject:
        """Parse arx:object data from element."""
        arx_object = ArxObject(
            object_id=element.get("arx:object-id", element.get("id", "")),
            object_type=element.get("arx:object-type", "unknown"),
            system=element.get("arx:system"),
        )

        # Extract object properties
        for key, value in element.attrib.items():
            if key.startswith("arx:") and not key in [
                "arx:object-id",
                "arx:object-type",
                "arx:system",
            ]:
                prop_name = key.replace("arx:", "")
                arx_object.add_property(prop_name, value)

        return arx_object

    def _parse_arx_behavior(self, element: ET.Element) -> ArxBehavior:
        """Parse arx:behavior data from element."""
        behavior = ArxBehavior()

        behavior_elem = element.find("arx:behavior")
        if behavior_elem is not None:
            # Parse variables
            variables_elem = behavior_elem.find("variables")
            if variables_elem is not None:
                for var_elem in variables_elem.findall("variable"):
                    name = var_elem.get("name")
                    value = float(var_elem.text or 0)
                    unit = var_elem.get("unit")
                    behavior.add_variable(name, value, unit)

            # Parse calculations
            calculations_elem = behavior_elem.find("calculations")
            if calculations_elem is not None:
                for calc_elem in calculations_elem.findall("calculation"):
                    name = calc_elem.get("name")
                    formula = calc_elem.get("formula")
                    behavior.add_calculation(name, formula)

            # Parse triggers
            triggers_elem = behavior_elem.find("triggers")
            if triggers_elem is not None:
                for trigger_elem in triggers_elem.findall("trigger"):
                    event = trigger_elem.get("event")
                    action = trigger_elem.get("action")
                    behavior.add_trigger(event, action)

        return behavior

    def _parse_arx_physics(self, element: ET.Element) -> ArxPhysics:
        """Parse arx:physics data from element."""
        physics = ArxPhysics()

        physics_elem = element.find("arx:physics")
        if physics_elem is not None:
            # Parse mass
            mass_elem = physics_elem.find("mass")
            if mass_elem is not None:
                mass_value = float(mass_elem.text or 0)
                mass_unit = mass_elem.get("unit", "kg")
                physics.set_mass(mass_value, mass_unit)

            # Parse anchor
            anchor_elem = physics_elem.find("anchor")
            if anchor_elem is not None:
                physics.set_anchor(anchor_elem.text)

            # Parse forces
            forces_elem = physics_elem.find("forces")
            if forces_elem is not None:
                for force_elem in forces_elem.findall("force"):
                    force_type = force_elem.get("type")
                    direction = force_elem.get("direction")
                    value = (
                        float(force_elem.get("value", 0))
                        if force_elem.get("value")
                        else None
                    )
                    physics.add_force(force_type, direction, value)

        return physics

    def parse_file(self, file_path: str) -> List[SVGXElement]:
        """
        Parse SVGX file and extract elements.

        Args:
            file_path: Path to SVGX file

        Returns:
            List of parsed SVGX elements
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                svgx_content = f.read()
            return self.parse(svgx_content)
        except FileNotFoundError:
            raise ValueError(f"SVGX file not found: {file_path}")
        except Exception as e:
            raise ValueError(f"Failed to parse SVGX file: {e}")

    def validate_svgx(self, svgx_content: str) -> bool:
        """
        Validate SVGX content against schema.

        Args:
            svgx_content: SVGX content to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Basic validation - check for required namespaces
            if 'xmlns:arx="http://arxos.io/svgx"' not in svgx_content:
                return False

            # Parse the content to check for well-formed XML
            ET.fromstring(svgx_content)
            return True

        except ET.ParseError:
            return False
        except Exception:
            return False
