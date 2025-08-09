"""
Post-deployment security tests for Arxos platform.
"""
import requests
import json


def test_post_deployment_security():
    """Test security after deployment."""
    print("Running post-deployment security tests...")

    base_url = "https://arxos.com"

    # Test HTTPS enforcement
    try:
        response = requests.get(f"http://arxos.com/health", timeout=10, allow_redirects=False)
        if response.status_code in [301, 302, 307, 308]:
            print("✅ HTTPS enforcement - PASSED (redirects to HTTPS)")
        else:
            print(f"❌ HTTPS enforcement - FAILED (status: {response.status_code})")
    except Exception as e:
        print(f"❌ HTTPS enforcement - ERROR: {e}")

    # Test security headers
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        headers = response.headers

        security_headers = {
            "Strict-Transport-Security": "HSTS header",
            "X-Content-Type-Options": "Content type options",
            "X-Frame-Options": "Frame options",
            "X-XSS-Protection": "XSS protection",
            "Content-Security-Policy": "CSP header"
        }

        for header, description in security_headers.items():
            if header in headers:
                print(f"✅ {description} - PASSED")
            else:
                print(f"❌ {description} - MISSING")

    except Exception as e:
        print(f"❌ Security headers test - ERROR: {e}")

    # Test authentication endpoints
    auth_endpoints = [
        "/api/v1/auth/login",
        "/api/v1/auth/logout",
        "/api/v1/auth/refresh"
    ]

    for endpoint in auth_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 405:  # Method not allowed for GET
                print(f"✅ {endpoint} - PASSED (proper method restriction)")
            else:
                print(f"❌ {endpoint} - FAILED (unexpected status: {response.status_code})")
        except Exception as e:
            print(f"❌ {endpoint} - ERROR: {e}")

    # Test rate limiting (basic check)
    try:
        # Make multiple rapid requests to test rate limiting
        responses = []
        for i in range(10):
            response = requests.get(f"{base_url}/health", timeout=5)
            responses.append(response.status_code)

        # Check if any requests were rate limited (429 status)
        if 429 in responses:
            print("✅ Rate limiting - PASSED (rate limiting detected)")
        else:
            print("⚠️  Rate limiting - NOT DETECTED (may be disabled in test)")

    except Exception as e:
        print(f"❌ Rate limiting test - ERROR: {e}")

    # Test CORS headers
    try:
        response = requests.options(f"{base_url}/api/v1/health", timeout=10)
        if "Access-Control-Allow-Origin" in response.headers:
            print("✅ CORS headers - PASSED")
        else:
            print("❌ CORS headers - MISSING")
    except Exception as e:
        print(f"❌ CORS headers test - ERROR: {e}")

    print("Post-deployment security tests completed")


if __name__ == "__main__":
    test_post_deployment_security()
