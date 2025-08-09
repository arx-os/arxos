"""
Smoke tests for staging deployment.
"""
import requests
import time


def test_staging_deployment():
    """Run smoke tests for staging deployment."""
    print("Running smoke tests for staging deployment...")

    # Test basic connectivity
    try:
        response = requests.get("https://staging.arxos.com/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

    # Test API endpoints
    try:
        response = requests.get("https://staging.arxos.com/api/v1/health", timeout=10)
        if response.status_code == 200:
            print("✅ API health check passed")
        else:
            print(f"❌ API health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ API health check error: {e}")

    print("Smoke tests completed")


if __name__ == "__main__":
    test_staging_deployment()
