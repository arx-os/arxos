package integration

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/internal/domain"
	httprouter "github.com/arx-os/arxos/internal/interfaces/http"
	"github.com/arx-os/arxos/pkg/auth"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestFloorRoomRESTAPI(t *testing.T) {
	// Setup test container and router
	container, cleanup := setupTestContainerLegacy(t)
	defer cleanup()

	jwtConfig := &auth.JWTConfig{
		SecretKey:          "test-secret-key-for-integration-testing",
		AccessTokenExpiry:  24 * 60 * 60,      // 24 hours
		RefreshTokenExpiry: 30 * 24 * 60 * 60, // 30 days
		Issuer:             "arxos-test",
		Audience:           "arxos-api",
		Algorithm:          "HS256",
	}

	routerConfig, err := httprouter.NewRouterConfig(nil, container, jwtConfig)
	require.NoError(t, err)

	router := httprouter.NewRouter(routerConfig)

	// Generate test JWT token using the same manager from routerConfig
	tokenPair, err := routerConfig.JWTManager.GenerateTokenPair("test-user-id", "test@example.com", "test-user", string(auth.RoleAdmin), "test-org-id", []string{}, "test-session", nil)
	require.NoError(t, err)
	token := tokenPair.AccessToken

	// Test data
	var buildingID, floorID, roomID string

	t.Run("Create Building First", func(t *testing.T) {
		reqBody := map[string]any{
			"name":    "Test Building for Floors",
			"address": "123 Test St",
		}
		body, _ := json.Marshal(reqBody)

		req := httptest.NewRequest(http.MethodPost, "/api/v1/buildings", bytes.NewReader(body))
		req.Header.Set("Authorization", "Bearer "+token)
		req.Header.Set("Content-Type", "application/json")

		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusCreated, w.Code)

		var building domain.Building
		err := json.Unmarshal(w.Body.Bytes(), &building)
		require.NoError(t, err)
		buildingID = building.ID.String()
		fmt.Printf("✅ Created building: %s\n", buildingID)
	})

	t.Run("Create Floor", func(t *testing.T) {
		reqBody := map[string]any{
			"building_id": buildingID,
			"name":        "Ground Floor",
			"level":       0,
		}
		body, _ := json.Marshal(reqBody)

		req := httptest.NewRequest(http.MethodPost, "/api/v1/floors", bytes.NewReader(body))
		req.Header.Set("Authorization", "Bearer "+token)
		req.Header.Set("Content-Type", "application/json")

		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusCreated, w.Code)

		var floor domain.Floor
		err := json.Unmarshal(w.Body.Bytes(), &floor)
		require.NoError(t, err)
		floorID = floor.ID.String()
		assert.Equal(t, "Ground Floor", floor.Name)
		assert.Equal(t, 0, floor.Level)
		fmt.Printf("✅ Created floor: %s\n", floorID)
	})

	t.Run("Get Floor by ID", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/api/v1/floors/"+floorID, nil)
		req.Header.Set("Authorization", "Bearer "+token)

		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var floor domain.Floor
		err := json.Unmarshal(w.Body.Bytes(), &floor)
		require.NoError(t, err)
		assert.Equal(t, floorID, floor.ID.String())
		assert.Equal(t, "Ground Floor", floor.Name)
		fmt.Printf("✅ Retrieved floor: %s\n", floorID)
	})

	t.Run("List Floors by Building", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/api/v1/floors?building_id="+buildingID, nil)
		req.Header.Set("Authorization", "Bearer "+token)

		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response map[string]any
		err := json.Unmarshal(w.Body.Bytes(), &response)
		require.NoError(t, err)
		assert.NotNil(t, response["floors"])
		floors := response["floors"].([]any)
		assert.GreaterOrEqual(t, len(floors), 1)
		fmt.Printf("✅ Listed %d floors for building\n", len(floors))
	})

	t.Run("Update Floor", func(t *testing.T) {
		reqBody := map[string]any{
			"name": "Updated Ground Floor",
		}
		body, _ := json.Marshal(reqBody)

		req := httptest.NewRequest(http.MethodPut, "/api/v1/floors/"+floorID, bytes.NewReader(body))
		req.Header.Set("Authorization", "Bearer "+token)
		req.Header.Set("Content-Type", "application/json")

		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var floor domain.Floor
		err := json.Unmarshal(w.Body.Bytes(), &floor)
		require.NoError(t, err)
		assert.Equal(t, "Updated Ground Floor", floor.Name)
		fmt.Printf("✅ Updated floor: %s\n", floorID)
	})

	t.Run("Create Room", func(t *testing.T) {
		reqBody := map[string]any{
			"floor_id": floorID,
			"name":     "Conference Room A",
			"number":   "101",
		}
		body, _ := json.Marshal(reqBody)

		req := httptest.NewRequest(http.MethodPost, "/api/v1/rooms", bytes.NewReader(body))
		req.Header.Set("Authorization", "Bearer "+token)
		req.Header.Set("Content-Type", "application/json")

		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusCreated, w.Code)

		var room domain.Room
		err := json.Unmarshal(w.Body.Bytes(), &room)
		require.NoError(t, err)
		roomID = room.ID.String()
		assert.Equal(t, "Conference Room A", room.Name)
		assert.Equal(t, "101", room.Number)
		fmt.Printf("✅ Created room: %s\n", roomID)
	})

	t.Run("Get Room by ID", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/api/v1/rooms/"+roomID, nil)
		req.Header.Set("Authorization", "Bearer "+token)

		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var room domain.Room
		err := json.Unmarshal(w.Body.Bytes(), &room)
		require.NoError(t, err)
		assert.Equal(t, roomID, room.ID.String())
		assert.Equal(t, "Conference Room A", room.Name)
		fmt.Printf("✅ Retrieved room: %s\n", roomID)
	})

	t.Run("List Rooms by Floor", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/api/v1/rooms?floor_id="+floorID, nil)
		req.Header.Set("Authorization", "Bearer "+token)

		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response map[string]any
		err := json.Unmarshal(w.Body.Bytes(), &response)
		require.NoError(t, err)
		assert.NotNil(t, response["rooms"])
		rooms := response["rooms"].([]any)
		assert.GreaterOrEqual(t, len(rooms), 1)
		fmt.Printf("✅ Listed %d rooms for floor\n", len(rooms))
	})

	t.Run("Update Room", func(t *testing.T) {
		reqBody := map[string]any{
			"name": "Updated Conference Room A",
		}
		body, _ := json.Marshal(reqBody)

		req := httptest.NewRequest(http.MethodPut, "/api/v1/rooms/"+roomID, bytes.NewReader(body))
		req.Header.Set("Authorization", "Bearer "+token)
		req.Header.Set("Content-Type", "application/json")

		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var room domain.Room
		err := json.Unmarshal(w.Body.Bytes(), &room)
		require.NoError(t, err)
		assert.Equal(t, "Updated Conference Room A", room.Name)
		fmt.Printf("✅ Updated room: %s\n", roomID)
	})

	t.Run("Get Floor Rooms", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/api/v1/floors/"+floorID+"/rooms", nil)
		req.Header.Set("Authorization", "Bearer "+token)

		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response map[string]any
		err := json.Unmarshal(w.Body.Bytes(), &response)
		require.NoError(t, err)
		assert.NotNil(t, response["rooms"])
		rooms := response["rooms"].([]any)
		assert.GreaterOrEqual(t, len(rooms), 1)
		fmt.Printf("✅ Retrieved %d rooms for floor via /floors/{id}/rooms\n", len(rooms))
	})

	t.Run("Delete Room", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodDelete, "/api/v1/rooms/"+roomID, nil)
		req.Header.Set("Authorization", "Bearer "+token)

		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusNoContent, w.Code)
		fmt.Printf("✅ Deleted room: %s\n", roomID)
	})

	t.Run("Delete Floor", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodDelete, "/api/v1/floors/"+floorID, nil)
		req.Header.Set("Authorization", "Bearer "+token)

		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusNoContent, w.Code)
		fmt.Printf("✅ Deleted floor: %s\n", floorID)
	})
}

// setupTestContainer initializes a test container with database connection
func setupTestContainerLegacy(t *testing.T) (*app.Container, func()) {
	container := app.NewContainer()

	cleanup := func() {
		// Cleanup code if needed
	}

	return container, cleanup
}
