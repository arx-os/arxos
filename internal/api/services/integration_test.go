package services_test

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/api"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/migration"
	"github.com/arx-os/arxos/internal/middleware"
	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq"
)

// TestServer encapsulates test server setup
type TestServer struct {
	Server      *api.Server
	DB          database.DB
	Router      http.Handler
	AuthService *MockAuthService
	Shutdown    func()
}

// SetupTestServer creates a test server with test PostgreSQL database
func SetupTestServer(t *testing.T) *TestServer {
	// Use test PostgreSQL database (can be configured via env vars)
	// For CI, use: "host=localhost port=5432 user=test dbname=arxos_test sslmode=disable"
	testDSN := "host=localhost port=5432 user=arxos password=arxos dbname=arxos_test sslmode=disable"
	sqlDB, err := sql.Open("postgres", testDSN)
	if err != nil {
		t.Skipf("Skipping integration test: PostgreSQL not available: %v", err)
		return nil
	}

	// Run migrations using the primary migration system
	sqlxDB := sqlx.NewDb(sqlDB, "postgres")
	migrationManager, err := migration.NewManager(sqlxDB)
	if err != nil {
		t.Skipf("Skipping integration test: Failed to create migration manager: %v", err)
		return nil
	}
	
	if err := migrationManager.Up(nil); err != nil {
		// Migrations might not exist in test environment, create basic schema
		createTestSchema(t, sqlDB)
	}

	// Create database wrapper
	db := NewTestDB(sqlDB)

	// Create services
	authService := NewMockAuthService()
	services := &api.Services{
		Auth:         authService,
		Building:     NewMockBuildingService(),
		User:         NewMockUserService(),
		Organization: NewMockOrganizationService(),
		DB:           db,
	}

	// Create server
	server := api.NewServer(":8080", services)

	// Get router
	router := server.Routes()

	return &TestServer{
		Server:      server,
		DB:          db,
		Router:      router,
		AuthService: authService,
		Shutdown: func() {
			sqlDB.Close()
		},
	}
}

// createTestSchema creates a minimal test schema
func createTestSchema(t *testing.T, db *sql.DB) {
	schema := `
	CREATE TABLE IF NOT EXISTS buildings (
		id TEXT PRIMARY KEY,
		arxos_id TEXT UNIQUE NOT NULL,
		name TEXT NOT NULL,
		address TEXT,
		city TEXT,
		state TEXT,
		country TEXT,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);

	CREATE TABLE IF NOT EXISTS users (
		id TEXT PRIMARY KEY,
		email TEXT UNIQUE NOT NULL,
		username TEXT UNIQUE NOT NULL,
		password_hash TEXT NOT NULL,
		role TEXT DEFAULT 'user',
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);

	CREATE TABLE IF NOT EXISTS sessions (
		id TEXT PRIMARY KEY,
		user_id TEXT NOT NULL,
		token_hash TEXT UNIQUE NOT NULL,
		expires_at TIMESTAMP NOT NULL,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (user_id) REFERENCES users(id)
	);
	`

	if _, err := db.Exec(schema); err != nil {
		t.Fatalf("Failed to create test schema: %v", err)
	}
}

// Helper functions

// makeRequest makes an HTTP request to the test server
func makeRequest(t *testing.T, ts *TestServer, method, path string, body interface{}) *httptest.ResponseRecorder {
	var reqBody io.Reader
	if body != nil {
		jsonBody, err := json.Marshal(body)
		if err != nil {
			t.Fatalf("Failed to marshal request body: %v", err)
		}
		reqBody = bytes.NewReader(jsonBody)
	}

	req, err := http.NewRequest(method, path, reqBody)
	if err != nil {
		t.Fatalf("Failed to create request: %v", err)
	}

	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}

	rr := httptest.NewRecorder()
	ts.Router.ServeHTTP(rr, req)

	return rr
}

// makeAuthenticatedRequest makes an authenticated request
func makeAuthenticatedRequest(t *testing.T, ts *TestServer, method, path, token string, body interface{}) *httptest.ResponseRecorder {
	var reqBody io.Reader
	if body != nil {
		jsonBody, err := json.Marshal(body)
		if err != nil {
			t.Fatalf("Failed to marshal request body: %v", err)
		}
		reqBody = bytes.NewReader(jsonBody)
	}

	req, err := http.NewRequest(method, path, reqBody)
	if err != nil {
		t.Fatalf("Failed to create request: %v", err)
	}

	req.Header.Set("Authorization", "Bearer "+token)
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}

	rr := httptest.NewRecorder()
	ts.Router.ServeHTTP(rr, req)

	return rr
}

// Test Cases

func TestHealthEndpoints(t *testing.T) {
	ts := SetupTestServer(t)
	defer ts.Shutdown()

	tests := []struct {
		name     string
		endpoint string
		wantCode int
	}{
		{"Health Check", "/health", http.StatusOK},
		{"Readiness Check", "/ready", http.StatusOK},
		{"Liveness Check", "/live", http.StatusOK},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			rr := makeRequest(t, ts, "GET", tt.endpoint, nil)

			if rr.Code != tt.wantCode {
				t.Errorf("Expected status %d, got %d", tt.wantCode, rr.Code)
			}

			// Verify response is JSON
			var response map[string]interface{}
			if err := json.Unmarshal(rr.Body.Bytes(), &response); err != nil {
				t.Errorf("Response is not valid JSON: %v", err)
			}

			// Check for required fields
			if _, ok := response["status"]; !ok {
				t.Error("Response missing 'status' field")
			}
			if _, ok := response["timestamp"]; !ok {
				t.Error("Response missing 'timestamp' field")
			}
		})
	}
}

func TestBuildingsCRUD(t *testing.T) {
	ts := SetupTestServer(t)
	defer ts.Shutdown()

	// Test Create Building
	t.Run("Create Building", func(t *testing.T) {
		building := middleware.CreateBuildingRequest{
			ArxosID:   "ARXOS-NA-US-NY-NYC-0001",
			Name:      "Test Building",
			Address:   "123 Test St",
			City:      "New York",
			State:     "NY",
			Country:   "USA",
			Latitude:  40.7128,
			Longitude: -74.0060,
		}

		rr := makeRequest(t, ts, "POST", "/api/v1/buildings", building)

		if rr.Code != http.StatusCreated {
			t.Errorf("Expected status 201, got %d: %s", rr.Code, rr.Body.String())
		}

		var response map[string]interface{}
		if err := json.Unmarshal(rr.Body.Bytes(), &response); err != nil {
			t.Fatalf("Failed to parse response: %v", err)
		}

		if response["arxos_id"] != building.ArxosID {
			t.Errorf("Expected arxos_id %s, got %v", building.ArxosID, response["arxos_id"])
		}
	})

	// Test Get Building
	t.Run("Get Building", func(t *testing.T) {
		rr := makeRequest(t, ts, "GET", "/api/v1/buildings/ARXOS-NA-US-NY-NYC-0001", nil)

		if rr.Code != http.StatusOK {
			t.Errorf("Expected status 200, got %d", rr.Code)
		}

		var building map[string]interface{}
		if err := json.Unmarshal(rr.Body.Bytes(), &building); err != nil {
			t.Fatalf("Failed to parse response: %v", err)
		}

		if building["name"] != "Test Building" {
			t.Errorf("Expected name 'Test Building', got %v", building["name"])
		}
	})

	// Test List Buildings
	t.Run("List Buildings", func(t *testing.T) {
		rr := makeRequest(t, ts, "GET", "/api/v1/buildings", nil)

		if rr.Code != http.StatusOK {
			t.Errorf("Expected status 200, got %d", rr.Code)
		}

		var buildings []map[string]interface{}
		if err := json.Unmarshal(rr.Body.Bytes(), &buildings); err != nil {
			t.Fatalf("Failed to parse response: %v", err)
		}

		if len(buildings) != 1 {
			t.Errorf("Expected 1 building, got %d", len(buildings))
		}
	})

	// Test Update Building
	t.Run("Update Building", func(t *testing.T) {
		update := map[string]interface{}{
			"name": "Updated Building",
		}

		rr := makeRequest(t, ts, "PUT", "/api/v1/buildings/ARXOS-NA-US-NY-NYC-0001", update)

		if rr.Code != http.StatusOK {
			t.Errorf("Expected status 200, got %d", rr.Code)
		}

		// Verify update
		rr = makeRequest(t, ts, "GET", "/api/v1/buildings/ARXOS-NA-US-NY-NYC-0001", nil)
		var building map[string]interface{}
		json.Unmarshal(rr.Body.Bytes(), &building)

		if building["name"] != "Updated Building" {
			t.Errorf("Expected name 'Updated Building', got %v", building["name"])
		}
	})

	// Test Delete Building
	t.Run("Delete Building", func(t *testing.T) {
		rr := makeRequest(t, ts, "DELETE", "/api/v1/buildings/ARXOS-NA-US-NY-NYC-0001", nil)

		if rr.Code != http.StatusNoContent {
			t.Errorf("Expected status 204, got %d", rr.Code)
		}

		// Verify deletion
		rr = makeRequest(t, ts, "GET", "/api/v1/buildings/ARXOS-NA-US-NY-NYC-0001", nil)
		if rr.Code != http.StatusNotFound {
			t.Errorf("Expected status 404 after deletion, got %d", rr.Code)
		}
	})
}

func TestAuthentication(t *testing.T) {
	ts := SetupTestServer(t)
	defer ts.Shutdown()

	// Enable authentication for this test
	ts.AuthService.EnableAuth = true

	// Test User Registration
	t.Run("User Registration", func(t *testing.T) {
		user := middleware.CreateUserRequest{
			Email:    "test@example.com",
			Username: "testuser",
			Password: "TestPass123!",
			FullName: "Test User",
			Role:     "user",
		}

		rr := makeRequest(t, ts, "POST", "/api/v1/auth/register", user)

		if rr.Code != http.StatusCreated {
			t.Errorf("Expected status 201, got %d: %s", rr.Code, rr.Body.String())
		}

		var response map[string]interface{}
		if err := json.Unmarshal(rr.Body.Bytes(), &response); err != nil {
			t.Fatalf("Failed to parse response: %v", err)
		}

		if _, ok := response["token"]; !ok {
			t.Error("Response missing 'token' field")
		}
	})

	// Test User Login
	t.Run("User Login", func(t *testing.T) {
		login := middleware.LoginRequest{
			Username: "testuser",
			Password: "TestPass123!",
		}

		rr := makeRequest(t, ts, "POST", "/api/v1/auth/login", login)

		if rr.Code != http.StatusOK {
			t.Errorf("Expected status 200, got %d: %s", rr.Code, rr.Body.String())
		}

		var response map[string]interface{}
		if err := json.Unmarshal(rr.Body.Bytes(), &response); err != nil {
			t.Fatalf("Failed to parse response: %v", err)
		}

		if _, ok := response["token"]; !ok {
			t.Error("Response missing 'token' field")
		}
	})

	// Test Invalid Login
	t.Run("Invalid Login", func(t *testing.T) {
		login := middleware.LoginRequest{
			Username: "testuser",
			Password: "wrongpassword",
		}

		rr := makeRequest(t, ts, "POST", "/api/v1/auth/login", login)

		if rr.Code != http.StatusUnauthorized {
			t.Errorf("Expected status 401, got %d", rr.Code)
		}
	})

	// Test Protected Endpoint
	t.Run("Protected Endpoint", func(t *testing.T) {
		// Try without token
		rr := makeRequest(t, ts, "GET", "/api/v1/users/profile", nil)
		if rr.Code != http.StatusUnauthorized {
			t.Errorf("Expected status 401 without token, got %d", rr.Code)
		}

		// Login to get token
		login := middleware.LoginRequest{
			Username: "testuser",
			Password: "TestPass123!",
		}
		rr = makeRequest(t, ts, "POST", "/api/v1/auth/login", login)

		var loginResp map[string]interface{}
		json.Unmarshal(rr.Body.Bytes(), &loginResp)
		token := loginResp["token"].(string)

		// Try with token
		rr = makeAuthenticatedRequest(t, ts, "GET", "/api/v1/users/profile", token, nil)
		if rr.Code != http.StatusOK {
			t.Errorf("Expected status 200 with token, got %d", rr.Code)
		}
	})
}

func TestRateLimiting(t *testing.T) {
	ts := SetupTestServer(t)
	defer ts.Shutdown()

	// Note: Rate limiting would need to be configured via middleware
	// For now, skip this test as it requires middleware changes

	// Make requests up to the limit
	for i := 0; i < 5; i++ {
		rr := makeRequest(t, ts, "GET", "/health", nil)
		if rr.Code != http.StatusOK {
			t.Errorf("Request %d: Expected status 200, got %d", i+1, rr.Code)
		}
	}

	// Next request should be rate limited
	rr := makeRequest(t, ts, "GET", "/health", nil)
	if rr.Code != http.StatusTooManyRequests {
		t.Errorf("Expected status 429 (rate limited), got %d", rr.Code)
	}

	// Wait for rate limit window to reset
	time.Sleep(1 * time.Second)

	// Should work again
	rr = makeRequest(t, ts, "GET", "/health", nil)
	if rr.Code != http.StatusOK {
		t.Errorf("Expected status 200 after rate limit reset, got %d", rr.Code)
	}
}

func TestInputValidation(t *testing.T) {
	ts := SetupTestServer(t)
	defer ts.Shutdown()

	tests := []struct {
		name     string
		payload  interface{}
		wantCode int
	}{
		{
			name: "Invalid ArxOS ID",
			payload: middleware.CreateBuildingRequest{
				ArxosID: "invalid-id",
				Name:    "Test",
			},
			wantCode: http.StatusBadRequest,
		},
		{
			name: "Missing Required Fields",
			payload: middleware.CreateBuildingRequest{
				ArxosID: "ARXOS-NA-US-NY-NYC-0001",
				// Missing Name
			},
			wantCode: http.StatusBadRequest,
		},
		{
			name: "Invalid Coordinates",
			payload: middleware.CreateBuildingRequest{
				ArxosID:   "ARXOS-NA-US-NY-NYC-0001",
				Name:      "Test",
				Latitude:  200, // Invalid
				Longitude: -74.0060,
			},
			wantCode: http.StatusBadRequest,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			rr := makeRequest(t, ts, "POST", "/api/v1/buildings", tt.payload)

			if rr.Code != tt.wantCode {
				t.Errorf("Expected status %d, got %d: %s", tt.wantCode, rr.Code, rr.Body.String())
			}

			if tt.wantCode == http.StatusBadRequest {
				var response middleware.ValidationResponse
				if err := json.Unmarshal(rr.Body.Bytes(), &response); err != nil {
					t.Errorf("Expected validation error response: %v", err)
				}

				if len(response.Details) == 0 {
					t.Error("Expected validation error details")
				}
			}
		})
	}
}

func TestPagination(t *testing.T) {
	ts := SetupTestServer(t)
	defer ts.Shutdown()

	// Create multiple buildings
	for i := 1; i <= 15; i++ {
		building := middleware.CreateBuildingRequest{
			ArxosID:   fmt.Sprintf("ARXOS-NA-US-NY-NYC-%04d", i),
			Name:      fmt.Sprintf("Building %d", i),
			Address:   fmt.Sprintf("%d Test St", i),
			City:      "New York",
			State:     "NY",
			Country:   "USA",
			Latitude:  40.7128,
			Longitude: -74.0060,
		}
		makeRequest(t, ts, "POST", "/api/v1/buildings", building)
	}

	// Test pagination
	tests := []struct {
		name      string
		query     string
		wantCount int
	}{
		{"First Page", "?page=1&limit=10", 10},
		{"Second Page", "?page=2&limit=10", 5},
		{"Small Limit", "?page=1&limit=5", 5},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			rr := makeRequest(t, ts, "GET", "/api/v1/buildings"+tt.query, nil)

			if rr.Code != http.StatusOK {
				t.Errorf("Expected status 200, got %d", rr.Code)
			}

			var response struct {
				Data []map[string]interface{} `json:"data"`
				Meta struct {
					Page  int `json:"page"`
					Limit int `json:"limit"`
					Total int `json:"total"`
				} `json:"meta"`
			}

			if err := json.Unmarshal(rr.Body.Bytes(), &response); err != nil {
				t.Fatalf("Failed to parse response: %v", err)
			}

			if len(response.Data) != tt.wantCount {
				t.Errorf("Expected %d items, got %d", tt.wantCount, len(response.Data))
			}

			if response.Meta.Total != 15 {
				t.Errorf("Expected total 15, got %d", response.Meta.Total)
			}
		})
	}
}

func TestConcurrentRequests(t *testing.T) {
	ts := SetupTestServer(t)
	defer ts.Shutdown()

	// Test concurrent reads
	t.Run("Concurrent Reads", func(t *testing.T) {
		// Create a building first
		building := middleware.CreateBuildingRequest{
			ArxosID:   "ARXOS-NA-US-NY-NYC-0001",
			Name:      "Test Building",
			Address:   "123 Test St",
			City:      "New York",
			State:     "NY",
			Country:   "USA",
			Latitude:  40.7128,
			Longitude: -74.0060,
		}
		makeRequest(t, ts, "POST", "/api/v1/buildings", building)

		// Make concurrent read requests
		done := make(chan bool, 10)
		for i := 0; i < 10; i++ {
			go func() {
				rr := makeRequest(t, ts, "GET", "/api/v1/buildings/ARXOS-NA-US-NY-NYC-0001", nil)
				if rr.Code != http.StatusOK {
					t.Errorf("Concurrent request failed with status %d", rr.Code)
				}
				done <- true
			}()
		}

		// Wait for all requests to complete
		for i := 0; i < 10; i++ {
			<-done
		}
	})

	// Test concurrent writes with different IDs
	t.Run("Concurrent Writes", func(t *testing.T) {
		done := make(chan bool, 10)
		for i := 0; i < 10; i++ {
			go func(id int) {
				building := middleware.CreateBuildingRequest{
					ArxosID:   fmt.Sprintf("ARXOS-NA-US-NY-NYC-%04d", id+100),
					Name:      fmt.Sprintf("Concurrent Building %d", id),
					Address:   fmt.Sprintf("%d Concurrent St", id),
					City:      "New York",
					State:     "NY",
					Country:   "USA",
					Latitude:  40.7128,
					Longitude: -74.0060,
				}
				rr := makeRequest(t, ts, "POST", "/api/v1/buildings", building)
				if rr.Code != http.StatusCreated {
					t.Errorf("Concurrent write failed with status %d", rr.Code)
				}
				done <- true
			}(i)
		}

		// Wait for all requests to complete
		for i := 0; i < 10; i++ {
			<-done
		}

		// Verify all buildings were created
		rr := makeRequest(t, ts, "GET", "/api/v1/buildings", nil)
		var buildings []map[string]interface{}
		json.Unmarshal(rr.Body.Bytes(), &buildings)

		if len(buildings) < 11 { // 1 from previous test + 10 concurrent
			t.Errorf("Expected at least 11 buildings, got %d", len(buildings))
		}
	})
}

// Benchmark tests

func BenchmarkHealthEndpoint(b *testing.B) {
	ts := SetupTestServer(&testing.T{})
	defer ts.Shutdown()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		req, _ := http.NewRequest("GET", "/health", nil)
		rr := httptest.NewRecorder()
		ts.Router.ServeHTTP(rr, req)
	}
}

func BenchmarkBuildingCreation(b *testing.B) {
	ts := SetupTestServer(&testing.T{})
	defer ts.Shutdown()

	building := middleware.CreateBuildingRequest{
		ArxosID:   "ARXOS-NA-US-NY-NYC-0001",
		Name:      "Benchmark Building",
		Address:   "123 Benchmark St",
		City:      "New York",
		State:     "NY",
		Country:   "USA",
		Latitude:  40.7128,
		Longitude: -74.0060,
	}

	body, _ := json.Marshal(building)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		// Update ArxOS ID for uniqueness
		building.ArxosID = fmt.Sprintf("ARXOS-NA-US-NY-NYC-%04d", i)
		body, _ = json.Marshal(building)

		req, _ := http.NewRequest("POST", "/api/v1/buildings", bytes.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
		rr := httptest.NewRecorder()
		ts.Router.ServeHTTP(rr, req)
	}
}
