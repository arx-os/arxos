"""
Tests for Advanced Rule Types

This module tests the advanced rule type components:
- Temporal rules engine
- Machine learning rules engine
- Dynamic rules engine
- Advanced rule integration
"""

import pytest
import time
import tempfile
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

from validate.temporal_engine import TemporalRuleEngine, TemporalCondition, TemporalOperator
from validate.ml_engine import MLRuleEngine, MLFeature, MLPrediction
from validate.dynamic_engine import DynamicRuleEngine
from models.mcp_models import (
    BuildingModel, BuildingObject, MCPFile, MCPRule, RuleCondition, RuleAction,
    Jurisdiction, RuleSeverity, RuleCategory, ConditionType, ActionType
)


class TestTemporalRules:
    """Test suite for temporal rules engine"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temporal_engine = TemporalRuleEngine()
        
        # Create test building model
        self.building_model = BuildingModel(
            building_id="test_building",
            building_name="Test Building",
            objects=[
                BuildingObject(
                    object_id="obj_1",
                    object_type="electrical_outlet",
                    properties={"load": 15.0, "voltage": 120},
                    location={"x": 10, "y": 10, "width": 5, "height": 3}
                ),
                BuildingObject(
                    object_id="obj_2",
                    object_type="light_fixture",
                    properties={"load": 60.0, "voltage": 120},
                    location={"x": 20, "y": 20, "width": 8, "height": 4}
                )
            ]
        )
    
    def test_temporal_condition_evaluation(self):
        """Test temporal condition evaluation"""
        # Test before condition
        condition = TemporalCondition(
            operator=TemporalOperator.BEFORE,
            start_time="2024-12-31 23:59:59",
            timezone="UTC"
        )
        
        result = self.temporal_engine.evaluate_temporal_condition(condition)
        assert isinstance(result, bool)
        
        # Test after condition
        condition = TemporalCondition(
            operator=TemporalOperator.AFTER,
            start_time="2020-01-01 00:00:00",
            timezone="UTC"
        )
        
        result = self.temporal_engine.evaluate_temporal_condition(condition)
        assert isinstance(result, bool)
    
    def test_business_hours_condition(self):
        """Test business hours condition"""
        condition = TemporalCondition(
            operator=TemporalOperator.BUSINESS_HOURS,
            business_hours_start="09:00",
            business_hours_end="17:00",
            timezone="UTC"
        )
        
        result = self.temporal_engine.evaluate_temporal_condition(condition)
        assert isinstance(result, bool)
    
    def test_weekday_weekend_conditions(self):
        """Test weekday and weekend conditions"""
        weekday_condition = TemporalCondition(operator=TemporalOperator.WEEKDAY)
        weekend_condition = TemporalCondition(operator=TemporalOperator.WEEKEND)
        
        weekday_result = self.temporal_engine.evaluate_temporal_condition(weekday_condition)
        weekend_result = self.temporal_engine.evaluate_temporal_condition(weekend_condition)
        
        assert isinstance(weekday_result, bool)
        assert isinstance(weekend_result, bool)
        # Weekday and weekend should be mutually exclusive
        assert weekday_result != weekend_result
    
    def test_during_condition(self):
        """Test during condition"""
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(hours=1)
        end_time = now + timedelta(hours=1)
        
        condition = TemporalCondition(
            operator=TemporalOperator.DURING,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            timezone="UTC"
        )
        
        result = self.temporal_engine.evaluate_temporal_condition(condition)
        assert result == True
    
    def test_every_condition(self):
        """Test recurring condition"""
        condition = TemporalCondition(
            operator=TemporalOperator.EVERY,
            start_time="every 30 minutes",
            timezone="UTC"
        )
        
        result = self.temporal_engine.evaluate_temporal_condition(condition)
        assert isinstance(result, bool)
    
    def test_create_temporal_rule(self):
        """Test creating temporal rule"""
        temporal_condition = TemporalCondition(
            operator=TemporalOperator.BUSINESS_HOURS,
            business_hours_start="09:00",
            business_hours_end="17:00"
        )
        
        base_conditions = [
            RuleCondition(
                type=ConditionType.PROPERTY,
                element_type="electrical_outlet",
                property="load",
                operator=">=",
                value=10.0
            )
        ]
        
        actions = [
            RuleAction(
                type=ActionType.VALIDATION,
                message="High load during business hours",
                severity=RuleSeverity.WARNING
            )
        ]
        
        rule = self.temporal_engine.create_temporal_rule(
            "temp_rule_001",
            "Temporal Test Rule",
            "Test temporal rule",
            temporal_condition,
            base_conditions,
            actions
        )
        
        assert rule.rule_id == "temp_rule_001"
        assert rule.category == RuleCategory.GENERAL
        assert len(rule.conditions) == 2  # Temporal + base condition
    
    def test_temporal_validation(self):
        """Test temporal validation"""
        # Create a simple temporal rule
        temporal_condition = TemporalCondition(
            operator=TemporalOperator.BUSINESS_HOURS,
            business_hours_start="09:00",
            business_hours_end="17:00"
        )
        
        rule = self.temporal_engine.create_temporal_rule(
            "temp_rule_002",
            "Temporal Validation Rule",
            "Test temporal validation",
            temporal_condition,
            [],
            [RuleAction(type=ActionType.VALIDATION, message="Test", severity=RuleSeverity.INFO)]
        )
        
        # Create MCP file with temporal rule
        mcp_file = MCPFile(
            mcp_id="temporal_test",
            name="Temporal Test MCP",
            description="Test temporal rules",
            jurisdiction=Jurisdiction(country="USA", state="Test"),
            version="1.0",
            effective_date="2024-01-01",
            rules=[rule]
        )
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump(mcp_file.to_dict(), f, indent=2)
            mcp_files = [f.name]
        
        try:
            # Test temporal validation
            result = self.temporal_engine.validate_building_model_temporal(
                self.building_model, mcp_files
            )
            
            assert 'temporal_results' in result
            assert 'total_rules' in result
            assert 'temporal_rules_executed' in result
            
        finally:
            # Clean up
            for file_path in mcp_files:
                try:
                    os.unlink(file_path)
                except:
                    pass


class TestMLRules:
    """Test suite for machine learning rules engine"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.ml_engine = MLRuleEngine()
        
        # Create test building model
        self.building_model = BuildingModel(
            building_id="ml_test_building",
            building_name="ML Test Building",
            objects=[
                BuildingObject(
                    object_id="obj_1",
                    object_type="electrical_outlet",
                    properties={"load": 15.0, "voltage": 120, "material": "copper"},
                    location={"x": 10, "y": 10, "width": 5, "height": 3}
                ),
                BuildingObject(
                    object_id="obj_2",
                    object_type="light_fixture",
                    properties={"load": 60.0, "voltage": 120, "material": "aluminum"},
                    location={"x": 20, "y": 20, "width": 8, "height": 4}
                )
            ]
        )
    
    def test_feature_definition(self):
        """Test feature definition"""
        features = [
            MLFeature(
                name="avg_load",
                feature_type="numeric",
                source="property",
                property_name="load",
                default_value=0.0
            ),
            MLFeature(
                name="material_type",
                feature_type="categorical",
                source="property",
                property_name="material",
                default_value="unknown"
            ),
            MLFeature(
                name="total_area",
                feature_type="numeric",
                source="calculated",
                calculation="area",
                default_value=0.0
            )
        ]
        
        self.ml_engine.define_features("ml_rule_001", features)
        
        # Test feature extraction
        extracted_features = self.ml_engine.extract_features(self.building_model, "ml_rule_001")
        
        assert "avg_load" in extracted_features
        assert "material_type" in extracted_features
        assert "total_area" in extracted_features
        assert extracted_features["avg_load"] == 37.5  # (15 + 60) / 2
        assert extracted_features["total_area"] == 47  # 5*3 + 8*4
    
    def test_model_training(self):
        """Test ML model training"""
        # Define features
        features = [
            MLFeature(name="avg_load", feature_type="numeric", source="property", property_name="load"),
            MLFeature(name="total_objects", feature_type="numeric", source="calculated", calculation="count")
        ]
        
        self.ml_engine.define_features("ml_rule_002", features)
        
        # Create training data
        training_data = [
            {"avg_load": 20.0, "total_objects": 5},
            {"avg_load": 30.0, "total_objects": 3},
            {"avg_load": 15.0, "total_objects": 2},
            {"avg_load": 40.0, "total_objects": 8},
            {"avg_load": 25.0, "total_objects": 4}
        ]
        
        target_values = [True, False, True, False, True]  # Binary classification
        
        # Train model
        self.ml_engine.train_model("ml_rule_002", training_data, target_values, "classifier")
        
        # Test prediction
        prediction = self.ml_engine.predict_compliance(self.building_model, "ml_rule_002")
        
        assert isinstance(prediction, MLPrediction)
        assert prediction.rule_id == "ml_rule_002"
        assert isinstance(prediction.prediction, bool)
        assert 0.0 <= prediction.confidence <= 1.0
        assert len(prediction.features_used) > 0
    
    def test_ml_rule_creation(self):
        """Test ML rule creation"""
        features = [
            MLFeature(name="avg_load", feature_type="numeric", source="property", property_name="load"),
            MLFeature(name="total_objects", feature_type="numeric", source="calculated", calculation="count")
        ]
        
        actions = [
            RuleAction(
                type=ActionType.VALIDATION,
                message="ML prediction indicates potential issue",
                severity=RuleSeverity.WARNING
            )
        ]
        
        rule = self.ml_engine.create_ml_rule(
            "ml_rule_003",
            "ML Test Rule",
            "Test ML rule",
            features,
            actions,
            "classifier"
        )
        
        assert rule.rule_id == "ml_rule_003"
        assert rule.category == RuleCategory.GENERAL
        assert len(rule.conditions) == 1  # ML condition
    
    def test_model_persistence(self):
        """Test model persistence"""
        # Define features and train model
        features = [
            MLFeature(name="avg_load", feature_type="numeric", source="property", property_name="load")
        ]
        
        self.ml_engine.define_features("ml_rule_004", features)
        
        training_data = [{"avg_load": 20.0}, {"avg_load": 30.0}, {"avg_load": 15.0}]
        target_values = [True, False, True]
        
        self.ml_engine.train_model("ml_rule_004", training_data, target_values, "classifier")
        
        # Clear models and reload
        self.ml_engine.models.clear()
        self.ml_engine.load_model("ml_rule_004", "classifier")
        
        # Test prediction after reload
        prediction = self.ml_engine.predict_compliance(self.building_model, "ml_rule_004")
        assert isinstance(prediction.prediction, bool)
    
    def test_model_performance_evaluation(self):
        """Test model performance evaluation"""
        # Define features and train model
        features = [
            MLFeature(name="avg_load", feature_type="numeric", source="property", property_name="load")
        ]
        
        self.ml_engine.define_features("ml_rule_005", features)
        
        training_data = [
            {"avg_load": 20.0}, {"avg_load": 30.0}, {"avg_load": 15.0},
            {"avg_load": 40.0}, {"avg_load": 25.0}, {"avg_load": 35.0}
        ]
        target_values = [True, False, True, False, True, False]
        
        self.ml_engine.train_model("ml_rule_005", training_data, target_values, "classifier")
        
        # Evaluate performance
        test_data = [{"avg_load": 22.0}, {"avg_load": 28.0}, {"avg_load": 18.0}]
        test_targets = [True, False, True]
        
        performance = self.ml_engine.evaluate_model_performance("ml_rule_005", test_data, test_targets)
        
        assert "accuracy" in performance
        assert "precision" in performance
        assert "recall" in performance
        assert "f1_score" in performance
        assert "predictions" in performance


class TestDynamicRules:
    """Test suite for dynamic rules engine"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.dynamic_engine = DynamicRuleEngine()
        
        # Create test building model
        self.building_model = BuildingModel(
            building_id="dynamic_test_building",
            building_name="Dynamic Test Building",
            objects=[
                BuildingObject(
                    object_id="obj_1",
                    object_type="electrical_outlet",
                    properties={"load": 15.0, "voltage": 120},
                    location={"x": 10, "y": 10, "width": 5, "height": 3}
                )
            ]
        )
        
        # Create test rule
        self.test_rule = MCPRule(
            rule_id="dynamic_rule_001",
            name="Dynamic Test Rule",
            description="Test dynamic rule",
            category=RuleCategory.GENERAL,
            conditions=[
                RuleCondition(
                    type=ConditionType.PROPERTY,
                    element_type="electrical_outlet",
                    property="load",
                    operator=">=",
                    value=10.0
                )
            ],
            actions=[
                RuleAction(
                    type=ActionType.VALIDATION,
                    message="Load threshold exceeded",
                    severity=RuleSeverity.WARNING
                )
            ]
        )
    
    def test_create_dynamic_rule(self):
        """Test creating dynamic rule"""
        rule_id = self.dynamic_engine.create_dynamic_rule(self.test_rule, "Test dynamic rule")
        
        assert rule_id == "dynamic_rule_001"
        assert rule_id in self.dynamic_engine.dynamic_rules
        
        dynamic_rule = self.dynamic_engine.dynamic_rules[rule_id]
        assert dynamic_rule.current_version == "v1.0"
        assert len(dynamic_rule.versions) == 1
    
    def test_modify_rule(self):
        """Test rule modification"""
        # Create dynamic rule
        rule_id = self.dynamic_engine.create_dynamic_rule(self.test_rule)
        
        # Modify rule
        modifications = {
            "name": "Modified Dynamic Rule",
            "description": "Modified description",
            "priority": 2
        }
        
        success = self.dynamic_engine.modify_rule(
            rule_id, modifications, "test_user", "Test modification"
        )
        
        assert success == True
        
        dynamic_rule = self.dynamic_engine.dynamic_rules[rule_id]
        assert dynamic_rule.current_version == "v2.0"
        assert dynamic_rule.base_rule.name == "Modified Dynamic Rule"
        assert dynamic_rule.base_rule.priority == 2
        assert len(dynamic_rule.versions) == 2
    
    def test_rollback_rule(self):
        """Test rule rollback"""
        # Create and modify rule
        rule_id = self.dynamic_engine.create_dynamic_rule(self.test_rule)
        
        modifications = {"name": "Modified Rule"}
        self.dynamic_engine.modify_rule(rule_id, modifications)
        
        # Rollback to original version
        success = self.dynamic_engine.rollback_rule(rule_id, "v1.0")
        
        assert success == True
        
        dynamic_rule = self.dynamic_engine.dynamic_rules[rule_id]
        assert dynamic_rule.current_version == "v1.0"
        assert dynamic_rule.base_rule.name == "Dynamic Test Rule"  # Original name
    
    def test_adaptive_conditions(self):
        """Test adaptive conditions"""
        # Create dynamic rule
        rule_id = self.dynamic_engine.create_dynamic_rule(self.test_rule)
        
        # Add adaptive condition
        adaptive_condition = {
            "type": "simple",
            "field": "building_size",
            "operator": ">",
            "value": 1000
        }
        
        success = self.dynamic_engine.add_adaptive_condition(rule_id, adaptive_condition)
        assert success == True
        
        # Test condition evaluation
        context = {"building_size": 1500}
        result = self.dynamic_engine.evaluate_adaptive_conditions(rule_id, context)
        assert result == True
        
        context = {"building_size": 500}
        result = self.dynamic_engine.evaluate_adaptive_conditions(rule_id, context)
        assert result == False
    
    def test_complex_adaptive_condition(self):
        """Test complex adaptive condition"""
        rule_id = self.dynamic_engine.create_dynamic_rule(self.test_rule)
        
        complex_condition = {
            "type": "complex",
            "expression": "building_size > 1000 and occupancy < 50"
        }
        
        self.dynamic_engine.add_adaptive_condition(rule_id, complex_condition)
        
        # Test evaluation
        context = {"building_size": 1500, "occupancy": 30}
        result = self.dynamic_engine.evaluate_adaptive_conditions(rule_id, context)
        assert result == True
        
        context = {"building_size": 800, "occupancy": 30}
        result = self.dynamic_engine.evaluate_adaptive_conditions(rule_id, context)
        assert result == False
    
    def test_time_based_adaptive_condition(self):
        """Test time-based adaptive condition"""
        rule_id = self.dynamic_engine.create_dynamic_rule(self.test_rule)
        
        time_condition = {
            "type": "time_based",
            "start_time": datetime.now() - timedelta(hours=1),
            "end_time": datetime.now() + timedelta(hours=1)
        }
        
        self.dynamic_engine.add_adaptive_condition(rule_id, time_condition)
        
        result = self.dynamic_engine.evaluate_adaptive_conditions(rule_id, {})
        assert result == True
    
    def test_dynamic_validation(self):
        """Test dynamic validation"""
        # Create dynamic rule
        rule_id = self.dynamic_engine.create_dynamic_rule(self.test_rule)
        
        # Create MCP file
        mcp_file = MCPFile(
            mcp_id="dynamic_test",
            name="Dynamic Test MCP",
            description="Test dynamic rules",
            jurisdiction=Jurisdiction(country="USA", state="Test"),
            version="1.0",
            effective_date="2024-01-01",
            rules=[self.test_rule]
        )
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump(mcp_file.to_dict(), f, indent=2)
            mcp_files = [f.name]
        
        try:
            # Test dynamic validation
            context = {"building_size": 1500, "occupancy": 30}
            result = self.dynamic_engine.validate_building_model_dynamic(
                self.building_model, mcp_files, context
            )
            
            assert 'dynamic_results' in result
            assert 'total_rules' in result
            assert 'dynamic_rules' in result
            assert 'adaptive_rules_executed' in result
            
        finally:
            # Clean up
            for file_path in mcp_files:
                try:
                    os.unlink(file_path)
                except:
                    pass
    
    def test_version_history(self):
        """Test version history tracking"""
        rule_id = self.dynamic_engine.create_dynamic_rule(self.test_rule)
        
        # Make several modifications
        for i in range(3):
            modifications = {"name": f"Modified Rule v{i+1}"}
            self.dynamic_engine.modify_rule(rule_id, modifications, f"user_{i}")
        
        # Get version history
        versions = self.dynamic_engine.get_rule_versions(rule_id)
        
        assert len(versions) == 4  # Initial + 3 modifications
        assert versions[0]['version_id'] == "v1.0"
        assert versions[-1]['version_id'] == "v4.0"
        assert versions[-1]['is_active'] == True
    
    def test_modification_history(self):
        """Test modification history tracking"""
        rule_id = self.dynamic_engine.create_dynamic_rule(self.test_rule)
        
        # Make modification
        modifications = {"name": "Modified Rule"}
        self.dynamic_engine.modify_rule(rule_id, modifications, "test_user", "Test modification")
        
        # Get modification history
        history = self.dynamic_engine.get_modification_history(rule_id)
        
        assert len(history) == 1
        assert history[0]['user'] == "test_user"
        assert history[0]['description'] == "Test modification"
        assert 'modifications' in history[0]


class TestAdvancedRulesIntegration:
    """Test suite for advanced rules integration"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temporal_engine = TemporalRuleEngine()
        self.ml_engine = MLRuleEngine()
        self.dynamic_engine = DynamicRuleEngine()
        
        self.building_model = BuildingModel(
            building_id="integration_test_building",
            building_name="Integration Test Building",
            objects=[
                BuildingObject(
                    object_id="obj_1",
                    object_type="electrical_outlet",
                    properties={"load": 15.0, "voltage": 120},
                    location={"x": 10, "y": 10, "width": 5, "height": 3}
                )
            ]
        )
    
    def test_advanced_rules_workflow(self):
        """Test complete advanced rules workflow"""
        # 1. Create temporal rule
        temporal_condition = TemporalCondition(
            operator=TemporalOperator.BUSINESS_HOURS,
            business_hours_start="09:00",
            business_hours_end="17:00"
        )
        
        temporal_rule = self.temporal_engine.create_temporal_rule(
            "adv_rule_001",
            "Advanced Temporal Rule",
            "Test advanced temporal rule",
            temporal_condition,
            [],
            [RuleAction(type=ActionType.VALIDATION, message="Temporal test", severity=RuleSeverity.INFO)]
        )
        
        # 2. Create ML rule
        features = [
            MLFeature(name="avg_load", feature_type="numeric", source="property", property_name="load")
        ]
        
        self.ml_engine.define_features("adv_rule_002", features)
        
        # Train ML model
        training_data = [{"avg_load": 20.0}, {"avg_load": 30.0}, {"avg_load": 15.0}]
        target_values = [True, False, True]
        self.ml_engine.train_model("adv_rule_002", training_data, target_values, "classifier")
        
        ml_rule = self.ml_engine.create_ml_rule(
            "adv_rule_002",
            "Advanced ML Rule",
            "Test advanced ML rule",
            features,
            [RuleAction(type=ActionType.VALIDATION, message="ML test", severity=RuleSeverity.WARNING)]
        )
        
        # 3. Create dynamic rule
        base_rule = MCPRule(
            rule_id="adv_rule_003",
            name="Advanced Dynamic Rule",
            description="Test advanced dynamic rule",
            category=RuleCategory.GENERAL,
            conditions=[],
            actions=[RuleAction(type=ActionType.VALIDATION, message="Dynamic test", severity=RuleSeverity.ERROR)]
        )
        
        self.dynamic_engine.create_dynamic_rule(base_rule)
        
        # 4. Test all engines
        # Temporal validation
        temporal_result = self.temporal_engine.evaluate_temporal_condition(temporal_condition)
        assert isinstance(temporal_result, bool)
        
        # ML prediction
        ml_prediction = self.ml_engine.predict_compliance(self.building_model, "adv_rule_002")
        assert isinstance(ml_prediction, MLPrediction)
        
        # Dynamic rule modification
        success = self.dynamic_engine.modify_rule(
            "adv_rule_003", {"name": "Modified Advanced Dynamic Rule"}
        )
        assert success == True
        
        # Verify all engines work together
        assert temporal_result is not None
        assert ml_prediction.confidence >= 0.0
        assert ml_prediction.confidence <= 1.0
        assert success == True 