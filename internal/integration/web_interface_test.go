//go:build integration
// +build integration

package integration

import (
	"fmt"
	"net/http"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/arx-os/arxos/pkg/models"
)

// TestWebInterfaceIntegration tests the complete web interface integration
func TestWebInterfaceIntegration(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	// Setup test environment
	config := setupTestEnvironment(t)
	defer config.cleanupTestEnvironment()

	// Get test users
	users := config.getTestUsers(t)

	t.Run("WebAuthenticationFlow", func(t *testing.T) {
		testWebAuthenticationFlow(t, config, users)
	})

	t.Run("WebBuildingManagement", func(t *testing.T) {
		testWebBuildingManagement(t, config, users)
	})

	t.Run("WebSecurityMiddleware", func(t *testing.T) {
		testWebSecurityMiddleware(t, config, users)
	})

	t.Run("WebHTMXEndpoints", func(t *testing.T) {
		testWebHTMXEndpoints(t, config, users)
	})

	t.Run("WebStaticAssets", func(t *testing.T) {
		testWebStaticAssets(t, config)
	})
}

// testWebAuthenticationFlow tests web authentication flows
func testWebAuthenticationFlow(t *testing.T, config *TestConfig, users map[string]*TestUser) {
	t.Run("LoginPage", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/login", nil, "")
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		// Check that it's HTML content
		contentType := resp.Header.Get("Content-Type")
		assert.Contains(t, contentType, "text/html")
	})

	t.Run("RegisterPage", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/register", nil, "")
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		contentType := resp.Header.Get("Content-Type")
		assert.Contains(t, contentType, "text/html")
	})

	t.Run("ForgotPasswordPage", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/forgot-password", nil, "")
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		contentType := resp.Header.Get("Content-Type")
		assert.Contains(t, contentType, "text/html")
	})

	t.Run("ResetPasswordPage", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/reset-password?token=test_token", nil, "")
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		contentType := resp.Header.Get("Content-Type")
		assert.Contains(t, contentType, "text/html")
	})

	t.Run("ProtectedRouteRedirect", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/dashboard", nil, "")
		require.NoError(t, err)
		require.Equal(t, http.StatusSeeOther, resp.StatusCode)

		// Should redirect to login
		location := resp.Header.Get("Location")
		assert.Contains(t, location, "/login")
	})

	t.Run("AuthenticatedAccess", func(t *testing.T) {
		// Create a session by logging in
		loginReq := map[string]string{
			"email":    "test@arxos.io",
			"password": "test_password",
		}

		resp, err := config.makeRequest("POST", "/api/auth/login", loginReq, "")
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		// Extract session cookie
		cookies := resp.Cookies()
		var sessionCookie *http.Cookie
		for _, cookie := range cookies {
			if cookie.Name == "session_id" {
				sessionCookie = cookie
				break
			}
		}
		require.NotNil(t, sessionCookie)

		// Now access protected route with session cookie
		req, err := http.NewRequest("GET", config.Server.URL+"/dashboard", nil)
		require.NoError(t, err)
		req.AddCookie(sessionCookie)

		client := &http.Client{}
		resp, err = client.Do(req)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)
	})
}

// testWebBuildingManagement tests web building management
func testWebBuildingManagement(t *testing.T, config *TestConfig, users map[string]*TestUser) {
	t.Run("BuildingsListPage", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/buildings", nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		contentType := resp.Header.Get("Content-Type")
		assert.Contains(t, contentType, "text/html")
	})

	t.Run("NewBuildingPage", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/buildings/new", nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		contentType := resp.Header.Get("Content-Type")
		assert.Contains(t, contentType, "text/html")
	})

	t.Run("BuildingDetailPage", func(t *testing.T) {
		// First create a building
		building := &models.Building{
			Name:         "Web Test Building",
			Address:      "789 Web Street",
			City:         "Test City",
			Country:      "Test Country",
			PostalCode:   "67890",
			BuildingType: "office",
			Floors:       2,
			GrossArea:    2000.0,
		}

		resp, err := config.makeRequest("POST", "/api/buildings", building, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusCreated, resp.StatusCode)

		var result map[string]interface{}
		err = config.parseJSONResponse(resp, &result)
		require.NoError(t, err)

		buildingID := result["data"].(map[string]interface{})["id"].(string)

		// Now access the building detail page
		resp, err = config.makeRequest("GET", "/buildings/"+buildingID, nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		contentType := resp.Header.Get("Content-Type")
		assert.Contains(t, contentType, "text/html")
	})
}

// testWebSecurityMiddleware tests web security middleware
func testWebSecurityMiddleware(t *testing.T, config *TestConfig, users map[string]*TestUser) {
	t.Run("SecurityHeaders", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/login", nil, "")
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		// Check security headers
		assert.Equal(t, "DENY", resp.Header.Get("X-Frame-Options"))
		assert.Equal(t, "nosniff", resp.Header.Get("X-Content-Type-Options"))
		assert.Equal(t, "1; mode=block", resp.Header.Get("X-XSS-Protection"))
		assert.NotEmpty(t, resp.Header.Get("Content-Security-Policy"))
	})

	t.Run("RateLimiting", func(t *testing.T) {
		// Make multiple requests quickly to test rate limiting
		for i := 0; i < 25; i++ { // Exceed the rate limit of 20
			resp, err := config.makeRequest("GET", "/login", nil, "")
			require.NoError(t, err)

			if i < 20 {
				assert.Equal(t, http.StatusOK, resp.StatusCode)
			} else {
				// Should be rate limited
				assert.Equal(t, http.StatusTooManyRequests, resp.StatusCode)
			}
		}
	})

	t.Run("CSRFProtection", func(t *testing.T) {
		// Try to make a POST request without CSRF token
		loginReq := map[string]string{
			"email":    "test@arxos.io",
			"password": "test_password",
		}

		resp, err := config.makeRequest("POST", "/api/auth/login", loginReq, "")
		require.NoError(t, err)

		// Should still work as login is excluded from CSRF protection
		assert.Equal(t, http.StatusOK, resp.StatusCode)
	})
}

// testWebHTMXEndpoints tests HTMX endpoints
func testWebHTMXEndpoints(t *testing.T, config *TestConfig, users map[string]*TestUser) {
	t.Run("GlobalSearch", func(t *testing.T) {
		params := "?q=test"
		resp, err := config.makeRequest("GET", "/htmx/search"+params, nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		contentType := resp.Header.Get("Content-Type")
		assert.Contains(t, contentType, "text/html")
	})

	t.Run("SearchSuggestions", func(t *testing.T) {
		params := "?q=test"
		resp, err := config.makeRequest("GET", "/htmx/search/suggestions"+params, nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		contentType := resp.Header.Get("Content-Type")
		assert.Contains(t, contentType, "text/html")
	})

	t.Run("RecentSearches", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/htmx/search/recent", nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		contentType := resp.Header.Get("Content-Type")
		assert.Contains(t, contentType, "text/html")
	})

	t.Run("Notifications", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/htmx/notifications", nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		contentType := resp.Header.Get("Content-Type")
		assert.Contains(t, contentType, "text/html")
	})
}

// testWebStaticAssets tests static asset serving
func testWebStaticAssets(t *testing.T, config *TestConfig) {
	t.Run("StaticAssets", func(t *testing.T) {
		// Test that static assets are served
		resp, err := config.makeRequest("GET", "/static/css/main.css", nil, "")
		require.NoError(t, err)

		// Should either return the file or 404 if it doesn't exist
		assert.True(t, resp.StatusCode == http.StatusOK || resp.StatusCode == http.StatusNotFound)
	})

	t.Run("Favicon", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/favicon.ico", nil, "")
		require.NoError(t, err)

		// Should either return the file or 404 if it doesn't exist
		assert.True(t, resp.StatusCode == http.StatusOK || resp.StatusCode == http.StatusNotFound)
	})
}

// TestWebInterfacePerformance tests web interface performance
func TestWebInterfacePerformance(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping performance test in short mode")
	}

	config := setupTestEnvironment(t)
	defer config.cleanupTestEnvironment()

	users := config.getTestUsers(t)

	t.Run("ConcurrentWebRequests", func(t *testing.T) {
		const numConcurrent = 50
		results := make(chan error, numConcurrent)

		for i := 0; i < numConcurrent; i++ {
			go func(i int) {
				resp, err := config.makeRequest("GET", "/login", nil, "")
				if err != nil {
					results <- err
					return
				}

				if resp.StatusCode != http.StatusOK {
					results <- fmt.Errorf("expected status 200, got %d", resp.StatusCode)
					return
				}

				results <- nil
			}(i)
		}

		// Wait for all requests to complete
		for i := 0; i < numConcurrent; i++ {
			select {
			case err := <-results:
				require.NoError(t, err)
			case <-time.After(30 * time.Second):
				t.Fatal("Concurrent web requests timed out")
			}
		}
	})

	t.Run("ResponseTime", func(t *testing.T) {
		start := time.Now()
		resp, err := config.makeRequest("GET", "/login", nil, "")
		duration := time.Since(start)

		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		// Response should be fast (less than 1 second)
		assert.Less(t, duration, time.Second)
	})
}
