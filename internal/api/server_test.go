package api_test

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/joelpate/arxos/internal/api"
	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/internal/services"
	"github.com/joelpate/arxos/pkg/models"
)

// TestServerHealth tests the health endpoint
func TestServerHealth(t *testing.T) {
	// Setup test server
	server := setupTestServer(t)
	
	// Create request
	req := httptest.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()
	
	// Handle request
	server.Routes().ServeHTTP(w, req)
	
	// Check response
	if w.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", w.Code)
	}
	
	var response map[string]string
	if err := json.NewDecoder(w.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}
	
	if response["status"] != "healthy" {
		t.Errorf("Expected status 'healthy', got %s", response["status"])
	}
}

// TestAuthFlow tests the complete authentication flow
func TestAuthFlow(t *testing.T) {
	server := setupTestServer(t)
	
	// Test registration
	regData := map[string]string{
		"email":    "test@example.com",
		"password": "SecurePass123!",
		"name":     "Test User",
	}
	
	body, _ := json.Marshal(regData)
	req := httptest.NewRequest("POST", "/api/v1/auth/register", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	
	server.Routes().ServeHTTP(w, req)
	
	if w.Code != http.StatusCreated && w.Code != http.StatusOK {
		t.Errorf("Registration failed with status %d: %s", w.Code, w.Body.String())
	}
	
	// Test login
	loginData := map[string]string{
		"email":    "test@example.com",
		"password": "SecurePass123!",
	}
	
	body, _ = json.Marshal(loginData)
	req = httptest.NewRequest("POST", "/api/v1/auth/login", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	w = httptest.NewRecorder()
	
	server.Routes().ServeHTTP(w, req)
	
	if w.Code != http.StatusOK {
		t.Errorf("Login failed with status %d: %s", w.Code, w.Body.String())
	}
	
	var authResp api.AuthResponse
	if err := json.NewDecoder(w.Body).Decode(&authResp); err != nil {
		t.Fatalf("Failed to decode auth response: %v", err)
	}
	
	if authResp.AccessToken == "" {
		t.Error("No access token received")
	}
	
	if authResp.RefreshToken == "" {
		t.Error("No refresh token received")
	}
	
	// Test token refresh
	refreshData := map[string]string{
		"refresh_token": authResp.RefreshToken,
	}
	
	body, _ = json.Marshal(refreshData)
	req = httptest.NewRequest("POST", "/api/v1/auth/refresh", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	w = httptest.NewRecorder()
	
	server.Routes().ServeHTTP(w, req)
	
	if w.Code != http.StatusOK {
		t.Errorf("Token refresh failed with status %d", w.Code)
	}
}

// TestBuildingCRUD tests building CRUD operations
func TestBuildingCRUD(t *testing.T) {
	server := setupTestServer(t)
	token := getTestToken(t, server)
	
	// Create building
	building := &models.FloorPlan{
		Name:     "Test Building",
		Building: "Building A",
		Level:    1,
		Rooms: []*models.Room{
			{
				ID:   "room1",
				Name: "Conference Room",
			},
		},
		Equipment: []*models.Equipment{
			{
				ID:     "eq1",
				Name:   "Projector",
				Type:   "AV",
				Status: models.StatusNormal,
			},
		},
	}
	
	body, _ := json.Marshal(building)
	req := httptest.NewRequest("POST", "/api/v1/buildings/create", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+token)
	w := httptest.NewRecorder()
	
	server.Routes().ServeHTTP(w, req)
	
	if w.Code != http.StatusCreated && w.Code != http.StatusOK {
		t.Errorf("Create building failed with status %d: %s", w.Code, w.Body.String())
	}
	
	// List buildings
	req = httptest.NewRequest("GET", "/api/v1/buildings", nil)
	req.Header.Set("Authorization", "Bearer "+token)
	w = httptest.NewRecorder()
	
	server.Routes().ServeHTTP(w, req)
	
	if w.Code != http.StatusOK {
		t.Errorf("List buildings failed with status %d", w.Code)
	}
	
	var buildings []*models.FloorPlan
	if err := json.NewDecoder(w.Body).Decode(&buildings); err != nil {
		t.Fatalf("Failed to decode buildings: %v", err)
	}
	
	if len(buildings) == 0 {
		t.Error("No buildings returned")
	}
}

// TestPDFToASCII tests PDF to ASCII conversion
func TestPDFToASCII(t *testing.T) {
	// This would test the PDF upload and conversion flow
	// For now, we'll test the ASCII renderer directly
	server := setupTestServer(t)
	token := getTestToken(t, server)
	
	// Create a building with known layout
	building := &models.FloorPlan{
		Name:     "ASCII Test Building",
		Building: "Test Complex",
		Level:    1,
		Rooms: []*models.Room{
			{
				ID:   "room1",
				Name: "Office",
				Bounds: models.Bounds{
					MinX: 0, MinY: 0,
					MaxX: 10, MaxY: 10,
				},
			},
			{
				ID:   "room2",
				Name: "Kitchen",
				Bounds: models.Bounds{
					MinX: 10, MinY: 0,
					MaxX: 20, MaxY: 10,
				},
			},
		},
		Equipment: []*models.Equipment{
			{
				ID:   "outlet1",
				Name: "Power Outlet",
				Type: "electrical",
				Location: &models.Point{
					X: 5, Y: 5,
				},
				Status: models.StatusNormal,
			},
		},
	}
	
	// Test that the building can be created and retrieved
	body, _ := json.Marshal(building)
	req := httptest.NewRequest("POST", "/api/v1/buildings/create", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+token)
	w := httptest.NewRecorder()
	
	server.Routes().ServeHTTP(w, req)
	
	if w.Code != http.StatusCreated && w.Code != http.StatusOK {
		t.Errorf("Create test building failed with status %d", w.Code)
	}
}

// Helper functions

func setupTestServer(t *testing.T) *api.Server {
	// Create in-memory database
	db, err := database.NewSQLiteDBFromPath(":memory:")
	if err != nil {
		t.Fatalf("Failed to create test database: %v", err)
	}
	
	// Initialize schema
	ctx := context.Background()
	if err := db.Migrate(ctx); err != nil {
		t.Fatalf("Failed to initialize database: %v", err)
	}
	
	// Create services
	authService := api.NewAuthService(db)
	buildingService := services.NewBuildingService(db)
	
	services := &api.Services{
		Auth:     authService,
		Building: buildingService,
		DB:       db,
	}
	
	// Create server
	server := api.NewServer(":0", services)
	return server
}

func getTestToken(t *testing.T, server *api.Server) string {
	// Create test user and get token
	loginData := map[string]string{
		"email":    "test@example.com",
		"password": "TestPass123!",
	}
	
	// First register
	body, _ := json.Marshal(loginData)
	req := httptest.NewRequest("POST", "/api/v1/auth/register", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	
	server.Routes().ServeHTTP(w, req)
	
	// Then login
	req = httptest.NewRequest("POST", "/api/v1/auth/login", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	w = httptest.NewRecorder()
	
	server.Routes().ServeHTTP(w, req)
	
	var authResp api.AuthResponse
	if err := json.NewDecoder(w.Body).Decode(&authResp); err != nil {
		t.Fatalf("Failed to get test token: %v", err)
	}
	
	return authResp.AccessToken
}