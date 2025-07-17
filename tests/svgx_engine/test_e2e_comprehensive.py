"""
SVGX Engine - Comprehensive End-to-End Tests

Tests covering all critical functionality including:
- Core parsing and validation
- Runtime evaluation and simulation
- Compilation and export
- Caching and performance
- Database integration
- Error handling and security
- API endpoints and responses
"""

import unittest
import time
import json
import tempfile
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app
from utils.errors import SVGXError, ValidationError, ParseError, RuntimeError
from utils.caching import cache_get, cache_set, cache_stats, cache_clear
from utils.database import get_database_manager, insert_document, get_document
from utils.logging_config import get_logger
from utils.performance import PerformanceMonitor


class TestSVGXEngineE2E(unittest.TestCase):
    """Comprehensive end-to-end tests for SVGX Engine."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = app
        self.client = app.test_client()
        self.logger = get_logger("test_e2e")
        self.performance_monitor = PerformanceMonitor()
        
        # Test SVGX content
        self.test_svgx = """
        <svgx>
            <circle id="test-circle" cx="100" cy="100" r="50" 
                    fill="red" stroke="black" stroke-width="2">
                <behavior>
                    <on-click>
                        <set-attribute name="fill" value="blue"/>
                    </on-click>
                </behavior>
            </circle>
            <rect id="test-rect" x="200" y="200" width="100" height="80" 
                  fill="green" stroke="black" stroke-width="2">
                <behavior>
                    <on-hover>
                        <set-attribute name="fill" value="yellow"/>
                    </on-hover>
                </behavior>
            </rect>
        </svgx>
        """
        
        # Clear cache and database before tests
        cache_clear()
        self.db_manager = get_database_manager()
    
    def tearDown(self):
        """Clean up after tests."""
        cache_clear()
    
    def test_01_health_endpoint(self):
        """Test health endpoint functionality."""
        self.logger.info("Testing health endpoint")
        
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
        self.assertIn('version', data)
        self.assertIn('performance', data)
        
        self.assertEqual(data['status'], 'healthy')
        self.assertIsInstance(data['performance'], dict)
    
    def test_02_parse_endpoint(self):
        """Test SVGX parsing endpoint."""
        self.logger.info("Testing parse endpoint")
        
        response = self.client.post('/parse', json={
            'content': self.test_svgx,
            'options': {'validate': True}
        })
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('elements', data)
        self.assertIsInstance(data['elements'], list)
        
        # Verify parsed elements
        elements = data['elements']
        self.assertGreater(len(elements), 0)
        
        # Check for circle element
        circle_found = any(elem.get('id') == 'test-circle' for elem in elements)
        self.assertTrue(circle_found)
        
        # Check for rect element
        rect_found = any(elem.get('id') == 'test-rect' for elem in elements)
        self.assertTrue(rect_found)
    
    def test_03_evaluate_endpoint(self):
        """Test behavior evaluation endpoint."""
        self.logger.info("Testing evaluate endpoint")
        
        response = self.client.post('/evaluate', json={
            'content': self.test_svgx,
            'options': {'interactive': True}
        })
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('behaviors', data)
        self.assertIsInstance(data['behaviors'], list)
    
    def test_04_simulate_endpoint(self):
        """Test physics simulation endpoint."""
        self.logger.info("Testing simulate endpoint")
        
        response = self.client.post('/simulate', json={
            'content': self.test_svgx,
            'options': {'duration': 1.0}
        })
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('simulation', data)
        self.assertIsInstance(data['simulation'], dict)
    
    def test_05_interactive_endpoints(self):
        """Test interactive operation endpoints."""
        self.logger.info("Testing interactive endpoints")
        
        # Test click operation
        response = self.client.post('/interactive', json={
            'operation': 'click',
            'element_id': 'test-circle',
            'coordinates': {'x': 100, 'y': 100},
            'modifiers': {'ctrl': False, 'shift': False}
        })
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        
        # Test hover operation
        response = self.client.post('/interactive', json={
            'operation': 'hover',
            'element_id': 'test-rect',
            'coordinates': {'x': 250, 'y': 240},
            'modifiers': {}
        })
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
    
    def test_06_precision_endpoint(self):
        """Test precision level endpoint."""
        self.logger.info("Testing precision endpoint")
        
        response = self.client.post('/precision', json={
            'level': 'compute',
            'coordinates': {'x': 100.123456, 'y': 200.789012}
        })
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('coordinates', data)
        
        # Verify precision handling
        coords = data['coordinates']
        self.assertIn('x', coords)
        self.assertIn('y', coords)
    
    def test_07_compile_endpoints(self):
        """Test compilation endpoints."""
        self.logger.info("Testing compile endpoints")
        
        # Test SVG compilation
        response = self.client.post('/compile/svg', json={
            'content': self.test_svgx,
            'options': {'format': 'svg'}
        })
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('output', data)
        self.assertIsInstance(data['output'], str)
        
        # Test JSON compilation
        response = self.client.post('/compile/json', json={
            'content': self.test_svgx,
            'options': {'format': 'json'}
        })
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('output', data)
        self.assertIsInstance(data['output'], dict)
    
    def test_08_state_endpoint(self):
        """Test interactive state endpoint."""
        self.logger.info("Testing state endpoint")
        
        response = self.client.get('/state')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('selected_elements', data)
        self.assertIn('hovered_element', data)
        self.assertIn('drag_state', data)
        self.assertIn('constraints', data)
        self.assertIn('precision_level', data)
    
    def test_09_metrics_endpoint(self):
        """Test metrics endpoint."""
        self.logger.info("Testing metrics endpoint")
        
        response = self.client.get('/metrics')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIsInstance(data, dict)
        self.assertIn('total_requests', data)
        self.assertIn('avg_response_time', data)
    
    def test_10_error_handling(self):
        """Test error handling with invalid input."""
        self.logger.info("Testing error handling")
        
        # Test invalid SVGX content
        response = self.client.post('/parse', json={
            'content': '<invalid>content</invalid>',
            'options': {'validate': True}
        })
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('message', data)
        
        # Test missing required fields
        response = self.client.post('/parse', json={})
        
        self.assertEqual(response.status_code, 422)
    
    def test_11_performance_targets(self):
        """Test performance targets from CTO directives."""
        self.logger.info("Testing performance targets")
        
        # Test UI response time (< 16ms)
        start_time = time.time()
        response = self.client.get('/health')
        ui_response_time = (time.time() - start_time) * 1000
        
        self.assertLess(ui_response_time, 16.0, 
                       f"UI response time {ui_response_time:.2f}ms exceeds 16ms target")
        
        # Test parse operation time
        start_time = time.time()
        response = self.client.post('/parse', json={
            'content': self.test_svgx,
            'options': {'validate': True}
        })
        parse_time = (time.time() - start_time) * 1000
        
        self.assertLess(parse_time, 32.0,
                       f"Parse time {parse_time:.2f}ms exceeds 32ms target")
        
        # Test evaluate operation time
        start_time = time.time()
        response = self.client.post('/evaluate', json={
            'content': self.test_svgx,
            'options': {'interactive': True}
        })
        evaluate_time = (time.time() - start_time) * 1000
        
        self.assertLess(evaluate_time, 100.0,
                       f"Evaluate time {evaluate_time:.2f}ms exceeds 100ms target")
    
    def test_12_caching_functionality(self):
        """Test caching system functionality."""
        self.logger.info("Testing caching functionality")
        
        # Test cache set and get
        test_key = "test_cache_key"
        test_value = {"test": "data", "timestamp": time.time()}
        
        # Set cache value
        success = cache_set(test_key, test_value, timedelta(minutes=5))
        self.assertTrue(success)
        
        # Get cache value
        cached_value = cache_get(test_key)
        self.assertIsNotNone(cached_value)
        self.assertEqual(cached_value, test_value)
        
        # Test cache statistics
        stats = cache_stats()
        self.assertIn('hits', stats)
        self.assertIn('misses', stats)
        self.assertIn('sets', stats)
        self.assertGreater(stats['sets'], 0)
    
    def test_13_database_integration(self):
        """Test database integration functionality."""
        self.logger.info("Testing database integration")
        
        # Test document insertion
        doc_name = f"test_doc_{int(time.time())}"
        doc_content = self.test_svgx
        user_id = "test_user"
        
        result = insert_document(doc_name, doc_content, user_id)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        
        # Get document ID from result
        if result.data and len(result.data) > 0:
            doc_id = result.data[0].get('id')
            if doc_id:
                # Test document retrieval
                get_result = get_document(doc_id)
                self.assertTrue(get_result.success)
                self.assertIsNotNone(get_result.data)
                
                if get_result.data:
                    retrieved_doc = get_result.data[0]
                    self.assertEqual(retrieved_doc['name'], doc_name)
                    self.assertEqual(retrieved_doc['content'], doc_content)
                    self.assertEqual(retrieved_doc['user_id'], user_id)
    
    def test_14_security_validation(self):
        """Test security validation and input sanitization."""
        self.logger.info("Testing security validation")
        
        # Test XSS prevention
        malicious_content = """
        <svgx>
            <script>alert('xss')</script>
            <circle cx="100" cy="100" r="50" fill="red"/>
        </svgx>
        """
        
        response = self.client.post('/parse', json={
            'content': malicious_content,
            'options': {'validate': True}
        })
        
        # Should either reject or sanitize the content
        self.assertIn(response.status_code, [200, 400])
        
        if response.status_code == 200:
            data = json.loads(response.data)
            # Verify script tags are not present in output
            output_str = json.dumps(data)
            self.assertNotIn('<script>', output_str)
    
    def test_15_concurrent_operations(self):
        """Test concurrent operations and thread safety."""
        self.logger.info("Testing concurrent operations")
        
        import threading
        
        results = []
        errors = []
        
        def make_request():
            try:
                response = self.client.post('/parse', json={
                    'content': self.test_svgx,
                    'options': {'validate': True}
                })
                results.append(response.status_code == 200)
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded
        self.assertEqual(len(results), 10)
        self.assertTrue(all(results))
        self.assertEqual(len(errors), 0)
    
    def test_16_memory_usage(self):
        """Test memory usage under load."""
        self.logger.info("Testing memory usage")
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform multiple operations
        for i in range(100):
            response = self.client.post('/parse', json={
                'content': self.test_svgx,
                'options': {'validate': True}
            })
            self.assertEqual(response.status_code, 200)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 100MB)
        self.assertLess(memory_increase, 100.0,
                       f"Memory increase {memory_increase:.2f}MB exceeds 100MB limit")
    
    def test_17_api_documentation(self):
        """Test API documentation endpoints."""
        self.logger.info("Testing API documentation")
        
        # Test OpenAPI docs
        response = self.client.get('/docs')
        self.assertEqual(response.status_code, 200)
        
        # Test ReDoc
        response = self.client.get('/redoc')
        self.assertEqual(response.status_code, 200)
    
    def test_18_logging_functionality(self):
        """Test logging system functionality."""
        self.logger.info("Testing logging functionality")
        
        # Test different log levels
        self.logger.debug("Debug message")
        self.logger.info("Info message")
        self.logger.warning("Warning message")
        self.logger.error("Error message")
        
        # Test performance logging
        self.logger.log_performance("test_operation", 15.5, 25.2, 5.1)
        
        # Test security logging
        self.logger.log_security("test_event", "test_action", "test_resource", "test_user", "127.0.0.1")
    
    def test_19_error_recovery(self):
        """Test error recovery and graceful degradation."""
        self.logger.info("Testing error recovery")
        
        # Test with corrupted SVGX content
        corrupted_content = """
        <svgx>
            <circle cx="100" cy="100" r="50" fill="red">
                <invalid-tag>content</invalid-tag>
            </circle>
        </svgx>
        """
        
        response = self.client.post('/parse', json={
            'content': corrupted_content,
            'options': {'validate': True}
        })
        
        # Should handle gracefully (either success with warnings or proper error)
        self.assertIn(response.status_code, [200, 400])
    
    def test_20_integration_workflow(self):
        """Test complete integration workflow."""
        self.logger.info("Testing complete integration workflow")
        
        # 1. Parse SVGX
        parse_response = self.client.post('/parse', json={
            'content': self.test_svgx,
            'options': {'validate': True}
        })
        self.assertEqual(parse_response.status_code, 200)
        
        # 2. Evaluate behaviors
        evaluate_response = self.client.post('/evaluate', json={
            'content': self.test_svgx,
            'options': {'interactive': True}
        })
        self.assertEqual(evaluate_response.status_code, 200)
        
        # 3. Simulate physics
        simulate_response = self.client.post('/simulate', json={
            'content': self.test_svgx,
            'options': {'duration': 0.5}
        })
        self.assertEqual(simulate_response.status_code, 200)
        
        # 4. Interactive operations
        click_response = self.client.post('/interactive', json={
            'operation': 'click',
            'element_id': 'test-circle',
            'coordinates': {'x': 100, 'y': 100}
        })
        self.assertEqual(click_response.status_code, 200)
        
        # 5. Compile to SVG
        compile_response = self.client.post('/compile/svg', json={
            'content': self.test_svgx,
            'options': {'format': 'svg'}
        })
        self.assertEqual(compile_response.status_code, 200)
        
        # 6. Check final state
        state_response = self.client.get('/state')
        self.assertEqual(state_response.status_code, 200)
        
        # Verify all operations completed successfully
        all_responses = [
            parse_response, evaluate_response, simulate_response,
            click_response, compile_response, state_response
        ]
        
        for response in all_responses:
            data = json.loads(response.data)
            self.assertIn('success', data)
            self.assertTrue(data['success'])


def run_comprehensive_tests():
    """Run comprehensive end-to-end tests."""
    print("Starting comprehensive SVGX Engine end-to-end tests...")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSVGXEngineE2E)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\nTest Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1) 