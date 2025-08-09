"""
Tests for SVGX Parser.
"""

import pytest
from svgx_engine.parser import SVGXParser, SVGXElement


class TestSVGXParser:
    """Test cases for SVGX Parser."""

    def setup_method(self):
        """Setup test fixtures."""
        self.parser = SVGXParser()

    def test_parse_basic_svgx(self):
        """Test parsing basic SVGX content."""
        svgx_content = """
        <svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
            <arx:object id="test_obj" type="test_type" system="test_system">
                <arx:geometry x="0" y="0" width="100mm" height="100mm"/>
            </arx:object>
            <rect x="0" y="0" width="100" height="100" arx:layer="test_layer"/>
        </svg>
        """

        elements = self.parser.parse(svgx_content)

        assert len(elements) > 0
        assert elements[0].tag == 'svg'

    def test_validate_svgx(self):
        """Test SVGX validation."""
        valid_svgx = """
        <svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
            <rect x="0" y="0" width="100" height="100"/>
        </svg>
        """

        invalid_svgx = """
        <svg>
            <rect x="0" y="0" width="100" height="100"/>
        </svg>
        """

        assert self.parser.validate_svgx(valid_svgx) is True
        assert self.parser.validate_svgx(invalid_svgx) is False

    def test_parse_arx_object(self):
        """Test parsing arx:object elements."""
        svgx_content = """
        <svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
            <arx:object id="obj1" type="electrical.light_fixture" system="electrical">
                <arx:behavior>
                    <variables>
                        <variable name="voltage" unit="V">120</variable>
                    </variables>
                </arx:behavior>
            </arx:object>
        </svg>
        """

        elements = self.parser.parse(svgx_content)

        # Find arx:object element
        arx_objects = [elem for elem in elements if elem.tag == 'arx:object']
        assert len(arx_objects) == 1

        obj = arx_objects[0]
        assert obj.arx_object is not None
        assert obj.arx_object.object_id == "obj1"
        assert obj.arx_object.object_type == "electrical.light_fixture"
        assert obj.arx_object.system == "electrical"

    def test_parse_arx_behavior(self):
        """Test parsing arx:behavior elements."""
        svgx_content = """
        <svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
            <rect id="test_rect" x="0" y="0" width="100" height="100">
                <arx:behavior>
                    <variables>
                        <variable name="voltage" unit="V">120</variable>
                        <variable name="resistance" unit="ohm">720</variable>
                    </variables>
                    <calculations>
                        <calculation name="current" formula="voltage / resistance"/>
                        <calculation name="power" formula="voltage * current"/>
                    </calculations>
                </arx:behavior>
            </rect>
        </svg>
        """

        elements = self.parser.parse(svgx_content)

        # Find element with behavior
        elements_with_behavior = [elem for elem in elements if elem.arx_behavior is not None]
        assert len(elements_with_behavior) == 1

        behavior = elements_with_behavior[0].arx_behavior
        assert len(behavior.variables) == 2
        assert behavior.variables["voltage"]["value"] == 120
        assert behavior.variables["voltage"]["unit"] == "V"
        assert len(behavior.calculations) == 2
        assert behavior.calculations["current"] == "voltage / resistance"

    def test_parse_arx_physics(self):
        """Test parsing arx:physics elements."""
        svgx_content = """
        <svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
            <rect id="test_rect" x="0" y="0" width="100" height="100">
                <arx:physics>
                    <mass unit="kg">2.5</mass>
                    <anchor>ceiling</anchor>
                    <forces>
                        <force type="gravity" direction="down" value="9.81"/>
                    </forces>
                </arx:physics>
            </rect>
        </svg>
        """

        elements = self.parser.parse(svgx_content)

        # Find element with physics
        elements_with_physics = [elem for elem in elements if elem.arx_physics is not None]
        assert len(elements_with_physics) == 1

        physics = elements_with_physics[0].arx_physics
        assert physics.mass["value"] == 2.5
        assert physics.mass["unit"] == "kg"
        assert physics.anchor == "ceiling"
        assert len(physics.forces) == 1
        assert physics.forces[0]["type"] == "gravity"
        assert physics.forces[0]["direction"] == "down"
        assert physics.forces[0]["value"] == 9.81
