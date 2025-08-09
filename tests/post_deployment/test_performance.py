"""
Post-deployment performance tests for Arxos platform.
"""
import requests
import time
import statistics


def test_post_deployment_performance():
    """Test performance after deployment."""
    print("Running post-deployment performance tests...")

    base_url = "https://arxos.com"

    # Test critical endpoints performance
    endpoints = [
        "/health",
        "/api/v1/health",
        "/api/v1/cad",
        "/api/v1/ai"
    ]

    performance_results = {}

    for endpoint in endpoints:
        print(f"Testing {endpoint} performance...")
        response_times = []

        # Run 5 requests to get performance metrics
        for i in range(5):
            try:
                start_time = time.time()
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
                end_time = time.time()

                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                response_times.append(response_time)

                if response.status_code == 200:
                    print(f"  Request {i+1}: {response_time:.2f}ms ✅")
                else:
                    print(f"  Request {i+1}: {response_time:.2f}ms ❌ ({response.status_code})")

            except Exception as e:
                print(f"  Request {i+1}: Error - {e}")

        if response_times:
            avg_time = statistics.mean(response_times)
            max_time = max(response_times)

            performance_results[endpoint] = {
                "average_response_time": avg_time,
                "max_response_time": max_time,
                "requests": len(response_times)
            }

            print(f"  Average: {avg_time:.2f}ms, Max: {max_time:.2f}ms")

    # Performance thresholds
    thresholds = {
        "average_response_time": 500,  # 500ms
        "max_response_time": 1000      # 1 second
    }

    print("\nPerformance Analysis:")
    for endpoint, metrics in performance_results.items():
        print(f"{endpoint}:")
        print(f"  Average: {metrics['average_response_time']:.2f}ms")
        print(f"  Max: {metrics['max_response_time']:.2f}ms")

        # Check thresholds
        if metrics['average_response_time'] > thresholds['average_response_time']:
            print(f"  ⚠️  Average response time exceeds threshold ({thresholds['average_response_time']}ms)")
        else:
            print(f"  ✅ Average response time within threshold")

        if metrics['max_response_time'] > thresholds['max_response_time']:
            print(f"  ⚠️  Max response time exceeds threshold ({thresholds['max_response_time']}ms)")
        else:
            print(f"  ✅ Max response time within threshold")

    print("Post-deployment performance tests completed")


if __name__ == "__main__":
    test_post_deployment_performance()
