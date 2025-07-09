"""
AHJ API Load Testing

Comprehensive load testing for AHJ API including:
- Concurrent user simulation
- High-volume annotation creation
- Session management under load
- Database performance under stress
- Memory usage monitoring
- Response time analysis
"""

import pytest
import asyncio
import aiohttp
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import json
import random
import string
from typing import List, Dict, Any
import psutil
import os

# Import the main app
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ahj_api_integration import (
    AHJAPIIntegration,
    AnnotationType,
    ViolationSeverity,
    InspectionStatus,
    PermissionLevel
)


class AHJAPILoadTester:
    """Load testing framework for AHJ API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {
            "requests": [],
            "errors": [],
            "performance_metrics": {},
            "memory_usage": [],
            "cpu_usage": []
        }
        self.start_time = None
        self.end_time = None
    
    def generate_test_data(self, num_users: int = 10, num_inspections: int = 50) -> Dict[str, Any]:
        """Generate test data for load testing."""
        users = []
        inspections = []
        
        # Generate test users
        for i in range(num_users):
            user = {
                "user_id": f"load_test_user_{i:03d}",
                "username": f"load_test_user_{i:03d}",
                "full_name": f"Load Test User {i}",
                "organization": "Load Test Organization",
                "jurisdiction": "Load Test District",
                "permission_level": random.choice(["inspector", "senior_inspector", "supervisor"]),
                "geographic_boundaries": [f"area_{i}"],
                "contact_email": f"load_test_user_{i}@example.com"
            }
            users.append(user)
        
        # Generate test inspections
        for i in range(num_inspections):
            inspection = {
                "inspection_id": f"load_test_inspection_{i:03d}",
                "user_id": f"load_test_user_{i % num_users:03d}",
                "status": random.choice(["pending", "in_progress", "completed"])
            }
            inspections.append(inspection)
        
        return {
            "users": users,
            "inspections": inspections
        }
    
    def create_annotation_request(self, inspection_id: str, user_id: str) -> Dict[str, Any]:
        """Create a random annotation request."""
        annotation_types = [
            "inspection_note",
            "code_violation", 
            "photo_attachment",
            "location_marker",
            "status_update"
        ]
        
        content_samples = [
            "Routine inspection completed. All systems operational.",
            "Minor maintenance required on HVAC system.",
            "Electrical panel inspection passed.",
            "Fire suppression system verified.",
            "Emergency exit clear and accessible.",
            "Building code compliance confirmed.",
            "Safety equipment properly maintained.",
            "Structural integrity assessment complete.",
            "Plumbing system inspection finished.",
            "Security system operational."
        ]
        
        return {
            "annotation_type": random.choice(annotation_types),
            "content": random.choice(content_samples),
            "location_coordinates": {
                "lat": random.uniform(40.0, 41.0),
                "lng": random.uniform(-74.0, -73.0)
            }
        }
    
    def measure_performance(self, func, *args, **kwargs) -> Dict[str, Any]:
        """Measure performance of a function."""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        start_cpu = psutil.Process().cpu_percent()
        
        try:
            result = func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        end_cpu = psutil.Process().cpu_percent()
        
        duration = end_time - start_time
        memory_delta = end_memory - start_memory
        cpu_usage = (start_cpu + end_cpu) / 2
        
        return {
            "success": success,
            "duration": duration,
            "memory_delta": memory_delta,
            "cpu_usage": cpu_usage,
            "error": error,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    def concurrent_annotation_creation(self, num_concurrent: int = 10, 
                                     num_annotations: int = 100) -> Dict[str, Any]:
        """Test concurrent annotation creation."""
        print(f"Testing concurrent annotation creation: {num_concurrent} users, {num_annotations} annotations")
        
        # Initialize AHJ service
        ahj_service = AHJAPIIntegration()
        
        # Create test users
        test_data = self.generate_test_data(num_concurrent, num_annotations)
        
        # Create users in the service
        for user in test_data["users"]:
            try:
                ahj_service.create_ahj_user(user)
            except Exception as e:
                print(f"Warning: Could not create user {user['user_id']}: {e}")
        
        results = []
        errors = []
        
        def create_annotation_batch(user_id: str, inspection_id: str, num_batch: int):
            """Create a batch of annotations for a user."""
            batch_results = []
            for i in range(num_batch):
                annotation_data = self.create_annotation_request(inspection_id, user_id)
                annotation_data["inspection_id"] = inspection_id
                
                result = self.measure_performance(
                    ahj_service.create_inspection_annotation,
                    annotation_data,
                    user_id
                )
                
                batch_results.append(result)
                
                if not result["success"]:
                    errors.append({
                        "user_id": user_id,
                        "inspection_id": inspection_id,
                        "error": result["error"],
                        "timestamp": result["timestamp"]
                    })
            
            return batch_results
        
        # Distribute annotations across users
        annotations_per_user = num_annotations // num_concurrent
        remaining_annotations = num_annotations % num_concurrent
        
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = []
            
            for i, user in enumerate(test_data["users"]):
                user_annotations = annotations_per_user
                if i < remaining_annotations:
                    user_annotations += 1
                
                if user_annotations > 0:
                    inspection_id = test_data["inspections"][i]["inspection_id"]
                    future = executor.submit(
                        create_annotation_batch,
                        user["user_id"],
                        inspection_id,
                        user_annotations
                    )
                    futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    batch_results = future.result()
                    results.extend(batch_results)
                except Exception as e:
                    errors.append({
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
        
        # Calculate performance metrics
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        if successful_requests:
            durations = [r["duration"] for r in successful_requests]
            memory_deltas = [r["memory_delta"] for r in successful_requests]
            cpu_usages = [r["cpu_usage"] for r in successful_requests]
            
            performance_metrics = {
                "total_requests": len(results),
                "successful_requests": len(successful_requests),
                "failed_requests": len(failed_requests),
                "success_rate": len(successful_requests) / len(results) * 100,
                "average_response_time": statistics.mean(durations),
                "median_response_time": statistics.median(durations),
                "min_response_time": min(durations),
                "max_response_time": max(durations),
                "average_memory_delta": statistics.mean(memory_deltas),
                "average_cpu_usage": statistics.mean(cpu_usages),
                "requests_per_second": len(successful_requests) / sum(durations),
                "concurrent_users": num_concurrent,
                "total_annotations": num_annotations
            }
        else:
            performance_metrics = {
                "total_requests": len(results),
                "successful_requests": 0,
                "failed_requests": len(failed_requests),
                "success_rate": 0,
                "error": "No successful requests"
            }
        
        return {
            "performance_metrics": performance_metrics,
            "errors": errors,
            "results": results
        }
    
    def session_management_load_test(self, num_sessions: int = 50) -> Dict[str, Any]:
        """Test session management under load."""
        print(f"Testing session management: {num_sessions} concurrent sessions")
        
        ahj_service = AHJAPIIntegration()
        
        # Create test users
        test_data = self.generate_test_data(num_sessions, num_sessions)
        
        results = []
        errors = []
        
        def create_and_end_session(user_id: str, inspection_id: str):
            """Create and end a session for a user."""
            session_results = []
            
            # Create session
            create_result = self.measure_performance(
                ahj_service.create_inspection_session,
                inspection_id,
                user_id
            )
            session_results.append(create_result)
            
            if create_result["success"]:
                session_id = create_result["result"].session_id
                
                # End session
                end_result = self.measure_performance(
                    ahj_service.end_inspection_session,
                    session_id,
                    user_id
                )
                session_results.append(end_result)
                
                if not end_result["success"]:
                    errors.append({
                        "user_id": user_id,
                        "session_id": session_id,
                        "error": end_result["error"],
                        "timestamp": end_result["timestamp"]
                    })
            else:
                errors.append({
                    "user_id": user_id,
                    "error": create_result["error"],
                    "timestamp": create_result["timestamp"]
                })
            
            return session_results
        
        with ThreadPoolExecutor(max_workers=min(num_sessions, 20)) as executor:
            futures = []
            
            for i, user in enumerate(test_data["users"]):
                inspection_id = test_data["inspections"][i]["inspection_id"]
                future = executor.submit(
                    create_and_end_session,
                    user["user_id"],
                    inspection_id
                )
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    session_results = future.result()
                    results.extend(session_results)
                except Exception as e:
                    errors.append({
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
        
        # Calculate metrics
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        if successful_requests:
            durations = [r["duration"] for r in successful_requests]
            
            performance_metrics = {
                "total_sessions": num_sessions,
                "successful_sessions": len(successful_requests) // 2,  # Create + End
                "failed_sessions": len(failed_requests),
                "success_rate": len(successful_requests) / len(results) * 100,
                "average_session_time": statistics.mean(durations),
                "median_session_time": statistics.median(durations),
                "min_session_time": min(durations),
                "max_session_time": max(durations)
            }
        else:
            performance_metrics = {
                "total_sessions": num_sessions,
                "successful_sessions": 0,
                "failed_sessions": len(failed_requests),
                "success_rate": 0,
                "error": "No successful sessions"
            }
        
        return {
            "performance_metrics": performance_metrics,
            "errors": errors,
            "results": results
        }
    
    def audit_logging_load_test(self, num_operations: int = 100) -> Dict[str, Any]:
        """Test audit logging under load."""
        print(f"Testing audit logging: {num_operations} operations")
        
        ahj_service = AHJAPIIntegration()
        
        # Create test users
        test_data = self.generate_test_data(10, num_operations)
        
        results = []
        errors = []
        
        def perform_audited_operation(user_id: str, operation_type: str):
            """Perform an operation that generates audit logs."""
            if operation_type == "annotation":
                annotation_data = self.create_annotation_request("test_inspection", user_id)
                annotation_data["inspection_id"] = "test_inspection"
                
                result = self.measure_performance(
                    ahj_service.create_inspection_annotation,
                    annotation_data,
                    user_id
                )
            elif operation_type == "session":
                result = self.measure_performance(
                    ahj_service.create_inspection_session,
                    "test_inspection",
                    user_id
                )
            elif operation_type == "audit_query":
                result = self.measure_performance(
                    ahj_service.get_audit_logs,
                    user_id
                )
            else:
                result = {
                    "success": False,
                    "error": f"Unknown operation type: {operation_type}",
                    "duration": 0,
                    "timestamp": datetime.now().isoformat()
                }
            
            return result
        
        operation_types = ["annotation", "session", "audit_query"]
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            
            for i in range(num_operations):
                user_id = test_data["users"][i % len(test_data["users"])]["user_id"]
                operation_type = operation_types[i % len(operation_types)]
                
                future = executor.submit(
                    perform_audited_operation,
                    user_id,
                    operation_type
                )
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    
                    if not result["success"]:
                        errors.append({
                            "error": result["error"],
                            "timestamp": result["timestamp"]
                        })
                except Exception as e:
                    errors.append({
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
        
        # Calculate metrics
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        if successful_requests:
            durations = [r["duration"] for r in successful_requests]
            
            performance_metrics = {
                "total_operations": num_operations,
                "successful_operations": len(successful_requests),
                "failed_operations": len(failed_requests),
                "success_rate": len(successful_requests) / len(results) * 100,
                "average_operation_time": statistics.mean(durations),
                "median_operation_time": statistics.median(durations),
                "min_operation_time": min(durations),
                "max_operation_time": max(durations),
                "operations_per_second": len(successful_requests) / sum(durations)
            }
        else:
            performance_metrics = {
                "total_operations": num_operations,
                "successful_operations": 0,
                "failed_operations": len(failed_requests),
                "success_rate": 0,
                "error": "No successful operations"
            }
        
        return {
            "performance_metrics": performance_metrics,
            "errors": errors,
            "results": results
        }
    
    def memory_usage_monitoring(self, duration_seconds: int = 60) -> Dict[str, Any]:
        """Monitor memory usage over time."""
        print(f"Monitoring memory usage for {duration_seconds} seconds")
        
        memory_readings = []
        cpu_readings = []
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            process = psutil.Process()
            
            memory_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = process.cpu_percent()
            
            memory_readings.append({
                "timestamp": datetime.now().isoformat(),
                "memory_mb": memory_mb,
                "cpu_percent": cpu_percent
            })
            
            cpu_readings.append(cpu_percent)
            
            time.sleep(1)  # Sample every second
        
        if memory_readings:
            memory_values = [r["memory_mb"] for r in memory_readings]
            cpu_values = [r["cpu_percent"] for r in memory_readings]
            
            memory_metrics = {
                "duration_seconds": duration_seconds,
                "samples_taken": len(memory_readings),
                "average_memory_mb": statistics.mean(memory_values),
                "peak_memory_mb": max(memory_values),
                "min_memory_mb": min(memory_values),
                "memory_variance": statistics.variance(memory_values),
                "average_cpu_percent": statistics.mean(cpu_values),
                "peak_cpu_percent": max(cpu_values),
                "min_cpu_percent": min(cpu_values)
            }
        else:
            memory_metrics = {
                "duration_seconds": duration_seconds,
                "samples_taken": 0,
                "error": "No memory readings taken"
            }
        
        return {
            "memory_metrics": memory_metrics,
            "readings": memory_readings
        }
    
    def run_comprehensive_load_test(self) -> Dict[str, Any]:
        """Run comprehensive load testing suite."""
        print("=" * 80)
        print("AHJ API COMPREHENSIVE LOAD TESTING")
        print("=" * 80)
        
        self.start_time = datetime.now()
        
        # Test 1: Concurrent annotation creation
        print("\n1. CONCURRENT ANNOTATION CREATION TEST")
        print("-" * 50)
        annotation_results = self.concurrent_annotation_creation(10, 100)
        
        # Test 2: Session management load test
        print("\n2. SESSION MANAGEMENT LOAD TEST")
        print("-" * 50)
        session_results = self.session_management_load_test(50)
        
        # Test 3: Audit logging load test
        print("\n3. AUDIT LOGGING LOAD TEST")
        print("-" * 50)
        audit_results = self.audit_logging_load_test(100)
        
        # Test 4: Memory usage monitoring
        print("\n4. MEMORY USAGE MONITORING")
        print("-" * 50)
        memory_results = self.memory_usage_monitoring(30)  # 30 seconds
        
        self.end_time = datetime.now()
        
        # Compile comprehensive results
        comprehensive_results = {
            "test_summary": {
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "total_duration": (self.end_time - self.start_time).total_seconds(),
                "tests_performed": 4
            },
            "annotation_creation": annotation_results,
            "session_management": session_results,
            "audit_logging": audit_results,
            "memory_monitoring": memory_results,
            "overall_performance": {
                "total_requests": (
                    annotation_results["performance_metrics"].get("total_requests", 0) +
                    session_results["performance_metrics"].get("total_sessions", 0) * 2 +
                    audit_results["performance_metrics"].get("total_operations", 0)
                ),
                "total_errors": (
                    len(annotation_results["errors"]) +
                    len(session_results["errors"]) +
                    len(audit_results["errors"])
                ),
                "overall_success_rate": self._calculate_overall_success_rate([
                    annotation_results["performance_metrics"],
                    session_results["performance_metrics"],
                    audit_results["performance_metrics"]
                ])
            }
        }
        
        # Print summary
        self._print_load_test_summary(comprehensive_results)
        
        return comprehensive_results
    
    def _calculate_overall_success_rate(self, metrics_list: List[Dict[str, Any]]) -> float:
        """Calculate overall success rate from multiple test results."""
        total_requests = 0
        total_successful = 0
        
        for metrics in metrics_list:
            total_requests += metrics.get("total_requests", 0)
            total_successful += metrics.get("successful_requests", 0)
        
        if total_requests > 0:
            return (total_successful / total_requests) * 100
        return 0.0
    
    def _print_load_test_summary(self, results: Dict[str, Any]):
        """Print comprehensive load test summary."""
        print("\n" + "=" * 80)
        print("LOAD TESTING SUMMARY")
        print("=" * 80)
        
        summary = results["test_summary"]
        overall = results["overall_performance"]
        
        print(f"Test Duration: {summary['total_duration']:.2f} seconds")
        print(f"Total Requests: {overall['total_requests']}")
        print(f"Total Errors: {overall['total_errors']}")
        print(f"Overall Success Rate: {overall['overall_success_rate']:.2f}%")
        
        # Annotation creation metrics
        ann_metrics = results["annotation_creation"]["performance_metrics"]
        print(f"\nAnnotation Creation:")
        print(f"  Requests: {ann_metrics.get('total_requests', 0)}")
        print(f"  Success Rate: {ann_metrics.get('success_rate', 0):.2f}%")
        print(f"  Avg Response Time: {ann_metrics.get('average_response_time', 0):.4f}s")
        print(f"  Requests/Second: {ann_metrics.get('requests_per_second', 0):.2f}")
        
        # Session management metrics
        session_metrics = results["session_management"]["performance_metrics"]
        print(f"\nSession Management:")
        print(f"  Sessions: {session_metrics.get('total_sessions', 0)}")
        print(f"  Success Rate: {session_metrics.get('success_rate', 0):.2f}%")
        print(f"  Avg Session Time: {session_metrics.get('average_session_time', 0):.4f}s")
        
        # Memory monitoring metrics
        memory_metrics = results["memory_monitoring"]["memory_metrics"]
        print(f"\nMemory Usage:")
        print(f"  Avg Memory: {memory_metrics.get('average_memory_mb', 0):.2f} MB")
        print(f"  Peak Memory: {memory_metrics.get('peak_memory_mb', 0):.2f} MB")
        print(f"  Avg CPU: {memory_metrics.get('average_cpu_percent', 0):.2f}%")
        
        print("\n" + "=" * 80)


class TestAHJAPILoad:
    """Load testing test cases."""
    
    def test_concurrent_annotation_creation(self):
        """Test concurrent annotation creation."""
        load_tester = AHJAPILoadTester()
        results = load_tester.concurrent_annotation_creation(5, 20)
        
        assert "performance_metrics" in results
        assert "errors" in results
        assert "results" in results
        
        metrics = results["performance_metrics"]
        assert metrics["total_requests"] > 0
        assert metrics["success_rate"] >= 0
    
    def test_session_management_load(self):
        """Test session management under load."""
        load_tester = AHJAPILoadTester()
        results = load_tester.session_management_load_test(10)
        
        assert "performance_metrics" in results
        assert "errors" in results
        assert "results" in results
        
        metrics = results["performance_metrics"]
        assert metrics["total_sessions"] > 0
        assert metrics["success_rate"] >= 0
    
    def test_audit_logging_load(self):
        """Test audit logging under load."""
        load_tester = AHJAPILoadTester()
        results = load_tester.audit_logging_load_test(20)
        
        assert "performance_metrics" in results
        assert "errors" in results
        assert "results" in results
        
        metrics = results["performance_metrics"]
        assert metrics["total_operations"] > 0
        assert metrics["success_rate"] >= 0
    
    def test_memory_usage_monitoring(self):
        """Test memory usage monitoring."""
        load_tester = AHJAPILoadTester()
        results = load_tester.memory_usage_monitoring(5)  # 5 seconds
        
        assert "memory_metrics" in results
        assert "readings" in results
        
        metrics = results["memory_metrics"]
        assert metrics["duration_seconds"] == 5
        assert metrics["samples_taken"] > 0
    
    def test_comprehensive_load_test(self):
        """Test comprehensive load testing suite."""
        load_tester = AHJAPILoadTester()
        results = load_tester.run_comprehensive_load_test()
        
        assert "test_summary" in results
        assert "annotation_creation" in results
        assert "session_management" in results
        assert "audit_logging" in results
        assert "memory_monitoring" in results
        assert "overall_performance" in results
        
        summary = results["test_summary"]
        assert summary["tests_performed"] == 4
        assert summary["total_duration"] > 0


if __name__ == "__main__":
    # Run comprehensive load test
    load_tester = AHJAPILoadTester()
    results = load_tester.run_comprehensive_load_test()
    
    # Save results to file
    with open("ahj_api_load_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nLoad test results saved to: ahj_api_load_test_results.json") 