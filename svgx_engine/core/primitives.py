"""
SVGX Engine - CAD Primitives

Defines core geometric primitives (Line, Arc, Circle, Rectangle, Polyline)
with micron precision and SVGX/XML serialization.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

from decimal import Decimal
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import xml.etree.ElementTree as ET
from svgx_engine.core.precision import precision_manager, PrecisionLevel


@dataclass
class Line:
    start_x: Decimal
    start_y: Decimal
    end_x: Decimal
    end_y: Decimal
    precision_level: PrecisionLevel = PrecisionLevel.MICRON

    def to_svgx(self) -> ET.Element:
        el = ET.Element("line")
        el.set("start_x", str(self.start_x))
        el.set("start_y", str(self.start_y))
        el.set("end_x", str(self.end_x))
        el.set("end_y", str(self.end_y))
        el.set("precision_level", self.precision_level.name)
        return el


@dataclass
class Arc:
    center_x: Decimal
    center_y: Decimal
    radius: Decimal
    start_angle: Decimal
    end_angle: Decimal
    precision_level: PrecisionLevel = PrecisionLevel.MICRON

    def to_svgx(self) -> ET.Element:
        el = ET.Element("arc")
        el.set("center_x", str(self.center_x))
        el.set("center_y", str(self.center_y))
        el.set("radius", str(self.radius))
        el.set("start_angle", str(self.start_angle))
        el.set("end_angle", str(self.end_angle))
        el.set("precision_level", self.precision_level.name)
        return el


@dataclass
class Circle:
    center_x: Decimal
    center_y: Decimal
    radius: Decimal
    precision_level: PrecisionLevel = PrecisionLevel.MICRON

    def to_svgx(self) -> ET.Element:
        el = ET.Element("circle")
        el.set("center_x", str(self.center_x))
        el.set("center_y", str(self.center_y))
        el.set("radius", str(self.radius))
        el.set("precision_level", self.precision_level.name)
        return el


@dataclass
class Rectangle:
    x: Decimal
    y: Decimal
    width: Decimal
    height: Decimal
    precision_level: PrecisionLevel = PrecisionLevel.MICRON

    def to_svgx(self) -> ET.Element:
        el = ET.Element("rectangle")
        el.set("x", str(self.x))
        el.set("y", str(self.y))
        el.set("width", str(self.width))
        el.set("height", str(self.height))
        el.set("precision_level", self.precision_level.name)
        return el


@dataclass
class Polyline:
    points: List[Dict[str, Decimal]] = field(default_factory=list)
    closed: bool = False
    precision_level: PrecisionLevel = PrecisionLevel.MICRON

    def to_svgx(self) -> ET.Element:
        el = ET.Element("polyline")
        el.set("closed", str(self.closed))
        el.set("precision_level", self.precision_level.name)
        for pt in self.points:
            pt_el = ET.SubElement(el, "point")
            pt_el.set("x", str(pt["x"]))
            pt_el.set("y", str(pt["y"]))
        return el
