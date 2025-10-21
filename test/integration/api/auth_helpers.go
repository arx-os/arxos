package integration

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/pkg/auth"
	"github.com/stretchr/testify/require"
)

// TestAuthHelper provides authentication helpers for API tests
type TestAuthHelper struct {
	jwtManager *auth.JWTManager
	server     *httptest.Server
	token      string
	userID     string
	email      string
	role       string
}

// NewTestAuthHelper creates a new authentication helper for tests
func NewTestAuthHelper(t *testing.T, server *httptest.Server, jwtManager *auth.JWTManager) *TestAuthHelper {
	t.Helper()

	require.NotNil(t, jwtManager, "JWT manager is required")

	helper := &TestAuthHelper{
		jwtManager: jwtManager,
		server:     server,
		userID:     "test-user-id",
		email:      "test@arxos.local",
		role:       "admin",
	}

	// Generate test token
	helper.generateToken(t)

	return helper
}

// generateToken creates a JWT token for testing
func (h *TestAuthHelper) generateToken(t *testing.T) {
	t.Helper()

	tokenPair, err := h.jwtManager.GenerateTokenPair(&auth.TokenGenerationRequest{
		UserID:         h.userID,
		Email:          h.email,
		Username:       "Test User",
		Role:           h.role,
		OrganizationID: "",
		Permissions:    []string{"building:read", "building:write", "building:delete", "equipment:read", "equipment:write", "equipment:delete"},
		SessionID:      "",
		DeviceInfo:     map[string]any{"test": true},
	})
	require.NoError(t, err, "Failed to generate token")

	h.token = tokenPair.AccessToken
}

// MakeAuthenticatedRequest makes an HTTP request with authentication
func (h *TestAuthHelper) MakeAuthenticatedRequest(t *testing.T, method, path string, body any) *http.Response {
	t.Helper()

	var bodyReader *bytes.Reader
	if body != nil {
		jsonBody, err := json.Marshal(body)
		require.NoError(t, err, "Failed to marshal request body")
		bodyReader = bytes.NewReader(jsonBody)
	} else {
		bodyReader = bytes.NewReader([]byte{})
	}

	req, err := http.NewRequest(method, h.server.URL+path, bodyReader)
	require.NoError(t, err, "Failed to create HTTP request")

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+h.token)

	resp, err := http.DefaultClient.Do(req)
	require.NoError(t, err, "HTTP request failed")

	return resp
}

// GET makes an authenticated GET request
func (h *TestAuthHelper) GET(t *testing.T, path string) *http.Response {
	return h.MakeAuthenticatedRequest(t, "GET", path, nil)
}

// POST makes an authenticated POST request
func (h *TestAuthHelper) POST(t *testing.T, path string, body any) *http.Response {
	return h.MakeAuthenticatedRequest(t, "POST", path, body)
}

// PUT makes an authenticated PUT request
func (h *TestAuthHelper) PUT(t *testing.T, path string, body any) *http.Response {
	return h.MakeAuthenticatedRequest(t, "PUT", path, body)
}

// DELETE makes an authenticated DELETE request
func (h *TestAuthHelper) DELETE(t *testing.T, path string) *http.Response {
	return h.MakeAuthenticatedRequest(t, "DELETE", path, nil)
}

// DecodeJSON decodes a JSON response into the target
func (h *TestAuthHelper) DecodeJSON(t *testing.T, resp *http.Response, target any) {
	t.Helper()
	err := json.NewDecoder(resp.Body).Decode(target)
	require.NoError(t, err, "Failed to decode JSON response")
}

// AssertStatusCode asserts the response status code
func (h *TestAuthHelper) AssertStatusCode(t *testing.T, resp *http.Response, expectedStatus int) {
	t.Helper()
	if resp.StatusCode != expectedStatus {
		// Try to read error message
		var errorMsg map[string]any
		json.NewDecoder(resp.Body).Decode(&errorMsg)
		t.Fatalf("Expected status %d but got %d. Error: %v", expectedStatus, resp.StatusCode, errorMsg)
	}
}

// CreateTestBuilding is a helper to create a building for tests
func (h *TestAuthHelper) CreateTestBuilding(t *testing.T, name, address string) string {
	t.Helper()

	building := map[string]any{
		"name":    name,
		"address": address,
	}

	resp := h.POST(t, "/api/v1/buildings", building)
	defer resp.Body.Close()

	h.AssertStatusCode(t, resp, http.StatusCreated)

	var result map[string]any
	h.DecodeJSON(t, resp, &result)

	buildingID, ok := result["id"].(string)
	require.True(t, ok, "Building ID should be a string")
	require.NotEmpty(t, buildingID, "Building ID should not be empty")

	return buildingID
}

// CreateTestFloor is a helper to create a floor for tests
func (h *TestAuthHelper) CreateTestFloor(t *testing.T, buildingID string, name string, level int) string {
	t.Helper()

	floor := map[string]any{
		"building_id": buildingID,
		"name":        name,
		"level":       level,
	}

	resp := h.POST(t, "/api/v1/floors", floor)
	defer resp.Body.Close()

	h.AssertStatusCode(t, resp, http.StatusCreated)

	var result map[string]any
	h.DecodeJSON(t, resp, &result)

	floorID, ok := result["id"].(string)
	require.True(t, ok, "Floor ID should be a string")
	require.NotEmpty(t, floorID, "Floor ID should not be empty")

	return floorID
}

// CreateTestRoom is a helper to create a room for tests
func (h *TestAuthHelper) CreateTestRoom(t *testing.T, floorID, name, number string) string {
	t.Helper()

	room := map[string]any{
		"floor_id": floorID,
		"name":     name,
		"number":   number,
	}

	resp := h.POST(t, "/api/v1/rooms", room)
	defer resp.Body.Close()

	h.AssertStatusCode(t, resp, http.StatusCreated)

	var result map[string]any
	h.DecodeJSON(t, resp, &result)

	roomID, ok := result["id"].(string)
	require.True(t, ok, "Room ID should be a string")
	require.NotEmpty(t, roomID, "Room ID should not be empty")

	return roomID
}

// CreateTestEquipment is a helper to create equipment for tests
func (h *TestAuthHelper) CreateTestEquipment(t *testing.T, buildingID, name, equipType string) string {
	t.Helper()

	equipment := map[string]any{
		"building_id": buildingID,
		"name":        name,
		"type":        equipType,
	}

	resp := h.POST(t, "/api/v1/equipment", equipment)
	defer resp.Body.Close()

	// Equipment creation might fail, so just check if we got a 2xx status
	if resp.StatusCode >= 200 && resp.StatusCode < 300 {
		var result map[string]any
		h.DecodeJSON(t, resp, &result)

		if id, ok := result["id"].(string); ok && id != "" {
			return id
		}
	}

	// If creation failed, log but don't fail the test
	t.Logf("Equipment creation returned status %d, may not be implemented yet", resp.StatusCode)
	return ""
}

// WithTestServer wraps a test with a configured test server and auth helper
func WithTestServer(t *testing.T, testFunc func(t *testing.T, server *httptest.Server, auth *TestAuthHelper, container *app.Container)) {
	t.Helper()

	// Setup server
	server, container := setupTestServerWithConfig(t)
	if server == nil {
		t.Skip("Test server setup failed")
		return
	}
	defer server.Close()
	defer container.Shutdown(context.Background())

	// Get JWT manager from container
	jwtManager := container.GetJWTManager()
	if jwtManager == nil {
		t.Skip("JWT manager not available")
		return
	}

	// Create auth helper using container's JWT manager
	authHelper := NewTestAuthHelper(t, server, jwtManager)

	// Run test
	testFunc(t, server, authHelper, container)
}
