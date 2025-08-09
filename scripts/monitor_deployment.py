"""
Deployment monitoring script for Arxos platform.
"""
import requests
import time
import argparse
import sys


def monitor_deployment(timeout=600):
    """Monitor deployment status."""
    print(f"Starting deployment monitoring (timeout: {timeout}s)...")

    base_url = "https://arxos.com"
    start_time = time.time()

    # Health check endpoints
    endpoints = [
        "/health",
        "/api/v1/health",
        "/api/v1/version"
    ]

    while time.time() - start_time < timeout:
        print(f"\n--- Health Check at {time.strftime('%H:%M:%S')} ---")

        all_healthy = True

        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    print(f"✅ {endpoint} - HEALTHY")
                else:
                    print(f"❌ {endpoint} - UNHEALTHY ({response.status_code})")
                    all_healthy = False
            except Exception as e:
                print(f"❌ {endpoint} - ERROR: {e}")
                all_healthy = False

        if all_healthy:
            print("🎉 All endpoints are healthy! Deployment monitoring completed successfully.")
            return True

        # Wait before next check
        time.sleep(30)

    print("⏰ Deployment monitoring timed out. Some endpoints may still be unhealthy.")
    return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Monitor deployment status")
    parser.add_argument("--timeout", type=int, default=600,
                       help="Monitoring timeout in seconds (default: 600)")

    args = parser.parse_args()

    success = monitor_deployment(args.timeout)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
