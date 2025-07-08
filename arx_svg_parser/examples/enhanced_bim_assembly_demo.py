"""
Enhanced BIM Assembly Pipeline Demo

This example demonstrates the enhanced BIM assembly pipeline with:
- Automatic SVG-to-BIM typing
- Property extraction and unit conversion
- Device and system categorization
- Comprehensive BIM model creation
"""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Any

from ..services.bim_assembly import (
    BIMAssemblyPipeline, AssemblyConfig, extract_and_convert_properties,
    determine_device_category
)
from ..models.bim import (
    Room, Wall, Door, Window, Device, SystemType, DeviceCategory,
    HVACZone, ElectricalPanel, SmokeDetector, Camera
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_svg_data() -> Dict[str, Any]:
    """Create comprehensive sample SVG data for demonstration."""
    return {
        'elements': [
            # Room elements
            {
                'id': 'room-office-1',
                'type': 'rect',
                'name': 'Office 101',
                'geometry': {
                    'type': 'polygon',
                    'coordinates': [[0, 0], [20, 0], [20, 15], [0, 15], [0, 0]]
                },
                'properties': {
                    'width': 2000,  # 2000px
                    'height': 1500,  # 1500px
                    'area': 3000000,  # 3,000,000px²
                    'room_type': 'office',
                    'room_number': '101',
                    'floor_level': 1
                },
                'metadata': {
                    'layer': 'rooms'
                }
            },
            {
                'id': 'room-conference-1',
                'type': 'rect',
                'name': 'Conference Room A',
                'geometry': {
                    'type': 'polygon',
                    'coordinates': [[20, 0], [35, 0], [35, 20], [20, 20], [20, 0]]
                },
                'properties': {
                    'width': 1500,  # 1500px
                    'height': 2000,  # 2000px
                    'area': 3000000,  # 3,000,000px²
                    'room_type': 'conference',
                    'room_number': 'CONF-A',
                    'floor_level': 1
                },
                'metadata': {
                    'layer': 'rooms'
                }
            },
            
            # Wall elements
            {
                'id': 'wall-interior-1',
                'type': 'rect',
                'name': 'Interior Wall 1',
                'geometry': {
                    'type': 'linestring',
                    'coordinates': [[20, 0], [20, 15]]
                },
                'properties': {
                    'width': 150,   # 150px
                    'height': 300,  # 300px
                    'thickness': 200, # 200px
                    'wall_type': 'interior',
                    'material': 'drywall'
                },
                'metadata': {
                    'layer': 'walls'
                }
            },
            {
                'id': 'wall-exterior-1',
                'type': 'rect',
                'name': 'Exterior Wall 1',
                'geometry': {
                    'type': 'linestring',
                    'coordinates': [[0, 0], [35, 0]]
                },
                'properties': {
                    'width': 3500,  # 3500px
                    'height': 400,  # 400px
                    'thickness': 300, # 300px
                    'wall_type': 'exterior',
                    'material': 'concrete'
                },
                'metadata': {
                    'layer': 'walls'
                }
            },
            
            # Door elements
            {
                'id': 'door-entry-1',
                'type': 'rect',
                'name': 'Main Entry Door',
                'geometry': {
                    'type': 'linestring',
                    'coordinates': [[5, 0], [7, 0]]
                },
                'properties': {
                    'width': 200,   # 200px
                    'height': 240,  # 240px
                    'door_type': 'swing',
                    'material': 'wood',
                    'is_emergency_exit': True
                },
                'metadata': {
                    'layer': 'doors'
                }
            },
            {
                'id': 'door-interior-1',
                'type': 'rect',
                'name': 'Interior Door',
                'geometry': {
                    'type': 'linestring',
                    'coordinates': [[20, 7], [20, 8]]
                },
                'properties': {
                    'width': 100,   # 100px
                    'height': 240,  # 240px
                    'door_type': 'swing',
                    'material': 'wood',
                    'is_emergency_exit': False
                },
                'metadata': {
                    'layer': 'doors'
                }
            },
            
            # Window elements
            {
                'id': 'window-1',
                'type': 'rect',
                'name': 'Window 1',
                'geometry': {
                    'type': 'linestring',
                    'coordinates': [[2, 0], [4, 0]]
                },
                'properties': {
                    'width': 200,   # 200px
                    'height': 120,  # 120px
                    'window_type': 'fixed',
                    'glazing_type': 'double_pane',
                    'u_value': 0.35
                },
                'metadata': {
                    'layer': 'windows'
                }
            },
            
            # HVAC devices
            {
                'id': 'ahu-1',
                'type': 'rect',
                'name': 'Air Handler Unit 1',
                'geometry': {
                    'type': 'point',
                    'coordinates': [25, 10]
                },
                'properties': {
                    'width': 100,   # 100px
                    'height': 80,   # 80px
                    'system_type': 'hvac',
                    'manufacturer': 'Carrier',
                    'model': '48TC',
                    'capacity': 5000,  # BTU/hr
                    'airflow': 2000    # CFM
                },
                'metadata': {
                    'layer': 'hvac'
                }
            },
            {
                'id': 'vav-1',
                'type': 'rect',
                'name': 'VAV Box 1',
                'geometry': {
                    'type': 'point',
                    'coordinates': [10, 8]
                },
                'properties': {
                    'width': 60,    # 60px
                    'height': 40,   # 40px
                    'system_type': 'hvac',
                    'manufacturer': 'Titus',
                    'model': 'TSS',
                    'max_airflow': 500,  # CFM
                    'min_airflow': 50    # CFM
                },
                'metadata': {
                    'layer': 'hvac'
                }
            },
            
            # Electrical devices
            {
                'id': 'panel-1',
                'type': 'rect',
                'name': 'Electrical Panel 1',
                'geometry': {
                    'type': 'point',
                    'coordinates': [30, 12]
                },
                'properties': {
                    'width': 80,    # 80px
                    'height': 60,   # 60px
                    'system_type': 'electrical',
                    'manufacturer': 'Square D',
                    'model': 'QO',
                    'voltage': 120,
                    'amperage': 100,
                    'panel_type': 'distribution'
                },
                'metadata': {
                    'layer': 'electrical'
                }
            },
            {
                'id': 'outlet-1',
                'type': 'rect',
                'name': 'Electrical Outlet 1',
                'geometry': {
                    'type': 'point',
                    'coordinates': [5, 10]
                },
                'properties': {
                    'width': 20,    # 20px
                    'height': 15,   # 15px
                    'system_type': 'electrical',
                    'voltage': 120,
                    'amperage': 15,
                    'outlet_type': 'duplex',
                    'is_gfci': True
                },
                'metadata': {
                    'layer': 'electrical'
                }
            },
            
            # Fire alarm devices
            {
                'id': 'smoke-1',
                'type': 'circle',
                'name': 'Smoke Detector 1',
                'geometry': {
                    'type': 'point',
                    'coordinates': [8, 12]
                },
                'properties': {
                    'system_type': 'fire_alarm',
                    'detector_type': 'photoelectric',
                    'sensitivity': 'high',
                    'coverage_area': 900  # sq ft
                },
                'metadata': {
                    'layer': 'smoke_detectors'
                }
            },
            {
                'id': 'pull-1',
                'type': 'rect',
                'name': 'Pull Station 1',
                'geometry': {
                    'type': 'point',
                    'coordinates': [15, 0]
                },
                'properties': {
                    'system_type': 'fire_alarm',
                    'pull_type': 'manual',
                    'height': 48  # inches
                },
                'metadata': {
                    'layer': 'pull_stations'
                }
            },
            
            # Security devices
            {
                'id': 'camera-1',
                'type': 'circle',
                'name': 'Security Camera 1',
                'geometry': {
                    'type': 'point',
                    'coordinates': [12, 5]
                },
                'properties': {
                    'system_type': 'security',
                    'camera_type': 'dome',
                    'resolution': '1080p',
                    'field_of_view': 90,
                    'night_vision': True
                },
                'metadata': {
                    'layer': 'cameras'
                }
            },
            {
                'id': 'card-reader-1',
                'type': 'rect',
                'name': 'Card Reader 1',
                'geometry': {
                    'type': 'point',
                    'coordinates': [20, 7.5]
                },
                'properties': {
                    'system_type': 'security',
                    'reader_type': 'proximity',
                    'technology': 'rfid'
                },
                'metadata': {
                    'layer': 'card_readers'
                }
            }
        ]
    }

def demonstrate_property_extraction():
    """Demonstrate property extraction and unit conversion."""
    logger.info("=== Property Extraction Demo ===")
    
    # Test property extraction
    svg_element = {
        'properties': {
            'width': 1000,  # 1000px
            'height': 800,   # 800px
            'thickness': 200, # 200px
            'area': 800000,  # 800,000px²
            'voltage': 120,
            'amperage': 100,
            'manufacturer': 'Carrier',
            'model': '48TC'
        },
        'metadata': {
            'layer': 'hvac',
            'style': 'solid'
        }
    }
    
    properties = extract_and_convert_properties(svg_element)
    
    logger.info("Original SVG properties:")
    logger.info(f"  Width: {svg_element['properties']['width']}px")
    logger.info(f"  Height: {svg_element['properties']['height']}px")
    logger.info(f"  Area: {svg_element['properties']['area']}px²")
    
    logger.info("Converted BIM properties:")
    logger.info(f"  Width: {properties['width']:.4f}m")
    logger.info(f"  Height: {properties['height']:.4f}m")
    logger.info(f"  Area: {properties['area']:.4f}m²")
    logger.info(f"  Voltage: {properties['voltage']}V")
    logger.info(f"  Amperage: {properties['amperage']}A")
    logger.info(f"  Manufacturer: {properties['manufacturer']}")
    logger.info(f"  Model: {properties['model']}")

def demonstrate_device_categorization():
    """Demonstrate device category determination."""
    logger.info("=== Device Categorization Demo ===")
    
    test_devices = [
        {'layer': 'ahu', 'expected': DeviceCategory.AHU},
        {'layer': 'vav_box', 'expected': DeviceCategory.VAV},
        {'layer': 'electrical_panel', 'expected': DeviceCategory.PANEL},
        {'layer': 'outlet', 'expected': DeviceCategory.OUTLET},
        {'layer': 'smoke_detector', 'expected': DeviceCategory.SMOKE_DETECTOR},
        {'layer': 'camera', 'expected': DeviceCategory.CAMERA},
        {'layer': 'unknown', 'expected': None}
    ]
    
    for device in test_devices:
        svg_element = {
            'type': 'rect',
            'metadata': {'layer': device['layer']},
            'properties': {}
        }
        
        category = determine_device_category(svg_element)
        expected = device['expected']
        
        logger.info(f"Layer: {device['layer']}")
        logger.info(f"  Detected Category: {category}")
        logger.info(f"  Expected Category: {expected}")
        logger.info(f"  Match: {category == expected}")
        logger.info("")

def demonstrate_assembly_pipeline():
    """Demonstrate the enhanced BIM assembly pipeline."""
    logger.info("=== Enhanced BIM Assembly Pipeline Demo ===")
    
    # Create assembly pipeline
    config = AssemblyConfig(
        validation_level='basic',
        conflict_resolution_enabled=False,
        performance_optimization_enabled=False,
        parallel_processing=False
    )
    pipeline = BIMAssemblyPipeline(config)
    
    # Create sample SVG data
    svg_data = create_sample_svg_data()
    
    logger.info(f"Processing {len(svg_data['elements'])} SVG elements...")
    
    # Mock geometry processor to avoid complex geometry generation
    pipeline.geometry_processor.generate_3d_from_2d_svg = lambda data, height: {
        'type': '3d_geometry',
        'center': [0, 0, 0],
        'size': [1, 1, 1]
    }
    
    # Process individual elements to demonstrate typing
    element_types = {}
    device_categories = {}
    
    for svg_element in svg_data['elements']:
        bim_element = pipeline._process_svg_element(svg_element)
        
        if bim_element:
            element_class = type(bim_element).__name__
            element_types[element_class] = element_types.get(element_class, 0) + 1
            
            if hasattr(bim_element, 'category'):
                category = bim_element.category
                if category:
                    device_categories[category.value] = device_categories.get(category.value, 0) + 1
            
            logger.info(f"Element: {bim_element.name}")
            logger.info(f"  BIM Class: {element_class}")
            logger.info(f"  Typing Confidence: {bim_element.metadata.get('typing', {}).get('confidence', 'N/A')}")
            if hasattr(bim_element, 'system_type'):
                logger.info(f"  System Type: {bim_element.system_type}")
            if hasattr(bim_element, 'category'):
                logger.info(f"  Device Category: {bim_element.category}")
            logger.info("")
    
    # Summary
    logger.info("=== Assembly Summary ===")
    logger.info("Element Type Distribution:")
    for element_type, count in element_types.items():
        logger.info(f"  {element_type}: {count}")
    
    logger.info("Device Category Distribution:")
    for category, count in device_categories.items():
        logger.info(f"  {category}: {count}")

def demonstrate_full_assembly():
    """Demonstrate full BIM assembly with automatic typing."""
    logger.info("=== Full BIM Assembly Demo ===")
    
    # Create assembly pipeline
    config = AssemblyConfig(
        validation_level='standard',
        conflict_resolution_enabled=True,
        performance_optimization_enabled=True,
        parallel_processing=False
    )
    pipeline = BIMAssemblyPipeline(config)
    
    # Create sample SVG data
    svg_data = create_sample_svg_data()
    
    # Mock geometry processor
    pipeline.geometry_processor.generate_3d_from_2d_svg = lambda data, height: {
        'type': '3d_geometry',
        'center': [0, 0, 0],
        'size': [1, 1, 1]
    }
    
    # Assemble BIM model
    logger.info("Starting BIM assembly...")
    result = pipeline.assemble_bim(svg_data)
    
    if result.success:
        logger.info("BIM assembly completed successfully!")
        logger.info(f"Assembly ID: {result.assembly_id}")
        logger.info(f"Total Elements: {len(result.elements)}")
        logger.info(f"Total Systems: {len(result.systems)}")
        logger.info(f"Total Spaces: {len(result.spaces)}")
        logger.info(f"Total Relationships: {len(result.relationships)}")
        logger.info(f"Assembly Time: {result.assembly_time:.3f}s")
        
        # Analyze element types
        element_type_counts = {}
        for element in result.elements:
            element_type = type(element).__name__
            element_type_counts[element_type] = element_type_counts.get(element_type, 0) + 1
        
        logger.info("Element Type Distribution:")
        for element_type, count in element_type_counts.items():
            logger.info(f"  {element_type}: {count}")
        
        # Check for typing metadata
        elements_with_typing = sum(1 for elem in result.elements if 'typing' in elem.metadata)
        logger.info(f"Elements with typing metadata: {elements_with_typing}/{len(result.elements)}")
        
        # Performance metrics
        logger.info("Performance Metrics:")
        for metric, value in result.performance_metrics.items():
            logger.info(f"  {metric}: {value}")
        
    else:
        logger.error("BIM assembly failed!")
        logger.error(f"Error: {result.validation_results.get('error', 'Unknown error')}")

def main():
    """Main demonstration function."""
    logger.info("Starting Enhanced BIM Assembly Pipeline Demo")
    
    # Demonstrate property extraction
    demonstrate_property_extraction()
    logger.info("")
    
    # Demonstrate device categorization
    demonstrate_device_categorization()
    logger.info("")
    
    # Demonstrate assembly pipeline
    demonstrate_assembly_pipeline()
    logger.info("")
    
    # Demonstrate full assembly
    demonstrate_full_assembly()
    
    logger.info("Demo completed successfully!")

if __name__ == "__main__":
    main() 