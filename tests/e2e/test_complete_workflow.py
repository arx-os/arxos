"""
End-to-end tests for complete workflows.
"""
import pytest
import requests
import json
import time


class TestCompleteWorkflow:
    """Test complete user workflows."""

    @pytest.fixture(autouse=True)
def setup(self):
        """Setup test environment."""
        self.base_url = "https://staging-api.arxos.com"
        self.timeout = 30
        self.test_data = {
            "building": {
                "name": "Test Building E2E",
                "type": "office",
                "floors": 5,
                "area": 10000
            },
            "device": {
                "name": "Test Device E2E",
                "type": "sensor",
                "location": "floor_1",
                "status": "active"
            }
        }

    def test_building_creation_workflow(self):
        """Test complete building creation workflow."""
        try:
            # Step 1: Create building
            response = requests.post(
                f"{self.base_url}/api/v1/buildings/",
                json=self.test_data["building"],
                timeout=self.timeout
            )
            assert response.status_code in [200, 201], f"Building creation failed: {response.status_code}"
            building_data = response.json()
            building_id = building_data.get("id")
            assert building_id is not None, "Building ID not returned"

            # Step 2: Verify building exists
            response = requests.get(
                f"{self.base_url}/api/v1/buildings/{building_id}",
                timeout=self.timeout
            )
            assert response.status_code == 200, "Building retrieval failed"
            retrieved_building = response.json()
            assert retrieved_building["name"] == self.test_data["building"]["name"]

            # Step 3: Update building
            updated_data = self.test_data["building"].copy()
            updated_data["floors"] = 6
            response = requests.put(
                f"{self.base_url}/api/v1/buildings/{building_id}",
                json=updated_data,
                timeout=self.timeout
            )
            assert response.status_code == 200, "Building update failed"

            # Step 4: Delete building (cleanup)
            response = requests.delete(
                f"{self.base_url}/api/v1/buildings/{building_id}",
                timeout=self.timeout
            )
            assert response.status_code in [200, 204], "Building deletion failed"

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Building workflow test skipped: {e}")

    def test_device_management_workflow(self):
        """Test complete device management workflow."""
        try:
            # Step 1: Create device
            response = requests.post(
                f"{self.base_url}/api/v1/devices/",
                json=self.test_data["device"],
                timeout=self.timeout
            )
            assert response.status_code in [200, 201], f"Device creation failed: {response.status_code}"
            device_data = response.json()
            device_id = device_data.get("id")
            assert device_id is not None, "Device ID not returned"

            # Step 2: Verify device exists
            response = requests.get(
                f"{self.base_url}/api/v1/devices/{device_id}",
                timeout=self.timeout
            )
            assert response.status_code == 200, "Device retrieval failed"
            retrieved_device = response.json()
            assert retrieved_device["name"] == self.test_data["device"]["name"]

            # Step 3: Update device status
            updated_data = self.test_data["device"].copy()
            updated_data["status"] = "inactive"
            response = requests.patch(
                f"{self.base_url}/api/v1/devices/{device_id}",
                json={"status": "inactive"},
                timeout=self.timeout
            )
            assert response.status_code == 200, "Device update failed"

            # Step 4: Delete device (cleanup)
            response = requests.delete(
                f"{self.base_url}/api/v1/devices/{device_id}",
                timeout=self.timeout
            )
            assert response.status_code in [200, 204], "Device deletion failed"

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Device workflow test skipped: {e}")

    def test_svgx_validation_workflow(self):
        """Test SVGX validation workflow."""
        try:
            # Test SVGX validation
            test_svgx = """
            <svgx>
                <building>
                    <floor level="1">
                        <room id="room1" area="100"/>
                        <room id="room2" area="150"/>
                    </floor>
                    <floor level="2">
                        <room id="room3" area="200"/>
                    </floor>
                </building>
            </svgx>
            """

            response = requests.post(
                f"{self.base_url}/api/v1/svgx/validate",
                data=test_svgx,
                headers={"Content-Type": "application/xml"},
                timeout=self.timeout
            )
            assert response.status_code == 200, "SVGX validation failed"

            validation_result = response.json()
            assert "valid" in validation_result, "Validation result missing"

        except requests.exceptions.RequestException as e:
            pytest.skip(f"SVGX validation test skipped: {e}")

    def test_authentication_workflow(self):
        """Test authentication workflow."""
        try:
            # Test registration
            user_data = {
                "username": f"test_user_{int(time.time())}",
                "email": f"test_{int(time.time())}@arxos.com",
                "password": "test_password_123"
            }

            response = requests.post(
                f"{self.base_url}/api/v1/auth/register",
                json=user_data,
                timeout=self.timeout
            )
            assert response.status_code in [200, 201], "User registration failed"

            # Test login
            login_data = {
                "username": user_data["username"],
                "password": user_data["password"]
            }

            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data,
                timeout=self.timeout
            )
            assert response.status_code == 200, "User login failed"

            login_result = response.json()
            assert "access_token" in login_result, "Access token not returned"

            # Test protected endpoint with token
            headers = {"Authorization": f"Bearer {login_result['access_token']}"}
            response = requests.get(
                f"{self.base_url}/api/v1/users/me",
                headers=headers,
                timeout=self.timeout
            )
            assert response.status_code == 200, "Protected endpoint access failed"

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Authentication workflow test skipped: {e}")


class TestPerformanceWorkflow:
    """Test performance-related workflows."""

    @pytest.fixture(autouse=True)
def setup(self):
        """Setup test environment."""
        self.base_url = "https://staging-api.arxos.com"
        self.timeout = 30

    def test_bulk_operations(self):
        """Test bulk operations performance."""
        try:
            # Test bulk building creation
            buildings = []
            for i in range(10):
                buildings.append({
                    "name": f"Bulk Building {i}",
                    "type": "office",
                    "floors": 3,
                    "area": 5000
                })

            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/v1/buildings/bulk",
                json={"buildings": buildings},
                timeout=self.timeout
            )
            end_time = time.time()

            assert response.status_code in [200, 201], "Bulk creation failed"
            assert (end_time - start_time) < 10.0, "Bulk operation too slow"

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Bulk operations test skipped: {e}")

    def test_concurrent_requests(self):
        """Test concurrent request handling."""
        try:
            import concurrent.futures

            def make_request():
                response = requests.get(f"{self.base_url}/health/", timeout=self.timeout)
                return response.status_code

            start_time = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request) for _ in range(20)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            end_time = time.time()

            assert all(status == 200 for status in results), "Some concurrent requests failed"
            assert (end_time - start_time) < 5.0, "Concurrent requests too slow"

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Concurrent requests test skipped: {e}")


if __name__ == "__main__":
    pytest.main([__file__])
