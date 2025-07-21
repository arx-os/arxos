"""
Unit tests for enhanced rule engine with external file loading and management utilities
"""

import unittest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch

from core.services.rule_engine


class TestRuleDefinition(unittest.TestCase):
    """Test RuleDefinition class"""
    
    def test_initialization(self):
        """Test RuleDefinition initialization"""
        rule = RuleDefinition(
            rule_name="test_rule",
            rule_type="structural",
            description="Test rule",
            severity="error",
            priority=5
        )
        
        self.assertEqual(rule.rule_name, "test_rule")
        self.assertEqual(rule.rule_type, "structural")
        self.assertEqual(rule.version, "1.0")
        self.assertEqual(rule.description, "Test rule")
        self.assertEqual(rule.severity, "error")
        self.assertEqual(rule.priority, 5)
        self.assertEqual(rule.conditions, [])
        self.assertEqual(rule.actions, [])
        self.assertTrue(rule.enabled)
    
    def test_to_validation_rule(self):
        """Test conversion to ValidationRule"""
        rule = RuleDefinition(
            rule_name="test_rule",
            rule_type="structural",
            conditions=[{"field": "test", "operator": ">=", "value": 10}]
        )
        
        validation_rule = rule.to_validation_rule(regulation_id=1)
        
        self.assertEqual(validation_rule.regulation_id, 1)
        self.assertEqual(validation_rule.rule_name, "test_rule")
        self.assertEqual(validation_rule.rule_type, "structural")
        self.assertEqual(validation_rule.severity, "error")
        self.assertEqual(validation_rule.priority, 1)
        self.assertTrue(validation_rule.active)


class TestEnhancedRuleEngine(unittest.TestCase):
    """Test EnhancedRuleEngine class"""
    
    def setUp(self):
        self.rule_engine = EnhancedRuleEngine()
    
    def test_load_rules_from_json_file(self):
        """Test loading rules from JSON file"""
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([
                {
                    "rule_name": "test_rule_1",
                    "rule_type": "structural",
                    "description": "Test rule 1",
                    "conditions": [
                        {
                            "field": "structural.loads.live_load",
                            "operator": ">=",
                            "value": 50
                        }
                    ]
                },
                {
                    "rule_name": "test_rule_2",
                    "rule_type": "fire_safety",
                    "description": "Test rule 2",
                    "conditions": [
                        {
                            "field": "fire_safety.egress.exit_width",
                            "operator": ">=",
                            "value": 36
                        }
                    ]
                }
            ], f)
            temp_file = f.name
        
        try:
            rules = self.rule_engine.load_rules_from_file(temp_file)
            
            self.assertEqual(len(rules), 2)
            self.assertEqual(rules[0].rule_name, "test_rule_1")
            self.assertEqual(rules[0].rule_type, "structural")
            self.assertEqual(rules[1].rule_name, "test_rule_2")
            self.assertEqual(rules[1].rule_type, "fire_safety")
            
            # Check that rules are stored in loaded_rules
            self.assertIn("test_rule_1", self.rule_engine.loaded_rules)
            self.assertIn("test_rule_2", self.rule_engine.loaded_rules)
            
        finally:
            os.unlink(temp_file)
    
    def test_load_rules_from_directory(self):
        """Test loading rules from directory"""
        # Create temporary directory with rule files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create first rule file
            rule_file_1 = os.path.join(temp_dir, "structural_rules.json")
            with open(rule_file_1, 'w') as f:
                json.dump([
                    {
                        "rule_name": "structural_rule",
                        "rule_type": "structural",
                        "conditions": [
                            {
                                "field": "structural.loads.live_load",
                                "operator": ">=",
                                "value": 50
                            }
                        ]
                    }
                ], f)
            
            # Create second rule file
            rule_file_2 = os.path.join(temp_dir, "fire_rules.json")
            with open(rule_file_2, 'w') as f:
                json.dump([
                    {
                        "rule_name": "fire_rule",
                        "rule_type": "fire_safety",
                        "conditions": [
                            {
                                "field": "fire_safety.egress.exit_width",
                                "operator": ">=",
                                "value": 36
                            }
                        ]
                    }
                ], f)
            
            # Create non-rule file (should be ignored)
            non_rule_file = os.path.join(temp_dir, "readme.txt")
            with open(non_rule_file, 'w') as f:
                f.write("This is not a rule file")
            
            rules = self.rule_engine.load_rules_from_directory(temp_dir, "*.json")
            
            self.assertEqual(len(rules), 2)
            rule_names = [rule.rule_name for rule in rules]
            self.assertIn("structural_rule", rule_names)
            self.assertIn("fire_rule", rule_names)
    
    def test_list_rules(self):
        """Test listing rules"""
        # Load some test rules
        rule1 = RuleDefinition("rule1", "structural", priority=5)
        rule2 = RuleDefinition("rule2", "fire_safety", priority=10)
        rule3 = RuleDefinition("rule3", "structural", priority=3, enabled=False)
        
        self.rule_engine.loaded_rules = {
            "rule1": rule1,
            "rule2": rule2,
            "rule3": rule3
        }
        
        # Test listing all rules
        all_rules = self.rule_engine.list_rules()
        self.assertEqual(len(all_rules), 2)  # Only enabled rules
        
        # Test listing by type
        structural_rules = self.rule_engine.list_rules(rule_type="structural")
        self.assertEqual(len(structural_rules), 1)
        self.assertEqual(structural_rules[0]['rule_name'], "rule1")
        
        # Test listing all rules including disabled
        all_rules_including_disabled = self.rule_engine.list_rules(enabled_only=False)
        self.assertEqual(len(all_rules_including_disabled), 3)
        
        # Test sorting by priority
        self.assertEqual(all_rules_including_disabled[0]['rule_name'], "rule2")  # Priority 10
        self.assertEqual(all_rules_including_disabled[1]['rule_name'], "rule1")  # Priority 5
        self.assertEqual(all_rules_including_disabled[2]['rule_name'], "rule3")  # Priority 3
    
    def test_get_rule(self):
        """Test getting a specific rule"""
        rule = RuleDefinition("test_rule", "structural")
        self.rule_engine.loaded_rules["test_rule"] = rule
        
        retrieved_rule = self.rule_engine.get_rule("test_rule")
        self.assertEqual(retrieved_rule, rule)
        
        # Test non-existent rule
        non_existent = self.rule_engine.get_rule("non_existent")
        self.assertIsNone(non_existent)
    
    def test_enable_disable_rule(self):
        """Test enabling and disabling rules"""
        rule = RuleDefinition("test_rule", "structural", enabled=False)
        self.rule_engine.loaded_rules["test_rule"] = rule
        
        # Test enabling
        result = self.rule_engine.enable_rule("test_rule")
        self.assertTrue(result)
        self.assertTrue(rule.enabled)
        
        # Test disabling
        result = self.rule_engine.disable_rule("test_rule")
        self.assertTrue(result)
        self.assertFalse(rule.enabled)
        
        # Test non-existent rule
        result = self.rule_engine.enable_rule("non_existent")
        self.assertFalse(result)
    
    def test_validate_rule_definition(self):
        """Test rule definition validation"""
        # Valid rule
        valid_rule = {
            "rule_name": "test_rule",
            "rule_type": "structural",
            "conditions": [
                {
                    "field": "test.field",
                    "operator": ">=",
                    "value": 10
                }
            ]
        }
        
        errors = self.rule_engine.validate_rule_definition(valid_rule)
        self.assertEqual(len(errors), 0)
        
        # Invalid rule - missing required fields
        invalid_rule = {
            "rule_name": "test_rule"
            # Missing rule_type and conditions
        }
        
        errors = self.rule_engine.validate_rule_definition(invalid_rule)
        self.assertGreater(len(errors), 0)
        self.assertIn("Missing required field: rule_type", errors)
        self.assertIn("Missing required field: conditions", errors)
        
        # Invalid rule - invalid rule type
        invalid_type_rule = {
            "rule_name": "test_rule",
            "rule_type": "invalid_type",
            "conditions": []
        }
        
        errors = self.rule_engine.validate_rule_definition(invalid_type_rule)
        self.assertGreater(len(errors), 0)
        self.assertIn("Invalid rule_type", errors[0])
        
        # Invalid rule - invalid severity
        invalid_severity_rule = {
            "rule_name": "test_rule",
            "rule_type": "structural",
            "severity": "invalid_severity",
            "conditions": []
        }
        
        errors = self.rule_engine.validate_rule_definition(invalid_severity_rule)
        self.assertGreater(len(errors), 0)
        self.assertIn("Invalid severity", errors[0])
        
        # Invalid rule - invalid condition
        invalid_condition_rule = {
            "rule_name": "test_rule",
            "rule_type": "structural",
            "conditions": [
                {
                    "field": "test.field",
                    "operator": "invalid_operator",
                    "value": 10
                }
            ]
        }
        
        errors = self.rule_engine.validate_rule_definition(invalid_condition_rule)
        self.assertGreater(len(errors), 0)
        self.assertIn("Invalid operator", errors[0])
    
    def test_test_rule(self):
        """Test rule testing functionality"""
        rule = RuleDefinition(
            "test_rule",
            "structural",
            conditions=[
                {
                    "field": "structural.loads.live_load",
                    "operator": ">=",
                    "value": 50,
                    "message": "Live load must be at least 50 psf"
                }
            ]
        )
        
        # Test with passing data
        passing_data = {
            "structural": {
                "loads": {
                    "live_load": 60
                }
            }
        }
        
        result = self.rule_engine.test_rule(rule, passing_data)
        self.assertTrue(result['passed'])
        self.assertEqual(result['rule_name'], "test_rule")
        self.assertIn('condition_results', result)
        self.assertTrue(result['condition_results'][0]['passed'])
        
        # Test with failing data
        failing_data = {
            "structural": {
                "loads": {
                    "live_load": 40
                }
            }
        }
        
        result = self.rule_engine.test_rule(rule, failing_data)
        self.assertFalse(result['passed'])
        self.assertIn('condition_results', result)
        self.assertFalse(result['condition_results'][0]['passed'])
        self.assertEqual(result['condition_results'][0]['actual_value'], 40)
        self.assertEqual(result['condition_results'][0]['expected_value'], 50)
    
    def test_execute_rule_with_rule_definition(self):
        """Test executing a rule using RuleDefinition"""
        rule = RuleDefinition(
            "test_rule",
            "structural",
            conditions=[
                {
                    "field": "structural.loads.live_load",
                    "operator": ">=",
                    "value": 50
                }
            ]
        )
        
        # Test with passing data
        passing_data = {
            "structural": {
                "loads": {
                    "live_load": 60
                }
            }
        }
        
        is_valid, message = self.rule_engine.execute_rule(rule, passing_data)
        self.assertTrue(is_valid)
        self.assertIsNone(message)
        
        # Test with failing data
        failing_data = {
            "structural": {
                "loads": {
                    "live_load": 40
                }
            }
        }
        
        is_valid, message = self.rule_engine.execute_rule(rule, failing_data)
        self.assertFalse(is_valid)
        self.assertIsNotNone(message)
    
    def test_parse_rule_definition(self):
        """Test parsing rule definition from dictionary"""
        rule_data = {
            "rule_name": "test_rule",
            "rule_type": "structural",
            "version": "2.0",
            "description": "Test rule description",
            "severity": "warning",
            "priority": 5,
            "conditions": [
                {
                    "field": "test.field",
                    "operator": ">=",
                    "value": 10
                }
            ],
            "actions": [
                {
                    "type": "recommend",
                    "message": "Test recommendation"
                }
            ],
            "enabled": False
        }
        
        rule = self.rule_engine._parse_rule_definition(rule_data)
        
        self.assertEqual(rule.rule_name, "test_rule")
        self.assertEqual(rule.rule_type, "structural")
        self.assertEqual(rule.version, "2.0")
        self.assertEqual(rule.description, "Test rule description")
        self.assertEqual(rule.severity, "warning")
        self.assertEqual(rule.priority, 5)
        self.assertEqual(len(rule.conditions), 1)
        self.assertEqual(len(rule.actions), 1)
        self.assertFalse(rule.enabled)
    
    def test_parse_rule_definition_missing_fields(self):
        """Test parsing rule definition with missing required fields"""
        rule_data = {
            "rule_name": "test_rule"
            # Missing rule_type and conditions
        }
        
        with self.assertRaises(ValueError) as context:
            self.rule_engine._parse_rule_definition(rule_data)
        
        self.assertIn("Missing required field", str(context.exception))


class TestRuleEngineIntegration(unittest.TestCase):
    """Integration tests for rule engine"""
    
    def setUp(self):
        self.rule_engine = EnhancedRuleEngine()
    
    def test_end_to_end_rule_workflow(self):
        """Test complete rule workflow from loading to execution"""
        # Create a temporary rule file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([
                {
                    "rule_name": "min_live_load",
                    "rule_type": "structural",
                    "description": "Minimum live load for office floors",
                    "severity": "error",
                    "priority": 10,
                    "conditions": [
                        {
                            "field": "structural.loads.live_load",
                            "operator": ">=",
                            "value": 50,
                            "message": "Live load must be at least 50 psf"
                        }
                    ],
                    "actions": [
                        {
                            "type": "recommend",
                            "message": "Increase live load capacity"
                        }
                    ],
                    "enabled": True
                }
            ], f)
            temp_file = f.name
        
        try:
            # Load rules
            rules = self.rule_engine.load_rules_from_file(temp_file)
            self.assertEqual(len(rules), 1)
            
            # List rules
            rule_list = self.rule_engine.list_rules()
            self.assertEqual(len(rule_list), 1)
            self.assertEqual(rule_list[0]['rule_name'], "min_live_load")
            
            # Get specific rule
            rule = self.rule_engine.get_rule("min_live_load")
            self.assertIsNotNone(rule)
            self.assertEqual(rule.rule_name, "min_live_load")
            
            # Test rule with passing data
            passing_data = {
                "structural": {
                    "loads": {
                        "live_load": 60
                    }
                }
            }
            
            test_result = self.rule_engine.test_rule(rule, passing_data)
            self.assertTrue(test_result['passed'])
            
            # Test rule with failing data
            failing_data = {
                "structural": {
                    "loads": {
                        "live_load": 40
                    }
                }
            }
            
            test_result = self.rule_engine.test_rule(rule, failing_data)
            self.assertFalse(test_result['passed'])
            
            # Execute rule
            is_valid, message = self.rule_engine.execute_rule(rule, passing_data)
            self.assertTrue(is_valid)
            
            is_valid, message = self.rule_engine.execute_rule(rule, failing_data)
            self.assertFalse(is_valid)
            self.assertIsNotNone(message)
            
            # Disable and enable rule
            self.rule_engine.disable_rule("min_live_load")
            self.assertFalse(rule.enabled)
            
            self.rule_engine.enable_rule("min_live_load")
            self.assertTrue(rule.enabled)
            
        finally:
            os.unlink(temp_file)


if __name__ == '__main__':
    unittest.main() 