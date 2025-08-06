"""
Enhanced Symbol Recognition Engine for SVGX Engine

This module provides advanced symbol recognition with fuzzy matching,
context awareness, and integration with the SVGX precision system.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
import xml.etree.ElementTree as ET
import os
from difflib import SequenceMatcher
from collections import defaultdict

# SVGX Engine imports
from svgx_engine.core.precision_coordinate import PrecisionCoordinate
from svgx_engine.core.precision_math import PrecisionMath
from svgx_engine.core.precision_validator import PrecisionValidator
from svgx_engine.core.precision_errors import ValidationError
from svgx_engine.logging.logging_config import get_logger

logger = get_logger(__name__)


class SymbolRecognitionEngine:
    """Enhanced engine for recognizing building system symbols with fuzzy matching and context awareness."""

    def __init__(self):
        self.symbol_library = self._load_complete_symbol_library()
        self.recognition_patterns = self._build_recognition_patterns()
        self.context_rules = self._build_context_rules()
        self.validation_rules = self._build_validation_rules()
        self.precision_math = PrecisionMath()
        self.precision_validator = PrecisionValidator()

    def _load_complete_symbol_library(self) -> Dict[str, Any]:
        """Load both hardcoded symbols and JSON symbol library with architectural/engineering symbols."""
        # Start with hardcoded symbols
        symbols = self._get_hardcoded_symbols()

        # Add architectural/engineering symbols
        self._add_architectural_symbols(symbols)
        self._add_engineering_symbols(symbols)

        logger.info(f"Loaded {len(symbols)} symbols for recognition")
        return symbols

    def _get_hardcoded_symbols(self) -> Dict[str, Any]:
        """Get hardcoded SVG symbols for basic recognition."""
        return {
            "circle": {
                "system": "geometric",
                "display_name": "Circle",
                "category": "geometric",
                "svg": '<circle cx="0" cy="0" r="1"/>',
                "tags": ["circle", "round", "geometric"],
                "validation_rules": ["must_have_radius"],
            },
            "rectangle": {
                "system": "geometric",
                "display_name": "Rectangle",
                "category": "geometric",
                "svg": '<rect x="0" y="0" width="1" height="1"/>',
                "tags": ["rectangle", "square", "geometric"],
                "validation_rules": ["must_have_dimensions"],
            },
            "line": {
                "system": "geometric",
                "display_name": "Line",
                "category": "geometric",
                "svg": '<line x1="0" y1="0" x2="1" y2="1"/>',
                "tags": ["line", "straight", "geometric"],
                "validation_rules": ["must_have_endpoints"],
            },
        }

    def _add_architectural_symbols(self, symbols: Dict[str, Any]):
        """Add architectural symbols to the library."""
        arch_symbols = {
            "wall": {
                "system": "structural",
                "display_name": "Wall",
                "category": "structural",
                "architectural_type": "wall",
                "tags": ["wall", "partition", "structural"],
                "validation_rules": ["must_have_thickness", "must_have_material"],
            },
            "door": {
                "system": "architectural",
                "display_name": "Door",
                "category": "architectural",
                "architectural_type": "door",
                "tags": ["door", "entrance", "exit"],
                "validation_rules": ["must_have_width", "must_have_height"],
            },
            "window": {
                "system": "architectural",
                "display_name": "Window",
                "category": "architectural",
                "architectural_type": "window",
                "tags": ["window", "glazing", "opening"],
                "validation_rules": ["must_have_width", "must_have_height"],
            },
            "column": {
                "system": "structural",
                "display_name": "Column",
                "category": "structural",
                "architectural_type": "column",
                "tags": ["column", "pillar", "support"],
                "validation_rules": ["must_have_dimensions"],
            },
            "beam": {
                "system": "structural",
                "display_name": "Beam",
                "category": "structural",
                "architectural_type": "beam",
                "tags": ["beam", "girder", "support"],
                "validation_rules": ["must_have_dimensions"],
            },
        }
        symbols.update(arch_symbols)

    def _add_engineering_symbols(self, symbols: Dict[str, Any]):
        """Add engineering symbols to the library."""
        eng_symbols = {
            "hvac_duct": {
                "system": "mechanical",
                "display_name": "HVAC Duct",
                "category": "mechanical",
                "engineering_type": "hvac",
                "tags": ["duct", "hvac", "air", "mechanical"],
                "validation_rules": ["must_have_diameter", "must_have_flow_rate"],
            },
            "electrical_outlet": {
                "system": "electrical",
                "display_name": "Electrical Outlet",
                "category": "electrical",
                "engineering_type": "electrical",
                "tags": ["outlet", "electrical", "power"],
                "validation_rules": ["must_have_voltage", "must_have_amperage"],
            },
            "light_fixture": {
                "system": "electrical",
                "display_name": "Light Fixture",
                "category": "electrical",
                "engineering_type": "lighting",
                "tags": ["light", "fixture", "electrical", "illumination"],
                "validation_rules": ["must_have_wattage", "must_have_lumens"],
            },
            "sprinkler": {
                "system": "fire_protection",
                "display_name": "Sprinkler",
                "category": "fire_protection",
                "engineering_type": "fire_suppression",
                "tags": ["sprinkler", "fire", "protection", "water"],
                "validation_rules": ["must_have_coverage_area", "must_have_flow_rate"],
            },
            "pipe": {
                "system": "plumbing",
                "display_name": "Pipe",
                "category": "plumbing",
                "engineering_type": "plumbing",
                "tags": ["pipe", "plumbing", "water", "gas"],
                "validation_rules": ["must_have_diameter", "must_have_material"],
            },
        }
        symbols.update(eng_symbols)

    def _build_context_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build context-aware interpretation rules."""
        return {
            "structural": [
                {"rule": "walls_must_be_vertical", "priority": 1},
                {"rule": "columns_must_be_vertical", "priority": 1},
                {"rule": "beams_must_be_horizontal", "priority": 1},
            ],
            "mechanical": [
                {"rule": "ducts_must_have_clearance", "priority": 2},
                {"rule": "equipment_must_be_accessible", "priority": 2},
            ],
            "electrical": [
                {"rule": "outlets_must_be_accessible", "priority": 2},
                {"rule": "wiring_must_be_concealed", "priority": 1},
            ],
            "fire_protection": [
                {"rule": "sprinklers_must_have_coverage", "priority": 3},
                {"rule": "exits_must_be_accessible", "priority": 3},
            ],
        }

    def _build_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Build validation rules for symbols."""
        return {
            "must_have_thickness": {
                "type": "numeric",
                "min_value": 0.1,
                "max_value": 2.0,
                "unit": "meters",
                "required": True,
            },
            "must_have_material": {
                "type": "string",
                "allowed_values": ["concrete", "steel", "wood", "masonry"],
                "required": True,
            },
            "must_have_width": {
                "type": "numeric",
                "min_value": 0.5,
                "max_value": 5.0,
                "unit": "meters",
                "required": True,
            },
            "must_have_height": {
                "type": "numeric",
                "min_value": 1.5,
                "max_value": 10.0,
                "unit": "meters",
                "required": True,
            },
            "must_have_dimensions": {
                "type": "numeric",
                "min_value": 0.1,
                "max_value": 10.0,
                "unit": "meters",
                "required": True,
            },
            "must_have_diameter": {
                "type": "numeric",
                "min_value": 0.01,
                "max_value": 2.0,
                "unit": "meters",
                "required": True,
            },
            "must_have_flow_rate": {
                "type": "numeric",
                "min_value": 0.1,
                "max_value": 1000.0,
                "unit": "lpm",
                "required": True,
            },
            "must_have_voltage": {
                "type": "numeric",
                "min_value": 110,
                "max_value": 480,
                "unit": "volts",
                "required": True,
            },
            "must_have_amperage": {
                "type": "numeric",
                "min_value": 1,
                "max_value": 100,
                "unit": "amps",
                "required": True,
            },
            "must_have_wattage": {
                "type": "numeric",
                "min_value": 1,
                "max_value": 10000,
                "unit": "watts",
                "required": True,
            },
            "must_have_lumens": {
                "type": "numeric",
                "min_value": 100,
                "max_value": 100000,
                "unit": "lumens",
                "required": True,
            },
            "must_have_coverage_area": {
                "type": "numeric",
                "min_value": 1,
                "max_value": 1000,
                "unit": "square_meters",
                "required": True,
            },
        }

    def fuzzy_match_symbols(
        self, query: str, threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """Find symbols using fuzzy matching with precision validation."""
        matches = []
        query_lower = query.lower()

        for symbol_id, symbol_data in self.symbol_library.items():
            # Check exact matches first
            if query_lower == symbol_id.lower():
                matches.append(
                    {
                        "symbol_id": symbol_id,
                        "confidence": 1.0,
                        "match_type": "exact",
                        "symbol_data": symbol_data,
                    }
                )
                continue

            # Check display name matches
            display_name = symbol_data.get("display_name", "").lower()
            if query_lower == display_name:
                matches.append(
                    {
                        "symbol_id": symbol_id,
                        "confidence": 0.95,
                        "match_type": "display_name",
                        "symbol_data": symbol_data,
                    }
                )
                continue

            # Check tag matches
            tags = symbol_data.get("tags", [])
            for tag in tags:
                if query_lower == tag.lower():
                    matches.append(
                        {
                            "symbol_id": symbol_id,
                            "confidence": 0.9,
                            "match_type": "tag",
                            "symbol_data": symbol_data,
                        }
                    )
                    break

            # Fuzzy matching
            max_ratio = 0
            for text_to_check in [symbol_id, display_name] + tags:
                ratio = SequenceMatcher(
                    None, query_lower, text_to_check.lower()
                ).ratio()
                max_ratio = max(max_ratio, ratio)

            if max_ratio >= threshold:
                matches.append(
                    {
                        "symbol_id": symbol_id,
                        "confidence": max_ratio,
                        "match_type": "fuzzy",
                        "symbol_data": symbol_data,
                    }
                )

        # Sort by confidence
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        return matches

    def context_aware_interpretation(
        self, symbol_id: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Interpret symbol based on context with precision validation."""
        if symbol_id not in self.symbol_library:
            return {"error": f"Symbol {symbol_id} not found"}

        symbol_data = self.symbol_library[symbol_id]
        system = symbol_data.get("system", "unknown")

        # Apply context rules
        context_rules = self.context_rules.get(system, [])
        interpretations = []

        for rule in context_rules:
            rule_name = rule["rule"]
            priority = rule["priority"]

            if rule_name == "walls_must_be_vertical":
                if symbol_data.get("architectural_type") == "wall":
                    interpretations.append(
                        {
                            "rule": rule_name,
                            "priority": priority,
                            "interpretation": "Wall must be vertical with 90-degree angles",
                            "constraints": {"rotation_z": 0.0, "tolerance": 0.01},
                        }
                    )

            elif rule_name == "columns_must_be_vertical":
                if symbol_data.get("architectural_type") == "column":
                    interpretations.append(
                        {
                            "rule": rule_name,
                            "priority": priority,
                            "interpretation": "Column must be vertical",
                            "constraints": {"rotation_z": 0.0, "tolerance": 0.01},
                        }
                    )

            elif rule_name == "beams_must_be_horizontal":
                if symbol_data.get("architectural_type") == "beam":
                    interpretations.append(
                        {
                            "rule": rule_name,
                            "priority": priority,
                            "interpretation": "Beam must be horizontal",
                            "constraints": {"rotation_z": 0.0, "tolerance": 0.01},
                        }
                    )

        return {
            "symbol_id": symbol_id,
            "symbol_data": symbol_data,
            "context": context,
            "interpretations": interpretations,
            "system": system,
        }

    def validate_symbol(
        self, symbol_id: str, properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate symbol properties using precision validation."""
        if symbol_id not in self.symbol_library:
            return {"error": f"Symbol {symbol_id} not found"}

        symbol_data = self.symbol_library[symbol_id]
        validation_rules = symbol_data.get("validation_rules", [])
        validation_results = []

        for rule_name in validation_rules:
            rule_config = self.validation_rules.get(rule_name)
            if not rule_config:
                continue

            rule_type = rule_config["type"]
            required = rule_config.get("required", False)

            if rule_type == "numeric":
                min_value = rule_config.get("min_value")
                max_value = rule_config.get("max_value")
                unit = rule_config.get("unit", "")

                # Find the property value
                property_value = None
                for prop_name, prop_value in properties.items():
                    if rule_name.lower().replace("must_have_", "") in prop_name.lower():
                        property_value = prop_value
                        break

                if property_value is None and required:
                    validation_results.append(
                        {
                            "rule": rule_name,
                            "status": "error",
                            "message": f"Required property {rule_name} not found",
                        }
                    )
                elif property_value is not None:
                    try:
                        value = float(property_value)
                        if min_value is not None and value < min_value:
                            validation_results.append(
                                {
                                    "rule": rule_name,
                                    "status": "error",
                                    "message": f"Value {value} is below minimum {min_value} {unit}",
                                }
                            )
                        elif max_value is not None and value > max_value:
                            validation_results.append(
                                {
                                    "rule": rule_name,
                                    "status": "error",
                                    "message": f"Value {value} is above maximum {max_value} {unit}",
                                }
                            )
                        else:
                            validation_results.append(
                                {
                                    "rule": rule_name,
                                    "status": "valid",
                                    "message": f"Value {value} is within valid range",
                                }
                            )
                    except (ValueError, TypeError):
                        validation_results.append(
                            {
                                "rule": rule_name,
                                "status": "error",
                                "message": f"Invalid numeric value: {property_value}",
                            }
                        )

            elif rule_type == "string":
                allowed_values = rule_config.get("allowed_values", [])

                # Find the property value
                property_value = None
                for prop_name, prop_value in properties.items():
                    if rule_name.lower().replace("must_have_", "") in prop_name.lower():
                        property_value = prop_value
                        break

                if property_value is None and required:
                    validation_results.append(
                        {
                            "rule": rule_name,
                            "status": "error",
                            "message": f"Required property {rule_name} not found",
                        }
                    )
                elif property_value is not None:
                    if allowed_values and property_value not in allowed_values:
                        validation_results.append(
                            {
                                "rule": rule_name,
                                "status": "error",
                                "message": f"Value {property_value} not in allowed values: {allowed_values}",
                            }
                        )
                    else:
                        validation_results.append(
                            {
                                "rule": rule_name,
                                "status": "valid",
                                "message": f"Value {property_value} is valid",
                            }
                        )

        return {
            "symbol_id": symbol_id,
            "validation_results": validation_results,
            "is_valid": all(
                result["status"] == "valid" for result in validation_results
            ),
        }

    def verify_symbol_placement(
        self, symbol_id: str, position: Dict[str, float], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify symbol placement using precision coordinates."""
        if symbol_id not in self.symbol_library:
            return {"error": f"Symbol {symbol_id} not found"}

        # Convert position to precision coordinates
        try:
            precision_position = PrecisionCoordinate(
                position.get("x", 0.0), position.get("y", 0.0), position.get("z", 0.0)
            )
        except Exception as e:
            return {"error": f"Invalid position coordinates: {e}"}

        symbol_data = self.symbol_library[symbol_id]
        placement_issues = []

        # Check for overlap with existing symbols
        existing_symbols = context.get("existing_symbols", [])
        for existing_symbol in existing_symbols:
            existing_pos = existing_symbol.get("position", {})
            existing_precision_pos = PrecisionCoordinate(
                existing_pos.get("x", 0.0),
                existing_pos.get("y", 0.0),
                existing_pos.get("z", 0.0),
            )

            # Calculate distance using precision math
            distance = self.precision_math.distance(
                precision_position, existing_precision_pos
            )

            if distance < 0.1:  # Minimum clearance
                placement_issues.append(
                    {
                        "type": "overlap",
                        "message": f"Symbol too close to existing symbol at distance {distance}",
                        "severity": "error",
                    }
                )

        # Check boundary constraints
        boundaries = context.get("boundaries", {})
        if boundaries:
            min_x = boundaries.get("min_x", float("-inf"))
            max_x = boundaries.get("max_x", float("inf"))
            min_y = boundaries.get("min_y", float("-inf"))
            max_y = boundaries.get("max_y", float("inf"))
            min_z = boundaries.get("min_z", float("-inf"))
            max_z = boundaries.get("max_z", float("inf"))

            if (
                precision_position.x < min_x
                or precision_position.x > max_x
                or precision_position.y < min_y
                or precision_position.y > max_y
                or precision_position.z < min_z
                or precision_position.z > max_z
            ):
                placement_issues.append(
                    {
                        "type": "boundary_violation",
                        "message": "Symbol placement outside allowed boundaries",
                        "severity": "error",
                    }
                )

        return {
            "symbol_id": symbol_id,
            "position": position,
            "precision_position": {
                "x": precision_position.x,
                "y": precision_position.y,
                "z": precision_position.z,
            },
            "placement_issues": placement_issues,
            "is_valid": len(placement_issues) == 0,
        }

    def _symbols_overlap(self, pos1: Dict[str, float], pos2: Dict[str, float]) -> bool:
        """Check if two symbols overlap using precision coordinates."""
        try:
            precision_pos1 = PrecisionCoordinate(
                pos1.get("x", 0.0), pos1.get("y", 0.0), pos1.get("z", 0.0)
            )
            precision_pos2 = PrecisionCoordinate(
                pos2.get("x", 0.0), pos2.get("y", 0.0), pos2.get("z", 0.0)
            )

            distance = self.precision_math.distance(precision_pos1, precision_pos2)
            return distance < 0.1  # Minimum clearance threshold
        except Exception:
            return False

    def _build_recognition_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build recognition patterns for different symbol types."""
        return {
            "geometric": [
                {"pattern": r"circle|round|circular", "confidence": 0.8},
                {"pattern": r"rect|rectangle|square", "confidence": 0.8},
                {"pattern": r"line|straight", "confidence": 0.7},
            ],
            "structural": [
                {"pattern": r"wall|partition", "confidence": 0.9},
                {"pattern": r"column|pillar|support", "confidence": 0.9},
                {"pattern": r"beam|girder", "confidence": 0.9},
            ],
            "architectural": [
                {"pattern": r"door|entrance|exit", "confidence": 0.9},
                {"pattern": r"window|glazing|opening", "confidence": 0.9},
            ],
            "mechanical": [
                {"pattern": r"duct|hvac|air", "confidence": 0.8},
                {"pattern": r"pipe|plumbing|water", "confidence": 0.8},
            ],
            "electrical": [
                {"pattern": r"outlet|electrical|power", "confidence": 0.8},
                {"pattern": r"light|fixture|illumination", "confidence": 0.8},
            ],
            "fire_protection": [
                {"pattern": r"sprinkler|fire|protection", "confidence": 0.9}
            ],
        }

    def _get_abbreviations(self, symbol_id: str, display_name: str) -> List[str]:
        """Generate abbreviations for symbol recognition."""
        abbreviations = []

        # Common abbreviations
        abbrev_map = {
            "wall": ["w", "wall"],
            "door": ["d", "dr", "door"],
            "window": ["w", "win", "window"],
            "column": ["col", "column"],
            "beam": ["b", "beam"],
            "hvac_duct": ["duct", "hvac"],
            "electrical_outlet": ["outlet", "elec"],
            "light_fixture": ["light", "fixture"],
            "sprinkler": ["spr", "sprinkler"],
            "pipe": ["p", "pipe"],
        }

        if symbol_id in abbrev_map:
            abbreviations.extend(abbrev_map[symbol_id])

        # Generate from display name
        words = display_name.lower().split()
        for word in words:
            if len(word) > 2:
                abbreviations.append(word[:3])
                abbreviations.append(word)

        return list(set(abbreviations))

    def _extract_shapes_from_svg(self, svg_content: str) -> List[Dict[str, Any]]:
        """Extract geometric shapes from SVG content."""
        shapes = []

        try:
            root = ET.fromstring(svg_content)

            for element in root.iter():
                shape_info = {}

                if element.tag.endswith("circle"):
                    shape_info = {
                        "type": "circle",
                        "cx": float(element.get("cx", 0)),
                        "cy": float(element.get("cy", 0)),
                        "r": float(element.get("r", 1)),
                    }
                elif element.tag.endswith("rect"):
                    shape_info = {
                        "type": "rectangle",
                        "x": float(element.get("x", 0)),
                        "y": float(element.get("y", 0)),
                        "width": float(element.get("width", 1)),
                        "height": float(element.get("height", 1)),
                    }
                elif element.tag.endswith("line"):
                    shape_info = {
                        "type": "line",
                        "x1": float(element.get("x1", 0)),
                        "y1": float(element.get("y1", 0)),
                        "x2": float(element.get("x2", 1)),
                        "y2": float(element.get("y2", 1)),
                    }
                elif element.tag.endswith("path"):
                    shape_info = {"type": "path", "d": element.get("d", "")}

                if shape_info:
                    shapes.append(shape_info)

        except ET.ParseError as e:
            logger.error(f"Error parsing SVG content: {e}")

        return shapes

    def recognize_symbols_in_content(
        self, content: str, content_type: str = "text"
    ) -> List[Dict[str, Any]]:
        """Recognize symbols in different types of content."""
        if content_type == "text":
            return self._recognize_from_text(content)
        elif content_type == "svg":
            return self._recognize_from_svg(content)
        else:
            return []

    def _recognize_from_text(self, text_content: str) -> List[Dict[str, Any]]:
        """Recognize symbols from text content."""
        recognized_symbols = []
        text_lower = text_content.lower()

        # Check each symbol in the library
        for symbol_id, symbol_data in self.symbol_library.items():
            confidence = 0.0
            match_type = "none"

            # Check exact matches
            if symbol_id.lower() in text_lower:
                confidence = 0.9
                match_type = "exact"
            elif symbol_data.get("display_name", "").lower() in text_lower:
                confidence = 0.85
                match_type = "display_name"
            else:
                # Check tags
                tags = symbol_data.get("tags", [])
                for tag in tags:
                    if tag.lower() in text_lower:
                        confidence = 0.8
                        match_type = "tag"
                        break

                # Check abbreviations
                if confidence == 0.0:
                    abbreviations = self._get_abbreviations(
                        symbol_id, symbol_data.get("display_name", "")
                    )
                    for abbrev in abbreviations:
                        if abbrev.lower() in text_lower:
                            confidence = 0.7
                            match_type = "abbreviation"
                            break

            if confidence > 0.0:
                recognized_symbols.append(
                    {
                        "symbol_id": symbol_id,
                        "confidence": confidence,
                        "match_type": match_type,
                        "symbol_data": symbol_data,
                        "context": text_content,
                    }
                )

        # Sort by confidence
        recognized_symbols.sort(key=lambda x: x["confidence"], reverse=True)
        return recognized_symbols

    def _recognize_from_svg(self, svg_content: str) -> List[Dict[str, Any]]:
        """Recognize symbols from SVG content."""
        recognized_symbols = []

        try:
            root = ET.fromstring(svg_content)
            shapes = self._recognize_shapes_in_svg(root)

            for shape in shapes:
                shape_type = shape.get("type", "")

                # Map shape types to symbols
                symbol_mapping = {
                    "circle": "circle",
                    "rectangle": "rectangle",
                    "line": "line",
                }

                if shape_type in symbol_mapping:
                    symbol_id = symbol_mapping[shape_type]
                    if symbol_id in self.symbol_library:
                        recognized_symbols.append(
                            {
                                "symbol_id": symbol_id,
                                "confidence": 0.9,
                                "match_type": "shape",
                                "symbol_data": self.symbol_library[symbol_id],
                                "shape_data": shape,
                            }
                        )

        except ET.ParseError as e:
            logger.error(f"Error parsing SVG content: {e}")

        return recognized_symbols

    def _recognize_shapes_in_svg(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Recognize geometric shapes in SVG element."""
        shapes = []

        for element in root.iter():
            shape_info = {}

            if element.tag.endswith("circle"):
                shape_info = {
                    "type": "circle",
                    "cx": float(element.get("cx", 0)),
                    "cy": float(element.get("cy", 0)),
                    "r": float(element.get("r", 1)),
                }
            elif element.tag.endswith("rect"):
                shape_info = {
                    "type": "rectangle",
                    "x": float(element.get("x", 0)),
                    "y": float(element.get("y", 0)),
                    "width": float(element.get("width", 1)),
                    "height": float(element.get("height", 1)),
                }
            elif element.tag.endswith("line"):
                shape_info = {
                    "type": "line",
                    "x1": float(element.get("x1", 0)),
                    "y1": float(element.get("y1", 0)),
                    "x2": float(element.get("x2", 1)),
                    "y2": float(element.get("y2", 1)),
                }
            elif element.tag.endswith("path"):
                shape_info = {"type": "path", "d": element.get("d", "")}

            if shape_info:
                shapes.append(shape_info)

        return shapes

    def get_symbol_metadata(self, symbol_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific symbol."""
        return self.symbol_library.get(symbol_id)

    def get_symbols_by_system(self, system: str) -> List[str]:
        """Get all symbols for a specific system."""
        return [
            symbol_id
            for symbol_id, symbol_data in self.symbol_library.items()
            if symbol_data.get("system") == system
        ]

    def get_symbols_by_category(self, category: str) -> List[str]:
        """Get all symbols for a specific category."""
        return [
            symbol_id
            for symbol_id, symbol_data in self.symbol_library.items()
            if symbol_data.get("category") == category
        ]

    def get_symbol_library_info(self) -> Dict[str, Any]:
        """Get information about the symbol library."""
        systems = set()
        categories = set()

        for symbol_data in self.symbol_library.values():
            systems.add(symbol_data.get("system", "unknown"))
            categories.add(symbol_data.get("category", "unknown"))

        return {
            "total_symbols": len(self.symbol_library),
            "systems": list(systems),
            "categories": list(categories),
            "symbol_ids": list(self.symbol_library.keys()),
        }
