"""
Unit tests for building code validation engine
"""

import unittest
import tempfile
import os
import json
from datetime import datetime, date
from unittest.mock import Mock, patch

from ..services.building_code_validator import (
    BuildingCodeValidator, RuleEngine, ValidationResult, ValidationStatus, ViolationSeverity
)
from ..models.building_regulations import (
    Regulation, ValidationRule, ValidationViolation, RegulationType
)


class TestValidationResult(unittest.TestCase):
    """Test ValidationResult class"""
    
    def setUp(self):
        self.result = ValidationResult(1, ValidationStatus.PENDING)
    
    def test_initialization(self):
        """Test ValidationResult initialization"""
        self.assertEqual(self.result.regulation_id, 1)
        self.assertEqual(self.result.status, ValidationStatus.PENDING)
        self.assertEqual(self.result.score, 0.0)
        self.assertEqual(len(self.result.violations), 0)
        self.assertEqual(len(self.result.warnings), 0)
        self.assertEqual(self.result.passed_rules, 0)
        self.assertEqual(self.result.failed_rules, 0)
        self.assertEqual(self.result.total_rules, 0)
    
    def test_add_violation_error(self):
        """Test adding error violation"""
        violation = ValidationViolation(
            rule_id=1,
            violation_type="structural",
            severity=ViolationSeverity.ERROR,
            description="Test error"
        )
        
        self.result.add_violation(violation)
        
        self.assertEqual(len(self.result.violations), 1)
        self.assertEqual(len(self.result.warnings), 0)
        self.assertEqual(self.result.failed_rules, 1)
        self.assertEqual(self.result.total_rules, 1)
    
    def test_add_violation_warning(self):
        """Test adding warning violation"""
        violation = ValidationViolation(
            rule_id=1,
            violation_type="structural",
            severity=ViolationSeverity.WARNING,
            description="Test warning"
        )
        
        self.result.add_violation(violation)
        
        self.assertEqual(len(self.result.violations), 0)
        self.assertEqual(len(self.result.warnings), 1)
        self.assertEqual(self.result.failed_rules, 0)
        self.assertEqual(self.result.total_rules, 1)
    
    def test_add_passed_rule(self):
        """Test adding passed rule"""
        self.result.add_passed_rule()
        
        self.assertEqual(self.result.passed_rules, 1)
        self.assertEqual(self.result.total_rules, 1)
        self.assertEqual(self.result.failed_rules, 0)
    
    def test_calculate_score_passed(self):
        """Test score calculation for passed validation"""
        self.result.add_passed_rule()
        self.result.add_passed_rule()
        self.result.add_passed_rule()
        
        self.result.calculate_score()
        
        self.assertEqual(self.result.score, 100.0)
        self.assertEqual(self.result.status, ValidationStatus.PASSED)
    
    def test_calculate_score_partial(self):
        """Test score calculation for partial validation"""
        self.result.add_passed_rule()
        self.result.add_passed_rule()

        violation = ValidationViolation(
            rule_id=1,
            violation_type="structural",
            severity=ViolationSeverity.ERROR,
            description="Test error"
        )
        self.result.add_violation(violation)
        self.result.calculate_score()

        self.assertAlmostEqual(self.result.score, 66.67, places=2)
        self.assertEqual(self.result.status, ValidationStatus.PARTIAL)
    
    def test_calculate_score_failed(self):
        """Test score calculation for failed validation"""
        violation1 = ValidationViolation(
            rule_id=1,
            violation_type="structural",
            severity=ViolationSeverity.ERROR,
            description="Test error 1"
        )
        violation2 = ValidationViolation(
            rule_id=2,
            violation_type="structural",
            severity=ViolationSeverity.ERROR,
            description="Test error 2"
        )
        
        self.result.add_violation(violation1)
        self.result.add_violation(violation2)
        
        self.result.calculate_score()
        
        self.assertEqual(self.result.score, 0.0)
        self.assertEqual(self.result.status, ValidationStatus.FAILED)
    
    def test_calculate_score_empty(self):
        """Test score calculation with no rules"""
        self.result.calculate_score()
        
        self.assertEqual(self.result.score, 100.0)
        self.assertEqual(self.result.status, ValidationStatus.PASSED)
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        self.result.add_passed_rule()
        
        violation = ValidationViolation(
            rule_id=1,
            violation_type="structural",
            severity=ViolationSeverity.ERROR,
            description="Test error"
        )
        self.result.add_violation(violation)
        
        self.result.calculate_score()
        
        result_dict = self.result.to_dict()
        
        self.assertEqual(result_dict['regulation_id'], 1)
        self.assertEqual(result_dict['status'], 'partial')
        self.assertEqual(result_dict['score'], 50.0)
        self.assertEqual(result_dict['total_rules'], 2)
        self.assertEqual(result_dict['passed_rules'], 1)
        self.assertEqual(result_dict['failed_rules'], 1)
        self.assertEqual(result_dict['warnings'], 0)
        self.assertEqual(len(result_dict['violations']), 1)
        self.assertEqual(len(result_dict['warnings_list']), 0)


class TestRuleEngine(unittest.TestCase):
    """Test RuleEngine class"""
    
    def setUp(self):
        self.rule_engine = RuleEngine()
    
    def test_validate_structural_load_requirements(self):
        """Test structural load validation"""
        rule_logic = {
            'load_requirements': {
                'dead_load': 100,
                'live_load': 50
            }
        }
        
        building_data = {
            'structural': {
                'loads': {
                    'dead_load': 120,
                    'live_load': 60
                }
            }
        }
        
        is_valid, message = self.rule_engine._validate_structural(rule_logic, building_data)
        
        self.assertTrue(is_valid)
        self.assertIsNone(message)
    
    def test_validate_structural_load_insufficient(self):
        """Test structural load validation with insufficient capacity"""
        rule_logic = {
            'load_requirements': {
                'dead_load': 100,
                'live_load': 50
            }
        }
        
        building_data = {
            'structural': {
                'loads': {
                    'dead_load': 80,
                    'live_load': 60
                }
            }
        }
        
        is_valid, message = self.rule_engine._validate_structural(rule_logic, building_data)
        
        self.assertFalse(is_valid)
        self.assertIn("Insufficient dead_load load capacity", message)
    
    def test_validate_fire_safety_resistance(self):
        """Test fire safety resistance validation"""
        rule_logic = {
            'fire_resistance': {
                'walls': 2,
                'doors': 1
            }
        }
        
        building_data = {
            'fire_safety': {
                'fire_ratings': {
                    'walls': 3,
                    'doors': 2
                }
            }
        }
        
        is_valid, message = self.rule_engine._validate_fire_safety(rule_logic, building_data)
        
        self.assertTrue(is_valid)
        self.assertIsNone(message)
    
    def test_validate_fire_safety_egress(self):
        """Test fire safety egress validation"""
        rule_logic = {
            'egress': {
                'exit_width': 36,
                'exit_distance': 200
            }
        }
        
        building_data = {
            'fire_safety': {
                'egress': {
                    'exit_width': 42,
                    'exit_distance': 150
                }
            }
        }
        
        is_valid, message = self.rule_engine._validate_fire_safety(rule_logic, building_data)
        
        self.assertTrue(is_valid)
        self.assertIsNone(message)
    
    def test_validate_accessibility_clear_width(self):
        """Test accessibility clear width validation"""
        rule_logic = {
            'clear_width': 36
        }
        
        building_data = {
            'accessibility': {
                'clear_width': 42
            }
        }
        
        is_valid, message = self.rule_engine._validate_accessibility(rule_logic, building_data)
        
        self.assertTrue(is_valid)
        self.assertIsNone(message)
    
    def test_validate_accessibility_ramp(self):
        """Test accessibility ramp validation"""
        rule_logic = {
            'ramp': {
                'max_slope': 8.33,
                'handrails': True
            }
        }
        
        building_data = {
            'accessibility': {
                'ramp': {
                    'slope': 7.0,
                    'handrails': True
                }
            }
        }
        
        is_valid, message = self.rule_engine._validate_accessibility(rule_logic, building_data)
        
        self.assertTrue(is_valid)
        self.assertIsNone(message)
    
    def test_validate_energy_insulation(self):
        """Test energy insulation validation"""
        rule_logic = {
            'insulation': {
                'walls': 20,
                'roof': 30
            }
        }
        
        building_data = {
            'energy': {
                'insulation': {
                    'walls': 25,
                    'roof': 35
                }
            }
        }
        
        is_valid, message = self.rule_engine._validate_energy(rule_logic, building_data)
        
        self.assertTrue(is_valid)
        self.assertIsNone(message)
    
    def test_validate_energy_windows(self):
        """Test energy window validation"""
        rule_logic = {
            'windows': {
                'max_u_factor': 0.35,
                'max_shgc': 0.25
            }
        }
        
        building_data = {
            'energy': {
                'windows': {
                    'u_factor': 0.30,
                    'shgc': 0.20
                }
            }
        }
        
        is_valid, message = self.rule_engine._validate_energy(rule_logic, building_data)
        
        self.assertTrue(is_valid)
        self.assertIsNone(message)
    
    def test_validate_mechanical_hvac(self):
        """Test mechanical HVAC validation"""
        rule_logic = {
            'hvac': {
                'ventilation_rate': 15,
                'equipment_efficiency': {
                    'chiller': 0.85
                }
            }
        }
        
        building_data = {
            'mechanical': {
                'hvac': {
                    'ventilation_rate': 20,
                    'equipment': {
                        'chiller': {
                            'efficiency': 0.90
                        }
                    }
                }
            }
        }
        
        is_valid, message = self.rule_engine._validate_mechanical(rule_logic, building_data)
        
        self.assertTrue(is_valid)
        self.assertIsNone(message)
    
    def test_validate_electrical_loads(self):
        """Test electrical load validation"""
        rule_logic = {
            'load_calculations': {
                'lighting': 100,
                'receptacles': 200
            }
        }
        
        building_data = {
            'electrical': {
                'loads': {
                    'lighting': 120,
                    'receptacles': 250
                }
            }
        }
        
        is_valid, message = self.rule_engine._validate_electrical(rule_logic, building_data)
        
        self.assertTrue(is_valid)
        self.assertIsNone(message)
    
    def test_validate_plumbing_fixtures(self):
        """Test plumbing fixture validation"""
        rule_logic = {
            'fixtures': {
                'faucets': {
                    'max_flow_rate': 2.2
                }
            }
        }
        
        building_data = {
            'plumbing': {
                'fixtures': {
                    'faucets': {
                        'flow_rate': 2.0
                    }
                }
            }
        }
        
        is_valid, message = self.rule_engine._validate_plumbing(rule_logic, building_data)
        
        self.assertTrue(is_valid)
        self.assertIsNone(message)
    
    def test_validate_environmental_materials(self):
        """Test environmental material validation"""
        rule_logic = {
            'sustainable_materials': {
                'steel': {
                    'min_recycled_content': 25
                }
            }
        }
        
        building_data = {
            'environmental': {
                'materials': {
                    'steel': {
                        'recycled_content': 30
                    }
                }
            }
        }
        
        is_valid, message = self.rule_engine._validate_environmental(rule_logic, building_data)
        
        self.assertTrue(is_valid)
        self.assertIsNone(message)
    
    def test_validate_general_conditions(self):
        """Test general condition validation"""
        rule_logic = {
            'conditions': [
                {
                    'field': 'building_type',
                    'operator': '==',
                    'value': 'commercial'
                }
            ]
        }
        
        building_data = {
            'building_type': 'commercial'
        }
        
        is_valid, message = self.rule_engine._validate_general(rule_logic, building_data)
        
        self.assertTrue(is_valid)
        self.assertIsNone(message)
    
    def test_get_nested_value(self):
        """Test nested value retrieval"""
        data = {
            'structural': {
                'loads': {
                    'dead_load': 100
                }
            }
        }
        
        value = self.rule_engine._get_nested_value(data, 'structural.loads.dead_load')
        self.assertEqual(value, 100)
        
        value = self.rule_engine._get_nested_value(data, 'structural.loads.live_load')
        self.assertIsNone(value)
    
    def test_apply_operator(self):
        """Test operator application"""
        # Test equality
        self.assertTrue(self.rule_engine._apply_operator(5, '==', 5))
        self.assertFalse(self.rule_engine._apply_operator(5, '==', 6))
        
        # Test inequality
        self.assertTrue(self.rule_engine._apply_operator(5, '!=', 6))
        self.assertFalse(self.rule_engine._apply_operator(5, '!=', 5))
        
        # Test greater than
        self.assertTrue(self.rule_engine._apply_operator(10, '>', 5))
        self.assertFalse(self.rule_engine._apply_operator(5, '>', 10))
        
        # Test less than
        self.assertTrue(self.rule_engine._apply_operator(5, '<', 10))
        self.assertFalse(self.rule_engine._apply_operator(10, '<', 5))
        
        # Test in operator
        self.assertTrue(self.rule_engine._apply_operator('a', 'in', ['a', 'b', 'c']))
        self.assertFalse(self.rule_engine._apply_operator('d', 'in', ['a', 'b', 'c']))
        
        # Test invalid operator
        self.assertFalse(self.rule_engine._apply_operator(5, 'invalid', 5))
        
        # Test None value
        self.assertFalse(self.rule_engine._apply_operator(None, '==', 5))


class TestBuildingCodeValidator(unittest.TestCase):
    """Test BuildingCodeValidator class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize validator with temporary database
        self.validator = BuildingCodeValidator(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test environment"""
        self.validator.close()
        os.unlink(self.temp_db.name)
    
    def test_initialization(self):
        """Test validator initialization"""
        self.assertIsNotNone(self.validator.db)
        self.assertIsNotNone(self.validator.rule_engine)
    
    def test_validate_design_no_regulations(self):
        """Test validation with no applicable regulations"""
        building_design = {
            'building_type': 'residential',
            'structural': {
                'loads': {
                    'dead_load': 100,
                    'live_load': 50
                }
            }
        }
        
        # Mock empty regulations
        with patch.object(self.validator.db, 'get_regulations', return_value=[]):
            results = self.validator.validate_design(building_design)
            self.assertEqual(len(results), 0)
    
    def test_validate_design_with_regulations(self):
        """Test validation with regulations"""
        building_design = {
            'building_type': 'commercial',
            'structural': {
                'loads': {
                    'dead_load': 100,
                    'live_load': 50
                }
            },
            'fire_safety': {
                'fire_ratings': {
                    'walls': 3,
                    'doors': 2
                },
                'egress': {
                    'exit_width': 42,
                    'exit_distance': 150
                }
            },
            'accessibility': {
                'clear_width': 42,
                'ramp': {
                    'slope': 7.0,
                    'handrails': True
                }
            }
        }
        
        # Get actual regulations from database
        regulations = self.validator.db.get_regulations()
        
        if regulations:
            results = self.validator.validate_design(building_design)
            self.assertIsInstance(results, list)
            
            for result in results:
                self.assertIsInstance(result, ValidationResult)
                self.assertIn(result.status, [ValidationStatus.PASSED, ValidationStatus.PARTIAL, ValidationStatus.FAILED])
                self.assertGreaterEqual(result.score, 0.0)
                self.assertLessEqual(result.score, 100.0)
    
    def test_validate_specific_regulation(self):
        """Test validation against specific regulation"""
        building_design = {
            'structural': {
                'loads': {
                    'dead_load': 100,
                    'live_load': 50
                }
            }
        }
        
        # Get a regulation from database
        regulations = self.validator.db.get_regulations()
        
        if regulations:
            regulation = regulations[0]
            result = self.validator.validate_specific_regulation(building_design, regulation.code)
            
            if result:
                self.assertIsInstance(result, ValidationResult)
                self.assertEqual(result.regulation_id, regulation.id)
    
    def test_validate_specific_regulation_not_found(self):
        """Test validation with non-existent regulation"""
        building_design = {
            'structural': {
                'loads': {
                    'dead_load': 100,
                    'live_load': 50
                }
            }
        }
        
        result = self.validator.validate_specific_regulation(building_design, "NON_EXISTENT_CODE")
        self.assertIsNone(result)
    
    def test_get_compliance_report(self):
        """Test compliance report generation"""
        building_id = "test_building_001"
        
        # Create mock validation results
        result1 = ValidationResult(1, ValidationStatus.PASSED)
        result1.add_passed_rule()
        result1.add_passed_rule()
        result1.calculate_score()
        
        result2 = ValidationResult(2, ValidationStatus.FAILED)
        violation = ValidationViolation(
            rule_id=1,
            violation_type="structural",
            severity=ViolationSeverity.ERROR,
            description="Test violation"
        )
        result2.add_violation(violation)
        result2.calculate_score()
        
        validation_results = [result1, result2]
        
        report = self.validator.get_compliance_report(building_id, validation_results)
        
        self.assertEqual(report['building_id'], building_id)
        self.assertEqual(report['overall_status'], 'failed')
        self.assertEqual(report['total_regulations'], 2)
        self.assertEqual(report['passed_regulations'], 1)
        self.assertEqual(report['failed_regulations'], 1)
        self.assertEqual(report['total_violations'], 1)
        self.assertIn('regulation_details', report)
        self.assertEqual(len(report['regulation_details']), 2)
    
    def test_get_applicable_regulations_all(self):
        """Test getting all applicable regulations"""
        regulations = self.validator._get_applicable_regulations()
        self.assertIsInstance(regulations, list)
        
        for regulation in regulations:
            self.assertIsInstance(regulation, Regulation)
    
    def test_get_applicable_regulations_filtered(self):
        """Test getting filtered regulations"""
        regulations = self.validator._get_applicable_regulations(['structural'])
        self.assertIsInstance(regulations, list)
        
        for regulation in regulations:
            self.assertEqual(regulation.regulation_type, 'structural')


class TestIntegration(unittest.TestCase):
    """Integration tests for building code validation"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.validator = BuildingCodeValidator(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test environment"""
        self.validator.close()
        os.unlink(self.temp_db.name)
    
    def test_end_to_end_validation(self):
        """Test end-to-end validation workflow"""
        # Create comprehensive building design
        building_design = {
            'building_type': 'commercial',
            'occupancy': 'office',
            'floors': 5,
            'structural': {
                'loads': {
                    'dead_load': 120,
                    'live_load': 60,
                    'snow_load': 30
                },
                'materials': {
                    'concrete': {
                        'strength': 4000,
                        'density': 150
                    },
                    'steel': {
                        'yield_strength': 50000,
                        'elastic_modulus': 29000
                    }
                }
            },
            'fire_safety': {
                'fire_ratings': {
                    'walls': 3,
                    'doors': 2,
                    'floors': 2
                },
                'egress': {
                    'exit_width': 42,
                    'exit_distance': 150,
                    'exit_count': 4
                },
                'sprinklers': True,
                'smoke_detectors': True
            },
            'accessibility': {
                'clear_width': 42,
                'ramp': {
                    'slope': 7.0,
                    'handrails': True,
                    'landings': True
                },
                'doors': {
                    'entrance': {
                        'width': 36,
                        'threshold': 0.5
                    },
                    'interior': {
                        'width': 32,
                        'threshold': 0.25
                    }
                },
                'elevators': True,
                'accessible_bathrooms': True
            },
            'energy': {
                'insulation': {
                    'walls': 25,
                    'roof': 35,
                    'floors': 20
                },
                'windows': {
                    'u_factor': 0.30,
                    'shgc': 0.20,
                    'vt': 0.50
                },
                'hvac_efficiency': {
                    'heating': 0.90,
                    'cooling': 0.85
                }
            },
            'mechanical': {
                'hvac': {
                    'ventilation_rate': 20,
                    'equipment': {
                        'chiller': {
                            'efficiency': 0.90,
                            'capacity': 100
                        },
                        'boiler': {
                            'efficiency': 0.85,
                            'capacity': 80
                        }
                    }
                }
            },
            'electrical': {
                'loads': {
                    'lighting': 120,
                    'receptacles': 250,
                    'hvac': 180,
                    'elevators': 50
                },
                'circuits': {
                    'lighting': {
                        'wire_size': 12,
                        'breaker_size': 20
                    },
                    'receptacles': {
                        'wire_size': 12,
                        'breaker_size': 20
                    }
                }
            },
            'plumbing': {
                'fixtures': {
                    'faucets': {
                        'flow_rate': 2.0,
                        'count': 20
                    },
                    'toilets': {
                        'flow_rate': 1.6,
                        'count': 15
                    }
                }
            },
            'environmental': {
                'materials': {
                    'steel': {
                        'recycled_content': 30
                    },
                    'concrete': {
                        'recycled_content': 15
                    }
                },
                'sustainable_features': [
                    'solar_panels',
                    'rainwater_harvesting',
                    'green_roof'
                ]
            }
        }
        
        # Perform validation
        results = self.validator.validate_design(building_design)
        
        # Verify results
        self.assertIsInstance(results, list)
        
        if results:
            # Generate compliance report
            report = self.validator.get_compliance_report("test_building_001", results)
            
            # Verify report structure
            self.assertIn('building_id', report)
            self.assertIn('overall_status', report)
            self.assertIn('overall_score', report)
            self.assertIn('total_regulations', report)
            self.assertIn('regulation_details', report)
            
            # Verify report content
            self.assertEqual(report['building_id'], "test_building_001")
            self.assertIn(report['overall_status'], ['passed', 'partial', 'failed'])
            self.assertGreaterEqual(report['overall_score'], 0.0)
            self.assertLessEqual(report['overall_score'], 100.0)
            self.assertEqual(report['total_regulations'], len(results))
            self.assertEqual(len(report['regulation_details']), len(results))
            
            # Log detailed results for debugging
            print(f"\nCompliance Report for {report['building_id']}:")
            print(f"Overall Status: {report['overall_status']}")
            print(f"Overall Score: {report['overall_score']:.1f}%")
            print(f"Total Regulations: {report['total_regulations']}")
            print(f"Passed: {report['passed_regulations']}, Failed: {report['failed_regulations']}, Partial: {report['partial_regulations']}")
            print(f"Total Violations: {report['total_violations']}, Total Warnings: {report['total_warnings']}")
            
            for detail in report['regulation_details']:
                print(f"\nRegulation: {detail['regulation_code']} - {detail['regulation_title']}")
                print(f"Status: {detail['status']}, Score: {detail['score']:.1f}%")
                print(f"Rules: {detail['passed_rules']}/{detail['total_rules']} passed")
                if detail['violations']:
                    print(f"Violations: {len(detail['violations'])}")
                if detail['warnings']:
                    print(f"Warnings: {detail['warnings']}")


if __name__ == '__main__':
    unittest.main() 