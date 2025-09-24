package integration

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/arx-os/arxos/internal/api/types"
	"github.com/arx-os/arxos/internal/handlers/web"
	"github.com/arx-os/arxos/pkg/models"
)

// TestAuthenticationFlow tests the complete authentication workflow
func TestAuthenticationFlow(t *testing.T) {
	// Setup test environment
	ctx := context.Background()
	services, cleanup := setupTestServices(t)
	defer cleanup()

	// Create test user
	user := &models.User{
		ID:           "test-user-1",
		Email:        "test@arxos.io",
		FullName:     "Test User",
		Role:         "user",
		PasswordHash: "hashed_password", // In real test, use proper hash
		IsActive:     true,
	}

	// Save user to database
	_, err := services.User.CreateUser(ctx, user.Email, "testpassword", user.FullName)
	require.NoError(t, err)

	// Create handler with auth service
	typesServices := &types.Services{
		DB:   services.DB,
		User: services.User,
	}
	handler, err := web.NewHandler(typesServices)
	require.NoError(t, err)

	router := web.NewAuthenticatedRouter(handler)
	server := httptest.NewServer(router)
	defer server.Close()

	t.Run("LoginSuccess", func(t *testing.T) {
		// Prepare login request
		loginReq := map[string]string{
			"email":    "test@arxos.io",
			"password": "test_password",
		}
		body, _ := json.Marshal(loginReq)

		// Send login request
		resp, err := http.Post(server.URL+"/api/auth/login", "application/json", bytes.NewReader(body))
		require.NoError(t, err)
		defer resp.Body.Close()

		// Check response
		assert.Equal(t, http.StatusOK, resp.StatusCode)

		// Parse response
		var loginResp map[string]interface{}
		err = json.NewDecoder(resp.Body).Decode(&loginResp)
		require.NoError(t, err)

		// Verify token exists
		assert.NotEmpty(t, loginResp["token"])
		assert.NotEmpty(t, loginResp["expires_at"])
		assert.NotNil(t, loginResp["user"])

		// Extract token for subsequent requests
		token := loginResp["token"].(string)
		assert.NotEmpty(t, token)
	})

	t.Run("LoginInvalidCredentials", func(t *testing.T) {
		loginReq := map[string]string{
			"email":    "test@arxos.io",
			"password": "wrong_password",
		}
		body, _ := json.Marshal(loginReq)

		resp, err := http.Post(server.URL+"/api/auth/login", "application/json", bytes.NewReader(body))
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusUnauthorized, resp.StatusCode)
	})

	t.Run("AccessProtectedRouteWithoutAuth", func(t *testing.T) {
		resp, err := http.Get(server.URL + "/buildings")
		require.NoError(t, err)
		defer resp.Body.Close()

		// Should redirect to login
		assert.Equal(t, http.StatusSeeOther, resp.StatusCode)
	})

	t.Run("AccessProtectedRouteWithAuth", func(t *testing.T) {
		// First login to get token
		loginReq := map[string]string{
			"email":    "test@arxos.io",
			"password": "test_password",
		}
		body, _ := json.Marshal(loginReq)

		resp, err := http.Post(server.URL+"/api/auth/login", "application/json", bytes.NewReader(body))
		require.NoError(t, err)

		var loginResp map[string]interface{}
		json.NewDecoder(resp.Body).Decode(&loginResp)
		resp.Body.Close()

		token := loginResp["token"].(string)

		// Access protected route with token
		req, _ := http.NewRequest("GET", server.URL+"/api/buildings", nil)
		req.Header.Set("Authorization", "Bearer "+token)

		client := &http.Client{}
		resp, err = client.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		// Should be able to access
		assert.NotEqual(t, http.StatusUnauthorized, resp.StatusCode)
	})

	t.Run("Logout", func(t *testing.T) {
		// Login first
		loginReq := map[string]string{
			"email":    "test@arxos.io",
			"password": "test_password",
		}
		body, _ := json.Marshal(loginReq)

		resp, err := http.Post(server.URL+"/api/auth/login", "application/json", bytes.NewReader(body))
		require.NoError(t, err)

		var loginResp map[string]interface{}
		json.NewDecoder(resp.Body).Decode(&loginResp)
		resp.Body.Close()

		token := loginResp["token"].(string)

		// Logout
		req, _ := http.NewRequest("POST", server.URL+"/api/auth/logout", nil)
		req.Header.Set("Authorization", "Bearer "+token)

		client := &http.Client{}
		resp, err = client.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusNoContent, resp.StatusCode)

		// Try to access protected route with same token (should fail)
		req, _ = http.NewRequest("GET", server.URL+"/api/buildings", nil)
		req.Header.Set("Authorization", "Bearer "+token)

		resp, err = client.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		// Token should be invalidated
		assert.Equal(t, http.StatusUnauthorized, resp.StatusCode)
	})
}

// TestRoleBasedAuthorization tests role-based access control
func TestRoleBasedAuthorization(t *testing.T) {
	ctx := context.Background()
	services, cleanup := setupTestServices(t)
	defer cleanup()

	// Create users with different roles
	users := []struct {
		user  *models.User
		token string
	}{
		{
			user: &models.User{
				ID:       "admin-1",
				Email:    "admin@arxos.io",
				FullName: "Admin User",
				Role:     "admin",
				IsActive: true,
			},
		},
		{
			user: &models.User{
				ID:       "user-1",
				Email:    "user@arxos.io",
				FullName: "Regular User",
				Role:     "user",
				IsActive: true,
			},
		},
		{
			user: &models.User{
				ID:       "viewer-1",
				Email:    "viewer@arxos.io",
				FullName: "Viewer User",
				Role:     "viewer",
				IsActive: true,
			},
		},
	}

	// Create users and get tokens
	for i := range users {
		_, err := services.User.CreateUser(ctx, users[i].user.Email, "testpassword", users[i].user.FullName)
		require.NoError(t, err)
		// Get token for each user (simplified for test)
		users[i].token = "test-token-" + users[i].user.Role
	}

	typesServices := &types.Services{
		DB:   services.DB,
		User: services.User,
	}
	handler, err := web.NewHandler(typesServices)
	require.NoError(t, err)

	router := web.NewAuthenticatedRouter(handler)
	server := httptest.NewServer(router)
	defer server.Close()

	tests := []struct {
		name           string
		endpoint       string
		method         string
		role           string
		expectedStatus int
	}{
		// Admin can do everything
		{"AdminDeleteBuilding", "/buildings/123", "DELETE", "admin", http.StatusNotImplemented},
		{"AdminCreateBuilding", "/buildings/new", "POST", "admin", http.StatusNotImplemented},

		// User can create/update but not delete
		{"UserCreateBuilding", "/buildings/new", "POST", "user", http.StatusNotImplemented},
		{"UserDeleteBuilding", "/buildings/123", "DELETE", "user", http.StatusForbidden},

		// Viewer can only read
		{"ViewerReadBuilding", "/buildings", "GET", "viewer", http.StatusOK},
		{"ViewerCreateBuilding", "/buildings/new", "POST", "viewer", http.StatusForbidden},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Find user with matching role
			var token string
			for _, u := range users {
				if u.user.Role == tt.role {
					token = u.token
					break
				}
			}

			req, _ := http.NewRequest(tt.method, server.URL+tt.endpoint, nil)
			req.Header.Set("Authorization", "Bearer "+token)

			client := &http.Client{
				CheckRedirect: func(req *http.Request, via []*http.Request) error {
					return http.ErrUseLastResponse
				},
			}

			resp, err := client.Do(req)
			require.NoError(t, err)
			defer resp.Body.Close()

			assert.Equal(t, tt.expectedStatus, resp.StatusCode,
				"Expected %d for %s accessing %s, got %d",
				tt.expectedStatus, tt.role, tt.endpoint, resp.StatusCode)
		})
	}
}

// TestSessionManagement tests session creation and management
func TestSessionManagement(t *testing.T) {
	// Create session store
	sessionStore := web.NewMemorySessionStore(1 * time.Minute)
	defer sessionStore.Close()

	t.Run("CreateSession", func(t *testing.T) {
		session := &web.Session{
			ID:        "test-session-1",
			UserID:    "user-1",
			Email:     "test@arxos.io",
			Name:      "Test User",
			Role:      "user",
			ExpiresAt: time.Now().Add(1 * time.Hour),
			CreatedAt: time.Now(),
		}

		err := sessionStore.Set(session.ID, session)
		assert.NoError(t, err)

		// Retrieve session
		retrieved, err := sessionStore.Get(session.ID)
		assert.NoError(t, err)
		assert.Equal(t, session.UserID, retrieved.UserID)
		assert.Equal(t, session.Email, retrieved.Email)
	})

	t.Run("ExpiredSession", func(t *testing.T) {
		session := &web.Session{
			ID:        "expired-session",
			UserID:    "user-1",
			ExpiresAt: time.Now().Add(-1 * time.Hour), // Already expired
		}

		err := sessionStore.Set(session.ID, session)
		assert.NoError(t, err)

		// Try to retrieve expired session
		_, err = sessionStore.Get(session.ID)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "expired")
	})

	t.Run("DeleteSession", func(t *testing.T) {
		session := &web.Session{
			ID:        "delete-session",
			UserID:    "user-1",
			ExpiresAt: time.Now().Add(1 * time.Hour),
		}

		err := sessionStore.Set(session.ID, session)
		assert.NoError(t, err)

		// Delete session
		err = sessionStore.Delete(session.ID)
		assert.NoError(t, err)

		// Try to retrieve deleted session
		_, err = sessionStore.Get(session.ID)
		assert.Error(t, err)
	})

	t.Run("SessionCleanup", func(t *testing.T) {
		// Create multiple sessions
		for i := 0; i < 5; i++ {
			session := &web.Session{
				ID:        fmt.Sprintf("session-%d", i),
				UserID:    fmt.Sprintf("user-%d", i),
				ExpiresAt: time.Now().Add(-1 * time.Hour), // All expired
			}
			sessionStore.Set(session.ID, session)
		}

		// Wait for cleanup (cleanup interval is 1 minute in test)
		time.Sleep(2 * time.Second)

		// Force cleanup - wait for automatic cleanup
		time.Sleep(100 * time.Millisecond)

		// Check that expired sessions are removed
		assert.Equal(t, 0, sessionStore.Count())
	})
}
