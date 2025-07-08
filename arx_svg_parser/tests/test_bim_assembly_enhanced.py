"""
Enhanced BIM Assembly Pipeline Tests

Tests for the enhanced BIM assembly pipeline with automatic typing,
property extraction, and unit conversion capabilities.
"""

import pytest
import json
from typing import Dict, List, Any

from ..services.bim_assembly import (
    BIMAssemblyPipeline, AssemblyConfig, extract_and_convert_properties,
    determine_device_category, BIM_CLASS_MAP
)
from ..models.bim import (
    Room, Wall, Door, Window, Device, SystemType, DeviceCategory,
    HVACZone, ElectricalPanel, SmokeDetector, Camera
)

class TestBIMAssemblyEnhanced:
    """Test cases for enhanced BIM assembly pipeline."""
    
    @pytest.fixture
    def assembly_pipeline(self):
        """Create a BIM assembly pipeline for testing."""
        config = AssemblyConfig(
            validation_level='basic',
            conflict_resolution_enabled=False,
            performance_optimization_enabled=False,
            parallel_processing=False
        )
        return BIMAssemblyPipeline(config)
    
    @pytest.fixture
    def sample_svg_data(self):
        """Create sample SVG data for testing."""
        return {
            'elements': [
                {
                    'id': 'room-1',
                    'type': 'rect',
                    'name': 'Office 101',
                    'geometry': {
                        'type': 'polygon',
                        'coordinates': [[0, 0], [10, 0], [10, 8], [0, 8], [0, 0]]
                    },
                    'properties': {
                        'width': 1000,  # 1000px
                        'height': 800,   # 800px
                        'area': 800000,  # 800,000px²
                        'room_type': 'office',
                        'room_number': '101'
                    },
                    'metadata': {
                        'layer': 'rooms'
                    }
                },
                {
                    'id': 'wall-1',
                    'type': 'rect',
                    'name': 'Interior Wall',
                    'geometry': {
                        'type': 'linestring',
                        'coordinates': [[0, 0], [10, 0]]
                    },
                    'properties': {
                        'width': 1000,  # 1000px
                        'height': 300,   # 300px
                        'thickness': 200, # 200px
                        'wall_type': 'interior'
                    },
                    'metadata': {
                        'layer': 'walls'
                    }
                },
                {
                    'id': 'door-1',
                    'type': 'rect',
                    'name': 'Entry Door',
                    'geometry': {
                        'type': 'linestring',
                        'coordinates': [[2, 0], [4, 0]]
                    },
                    'properties': {
                        'width': 200,   # 200px
                        'height': 240,  # 240px
                        'door_type': 'swing'
                    },
                    'metadata': {
                        'layer': 'doors'
                    }
                },
                {
                    'id': 'ahu-1',
                    'type': 'rect',
                    'name': 'Air Handler Unit',
                    'geometry': {
                        'type': 'point',
                        'coordinates': [5, 4]
                    },
                    'properties': {
                        'width': 100,   # 100px
                        'height': 80,   # 80px
                        'system_type': 'hvac',
                        'manufacturer': 'Carrier',
                        'model': '48TC',
                        'capacity': 5000  # BTU/hr
                    },
                    'metadata': {
                        'layer': 'hvac'
                    }
                },
                {
                    'id': 'panel-1',
                    'type': 'rect',
                    'name': 'Electrical Panel',
                    'geometry': {
                        'type': 'point',
                        'coordinates': [8, 6]
                    },
                    'properties': {
                        'width': 60,    # 60px
                        'height': 40,   # 40px
                        'system_type': 'electrical',
                        'voltage': 120,
                        'amperage': 100,
                        'panel_type': 'distribution'
                    },
                    'metadata': {
                        'layer': 'electrical'
                    }
                },
                {
                    'id': 'smoke-1',
                    'type': 'circle',
                    'name': 'Smoke Detector',
                    'geometry': {
                        'type': 'point',
                        'coordinates': [3, 6]
                    },
                    'properties': {
                        'system_type': 'fire_alarm',
                        'detector_type': 'photoelectric',
                        'sensitivity': 'high'
                    },
                    'metadata': {
                        'layer': 'smoke_detectors'
                    }
                },
                {
                    'id': 'camera-1',
                    'type': 'circle',
                    'name': 'Security Camera',
                    'geometry': {
                        'type': 'point',
                        'coordinates': [7, 2]
                    },
                    'properties': {
                        'system_type': 'security',
                        'camera_type': 'dome',
                        'resolution': '1080p',
                        'field_of_view': 90
                    },
                    'metadata': {
                        'layer': 'cameras'
                    }
                }
            ]
        }
    
    def test_extract_and_convert_properties(self):
        """Test property extraction and unit conversion."""
        svg_element = {
            'properties': {
                'width': 1000,  # 1000px
                'height': 800,   # 800px
                'thickness': 200, # 200px
                'x': 100,        # 100px
                'y': 200,        # 200px
                'area': 800000,  # 800,000px²
                'voltage': 120,
                'amperage': 100,
                'manufacturer': 'Carrier',
                'model': '48TC'
            },
            'metadata': {
                'layer': 'hvac',
                'style': 'solid',
                'visibility': 'visible'
            }
        }
        
        properties = extract_and_convert_properties(svg_element)
        
        # Check unit conversions (px to m)
        assert abs(properties['width'] - 0.2646) < 0.001  # 1000px * 0.0254/96
        assert abs(properties['height'] - 0.2117) < 0.001  # 800px * 0.0254/96
        assert abs(properties['thickness'] - 0.0529) < 0.001  # 200px * 0.0254/96
        assert abs(properties['x'] - 0.0265) < 0.001  # 100px * 0.0254/96
        assert abs(properties['y'] - 0.0529) < 0.001  # 200px * 0.0254/96
        assert abs(properties['area'] - 0.0556) < 0.001  # 800000px² * (0.0254/96)²
        
        # Check non-dimensional properties
        assert properties['voltage'] == 120
        assert properties['amperage'] == 100
        assert properties['manufacturer'] == 'Carrier'
        assert properties['model'] == '48TC'
        assert properties['layer'] == 'hvac'
        assert properties['style'] == 'solid'
        assert properties['visibility'] == 'visible'
    
    def test_determine_device_category(self):
        """Test device category determination."""
        # Test HVAC devices
        ahu_element = {
            'type': 'rect',
            'metadata': {'layer': 'ahu'},
            'properties': {}
        }
        assert determine_device_category(ahu_element) == DeviceCategory.AHU
        
        vav_element = {
            'type': 'rect',
            'metadata': {'layer': 'vav_box'},
            'properties': {}
        }
        assert determine_device_category(vav_element) == DeviceCategory.VAV
        
        # Test electrical devices
        panel_element = {
            'type': 'rect',
            'metadata': {'layer': 'electrical_panel'},
            'properties': {}
        }
        assert determine_device_category(panel_element) == DeviceCategory.PANEL
        
        outlet_element = {
            'type': 'rect',
            'metadata': {'layer': 'outlet'},
            'properties': {}
        }
        assert determine_device_category(outlet_element) == DeviceCategory.OUTLET
        
        # Test fire alarm devices
        smoke_element = {
            'type': 'circle',
            'metadata': {'layer': 'smoke_detector'},
            'properties': {}
        }
        assert determine_device_category(smoke_element) == DeviceCategory.SMOKE_DETECTOR
        
        # Test security devices
        camera_element = {
            'type': 'circle',
            'metadata': {'layer': 'camera'},
            'properties': {}
        }
        assert determine_device_category(camera_element) == DeviceCategory.CAMERA
        
        # Test unknown device
        unknown_element = {
            'type': 'rect',
            'metadata': {'layer': 'unknown'},
            'properties': {}
        }
        assert determine_device_category(unknown_element) is None
    
    def test_bim_class_mapping(self):
        """Test BIM class mapping."""
        assert 'Room' in BIM_CLASS_MAP
        assert 'Wall' in BIM_CLASS_MAP
        assert 'Door' in BIM_CLASS_MAP
        assert 'Window' in BIM_CLASS_MAP
        assert 'Device' in BIM_CLASS_MAP
        assert 'HVACZone' in BIM_CLASS_MAP
        assert 'ElectricalPanel' in BIM_CLASS_MAP
        assert 'SmokeDetector' in BIM_CLASS_MAP
        assert 'Camera' in BIM_CLASS_MAP
        assert 'BIMElement' in BIM_CLASS_MAP
        
        # Test class instantiation
        assert BIM_CLASS_MAP['Room'] == Room
        assert BIM_CLASS_MAP['Wall'] == Wall
        assert BIM_CLASS_MAP['Device'] == Device
    
    def test_assembly_pipeline_automatic_typing(self, assembly_pipeline, sample_svg_data):
        """Test automatic typing in assembly pipeline."""
        # Mock geometry processor to avoid complex geometry generation
        assembly_pipeline.geometry_processor.generate_3d_from_2d_svg = lambda data, height: {
            'type': '3d_geometry',
            'center': [0, 0, 0],
            'size': [1, 1, 1]
        }
        
        # Process individual elements
        room_element = sample_svg_data['elements'][0]
        bim_room = assembly_pipeline._process_svg_element(room_element)
        
        assert isinstance(bim_room, Room)
        assert bim_room.room_type == 'office'
        assert bim_room.room_number == '101'
        assert 'typing' in bim_room.model_metadata
        assert bim_room.model_metadata['typing']['bim_class'] == 'Room'
        
        wall_element = sample_svg_data['elements'][1]
        bim_wall = assembly_pipeline._process_svg_element(wall_element)
        
        assert isinstance(bim_wall, Wall)
        assert bim_wall.wall_type == 'interior'
        assert 'typing' in bim_wall.model_metadata
        assert bim_wall.model_metadata['typing']['bim_class'] == 'Wall'
        
        door_element = sample_svg_data['elements'][2]
        bim_door = assembly_pipeline._process_svg_element(door_element)
        
        assert isinstance(bim_door, Door)
        assert bim_door.door_type == 'swing'
        assert 'typing' in bim_door.model_metadata
        assert bim_door.model_metadata['typing']['bim_class'] == 'Door'
        
        ahu_element = sample_svg_data['elements'][3]
        bim_ahu = assembly_pipeline._process_svg_element(ahu_element)
        
        assert isinstance(bim_ahu, Device)
        assert bim_ahu.system_type == SystemType.HVAC
        assert bim_ahu.category == DeviceCategory.AHU
        assert bim_ahu.manufacturer == 'Carrier'
        assert bim_ahu.model == '48TC'
        assert 'typing' in bim_ahu.model_metadata
        assert bim_ahu.model_metadata['typing']['bim_class'] == 'Device'
        
        panel_element = sample_svg_data['elements'][4]
        bim_panel = assembly_pipeline._process_svg_element(panel_element)
        
        assert isinstance(bim_panel, ElectricalPanel)
        assert bim_panel.panel_type == 'distribution'
        assert bim_panel.voltage == 120
        assert bim_panel.amperage == 100
        assert 'typing' in bim_panel.model_metadata
        assert bim_panel.model_metadata['typing']['bim_class'] == 'ElectricalPanel'
        
        smoke_element = sample_svg_data['elements'][5]
        bim_smoke = assembly_pipeline._process_svg_element(smoke_element)
        
        assert isinstance(bim_smoke, SmokeDetector)
        assert bim_smoke.detector_type == 'photoelectric'
        assert bim_smoke.sensitivity == 'high'
        assert 'typing' in bim_smoke.model_metadata
        assert bim_smoke.model_metadata['typing']['bim_class'] == 'SmokeDetector'
        
        camera_element = sample_svg_data['elements'][6]
        bim_camera = assembly_pipeline._process_svg_element(camera_element)
        
        assert isinstance(bim_camera, Camera)
        assert bim_camera.camera_type == 'dome'
        assert bim_camera.resolution == '1080p'
        assert bim_camera.field_of_view == 90
        assert 'typing' in bim_camera.model_metadata
        assert bim_camera.model_metadata['typing']['bim_class'] == 'Camera'
    
    def test_property_extraction_edge_cases(self):
        """Test property extraction with edge cases."""
        # Test missing properties
        svg_element = {
            'properties': {},
            'metadata': {}
        }
        properties = extract_and_convert_properties(svg_element)
        assert isinstance(properties, dict)
        assert len(properties) == 0
        
        # Test invalid numeric values
        svg_element = {
            'properties': {
                'width': 'invalid',
                'height': None,
                'voltage': '120'
            },
            'metadata': {}
        }
        properties = extract_and_convert_properties(svg_element)
        # Should handle gracefully without crashing
        assert isinstance(properties, dict)
        
        # Test with only metadata
        svg_element = {
            'properties': {},
            'metadata': {
                'layer': 'test_layer',
                'style': 'dashed'
            }
        }
        properties = extract_and_convert_properties(svg_element)
        assert properties['layer'] == 'test_layer'
        assert properties['style'] == 'dashed'
    
    def test_device_category_edge_cases(self):
        """Test device category determination with edge cases."""
        # Test missing metadata
        svg_element = {
            'type': 'rect',
            'metadata': {},
            'properties': {}
        }
        assert determine_device_category(svg_element) is None
        
        # Test case insensitive matching
        svg_element = {
            'type': 'rect',
            'metadata': {'layer': 'AHU'},
            'properties': {}
        }
        assert determine_device_category(svg_element) == DeviceCategory.AHU
        
        # Test partial matches
        svg_element = {
            'type': 'rect',
            'metadata': {'layer': 'air_handler_unit'},
            'properties': {}
        }
        assert determine_device_category(svg_element) == DeviceCategory.AHU
    
    def test_assembly_pipeline_integration(self, assembly_pipeline, sample_svg_data):
        """Test full assembly pipeline integration."""
        # Mock geometry processor
        assembly_pipeline.geometry_processor.generate_3d_from_2d_svg = lambda data, height: {
            'type': '3d_geometry',
            'center': [0, 0, 0],
            'size': [1, 1, 1]
        }
        
        # Test assembly with automatic typing
        result = assembly_pipeline.assemble_bim(sample_svg_data)
        
        assert result.success is True
        assert len(result.elements) == 7
        
        # Check that elements are properly typed
        element_types = [type(elem) for elem in result.elements]
        assert Room in element_types
        assert Wall in element_types
        assert Door in element_types
        assert Device in element_types
        assert ElectricalPanel in element_types
        assert SmokeDetector in element_types
        assert Camera in element_types
        
        # Check that all elements have typing metadata
        for element in result.elements:
            assert 'typing' in element.metadata
            assert 'bim_class' in element.metadata['typing']
            assert 'confidence' in element.metadata['typing']
            assert 'typing_method' in element.metadata['typing']
    
    def test_fallback_to_bim_element(self, assembly_pipeline):
        """Test fallback to generic BIMElement when no mapping is found."""
        # Create SVG element with unknown type/layer combination
        unknown_element = {
            'id': 'unknown-1',
            'type': 'unknown_type',
            'name': 'Unknown Element',
            'geometry': {
                'type': 'point',
                'coordinates': [0, 0]
            },
            'properties': {},
            'metadata': {
                'layer': 'unknown_layer'
            }
        }
        
        # Mock geometry processor
        assembly_pipeline.geometry_processor.generate_3d_from_2d_svg = lambda data, height: {
            'type': '3d_geometry',
            'center': [0, 0, 0],
            'size': [1, 1, 1]
        }
        
        bim_element = assembly_pipeline._process_svg_element(unknown_element)
        
        # Should fallback to generic BIMElement
        assert isinstance(bim_element, BIMElement)
        assert bim_element.name == 'Unknown Element'
        assert 'typing' in bim_element.model_metadata
        assert bim_element.model_metadata['typing']['bim_class'] == 'BIMElement'

if __name__ == "__main__":
    pytest.main([__file__]) 