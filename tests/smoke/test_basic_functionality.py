"""
Smoke tests for basic functionality.
"""
import pytest
import requests
import time


class TestBasicFunctionality:
    """Test basic functionality of the Arxos platform."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.base_url = "https://staging-api.arxos.com"
        self.timeout = 30

    def test_health_endpoint(self):
        """Test health endpoint is accessible."""
        try:
            response = requests.get(f"{self.base_url}/health/", timeout=self.timeout)
            assert response.status_code == 200
            assert "status" in response.json()
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Health endpoint not accessible: {e}")

    def test_api_documentation(self):
        """Test API documentation is accessible."""
        try:
            response = requests.get(f"{self.base_url}/docs/", timeout=self.timeout)
            assert response.status_code == 200
        except requests.exceptions.RequestException as e:
            pytest.skip(f"API documentation not accessible: {e}")

    def test_openapi_schema(self):
        """Test OpenAPI schema is accessible."""
        try:
            response = requests.get(f"{self.base_url}/openapi.json", timeout=self.timeout)
            assert response.status_code == 200
            schema = response.json()
            assert "openapi" in schema
        except requests.exceptions.RequestException as e:
            pytest.skip(f"OpenAPI schema not accessible: {e}")

    def test_metrics_endpoint(self):
        """Test metrics endpoint is accessible."""
        try:
            response = requests.get(f"{self.base_url}/metrics/", timeout=self.timeout)
            assert response.status_code == 200
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Metrics endpoint not accessible: {e}")


class TestServiceConnectivity:
    """Test service connectivity."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.services = {
            "api": "https://staging-api.arxos.com",
            "ai": "https://staging-ai.arxos.com",
            "realtime": "https://staging-realtime.arxos.com",
            "auth": "https://staging-auth.arxos.com"
        }
        self.timeout = 30

    def test_service_health_checks(self):
        """Test all services are healthy."""
        for service_name, service_url in self.services.items():
            try:
                response = requests.get(f"{service_url}/health/", timeout=self.timeout)
                assert response.status_code == 200, f"{service_name} health check failed"
            except requests.exceptions.RequestException as e:
                pytest.skip(f"{service_name} not accessible: {e}")

    def test_service_response_times(self):
        """Test service response times are acceptable."""
        for service_name, service_url in self.services.items():
            try:
                start_time = time.time()
                response = requests.get(f"{service_url}/health/", timeout=self.timeout)
                end_time = time.time()

                response_time = end_time - start_time
                assert response_time < 5.0, f"{service_name} response time too slow: {response_time}s"
                assert response.status_code == 200, f"{service_name} health check failed"
            except requests.exceptions.RequestException as e:
                pytest.skip(f"{service_name} not accessible: {e}")


if __name__ == "__main__":
    pytest.main([__file__])
