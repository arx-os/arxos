"""
Comprehensive tests for the enhanced BIM data models.
Tests all new features including validation, serialization, and new entity types.
"""

import pytest
import json
from datetime import datetime
from typing import List, Dict, Any

from ..models.bim import (
    Geometry, GeometryType, SystemType, RoomType, DeviceCategory,
    BIMElementBase, Room, Wall, Door, Window, HVACZone, AirHandler, VAVBox,
    ElectricalCircuit, ElectricalPanel, ElectricalOutlet,
    PlumbingSystem, PlumbingFixture, Valve,
    FireAlarmSystem, SmokeDetector, SecuritySystem, Camera,
    Device, Label, BIMModel, build_bim_model
)


class TestGeometry:
    """Test geometry validation and creation."""
    
    def test_valid_point_geometry(self):
        """Test valid point geometry creation."""
        geom = Geometry(
            type=GeometryType.POINT,
            coordinates=[10.0, 20.0]
        )
        assert geom.type == GeometryType.POINT
        assert geom.coordinates == [10.0, 20.0]
    
    def test_valid_linestring_geometry(self):
        """Test valid linestring geometry creation."""
        geom = Geometry(
            type=GeometryType.LINESTRING,
            coordinates=[[0, 0], [10, 0], [10, 10]]
        )
        assert geom.type == GeometryType.LINESTRING
        assert len(geom.coordinates) == 3
    
    def test_valid_polygon_geometry(self):
        """Test valid polygon geometry creation."""
        geom = Geometry(
            type=GeometryType.POLYGON,
            coordinates=[[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]
        )
        assert geom.type == GeometryType.POLYGON
        assert geom.coordinates[0][0] == geom.coordinates[0][-1]  # Closed
    
    def test_invalid_polygon_not_closed(self):
        """Test invalid polygon that is not closed."""
        with pytest.raises(ValueError, match="Polygon coordinates must be closed"):
            Geometry(
                type=GeometryType.POLYGON,
                coordinates=[[[0, 0], [10, 0], [10, 10], [0, 10]]]  # Not closed
            )
    
    def test_invalid_point_coordinates(self):
        """Test invalid point coordinates."""
        with pytest.raises(ValueError, match="Point coordinates must be"):
            Geometry(
                type=GeometryType.POINT,
                coordinates=[10.0]  # Missing y coordinate
            )
    
    def test_invalid_linestring_coordinates(self):
        """Test invalid linestring coordinates."""
        with pytest.raises(ValueError, match="LineString must have at least 2 points"):
            Geometry(
                type=GeometryType.LINESTRING,
                coordinates=[[0, 0]]  # Only one point
            )


class TestBIMElementBase:
    """Test base BIM element functionality."""
    
    def test_bim_element_creation(self):
        """Test basic BIM element creation."""
        geom = Geometry(type=GeometryType.POINT, coordinates=[0, 0])
        element = BIMElementBase(
            id="test-123",
            name="Test Element",
            geometry=geom
        )
        assert element.id == "test-123"
        assert element.name == "Test Element"
        assert element.geometry == geom
        assert element.children == []
        assert element.properties == {}
    
    def test_bim_element_with_children(self):
        """Test BIM element with children."""
        geom = Geometry(type=GeometryType.POINT, coordinates=[0, 0])
        element = BIMElementBase(
            id="parent-123",
            name="Parent Element",
            geometry=geom,
            children=["child-1", "child-2"]
        )
        assert len(element.children) == 2
        assert "child-1" in element.children
    
    def test_add_child_method(self):
        """Test adding child to BIM element."""
        geom = Geometry(type=GeometryType.POINT, coordinates=[0, 0])
        element = BIMElementBase(
            id="parent-123",
            name="Parent Element",
            geometry=geom
        )
        element.add_child("child-123")
        assert "child-123" in element.children
        assert len(element.children) == 1
    
    def test_remove_child_method(self):
        """Test removing child from BIM element."""
        geom = Geometry(type=GeometryType.POINT, coordinates=[0, 0])
        element = BIMElementBase(
            id="parent-123",
            name="Parent Element",
            geometry=geom,
            children=["child-1", "child-2"]
        )
        element.remove_child("child-1")
        assert "child-1" not in element.children
        assert "child-2" in element.children
    
    def test_add_property_method(self):
        """Test adding property to BIM element."""
        geom = Geometry(type=GeometryType.POINT, coordinates=[0, 0])
        element = BIMElementBase(
            id="test-123",
            name="Test Element",
            geometry=geom
        )
        element.add_property("material", "steel")
        element.add_property("color", "red")
        assert element.get_property("material") == "steel"
        assert element.get_property("color") == "red"
        assert element.get_property("nonexistent", "default") == "default"
    
    def test_invalid_id_validation(self):
        """Test ID validation."""
        geom = Geometry(type=GeometryType.POINT, coordinates=[0, 0])
        with pytest.raises(ValueError, match="ID cannot be empty"):
            BIMElementBase(
                id="",
                name="Test Element",
                geometry=geom
            )


class TestRoom:
    """Test Room entity type."""
    
    def test_room_creation(self):
        """Test basic room creation."""
        geom = Geometry(type=GeometryType.POLYGON, coordinates=[[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]])
        room = Room(
            name="Conference Room A",
            geometry=geom,
            room_type=RoomType.CONFERENCE,
            room_number="101",
            area=100.0,
            ceiling_height=3.0
        )
        assert room.name == "Conference Room A"
        assert room.room_type == RoomType.CONFERENCE
        assert room.room_number == "101"
        assert room.area == 100.0
        assert room.ceiling_height == 3.0
    
    def test_room_validation(self):
        """Test room validation."""
        geom = Geometry(type=GeometryType.POLYGON, coordinates=[[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]])
        
        # Test invalid area
        with pytest.raises(ValueError, match="Area must be positive"):
            Room(
                name="Invalid Room",
                geometry=geom,
                area=-10.0
            )
        
        # Test invalid volume
        with pytest.raises(ValueError, match="Volume must be positive"):
            Room(
                name="Invalid Room",
                geometry=geom,
                volume=-50.0
            )


class TestHVACElements:
    """Test HVAC system elements."""
    
    def test_hvac_zone_creation(self):
        """Test HVAC zone creation."""
        geom = Geometry(type=GeometryType.POLYGON, coordinates=[[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]])
        zone = HVACZone(
            name="Zone 1",
            geometry=geom,
            zone_type="thermal",
            temperature_setpoint=22.0,
            humidity_setpoint=50.0,
            airflow_requirement=100.0
        )
        assert zone.zone_type == "thermal"
        assert zone.temperature_setpoint == 22.0
        assert zone.humidity_setpoint == 50.0
        assert zone.airflow_requirement == 100.0
    
    def test_air_handler_creation(self):
        """Test air handler creation."""
        geom = Geometry(type=GeometryType.POINT, coordinates=[5, 5])
        ahu = AirHandler(
            name="AHU-01",
            geometry=geom,
            capacity=50000.0,
            airflow=2000.0,
            efficiency=0.85,
            manufacturer="Carrier",
            model="48TC"
        )
        assert ahu.system_type == SystemType.HVAC
        assert ahu.category == DeviceCategory.AHU
        assert ahu.capacity == 50000.0
        assert ahu.airflow == 2000.0
        assert ahu.efficiency == 0.85
        assert ahu.manufacturer == "Carrier"
    
    def test_vav_box_creation(self):
        """Test VAV box creation."""
        geom = Geometry(type=GeometryType.POINT, coordinates=[3, 3])
        vav = VAVBox(
            name="VAV-01",
            geometry=geom,
            max_airflow=500.0,
            min_airflow=50.0,
            reheat_capacity=5000.0,
            damper_type="butterfly",
            controller_type="DDC"
        )
        assert vav.system_type == SystemType.HVAC
        assert vav.category == DeviceCategory.VAV
        assert vav.max_airflow == 500.0
        assert vav.min_airflow == 50.0
        assert vav.reheat_capacity == 5000.0


class TestElectricalElements:
    """Test electrical system elements."""
    
    def test_electrical_circuit_creation(self):
        """Test electrical circuit creation."""
        geom = Geometry(type=GeometryType.LINESTRING, coordinates=[[0, 0], [10, 0]])
        circuit = ElectricalCircuit(
            name="Circuit A1",
            geometry=geom,
            circuit_type="power",
            voltage=120.0,
            amperage=20.0,
            phase="single",
            breaker_size=20.0,
            panel_id="panel-01"
        )
        assert circuit.circuit_type == "power"
        assert circuit.voltage == 120.0
        assert circuit.amperage == 20.0
        assert circuit.phase == "single"
        assert circuit.breaker_size == 20.0
    
    def test_electrical_panel_creation(self):
        """Test electrical panel creation."""
        geom = Geometry(type=GeometryType.POINT, coordinates=[0, 0])
        panel = ElectricalPanel(
            name="Panel A",
            geometry=geom,
            panel_type="distribution",
            voltage=480.0,
            amperage=100.0,
            phase="three",
            circuit_count=20,
            available_circuits=5
        )
        assert panel.system_type == SystemType.ELECTRICAL
        assert panel.category == DeviceCategory.PANEL
        assert panel.voltage == 480.0
        assert panel.amperage == 100.0
        assert panel.circuit_count == 20
    
    def test_electrical_outlet_creation(self):
        """Test electrical outlet creation."""
        geom = Geometry(type=GeometryType.POINT, coordinates=[5, 5])
        outlet = ElectricalOutlet(
            name="Outlet 1",
            geometry=geom,
            outlet_type="duplex",
            voltage=120.0,
            amperage=15.0,
            circuit_id="circuit-01",
            is_gfci=True,
            is_emergency=False
        )
        assert outlet.system_type == SystemType.ELECTRICAL
        assert outlet.category == DeviceCategory.OUTLET
        assert outlet.outlet_type == "duplex"
        assert outlet.voltage == 120.0
        assert outlet.is_gfci is True


class TestPlumbingElements:
    """Test plumbing system elements."""
    
    def test_plumbing_system_creation(self):
        """Test plumbing system creation."""
        geom = Geometry(type=GeometryType.LINESTRING, coordinates=[[0, 0], [20, 0]])
        system = PlumbingSystem(
            name="Cold Water System",
            geometry=geom,
            pipe_material="copper",
            pipe_size="1 inch",
            flow_rate=10.0,
            pressure=50.0,
            temperature=20.0
        )
        assert system.system_type == SystemType.PLUMBING
        assert system.pipe_material == "copper"
        assert system.pipe_size == "1 inch"
        assert system.flow_rate == 10.0
        assert system.pressure == 50.0
    
    def test_plumbing_fixture_creation(self):
        """Test plumbing fixture creation."""
        geom = Geometry(type=GeometryType.POINT, coordinates=[10, 10])
        fixture = PlumbingFixture(
            name="Sink 1",
            geometry=geom,
            fixture_type="sink",
            flow_rate=2.5,
            water_consumption=1.5,
            manufacturer="Kohler",
            model="K-1234"
        )
        assert fixture.system_type == SystemType.PLUMBING
        assert fixture.category == DeviceCategory.FIXTURE
        assert fixture.fixture_type == "sink"
        assert fixture.flow_rate == 2.5
    
    def test_valve_creation(self):
        """Test valve creation."""
        geom = Geometry(type=GeometryType.POINT, coordinates=[5, 5])
        valve = Valve(
            name="Valve 1",
            geometry=geom,
            valve_type="ball",
            size="1/2 inch",
            material="brass",
            pressure_rating=150.0,
            is_automatic=True,
            actuator_type="electric"
        )
        assert valve.system_type == SystemType.PLUMBING
        assert valve.category == DeviceCategory.VALVE
        assert valve.valve_type == "ball"
        assert valve.size == "1/2 inch"
        assert valve.is_automatic is True


class TestFireAlarmElements:
    """Test fire alarm system elements."""
    
    def test_fire_alarm_system_creation(self):
        """Test fire alarm system creation."""
        geom = Geometry(type=GeometryType.POINT, coordinates=[0, 0])
        system = FireAlarmSystem(
            name="Fire Alarm Panel",
            geometry=geom,
            panel_type="addressable",
            zone_count=8,
            device_count=24,
            battery_backup=True,
            emergency_power=True
        )
        assert system.system_type == SystemType.FIRE_ALARM
        assert system.panel_type == "addressable"
        assert system.zone_count == 8
        assert system.device_count == 24
        assert system.battery_backup is True
    
    def test_smoke_detector_creation(self):
        """Test smoke detector creation."""
        geom = Geometry(type=GeometryType.POINT, coordinates=[10, 10])
        detector = SmokeDetector(
            name="Smoke Detector 1",
            geometry=geom,
            detector_type="photoelectric",
            sensitivity="medium",
            coverage_area=900.0,
            battery_type="lithium",
            last_test_date=datetime(2023, 1, 1),
            next_test_date=datetime(2024, 1, 1)
        )
        assert detector.system_type == SystemType.FIRE_ALARM
        assert detector.category == DeviceCategory.SMOKE_DETECTOR
        assert detector.detector_type == "photoelectric"
        assert detector.coverage_area == 900.0


class TestSecurityElements:
    """Test security system elements."""
    
    def test_security_system_creation(self):
        """Test security system creation."""
        geom = Geometry(type=GeometryType.POINT, coordinates=[0, 0])
        system = SecuritySystem(
            name="Security System",
            geometry=geom,
            system_type_detail="access_control",
            device_count=12,
            zone_count=4,
            recording_capacity="30 days",
            backup_power=True
        )
        assert system.system_type == SystemType.SECURITY
        assert system.system_type_detail == "access_control"
        assert system.device_count == 12
        assert system.recording_capacity == "30 days"
    
    def test_camera_creation(self):
        """Test camera creation."""
        geom = Geometry(type=GeometryType.POINT, coordinates=[15, 15])
        camera = Camera(
            name="Camera 1",
            geometry=geom,
            camera_type="dome",
            resolution="1080p",
            field_of_view=90.0,
            night_vision=True,
            ptz_capable=True,
            recording_enabled=True,
            storage_location="NAS-01"
        )
        assert camera.system_type == SystemType.SECURITY
        assert camera.category == DeviceCategory.CAMERA
        assert camera.camera_type == "dome"
        assert camera.resolution == "1080p"
        assert camera.night_vision is True
        assert camera.ptz_capable is True


class TestBIMModel:
    """Test the main BIM model functionality."""
    
    def test_bim_model_creation(self):
        """Test basic BIM model creation."""
        model = BIMModel(
            name="Test Building",
            description="A test building model"
        )
        assert model.name == "Test Building"
        assert model.description == "A test building model"
        assert model.version == "1.0"
        assert len(model.rooms) == 0
        assert len(model.devices) == 0
    
    def test_add_element_method(self):
        """Test adding elements to BIM model."""
        model = BIMModel(name="Test Building")
        
        # Add a room
        room_geom = Geometry(type=GeometryType.POLYGON, coordinates=[[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]])
        room = Room(name="Room 1", geometry=room_geom)
        model.add_element(room)
        assert len(model.rooms) == 1
        assert model.rooms[0].name == "Room 1"
        
        # Add a device
        device_geom = Geometry(type=GeometryType.POINT, coordinates=[5, 5])
        device = Device(
            name="AHU-01",
            geometry=device_geom,
            system_type=SystemType.HVAC,
            category=DeviceCategory.AHU
        )
        model.add_element(device)
        assert len(model.devices) == 1
        assert model.devices[0].name == "AHU-01"
    
    def test_get_element_by_id(self):
        """Test getting element by ID."""
        model = BIMModel(name="Test Building")
        
        # Add elements with known IDs
        room_geom = Geometry(type=GeometryType.POLYGON, coordinates=[[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]])
        room = Room(id="room-123", name="Room 1", geometry=room_geom)
        model.add_element(room)
        
        device_geom = Geometry(type=GeometryType.POINT, coordinates=[5, 5])
        device = Device(
            id="device-456",
            name="Device 1",
            geometry=device_geom,
            system_type=SystemType.HVAC,
            category=DeviceCategory.AHU
        )
        model.add_element(device)
        
        # Test retrieval
        found_room = model.get_element_by_id("room-123")
        found_device = model.get_element_by_id("device-456")
        not_found = model.get_element_by_id("nonexistent")
        
        assert found_room is not None
        assert found_room.name == "Room 1"
        assert found_device is not None
        assert found_device.name == "Device 1"
        assert not_found is None
    
    def test_get_elements_by_system(self):
        """Test getting elements by system type."""
        model = BIMModel(name="Test Building")
        
        # Add HVAC elements
        ahu_geom = Geometry(type=GeometryType.POINT, coordinates=[0, 0])
        ahu = AirHandler(name="AHU-01", geometry=ahu_geom)
        model.add_element(ahu)
        
        vav_geom = Geometry(type=GeometryType.POINT, coordinates=[5, 5])
        vav = VAVBox(name="VAV-01", geometry=vav_geom)
        model.add_element(vav)
        
        # Add electrical elements
        panel_geom = Geometry(type=GeometryType.POINT, coordinates=[10, 10])
        panel = ElectricalPanel(name="Panel A", geometry=panel_geom)
        model.add_element(panel)
        
        # Test system filtering
        hvac_elements = model.get_elements_by_system(SystemType.HVAC)
        electrical_elements = model.get_elements_by_system(SystemType.ELECTRICAL)
        
        assert len(hvac_elements) == 2
        assert len(electrical_elements) == 1
        
        hvac_names = [elem.name for elem in hvac_elements]
        assert "AHU-01" in hvac_names
        assert "VAV-01" in hvac_names
    
    def test_validate_model(self):
        """Test BIM model validation."""
        model = BIMModel(name="Test Building")
        
        # Add elements with duplicate IDs (should cause validation error)
        room_geom = Geometry(type=GeometryType.POLYGON, coordinates=[[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]])
        room1 = Room(id="duplicate-id", name="Room 1", geometry=room_geom)
        room2 = Room(id="duplicate-id", name="Room 2", geometry=room_geom)
        model.add_element(room1)
        model.add_element(room2)
        
        # Add element with orphaned child reference
        device_geom = Geometry(type=GeometryType.POINT, coordinates=[5, 5])
        device = Device(
            name="Device 1",
            geometry=device_geom,
            system_type=SystemType.HVAC,
            category=DeviceCategory.AHU,
            children=["nonexistent-child"]
        )
        model.add_element(device)
        
        # Validate model
        errors = model.validate_model()
        assert len(errors) == 2
        assert "Duplicate ID found: duplicate-id" in errors
        assert "Orphaned child reference: nonexistent-child in" in errors
    
    def test_serialization_deserialization(self):
        """Test BIM model serialization and deserialization."""
        model = BIMModel(name="Test Building")
        
        # Add some elements
        room_geom = Geometry(type=GeometryType.POLYGON, coordinates=[[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]])
        room = Room(name="Room 1", geometry=room_geom, room_type=RoomType.OFFICE)
        model.add_element(room)
        
        device_geom = Geometry(type=GeometryType.POINT, coordinates=[5, 5])
        device = Device(
            name="AHU-01",
            geometry=device_geom,
            system_type=SystemType.HVAC,
            category=DeviceCategory.AHU
        )
        model.add_element(device)
        
        # Test to_dict
        model_dict = model.to_dict()
        assert model_dict['name'] == "Test Building"
        assert len(model_dict['rooms']) == 1
        assert len(model_dict['devices']) == 1
        assert model_dict['rooms'][0]['name'] == "Room 1"
        assert model_dict['devices'][0]['name'] == "AHU-01"
        
        # Test to_json
        json_str = model.to_json()
        assert isinstance(json_str, str)
        assert "Test Building" in json_str
        
        # Test from_dict
        reconstructed_model = BIMModel.from_dict(model_dict)
        assert reconstructed_model.name == "Test Building"
        assert len(reconstructed_model.rooms) == 1
        assert len(reconstructed_model.devices) == 1
        
        # Test from_json
        reconstructed_from_json = BIMModel.from_json(json_str)
        assert reconstructed_from_json.name == "Test Building"
        assert len(reconstructed_from_json.rooms) == 1


class TestBuildBIMModel:
    """Test the build_bim_model utility function."""
    
    def test_build_bim_model_from_svg_elements(self):
        """Test building BIM model from SVG elements."""
        svg_elements = [
            {
                'type': 'room',
                'name': 'Conference Room',
                'coordinates': [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
                'room_type': 'conference',
                'room_number': '101',
                'area': 100.0
            },
            {
                'type': 'device',
                'name': 'AHU-01',
                'coordinates': [5, 5],
                'system': 'hvac',
                'category': 'ahu',
                'manufacturer': 'Carrier',
                'model': '48TC'
            },
            {
                'type': 'wall',
                'name': 'Wall 1',
                'coordinates': [[0, 0], [10, 0]],
                'wall_type': 'interior',
                'thickness': 0.2,
                'height': 3.0
            }
        ]
        
        bim_model = build_bim_model(svg_elements)
        
        assert len(bim_model.rooms) == 1
        assert len(bim_model.devices) == 1
        assert len(bim_model.walls) == 1
        
        assert bim_model.rooms[0].name == "Conference Room"
        assert bim_model.rooms[0].room_type == RoomType.CONFERENCE
        assert bim_model.rooms[0].room_number == "101"
        assert bim_model.rooms[0].area == 100.0
        
        assert bim_model.devices[0].name == "AHU-01"
        assert bim_model.devices[0].system_type == SystemType.HVAC
        assert bim_model.devices[0].category == DeviceCategory.AHU
        assert bim_model.devices[0].manufacturer == "Carrier"
        
        assert bim_model.walls[0].name == "Wall 1"
        assert bim_model.walls[0].wall_type == "interior"
        assert bim_model.walls[0].thickness == 0.2
        assert bim_model.walls[0].height == 3.0


if __name__ == "__main__":
    pytest.main([__file__]) 