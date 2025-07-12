"""
Comprehensive Integration Tests for SVG-BIM System

This module provides end-to-end testing for the complete SVG-BIM pipeline including:
- Full workflow testing (SVG → BIM → Export)
- Stress testing with large files
- Edge case handling
- Performance benchmarking
- Error recovery scenarios
"""

import pytest
import tempfile
import os
import time
import json
from typing import Dict, List, Any
from unittest.mock import Mock, patch

from ..services.svg_parser import extract_svg_elements
from ..services.bim_assembly import BIMAssemblyPipeline, AssemblyConfig
from services.export_integration import ExportIntegration
from ..services.persistence import PersistenceService
from services.performance_optimizer import PerformanceOptimizer, OptimizationLevel
from ..utils.errors import (
    SVGParseError, BIMAssemblyError, GeometryError, RelationshipError,
    EnrichmentError, ValidationError, ExportError
)


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.bim_pipeline = BIMAssemblyPipeline()
        self.export_service = ExportIntegration()
        self.persistence = PersistenceService()
        self.optimizer = PerformanceOptimizer(OptimizationLevel.STANDARD)
        
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
    
    def test_complete_svg_to_bim_workflow(self):
        """Test complete SVG to BIM workflow."""
        try:
            # Step 1: Parse SVG
            svg_elements = extract_svg_elements(self.sample_svg)
            assert len(svg_elements) > 0
            
            # Step 2: Assemble BIM
            svg_data = {"elements": svg_elements}
            result = self.bim_pipeline.assemble_bim(svg_data)
            assert result.success
            assert len(result.elements) > 0
            
            # Step 3: Export BIM
            bim_data = {
                "elements": [elem.dict() for elem in result.elements],
                "systems": [sys.dict() for sys in result.systems],
                "spaces": [space.dict() for space in result.spaces],
                "relationships": [rel.dict() for rel in result.relationships],
                "metadata": {
                    "assembly_time": result.assembly_time,
                    "element_count": len(result.elements)
                }
            }
            
            # Step 4: Save and load BIM
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                file_path = f.name
            
            try:
                self.persistence.save_bim_json(bim_data, file_path)
                loaded_data = self.persistence.load_bim_json(file_path)
                
                # Verify data integrity
                assert loaded_data["elements"] == bim_data["elements"]
                assert loaded_data["systems"] == bim_data["systems"]
                assert loaded_data["spaces"] == bim_data["spaces"]
                assert loaded_data["relationships"] == bim_data["relationships"]
                
            finally:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    
        except Exception as e:
            pytest.fail(f"End-to-end workflow failed: {e}")
    
    def test_svg_to_bim_with_optimization(self):
        """Test SVG to BIM workflow with performance optimization."""
        try:
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
            
        except Exception as e:
            pytest.fail(f"Optimized workflow failed: {e}")
    
    def test_multiple_format_export(self):
        """Test exporting BIM data in multiple formats."""
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
            
            # Test JSON export
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as json_file:
                json_path = json_file.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as xml_file:
                xml_path = xml_file.name
            
            try:
                # Export to JSON
                self.export_service.save_bim_assembly(bim_data, json_path, "json")
                assert os.path.exists(json_path)
                
                # Export to XML
                self.export_service.save_bim_assembly(bim_data, xml_path, "xml")
                assert os.path.exists(xml_path)
                
                # Verify both files can be loaded
                json_data = self.export_service.load_bim_assembly(json_path, "json")
                xml_data = self.export_service.load_bim_assembly(xml_path, "xml")
                
                assert json_data["metadata"] == bim_data["metadata"]
                assert "elements" in xml_data
                
            finally:
                for path in [json_path, xml_path]:
                    if os.path.exists(path):
                        os.unlink(path)
                        
        except Exception as e:
            pytest.fail(f"Multiple format export failed: {e}")


class TestStressTesting:
    """Test system performance under stress."""
    
    def test_large_svg_processing(self):
        """Test processing of large SVG files."""
        # Generate large SVG content
        large_svg = '<svg width="2000" height="2000" xmlns="http://www.w3.org/2000/svg">'
        for i in range(1000):  # 1000 elements
            x = (i % 50) * 40
            y = (i // 50) * 40
            large_svg += f'<rect x="{x}" y="{y}" width="30" height="30" fill="gray" data-bim-type="wall"/>'
        large_svg += '</svg>'
        
        try:
            start_time = time.time()
            
            # Parse large SVG
            svg_elements = extract_svg_elements(large_svg)
            parse_time = time.time() - start_time
            
            # Assemble BIM
            svg_data = {"elements": svg_elements}
            result = self.bim_pipeline.assemble_bim(svg_data)
            
            total_time = time.time() - start_time
            
            # Verify performance
            assert len(svg_elements) >= 1000
            assert result.success
            assert total_time < 30.0  # Should complete within 30 seconds
            assert parse_time < 5.0   # Parsing should be fast
            
        except Exception as e:
            pytest.fail(f"Large SVG processing failed: {e}")
    
    def test_concurrent_processing(self):
        """Test concurrent processing of multiple SVGs."""
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


class TestEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_empty_svg(self):
        """Test processing of empty SVG."""
        empty_svg = '<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg"></svg>'
        
        try:
            svg_elements = extract_svg_elements(empty_svg)
            assert len(svg_elements) == 0
            
            svg_data = {"elements": svg_elements}
            result = self.bim_pipeline.assemble_bim(svg_data)
            
            # Should handle empty SVG gracefully
            assert result.success
            assert len(result.elements) == 0
            
        except Exception as e:
            pytest.fail(f"Empty SVG processing failed: {e}")
    
    def test_malformed_svg(self):
        """Test processing of malformed SVG."""
        malformed_svg = '<svg><rect x="100" y="100" width="200" height="20" fill="gray"'
        
        try:
            # Should handle malformed SVG gracefully
            svg_elements = extract_svg_elements(malformed_svg)
            # Should either parse what it can or raise appropriate error
            assert isinstance(svg_elements, list)
            
        except SVGParseError:
            # Expected for malformed SVG
            pass
        except Exception as e:
            pytest.fail(f"Malformed SVG handling failed: {e}")
    
    def test_unsupported_bim_types(self):
        """Test handling of unsupported BIM types."""
        unsupported_svg = """
        <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
            <rect x="100" y="100" width="200" height="20" fill="gray" data-bim-type="unsupported_type"/>
        </svg>
        """
        
        try:
            svg_elements = extract_svg_elements(unsupported_svg)
            svg_data = {"elements": svg_elements}
            result = self.bim_pipeline.assemble_bim(svg_data)
            
            # Should handle unsupported types gracefully
            assert result.success
            
        except Exception as e:
            pytest.fail(f"Unsupported BIM type handling failed: {e}")
    
    def test_memory_intensive_operations(self):
        """Test memory handling during intensive operations."""
        # Create memory-intensive SVG
        memory_svg = '<svg width="2000" height="2000" xmlns="http://www.w3.org/2000/svg">'
        for i in range(5000):  # 5000 elements
            x = (i % 100) * 20
            y = (i // 100) * 20
            memory_svg += f'<rect x="{x}" y="{y}" width="15" height="15" fill="gray" data-bim-type="wall"/>'
        memory_svg += '</svg>'
        
        try:
            # Monitor memory usage
            import psutil
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Process memory-intensive SVG
            svg_elements = extract_svg_elements(memory_svg)
            svg_data = {"elements": svg_elements}
            result = self.bim_pipeline.assemble_bim(svg_data)
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Verify memory usage is reasonable
            assert result.success
            assert memory_increase < 500  # Should not increase by more than 500MB
            
        except Exception as e:
            pytest.fail(f"Memory-intensive operation failed: {e}")


class TestErrorRecovery:
    """Test error recovery scenarios."""
    
    def test_partial_failure_recovery(self):
        """Test recovery from partial failures."""
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
            
        except Exception as e:
            pytest.fail(f"Partial failure recovery failed: {e}")
    
    def test_graceful_degradation(self):
        """Test graceful degradation when components fail."""
        try:
            # Test with missing optional components
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
            
        except Exception as e:
            pytest.fail(f"Graceful degradation failed: {e}")


class TestPerformanceBenchmarking:
    """Test performance benchmarking."""
    
    def test_processing_speed_benchmark(self):
        """Benchmark processing speed."""
        benchmark_svg = """
        <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
        """ + '\n'.join([f'<rect x="{i*10}" y="{i*10}" width="10" height="10" fill="gray" data-bim-type="wall"/>' for i in range(100)]) + """
        </svg>
        """
        
        try:
            # Benchmark parsing
            start_time = time.time()
            svg_elements = extract_svg_elements(benchmark_svg)
            parse_time = time.time() - start_time
            
            # Benchmark assembly
            start_time = time.time()
            svg_data = {"elements": svg_elements}
            result = self.bim_pipeline.assemble_bim(svg_data)
            assembly_time = time.time() - start_time
            
            # Verify performance targets
            assert parse_time < 1.0, f"Parsing too slow: {parse_time}s"
            assert assembly_time < 5.0, f"Assembly too slow: {assembly_time}s"
            assert result.success
            
            print(f"Performance: Parse={parse_time:.3f}s, Assembly={assembly_time:.3f}s")
            
        except Exception as e:
            pytest.fail(f"Performance benchmarking failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__]) 