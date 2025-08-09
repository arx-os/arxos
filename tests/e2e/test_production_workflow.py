"""
End-to-end tests for production workflow.
"""
import requests
import json
import time


def test_production_workflow():
    """Test complete production workflow."""
    print("Running end-to-end production workflow tests...")

    base_url = "https://arxos.com"

    # Test user authentication
    try:
        auth_data = {"username": "test_user", "password": "test_password"}
        response = requests.post(f"{base_url}/api/v1/auth/login", json=auth_data, timeout=10)
        if response.status_code == 200:
            print("✅ Authentication test passed")
            token = response.json().get("token")
        else:
            print(f"❌ Authentication test failed: {response.status_code}")
            token = None
    except Exception as e:
        print(f"❌ Authentication test error: {e}")
        token = None

    # Test CAD functionality
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = requests.get(f"{base_url}/api/v1/cad", headers=headers, timeout=10)
            if response.status_code == 200:
                print("✅ CAD functionality test passed")
            else:
                print(f"❌ CAD functionality test failed: {response.status_code}")
        except Exception as e:
            print(f"❌ CAD functionality test error: {e}")

    # Test AI functionality
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        try:
            ai_data = {"query": "Create a simple building design"}
            response = requests.post(f"{base_url}/api/v1/ai/query", json=ai_data, headers=headers, timeout=10)
            if response.status_code == 200:
                print("✅ AI functionality test passed")
            else:
                print(f"❌ AI functionality test failed: {response.status_code}")
        except Exception as e:
            print(f"❌ AI functionality test error: {e}")

    # Test file upload
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        try:
            files = {"file": ("test.svgx", "test content", "application/svgx")}
            response = requests.post(f"{base_url}/api/v1/files/upload", files=files, headers=headers, timeout=10)
            if response.status_code == 200:
                print("✅ File upload test passed")
            else:
                print(f"❌ File upload test failed: {response.status_code}")
        except Exception as e:
            print(f"❌ File upload test error: {e}")

    print("End-to-end production workflow tests completed")


if __name__ == "__main__":
    test_production_workflow()
