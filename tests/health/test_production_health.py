"""
Production health tests for Arxos platform.
"""
import requests
import argparse
import sys


def test_production_health(environment="blue"):
    """Test production health for specified environment."""
    print(f"Running production health tests for {environment} environment...")

    base_url = f"https://{environment}.arxos.com"

    # Test basic health
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ {environment} health check passed")
        else:
            print(f"❌ {environment} health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ {environment} health check error: {e}")

    # Test API health
    try:
        response = requests.get(f"{base_url}/api/v1/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ {environment} API health check passed")
        else:
            print(f"❌ {environment} API health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ {environment} API health check error: {e}")

    # Test database connectivity
    try:
        response = requests.get(f"{base_url}/api/v1/db/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ {environment} database health check passed")
        else:
            print(f"❌ {environment} database health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ {environment} database health check error: {e}")

    print(f"Production health tests for {environment} completed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test production health")
    parser.add_argument("--environment", default="blue", choices=["blue", "green"],
                       help="Environment to test (blue or green)")

    args = parser.parse_args()
    test_production_health(args.environment)
