"""
End-to-End Workflow Tests for SVG-BIM System

This module provides comprehensive end-to-end testing for the complete SVG-BIM pipeline:
- Complete workflow testing (SVG → Parse → Enrich → Assemble → Export)
- Integration testing between all components
- Real-world scenario testing
- Performance and scalability testing
- Error recovery and resilience testing
"""

import pytest
import tempfile
import os
import time
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock, patch

from core.services.svg_parser
from ..services.bim_assembly import BIMAssemblyPipeline, AssemblyConfig
from services.export_integration import ExportIntegration
from core.services.persistence
from services.performance_optimizer import PerformanceOptimizer, OptimizationLevel
from core.services.spatial_reasoning
from services.relationship_manager import AdvancedRelationshipManager
from core.api.main
from core.utils.errors
    SVGParseError, BIMAssemblyError, GeometryError, RelationshipError,
    EnrichmentError, ValidationError, ExportError
)


class TestCompleteWorkflows:
    """Test complete end-to-end workflows."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.bim_pipeline = BIMAssemblyPipeline()
        self.export_service = ExportIntegration()
        self.persistence = PersistenceService()
        self.optimizer = PerformanceOptimizer(OptimizationLevel.STANDARD)
        self.spatial_engine = SpatialReasoningEngine()
        self.rel_manager = AdvancedRelationshipManager()
        
        # Create test directory
        self.test_dir = tempfile.mkdtemp()
        
        # Sample SVG content for testing
        self.sample_svg = """
        <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
            <!-- Walls -->
            <rect x="100" y="100" width="200" height="20" fill="gray" class="wall" data-bim-type="wall"/>
            <rect x="100" y="300" width="200" height="20" fill="gray" class="wall" data-bim-type="wall"/>
            <rect x="100" y="100" width="20" height="200" fill="gray" class="wall" data-bim-type="wall"/>
            <rect x="280" y="100" width="20" height="200" fill="gray" class="wall" data-bim-type="wall"/>
            
            <!-- Doors -->
            <rect x="180" y="100" width="40" height="20" fill="brown" class="door" data-bim-type="door"/>
            <rect x="180" y="300" width="40" height="20" fill="brown" class="door" data-bim-type="door"/>
            
            <!-- Windows -->
            <rect x="120" y="80" width="60" height="20" fill="blue" class="window" data-bim-type="window"/>
            <rect x="220" y="80" width="60" height="20" fill="blue" class="window" data-bim-type="window"/>
            
            <!-- HVAC Equipment -->
            <circle cx="150" cy="200" r="30" fill="green" class="hvac" data-bim-type="hvac"/>
            <rect x="200" y="180" width="40" height="40" fill="green" class="hvac" data-bim-type="hvac"/>
            
            <!-- Electrical -->
            <circle cx="250" cy="150" r="15" fill="yellow" class="electrical" data-bim-type="electrical"/>
            <circle cx="250" cy="250" r="15" fill="yellow" class="electrical" data-bim-type="electrical"/>
        </svg>
        """
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_complete_svg_to_bim_workflow(self):
        """Test complete SVG to BIM workflow with all components."""
        try:
            # Step 1: Parse SVG
            svg_elements = extract_svg_elements(self.sample_svg)
            assert len(svg_elements) > 0
            print(f"Parsed {len(svg_elements)} SVG elements")
            
            # Step 2: Assemble BIM with enrichment
            svg_data = {"elements": svg_elements}
            result = self.bim_pipeline.assemble_bim(svg_data)
            assert result.success
            assert len(result.elements) > 0
            print(f"Assembled {len(result.elements)} BIM elements")
            
            # Step 3: Spatial reasoning
            spatial_analysis = self.spatial_engine.analyze_spatial_relationships(result.elements)
            print(f"Spatial analysis: {len(spatial_analysis.spatial_groups)} groups, {len(spatial_analysis.collisions)} collisions")
            
            # Step 4: Relationship management
            for element in result.elements:
                self.rel_manager.add_element(element)
            
            # Add some relationships
            wall_elements = [e for e in result.elements if e.bim_type == "wall"]
            door_elements = [e for e in result.elements if e.bim_type == "door"]
            
            if wall_elements and door_elements:
                self.rel_manager.add_relationship(
                    source_id=wall_elements[0].id,
                    target_id=door_elements[0].id,
                    relationship_type="contains",
                    properties={"opening_type": "doorway"}
                )
            
            # Step 5: Export BIM
            bim_data = {
                "elements": [elem.dict() for elem in result.elements],
                "systems": [sys.dict() for sys in result.systems],
                "spaces": [space.dict() for space in result.spaces],
                "relationships": [rel.dict() for rel in result.relationships],
                "spatial_analysis": {
                    "spatial_groups": len(spatial_analysis.spatial_groups),
                    "collisions": len(spatial_analysis.collisions),
                    "accessibility_score": spatial_analysis.accessibility_score
                },
                "metadata": {
                    "assembly_time": result.assembly_time,
                    "element_count": len(result.elements),
                    "workflow_version": "1.0"
                }
            }
            
            # Step 6: Save and load BIM
            output_file = os.path.join(self.test_dir, "bim_output.json")
            self.persistence.save_bim_json(bim_data, output_file)
            assert os.path.exists(output_file)
            
            loaded_data = self.persistence.load_bim_json(output_file)
            assert loaded_data["elements"] == bim_data["elements"]
            assert loaded_data["metadata"]["element_count"] == bim_data["metadata"]["element_count"]
            
            print(f"Complete workflow successful: {len(result.elements)} elements processed")
            
        except Exception as e:
            pytest.fail(f"Complete workflow failed: {e}")
    
    def test_optimized_workflow(self):
        """Test workflow with performance optimization."""
        try:
            # Start monitoring
            self.optimizer.start_monitoring()
            
            # Parse SVG with optimization
            optimized_parser = self.optimizer.optimize_operation(
                "svg_parsing", extract_svg_elements, use_caching=True, use_profiling=True
            )
            svg_elements = optimized_parser(self.sample_svg)
            
            # Assemble BIM with optimization
            svg_data = {"elements": svg_elements}
            result = self.bim_pipeline.assemble_bim(svg_data)
            assert result.success
            
            # Check optimization metrics
            report = self.optimizer.get_optimization_report()
            assert report['profiler_summary']['total_operations'] > 0
            
            # Stop monitoring
            self.optimizer.stop_monitoring()
            
            print(f"Optimized workflow completed with {len(result.elements)} elements")
            
        except Exception as e:
            pytest.fail(f"Optimized workflow failed: {e}")
    
    def test_multiple_format_export_workflow(self):
        """Test workflow with multiple export formats."""
        try:
            # Parse and assemble
            svg_elements = extract_svg_elements(self.sample_svg)
            svg_data = {"elements": svg_elements}
            result = self.bim_pipeline.assemble_bim(svg_data)
            assert result.success
            
            # Prepare BIM data
            bim_data = {
                "elements": [elem.dict() for elem in result.elements],
                "systems": [sys.dict() for sys in result.systems],
                "spaces": [space.dict() for space in result.spaces],
                "relationships": [rel.dict() for rel in result.relationships],
                "metadata": {"version": "1.0"}
            }
            
            # Export to multiple formats
            json_file = os.path.join(self.test_dir, "output.json")
            xml_file = os.path.join(self.test_dir, "output.xml")
            svg_file = os.path.join(self.test_dir, "output.svg")
            
            # JSON export
            self.export_service.save_bim_assembly(bim_data, json_file, "json")
            assert os.path.exists(json_file)
            
            # XML export
            self.export_service.save_bim_assembly(bim_data, xml_file, "xml")
            assert os.path.exists(xml_file)
            
            # SVG export
            self.export_service.save_bim_assembly(bim_data, svg_file, "svg")
            assert os.path.exists(svg_file)
            
            # Verify all files can be loaded
            json_data = self.export_service.load_bim_assembly(json_file, "json")
            xml_data = self.export_service.load_bim_assembly(xml_file, "xml")
            
            assert json_data["metadata"] == bim_data["metadata"]
            assert "elements" in xml_data
            
            print(f"Multiple format export successful: JSON, XML, SVG")
            
        except Exception as e:
            pytest.fail(f"Multiple format export workflow failed: {e}")


class TestRealWorldScenarios:
    """Test real-world scenarios and use cases."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.bim_pipeline = BIMAssemblyPipeline()
        self.export_service = ExportIntegration()
        self.persistence = PersistenceService()
        
        # Complex building floor plan
        self.complex_svg = """
        <svg width="1200" height="800" xmlns="http://www.w3.org/2000/svg">
            <!-- Office Building Floor Plan -->
            
            <!-- Exterior Walls -->
            <rect x="50" y="50" width="1100" height="20" fill="darkgray" data-bim-type="wall" data-material="concrete"/>
            <rect x="50" y="730" width="1100" height="20" fill="darkgray" data-bim-type="wall" data-material="concrete"/>
            <rect x="50" y="50" width="20" height="700" fill="darkgray" data-bim-type="wall" data-material="concrete"/>
            <rect x="1130" y="50" width="20" height="700" fill="darkgray" data-bim-type="wall" data-material="concrete"/>
            
            <!-- Interior Walls -->
            <rect x="300" y="50" width="20" height="700" fill="gray" data-bim-type="wall" data-material="drywall"/>
            <rect x="600" y="50" width="20" height="700" fill="gray" data-bim-type="wall" data-material="drywall"/>
            <rect x="900" y="50" width="20" height="700" fill="gray" data-bim-type="wall" data-material="drywall"/>
            <rect x="50" y="250" width="1100" height="20" fill="gray" data-bim-type="wall" data-material="drywall"/>
            <rect x="50" y="500" width="1100" height="20" fill="gray" data-bim-type="wall" data-material="drywall"/>
            
            <!-- Doors -->
            <rect x="280" y="50" width="40" height="20" fill="brown" data-bim-type="door" data-door-type="swing"/>
            <rect x="580" y="50" width="40" height="20" fill="brown" data-bim-type="door" data-door-type="swing"/>
            <rect x="880" y="50" width="40" height="20" fill="brown" data-bim-type="door" data-door-type="swing"/>
            <rect x="50" y="230" width="20" height="40" fill="brown" data-bim-type="door" data-door-type="swing"/>
            <rect x="50" y="480" width="20" height="40" fill="brown" data-bim-type="door" data-door-type="swing"/>
            
            <!-- Windows -->
            <rect x="100" y="30" width="80" height="20" fill="lightblue" data-bim-type="window" data-window-type="fixed"/>
            <rect x="400" y="30" width="80" height="20" fill="lightblue" data-bim-type="window" data-window-type="fixed"/>
            <rect x="700" y="30" width="80" height="20" fill="lightblue" data-bim-type="window" data-window-type="fixed"/>
            <rect x="1000" y="30" width="80" height="20" fill="lightblue" data-bim-type="window" data-window-type="fixed"/>
            
            <!-- HVAC Equipment -->
            <circle cx="150" cy="150" r="25" fill="green" data-bim-type="hvac" data-equipment-type="air-handler"/>
            <circle cx="450" cy="150" r="25" fill="green" data-bim-type="hvac" data-equipment-type="air-handler"/>
            <circle cx="750" cy="150" r="25" fill="green" data-bim-type="hvac" data-equipment-type="air-handler"/>
            <circle cx="1050" cy="150" r="25" fill="green" data-bim-type="hvac" data-equipment-type="air-handler"/>
            
            <!-- Electrical Panels -->
            <rect x="150" y="350" width="40" height="60" fill="yellow" data-bim-type="electrical" data-panel-type="distribution"/>
            <rect x="450" y="350" width="40" height="60" fill="yellow" data-bim-type="electrical" data-panel-type="distribution"/>
            <rect x="750" y="350" width="40" height="60" fill="yellow" data-bim-type="electrical" data-panel-type="distribution"/>
            <rect x="1050" y="350" width="40" height="60" fill="yellow" data-bim-type="electrical" data-panel-type="distribution"/>
            
            <!-- Plumbing Fixtures -->
            <rect x="200" y="600" width="30" height="30" fill="blue" data-bim-type="plumbing" data-fixture-type="sink"/>
            <rect x="500" y="600" width="30" height="30" fill="blue" data-bim-type="plumbing" data-fixture-type="sink"/>
            <rect x="800" y="600" width="30" height="30" fill="blue" data-bim-type="plumbing" data-fixture-type="sink"/>
            <rect x="1100" y="600" width="30" height="30" fill="blue" data-bim-type="plumbing" data-fixture-type="sink"/>
            
            <!-- Fire Safety -->
            <circle cx="200" cy="400" r="15" fill="red" data-bim-type="fire_safety" data-device-type="smoke-detector"/>
            <circle cx="500" cy="400" r="15" fill="red" data-bim-type="fire_safety" data-device-type="smoke-detector"/>
            <circle cx="800" cy="400" r="15" fill="red" data-bim-type="fire_safety" data-device-type="smoke-detector"/>
            <circle cx="1100" cy="400" r="15" fill="red" data-bim-type="fire_safety" data-device-type="smoke-detector"/>
        </svg>
        """
    
    def test_complex_building_workflow(self):
        """Test workflow with complex building floor plan."""
        try:
            # Parse complex SVG
            svg_elements = extract_svg_elements(self.complex_svg)
            assert len(svg_elements) > 20  # Should have many elements
            
            # Assemble BIM
            svg_data = {"elements": svg_elements}
            result = self.bim_pipeline.assemble_bim(svg_data)
            assert result.success
            assert len(result.elements) > 20
            
            # Verify different BIM types
            bim_types = set(elem.bim_type for elem in result.elements)
            expected_types = {"wall", "door", "window", "hvac", "electrical", "plumbing", "fire_safety"}
            assert expected_types.issubset(bim_types)
            
            # Export complex BIM
            bim_data = {
                "elements": [elem.dict() for elem in result.elements],
                "systems": [sys.dict() for sys in result.systems],
                "spaces": [space.dict() for space in result.spaces],
                "relationships": [rel.dict() for rel in result.relationships],
                "metadata": {
                    "building_type": "office",
                    "floor_number": 1,
                    "total_elements": len(result.elements)
                }
            }
            
            # Save complex BIM
            output_file = "complex_building_bim.json"
            self.persistence.save_bim_json(bim_data, output_file)
            assert os.path.exists(output_file)
            
            # Clean up
            if os.path.exists(output_file):
                os.unlink(output_file)
            
            print(f"Complex building workflow successful: {len(result.elements)} elements")
            
        except Exception as e:
            pytest.fail(f"Complex building workflow failed: {e}")
    
    def test_multi_floor_workflow(self):
        """Test workflow with multiple floors."""
        try:
            # Create multiple floor SVGs
            floors = []
            for floor_num in range(1, 4):  # 3 floors
                floor_svg = f"""
                <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
                    <rect x="100" y="100" width="200" height="20" fill="gray" data-bim-type="wall" data-floor="{floor_num}"/>
                    <circle cx="150" cy="200" r="30" fill="blue" data-bim-type="hvac" data-floor="{floor_num}"/>
                    <circle cx="250" cy="200" r="15" fill="yellow" data-bim-type="electrical" data-floor="{floor_num}"/>
                </svg>
                """
                floors.append(floor_svg)
            
            # Process each floor
            all_bim_data = []
            for i, floor_svg in enumerate(floors):
                svg_elements = extract_svg_elements(floor_svg)
                svg_data = {"elements": svg_elements}
                result = self.bim_pipeline.assemble_bim(svg_data)
                assert result.success
                
                bim_data = {
                    "floor_number": i + 1,
                    "elements": [elem.dict() for elem in result.elements],
                    "systems": [sys.dict() for sys in result.systems],
                    "spaces": [space.dict() for space in result.spaces],
                    "relationships": [rel.dict() for rel in result.relationships]
                }
                all_bim_data.append(bim_data)
            
            # Combine multi-floor data
            building_data = {
                "building_name": "Test Building",
                "floors": all_bim_data,
                "total_floors": len(floors),
                "total_elements": sum(len(floor["elements"]) for floor in all_bim_data)
            }
            
            # Save multi-floor BIM
            output_file = "multi_floor_building.json"
            self.persistence.save_bim_json(building_data, output_file)
            assert os.path.exists(output_file)
            
            # Clean up
            if os.path.exists(output_file):
                os.unlink(output_file)
            
            print(f"Multi-floor workflow successful: {building_data['total_elements']} total elements")
            
        except Exception as e:
            pytest.fail(f"Multi-floor workflow failed: {e}")


class TestAPIWorkflows:
    """Test API-based workflows."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = app.test_client()
        
        # Sample SVG for API testing
        self.test_svg = """
        <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
            <rect x="100" y="100" width="200" height="20" fill="gray" data-bim-type="wall"/>
            <circle cx="150" cy="200" r="30" fill="blue" data-bim-type="hvac"/>
        </svg>
        """
    
    def test_api_health_check(self):
        """Test API health check endpoint."""
        response = self.client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
    
    def test_api_svg_upload_workflow(self):
        """Test complete API workflow with SVG upload."""
        try:
            # Create temporary SVG file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
                f.write(self.test_svg)
                svg_file_path = f.name
            
            try:
                # Upload SVG
                with open(svg_file_path, 'rb') as f:
                    response = self.client.post('/upload/svg', 
                                             data={'file': (f, 'test.svg')},
                                             content_type='multipart/form-data')
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] == True
                
                # Assemble BIM
                response = self.client.post('/assemble/bim',
                                         data={'svg_content': self.test_svg,
                                               'format': 'json'})
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] == True
                
            finally:
                if os.path.exists(svg_file_path):
                    os.unlink(svg_file_path)
            
            print("API workflow successful")
            
        except Exception as e:
            pytest.fail(f"API workflow failed: {e}")
    
    def test_api_error_handling(self):
        """Test API error handling."""
        # Test with invalid SVG
        response = self.client.post('/assemble/bim',
                                 data={'svg_content': 'invalid svg content'})
        
        # Should handle gracefully
        assert response.status_code in [400, 500]
    
    def test_api_query_workflow(self):
        """Test API query workflow."""
        # First create some BIM data
        response = self.client.post('/assemble/bim',
                                 data={'svg_content': self.test_svg,
                                       'format': 'json'})
        
        if response.status_code == 200:
            data = response.get_json()
            file_id = data.get('file_path', 'test123')
            
            # Query BIM data
            response = self.client.get(f'/query/bim/{file_id}?query_type=summary')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['success'] == True


class TestPerformanceWorkflows:
    """Test performance and scalability workflows."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.optimizer = PerformanceOptimizer(OptimizationLevel.AGGRESSIVE)
        self.bim_pipeline = BIMAssemblyPipeline()
    
    def test_large_scale_workflow(self):
        """Test workflow with large-scale data."""
        try:
            # Generate large SVG
            large_svg = '<svg width="2000" height="2000" xmlns="http://www.w3.org/2000/svg">'
            for i in range(500):  # 500 elements
                x = (i % 50) * 40
                y = (i // 50) * 40
                large_svg += f'<rect x="{x}" y="{y}" width="30" height="30" fill="gray" data-bim-type="wall"/>'
            large_svg += '</svg>'
            
            start_time = time.time()
            
            # Parse large SVG
            svg_elements = extract_svg_elements(large_svg)
            parse_time = time.time() - start_time
            
            # Assemble BIM
            svg_data = {"elements": svg_elements}
            result = self.bim_pipeline.assemble_bim(svg_data)
            
            total_time = time.time() - start_time
            
            # Verify performance
            assert len(svg_elements) >= 500
            assert result.success
            assert total_time < 30.0  # Should complete within 30 seconds
            assert parse_time < 5.0   # Parsing should be fast
            
            print(f"Large-scale workflow: {len(svg_elements)} elements in {total_time:.2f}s")
            
        except Exception as e:
            pytest.fail(f"Large-scale workflow failed: {e}")
    
    def test_concurrent_workflow(self):
        """Test concurrent processing workflows."""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def process_svg(svg_content, thread_id):
            try:
                svg_elements = extract_svg_elements(svg_content)
                svg_data = {"elements": svg_elements}
                result = self.bim_pipeline.assemble_bim(svg_data)
                results_queue.put((thread_id, result.success, len(result.elements)))
            except Exception as e:
                results_queue.put((thread_id, False, str(e)))
        
        # Create multiple SVG contents
        svg_contents = []
        for i in range(5):
            svg_content = f"""
            <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
                <rect x="{100 + i*50}" y="100" width="200" height="20" fill="gray" data-bim-type="wall"/>
                <circle cx="{150 + i*50}" cy="200" r="30" fill="blue" data-bim-type="hvac"/>
            </svg>
            """
            svg_contents.append(svg_content)
        
        # Start concurrent processing
        threads = []
        for i, svg_content in enumerate(svg_contents):
            thread = threading.Thread(target=process_svg, args=(svg_content, i))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Verify all threads completed successfully
        assert len(results) == 5
        for thread_id, success, element_count in results:
            assert success, f"Thread {thread_id} failed"
            assert element_count > 0, f"Thread {thread_id} returned no elements"
        
        print(f"Concurrent workflow successful: {len(results)} threads completed")


class TestErrorRecoveryWorkflows:
    """Test error recovery and resilience workflows."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.bim_pipeline = BIMAssemblyPipeline()
    
    def test_partial_failure_recovery(self):
        """Test recovery from partial failures."""
        # Mixed valid/invalid SVG
        mixed_svg = """
        <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
            <rect x="100" y="100" width="200" height="20" fill="gray" data-bim-type="wall"/>
            <rect x="invalid" y="invalid" width="invalid" height="invalid" fill="gray" data-bim-type="wall"/>
            <circle cx="150" cy="200" r="30" fill="blue" data-bim-type="hvac"/>
        </svg>
        """
        
        try:
            # Should handle mixed valid/invalid elements
            svg_elements = extract_svg_elements(mixed_svg)
            assert len(svg_elements) > 0  # Should extract valid elements
            
            svg_data = {"elements": svg_elements}
            result = self.bim_pipeline.assemble_bim(svg_data)
            
            # Should succeed with valid elements
            assert result.success
            assert len(result.elements) > 0
            
            print("Partial failure recovery successful")
            
        except Exception as e:
            pytest.fail(f"Partial failure recovery failed: {e}")
    
    def test_graceful_degradation(self):
        """Test graceful degradation when components fail."""
        try:
            # Test with minimal SVG
            basic_svg = """
            <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
                <rect x="100" y="100" width="200" height="20" fill="gray"/>
            </svg>
            """
            
            svg_elements = extract_svg_elements(basic_svg)
            svg_data = {"elements": svg_elements}
            
            # Should work even with minimal data
            result = self.bim_pipeline.assemble_bim(svg_data)
            assert result.success
            
            print("Graceful degradation successful")
            
        except Exception as e:
            pytest.fail(f"Graceful degradation failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__]) 