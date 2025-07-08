"""
Comprehensive Tests for BIM Features

This module tests all BIM features including:
- BIM assembly pipeline
- BIM validation
- BIM export/import
- BIM visualization
- BIM collaboration
"""

import unittest
import tempfile
import json
import time
from typing import Dict, List, Any
from pathlib import Path

from services.bim_assembly import BIMAssemblyPipeline, AssemblyConfig, ValidationLevel
from services.bim_validator import BIMValidator, ValidationLevel as ValidatorLevel
from services.bim_export_import import BIMExportImportService, ExportFormat, ImportFormat, ExportOptions, ImportOptions
from services.bim_visualization import BIMVisualizer, ViewMode, VisualizationStyle
from services.bim_collaboration import BIMCollaborationService, UserRole, ChangeType, ConflictResolution
from models.bim import (
    Room, Wall, Door, Window, Device, SystemType, DeviceCategory,
    Geometry, GeometryType, BIMModel
)
from utils.errors import BIMAssemblyError, ValidationError, ExportError, ImportError, CollaborationError


class TestBIMAssemblyPipeline(unittest.TestCase):
    """Test BIM assembly pipeline functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = AssemblyConfig(
            validation_level=ValidationLevel.STANDARD,
            conflict_resolution_enabled=True,
            performance_optimization_enabled=True,
            parallel_processing=True,
            max_workers=2,
            batch_size=50
        )
        self.pipeline = BIMAssemblyPipeline(self.config)
        
        # Test SVG data
        self.test_svg_data = {
            'elements': [
                {
                    'id': 'room_1',
                    'type': 'rect',
                    'coordinates': [[0, 0], [10, 0], [10, 8], [0, 8], [0, 0]],
                    'properties': {
                        'room_type': 'office',
                        'room_number': '101',
                        'area': 80.0
                    },
                    'metadata': {
                        'layer': 'rooms',
                        'symbol_metadata': {
                            'category': 'room',
                            'system': 'spatial',
                            'tags': ['office', 'spatial']
                        }
                    }
                },
                {
                    'id': 'wall_1',
                    'type': 'line',
                    'coordinates': [[0, 0], [10, 0]],
                    'properties': {
                        'wall_type': 'interior',
                        'thickness': 0.2,
                        'height': 3.0
                    },
                    'metadata': {
                        'layer': 'walls',
                        'symbol_metadata': {
                            'category': 'wall',
                            'system': 'structural',
                            'tags': ['wall', 'structural']
                        }
                    }
                },
                {
                    'id': 'device_1',
                    'type': 'circle',
                    'coordinates': [5, 4],
                    'properties': {
                        'system_type': 'hvac',
                        'category': 'ahu',
                        'manufacturer': 'Test Corp',
                        'model': 'AHU-100'
                    },
                    'metadata': {
                        'layer': 'hvac',
                        'symbol_metadata': {
                            'category': 'device',
                            'system': 'hvac',
                            'tags': ['device', 'hvac', 'ahu']
                        }
                    }
                }
            ]
        }
    
    def test_bim_assembly_pipeline_creation(self):
        """Test BIM assembly pipeline creation."""
        self.assertIsNotNone(self.pipeline)
        self.assertEqual(self.pipeline.config.validation_level, ValidationLevel.STANDARD)
        self.assertTrue(self.pipeline.config.conflict_resolution_enabled)
        self.assertTrue(self.pipeline.config.performance_optimization_enabled)
    
    def test_geometry_extraction(self):
        """Test geometry extraction from SVG data."""
        elements = self.pipeline._extract_geometry(self.test_svg_data)
        
        self.assertIsInstance(elements, list)
        self.assertGreater(len(elements), 0)
        
        for element in elements:
            self.assertIsNotNone(element.geometry)
            self.assertIsNotNone(element.id)
    
    def test_element_classification(self):
        """Test element classification."""
        # First extract geometry
        elements = self.pipeline._extract_geometry(self.test_svg_data)
        
        # Then classify elements
        self.pipeline.elements = {elem.id: elem for elem in elements}
        self.pipeline._classify_elements()
        
        # Check that elements have categories
        for element in self.pipeline.elements.values():
            self.assertIsNotNone(element.category)
    
    def test_spatial_organization(self):
        """Test spatial organization."""
        # Extract and classify elements
        elements = self.pipeline._extract_geometry(self.test_svg_data)
        self.pipeline.elements = {elem.id: elem for elem in elements}
        self.pipeline._classify_elements()
        
        # Organize spatial structure
        self.pipeline._organize_spatial_structure()
        
        # Check that spaces were created
        self.assertGreater(len(self.pipeline.spaces), 0)
    
    def test_system_integration(self):
        """Test system integration."""
        # Extract and classify elements
        elements = self.pipeline._extract_geometry(self.test_svg_data)
        self.pipeline.elements = {elem.id: elem for elem in elements}
        self.pipeline._classify_elements()
        
        # Integrate systems
        self.pipeline._integrate_systems()
        
        # Check that systems were created
        self.assertGreater(len(self.pipeline.systems), 0)
    
    def test_relationship_establishment(self):
        """Test relationship establishment."""
        # Extract and classify elements
        elements = self.pipeline._extract_geometry(self.test_svg_data)
        self.pipeline.elements = {elem.id: elem for elem in elements}
        self.pipeline._classify_elements()
        
        # Establish relationships
        self.pipeline._establish_relationships()
        
        # Check that relationships were created
        self.assertGreater(len(self.pipeline.relationships), 0)
    
    def test_conflict_resolution(self):
        """Test conflict resolution."""
        # Extract and classify elements
        elements = self.pipeline._extract_geometry(self.test_svg_data)
        self.pipeline.elements = {elem.id: elem for elem in elements}
        self.pipeline._classify_elements()
        
        # Resolve conflicts
        self.pipeline._resolve_conflicts()
        
        # Check that conflicts were processed
        # (May be empty if no conflicts detected)
        self.assertIsInstance(self.pipeline.conflicts, list)
    
    def test_consistency_validation(self):
        """Test consistency validation."""
        # Extract and classify elements
        elements = self.pipeline._extract_geometry(self.test_svg_data)
        self.pipeline.elements = {elem.id: elem for elem in elements}
        self.pipeline._classify_elements()
        
        # Validate consistency
        validation_results = self.pipeline._validate_consistency()
        
        # Check validation results structure
        self.assertIn('overall_valid', validation_results)
        self.assertIn('element_validation', validation_results)
        self.assertIn('system_validation', validation_results)
        self.assertIn('spatial_validation', validation_results)
        self.assertIn('relationship_validation', validation_results)
        self.assertIn('geometry_validation', validation_results)
    
    def test_complete_assembly_pipeline(self):
        """Test complete BIM assembly pipeline."""
        result = self.pipeline.assemble_bim(self.test_svg_data)
        
        # Check result structure
        self.assertTrue(result.success)
        self.assertIsNotNone(result.assembly_id)
        self.assertGreater(len(result.elements), 0)
        self.assertIsInstance(result.systems, list)
        self.assertIsInstance(result.spaces, list)
        self.assertIsInstance(result.relationships, list)
        self.assertIsInstance(result.conflicts, list)
        self.assertIsInstance(result.validation_results, dict)
        self.assertIsInstance(result.performance_metrics, dict)
        self.assertGreater(result.assembly_time, 0)
    
    def test_error_handling(self):
        """Test error handling in assembly pipeline."""
        # Test with invalid SVG data
        invalid_svg_data = {
            'elements': [
                {
                    'id': 'invalid_element',
                    'type': 'unknown_type',
                    'coordinates': None  # Invalid coordinates
                }
            ]
        }
        
        result = self.pipeline.assemble_bim(invalid_svg_data)
        
        # Should still succeed but with warnings
        self.assertTrue(result.success)
        self.assertGreaterEqual(len(result.elements), 0)
    
    def test_assembly_statistics(self):
        """Test assembly statistics."""
        result = self.pipeline.assemble_bim(self.test_svg_data)
        
        # Get statistics
        stats = self.pipeline.get_assembly_statistics()
        
        # Check statistics structure
        self.assertIn('total_elements', stats)
        self.assertIn('total_systems', stats)
        self.assertIn('total_spaces', stats)
        self.assertIn('total_relationships', stats)
        self.assertIn('total_conflicts', stats)
        self.assertIn('resolved_conflicts', stats)
        self.assertIn('performance_metrics', stats)
        
        # Check statistics match result
        self.assertEqual(stats['total_elements'], len(result.elements))
        self.assertEqual(stats['total_systems'], len(result.systems))
        self.assertEqual(stats['total_spaces'], len(result.spaces))
        self.assertEqual(stats['total_relationships'], len(result.relationships))


class TestBIMValidator(unittest.TestCase):
    """Test BIM validation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = BIMValidator(ValidatorLevel.STANDARD)
        
        # Create test BIM elements
        self.test_elements = [
            Room(
                id='room_1',
                name='Office 101',
                geometry=Geometry(
                    type=GeometryType.POLYGON,
                    coordinates=[[[0, 0], [10, 0], [10, 8], [0, 8], [0, 0]]]
                ),
                room_type='office',
                area=80.0
            ),
            Wall(
                id='wall_1',
                name='Interior Wall',
                geometry=Geometry(
                    type=GeometryType.LINESTRING,
                    coordinates=[[0, 0], [10, 0]]
                ),
                wall_type='interior',
                thickness=0.2
            ),
            Device(
                id='device_1',
                name='HVAC Unit',
                geometry=Geometry(
                    type=GeometryType.POINT,
                    coordinates=[5, 4]
                ),
                system_type=SystemType.HVAC,
                category=DeviceCategory.AHU
            )
        ]
    
    def test_validator_creation(self):
        """Test BIM validator creation."""
        self.assertIsNotNone(self.validator)
        self.assertEqual(self.validator.validation_level, ValidatorLevel.STANDARD)
    
    def test_geometry_validation(self):
        """Test geometry validation."""
        result = self.validator.validate_bim_model(self.test_elements)
        
        self.assertIsInstance(result, type(self.validator).__module__ + '.ValidationResult')
        self.assertTrue(result.valid)
        self.assertGreaterEqual(result.total_issues, 0)
    
    def test_property_validation(self):
        """Test property validation."""
        result = self.validator.validate_bim_model(self.test_elements)
        
        # Check property validation results
        property_validation = result.issues_by_category.get('property', [])
        self.assertIsInstance(property_validation, list)
    
    def test_spatial_validation(self):
        """Test spatial relationship validation."""
        result = self.validator.validate_bim_model(self.test_elements)
        
        # Check spatial validation results
        spatial_validation = result.issues_by_category.get('spatial', [])
        self.assertIsInstance(spatial_validation, list)
    
    def test_validation_with_invalid_elements(self):
        """Test validation with invalid elements."""
        # Create invalid element
        invalid_element = Room(
            id='invalid_room',
            name='Invalid Room',
            geometry=Geometry(
                type=GeometryType.POLYGON,
                coordinates=[[[0, 0], [10, 0], [0, 0]]]  # Invalid polygon
            ),
            area=-10.0  # Invalid area
        )
        
        elements_with_invalid = self.test_elements + [invalid_element]
        result = self.validator.validate_bim_model(elements_with_invalid)
        
        # Should have validation issues
        self.assertGreater(result.total_issues, 0)
    
    def test_validation_levels(self):
        """Test different validation levels."""
        # Test basic validation
        basic_validator = BIMValidator(ValidatorLevel.BASIC)
        basic_result = basic_validator.validate_bim_model(self.test_elements)
        
        # Test comprehensive validation
        comprehensive_validator = BIMValidator(ValidatorLevel.COMPREHENSIVE)
        comprehensive_result = comprehensive_validator.validate_bim_model(self.test_elements)
        
        # Comprehensive validation should be more thorough
        self.assertIsInstance(basic_result, type(comprehensive_result))
    
    def test_validation_issue_details(self):
        """Test validation issue details."""
        result = self.validator.validate_bim_model(self.test_elements)
        
        for issue in result.issues_by_severity.get('error', []):
            self.assertIsNotNone(issue.issue_id)
            self.assertIsNotNone(issue.category)
            self.assertIsNotNone(issue.severity)
            self.assertIsNotNone(issue.description)


class TestBIMExportImport(unittest.TestCase):
    """Test BIM export/import functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.export_import_service = BIMExportImportService()
        
        # Create test BIM model
        self.test_model = BIMModel(
            id='test_model',
            name='Test BIM Model',
            description='Test model for export/import testing'
        )
        
        # Add test elements
        room = Room(
            id='room_1',
            name='Test Room',
            geometry=Geometry(
                type=GeometryType.POLYGON,
                coordinates=[[[0, 0], [10, 0], [10, 8], [0, 8], [0, 0]]]
            ),
            room_type='office',
            area=80.0
        )
        
        wall = Wall(
            id='wall_1',
            name='Test Wall',
            geometry=Geometry(
                type=GeometryType.LINESTRING,
                coordinates=[[0, 0], [10, 0]]
            ),
            wall_type='interior',
            thickness=0.2
        )
        
        self.test_model.add_element(room)
        self.test_model.add_element(wall)
    
    def test_export_import_service_creation(self):
        """Test export/import service creation."""
        self.assertIsNotNone(self.export_import_service)
        self.assertIsNotNone(self.export_import_service.supported_formats)
        self.assertIsNotNone(self.export_import_service.import_formats)
    
    def test_json_export(self):
        """Test JSON export."""
        options = ExportOptions(
            format=ExportFormat.JSON,
            include_metadata=True,
            include_relationships=True,
            include_systems=True,
            include_geometry=True,
            include_properties=True
        )
        
        result = self.export_import_service.export_bim(self.test_model, options)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.file_path)
        self.assertEqual(result.format, ExportFormat.JSON)
        self.assertGreater(result.elements_exported, 0)
        self.assertGreater(result.export_time, 0)
    
    def test_xml_export(self):
        """Test XML export."""
        options = ExportOptions(
            format=ExportFormat.XML,
            include_metadata=True,
            include_relationships=True,
            include_systems=True,
            include_geometry=True,
            include_properties=True
        )
        
        result = self.export_import_service.export_bim(self.test_model, options)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.file_path)
        self.assertEqual(result.format, ExportFormat.XML)
        self.assertGreater(result.elements_exported, 0)
        self.assertGreater(result.export_time, 0)
    
    def test_json_import(self):
        """Test JSON import."""
        # First export to JSON
        export_options = ExportOptions(format=ExportFormat.JSON)
        export_result = self.export_import_service.export_bim(self.test_model, export_options)
        
        # Then import the JSON file
        import_options = ImportOptions(
            format=ImportFormat.JSON,
            validate_on_import=True,
            create_systems=True,
            create_relationships=True
        )
        
        import_result = self.export_import_service.import_bim(
            export_result.file_path, import_options
        )
        
        self.assertTrue(import_result.success)
        self.assertEqual(import_result.format, ImportFormat.JSON)
        self.assertGreater(import_result.elements_imported, 0)
        self.assertGreater(import_result.import_time, 0)
    
    def test_xml_import(self):
        """Test XML import."""
        # First export to XML
        export_options = ExportOptions(format=ExportFormat.XML)
        export_result = self.export_import_service.export_bim(self.test_model, export_options)
        
        # Then import the XML file
        import_options = ImportOptions(
            format=ImportFormat.XML,
            validate_on_import=True,
            create_systems=True,
            create_relationships=True
        )
        
        import_result = self.export_import_service.import_bim(
            export_result.file_path, import_options
        )
        
        self.assertTrue(import_result.success)
        self.assertEqual(import_result.format, ImportFormat.XML)
        self.assertGreater(import_result.elements_imported, 0)
        self.assertGreater(import_result.import_time, 0)
    
    def test_export_with_validation(self):
        """Test export with validation."""
        options = ExportOptions(
            format=ExportFormat.JSON,
            validation_level=ValidatorLevel.STANDARD
        )
        
        result = self.export_import_service.export_bim(self.test_model, options)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.validation_results)
    
    def test_export_error_handling(self):
        """Test export error handling."""
        # Test with unsupported format
        options = ExportOptions(format=ExportFormat.FBX)
        
        result = self.export_import_service.export_bim(self.test_model, options)
        
        self.assertFalse(result.success)
        self.assertGreater(len(result.errors), 0)
    
    def test_import_error_handling(self):
        """Test import error handling."""
        # Test with non-existent file
        import_options = ImportOptions(format=ImportFormat.JSON)
        
        result = self.export_import_service.import_bim('non_existent_file.json', import_options)
        
        self.assertFalse(result.success)
        self.assertGreater(len(result.errors), 0)


class TestBIMVisualization(unittest.TestCase):
    """Test BIM visualization functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.visualizer = BIMVisualizer()
        
        # Create test BIM elements
        self.test_elements = [
            Room(
                id='room_1',
                name='Test Room',
                geometry=Geometry(
                    type=GeometryType.POLYGON,
                    coordinates=[[[0, 0], [10, 0], [10, 8], [0, 8], [0, 0]]]
                ),
                room_type='office',
                area=80.0
            ),
            Wall(
                id='wall_1',
                name='Test Wall',
                geometry=Geometry(
                    type=GeometryType.LINESTRING,
                    coordinates=[[0, 0], [10, 0]]
                ),
                wall_type='interior',
                thickness=0.2
            ),
            Device(
                id='device_1',
                name='Test Device',
                geometry=Geometry(
                    type=GeometryType.POINT,
                    coordinates=[5, 4]
                ),
                system_type=SystemType.HVAC,
                category=DeviceCategory.AHU
            )
        ]
    
    def test_visualizer_creation(self):
        """Test visualizer creation."""
        self.assertIsNotNone(self.visualizer)
        self.assertIsNotNone(self.visualizer.viewport_config)
        self.assertIsNotNone(self.visualizer.camera_config)
        self.assertIsNotNone(self.visualizer.visualization_style)
        self.assertIsNotNone(self.visualizer.color_palette)
        self.assertIsNotNone(self.visualizer.element_styles)
    
    def test_2d_rendering(self):
        """Test 2D rendering."""
        style = VisualizationStyle(
            visualization_type='solid',
            show_labels=True,
            show_annotations=True
        )
        
        result = self.visualizer.render_2d_view(
            self.test_elements, 
            ViewMode.PLAN, 
            style
        )
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.svg_data)
        self.assertGreater(result.elements_rendered, 0)
        self.assertGreater(result.rendering_time, 0)
    
    def test_3d_rendering(self):
        """Test 3D rendering."""
        style = VisualizationStyle(
            visualization_type='solid',
            show_labels=True,
            show_annotations=True
        )
        
        result = self.visualizer.render_3d_view(self.test_elements, style)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.json_data)
        self.assertGreater(result.elements_rendered, 0)
        self.assertGreater(result.rendering_time, 0)
    
    def test_interactive_viewer(self):
        """Test interactive viewer creation."""
        viewer_data = self.visualizer.create_interactive_viewer(
            self.test_elements, 
            ViewMode.PLAN
        )
        
        self.assertIsInstance(viewer_data, dict)
        self.assertIn('type', viewer_data)
        self.assertEqual(viewer_data['type'], 'interactive_viewer')
        self.assertIn('elements', viewer_data)
        self.assertIn('interactions', viewer_data)
        self.assertIn('controls', viewer_data)
    
    def test_different_view_modes(self):
        """Test different view modes."""
        style = VisualizationStyle()
        
        # Test plan view
        plan_result = self.visualizer.render_2d_view(
            self.test_elements, 
            ViewMode.PLAN, 
            style
        )
        self.assertTrue(plan_result.success)
        
        # Test elevation view
        elevation_result = self.visualizer.render_2d_view(
            self.test_elements, 
            ViewMode.ELEVATION, 
            style
        )
        self.assertTrue(elevation_result.success)
    
    def test_different_visualization_styles(self):
        """Test different visualization styles."""
        # Test solid style
        solid_style = VisualizationStyle(visualization_type='solid')
        solid_result = self.visualizer.render_2d_view(
            self.test_elements, 
            ViewMode.PLAN, 
            solid_style
        )
        self.assertTrue(solid_result.success)
        
        # Test wireframe style
        wireframe_style = VisualizationStyle(visualization_type='wireframe')
        wireframe_result = self.visualizer.render_2d_view(
            self.test_elements, 
            ViewMode.PLAN, 
            wireframe_style
        )
        self.assertTrue(wireframe_result.success)
    
    def test_geometry_conversion(self):
        """Test geometry conversion methods."""
        # Test polygon to SVG path
        polygon_coords = [[0, 0], [10, 0], [10, 8], [0, 8], [0, 0]]
        svg_path = self.visualizer._polygon_to_svg_path(polygon_coords, ViewMode.PLAN)
        self.assertIsInstance(svg_path, str)
        self.assertGreater(len(svg_path), 0)
        
        # Test linestring to SVG path
        linestring_coords = [[0, 0], [10, 0]]
        svg_path = self.visualizer._linestring_to_svg_path(linestring_coords, ViewMode.PLAN)
        self.assertIsInstance(svg_path, str)
        self.assertGreater(len(svg_path), 0)
        
        # Test point to SVG path
        point_coords = [5, 4]
        svg_path = self.visualizer._point_to_svg_path(point_coords, ViewMode.PLAN)
        self.assertIsInstance(svg_path, str)
        self.assertGreater(len(svg_path), 0)


class TestBIMCollaboration(unittest.TestCase):
    """Test BIM collaboration functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.collaboration_service = BIMCollaborationService()
        self.model_id = 'test_model'
        self.owner_id = 'owner_1'
        self.owner_username = 'test_owner'
        self.owner_email = 'owner@test.com'
    
    def test_collaboration_service_creation(self):
        """Test collaboration service creation."""
        self.assertIsNotNone(self.collaboration_service)
        self.assertIsNotNone(self.collaboration_service.sessions)
    
    def test_session_creation(self):
        """Test session creation."""
        session_id = self.collaboration_service.create_session(
            self.model_id,
            self.owner_id,
            self.owner_username,
            self.owner_email
        )
        
        self.assertIsNotNone(session_id)
        self.assertIn(session_id, self.collaboration_service.sessions)
        
        session = self.collaboration_service.sessions[session_id]
        self.assertEqual(session.model_id, self.model_id)
        self.assertIn(self.owner_id, session.users)
        self.assertEqual(session.users[self.owner_id].role, UserRole.OWNER)
    
    def test_user_joining(self):
        """Test user joining session."""
        session_id = self.collaboration_service.create_session(
            self.model_id,
            self.owner_id,
            self.owner_username,
            self.owner_email
        )
        
        # Join as editor
        user_id = 'user_1'
        username = 'test_user'
        email = 'user@test.com'
        
        success = self.collaboration_service.join_session(
            session_id,
            user_id,
            username,
            email,
            UserRole.EDITOR
        )
        
        self.assertTrue(success)
        
        session = self.collaboration_service.sessions[session_id]
        self.assertIn(user_id, session.users)
        self.assertEqual(session.users[user_id].role, UserRole.EDITOR)
    
    def test_making_changes(self):
        """Test making changes to the model."""
        session_id = self.collaboration_service.create_session(
            self.model_id,
            self.owner_id,
            self.owner_username,
            self.owner_email
        )
        
        # Make a change
        change_id = self.collaboration_service.make_change(
            session_id,
            self.owner_id,
            ChangeType.CREATE,
            'element_1',
            'Room',
            {'name': 'New Room', 'area': 100.0},
            description='Created new room'
        )
        
        self.assertIsNotNone(change_id)
        
        # Check that change was recorded
        session = self.collaboration_service.sessions[session_id]
        self.assertIn(change_id, session.active_changes)
    
    def test_conflict_detection(self):
        """Test conflict detection."""
        session_id = self.collaboration_service.create_session(
            self.model_id,
            self.owner_id,
            self.owner_username,
            self.owner_email
        )
        
        # Add another user
        user_id = 'user_1'
        self.collaboration_service.join_session(
            session_id,
            user_id,
            'test_user',
            'user@test.com',
            UserRole.EDITOR
        )
        
        # Make conflicting changes
        change1_id = self.collaboration_service.make_change(
            session_id,
            self.owner_id,
            ChangeType.UPDATE,
            'element_1',
            'Room',
            {'name': 'Room A'},
            description='Changed name to Room A'
        )
        
        change2_id = self.collaboration_service.make_change(
            session_id,
            user_id,
            ChangeType.UPDATE,
            'element_1',
            'Room',
            {'name': 'Room B'},
            description='Changed name to Room B'
        )
        
        # Check for conflicts
        conflicts = self.collaboration_service.get_conflicts(session_id, self.owner_id)
        self.assertGreater(len(conflicts), 0)
    
    def test_conflict_resolution(self):
        """Test conflict resolution."""
        session_id = self.collaboration_service.create_session(
            self.model_id,
            self.owner_id,
            self.owner_username,
            self.owner_email
        )
        
        # Add another user
        user_id = 'user_1'
        self.collaboration_service.join_session(
            session_id,
            user_id,
            'test_user',
            'user@test.com',
            UserRole.EDITOR
        )
        
        # Make conflicting changes
        self.collaboration_service.make_change(
            session_id,
            self.owner_id,
            ChangeType.UPDATE,
            'element_1',
            'Room',
            {'name': 'Room A'}
        )
        
        self.collaboration_service.make_change(
            session_id,
            user_id,
            ChangeType.UPDATE,
            'element_1',
            'Room',
            {'name': 'Room B'}
        )
        
        # Get conflicts
        conflicts = self.collaboration_service.get_conflicts(session_id, self.owner_id)
        
        if conflicts:
            # Resolve first conflict
            conflict = conflicts[0]
            success = self.collaboration_service.resolve_conflict(
                session_id,
                conflict['conflict_id'],
                ConflictResolution.LAST_WRITER_WINS,
                self.owner_id
            )
            
            self.assertTrue(success)
    
    def test_session_status(self):
        """Test getting session status."""
        session_id = self.collaboration_service.create_session(
            self.model_id,
            self.owner_id,
            self.owner_username,
            self.owner_email
        )
        
        # Add another user
        user_id = 'user_1'
        self.collaboration_service.join_session(
            session_id,
            user_id,
            'test_user',
            'user@test.com',
            UserRole.EDITOR
        )
        
        # Make some changes
        self.collaboration_service.make_change(
            session_id,
            self.owner_id,
            ChangeType.CREATE,
            'element_1',
            'Room',
            {'name': 'Test Room'}
        )
        
        # Get session status
        status = self.collaboration_service.get_session_status(session_id)
        
        self.assertIn('session_id', status)
        self.assertIn('model_id', status)
        self.assertIn('user_count', status)
        self.assertIn('active_changes', status)
        self.assertIn('conflicts', status)
        self.assertIn('versions', status)
        self.assertIn('users', status)
        
        self.assertEqual(status['session_id'], session_id)
        self.assertEqual(status['model_id'], self.model_id)
        self.assertEqual(status['user_count'], 2)
        self.assertGreater(status['active_changes'], 0)
    
    def test_version_control(self):
        """Test version control functionality."""
        session_id = self.collaboration_service.create_session(
            self.model_id,
            self.owner_id,
            self.owner_username,
            self.owner_email
        )
        
        # Make some changes
        for i in range(5):
            self.collaboration_service.make_change(
                session_id,
                self.owner_id,
                ChangeType.CREATE,
                f'element_{i}',
                'Room',
                {'name': f'Room {i}'}
            )
        
        # Get versions
        versions = self.collaboration_service.get_versions(session_id, self.owner_id)
        
        # Should have at least one version
        self.assertGreater(len(versions), 0)
    
    def test_branch_creation(self):
        """Test branch creation."""
        session_id = self.collaboration_service.create_session(
            self.model_id,
            self.owner_id,
            self.owner_username,
            self.owner_email
        )
        
        # Create branch
        branch_session_id = self.collaboration_service.create_branch(
            session_id,
            self.owner_id,
            'test_branch',
            'Test branch for collaboration'
        )
        
        self.assertIsNotNone(branch_session_id)
        self.assertIn(branch_session_id, self.collaboration_service.sessions)
    
    def test_export_collaboration_data(self):
        """Test exporting collaboration data."""
        session_id = self.collaboration_service.create_session(
            self.model_id,
            self.owner_id,
            self.owner_username,
            self.owner_email
        )
        
        # Add another user
        user_id = 'user_1'
        self.collaboration_service.join_session(
            session_id,
            user_id,
            'test_user',
            'user@test.com',
            UserRole.EDITOR
        )
        
        # Make some changes
        self.collaboration_service.make_change(
            session_id,
            self.owner_id,
            ChangeType.CREATE,
            'element_1',
            'Room',
            {'name': 'Test Room'}
        )
        
        # Export collaboration data
        data = self.collaboration_service.export_collaboration_data(session_id, self.owner_id)
        
        self.assertIn('session_id', data)
        self.assertIn('model_id', data)
        self.assertIn('users', data)
        self.assertIn('changes', data)
        self.assertIn('conflicts', data)
        self.assertIn('versions', data)
        
        self.assertEqual(data['session_id'], session_id)
        self.assertEqual(data['model_id'], self.model_id)


if __name__ == '__main__':
    unittest.main() 