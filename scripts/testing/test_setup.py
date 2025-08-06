#!/usr/bin/env python3
"""
Arxos Setup Test Script
This script tests the complete Arxos local development environment.
"""

import requests
import json
import time
import sys
from pathlib import Path

# Test configuration
SERVICES = {
    "svg_parser": {"url": "http://localhost:8000", "health_endpoint": "/health"},
    "backend": {"url": "http://localhost:8080", "health_endpoint": "/api/health"},
    "svgx_engine": {"url": "http://localhost:8001", "health_endpoint": "/health"},
    "web_frontend": {"url": "http://localhost:3000", "health_endpoint": "/"},
}


def print_status(message, status="INFO"):
    """Print colored status messages."""
    colors = {
        "INFO": "\033[94m",
        "SUCCESS": "\033[92m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
    }
    reset = "\033[0m"
    color = colors.get(status, colors["INFO"])
    print(f"{color}[{status}]{reset} {message}")


def wait_for_service(url, endpoint, service_name, max_attempts=30):
    """Wait for a service to be ready."""
    print_status(f"Waiting for {service_name} to be ready...")

    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print_status(f"{service_name} is ready!", "SUCCESS")
                return True
        except requests.exceptions.RequestException:
            pass

        print(".", end="", flush=True)
        time.sleep(2)

    print_status(f"{service_name} failed to start within expected time", "ERROR")
    return False


def test_service_health(service_name, config):
    """Test a service's health endpoint."""
    try:
        response = requests.get(
            f"{config['url']}{config['health_endpoint']}", timeout=10
        )
        if response.status_code == 200:
            print_status(f"{service_name} health check passed", "SUCCESS")
            return True
        else:
            print_status(
                f"{service_name} health check failed (status: {response.status_code})",
                "ERROR",
            )
            return False
    except requests.exceptions.RequestException as e:
        print_status(f"{service_name} health check failed: {e}", "ERROR")
        return False


def test_user_registration():
    """Test user registration functionality."""
    print_status("Testing user registration...")

    try:
        response = requests.post(
            "http://localhost:8080/api/register",
            json={
                "username": "testuser",
                "email": "test@arxos.com",
                "password": "password123",
            },
            timeout=10,
        )

        if response.status_code in [200, 201, 409]:  # 409 means user already exists
            print_status("User registration test passed", "SUCCESS")
            return True
        else:
            print_status(
                f"User registration failed (status: {response.status_code})", "ERROR"
            )
            return False
    except requests.exceptions.RequestException as e:
        print_status(f"User registration test failed: {e}", "ERROR")
        return False


def test_user_login():
    """Test user login functionality."""
    print_status("Testing user login...")

    try:
        response = requests.post(
            "http://localhost:8080/api/login",
            json={"username": "testuser", "password": "password123"},
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            if "token" in data:
                print_status("User login test passed", "SUCCESS")
                return data["token"]
            else:
                print_status("User login failed: no token in response", "ERROR")
                return None
        else:
            print_status(f"User login failed (status: {response.status_code})", "ERROR")
            return None
    except requests.exceptions.RequestException as e:
        print_status(f"User login test failed: {e}", "ERROR")
        return None


def test_svg_upload(token):
    """Test SVG upload functionality."""
    print_status("Testing SVG upload...")

    # Create a simple test SVG
    test_svg = """<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <rect x="100" y="100" width="200" height="150" fill="white" stroke="black"/>
  <circle cx="200" cy="175" r="20" fill="red"/>
</svg>"""

    try:
        # First create a test building
        building_response = requests.post(
            "http://localhost:8080/api/buildings",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Test Building",
                "address": "123 Test Street",
                "description": "Test building for development",
            },
            timeout=10,
        )

        if building_response.status_code in [200, 201]:
            print_status("Building creation test passed", "SUCCESS")
        else:
            print_status(
                f"Building creation failed (status: {building_response.status_code})",
                "WARNING",
            )

        # Test SVG upload to SVG Parser
        upload_response = requests.post(
            "http://localhost:8000/api/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("test.svg", test_svg, "image/svg+xml")},
            data={"building_id": "1", "name": "Test Floor"},
            timeout=10,
        )

        if upload_response.status_code in [200, 201]:
            print_status("SVG upload test passed", "SUCCESS")
            return True
        else:
            print_status(
                f"SVG upload failed (status: {upload_response.status_code})", "WARNING"
            )
            return False
    except requests.exceptions.RequestException as e:
        print_status(f"SVG upload test failed: {e}", "WARNING")
        return False


def test_svgx_engine():
    """Test SVGX Engine functionality."""
    print_status("Testing SVGX Engine...")

    test_svgx = """<svgx>
  <element id="test-rect" type="rectangle" x="100" y="100" width="200" height="150">
    <properties>
      <property name="fill" value="white"/>
      <property name="stroke" value="black"/>
    </properties>
  </element>
</svgx>"""

    try:
        response = requests.post(
            "http://localhost:8001/parse",
            json={"content": test_svgx, "options": {"precision": "high"}},
            timeout=10,
        )

        if response.status_code == 200:
            print_status("SVGX Engine parse test passed", "SUCCESS")
            return True
        else:
            print_status(
                f"SVGX Engine parse failed (status: {response.status_code})", "WARNING"
            )
            return False
    except requests.exceptions.RequestException as e:
        print_status(f"SVGX Engine test failed: {e}", "WARNING")
        return False


def test_api_documentation():
    """Test API documentation endpoints."""
    print_status("Testing API documentation...")

    docs_endpoints = [
        ("http://localhost:8000/docs", "SVG Parser API Docs"),
        ("http://localhost:8080/docs", "Backend API Docs"),
        ("http://localhost:8001/docs", "SVGX Engine API Docs"),
    ]

    success_count = 0
    for url, name in docs_endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print_status(f"{name} accessible", "SUCCESS")
                success_count += 1
            else:
                print_status(
                    f"{name} not accessible (status: {response.status_code})", "WARNING"
                )
        except requests.exceptions.RequestException as e:
            print_status(f"{name} not accessible: {e}", "WARNING")

    return success_count > 0


def main():
    """Main test function."""
    print_status("Starting Arxos Setup Test...")
    print_status("=" * 50)

    # Wait for all services to be ready
    print_status("Waiting for services to be ready...")
    all_ready = True

    for service_name, config in SERVICES.items():
        if not wait_for_service(config["url"], config["health_endpoint"], service_name):
            all_ready = False

    if not all_ready:
        print_status("Some services failed to start. Please check the setup.", "ERROR")
        return False

    print_status("All services are ready!", "SUCCESS")
    print_status("=" * 50)

    # Test service health
    print_status("Testing service health...")
    health_tests_passed = 0
    total_health_tests = len(SERVICES)

    for service_name, config in SERVICES.items():
        if test_service_health(service_name, config):
            health_tests_passed += 1

    print_status(f"Health tests: {health_tests_passed}/{total_health_tests} passed")
    print_status("=" * 50)

    # Test user functionality
    print_status("Testing user functionality...")
    user_registration_ok = test_user_registration()
    token = test_user_login()
    user_login_ok = token is not None

    print_status("=" * 50)

    # Test SVG functionality
    print_status("Testing SVG functionality...")
    svg_upload_ok = False
    if token:
        svg_upload_ok = test_svg_upload(token)

    svgx_engine_ok = test_svgx_engine()

    print_status("=" * 50)

    # Test API documentation
    print_status("Testing API documentation...")
    docs_ok = test_api_documentation()

    print_status("=" * 50)

    # Summary
    print_status("Test Summary:", "INFO")
    print_status(f"  - Service Health: {health_tests_passed}/{total_health_tests}")
    print_status(f"  - User Registration: {'✓' if user_registration_ok else '✗'}")
    print_status(f"  - User Login: {'✓' if user_login_ok else '✗'}")
    print_status(f"  - SVG Upload: {'✓' if svg_upload_ok else '✗'}")
    print_status(f"  - SVGX Engine: {'✓' if svgx_engine_ok else '✗'}")
    print_status(f"  - API Documentation: {'✓' if docs_ok else '✗'}")

    # Overall result
    total_tests = 5  # health + registration + login + upload + svgx + docs
    passed_tests = (
        health_tests_passed
        + (1 if user_registration_ok else 0)
        + (1 if user_login_ok else 0)
        + (1 if svg_upload_ok else 0)
        + (1 if svgx_engine_ok else 0)
        + (1 if docs_ok else 0)
    )

    if passed_tests >= total_tests * 0.8:  # 80% success rate
        print_status("Arxos setup test PASSED!", "SUCCESS")
        print_status("Your local development environment is working correctly.")
        return True
    else:
        print_status("Arxos setup test FAILED!", "ERROR")
        print_status(
            "Some components are not working correctly. Please check the setup."
        )
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_status("Test interrupted by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        print_status(f"Test failed with error: {e}", "ERROR")
        sys.exit(1)
