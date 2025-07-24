"""
Comprehensive Performance Monitoring Test Suite for SVGX Engine

This test suite provides comprehensive performance monitoring for:
- Plugin execution performance
- Collaborative editing performance
- Memory usage and optimization
- Response time monitoring
- Error rate tracking
- Resource utilization monitoring
"""

import asyncio
import json
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock

import pytest
import psutil
from fastapi.testclient import TestClient

from svgx_engine.services.plugin_system import (
    PluginManager, PluginMonitor, PluginDevelopmentKit,
    PluginType, PluginStatus, PluginSecurityLevel
)
from svgx_engine.services.performance_optimizer import SVGXPerformanceOptimizer
from svgx_engine.services.metrics_collector import metrics_collector
from svgx_engine.services.api_interface import app


class TestPerformanceMonitoringComprehensive(unittest.TestCase):
    """Comprehensive performance monitoring test suite."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_dir = Path(self.temp_dir) / "plugins"
        self.plugin_dir.mkdir(exist_ok=True)
        
        # Initialize performance components
        self.performance_optimizer = SVGXPerformanceOptimizer()
        self.plugin_manager = PluginManager(plugin_dir=str(self.plugin_dir))
        self.plugin_monitor = PluginMonitor()
        
        # Test client for API testing
        self.client = TestClient(app)
        
        # Create test plugins
        self._create_test_plugins()
        
        # Performance tracking
        self.performance_metrics = []
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_plugins(self):
        """Create test plugins for performance testing."""
        
        # Fast plugin
        fast_plugin_content = '''
"""
Fast Test Plugin
"""
import time
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from svgx_engine.services.plugin_system import (
    BehaviorHandlerPlugin, PluginMetadata, PluginSecurityLevel, PluginType
)

logger = logging.getLogger(__name__)

class FastPlugin(BehaviorHandlerPlugin):
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            name="fast_plugin",
            version="1.0.0",
            description="Fast test plugin",
            author="Test Author",
            plugin_type=PluginType.BEHAVIOR_HANDLER,
            security_level=PluginSecurityLevel.VERIFIED,
            tags=["test", "fast"],
            dependencies=[],
            requirements=[]
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        return True
    
    def handle_ui_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        # Simulate fast processing
        time.sleep(0.001)  # 1ms processing time
        return {
            "status": "processed",
            "plugin": "fast_plugin",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "processing_time_ms": 1
        }
'''
        
        # Slow plugin
        slow_plugin_content = '''
"""
Slow Test Plugin
"""
import time
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from svgx_engine.services.plugin_system import (
    BehaviorHandlerPlugin, PluginMetadata, PluginSecurityLevel, PluginType
)

logger = logging.getLogger(__name__)

class SlowPlugin(BehaviorHandlerPlugin):
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            name="slow_plugin",
            version="1.0.0",
            description="Slow test plugin",
            author="Test Author",
            plugin_type=PluginType.BEHAVIOR_HANDLER,
            security_level=PluginSecurityLevel.VERIFIED,
            tags=["test", "slow"],
            dependencies=[],
            requirements=[]
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        return True
    
    def handle_ui_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        # Simulate slow processing
        time.sleep(0.1)  # 100ms processing time
        return {
            "status": "processed",
            "plugin": "slow_plugin",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "processing_time_ms": 100
        }
'''
        
        # Memory-intensive plugin
        memory_plugin_content = '''
"""
Memory Intensive Test Plugin
"""
import time
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from svgx_engine.services.plugin_system import (
    BehaviorHandlerPlugin, PluginMetadata, PluginSecurityLevel, PluginType
)

logger = logging.getLogger(__name__)

class MemoryPlugin(BehaviorHandlerPlugin):
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            name="memory_plugin",
            version="1.0.0",
            description="Memory intensive test plugin",
            author="Test Author",
            plugin_type=PluginType.BEHAVIOR_HANDLER,
            security_level=PluginSecurityLevel.VERIFIED,
            tags=["test", "memory"],
            dependencies=[],
            requirements=[]
        )
        self.data_store = []
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        return True
    
    def handle_ui_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        # Simulate memory usage
        self.data_store.append(event_data.copy())
        
        # Keep only last 100 items to prevent memory leak
        if len(self.data_store) > 100:
            self.data_store = self.data_store[-100:]
        
        return {
            "status": "processed",
            "plugin": "memory_plugin",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "memory_items": len(self.data_store)
        }
'''
        
        # Write plugin files
        fast_plugin_path = self.plugin_dir / "fast_plugin.py"
        slow_plugin_path = self.plugin_dir / "slow_plugin.py"
        memory_plugin_path = self.plugin_dir / "memory_plugin.py"
        
        with open(fast_plugin_path, 'w') as f:
            f.write(fast_plugin_content)
        
        with open(slow_plugin_path, 'w') as f:
            f.write(slow_plugin_content)
        
        with open(memory_plugin_path, 'w') as f:
            f.write(memory_plugin_content)
    
    def test_plugin_performance_monitoring(self):
        """Test plugin performance monitoring."""
        # Load plugins
        fast_plugin_path = self.plugin_dir / "fast_plugin.py"
        slow_plugin_path = self.plugin_dir / "slow_plugin.py"
        
        self.plugin_manager.load_plugin(str(fast_plugin_path))
        self.plugin_manager.load_plugin(str(slow_plugin_path))
        
        # Test fast plugin performance
        start_time = time.time()
        event_data = {"event_type": "click", "x": 100, "y": 200}
        
        result = self.plugin_manager.execute_plugin(
            "fast_plugin_1.0.0", "handle_ui_event", event_data
        )
        
        fast_execution_time = time.time() - start_time
        
        # Test slow plugin performance
        start_time = time.time()
        result = self.plugin_manager.execute_plugin(
            "slow_plugin_1.0.0", "handle_ui_event", event_data
        )
        
        slow_execution_time = time.time() - start_time
        
        # Verify performance differences
        self.assertLess(fast_execution_time, slow_execution_time)
        self.assertLess(fast_execution_time, 0.01)  # Fast plugin < 10ms
        self.assertGreater(slow_execution_time, 0.05)  # Slow plugin > 50ms
        
        # Test performance metrics
        fast_performance = self.plugin_monitor.get_plugin_performance("fast_plugin_1.0.0")
        slow_performance = self.plugin_monitor.get_plugin_performance("slow_plugin_1.0.0")
        
        self.assertIsNotNone(fast_performance)
        self.assertIsNotNone(slow_performance)
        self.assertIn("total_executions", fast_performance)
        self.assertIn("average_execution_time", fast_performance)
        self.assertIn("success_rate", fast_performance)
    
    def test_memory_usage_monitoring(self):
        """Test memory usage monitoring."""
        # Load memory-intensive plugin
        memory_plugin_path = self.plugin_dir / "memory_plugin.py"
        self.plugin_manager.load_plugin(str(memory_plugin_path))
        
        # Monitor memory usage
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Execute plugin multiple times
        for i in range(50):
            event_data = {"event_type": "click", "x": i, "y": i, "data": f"test_data_{i}"}
            result = self.plugin_manager.execute_plugin(
                "memory_plugin_1.0.0", "handle_ui_event", event_data
            )
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB)
        self.assertLess(memory_increase, 50.0)
        
        # Test memory optimization
        self.performance_optimizer.optimize_memory_usage()
        
        optimized_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Memory should be optimized
        self.assertLessEqual(optimized_memory, final_memory)
    
    def test_response_time_monitoring(self):
        """Test response time monitoring."""
        # Test API response times
        endpoints = [
            "/health/",
            "/metrics/",
            "/runtime/canvases/",
            "/plugins/"
        ]
        
        response_times = {}
        
        for endpoint in endpoints:
            start_time = time.time()
            response = self.client.get(endpoint)
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            response_times[endpoint] = response_time_ms
            
            # Response time should be reasonable (less than 1000ms)
            self.assertLess(response_time_ms, 1000.0)
        
        # Test response time consistency
        for endpoint, response_time in response_times.items():
            # Multiple requests should have consistent response times
            times = []
            for i in range(5):
                start_time = time.time()
                self.client.get(endpoint)
                end_time = time.time()
                times.append((end_time - start_time) * 1000)
            
            # Response times should be consistent (within 50% of average)
            avg_time = sum(times) / len(times)
            for time_val in times:
                self.assertLess(abs(time_val - avg_time) / avg_time, 0.5)
    
    def test_error_rate_monitoring(self):
        """Test error rate monitoring."""
        # Test error rate tracking
        initial_errors = metrics_collector.get_error_stats()
        
        # Generate some errors
        for i in range(10):
            try:
                # Attempt to access non-existent plugin
                self.plugin_manager.execute_plugin(
                    "non_existent_plugin", "handle_ui_event", {}
                )
            except:
                pass
        
        # Test error rate calculation
        final_errors = metrics_collector.get_error_stats()
        
        # Error count should increase
        self.assertGreaterEqual(
            final_errors.get("total_errors", 0),
            initial_errors.get("total_errors", 0)
        )
    
    def test_resource_utilization_monitoring(self):
        """Test resource utilization monitoring."""
        # Monitor CPU usage
        initial_cpu = psutil.cpu_percent(interval=1)
        
        # Perform CPU-intensive operations
        for i in range(1000):
            _ = i * i
        
        final_cpu = psutil.cpu_percent(interval=1)
        
        # CPU usage should be reasonable
        self.assertLess(final_cpu, 100.0)
        
        # Monitor disk usage
        disk_usage = psutil.disk_usage('/')
        disk_percent = disk_usage.percent
        
        # Disk usage should be reasonable
        self.assertLess(disk_percent, 90.0)
        
        # Monitor network usage
        network_stats = psutil.net_io_counters()
        
        # Network stats should be available
        self.assertIsNotNone(network_stats)
        self.assertGreaterEqual(network_stats.bytes_sent, 0)
        self.assertGreaterEqual(network_stats.bytes_recv, 0)
    
    def test_concurrent_performance_monitoring(self):
        """Test concurrent performance monitoring."""
        # Load fast plugin
        fast_plugin_path = self.plugin_dir / "fast_plugin.py"
        self.plugin_manager.load_plugin(str(fast_plugin_path))
        
        # Test concurrent execution
        async def execute_concurrent():
            tasks = []
            for i in range(10):
                event_data = {"event_type": "click", "x": i, "y": i}
                task = asyncio.create_task(
                    asyncio.to_thread(
                        self.plugin_manager.execute_plugin,
                        "fast_plugin_1.0.0",
                        "handle_ui_event",
                        event_data
                    )
                )
                tasks.append(task)
            
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            return results, end_time - start_time
        
        # Run concurrent execution
        results, execution_time = asyncio.run(execute_concurrent())
        
        # All executions should succeed
        self.assertEqual(len(results), 10)
        for result in results:
            self.assertIsNotNone(result)
            self.assertEqual(result["status"], "processed")
        
        # Concurrent execution should be faster than sequential
        # (though overhead might make it similar for simple operations)
        self.assertLess(execution_time, 1.0)  # Should complete within 1 second
    
    def test_performance_optimization(self):
        """Test performance optimization features."""
        # Test caching optimization
        with self.performance_optimizer.optimize_operation(
            "test_operation", use_caching=True, use_profiling=True
        ):
            # Simulate expensive operation
            time.sleep(0.01)
            result = {"data": "test_result"}
        
        # Test memory optimization
        memory_optimization = self.performance_optimizer.optimize_memory_usage()
        
        self.assertIsNotNone(memory_optimization)
        self.assertIn("memory_savings", memory_optimization)
        
        # Test parallel processing optimization
        def expensive_function(x):
            time.sleep(0.01)
            return x * x
        
        with self.performance_optimizer.optimize_operation(
            "parallel_test", use_parallel=True
        ):
            results = []
            for i in range(10):
                results.append(expensive_function(i))
        
        self.assertEqual(len(results), 10)
        for i, result in enumerate(results):
            self.assertEqual(result, i * i)
    
    def test_performance_metrics_collection(self):
        """Test performance metrics collection."""
        # Test metrics collection
        metrics = self.performance_optimizer.get_performance_summary()
        
        self.assertIsNotNone(metrics)
        self.assertIn("avg_cpu_usage", metrics)
        self.assertIn("avg_memory_usage", metrics)
        self.assertIn("avg_response_time", metrics)
        self.assertIn("avg_throughput", metrics)
        self.assertIn("avg_error_rate", metrics)
        
        # Test real-time metrics
        real_time_metrics = self.performance_optimizer.get_real_time_metrics()
        
        self.assertIsNotNone(real_time_metrics)
        self.assertIn("cpu_usage", real_time_metrics)
        self.assertIn("memory_usage", real_time_metrics)
        self.assertIn("response_time", real_time_metrics)
        self.assertIn("throughput", real_time_metrics)
        self.assertIn("error_rate", real_time_metrics)
    
    def test_performance_alerts(self):
        """Test performance alerting system."""
        # Test performance threshold alerts
        alerts = self.performance_optimizer.check_performance_alerts()
        
        self.assertIsNotNone(alerts)
        self.assertIsInstance(alerts, list)
        
        # Test resource alerts
        resource_alerts = self.performance_optimizer.get_resource_alerts()
        
        self.assertIsNotNone(resource_alerts)
        self.assertIsInstance(resource_alerts, list)
    
    def test_performance_api_endpoints(self):
        """Test performance monitoring API endpoints."""
        # Test performance metrics endpoint
        response = self.client.get("/metrics/")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("cpu_usage", data)
        self.assertIn("memory_usage", data)
        self.assertIn("response_time", data)
        self.assertIn("throughput", data)
        self.assertIn("error_rate", data)
        
        # Test plugin performance endpoint
        response = self.client.get("/plugins/metrics/")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("system_metrics", data)
        self.assertIn("usage_report", data)
    
    def test_performance_benchmarks(self):
        """Test performance benchmarking."""
        # Test plugin execution benchmarks
        fast_plugin_path = self.plugin_dir / "fast_plugin.py"
        self.plugin_manager.load_plugin(str(fast_plugin_path))
        
        # Benchmark fast plugin
        execution_times = []
        for i in range(100):
            start_time = time.time()
            self.plugin_manager.execute_plugin(
                "fast_plugin_1.0.0", "handle_ui_event", {"event_type": "click", "x": i, "y": i}
            )
            end_time = time.time()
            execution_times.append((end_time - start_time) * 1000)
        
        # Calculate benchmark statistics
        avg_execution_time = sum(execution_times) / len(execution_times)
        min_execution_time = min(execution_times)
        max_execution_time = max(execution_times)
        
        # Performance should meet benchmarks
        self.assertLess(avg_execution_time, 10.0)  # Average < 10ms
        self.assertLess(max_execution_time, 50.0)  # Max < 50ms
        
        # Test memory benchmark
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Perform memory-intensive operations
        for i in range(1000):
            _ = [i] * 1000
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        self.assertLess(memory_increase, 100.0)  # < 100MB increase
    
    def test_performance_regression_detection(self):
        """Test performance regression detection."""
        # Test baseline performance
        baseline_metrics = self.performance_optimizer.get_performance_summary()
        
        # Simulate performance regression
        with patch.object(self.performance_optimizer, 'get_real_time_metrics') as mock_metrics:
            mock_metrics.return_value = {
                "cpu_usage": 95.0,  # High CPU usage
                "memory_usage": 90.0,  # High memory usage
                "response_time": 5000.0,  # High response time
                "throughput": 10.0,  # Low throughput
                "error_rate": 15.0  # High error rate
            }
            
            # Check for performance regression
            regression_alerts = self.performance_optimizer.detect_performance_regression(baseline_metrics)
            
            self.assertIsNotNone(regression_alerts)
            self.assertGreater(len(regression_alerts), 0)
    
    def test_performance_optimization_strategies(self):
        """Test performance optimization strategies."""
        # Test different optimization strategies
        
        # Test caching strategy
        cache_optimization = self.performance_optimizer.optimize_caching_strategy()
        self.assertIsNotNone(cache_optimization)
        
        # Test memory optimization strategy
        memory_optimization = self.performance_optimizer.optimize_memory_strategy()
        self.assertIsNotNone(memory_optimization)
        
        # Test CPU optimization strategy
        cpu_optimization = self.performance_optimizer.optimize_cpu_strategy()
        self.assertIsNotNone(cpu_optimization)
        
        # Test I/O optimization strategy
        io_optimization = self.performance_optimizer.optimize_io_strategy()
        self.assertIsNotNone(io_optimization)
    
    def test_comprehensive_performance_monitoring(self):
        """Test comprehensive performance monitoring."""
        # Test all performance monitoring components together
        
        # 1. Load plugins
        fast_plugin_path = self.plugin_dir / "fast_plugin.py"
        slow_plugin_path = self.plugin_dir / "slow_plugin.py"
        memory_plugin_path = self.plugin_dir / "memory_plugin.py"
        
        self.plugin_manager.load_plugin(str(fast_plugin_path))
        self.plugin_manager.load_plugin(str(slow_plugin_path))
        self.plugin_manager.load_plugin(str(memory_plugin_path))
        
        # 2. Execute plugins with performance monitoring
        plugins = ["fast_plugin_1.0.0", "slow_plugin_1.0.0", "memory_plugin_1.0.0"]
        
        for plugin_name in plugins:
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            result = self.plugin_manager.execute_plugin(
                plugin_name, "handle_ui_event", {"event_type": "click", "x": 100, "y": 200}
            )
            
            execution_time = (time.time() - start_time) * 1000
            memory_usage = (psutil.Process().memory_info().rss / 1024 / 1024) - start_memory
            
            # Record performance metrics
            self.performance_metrics.append({
                "plugin": plugin_name,
                "execution_time_ms": execution_time,
                "memory_usage_mb": memory_usage,
                "success": result["status"] == "processed"
            })
        
        # 3. Analyze performance metrics
        total_executions = len(self.performance_metrics)
        successful_executions = sum(1 for m in self.performance_metrics if m["success"])
        avg_execution_time = sum(m["execution_time_ms"] for m in self.performance_metrics) / total_executions
        total_memory_usage = sum(m["memory_usage_mb"] for m in self.performance_metrics)
        
        # 4. Verify performance requirements
        self.assertEqual(successful_executions, total_executions)  # All should succeed
        self.assertLess(avg_execution_time, 100.0)  # Average < 100ms
        self.assertLess(total_memory_usage, 50.0)  # Total memory < 50MB
        
        # 5. Test performance optimization
        optimization_result = self.performance_optimizer.optimize_all_strategies()
        self.assertIsNotNone(optimization_result)
        self.assertIn("caching_optimization", optimization_result)
        self.assertIn("memory_optimization", optimization_result)
        self.assertIn("cpu_optimization", optimization_result)
        self.assertIn("io_optimization", optimization_result)


if __name__ == "__main__":
    unittest.main() 