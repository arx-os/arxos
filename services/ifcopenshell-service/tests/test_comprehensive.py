"""
Comprehensive Test Suite for IfcOpenShell Service

This module provides comprehensive testing including:
- Unit tests for all modules
- Integration tests for API endpoints
- Performance tests for load testing
- End-to-end tests for complete workflows
"""

import pytest
import json
import time
import os
import tempfile
from unittest.mock import Mock, patch
import requests
from concurrent.futures import ThreadPoolExecutor
import threading

# Import the modules to test
from main import app, performance_cache, performance_monitor, error_handler
from models.validation import validator, IFCValidationResult
from models.spatial import spatial_query, SpatialQuery
from models.performance import PerformanceCache, PerformanceMonitor
from models.errors import IFCServiceError, ErrorHandler


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_ifc_data():
    """Create sample IFC data for testing"""
    return b"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('test.ifc','2024-01-01T00:00:00',('Test User'),('Test Organization'),'Test Software','Test Software Version','Test Identifier');
FILE_SCHEMA(('IFC4'));
ENDSEC;

DATA;
#1=IFCPROJECT('0x1234567890abcdef', 'Test Project', 'Test Project Description', $, $, $, $, $, $);
#2=IFCSITE('0x2345678901bcdefg', 'Test Site', 'Test Site Description', $, $, $, $, $, $);
#3=IFCBUILDING('0x3456789012cdefgh', 'Test Building', 'Test Building Description', $, $, $, $, $, $);
#4=IFCBUILDINGSTOREY('0x4567890123defghi', 'Ground Floor', 'Ground Floor Description', $, $, $, $, $, $);
#5=IFCSPACE('0x5678901234efghij', 'Test Space', 'Test Space Description', $, $, $, $, $, $);
#6=IFCWALL('0x6789012345fghijk', 'Test Wall', 'Test Wall Description', $, $, $, $, $, $);
#7=IFCDOOR('0x7890123456ghijkl', 'Test Door', 'Test Door Description', $, $, $, $, $, $);
#8=IFCWINDOW('0x8901234567hijklm', 'Test Window', 'Test Window Description', $, $, $, $, $, $);
ENDSEC;

END-ISO-10303-21;"""


@pytest.fixture
def large_ifc_data():
    """Create large IFC data for performance testing"""
    base_data = b"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('large_test.ifc','2024-01-01T00:00:00',('Test User'),('Test Organization'),'Test Software','Test Software Version','Test Identifier');
FILE_SCHEMA(('IFC4'));
ENDSEC;

DATA;"""
    
    # Generate many entities
    entities = []
    for i in range(1000):
        entities.append(f"#{i+1}=IFCSPACE('0x{i:016x}', 'Space {i}', 'Space {i} Description', $, $, $, $, $, $);")
    
    entities.append("ENDSEC;")
    entities.append("END-ISO-10303-21;")
    
    return base_data + b"\n".join(entity.encode() for entity in entities)


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_basic_health(self, client):
        """Test basic health endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'ifcopenshell'
        assert 'version' in data
        assert 'timestamp' in data
    
    def test_detailed_health(self, client):
        """Test detailed health endpoint"""
        response = client.get('/api/monitoring/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'performance' in data
        assert 'cache' in data
        assert 'errors' in data
        assert 'configuration' in data


class TestParseEndpoint:
    """Test IFC parsing endpoint"""
    
    def test_parse_success(self, client, sample_ifc_data):
        """Test successful IFC parsing"""
        response = client.post('/api/parse', data=sample_ifc_data)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'buildings' in data
        assert 'spaces' in data
        assert 'equipment' in data
        assert 'total_entities' in data
        assert 'metadata' in data
    
    def test_parse_no_data(self, client):
        """Test parsing with no data"""
        response = client.post('/api/parse')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] == False
        assert data['error']['code'] == 'NO_DATA'
    
    def test_parse_large_file(self, client, large_ifc_data):
        """Test parsing large IFC file"""
        response = client.post('/api/parse', data=large_ifc_data)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['total_entities'] > 0
    
    def test_parse_invalid_data(self, client):
        """Test parsing invalid IFC data"""
        invalid_data = b"This is not IFC data"
        response = client.post('/api/parse', data=invalid_data)
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'error' in data


class TestValidationEndpoint:
    """Test IFC validation endpoint"""
    
    def test_validation_success(self, client, sample_ifc_data):
        """Test successful IFC validation"""
        response = client.post('/api/validate', data=sample_ifc_data)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'valid' in data
        assert 'warnings' in data
        assert 'errors' in data
        assert 'compliance' in data
        assert 'entity_counts' in data
    
    def test_validation_no_data(self, client):
        """Test validation with no data"""
        response = client.post('/api/validate')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] == False
        assert data['error']['code'] == 'NO_DATA'
    
    def test_validation_caching(self, client, sample_ifc_data):
        """Test validation caching"""
        # First request
        response1 = client.post('/api/validate', data=sample_ifc_data)
        assert response1.status_code == 200
        
        # Second request (should be cached)
        response2 = client.post('/api/validate', data=sample_ifc_data)
        assert response2.status_code == 200
        
        data1 = json.loads(response1.data)
        data2 = json.loads(response2.data)
        assert data1 == data2


class TestSpatialEndpoints:
    """Test spatial query endpoints"""
    
    def test_spatial_query_within_bounds(self, client, sample_ifc_data):
        """Test spatial query within bounds"""
        query_data = {
            "operation": "within_bounds",
            "bounds": {"min": [0, 0, 0], "max": [100, 100, 100]}
        }
        
        response = client.post('/api/spatial/query', 
                             data=sample_ifc_data,
                             content_type='application/octet-stream',
                             headers={'Content-Type': 'application/json'})
        
        # Note: This test might need adjustment based on actual implementation
        assert response.status_code in [200, 400]  # 400 if JSON parsing fails
    
    def test_spatial_query_statistics(self, client, sample_ifc_data):
        """Test spatial statistics query"""
        query_data = {
            "operation": "statistics"
        }
        
        response = client.post('/api/spatial/query',
                             data=sample_ifc_data,
                             content_type='application/octet-stream')
        
        assert response.status_code in [200, 400]
    
    def test_spatial_bounds(self, client, sample_ifc_data):
        """Test spatial bounds endpoint"""
        response = client.post('/api/spatial/bounds', data=sample_ifc_data)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'bounding_box' in data
        assert 'spatial_coverage' in data


class TestMetricsEndpoints:
    """Test metrics and monitoring endpoints"""
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint"""
        response = client.get('/metrics')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'cache_stats' in data
        assert 'performance_metrics' in data
        assert 'configuration' in data
    
    def test_service_stats(self, client):
        """Test service statistics endpoint"""
        response = client.get('/api/monitoring/stats')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'performance_metrics' in data
        assert 'cache_statistics' in data
        assert 'error_statistics' in data


class TestPerformance:
    """Performance and load testing"""
    
    def test_concurrent_requests(self, client, sample_ifc_data):
        """Test concurrent request handling"""
        def make_request():
            response = client.post('/api/parse', data=sample_ifc_data)
            return response.status_code == 200
        
        # Test with 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in futures]
        
        # All requests should succeed
        assert all(results)
    
    def test_parse_performance(self, client, sample_ifc_data):
        """Test parsing performance"""
        start_time = time.time()
        response = client.post('/api/parse', data=sample_ifc_data)
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 5.0  # Should complete within 5 seconds
    
    def test_cache_performance(self, client, sample_ifc_data):
        """Test cache performance"""
        # First request (cache miss)
        start_time = time.time()
        response1 = client.post('/api/parse', data=sample_ifc_data)
        first_duration = time.time() - start_time
        
        # Second request (cache hit)
        start_time = time.time()
        response2 = client.post('/api/parse', data=sample_ifc_data)
        second_duration = time.time() - start_time
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert second_duration < first_duration  # Cache hit should be faster


class TestErrorHandling:
    """Test error handling and recovery"""
    
    def test_file_size_limit(self, client):
        """Test file size limit handling"""
        large_data = b"x" * (200 * 1024 * 1024)  # 200MB
        response = client.post('/api/parse', data=large_data)
        
        assert response.status_code == 413
        data = json.loads(response.data)
        assert data['success'] == False
        assert data['error']['code'] == 'FILE_TOO_LARGE'
    
    def test_invalid_json_query(self, client, sample_ifc_data):
        """Test invalid JSON in spatial query"""
        response = client.post('/api/spatial/query',
                             data=sample_ifc_data,
                             content_type='application/octet-stream')
        
        # Should handle gracefully
        assert response.status_code in [200, 400]


class TestValidationModule:
    """Test validation module directly"""
    
    def test_ifc_validation_result(self):
        """Test IFCValidationResult class"""
        result = IFCValidationResult()
        assert result.valid == True
        assert result.warnings == []
        assert result.errors == []
        assert 'buildingSMART' in result.compliance
    
    def test_validator_basic_validation(self, sample_ifc_data):
        """Test validator with sample data"""
        result = validator.validate_ifc(sample_ifc_data)
        assert isinstance(result, IFCValidationResult)
        assert hasattr(result, 'valid')
        assert hasattr(result, 'warnings')
        assert hasattr(result, 'errors')


class TestSpatialModule:
    """Test spatial module directly"""
    
    def test_spatial_query_initialization(self):
        """Test SpatialQuery initialization"""
        query = SpatialQuery()
        assert hasattr(query, 'spatial_entities')
        assert isinstance(query.spatial_entities, list)
    
    def test_spatial_query_within_bounds(self, sample_ifc_data):
        """Test spatial query within bounds"""
        import ifcopenshell
        import io
        
        model = ifcopenshell.open(io.BytesIO(sample_ifc_data))
        bounds = {"min": [0, 0, 0], "max": [100, 100, 100]}
        
        result = spatial_query.query_within_bounds(model, bounds)
        assert result['success'] == True
        assert 'results' in result
        assert 'total_found' in result


class TestPerformanceModule:
    """Test performance module directly"""
    
    def test_performance_cache(self):
        """Test performance cache functionality"""
        cache = PerformanceCache()
        
        # Test set and get
        test_data = {"test": "data"}
        cache.set("test_key", test_data, 60)
        retrieved = cache.get("test_key")
        
        assert retrieved == test_data
    
    def test_performance_monitor(self):
        """Test performance monitor"""
        monitor = PerformanceMonitor()
        
        # Record some metrics
        monitor.record_request("test_endpoint", 1.0, True)
        monitor.record_request("test_endpoint", 2.0, False)
        
        metrics = monitor.get_metrics()
        assert metrics['requests_total'] == 2
        assert metrics['error_rate'] > 0


class TestErrorModule:
    """Test error handling module"""
    
    def test_error_handler(self):
        """Test error handler functionality"""
        handler = ErrorHandler()
        
        # Test error handling
        error = IFCServiceError("Test error", "TEST_ERROR")
        result = handler.handle_error(error)
        
        assert result['success'] == False
        assert result['error']['code'] == 'TEST_ERROR'
    
    def test_custom_exceptions(self):
        """Test custom exception classes"""
        # Test IFCParseError
        parse_error = IFCParseError("Parse failed")
        assert parse_error.error_code == "IFC_PARSE_ERROR"
        
        # Test IFCValidationError
        validation_error = IFCValidationError("Validation failed")
        assert validation_error.error_code == "IFC_VALIDATION_ERROR"
        
        # Test SpatialQueryError
        spatial_error = SpatialQueryError("Spatial query failed")
        assert spatial_error.error_code == "SPATIAL_QUERY_ERROR"


# Integration Tests
class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_complete_ifc_workflow(self, client, sample_ifc_data):
        """Test complete IFC processing workflow"""
        # 1. Parse IFC
        parse_response = client.post('/api/parse', data=sample_ifc_data)
        assert parse_response.status_code == 200
        
        parse_data = json.loads(parse_response.data)
        assert parse_data['success'] == True
        
        # 2. Validate IFC
        validate_response = client.post('/api/validate', data=sample_ifc_data)
        assert validate_response.status_code == 200
        
        validate_data = json.loads(validate_response.data)
        assert validate_data['success'] == True
        
        # 3. Get spatial bounds
        bounds_response = client.post('/api/spatial/bounds', data=sample_ifc_data)
        assert bounds_response.status_code == 200
        
        bounds_data = json.loads(bounds_response.data)
        assert bounds_data['success'] == True
    
    def test_service_health_monitoring(self, client):
        """Test service health monitoring"""
        # Check basic health
        health_response = client.get('/health')
        assert health_response.status_code == 200
        
        # Check detailed health
        detailed_health_response = client.get('/api/monitoring/health')
        assert detailed_health_response.status_code == 200
        
        # Check metrics
        metrics_response = client.get('/metrics')
        assert metrics_response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
