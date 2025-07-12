"""
Property-Based Tests for SVG-BIM System (using hypothesis)

- Tests geometry, relationships, and assembly with randomized and edge-case data
"""

import unittest
from hypothesis import given, strategies as st
from ..models.bim import Geometry, GeometryType, Room, Wall, Device, BIMModel, RoomType, SystemType, DeviceCategory
from ..services.bim_assembly import BIMAssemblyPipeline

class TestGeometryPropertyBased(unittest.TestCase):
    @given(
        st.lists(st.tuples(st.floats(-1e6, 1e6), st.floats(-1e6, 1e6)), min_size=3, max_size=10)
    )
    def test_polygon_geometry_valid(self, coords):
        # Ensure closed polygon
        if coords and coords[0] != coords[-1]:
            coords.append(coords[0])
        geom = Geometry(type=GeometryType.POLYGON, coordinates=[coords])
        self.assertEqual(geom.type, GeometryType.POLYGON)
        self.assertTrue(len(geom.coordinates[0]) >= 4)

    @given(
        st.lists(st.tuples(st.floats(-1e6, 1e6), st.floats(-1e6, 1e6)), min_size=2, max_size=20)
    )
    def test_linestring_geometry_valid(self, coords):
        geom = Geometry(type=GeometryType.LINESTRING, coordinates=coords)
        self.assertEqual(geom.type, GeometryType.LINESTRING)
        self.assertTrue(len(geom.coordinates) >= 2)

class TestRelationshipPropertyBased(unittest.TestCase):
    @given(
        st.lists(st.text(min_size=1, max_size=10), min_size=2, max_size=10)
    )
    def test_room_relationships(self, names):
        # Create rooms and link as neighbors
        rooms = [Room(name=n, geometry=Geometry(type=GeometryType.POLYGON, coordinates=[[(0,0),(1,0),(1,1),(0,1),(0,0)]]), room_type=RoomType.OFFICE) for n in names]
        for i in range(len(rooms)-1):
            rooms[i].add_child(rooms[i+1].id)
        # Check relationships
        for i in range(len(rooms)-1):
            self.assertIn(rooms[i+1].id, rooms[i].children)

class TestAssemblyPropertyBased(unittest.TestCase):
    @given(
        st.lists(
            st.fixed_dictionaries({
                "type": st.sampled_from(["room", "wall", "device"]),
                "name": st.text(min_size=1, max_size=10),
                "coordinates": st.lists(st.tuples(st.floats(-1e3, 1e3), st.floats(-1e3, 1e3)), min_size=2, max_size=10),
                "room_type": st.sampled_from(["office", "conference", "general"]),
                "system": st.sampled_from(["hvac", "electrical", "plumbing"]),
                "category": st.sampled_from(["ahu", "vav", "outlet"]),
            }),
            min_size=1, max_size=10
        )
    )
    def test_bim_assembly_pipeline(self, elements):
        pipeline = BIMAssemblyPipeline()
        svg_data = {"elements": elements}
        try:
            result = pipeline.assemble_bim(svg_data)
            self.assertTrue(result.success)
            self.assertGreaterEqual(len(result.elements), 0)
        except Exception as e:
            # Should not raise for valid random input
            self.fail(f"Assembly failed: {e}") 