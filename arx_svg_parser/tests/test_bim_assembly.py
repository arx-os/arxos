"""
Tests for BIM Assembly Pipeline

This module tests:
- Multi-step BIM construction process
- Conflict resolution for overlapping elements
- BIM consistency validation
- Performance optimization for large models
"""

import unittest
import time
from typing import Dict, Any

from ..services.enhanced_bim_assembly import (
    BIMAssemblyPipeline, AssemblyConfig, AssemblyStep, ConflictType, ValidationLevel
)
from models.bim import BIMElement, BIMSystem, BIMSpace, BIMRelationship


class TestBIMAssemblyPipeline(unittest.TestCase):
    """Test cases for BIM assembly pipeline functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = AssemblyConfig(
            validation_level=ValidationLevel.STANDARD,
            conflict_resolution_enabled=True,
            performance_optimization_enabled=True,
            parallel_processing=False,  # Disable for testing
            max_workers=2,
            batch_size=10
        )
        self.pipeline = BIMAssemblyPipeline(self.config)
        
        # Test SVG data
        self.test_svg_data = {
            'elements': [
                {
                    'id': 'wall_1',
                    'type': 'wall',
                    'geometry': {
                        'type': 'rect',
                        'x': 0, 'y': 0,
                        'width': 10, 'height': 0.2
                    },
                    'properties': {'material': 'concrete'},
                    'metadata': {'layer': 'structural'}
                },
                {
                    'id': 'wall_2',
                    'type': 'wall',
                    'geometry': {
                        'type': 'rect',
                        'x': 0, 'y': 0,
                        'width': 0.2, 'height': 8
                    },
                    'properties': {'material': 'concrete'},
                    'metadata': {'layer': 'structural'}
                },
                {
                    'id': 'door_1',
                    'type': 'door',
                    'geometry': {
                        'type': 'rect',
                        'x': 2, 'y': 0,
                        'width': 1, 'height': 2
                    },
                    'properties': {'material': 'wood'},
                    'metadata': {'layer': 'openings'}
                },
                {
                    'id': 'window_1',
                    'type': 'window',
                    'geometry': {
                        'type': 'rect',
                        'x': 4, 'y': 1,
                        'width': 1.5, 'height': 1.5
                    },
                    'properties': {'material': 'glass'},
                    'metadata': {'layer': 'openings'}
                },
                {
                    'id': 'duct_1',
                    'type': 'duct',
                    'geometry': {
                        'type': 'rect',
                        'x': 1, 'y': 2,
                        'width': 0.3, 'height': 0.3
                    },
                    'properties': {'material': 'metal'},
                    'metadata': {'layer': 'hvac'}
                }
            ]
        }
    
    def test_complete_assembly_pipeline(self):
        """Test complete BIM assembly pipeline."""
        result = self.pipeline.assemble_bim(self.test_svg_data)
        
        # Verify assembly was successful
        self.assertTrue(result.success)
        self.assertIsNotNone(result.assembly_id)
        self.assertGreater(len(result.elements), 0)
        self.assertGreater(len(result.systems), 0)
        self.assertGreater(len(result.spaces), 0)
        self.assertGreater(len(result.relationships), 0)
        
        # Verify performance metrics
        self.assertIn('processing_time', result.performance_metrics)
        self.assertIn('total_elements', result.performance_metrics)
        self.assertGreater(result.assembly_time, 0)
    
    def test_geometry_extraction(self):
        """Test geometry extraction from SVG data."""
        elements = self.pipeline._extract_geometry(self.test_svg_data)
        
        self.assertEqual(len(elements), 5)  # 5 elements in test data
        
        # Verify each element has proper structure
        for element in elements:
            self.assertIsInstance(element, BIMElement)
            self.assertIsNotNone(element.element_id)
            self.assertIsNotNone(element.element_type)
            self.assertIsNotNone(element.geometry)
    
    def test_element_classification(self):
        """Test element classification."""
        # Extract elements first
        elements = self.pipeline._extract_geometry(self.test_svg_data)
        self.pipeline.elements = {elem.element_id: elem for elem in elements}
        
        # Run classification
        self.pipeline._classify_elements()
        
        # Verify classification
        for element in self.pipeline.elements.values():
            self.assertIsNotNone(element.category)
            self.assertIn('classification', element.metadata)
    
    def test_spatial_organization(self):
        """Test spatial organization."""
        # Setup elements
        elements = self.pipeline._extract_geometry(self.test_svg_data)
        self.pipeline.elements = {elem.element_id: elem for elem in elements}
        self.pipeline._classify_elements()
        
        # Run spatial organization
        self.pipeline._organize_spatial_structure()
        
        # Verify spaces were created
        self.assertGreater(len(self.pipeline.spaces), 0)
        
        # Verify each space has elements
        for space in self.pipeline.spaces.values():
            self.assertIsInstance(space, BIMSpace)
            self.assertGreater(len(space.elements), 0)
            self.assertIsNotNone(space.boundaries)
    
    def test_system_integration(self):
        """Test system integration."""
        # Setup elements
        elements = self.pipeline._extract_geometry(self.test_svg_data)
        self.pipeline.elements = {elem.element_id: elem for elem in elements}
        self.pipeline._classify_elements()
        
        # Run system integration
        self.pipeline._integrate_systems()
        
        # Verify systems were created
        self.assertGreater(len(self.pipeline.systems), 0)
        
        # Verify each system has elements
        for system in self.pipeline.systems.values():
            self.assertIsInstance(system, BIMSystem)
            self.assertGreater(len(system.elements), 0)
    
    def test_relationship_establishment(self):
        """Test relationship establishment."""
        # Setup elements and systems
        elements = self.pipeline._extract_geometry(self.test_svg_data)
        self.pipeline.elements = {elem.element_id: elem for elem in elements}
        self.pipeline._classify_elements()
        self.pipeline._organize_spatial_structure()
        self.pipeline._integrate_systems()
        
        # Run relationship establishment
        self.pipeline._establish_relationships()
        
        # Verify relationships were created
        self.assertGreater(len(self.pipeline.relationships), 0)
        
        # Verify relationship structure
        for relationship in self.pipeline.relationships:
            self.assertIsInstance(relationship, BIMRelationship)
            self.assertIsNotNone(relationship.relationship_id)
            self.assertIsNotNone(relationship.relationship_type)
            self.assertIsNotNone(relationship.source_id)
            self.assertIsNotNone(relationship.target_id)
    
    def test_conflict_detection(self):
        """Test conflict detection."""
        # Create overlapping elements
        overlapping_svg_data = {
            'elements': [
                {
                    'id': 'element_1',
                    'type': 'wall',
                    'geometry': {
                        'type': 'rect',
                        'x': 0, 'y': 0,
                        'width': 5, 'height': 0.2
                    }
                },
                {
                    'id': 'element_2',
                    'type': 'wall',
                    'geometry': {
                        'type': 'rect',
                        'x': 2, 'y': 0,
                        'width': 5, 'height': 0.2
                    }
                }
            ]
        }
        
        # Setup pipeline with overlapping elements
        elements = self.pipeline._extract_geometry(overlapping_svg_data)
        self.pipeline.elements = {elem.element_id: elem for elem in elements}
        
        # Run conflict detection
        self.pipeline._detect_geometric_conflicts()
        
        # Verify conflicts were detected
        self.assertGreater(len(self.pipeline.conflicts), 0)
        
        # Verify conflict structure
        for conflict in self.pipeline.conflicts:
            self.assertIsNotNone(conflict.conflict_id)
            self.assertIsNotNone(conflict.conflict_type)
            self.assertGreater(len(conflict.elements), 0)
            self.assertGreaterEqual(conflict.severity, 0.0)
            self.assertLessEqual(conflict.severity, 1.0)
    
    def test_conflict_resolution(self):
        """Test conflict resolution."""
        # Create conflicting elements
        conflicting_svg_data = {
            'elements': [
                {
                    'id': 'element_1',
                    'type': 'wall',
                    'geometry': {
                        'type': 'rect',
                        'x': 0, 'y': 0,
                        'width': 5, 'height': 0.2
                    }
                },
                {
                    'id': 'element_2',
                    'type': 'wall',
                    'geometry': {
                        'type': 'rect',
                        'x': 2, 'y': 0,
                        'width': 5, 'height': 0.2
                    }
                }
            ]
        }
        
        # Run complete assembly with conflict resolution
        result = self.pipeline.assemble_bim(conflicting_svg_data)
        
        # Verify assembly completed
        self.assertTrue(result.success)
        
        # Verify conflicts were resolved
        resolved_conflicts = sum(1 for c in result.conflicts if c.resolved)
        self.assertGreater(resolved_conflicts, 0)
    
    def test_consistency_validation(self):
        """Test consistency validation."""
        # Run complete assembly
        result = self.pipeline.assemble_bim(self.test_svg_data)
        
        # Verify validation results
        self.assertIn('validation_results', result.__dict__)
        validation_results = result.validation_results
        
        # Check validation structure
        self.assertIn('overall_valid', validation_results)
        self.assertIn('element_validation', validation_results)
        self.assertIn('system_validation', validation_results)
        self.assertIn('spatial_validation', validation_results)
        self.assertIn('relationship_validation', validation_results)
        self.assertIn('geometry_validation', validation_results)
        
        # Verify validation results are valid
        for validation_type, validation_result in validation_results.items():
            if isinstance(validation_result, dict) and 'valid' in validation_result:
                self.assertTrue(validation_result['valid'])
    
    def test_performance_optimization(self):
        """Test performance optimization."""
        # Create large dataset
        large_svg_data = {
            'elements': [
                {
                    'id': f'element_{i}',
                    'type': 'wall',
                    'geometry': {
                        'type': 'rect',
                        'x': i, 'y': i,
                        'width': 1, 'height': 1
                    }
                }
                for i in range(50)  # Create 50 elements
            ]
        }
        
        # Run assembly with performance optimization
        result = self.pipeline.assemble_bim(large_svg_data)
        
        # Verify optimization was applied
        self.assertTrue(result.success)
        self.assertGreater(len(result.elements), 0)
        
        # Check performance metrics
        self.assertIn('processing_time', result.performance_metrics)
        self.assertIn('total_elements', result.performance_metrics)
    
    def test_assembly_configuration(self):
        """Test assembly configuration options."""
        # Test different configurations
        configs = [
            AssemblyConfig(validation_level=ValidationLevel.BASIC),
            AssemblyConfig(validation_level=ValidationLevel.COMPREHENSIVE),
            AssemblyConfig(conflict_resolution_enabled=False),
            AssemblyConfig(performance_optimization_enabled=False),
            AssemblyConfig(parallel_processing=True, max_workers=4)
        ]
        
        for config in configs:
            pipeline = BIMAssemblyPipeline(config)
            result = pipeline.assemble_bim(self.test_svg_data)
            
            # Verify assembly completed
            self.assertTrue(result.success)
            self.assertGreater(len(result.elements), 0)
    
    def test_error_handling(self):
        """Test error handling in assembly pipeline."""
        # Test with invalid SVG data
        invalid_svg_data = {
            'elements': [
                {
                    'id': 'invalid_element',
                    'type': 'unknown_type',
                    'geometry': None  # Invalid geometry
                }
            ]
        }
        
        result = self.pipeline.assemble_bim(invalid_svg_data)
        
        # Verify assembly handles errors gracefully
        self.assertTrue(result.success)  # Should still succeed but with warnings
        self.assertGreaterEqual(len(result.elements), 0)
    
    def test_assembly_statistics(self):
        """Test assembly statistics."""
        result = self.pipeline.assemble_bim(self.test_svg_data)
        
        # Get statistics
        stats = self.pipeline.get_assembly_statistics()
        
        # Verify statistics structure
        self.assertIn('total_elements', stats)
        self.assertIn('total_systems', stats)
        self.assertIn('total_spaces', stats)
        self.assertIn('total_relationships', stats)
        self.assertIn('total_conflicts', stats)
        self.assertIn('resolved_conflicts', stats)
        self.assertIn('performance_metrics', stats)
        
        # Verify statistics match result
        self.assertEqual(stats['total_elements'], len(result.elements))
        self.assertEqual(stats['total_systems'], len(result.systems))
        self.assertEqual(stats['total_spaces'], len(result.spaces))
        self.assertEqual(stats['total_relationships'], len(result.relationships))
    
    def test_assembly_report_export(self):
        """Test assembly report export."""
        result = self.pipeline.assemble_bim(self.test_svg_data)
        
        # Export report
        report = self.pipeline.export_assembly_report()
        
        # Verify report structure
        self.assertIn('assembly_id', report)
        self.assertIn('timestamp', report)
        self.assertIn('statistics', report)
        self.assertIn('elements', report)
        self.assertIn('systems', report)
        self.assertIn('spaces', report)
        self.assertIn('relationships', report)
        self.assertIn('conflicts', report)
        self.assertIn('performance_metrics', report)
        
        # Verify report data
        self.assertGreater(len(report['elements']), 0)
        self.assertGreater(len(report['systems']), 0)
        self.assertGreater(len(report['spaces']), 0)
    
    def test_parallel_processing(self):
        """Test parallel processing capabilities."""
        # Create configuration with parallel processing
        parallel_config = AssemblyConfig(
            parallel_processing=True,
            max_workers=2,
            batch_size=5
        )
        parallel_pipeline = BIMAssemblyPipeline(parallel_config)
        
        # Create larger dataset for parallel processing
        large_svg_data = {
            'elements': [
                {
                    'id': f'element_{i}',
                    'type': 'wall',
                    'geometry': {
                        'type': 'rect',
                        'x': i, 'y': i,
                        'width': 1, 'height': 1
                    }
                }
                for i in range(20)  # Create 20 elements
            ]
        }
        
        # Run assembly with parallel processing
        result = parallel_pipeline.assemble_bim(large_svg_data)
        
        # Verify parallel processing completed successfully
        self.assertTrue(result.success)
        self.assertEqual(len(result.elements), 20)
    
    def test_batch_processing(self):
        """Test batch processing for large models."""
        # Create large dataset
        large_svg_data = {
            'elements': [
                {
                    'id': f'element_{i}',
                    'type': 'wall',
                    'geometry': {
                        'type': 'rect',
                        'x': i, 'y': i,
                        'width': 1, 'height': 1
                    }
                }
                for i in range(100)  # Create 100 elements
            ]
        }
        
        # Configure for batch processing
        batch_config = AssemblyConfig(
            batch_size=20,
            max_workers=2
        )
        batch_pipeline = BIMAssemblyPipeline(batch_config)
        
        # Run assembly with batch processing
        result = batch_pipeline.assemble_bim(large_svg_data)
        
        # Verify batch processing completed successfully
        self.assertTrue(result.success)
        self.assertEqual(len(result.elements), 100)
        
        # Verify performance metrics
        self.assertIn('processing_time', result.performance_metrics)
        self.assertGreater(result.performance_metrics['processing_time'], 0)


if __name__ == '__main__':
    unittest.main() 