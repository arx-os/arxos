#!/usr/bin/env python3
"""
Performance tests for SDKs
Tests response times, concurrent requests, memory usage, and load testing
"""

import pytest
import time
import psutil
import threading
import concurrent.futures
import statistics
from pathlib import Path
from typing import Dict, Any, List
import requests
import json

class TestSDKPerformance:
    """Performance test suite for SDKs"""
    
    @pytest.fixture
    def performance_config(self):
        """Performance test configuration"""
        return {
            "base_url": "http://localhost:8080",
            "concurrent_users": 10,
            "requests_per_user": 100,
            "timeout": 30,
            "max_response_time": 5.0,
            "max_memory_usage": 100 * 1024 * 1024,  # 100MB
            "load_test_duration": 60,  # 60 seconds
            "target_rps": 100  # requests per second
        }
    
    def test_response_time_performance(self, performance_config):
        """Test API response time performance"""
        try:
            response_times = []
            
            # Make 100 requests and measure response times
            for i in range(100):
                start_time = time.time()
                
                response = requests.get(
                    f"{performance_config['base_url']}/api/health",
                    timeout=performance_config['timeout']
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                response_times.append(response_time)
                
                assert response.status_code == 200, f"Request {i} failed: {response.status_code}"
            
            # Calculate statistics
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
            
            # Assertions
            assert avg_response_time < performance_config['max_response_time'], \
                f"Average response time {avg_response_time:.3f}s exceeds {performance_config['max_response_time']}s"
            
            assert p95_response_time < performance_config['max_response_time'] * 2, \
                f"95th percentile response time {p95_response_time:.3f}s too high"
            
            assert p99_response_time < performance_config['max_response_time'] * 3, \
                f"99th percentile response time {p99_response_time:.3f}s too high"
            
            print(f"Response Time Performance:")
            print(f"  Average: {avg_response_time:.3f}s")
            print(f"  Median: {median_response_time:.3f}s")
            print(f"  95th percentile: {p95_response_time:.3f}s")
            print(f"  99th percentile: {p99_response_time:.3f}s")
            
        except requests.RequestException as e:
            pytest.skip(f"Performance test not available: {e}")
    
    def test_concurrent_requests_performance(self, performance_config):
        """Test concurrent request performance"""
        try:
            def make_request():
                """Make a single request and return response time"""
                start_time = time.time()
                response = requests.get(
                    f"{performance_config['base_url']}/api/health",
                    timeout=performance_config['timeout']
                )
                end_time = time.time()
                
                return {
                    'response_time': end_time - start_time,
                    'status_code': response.status_code,
                    'success': response.status_code == 200
                }
            
            # Run concurrent requests
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=performance_config['concurrent_users']
            ) as executor:
                futures = [
                    executor.submit(make_request) 
                    for _ in range(performance_config['concurrent_users'] * performance_config['requests_per_user'])
                ]
                
                results = [future.result() for future in futures]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Calculate statistics
            response_times = [r['response_time'] for r in results]
            success_count = sum(1 for r in results if r['success'])
            total_requests = len(results)
            
            avg_response_time = statistics.mean(response_times)
            requests_per_second = total_requests / total_time
            
            # Assertions
            assert success_count == total_requests, f"All {total_requests} requests should succeed, got {success_count}"
            
            assert avg_response_time < performance_config['max_response_time'], \
                f"Average concurrent response time {avg_response_time:.3f}s exceeds {performance_config['max_response_time']}s"
            
            assert requests_per_second >= performance_config['target_rps'] * 0.8, \
                f"Requests per second {requests_per_second:.1f} below target {performance_config['target_rps']}"
            
            print(f"Concurrent Request Performance:")
            print(f"  Total requests: {total_requests}")
            print(f"  Successful requests: {success_count}")
            print(f"  Total time: {total_time:.3f}s")
            print(f"  Average response time: {avg_response_time:.3f}s")
            print(f"  Requests per second: {requests_per_second:.1f}")
            
        except requests.RequestException as e:
            pytest.skip(f"Concurrent performance test not available: {e}")
    
    def test_memory_usage_performance(self, performance_config):
        """Test memory usage during API operations"""
        try:
            process = psutil.Process()
            initial_memory = process.memory_info().rss
            
            # Make many requests to test memory usage
            for i in range(1000):
                response = requests.get(
                    f"{performance_config['base_url']}/api/health",
                    timeout=performance_config['timeout']
                )
                
                assert response.status_code == 200, f"Request {i} failed"
                
                # Check memory every 100 requests
                if i % 100 == 0:
                    current_memory = process.memory_info().rss
                    memory_increase = current_memory - initial_memory
                    
                    # Memory should not increase excessively
                    assert memory_increase < performance_config['max_memory_usage'], \
                        f"Memory increase {memory_increase / 1024 / 1024:.1f}MB exceeds limit"
            
            final_memory = process.memory_info().rss
            total_memory_increase = final_memory - initial_memory
            
            print(f"Memory Usage Performance:")
            print(f"  Initial memory: {initial_memory / 1024 / 1024:.1f}MB")
            print(f"  Final memory: {final_memory / 1024 / 1024:.1f}MB")
            print(f"  Total increase: {total_memory_increase / 1024 / 1024:.1f}MB")
            
            assert total_memory_increase < performance_config['max_memory_usage'], \
                f"Total memory increase {total_memory_increase / 1024 / 1024:.1f}MB exceeds limit"
                
        except requests.RequestException as e:
            pytest.skip(f"Memory usage test not available: {e}")
    
    def test_load_testing(self, performance_config):
        """Test sustained load over time"""
        try:
            def load_worker(worker_id: int, duration: int, target_rps: int):
                """Worker function for load testing"""
                start_time = time.time()
                request_count = 0
                response_times = []
                
                while time.time() - start_time < duration:
                    request_start = time.time()
                    
                    try:
                        response = requests.get(
                            f"{performance_config['base_url']}/api/health",
                            timeout=performance_config['timeout']
                        )
                        
                        request_end = time.time()
                        response_time = request_end - request_start
                        response_times.append(response_time)
                        
                        if response.status_code == 200:
                            request_count += 1
                        
                        # Control request rate
                        time.sleep(1.0 / target_rps)
                        
                    except requests.RequestException:
                        continue
                
                return {
                    'worker_id': worker_id,
                    'request_count': request_count,
                    'response_times': response_times,
                    'duration': time.time() - start_time
                }
            
            # Start load test
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=performance_config['concurrent_users']
            ) as executor:
                futures = [
                    executor.submit(
                        load_worker, 
                        i, 
                        performance_config['load_test_duration'],
                        performance_config['target_rps'] // performance_config['concurrent_users']
                    )
                    for i in range(performance_config['concurrent_users'])
                ]
                
                results = [future.result() for future in futures]
            
            end_time = time.time()
            total_duration = end_time - start_time
            
            # Calculate load test statistics
            total_requests = sum(r['request_count'] for r in results)
            all_response_times = []
            for r in results:
                all_response_times.extend(r['response_times'])
            
            avg_response_time = statistics.mean(all_response_times) if all_response_times else 0
            p95_response_time = statistics.quantiles(all_response_times, n=20)[18] if len(all_response_times) >= 20 else 0
            requests_per_second = total_requests / total_duration
            
            # Assertions
            assert total_requests > 0, "Should make requests during load test"
            
            assert avg_response_time < performance_config['max_response_time'], \
                f"Load test average response time {avg_response_time:.3f}s exceeds limit"
            
            assert requests_per_second >= performance_config['target_rps'] * 0.7, \
                f"Load test RPS {requests_per_second:.1f} below target {performance_config['target_rps']}"
            
            print(f"Load Test Performance:")
            print(f"  Duration: {total_duration:.1f}s")
            print(f"  Total requests: {total_requests}")
            print(f"  Requests per second: {requests_per_second:.1f}")
            print(f"  Average response time: {avg_response_time:.3f}s")
            print(f"  95th percentile response time: {p95_response_time:.3f}s")
            
        except requests.RequestException as e:
            pytest.skip(f"Load test not available: {e}")
    
    def test_authentication_performance(self, performance_config):
        """Test authentication performance"""
        try:
            auth_times = []
            
            # Test authentication performance
            for i in range(50):
                start_time = time.time()
                
                response = requests.post(
                    f"{performance_config['base_url']}/api/auth/login",
                    json={
                        "username": "test-user",
                        "password": "test-password"
                    },
                    timeout=performance_config['timeout']
                )
                
                end_time = time.time()
                auth_time = end_time - start_time
                auth_times.append(auth_time)
                
                # Don't fail on auth errors, just measure time
                if response.status_code != 200:
                    print(f"Auth request {i} failed: {response.status_code}")
            
            if auth_times:
                avg_auth_time = statistics.mean(auth_times)
                max_auth_time = max(auth_times)
                
                print(f"Authentication Performance:")
                print(f"  Average auth time: {avg_auth_time:.3f}s")
                print(f"  Max auth time: {max_auth_time:.3f}s")
                
                assert avg_auth_time < performance_config['max_response_time'] * 2, \
                    f"Average auth time {avg_auth_time:.3f}s too high"
                    
        except requests.RequestException as e:
            pytest.skip(f"Authentication performance test not available: {e}")
    
    def test_database_query_performance(self, performance_config):
        """Test database query performance"""
        try:
            query_times = []
            
            # Test database query performance
            for i in range(100):
                start_time = time.time()
                
                response = requests.get(
                    f"{performance_config['base_url']}/api/projects",
                    timeout=performance_config['timeout']
                )
                
                end_time = time.time()
                query_time = end_time - start_time
                query_times.append(query_time)
                
                # Don't fail on auth errors, just measure time
                if response.status_code not in [200, 401]:
                    print(f"Query request {i} failed: {response.status_code}")
            
            if query_times:
                avg_query_time = statistics.mean(query_times)
                p95_query_time = statistics.quantiles(query_times, n=20)[18] if len(query_times) >= 20 else 0
                
                print(f"Database Query Performance:")
                print(f"  Average query time: {avg_query_time:.3f}s")
                print(f"  95th percentile query time: {p95_query_time:.3f}s")
                
                assert avg_query_time < performance_config['max_response_time'] * 1.5, \
                    f"Average query time {avg_query_time:.3f}s too high"
                    
        except requests.RequestException as e:
            pytest.skip(f"Database query performance test not available: {e}")
    
    def test_file_upload_performance(self, performance_config):
        """Test file upload performance"""
        try:
            # Create test file content
            test_content = "Test file content for performance testing" * 1000
            
            upload_times = []
            
            # Test file upload performance
            for i in range(20):
                start_time = time.time()
                
                response = requests.post(
                    f"{performance_config['base_url']}/api/files/upload",
                    files={"file": ("test.txt", test_content, "text/plain")},
                    timeout=performance_config['timeout']
                )
                
                end_time = time.time()
                upload_time = end_time - start_time
                upload_times.append(upload_time)
                
                # Don't fail on auth errors, just measure time
                if response.status_code not in [201, 401]:
                    print(f"Upload request {i} failed: {response.status_code}")
            
            if upload_times:
                avg_upload_time = statistics.mean(upload_times)
                max_upload_time = max(upload_times)
                
                print(f"File Upload Performance:")
                print(f"  Average upload time: {avg_upload_time:.3f}s")
                print(f"  Max upload time: {max_upload_time:.3f}s")
                
                assert avg_upload_time < performance_config['max_response_time'] * 3, \
                    f"Average upload time {avg_upload_time:.3f}s too high"
                    
        except requests.RequestException as e:
            pytest.skip(f"File upload performance test not available: {e}")
    
    def test_error_recovery_performance(self, performance_config):
        """Test error recovery performance"""
        try:
            recovery_times = []
            
            # Test error recovery by making invalid requests followed by valid ones
            for i in range(20):
                # Make invalid request
                try:
                    requests.get(
                        f"{performance_config['base_url']}/api/invalid-endpoint",
                        timeout=5
                    )
                except:
                    pass
                
                # Measure recovery time
                start_time = time.time()
                
                response = requests.get(
                    f"{performance_config['base_url']}/api/health",
                    timeout=performance_config['timeout']
                )
                
                end_time = time.time()
                recovery_time = end_time - start_time
                recovery_times.append(recovery_time)
                
                assert response.status_code == 200, f"Recovery request {i} failed"
            
            if recovery_times:
                avg_recovery_time = statistics.mean(recovery_times)
                max_recovery_time = max(recovery_times)
                
                print(f"Error Recovery Performance:")
                print(f"  Average recovery time: {avg_recovery_time:.3f}s")
                print(f"  Max recovery time: {max_recovery_time:.3f}s")
                
                assert avg_recovery_time < performance_config['max_response_time'] * 1.5, \
                    f"Average recovery time {avg_recovery_time:.3f}s too high"
                    
        except requests.RequestException as e:
            pytest.skip(f"Error recovery performance test not available: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 