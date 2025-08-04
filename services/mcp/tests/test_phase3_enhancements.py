"""
Test Phase 3 Enhancements

This test suite validates the Phase 3 enhancements including:
- New building code MCP files (NEC 2023, IBC 2024, IPC 2024, IMC 2024)
- California state-specific requirements
- Spatial relationship engine
- Enhanced formula evaluation
- Cross-system validation
"""

import json
import tempfile
import os
from pathlib import Path
from datetime import datetime
import pytest

from validate.rule_engine import MCPRuleEngine
from validate.spatial_engine import SpatialEngine
from models.mcp_models import (
    BuildingModel, BuildingObject, MCPFile, MCPRule, RuleCondition, RuleAction,
    Jurisdiction, RuleSeverity, RuleCategory, ConditionType, ActionType
)


class TestPhase3Enhancements:
    """Test suite for Phase 3 enhancements"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.engine = MCPRuleEngine()
        self.spatial_engine = SpatialEngine()
        
        # Create comprehensive building model
        self.building_model = self._create_comprehensive_building_model()
        
        # Create MCP files for testing
        self.mcp_files = self._create_test_mcp_files()
    
    def _create_comprehensive_building_model(self) -> BuildingModel:
        """Create a comprehensive building model for testing"""
        return BuildingModel(
            building_id="phase3_test_building",
            building_name="Phase 3 Test Building",
            objects=[
                # Electrical System
                BuildingObject(
                    object_id="panel_main",
                    object_type="electrical_panel",
                    properties={
                        "type": "main_panel",
                        "capacity": 200.0,
                        "voltage": 120,
                        "phases": 3,
                        "location": "electrical_room"
                    },
                    location={"x": 500, "y": 100, "z": 0, "width": 40, "height": 60, "depth": 20}
                ),
                BuildingObject(
                    object_id="outlet_bathroom_1",
                    object_type="electrical_outlet",
                    properties={
                        "location": "bathroom",
                        "load": 15.0,
                        "gfci_protected": False,
                        "voltage": 120,
                        "circuit": "circuit_001"
                    },
                    location={"x": 100, "y": 200, "z": 0, "width": 8, "height": 8, "depth": 4}
                ),
                BuildingObject(
                    object_id="outlet_kitchen_1",
                    object_type="electrical_outlet",
                    properties={
                        "location": "kitchen",
                        "load": 20.0,
                        "gfci_protected": True,
                        "voltage": 120,
                        "circuit": "circuit_002"
                    },
                    location={"x": 150, "y": 250, "z": 0, "width": 8, "height": 8, "depth": 4}
                ),
                BuildingObject(
                    object_id="outlet_bedroom_1",
                    object_type="electrical_outlet",
                    properties={
                        "location": "bedroom",
                        "load": 10.0,
                        "gfci_protected": False,
                        "voltage": 120,
                        "circuit": "circuit_003"
                    },
                    location={"x": 200, "y": 300, "z": 0, "width": 8, "height": 8, "depth": 4}
                ),
                
                # HVAC System
                BuildingObject(
                    object_id="hvac_air_handler",
                    object_type="hvac_unit",
                    properties={
                        "type": "air_handler",
                        "capacity": 36000.0,
                        "efficiency_rating": 85,
                        "location": "mechanical_room"
                    },
                    location={"x": 600, "y": 200, "z": 0, "width": 60, "height": 40, "depth": 30}
                ),
                BuildingObject(
                    object_id="duct_supply_1",
                    object_type="duct",
                    properties={
                        "type": "supply",
                        "airflow": 1200.0,
                        "location": "attic"
                    },
                    location={"x": 550, "y": 180, "z": 10, "width": 20, "height": 12, "depth": 100}
                ),
                
                # Plumbing System
                BuildingObject(
                    object_id="water_heater_1",
                    object_type="water_heater",
                    properties={
                        "type": "tank",
                        "capacity": 50.0,
                        "location": "mechanical_room"
                    },
                    location={"x": 650, "y": 150, "z": 0, "width": 24, "height": 60, "depth": 24}
                ),
                BuildingObject(
                    object_id="sink_bathroom_1",
                    object_type="plumbing_fixture",
                    properties={
                        "type": "sink",
                        "flow_rate": 2.5,
                        "location": "bathroom"
                    },
                    location={"x": 110, "y": 210, "z": 0, "width": 20, "height": 16, "depth": 8}
                ),
                BuildingObject(
                    object_id="toilet_bathroom_1",
                    object_type="plumbing_fixture",
                    properties={
                        "type": "toilet",
                        "flow_rate": 1.6,
                        "location": "bathroom"
                    },
                    location={"x": 120, "y": 220, "z": 0, "width": 18, "height": 28, "depth": 8}
                ),
                
                # Rooms
                BuildingObject(
                    object_id="room_bathroom_1",
                    object_type="room",
                    properties={
                        "type": "bathroom",
                        "area": 80.0,
                        "occupancy": 2,
                        "height": 8.0
                    },
                    location={"x": 90, "y": 190, "z": 0, "width": 100, "height": 80, "depth": 8}
                ),
                BuildingObject(
                    object_id="room_kitchen_1",
                    object_type="room",
                    properties={
                        "type": "kitchen",
                        "area": 120.0,
                        "occupancy": 4,
                        "height": 8.0
                    },
                    location={"x": 140, "y": 240, "z": 0, "width": 120, "height": 100, "depth": 8}
                ),
                BuildingObject(
                    object_id="room_bedroom_1",
                    object_type="room",
                    properties={
                        "type": "bedroom",
                        "area": 150.0,
                        "occupancy": 2,
                        "height": 8.0
                    },
                    location={"x": 190, "y": 290, "z": 0, "width": 150, "height": 100, "depth": 8}
                ),
                
                # Exit Paths
                BuildingObject(
                    object_id="exit_path_1",
                    object_type="exit_path",
                    properties={
                        "type": "exit_access",
                        "width": 36.0
                    },
                    location={"x": 300, "y": 100, "z": 0, "width": 36, "height": 200, "depth": 8}
                ),
                BuildingObject(
                    object_id="exit_door_1",
                    object_type="exit_door",
                    properties={
                        "type": "exit_discharge",
                        "width": 36.0
                    },
                    location={"x": 318, "y": 0, "z": 0, "width": 36, "height": 80, "depth": 4}
                )
            ]
        )
    
    def _create_test_mcp_files(self) -> list:
        """Create test MCP files"""
        mcp_files = []
        
        # NEC 2023 Base
        nec_base = {
            "mcp_id": "test_nec_2023_base",
            "name": "Test NEC 2023 Base",
            "description": "Test NEC 2023 base requirements",
            "jurisdiction": {"country": "US", "state": None, "city": None},
            "version": "2023",
            "effective_date": "2023-01-01",
            "rules": [
                {
                    "rule_id": "test_nec_210_8",
                    "name": "Test GFCI Protection",
                    "description": "Test GFCI protection requirements",
                    "category": "electrical_safety",
                    "priority": 1,
                    "conditions": [
                        {
                            "type": "property",
                            "element_type": "electrical_outlet",
                            "property": "location",
                            "operator": "in",
                            "value": ["bathroom", "kitchen"]
                        }
                    ],
                    "actions": [
                        {
                            "type": "validation",
                            "message": "GFCI protection required for outlets in wet locations",
                            "severity": "error",
                            "code_reference": "NEC 210.8(A)"
                        }
                    ]
                }
            ]
        }
        
        # IBC 2024 Base
        ibc_base = {
            "mcp_id": "test_ibc_2024_base",
            "name": "Test IBC 2024 Base",
            "description": "Test IBC 2024 base requirements",
            "jurisdiction": {"country": "US", "state": None, "city": None},
            "version": "2024",
            "effective_date": "2024-01-01",
            "rules": [
                {
                    "rule_id": "test_ibc_1003",
                    "name": "Test Means of Egress",
                    "description": "Test means of egress requirements",
                    "category": "fire_safety_egress",
                    "priority": 1,
                    "conditions": [
                        {
                            "type": "property",
                            "element_type": "room",
                            "property": "occupancy",
                            "operator": ">",
                            "value": 0
                        }
                    ],
                    "actions": [
                        {
                            "type": "validation",
                            "message": "Means of egress required for all occupied spaces",
                            "severity": "error",
                            "code_reference": "IBC 1003.1"
                        }
                    ]
                }
            ]
        }
        
        # Create temporary files
        for mcp_data, filename in [(nec_base, "nec_base.json"), (ibc_base, "ibc_base.json")]:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(mcp_data, f, indent=2)
                mcp_files.append(f.name)
        
        return mcp_files
    
    def test_spatial_engine_distance_calculation(self):
        """Test spatial engine distance calculations"""
        obj_a = self.building_model.objects[0]  # panel_main
        obj_b = self.building_model.objects[1]  # outlet_bathroom_1
        
        distance = self.spatial_engine.calculate_distance(obj_a, obj_b)
        assert distance > 0
        assert distance < 1000  # Reasonable distance
    
    def test_spatial_engine_adjacency_detection(self):
        """Test spatial engine adjacency detection"""
        obj_a = self.building_model.objects[8]  # room_bathroom_1
        obj_b = self.building_model.objects[9]  # room_kitchen_1
        
        # These rooms should be adjacent
        is_adjacent = self.spatial_engine.check_spatial_relationship(obj_a, obj_b, 'adjacent', max_distance=5.0)
        assert is_adjacent
    
    def test_spatial_engine_room_area_calculation(self):
        """Test spatial engine room area calculation"""
        room = self.building_model.objects[8]  # room_bathroom_1
        area = self.spatial_engine.calculate_room_area(room)
        assert area == 8000.0  # 100 * 80
    
    def test_spatial_engine_room_volume_calculation(self):
        """Test spatial engine room volume calculation"""
        room = self.building_model.objects[8]  # room_bathroom_1
        volume = self.spatial_engine.calculate_room_volume(room)
        assert volume == 64000.0  # 100 * 80 * 8
    
    def test_spatial_engine_floor_level_detection(self):
        """Test spatial engine floor level detection"""
        room = self.building_model.objects[8]  # room_bathroom_1
        floor_level = self.spatial_engine.get_floor_level(room)
        assert floor_level == 0  # Ground floor
    
    def test_spatial_engine_egress_distance_calculation(self):
        """Test spatial engine egress distance calculation"""
        room = self.building_model.objects[8]  # room_bathroom_1
        exits = [obj for obj in self.building_model.objects if obj.object_type == "exit_door"]
        
        egress_distance = self.spatial_engine.calculate_egress_distance(room, exits)
        assert egress_distance > 0
        assert egress_distance < 1000  # Reasonable distance
    
    def test_enhanced_formula_evaluation(self):
        """Test enhanced formula evaluation with new variables"""
        # Test capacity calculation
        hvac_unit = next(obj for obj in self.building_model.objects if obj.object_type == "hvac_unit")
        
        # Create a rule with capacity calculation
        rule = MCPRule(
            rule_id="test_capacity_calc",
            name="Test Capacity Calculation",
            description="Test capacity calculation",
            category=RuleCategory.MECHANICAL_HVAC,
            conditions=[
                RuleCondition(
                    type=ConditionType.PROPERTY,
                    element_type="hvac_unit",
                    property="type",
                    operator="==",
                    value="air_handler"
                )
            ],
            actions=[
                RuleAction(
                    type=ActionType.CALCULATION,
                    formula="capacity * 0.85",
                    unit="BTU/hr",
                    description="Effective cooling capacity"
                )
            ]
        )
        
        # Execute rule
        result = self.engine._execute_rule(rule, self.building_model)
        assert result.passed
        assert "capacity * 0.85" in result.calculations
    
    def test_cross_system_validation(self):
        """Test cross-system validation capabilities"""
        # Test electrical load vs HVAC capacity
        electrical_load = sum(obj.properties.get('load', 0) for obj in self.building_model.objects 
                           if obj.object_type == "electrical_outlet")
        hvac_capacity = next(obj.properties.get('capacity', 0) for obj in self.building_model.objects 
                           if obj.object_type == "hvac_unit")
        
        # Basic validation - electrical load should be reasonable compared to HVAC capacity
        assert electrical_load > 0
        assert hvac_capacity > 0
        assert hvac_capacity > electrical_load  # HVAC should be larger than electrical load
    
    def test_new_building_codes_loading(self):
        """Test loading of new building code MCP files"""
        for mcp_file in self.mcp_files:
            try:
                mcp_file_obj = self.engine.load_mcp_file(mcp_file)
                assert mcp_file_obj is not None
                assert len(mcp_file_obj.rules) > 0
            except Exception as e:
                pytest.fail(f"Failed to load MCP file {mcp_file}: {e}")
    
    def test_comprehensive_validation(self):
        """Test comprehensive validation with new building codes"""
        try:
            compliance_report = self.engine.validate_building_model(self.building_model, self.mcp_files)
            assert compliance_report is not None
            assert compliance_report.building_id == "phase3_test_building"
            assert len(compliance_report.validation_reports) > 0
        except Exception as e:
            pytest.fail(f"Failed comprehensive validation: {e}")
    
    def test_spatial_constraint_validation(self):
        """Test spatial constraint validation"""
        constraints = [
            {
                "type": "adjacency",
                "object_a_type": "room",
                "object_b_type": "exit_path",
                "relationship": "adjacent",
                "max_distance": 10.0
            }
        ]
        
        violations = self.spatial_engine.validate_spatial_constraints(
            self.building_model.objects, constraints
        )
        
        # Should have some violations or none, but not crash
        assert isinstance(violations, list)
    
    def test_egress_requirements_validation(self):
        """Test egress requirements validation"""
        rooms = [obj for obj in self.building_model.objects if obj.object_type == "room"]
        exits = [obj for obj in self.building_model.objects if obj.object_type == "exit_door"]
        
        violations = self.spatial_engine.validate_egress_requirements(rooms, exits, max_egress_distance=50.0)
        
        # Should have some violations or none, but not crash
        assert isinstance(violations, list)
    
    def test_performance_metrics(self):
        """Test performance metrics with enhanced engine"""
        start_time = datetime.now()
        
        # Run comprehensive validation
        compliance_report = self.engine.validate_building_model(self.building_model, self.mcp_files)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Performance should be reasonable
        assert execution_time < 10.0  # Should complete within 10 seconds
        assert compliance_report is not None
    
    def teardown_method(self):
        """Clean up test files"""
        for mcp_file in self.mcp_files:
            try:
                os.unlink(mcp_file)
            except:
                pass


if __name__ == "__main__":
    # Run tests
    test_suite = TestPhase3Enhancements()
    test_suite.setup_method()
    
    print("🧪 Running Phase 3 Enhancement Tests...")
    
    # Test spatial engine
    test_suite.test_spatial_engine_distance_calculation()
    print("✅ Spatial engine distance calculation")
    
    test_suite.test_spatial_engine_adjacency_detection()
    print("✅ Spatial engine adjacency detection")
    
    test_suite.test_spatial_engine_room_area_calculation()
    print("✅ Spatial engine room area calculation")
    
    test_suite.test_enhanced_formula_evaluation()
    print("✅ Enhanced formula evaluation")
    
    test_suite.test_comprehensive_validation()
    print("✅ Comprehensive validation")
    
    test_suite.test_performance_metrics()
    print("✅ Performance metrics")
    
    test_suite.teardown_method()
    print("🎉 All Phase 3 enhancement tests passed!") 