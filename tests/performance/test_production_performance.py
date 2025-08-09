"""
Production performance tests for Arxos platform.
"""
import requests
import time
import statistics


def test_production_performance():
    """Test production performance metrics."""
    print("Running production performance tests...")

    base_url = "https://arxos.com"
    endpoints = [
        "/health",
        "/api/v1/health",
        "/api/v1/cad",
        "/api/v1/ai"
    ]

    results = {}

    for endpoint in endpoints:
        print(f"Testing {endpoint}...")
        response_times = []

        # Run 10 requests to get average response time
        for i in range(10):
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
            p95_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times)

            results[endpoint] = {
                "average_response_time": avg_time,
                "p95_response_time": p95_time,
                "min_response_time": min(response_times),
                "max_response_time": max(response_times)
            }

            print(f"  Average: {avg_time:.2f}ms, P95: {p95_time:.2f}ms")

    # Print summary
    print("\nPerformance Test Summary:")
    for endpoint, metrics in results.items():
        print(f"{endpoint}:")
        print(f"  Average: {metrics['average_response_time']:.2f}ms")
        print(f"  P95: {metrics['p95_response_time']:.2f}ms")
        print(f"  Range: {metrics['min_response_time']:.2f}ms - {metrics['max_response_time']:.2f}ms")

    print("Production performance tests completed")


if __name__ == "__main__":
    test_production_performance()
