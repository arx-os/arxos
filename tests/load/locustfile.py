"""
Load testing configuration for Arxos platform using Locust.
"""
from locust import HttpUser, task, between
import json
import random


class ArxosLoadTest(HttpUser):
    """Load test user for Arxos platform."""

    wait_time = between(1, 3)

    def on_start(self):
        """Setup before each user session."""
        # Initialize test data
        self.test_buildings = [
            {"name": "Test Building 1", "type": "office", "floors": 5},
            {"name": "Test Building 2", "type": "residential", "floors": 10},
            {"name": "Test Building 3", "type": "industrial", "floors": 3}
        ]

    @task(3)
def health_check(self):
        """Test health endpoint."""
        self.client.get("/health/")

    @task(2)
def get_buildings(self):
        """Test buildings endpoint."""
        self.client.get("/api/v1/buildings/")

    @task(1)
def create_building(self):
        """Test building creation."""
        building_data = random.choice(self.test_buildings)
        headers = {"Content-Type": "application/json"}
        self.client.post(
            "/api/v1/buildings/",
            json=building_data,
            headers=headers
        )

    @task(1)
def get_devices(self):
        """Test devices endpoint."""
        self.client.get("/api/v1/devices/")

    @task(1)
def svgx_validation(self):
        """Test SVGX validation endpoint."""
        test_svgx = """
        <svgx>
            <building>
                <floor level="1">
                    <room id="room1" area="100"/>
                </floor>
            </building>
        </svgx>
        """
        headers = {"Content-Type": "application/xml"}
        self.client.post(
            "/api/v1/svgx/validate",
            data=test_svgx,
            headers=headers
        )


class ArxosAPITest(HttpUser):
    """API-specific load test user."""

    wait_time = between(2, 5)

    @task(2)
def api_documentation(self):
        """Test API documentation endpoint."""
        self.client.get("/docs/")

    @task(1)
def openapi_schema(self):
        """Test OpenAPI schema endpoint."""
        self.client.get("/openapi.json")

    @task(1)
def metrics_endpoint(self):
        """Test metrics endpoint."""
        self.client.get("/metrics/")


class ArxosAuthTest(HttpUser):
    """Authentication load test user."""

    wait_time = between(1, 2)

    @task(1)
def login_endpoint(self):
        """Test login endpoint."""
        login_data = {
            "username": "test_user",
            "password": "test_password"
        }
        headers = {"Content-Type": "application/json"}
        self.client.post(
            "/api/v1/auth/login",
            json=login_data,
            headers=headers
        )

    @task(1)
def register_endpoint(self):
        """Test registration endpoint."""
        register_data = {
            "username": f"user_{random.randint(1000, 9999)}",
            "email": f"user_{random.randint(1000, 9999)}@test.com",
            "password": "test_password"
        }
        headers = {"Content-Type": "application/json"}
        self.client.post(
            "/api/v1/auth/register",
            json=register_data,
            headers=headers
        )
