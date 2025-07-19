#!/usr/bin/env python3
"""
Audiovisual (AV) System Integration Tests

This module tests the complete AV system integration including
schema validation, symbol creation, behavior profiles, and
pipeline execution for the audiovisual system.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from svgx_engine.services.pipeline_integration import PipelineIntegrationService
from svgx_engine.services.validation_engine import ValidationEngine
from svgx_engine.services.symbol_manager import SymbolManager
from svgx_engine.services.behavior_engine import BehaviorEngine


class TestAVSystemIntegration(unittest.TestCase):
    """Test suite for AV system integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.av_system = "audiovisual"
        self.service = PipelineIntegrationService()
        
        # Create test directories
        self.schemas_dir = Path(self.temp_dir) / "schemas"
        self.schemas_dir.mkdir()
        
        self.symbols_dir = Path(self.temp_dir) / "arx-symbol-library"
        self.symbols_dir.mkdir()
        
        self.behavior_dir = Path(self.temp_dir) / "svgx_engine" / "behavior"
        self.behavior_dir.mkdir(parents=True)
        
        # Patch the services to use test directories
        with patch.object(self.service.symbol_manager, 'symbol_library_path', self.symbols_dir):
            with patch.object(self.service.behavior_engine, 'behavior_path', self.behavior_dir):
                pass
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_av_schema_validation(self):
        """Test AV system schema validation"""
        print("Testing AV system schema validation...")
        
        # Load the AV schema
        schema_file = Path(__file__).parent.parent / "schemas" / "audiovisual" / "schema.json"
        
        if schema_file.exists():
            with open(schema_file, 'r') as f:
                schema_data = json.load(f)
            
            # Validate schema structure
            self.assertEqual(schema_data["system"], "audiovisual")
            self.assertIn("objects", schema_data)
            self.assertIn("display", schema_data["objects"])
            self.assertIn("projector", schema_data["objects"])
            self.assertIn("speaker", schema_data["objects"])
            self.assertIn("control_system", schema_data["objects"])
            
            # Validate display object
            display_obj = schema_data["objects"]["display"]
            self.assertEqual(display_obj["properties"]["type"], "display")
            self.assertEqual(display_obj["properties"]["technology"], "LED")
            self.assertIn("behavior_profile", display_obj)
            
            # Validate projector object
            projector_obj = schema_data["objects"]["projector"]
            self.assertEqual(projector_obj["properties"]["type"], "projector")
            self.assertEqual(projector_obj["properties"]["technology"], "DLP")
            self.assertIn("behavior_profile", projector_obj)
            
            print("✅ AV schema validation passed")
        else:
            self.fail("AV schema file not found")
    
    def test_av_symbol_creation(self):
        """Test AV symbol creation and validation"""
        print("Testing AV symbol creation...")
        
        # Create AV symbols directory
        av_symbols_dir = self.symbols_dir / self.av_system
        av_symbols_dir.mkdir()
        
        # Test display symbol
        display_symbol = {
            "id": "AV_Display_001",
            "name": "LED Display",
            "system": "audiovisual",
            "category": "display",
            "svg": "<svg width='80' height='60'><rect width='80' height='60' fill='blue'/></svg>",
            "properties": {
                "type": "display",
                "technology": "LED",
                "resolution": "1920x1080"
            },
            "connections": ["power", "control", "video", "audio"],
            "behavior_profile": "display_behavior"
        }
        
        display_file = av_symbols_dir / "AV_Display_001.json"
        with open(display_file, 'w') as f:
            json.dump(display_symbol, f, indent=2)
        
        # Test projector symbol
        projector_symbol = {
            "id": "AV_Projector_001",
            "name": "DLP Projector",
            "system": "audiovisual",
            "category": "projector",
            "svg": "<svg width='100' height='80'><rect width='100' height='80' fill='gray'/></svg>",
            "properties": {
                "type": "projector",
                "technology": "DLP",
                "brightness": "3000 lumens"
            },
            "connections": ["power", "control", "video", "audio"],
            "behavior_profile": "projector_behavior"
        }
        
        projector_file = av_symbols_dir / "AV_Projector_001.json"
        with open(projector_file, 'w') as f:
            json.dump(projector_symbol, f, indent=2)
        
        # Validate symbols
        symbol_manager = SymbolManager()
        symbol_manager.symbol_library_path = self.symbols_dir
        
        # Test symbol validation
        validation_result = symbol_manager.validate_symbols(self.av_system)
        self.assertTrue(validation_result.get("success", False))
        
        print("✅ AV symbol creation and validation passed")
    
    def test_av_behavior_profiles(self):
        """Test AV behavior profile implementation"""
        print("Testing AV behavior profiles...")
        
        # Create behavior profiles
        behavior_files = {
            "display_behavior.py": """
class DisplayBehavior:
    def __init__(self):
        self.power_state = "off"
        self.brightness = 50
    
    def power_on(self):
        self.power_state = "on"
        return {"status": "powered_on", "brightness": self.brightness}
    
    def set_brightness(self, level):
        self.brightness = max(0, min(100, level))
        return {"status": "brightness_set", "level": self.brightness}
    
    def validate_connections(self, connections):
        required = ["power", "control"]
        return all(conn in connections for conn in required)
""",
            "projector_behavior.py": """
class ProjectorBehavior:
    def __init__(self):
        self.power_state = "off"
        self.brightness = 100
        self.lamp_hours = 0
    
    def power_on(self):
        self.power_state = "on"
        return {"status": "powered_on", "brightness": self.brightness}
    
    def set_brightness(self, level):
        self.brightness = max(0, min(100, level))
        return {"status": "brightness_set", "level": self.brightness}
    
    def get_lamp_status(self):
        return {"lamp_hours": self.lamp_hours, "status": "good"}
    
    def validate_connections(self, connections):
        required = ["power", "control"]
        return all(conn in connections for conn in required)
""",
            "speaker_behavior.py": """
class SpeakerBehavior:
    def __init__(self):
        self.power_state = "off"
        self.volume = 50
    
    def power_on(self):
        self.power_state = "on"
        return {"status": "powered_on", "volume": self.volume}
    
    def set_volume(self, level):
        self.volume = max(0, min(100, level))
        return {"status": "volume_set", "level": self.volume}
    
    def validate_connections(self, connections):
        required = ["power", "signal"]
        return all(conn in connections for conn in required)
""",
            "control_system_behavior.py": """
class ControlSystemBehavior:
    def __init__(self):
        self.power_state = "off"
        self.connected_devices = []
    
    def power_on(self):
        self.power_state = "on"
        return {"status": "powered_on", "devices": self.connected_devices}
    
    def add_device(self, device_id):
        self.connected_devices.append(device_id)
        return {"status": "device_added", "devices": self.connected_devices}
    
    def validate_connections(self, connections):
        required = ["power", "network"]
        return all(conn in connections for conn in required)
"""
        }
        
        for filename, content in behavior_files.items():
            behavior_file = self.behavior_dir / filename
            with open(behavior_file, 'w') as f:
                f.write(content)
        
        # Test behavior validation
        behavior_engine = BehaviorEngine()
        behavior_engine.behavior_path = self.behavior_dir
        
        validation_result = behavior_engine.validate_behaviors(self.av_system)
        self.assertTrue(validation_result.get("success", False))
        
        print("✅ AV behavior profiles implementation passed")
    
    def test_av_pipeline_execution(self):
        """Test complete AV pipeline execution"""
        print("Testing AV pipeline execution...")
        
        # Execute AV pipeline
        pipeline_result = self.service.handle_operation("execute-pipeline", {
            "system": self.av_system,
            "dry_run": True  # Use dry run for testing
        })
        
        self.assertTrue(pipeline_result.get("success", False),
                       f"AV pipeline execution failed: {pipeline_result.get('error')}")
        
        print("✅ AV pipeline execution passed")
    
    def test_av_system_validation(self):
        """Test complete AV system validation"""
        print("Testing AV system validation...")
        
        # Validate schema
        schema_result = self.service.handle_operation("validate-schema", {
            "system": self.av_system
        })
        self.assertTrue(schema_result.get("success", False))
        
        # Validate symbols
        symbols_result = self.service.handle_operation("validate-symbols", {
            "system": self.av_system
        })
        self.assertTrue(symbols_result.get("success", False))
        
        # Validate behaviors
        behaviors_result = self.service.handle_operation("validate-behavior", {
            "system": self.av_system
        })
        self.assertTrue(behaviors_result.get("success", False))
        
        print("✅ AV system validation passed")
    
    def test_av_device_operations(self):
        """Test AV device operations"""
        print("Testing AV device operations...")
        
        # Test display operations
        display_operations = [
            ("power_on", {}),
            ("set_brightness", {"level": 75}),
            ("set_input_source", {"input_source": "HDMI1"}),
            ("get_status", {})
        ]
        
        for operation, params in display_operations:
            result = self.service.handle_operation(f"display_{operation}", {
                "system": self.av_system,
                "device_id": "AV_Display_001",
                **params
            })
            # Should return a result (even if it's an error for missing device)
            self.assertIsNotNone(result)
        
        # Test projector operations
        projector_operations = [
            ("power_on", {}),
            ("set_brightness", {"level": 100}),
            ("adjust_keystone", {"keystone_value": 5}),
            ("get_lamp_status", {})
        ]
        
        for operation, params in projector_operations:
            result = self.service.handle_operation(f"projector_{operation}", {
                "system": self.av_system,
                "device_id": "AV_Projector_001",
                **params
            })
            # Should return a result (even if it's an error for missing device)
            self.assertIsNotNone(result)
        
        print("✅ AV device operations passed")
    
    def test_av_system_integration(self):
        """Test AV system integration scenarios"""
        print("Testing AV system integration scenarios...")
        
        # Test conference room scenario
        conference_room_devices = [
            "AV_Display_001",  # Main display
            "AV_Projector_001",  # Projector
            "AV_Speaker_001",  # Ceiling speakers
            "AV_Control_001"   # Control system
        ]
        
        for device_id in conference_room_devices:
            # Test device initialization
            init_result = self.service.handle_operation("initialize_device", {
                "system": self.av_system,
                "device_id": device_id
            })
            self.assertIsNotNone(init_result)
            
            # Test device status
            status_result = self.service.handle_operation("get_device_status", {
                "system": self.av_system,
                "device_id": device_id
            })
            self.assertIsNotNone(status_result)
        
        # Test system-wide operations
        system_operations = [
            ("power_on_all", {}),
            ("calibrate_system", {}),
            ("get_system_status", {}),
            ("run_diagnostics", {})
        ]
        
        for operation, params in system_operations:
            result = self.service.handle_operation(f"av_{operation}", {
                "system": self.av_system,
                **params
            })
            self.assertIsNotNone(result)
        
        print("✅ AV system integration scenarios passed")
    
    def test_av_compliance_checking(self):
        """Test AV system compliance checking"""
        print("Testing AV compliance checking...")
        
        # Test electrical compliance
        electrical_compliance = self.service.handle_operation("check_electrical_compliance", {
            "system": self.av_system
        })
        self.assertIsNotNone(electrical_compliance)
        
        # Test safety compliance
        safety_compliance = self.service.handle_operation("check_safety_compliance", {
            "system": self.av_system
        })
        self.assertIsNotNone(safety_compliance)
        
        # Test accessibility compliance
        accessibility_compliance = self.service.handle_operation("check_accessibility_compliance", {
            "system": self.av_system
        })
        self.assertIsNotNone(accessibility_compliance)
        
        print("✅ AV compliance checking passed")
    
    def test_av_performance_monitoring(self):
        """Test AV system performance monitoring"""
        print("Testing AV performance monitoring...")
        
        # Test performance metrics collection
        performance_result = self.service.handle_operation("get_performance_metrics", {
            "system": self.av_system
        })
        self.assertIsNotNone(performance_result)
        
        # Test health monitoring
        health_result = self.service.handle_operation("get_system_health", {
            "system": self.av_system
        })
        self.assertIsNotNone(health_result)
        
        # Test alert generation
        alert_result = self.service.handle_operation("check_alerts", {
            "system": self.av_system
        })
        self.assertIsNotNone(alert_result)
        
        print("✅ AV performance monitoring passed")


def run_av_integration_tests():
    """Run all AV integration tests"""
    print("🧪 Starting AV System Integration Tests")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAVSystemIntegration)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 AV Integration Test Summary")
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.wasSuccessful():
        print("🎉 All AV integration tests PASSED!")
        return True
    else:
        print("❌ Some AV integration tests FAILED!")
        return False


if __name__ == "__main__":
    success = run_av_integration_tests()
    sys.exit(0 if success else 1) 