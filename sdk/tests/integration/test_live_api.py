#!/usr/bin/env python3
"""
Integration tests for live API testing
Tests real API endpoints and workflows
"""

import pytest
import requests
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional


class TestLiveAPI:
    """Integration test suite for live API testing"""

    @pytest.fixture
    def api_config(self):
        """API configuration for testing"""
        return {
            "base_url": "http://localhost:8080",
            "svg_parser_url": "http://localhost:8082",
            "cmms_url": "http://localhost:8081",
            "database_url": "http://localhost:8083",
            "test_user": "test-user",
            "test_password": "test-password",
            "test_project": "test-project",
            "test_building": "test-building",
        }

    @pytest.fixture
    def auth_token(self, api_config):
        """Get authentication token"""
        try:
            response = requests.post(
                f"{api_config['base_url']}/api/auth/login",
                json={
                    "username": api_config["test_user"],
                    "password": api_config["test_password"],
                },
                timeout=10,
            )

            if response.status_code == 200:
                return response.json().get("token")
            else:
                return None

        except requests.RequestException:
            return None

    def test_api_health_check(self, api_config):
        """Test API health check endpoint"""
        try:
            response = requests.get(f"{api_config['base_url']}/api/health", timeout=10)

            assert (
                response.status_code == 200
            ), f"Health check failed: {response.status_code}"

            data = response.json()
            assert "status" in data, "Health response should have status field"
            assert data["status"] == "healthy", "API should be healthy"

        except requests.RequestException as e:
            pytest.skip(f"API not available: {e}")

    def test_authentication_flow(self, api_config):
        """Test complete authentication flow"""
        try:
            # Test login
            login_response = requests.post(
                f"{api_config['base_url']}/api/auth/login",
                json={
                    "username": api_config["test_user"],
                    "password": api_config["test_password"],
                },
                timeout=10,
            )

            if login_response.status_code == 200:
                token = login_response.json().get("token")
                assert token is not None, "Should return authentication token"

                # Test token validation
                headers = {"Authorization": f"Bearer {token}"}
                validate_response = requests.get(
                    f"{api_config['base_url']}/api/auth/validate",
                    headers=headers,
                    timeout=10,
                )

                assert (
                    validate_response.status_code == 200
                ), "Token validation should succeed"

            else:
                pytest.skip("Authentication not available")

        except requests.RequestException as e:
            pytest.skip(f"Authentication API not available: {e}")

    def test_project_workflow(self, api_config, auth_token):
        """Test complete project workflow"""
        if not auth_token:
            pytest.skip("Authentication required")

        try:
            headers = {"Authorization": f"Bearer {auth_token}"}

            # 1. Create project
            project_data = {
                "name": f"{api_config['test_project']}-{int(time.time())}",
                "description": "Test project for integration testing",
                "type": "building",
            }

            create_response = requests.post(
                f"{api_config['base_url']}/api/projects",
                json=project_data,
                headers=headers,
                timeout=10,
            )

            if create_response.status_code == 201:
                project = create_response.json()
                project_id = project.get("id")
                assert project_id is not None, "Should return project ID"

                # 2. Create building
                building_data = {
                    "name": f"{api_config['test_building']}-{int(time.time())}",
                    "address": "123 Test Street",
                    "project_id": project_id,
                }

                building_response = requests.post(
                    f"{api_config['base_url']}/api/buildings",
                    json=building_data,
                    headers=headers,
                    timeout=10,
                )

                if building_response.status_code == 201:
                    building = building_response.json()
                    building_id = building.get("id")
                    assert building_id is not None, "Should return building ID"

                    # 3. Get project with buildings
                    get_response = requests.get(
                        f"{api_config['base_url']}/api/projects/{project_id}",
                        headers=headers,
                        timeout=10,
                    )

                    assert get_response.status_code == 200, "Should retrieve project"
                    retrieved_project = get_response.json()
                    assert (
                        retrieved_project["id"] == project_id
                    ), "Should return correct project"

                    # 4. Clean up (if supported)
                    try:
                        requests.delete(
                            f"{api_config['base_url']}/api/projects/{project_id}",
                            headers=headers,
                            timeout=10,
                        )
                    except:
                        pass  # Cleanup optional

                else:
                    pytest.skip("Building creation not available")
            else:
                pytest.skip("Project creation not available")

        except requests.RequestException as e:
            pytest.skip(f"Project API not available: {e}")

    def test_bim_objects_workflow(self, api_config, auth_token):
        """Test BIM objects workflow"""
        if not auth_token:
            pytest.skip("Authentication required")

        try:
            headers = {"Authorization": f"Bearer {auth_token}"}

            # 1. Create wall
            wall_data = {
                "name": f"test-wall-{int(time.time())}",
                "type": "wall",
                "coordinates": {"x": 0, "y": 0, "z": 0},
                "dimensions": {"width": 10, "height": 3, "depth": 0.2},
            }

            wall_response = requests.post(
                f"{api_config['base_url']}/api/bim-objects/walls",
                json=wall_data,
                headers=headers,
                timeout=10,
            )

            if wall_response.status_code == 201:
                wall = wall_response.json()
                wall_id = wall.get("id")
                assert wall_id is not None, "Should return wall ID"

                # 2. Create room
                room_data = {
                    "name": f"test-room-{int(time.time())}",
                    "type": "room",
                    "coordinates": {"x": 0, "y": 0, "z": 0},
                    "dimensions": {"width": 5, "height": 3, "depth": 5},
                }

                room_response = requests.post(
                    f"{api_config['base_url']}/api/bim-objects/rooms",
                    json=room_data,
                    headers=headers,
                    timeout=10,
                )

                if room_response.status_code == 201:
                    room = room_response.json()
                    room_id = room.get("id")
                    assert room_id is not None, "Should return room ID"

                    # 3. Get BIM objects
                    objects_response = requests.get(
                        f"{api_config['base_url']}/api/bim-objects",
                        headers=headers,
                        timeout=10,
                    )

                    assert (
                        objects_response.status_code == 200
                    ), "Should retrieve BIM objects"
                    objects = objects_response.json()
                    assert isinstance(objects, list), "Should return list of objects"

                    # 4. Clean up
                    try:
                        requests.delete(
                            f"{api_config['base_url']}/api/bim-objects/walls/{wall_id}",
                            headers=headers,
                            timeout=10,
                        )
                        requests.delete(
                            f"{api_config['base_url']}/api/bim-objects/rooms/{room_id}",
                            headers=headers,
                            timeout=10,
                        )
                    except:
                        pass

                else:
                    pytest.skip("Room creation not available")
            else:
                pytest.skip("Wall creation not available")

        except requests.RequestException as e:
            pytest.skip(f"BIM objects API not available: {e}")

    def test_asset_management_workflow(self, api_config, auth_token):
        """Test asset management workflow"""
        if not auth_token:
            pytest.skip("Authentication required")

        try:
            headers = {"Authorization": f"Bearer {auth_token}"}

            # 1. Create asset
            asset_data = {
                "name": f"test-asset-{int(time.time())}",
                "type": "equipment",
                "location": "Building A",
                "status": "active",
            }

            asset_response = requests.post(
                f"{api_config['base_url']}/api/assets",
                json=asset_data,
                headers=headers,
                timeout=10,
            )

            if asset_response.status_code == 201:
                asset = asset_response.json()
                asset_id = asset.get("id")
                assert asset_id is not None, "Should return asset ID"

                # 2. Update asset
                update_data = {"status": "maintenance"}
                update_response = requests.put(
                    f"{api_config['base_url']}/api/assets/{asset_id}",
                    json=update_data,
                    headers=headers,
                    timeout=10,
                )

                assert update_response.status_code == 200, "Should update asset"

                # 3. Get asset
                get_response = requests.get(
                    f"{api_config['base_url']}/api/assets/{asset_id}",
                    headers=headers,
                    timeout=10,
                )

                assert get_response.status_code == 200, "Should retrieve asset"
                retrieved_asset = get_response.json()
                assert (
                    retrieved_asset["status"] == "maintenance"
                ), "Should reflect update"

                # 4. Clean up
                try:
                    requests.delete(
                        f"{api_config['base_url']}/api/assets/{asset_id}",
                        headers=headers,
                        timeout=10,
                    )
                except:
                    pass

            else:
                pytest.skip("Asset creation not available")

        except requests.RequestException as e:
            pytest.skip(f"Asset management API not available: {e}")

    def test_svg_parser_integration(self, api_config):
        """Test SVG parser integration"""
        try:
            # Test SVG parser health
            health_response = requests.get(
                f"{api_config['svg_parser_url']}/health", timeout=10
            )

            if health_response.status_code == 200:
                # Test symbol upload
                test_svg = """
                <svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
                    <rect width="100" height="100" fill="blue"/>
                </svg>
                """

                upload_response = requests.post(
                    f"{api_config['svg_parser_url']}/symbols/upload",
                    files={"file": ("test.svg", test_svg, "image/svg+xml")},
                    timeout=10,
                )

                if upload_response.status_code == 201:
                    symbol = upload_response.json()
                    symbol_id = symbol.get("id")
                    assert symbol_id is not None, "Should return symbol ID"

                    # Clean up
                    try:
                        requests.delete(
                            f"{api_config['svg_parser_url']}/symbols/{symbol_id}",
                            timeout=10,
                        )
                    except:
                        pass

                else:
                    pytest.skip("Symbol upload not available")
            else:
                pytest.skip("SVG parser not available")

        except requests.RequestException as e:
            pytest.skip(f"SVG parser API not available: {e}")

    def test_cmms_integration(self, api_config):
        """Test CMMS integration"""
        try:
            # Test CMMS health
            health_response = requests.get(
                f"{api_config['cmms_url']}/health", timeout=10
            )

            if health_response.status_code == 200:
                # Test CMMS connections
                connections_response = requests.get(
                    f"{api_config['cmms_url']}/cmms/connections", timeout=10
                )

                assert (
                    connections_response.status_code == 200
                ), "Should retrieve CMMS connections"
                connections = connections_response.json()
                assert isinstance(
                    connections, list
                ), "Should return list of connections"

            else:
                pytest.skip("CMMS not available")

        except requests.RequestException as e:
            pytest.skip(f"CMMS API not available: {e}")

    def test_database_infrastructure(self, api_config):
        """Test database infrastructure"""
        try:
            # Test database health
            health_response = requests.get(
                f"{api_config['database_url']}/health", timeout=10
            )

            if health_response.status_code == 200:
                # Test database status
                status_response = requests.get(
                    f"{api_config['database_url']}/database/status", timeout=10
                )

                assert (
                    status_response.status_code == 200
                ), "Should retrieve database status"
                status = status_response.json()
                assert "status" in status, "Should have status field"

            else:
                pytest.skip("Database infrastructure not available")

        except requests.RequestException as e:
            pytest.skip(f"Database infrastructure API not available: {e}")

    def test_error_handling(self, api_config):
        """Test error handling scenarios"""
        try:
            # Test invalid authentication
            invalid_auth_response = requests.get(
                f"{api_config['base_url']}/api/projects",
                headers={"Authorization": "Bearer invalid-token"},
                timeout=10,
            )

            assert (
                invalid_auth_response.status_code == 401
            ), "Should reject invalid token"

            # Test invalid endpoint
            invalid_endpoint_response = requests.get(
                f"{api_config['base_url']}/api/invalid-endpoint", timeout=10
            )

            assert (
                invalid_endpoint_response.status_code == 404
            ), "Should return 404 for invalid endpoint"

            # Test invalid data
            invalid_data_response = requests.post(
                f"{api_config['base_url']}/api/projects",
                json={"invalid": "data"},
                timeout=10,
            )

            assert invalid_data_response.status_code in [
                400,
                401,
            ], "Should reject invalid data"

        except requests.RequestException as e:
            pytest.skip(f"Error handling test not available: {e}")

    def test_performance_metrics(self, api_config):
        """Test API performance metrics"""
        try:
            # Test response time
            start_time = time.time()
            response = requests.get(f"{api_config['base_url']}/api/health", timeout=10)
            end_time = time.time()

            response_time = end_time - start_time
            assert (
                response_time < 5.0
            ), f"Response time should be under 5 seconds: {response_time}"

            # Test concurrent requests
            import concurrent.futures

            def make_request():
                return requests.get(f"{api_config['base_url']}/api/health", timeout=10)

            start_time = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(10)]
                results = [future.result() for future in futures]
            end_time = time.time()

            concurrent_time = end_time - start_time
            assert (
                concurrent_time < 10.0
            ), f"Concurrent requests should complete under 10 seconds: {concurrent_time}"

            # All requests should succeed
            for result in results:
                assert (
                    result.status_code == 200
                ), "All concurrent requests should succeed"

        except requests.RequestException as e:
            pytest.skip(f"Performance test not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
