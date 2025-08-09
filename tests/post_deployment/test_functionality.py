"""
Post-deployment functionality tests for Arxos platform.
"""
import requests
import json


def test_post_deployment_functionality():
    """Test functionality after deployment."""
    print("Running post-deployment functionality tests...")

    base_url = "https://arxos.com"

    # Test basic functionality
    endpoints = [
        "/health",
        "/api/v1/health",
        "/api/v1/version",
        "/api/v1/status"
    ]

    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {endpoint} - PASSED")
            else:
                print(f"❌ {endpoint} - FAILED ({response.status_code})")
        except Exception as e:
            print(f"❌ {endpoint} - ERROR: {e}")

    # Test database connectivity
    try:
        response = requests.get(f"{base_url}/api/v1/db/health", timeout=10)
        if response.status_code == 200:
            print("✅ Database connectivity - PASSED")
        else:
            print(f"❌ Database connectivity - FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ Database connectivity - ERROR: {e}")

    # Test cache connectivity
    try:
        response = requests.get(f"{base_url}/api/v1/cache/health", timeout=10)
        if response.status_code == 200:
            print("✅ Cache connectivity - PASSED")
        else:
            print(f"❌ Cache connectivity - FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ Cache connectivity - ERROR: {e}")

    # Test file system access
    try:
        response = requests.get(f"{base_url}/api/v1/files/health", timeout=10)
        if response.status_code == 200:
            print("✅ File system access - PASSED")
        else:
            print(f"❌ File system access - FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ File system access - ERROR: {e}")

    print("Post-deployment functionality tests completed")


if __name__ == "__main__":
    test_post_deployment_functionality()
