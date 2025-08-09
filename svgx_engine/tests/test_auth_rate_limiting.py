import pytest
import time
import jwt
from fastapi.testclient import TestClient
from svgx_engine.services.api_interface import app
from svgx_engine.services.auth_middleware import auth_middleware, SECRET_KEY, ALGORITHM
from svgx_engine.services.rate_limiter import rate_limiter

class TestAuthenticationAndRateLimiting:
    """Test suite for authentication and rate limiting functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.test_user_email = "editor@example.com"
        self.test_password = "password"
        self.access_token = None

    def test_login_success(self):
        """Test successful login."""
        response = self.client.post("/auth/login", json={
            "email": self.test_user_email,
            "password": self.test_password
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 1800
        assert "user" in data
        assert data["user"]["email"] == self.test_user_email

        # Store token for other tests
        self.access_token = data["access_token"]

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = self.client.post("/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })

        assert response.status_code == 401
        data = response.json()
        assert data["status"] == "error"
        assert "Invalid credentials" in data["message"]

    def test_login_missing_fields(self):
        """Test login with missing fields."""
        response = self.client.post("/auth/login", json={})
        assert response.status_code == 400

        response = self.client.post("/auth/login", json={"email": "test@example.com"})
        assert response.status_code == 400

    def test_refresh_token(self):
        """Test token refresh."""
        # First login to get token
        login_response = self.client.post("/auth/login", json={
            "email": self.test_user_email,
            "password": self.test_password
        })
        token = login_response.json()["access_token"]

        # Refresh token
        response = self.client.post("/auth/refresh", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_invalid(self):
        """Test token refresh with invalid token."""
        response = self.client.post("/auth/refresh", headers={
            "Authorization": "Bearer invalid_token"
        })

        assert response.status_code == 401

    def test_get_current_user_info(self):
        """Test getting current user information."""
        # First login to get token
        login_response = self.client.post("/auth/login", json={
            "email": self.test_user_email,
            "password": self.test_password
        })
        token = login_response.json()["access_token"]

        response = self.client.get("/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "user" in data
        assert data["user"]["email"] == self.test_user_email
        assert "permissions" in data["user"]

    def test_protected_endpoint_with_auth(self):
        """Test accessing protected endpoint with valid authentication."""
        # First login to get token
        login_response = self.client.post("/auth/login", json={
            "email": self.test_user_email,
            "password": self.test_password
        })
        token = login_response.json()["access_token"]

        # Access protected endpoint
        response = self.client.get("/metrics/", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response.status_code == 200

    def test_protected_endpoint_without_auth(self):
        """Test accessing protected endpoint without authentication."""
        response = self.client.get("/metrics/")
        assert response.status_code == 401

    def test_protected_endpoint_with_invalid_token(self):
        """Test accessing protected endpoint with invalid token."""
        response = self.client.get("/metrics/", headers={
            "Authorization": "Bearer invalid_token"
        })
        assert response.status_code == 401

    def test_admin_endpoint_access(self):
        """Test admin-only endpoint access."""
        # Login as admin
        admin_response = self.client.post("/auth/login", json={
            "email": "admin@example.com",
            "password": "password"
        })
        admin_token = admin_response.json()["access_token"]

        # Login as editor
        editor_response = self.client.post("/auth/login", json={
            "email": "editor@example.com",
            "password": "password"
        })
        editor_token = editor_response.json()["access_token"]

        # Admin should be able to access admin endpoint
        admin_response = self.client.get("/errors/stats/", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert admin_response.status_code == 200

        # Editor should not be able to access admin endpoint
        editor_response = self.client.get("/errors/stats/", headers={
            "Authorization": f"Bearer {editor_token}"
        })
        assert editor_response.status_code == 403

    def test_rate_limiting_basic(self):
        """Test basic rate limiting functionality."""
        # Make multiple requests quickly
        responses = []
        for i in range(35):  # Exceed the 30 requests per minute limit for POST
            response = self.client.post("/runtime/ui-event/", json={
                "event_type": "test",
                "canvas_id": "test-canvas"
            })
            responses.append(response)

        # Check that some requests were rate limited
        rate_limited_count = sum(1 for r in responses if r.status_code == 429)
        assert rate_limited_count > 0

        # Check rate limit headers
        for response in responses:
            if response.status_code == 200:
                assert "X-RateLimit-Limit" in response.headers
                assert "X-RateLimit-Remaining" in response.headers

    def test_rate_limiting_different_endpoints(self):
        """Test rate limiting on different endpoints."""
        # Test GET endpoint (60 requests per minute)
        responses = []
        for i in range(65):  # Exceed the 60 requests per minute limit for GET
            response = self.client.get("/health/")
            responses.append(response)

        rate_limited_count = sum(1 for r in responses if r.status_code == 429)
        assert rate_limited_count > 0

    def test_rate_limiting_custom_limits(self):
        """Test custom rate limits for specific endpoints."""
        # Test metrics endpoint (10 requests per minute)
        responses = []
        for i in range(15):  # Exceed the 10 requests per minute limit
            response = self.client.get("/metrics/", headers={
                "Authorization": f"Bearer {self.access_token}" if self.access_token else ""
            })
            responses.append(response)

        rate_limited_count = sum(1 for r in responses if r.status_code == 429)
        assert rate_limited_count > 0

    def test_rate_limiting_by_user(self):
        """Test that rate limiting is per-user."""
        # Login as different users
        user1_response = self.client.post("/auth/login", json={
            "email": "editor@example.com",
            "password": "password"
        })
        user1_token = user1_response.json()["access_token"]

        user2_response = self.client.post("/auth/login", json={
            "email": "viewer@example.com",
            "password": "password"
        })
        user2_token = user2_response.json()["access_token"]

        # Make requests as user1
        user1_responses = []
        for i in range(25):  # Under the limit
            response = self.client.get("/health/", headers={
                "Authorization": f"Bearer {user1_token}"
            })
            user1_responses.append(response)

        # Make requests as user2
        user2_responses = []
        for i in range(25):  # Under the limit
            response = self.client.get("/health/", headers={
                "Authorization": f"Bearer {user2_token}"
            })
            user2_responses.append(response)

        # Both users should be able to make requests
        user1_success = sum(1 for r in user1_responses if r.status_code == 200)
        user2_success = sum(1 for r in user2_responses if r.status_code == 200)

        assert user1_success > 0
        assert user2_success > 0

    def test_token_expiration(self):
        """Test that expired tokens are rejected."""
        # Create an expired token
        expired_token_data = {
            "sub": "test-user",
            "username": "test",
            "role": "editor",
            "exp": time.time() - 3600  # Expired 1 hour ago
        }
        expired_token = jwt.encode(expired_token_data, SECRET_KEY, algorithm=ALGORITHM)

        response = self.client.get("/metrics/", headers={
            "Authorization": f"Bearer {expired_token}"
        })

        assert response.status_code == 401

    def test_invalid_token_format(self):
        """Test handling of invalid token formats."""
        response = self.client.get("/metrics/", headers={
            "Authorization": "Bearer invalid.token.format"
        })

        assert response.status_code == 401

    def test_missing_authorization_header(self):
        """Test handling of missing authorization header."""
        response = self.client.get("/metrics/")
        assert response.status_code == 401

    def test_public_endpoints_no_auth_required(self):
        """Test that public endpoints don't require authentication."""
        # Root endpoint
        response = self.client.get("/")
        assert response.status_code == 200

        # Health endpoints
        response = self.client.get("/health/")
        assert response.status_code == 200

        response = self.client.get("/health/summary/")
        assert response.status_code == 200

    def test_permission_based_access(self):
        """Test permission-based access control."""
        # Login as different user types
        admin_response = self.client.post("/auth/login", json={
            "email": "admin@example.com",
            "password": "password"
        })
        admin_token = admin_response.json()["access_token"]

        viewer_response = self.client.post("/auth/login", json={
            "email": "viewer@example.com",
            "password": "password"
        })
        viewer_token = viewer_response.json()["access_token"]

        # Test write permission required endpoint
        write_endpoint_data = {
            "event_type": "test",
            "canvas_id": "test-canvas"
        }

        # Admin should have write permission
        admin_write_response = self.client.post("/runtime/ui-event/",
            json=write_endpoint_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert admin_write_response.status_code == 200

        # Viewer should not have write permission
        viewer_write_response = self.client.post("/runtime/ui-event/",
            json=write_endpoint_data,
            headers={"Authorization": f"Bearer {viewer_token}"}
        )
        assert viewer_write_response.status_code == 403

    def test_rate_limit_headers(self):
        """Test that rate limit headers are present."""
        response = self.client.get("/health/")

        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers

        # Check that headers have valid values
        limit = int(response.headers["X-RateLimit-Limit"])
        remaining = int(response.headers["X-RateLimit-Remaining"])

        assert limit > 0
        assert remaining >= 0
        assert remaining <= limit

    def test_rate_limit_retry_after(self):
        """Test rate limit retry-after header."""
        # Make enough requests to trigger rate limiting
        responses = []
        for i in range(35):  # Exceed POST limit
            response = self.client.post("/runtime/ui-event/", json={
                "event_type": "test",
                "canvas_id": "test-canvas"
            })
            responses.append(response)

        # Find a rate limited response
        rate_limited_response = None
        for response in responses:
            if response.status_code == 429:
                rate_limited_response = response
                break

        assert rate_limited_response is not None
        assert "Retry-After" in rate_limited_response.headers

        retry_after = int(rate_limited_response.headers["Retry-After"])
        assert retry_after > 0

    def test_rate_limit_error_response(self):
        """Test rate limit error response format."""
        # Make enough requests to trigger rate limiting
        responses = []
        for i in range(35):  # Exceed POST limit
            response = self.client.post("/runtime/ui-event/", json={
                "event_type": "test",
                "canvas_id": "test-canvas"
            })
            responses.append(response)

        # Find a rate limited response
        rate_limited_response = None
        for response in responses:
            if response.status_code == 429:
                rate_limited_response = response
                break

        assert rate_limited_response is not None

        data = rate_limited_response.json()
        assert data["status"] == "error"
        assert data["error_code"] == "RATE_LIMIT_EXCEEDED"
        assert "retry_after_seconds" in data
        assert "rate_limit_info" in data

    def test_authentication_logging(self):
        """Test that authentication events are logged."""
        # This is a basic test - in a real implementation, you'd check logs'
        response = self.client.post("/auth/login", json={
            "email": self.test_user_email,
            "password": self.test_password
        })

        assert response.status_code == 200
        # Authentication logging would be verified by checking logs

    def test_rate_limit_cleanup(self):
        """Test rate limit cleanup functionality."""
        # This is a basic test - in a real implementation, you'd verify cleanup'
        # The cleanup happens in the background, so we just test that it doesn't break'
        rate_limiter.cleanup_expired_buckets()
        # No assertion needed - just checking it doesn't raise an exception'

    def test_token_validation_edge_cases(self):
        """Test token validation edge cases."""
        # Test with malformed token
        response = self.client.get("/metrics/", headers={
            "Authorization": "Bearer malformed.token.here"
        })
        assert response.status_code == 401

        # Test with empty token
        response = self.client.get("/metrics/", headers={
            "Authorization": "Bearer "
        })
        assert response.status_code == 401

        # Test with wrong token type
        response = self.client.get("/metrics/", headers={
            "Authorization": "Basic dGVzdDp0ZXN0"
        })
        assert response.status_code == 401
