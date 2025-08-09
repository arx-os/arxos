"""
Performance tests for Arxos platform using Locust.
"""
from locust import HttpUser, task, between


class ArxosUser(HttpUser):
    """Simulates user behavior for Arxos platform."""

    wait_time = between(1, 3)

    def on_start(self):
        """Setup before each user session."""
        pass

    @task(3)
def test_homepage(self):
        """Test homepage performance."""
        self.client.get("/")

    @task(2)
def test_api_health(self):
        """Test API health endpoint."""
        self.client.get("/health")

    @task(1)
def test_cad_endpoint(self):
        """Test CAD endpoint performance."""
        self.client.get("/api/v1/cad")

    @task(1)
def test_ai_endpoint(self):
        """Test AI endpoint performance."""
        self.client.get("/api/v1/ai")
