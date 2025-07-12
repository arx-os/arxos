"""
Tests for Persistence, Export, and Interoperability System

This module tests the comprehensive persistence, export, and interoperability features:
- Robust serialization for all BIM types
- Exporters for various BIM formats
- Database integration hooks
- Interoperability with external systems
"""

import unittest
import json
import tempfile
import os
import sqlite3
from typing import Dict, List, Any
from unittest.mock import Mock, patch
from pathlib import Path

from ..services.persistence_export_interoperability import (
    BIMSerializer, BIMExporter, PersistenceExportManager,
    ExportFormat, DatabaseType, ExportOptions, DatabaseConfig,
    SQLiteInterface, create_persistence_manager, export_bim_model,
    save_bim_model_to_database, load_bim_model_from_database
)
from ..models.bim import (
    BIMModel, Room, Wall, Door, Window, Device, Geometry, GeometryType,
    RoomType, SystemType, DeviceCategory
)
from ..utils.errors import ExportError, PersistenceError


class TestBIMSerializer(unittest.TestCase):
    """Test BIM serialization functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.serializer = BIMSerializer()
        
        # Create test BIM model
        self.test_model = BIMModel(name="Test Building")
        
        # Add test room
        room_geom = Geometry(type=GeometryType.POLYGON, coordinates=[[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]])
        self.test_room = Room(
            name="Test Room",
            geometry=room_geom,
            room_type=RoomType.OFFICE,
            room_number="101",
            area=100.0,
            floor_level=1.0,
            ceiling_height=3.0,
            occupants=5
        )
        self.test_model.add_element(self.test_room)
        
        # Add test wall
        wall_geom = Geometry(type=GeometryType.LINESTRING, coordinates=[[0, 0], [10, 0]])
        self.test_wall = Wall(
            name="Test Wall",
            geometry=wall_geom,
            wall_type="interior",
            thickness=0.2,
            height=3.0
        )
        self.test_model.add_element(self.test_wall)
        
        # Add test device
        device_geom = Geometry(type=GeometryType.POINT, coordinates=[5, 5])
        self.test_device = Device(
            name="Test Device",
            geometry=device_geom,
            system_type=SystemType.HVAC,
            category=DeviceCategory.AHU,
            manufacturer="Test Manufacturer",
            model="Test Model"
        )
        self.test_model.add_element(self.test_device)
    
    def test_to_dict(self):
        """Test converting BIM objects to dictionary."""
        # Test BIM model
        model_dict = self.serializer.to_dict(self.test_model)
        self.assertIsInstance(model_dict, dict)
        self.assertEqual(model_dict['name'], "Test Building")
        self.assertIn('rooms', model_dict)
        self.assertIn('walls', model_dict)
        self.assertIn('devices', model_dict)
        
        # Test room
        room_dict = self.serializer.to_dict(self.test_room)
        self.assertIsInstance(room_dict, dict)
        self.assertEqual(room_dict['name'], "Test Room")
        self.assertEqual(room_dict['room_type'], "office")
        self.assertEqual(room_dict['room_number'], "101")
        
        # Test wall
        wall_dict = self.serializer.to_dict(self.test_wall)
        self.assertIsInstance(wall_dict, dict)
        self.assertEqual(wall_dict['name'], "Test Wall")
        self.assertEqual(wall_dict['wall_type'], "interior")
        self.assertEqual(wall_dict['thickness'], 0.2)
        
        # Test device
        device_dict = self.serializer.to_dict(self.test_device)
        self.assertIsInstance(device_dict, dict)
        self.assertEqual(device_dict['name'], "Test Device")
        self.assertEqual(device_dict['system_type'], "hvac")
        self.assertEqual(device_dict['category'], "ahu")
    
    def test_from_dict(self):
        """Test creating BIM objects from dictionary."""
        # Test BIM model
        model_dict = self.serializer.to_dict(self.test_model)
        reconstructed_model = self.serializer.from_dict(model_dict, BIMModel)
        self.assertIsInstance(reconstructed_model, BIMModel)
        self.assertEqual(reconstructed_model.name, "Test Building")
        self.assertEqual(len(reconstructed_model.rooms), 1)
        self.assertEqual(len(reconstructed_model.walls), 1)
        self.assertEqual(len(reconstructed_model.devices), 1)
        
        # Test room
        room_dict = self.serializer.to_dict(self.test_room)
        reconstructed_room = self.serializer.from_dict(room_dict, Room)
        self.assertIsInstance(reconstructed_room, Room)
        self.assertEqual(reconstructed_room.name, "Test Room")
        self.assertEqual(reconstructed_room.room_type, RoomType.OFFICE)
    
    def test_to_json(self):
        """Test converting BIM objects to JSON."""
        # Test BIM model
        json_str = self.serializer.to_json(self.test_model)
        self.assertIsInstance(json_str, str)
        self.assertIn("Test Building", json_str)
        self.assertIn("rooms", json_str)
        self.assertIn("walls", json_str)
        self.assertIn("devices", json_str)
        
        # Test with pretty=False
        json_str_compact = self.serializer.to_json(self.test_model, pretty=False)
        self.assertIsInstance(json_str_compact, str)
        self.assertIn("Test Building", json_str_compact)
        
        # Test room
        room_json = self.serializer.to_json(self.test_room)
        self.assertIsInstance(room_json, str)
        self.assertIn("Test Room", room_json)
        self.assertIn("office", room_json)
    
    def test_from_json(self):
        """Test creating BIM objects from JSON."""
        # Test BIM model
        json_str = self.serializer.to_json(self.test_model)
        reconstructed_model = self.serializer.from_json(json_str, BIMModel)
        self.assertIsInstance(reconstructed_model, BIMModel)
        self.assertEqual(reconstructed_model.name, "Test Building")
        self.assertEqual(len(reconstructed_model.rooms), 1)
        
        # Test room
        room_json = self.serializer.to_json(self.test_room)
        reconstructed_room = self.serializer.from_json(room_json, Room)
        self.assertIsInstance(reconstructed_room, Room)
        self.assertEqual(reconstructed_room.name, "Test Room")
    
    def test_to_pickle(self):
        """Test converting BIM objects to pickle."""
        pickle_bytes = self.serializer.to_pickle(self.test_model)
        self.assertIsInstance(pickle_bytes, bytes)
        self.assertGreater(len(pickle_bytes), 0)
    
    def test_from_pickle(self):
        """Test creating BIM objects from pickle."""
        pickle_bytes = self.serializer.to_pickle(self.test_model)
        reconstructed_model = self.serializer.from_pickle(pickle_bytes)
        self.assertIsInstance(reconstructed_model, BIMModel)
        self.assertEqual(reconstructed_model.name, "Test Building")


class TestBIMExporter(unittest.TestCase):
    """Test BIM export functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.exporter = BIMExporter()
        
        # Create test BIM model
        self.test_model = BIMModel(name="Test Building")
        
        # Add test room
        room_geom = Geometry(type=GeometryType.POLYGON, coordinates=[[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]])
        test_room = Room(
            name="Test Room",
            geometry=room_geom,
            room_type=RoomType.OFFICE,
            room_number="101",
            area=100.0
        )
        self.test_model.add_element(test_room)
        
        # Add test wall
        wall_geom = Geometry(type=GeometryType.LINESTRING, coordinates=[[0, 0], [10, 0]])
        test_wall = Wall(
            name="Test Wall",
            geometry=wall_geom,
            wall_type="interior",
            thickness=0.2,
            height=3.0
        )
        self.test_model.add_element(test_wall)
        
        # Add test device
        device_geom = Geometry(type=GeometryType.POINT, coordinates=[5, 5])
        test_device = Device(
            name="Test Device",
            geometry=device_geom,
            system_type=SystemType.HVAC,
            category=DeviceCategory.AHU
        )
        self.test_model.add_element(test_device)
    
    def test_export_to_json(self):
        """Test exporting to JSON format."""
        options = ExportOptions(format=ExportFormat.JSON)
        json_str = self.exporter.export_bim_model(self.test_model, options)
        
        self.assertIsInstance(json_str, str)
        self.assertIn("Test Building", json_str)
        self.assertIn("rooms", json_str)
        self.assertIn("walls", json_str)
        self.assertIn("devices", json_str)
        
        # Parse JSON to verify structure
        data = json.loads(json_str)
        self.assertEqual(data['name'], "Test Building")
        self.assertEqual(len(data['rooms']), 1)
        self.assertEqual(len(data['walls']), 1)
        self.assertEqual(len(data['devices']), 1)
    
    def test_export_to_xml(self):
        """Test exporting to XML format."""
        options = ExportOptions(format=ExportFormat.XML)
        xml_str = self.exporter.export_bim_model(self.test_model, options)
        
        self.assertIsInstance(xml_str, str)
        self.assertIn("BIMModel", xml_str)
        self.assertIn("Test Building", xml_str)
        self.assertIn("rooms", xml_str)
        self.assertIn("walls", xml_str)
        self.assertIn("devices", xml_str)
    
    def test_export_to_csv(self):
        """Test exporting to CSV format."""
        options = ExportOptions(format=ExportFormat.CSV)
        csv_str = self.exporter.export_bim_model(self.test_model, options)
        
        self.assertIsInstance(csv_str, str)
        self.assertIn("type", csv_str)
        self.assertIn("id", csv_str)
        self.assertIn("name", csv_str)
        self.assertIn("room", csv_str)
        self.assertIn("wall", csv_str)
        self.assertIn("device", csv_str)
        
        # Verify CSV structure
        lines = csv_str.strip().split('\n')
        self.assertGreater(len(lines), 1)  # Header + data
        
        # Check header
        header = lines[0]
        self.assertIn("type", header)
        self.assertIn("id", header)
        self.assertIn("name", header)
    
    def test_export_to_ifc(self):
        """Test exporting to IFC format."""
        options = ExportOptions(format=ExportFormat.IFC)
        ifc_str = self.exporter.export_bim_model(self.test_model, options)
        
        self.assertIsInstance(ifc_str, str)
        self.assertIn("ISO-10303-21", ifc_str)
        self.assertIn("IFCPROJECT", ifc_str)
        self.assertIn("IFCBUILDINGSTOREY", ifc_str)
        self.assertIn("IFCWALL", ifc_str)
    
    def test_export_to_gbxml(self):
        """Test exporting to gbXML format."""
        options = ExportOptions(format=ExportFormat.GBXML)
        gbxml_str = self.exporter.export_bim_model(self.test_model, options)
        
        self.assertIsInstance(gbxml_str, str)
        self.assertIn("gbXML", gbxml_str)
        self.assertIn("Campus", gbxml_str)
        self.assertIn("Building", gbxml_str)
        self.assertIn("Space", gbxml_str)
    
    def test_export_to_pickle(self):
        """Test exporting to pickle format."""
        options = ExportOptions(format=ExportFormat.PICKLE)
        pickle_bytes = self.exporter.export_bim_model(self.test_model, options)
        
        self.assertIsInstance(pickle_bytes, bytes)
        self.assertGreater(len(pickle_bytes), 0)
    
    def test_export_with_options(self):
        """Test exporting with various options."""
        # Test without metadata
        options = ExportOptions(format=ExportFormat.JSON, include_metadata=False)
        json_str = self.exporter.export_bim_model(self.test_model, options)
        data = json.loads(json_str)
        self.assertNotIn('metadata', data)
        
        # Test without geometry
        options = ExportOptions(format=ExportFormat.JSON, include_geometry=False)
        json_str = self.exporter.export_bim_model(self.test_model, options)
        data = json.loads(json_str)
        # Check that geometry is removed from rooms
        if data['rooms']:
            self.assertNotIn('geometry', data['rooms'][0])
        
        # Test without properties
        options = ExportOptions(format=ExportFormat.JSON, include_properties=False)
        json_str = self.exporter.export_bim_model(self.test_model, options)
        data = json.loads(json_str)
        # Check that properties are removed
        if data['rooms']:
            self.assertNotIn('properties', data['rooms'][0])
    
    def test_unsupported_format(self):
        """Test handling of unsupported export format."""
        options = ExportOptions(format=ExportFormat.SQLITE)  # Not implemented in exporter
        with self.assertRaises(ExportError):
            self.exporter.export_bim_model(self.test_model, options)


class TestSQLiteInterface(unittest.TestCase):
    """Test SQLite database interface."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        self.db_config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            connection_string=self.temp_db.name,
            table_name="test_bim_models"
        )
        
        self.db_interface = SQLiteInterface(self.db_config)
        
        # Create test BIM model
        self.test_model = BIMModel(name="Test Building")
        room_geom = Geometry(type=GeometryType.POLYGON, coordinates=[[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]])
        test_room = Room(name="Test Room", geometry=room_geom, room_type=RoomType.OFFICE)
        self.test_model.add_element(test_room)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.db_interface.disconnect()
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_connect(self):
        """Test database connection."""
        self.db_interface.connect()
        self.assertIsNotNone(self.db_interface.connection)
        
        # Verify table was created
        cursor = self.db_interface.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
                      (self.db_config.table_name,))
        result = cursor.fetchone()
        self.assertIsNotNone(result)
    
    def test_save_and_load_bim_model(self):
        """Test saving and loading BIM model."""
        model_id = "test_model_1"
        
        # Save model
        self.db_interface.connect()
        self.db_interface.save_bim_model(self.test_model, model_id)
        
        # Load model
        loaded_model = self.db_interface.load_bim_model(model_id)
        
        # Verify loaded model
        self.assertIsInstance(loaded_model, BIMModel)
        self.assertEqual(loaded_model.name, "Test Building")
        self.assertEqual(len(loaded_model.rooms), 1)
        self.assertEqual(loaded_model.rooms[0].name, "Test Room")
    
    def test_list_models(self):
        """Test listing models in database."""
        self.db_interface.connect()
        
        # Save multiple models
        model_ids = ["model_1", "model_2", "model_3"]
        for model_id in model_ids:
            self.db_interface.save_bim_model(self.test_model, model_id)
        
        # List models
        listed_models = self.db_interface.list_models()
        
        # Verify all models are listed
        for model_id in model_ids:
            self.assertIn(model_id, listed_models)
    
    def test_delete_model(self):
        """Test deleting model from database."""
        model_id = "test_model_to_delete"
        
        self.db_interface.connect()
        
        # Save model
        self.db_interface.save_bim_model(self.test_model, model_id)
        
        # Verify model exists
        listed_models = self.db_interface.list_models()
        self.assertIn(model_id, listed_models)
        
        # Delete model
        self.db_interface.delete_model(model_id)
        
        # Verify model is deleted
        listed_models = self.db_interface.list_models()
        self.assertNotIn(model_id, listed_models)
    
    def test_load_nonexistent_model(self):
        """Test loading non-existent model."""
        self.db_interface.connect()
        
        with self.assertRaises(PersistenceError):
            self.db_interface.load_bim_model("nonexistent_model")


class TestPersistenceExportManager(unittest.TestCase):
    """Test persistence export manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = PersistenceExportManager()
        
        # Create test BIM model
        self.test_model = BIMModel(name="Test Building")
        room_geom = Geometry(type=GeometryType.POLYGON, coordinates=[[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]])
        test_room = Room(name="Test Room", geometry=room_geom, room_type=RoomType.OFFICE)
        self.test_model.add_element(test_room)
    
    def test_export_bim_model(self):
        """Test exporting BIM model to file."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            options = ExportOptions(format=ExportFormat.JSON)
            self.manager.export_bim_model(self.test_model, temp_path, options)
            
            # Verify file was created
            self.assertTrue(os.path.exists(temp_path))
            
            # Verify file content
            with open(temp_path, 'r') as f:
                content = f.read()
                self.assertIn("Test Building", content)
                self.assertIn("rooms", content)
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_save_and_load_from_database(self):
        """Test saving and loading from database."""
        db_config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            connection_string=":memory:",
            table_name="test_bim_models"
        )
        
        model_id = "test_model_1"
        
        # Save model
        self.manager.save_bim_model_to_database(self.test_model, model_id, db_config)
        
        # Load model
        loaded_model = self.manager.load_bim_model_from_database(model_id, db_config)
        
        # Verify loaded model
        self.assertIsInstance(loaded_model, BIMModel)
        self.assertEqual(loaded_model.name, "Test Building")
        self.assertEqual(len(loaded_model.rooms), 1)
    
    def test_list_database_models(self):
        """Test listing database models."""
        db_config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            connection_string=":memory:",
            table_name="test_bim_models"
        )
        
        # Save multiple models
        model_ids = ["model_1", "model_2", "model_3"]
        for model_id in model_ids:
            self.manager.save_bim_model_to_database(self.test_model, model_id, db_config)
        
        # List models
        listed_models = self.manager.list_database_models(db_config)
        
        # Verify all models are listed
        for model_id in model_ids:
            self.assertIn(model_id, listed_models)
    
    def test_delete_database_model(self):
        """Test deleting database model."""
        db_config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            connection_string=":memory:",
            table_name="test_bim_models"
        )
        
        model_id = "test_model_to_delete"
        
        # Save model
        self.manager.save_bim_model_to_database(self.test_model, model_id, db_config)
        
        # Verify model exists
        listed_models = self.manager.list_database_models(db_config)
        self.assertIn(model_id, listed_models)
        
        # Delete model
        self.manager.delete_database_model(model_id, db_config)
        
        # Verify model is deleted
        listed_models = self.manager.list_database_models(db_config)
        self.assertNotIn(model_id, listed_models)
    
    def test_close_database_connections(self):
        """Test closing database connections."""
        db_config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            connection_string=":memory:",
            table_name="test_bim_models"
        )
        
        # Create connection
        self.manager.save_bim_model_to_database(self.test_model, "test_model", db_config)
        
        # Close connections
        self.manager.close_database_connections()
        
        # Verify connections are closed
        self.assertEqual(len(self.manager.database_interfaces), 0)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_model = BIMModel(name="Test Building")
        room_geom = Geometry(type=GeometryType.POLYGON, coordinates=[[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]])
        test_room = Room(name="Test Room", geometry=room_geom, room_type=RoomType.OFFICE)
        self.test_model.add_element(test_room)
    
    def test_create_persistence_manager(self):
        """Test creating persistence manager."""
        manager = create_persistence_manager()
        self.assertIsInstance(manager, PersistenceExportManager)
    
    def test_export_bim_model_function(self):
        """Test export_bim_model convenience function."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            export_bim_model(self.test_model, temp_path, ExportFormat.JSON)
            
            # Verify file was created
            self.assertTrue(os.path.exists(temp_path))
            
            # Verify file content
            with open(temp_path, 'r') as f:
                content = f.read()
                self.assertIn("Test Building", content)
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_save_bim_model_to_database_function(self):
        """Test save_bim_model_to_database convenience function."""
        model_id = "test_model_1"
        
        save_bim_model_to_database(
            self.test_model, 
            model_id, 
            DatabaseType.SQLITE, 
            ":memory:"
        )
        
        # Verify model can be loaded
        loaded_model = load_bim_model_from_database(
            model_id, 
            DatabaseType.SQLITE, 
            ":memory:"
        )
        
        self.assertIsInstance(loaded_model, BIMModel)
        self.assertEqual(loaded_model.name, "Test Building")
    
    def test_load_bim_model_from_database_function(self):
        """Test load_bim_model_from_database convenience function."""
        model_id = "test_model_2"
        
        # Save model first
        save_bim_model_to_database(
            self.test_model, 
            model_id, 
            DatabaseType.SQLITE, 
            ":memory:"
        )
        
        # Load model
        loaded_model = load_bim_model_from_database(
            model_id, 
            DatabaseType.SQLITE, 
            ":memory:"
        )
        
        self.assertIsInstance(loaded_model, BIMModel)
        self.assertEqual(loaded_model.name, "Test Building")
        self.assertEqual(len(loaded_model.rooms), 1)


class TestPersistenceExportIntegration(unittest.TestCase):
    """Integration tests for persistence and export."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_model = BIMModel(name="Integration Test Building")
        
        # Add various elements
        room_geom = Geometry(type=GeometryType.POLYGON, coordinates=[[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]])
        room = Room(name="Office 101", geometry=room_geom, room_type=RoomType.OFFICE, area=100.0)
        self.test_model.add_element(room)
        
        wall_geom = Geometry(type=GeometryType.LINESTRING, coordinates=[[0, 0], [10, 0]])
        wall = Wall(name="Interior Wall", geometry=wall_geom, wall_type="interior", thickness=0.2)
        self.test_model.add_element(wall)
        
        device_geom = Geometry(type=GeometryType.POINT, coordinates=[5, 5])
        device = Device(name="AHU-01", geometry=device_geom, system_type=SystemType.HVAC, category=DeviceCategory.AHU)
        self.test_model.add_element(device)
    
    def test_complete_export_workflow(self):
        """Test complete export workflow with multiple formats."""
        manager = create_persistence_manager()
        
        # Test JSON export
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as json_file:
            json_path = json_file.name
        
        try:
            options = ExportOptions(format=ExportFormat.JSON)
            manager.export_bim_model(self.test_model, json_path, options)
            
            # Verify JSON export
            with open(json_path, 'r') as f:
                content = f.read()
                data = json.loads(content)
                self.assertEqual(data['name'], "Integration Test Building")
                self.assertEqual(len(data['rooms']), 1)
                self.assertEqual(len(data['walls']), 1)
                self.assertEqual(len(data['devices']), 1)
        
        finally:
            if os.path.exists(json_path):
                os.unlink(json_path)
    
    def test_complete_database_workflow(self):
        """Test complete database workflow."""
        manager = create_persistence_manager()
        db_config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            connection_string=":memory:",
            table_name="integration_test"
        )
        
        model_id = "integration_test_model"
        
        # Save model
        manager.save_bim_model_to_database(self.test_model, model_id, db_config)
        
        # List models
        models = manager.list_database_models(db_config)
        self.assertIn(model_id, models)
        
        # Load model
        loaded_model = manager.load_bim_model_from_database(model_id, db_config)
        self.assertEqual(loaded_model.name, "Integration Test Building")
        self.assertEqual(len(loaded_model.rooms), 1)
        self.assertEqual(len(loaded_model.walls), 1)
        self.assertEqual(len(loaded_model.devices), 1)
        
        # Delete model
        manager.delete_database_model(model_id, db_config)
        
        # Verify deletion
        models = manager.list_database_models(db_config)
        self.assertNotIn(model_id, models)
    
    def test_round_trip_serialization(self):
        """Test round-trip serialization and deserialization."""
        # Export to JSON
        json_str = BIMSerializer.to_json(self.test_model)
        
        # Import from JSON
        reconstructed_model = BIMSerializer.from_json(json_str, BIMModel)
        
        # Verify reconstruction
        self.assertEqual(reconstructed_model.name, "Integration Test Building")
        self.assertEqual(len(reconstructed_model.rooms), 1)
        self.assertEqual(len(reconstructed_model.walls), 1)
        self.assertEqual(len(reconstructed_model.devices), 1)
        
        # Verify room details
        original_room = self.test_model.rooms[0]
        reconstructed_room = reconstructed_model.rooms[0]
        self.assertEqual(original_room.name, reconstructed_room.name)
        self.assertEqual(original_room.room_type, reconstructed_room.room_type)
        self.assertEqual(original_room.area, reconstructed_room.area)


if __name__ == "__main__":
    unittest.main() 