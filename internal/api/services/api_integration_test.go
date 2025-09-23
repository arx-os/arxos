//go:build integration
// +build integration

package services

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"sync"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/services"
	"github.com/arx-os/arxos/internal/spatial"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/stretchr/testify/suite"
)

type APIIntegrationTestSuite struct {
	suite.Suite
	server    *Server
	router    *gin.Engine
	db        *database.PostGISDB
	services  *services.ServiceRegistry
	ctx       context.Context
	baseURL   string
}

func (s *APIIntegrationTestSuite) SetupSuite() {
	// Setup test configuration
	cfg := &config.Config{
		Server: config.ServerConfig{
			Port:            8080,
			ReadTimeout:     30 * time.Second,
			WriteTimeout:    30 * time.Second,
			ShutdownTimeout: 10 * time.Second,
		},
		Database: config.DatabaseConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "arxos_test",
			User:     "test",
			Password: "test",
			SSLMode:  "disable",
			MaxConns: 10,
		},
	}

	// Initialize database
	s.db = database.NewPostGISDB(database.PostGISConfig{
		Host:     cfg.Database.Host,
		Port:     cfg.Database.Port,
		Database: cfg.Database.Database,
		User:     cfg.Database.User,
		Password: cfg.Database.Password,
		SSLMode:  cfg.Database.SSLMode,
		MaxConns: cfg.Database.MaxConns,
	})

	s.ctx = context.Background()
	err := s.db.Connect(s.ctx)
	s.Require().NoError(err, "Failed to connect to test database")

	err = s.db.InitializeSchema(s.ctx)
	s.Require().NoError(err, "Failed to initialize schema")

	// Initialize services
	s.services = services.NewServiceRegistry(s.db)

	// Setup API server
	s.server = NewServer(cfg, s.services)
	s.router = s.server.setupRouter()
}

func (s *APIIntegrationTestSuite) TearDownSuite() {
	if s.db != nil {
		s.cleanupTestData()
		s.db.Close()
	}
}

func (s *APIIntegrationTestSuite) SetupTest() {
	s.cleanupTestData()
}

func (s *APIIntegrationTestSuite) cleanupTestData() {
	queries := []string{
		"DELETE FROM buildings WHERE name LIKE 'TEST_%'",
		"DELETE FROM floors WHERE name LIKE 'TEST_%'",
		"DELETE FROM equipment WHERE id LIKE 'TEST_%'",
		"DELETE FROM equipment_positions WHERE equipment_id LIKE 'TEST_%'",
		"DELETE FROM floor_boundaries WHERE floor_id LIKE 'TEST_%'",
	}

	for _, q := range queries {
		_, err := s.db.GetDB().ExecContext(s.ctx, q)
		if err != nil {
			s.T().Logf("Warning: cleanup query failed: %v", err)
		}
	}
}

func TestAPIIntegrationSuite(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test suite")
	}
	suite.Run(t, new(APIIntegrationTestSuite))
}

// Helper function to make HTTP requests
func (s *APIIntegrationTestSuite) makeRequest(method, path string, body interface{}) *httptest.ResponseRecorder {
	var reqBody io.Reader
	if body != nil {
		jsonBody, err := json.Marshal(body)
		s.Require().NoError(err)
		reqBody = bytes.NewReader(jsonBody)
	}

	req := httptest.NewRequest(method, path, reqBody)
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}

	w := httptest.NewRecorder()
	s.router.ServeHTTP(w, req)
	return w
}

// TestHealthEndpoint tests the health check endpoint
func (s *APIIntegrationTestSuite) TestHealthEndpoint() {
	resp := s.makeRequest("GET", "/health", nil)

	s.Equal(http.StatusOK, resp.Code)

	var result map[string]interface{}
	err := json.Unmarshal(resp.Body.Bytes(), &result)
	s.Require().NoError(err)

	s.Equal("healthy", result["status"])
	s.Contains(result, "database")
}

// TestBuildingCRUD tests building CRUD operations
func (s *APIIntegrationTestSuite) TestBuildingCRUD() {
	// Create building
	building := models.Building{
		ID:          uuid.New().String(),
		Name:        "TEST_Building_1",
		Address:     "123 Test Street",
		Description: "Test building for integration tests",
		Metadata: map[string]interface{}{
			"type": "commercial",
			"year": 2024,
		},
	}

	// Test Create
	resp := s.makeRequest("POST", "/api/v1/buildings", building)
	s.Equal(http.StatusCreated, resp.Code)

	var createdBuilding models.Building
	err := json.Unmarshal(resp.Body.Bytes(), &createdBuilding)
	s.Require().NoError(err)
	s.Equal(building.Name, createdBuilding.Name)

	// Test Get
	resp = s.makeRequest("GET", fmt.Sprintf("/api/v1/buildings/%s", createdBuilding.ID), nil)
	s.Equal(http.StatusOK, resp.Code)

	var retrievedBuilding models.Building
	err = json.Unmarshal(resp.Body.Bytes(), &retrievedBuilding)
	s.Require().NoError(err)
	s.Equal(building.Name, retrievedBuilding.Name)

	// Test Update
	updatedBuilding := retrievedBuilding
	updatedBuilding.Description = "Updated description"

	resp = s.makeRequest("PUT", fmt.Sprintf("/api/v1/buildings/%s", updatedBuilding.ID), updatedBuilding)
	s.Equal(http.StatusOK, resp.Code)

	// Test List
	resp = s.makeRequest("GET", "/api/v1/buildings", nil)
	s.Equal(http.StatusOK, resp.Code)

	var buildings []models.Building
	err = json.Unmarshal(resp.Body.Bytes(), &buildings)
	s.Require().NoError(err)
	s.Greater(len(buildings), 0)

	// Test Delete
	resp = s.makeRequest("DELETE", fmt.Sprintf("/api/v1/buildings/%s", createdBuilding.ID), nil)
	s.Equal(http.StatusNoContent, resp.Code)

	// Verify deletion
	resp = s.makeRequest("GET", fmt.Sprintf("/api/v1/buildings/%s", createdBuilding.ID), nil)
	s.Equal(http.StatusNotFound, resp.Code)
}

// TestEquipmentPositioning tests equipment positioning endpoints
func (s *APIIntegrationTestSuite) TestEquipmentPositioning() {
	// Create test equipment
	equipment := models.Equipment{
		ID:       fmt.Sprintf("TEST_EQ_%s", uuid.New().String()[:8]),
		Name:     "Test Equipment",
		Type:     "HVAC",
		Status:   "active",
		Metadata: map[string]interface{}{"model": "XYZ-123"},
	}

	resp := s.makeRequest("POST", "/api/v1/equipment", equipment)
	s.Equal(http.StatusCreated, resp.Code)

	// Update position
	position := map[string]interface{}{
		"equipment_id": equipment.ID,
		"position": map[string]float64{
			"x": 1000.5,
			"y": 2000.3,
			"z": 3000.0,
		},
		"confidence": "high",
		"source":     "manual",
	}

	resp = s.makeRequest("PUT", fmt.Sprintf("/api/v1/equipment/%s/position", equipment.ID), position)
	s.Equal(http.StatusOK, resp.Code)

	// Get position
	resp = s.makeRequest("GET", fmt.Sprintf("/api/v1/equipment/%s/position", equipment.ID), nil)
	s.Equal(http.StatusOK, resp.Code)

	var retrievedPos map[string]interface{}
	err := json.Unmarshal(resp.Body.Bytes(), &retrievedPos)
	s.Require().NoError(err)
	s.Contains(retrievedPos, "position")
	s.Contains(retrievedPos, "confidence")

	// Test proximity search
	searchParams := map[string]interface{}{
		"center": map[string]float64{
			"x": 1000.0,
			"y": 2000.0,
			"z": 3000.0,
		},
		"radius": 500.0,
	}

	resp = s.makeRequest("POST", "/api/v1/equipment/search/proximity", searchParams)
	s.Equal(http.StatusOK, resp.Code)

	var results []map[string]interface{}
	err = json.Unmarshal(resp.Body.Bytes(), &results)
	s.Require().NoError(err)
	s.Greater(len(results), 0)
}

// TestConcurrentRequests tests API under concurrent load
func (s *APIIntegrationTestSuite) TestConcurrentRequests() {
	const numWorkers = 20
	const requestsPerWorker = 10

	// Create test data
	baseEquipment := models.Equipment{
		ID:   "TEST_CONCURRENT_BASE",
		Name: "Concurrent Test Equipment",
		Type: "sensor",
	}

	resp := s.makeRequest("POST", "/api/v1/equipment", baseEquipment)
	s.Require().Equal(http.StatusCreated, resp.Code)

	// Launch concurrent workers
	var wg sync.WaitGroup
	errors := make(chan error, numWorkers*requestsPerWorker)

	for w := 0; w < numWorkers; w++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()

			for r := 0; r < requestsPerWorker; r++ {
				// Randomly choose operation
				switch r % 3 {
				case 0: // Read
					resp := s.makeRequest("GET", fmt.Sprintf("/api/v1/equipment/%s", baseEquipment.ID), nil)
					if resp.Code != http.StatusOK {
						errors <- fmt.Errorf("worker %d: GET failed with status %d", workerID, resp.Code)
					}

				case 1: // Update position
					position := map[string]interface{}{
						"equipment_id": baseEquipment.ID,
						"position": map[string]float64{
							"x": float64(workerID * 100),
							"y": float64(r * 100),
							"z": 0,
						},
						"confidence": "medium",
						"source":     fmt.Sprintf("worker_%d", workerID),
					}
					resp := s.makeRequest("PUT", fmt.Sprintf("/api/v1/equipment/%s/position", baseEquipment.ID), position)
					if resp.Code != http.StatusOK {
						errors <- fmt.Errorf("worker %d: PUT position failed with status %d", workerID, resp.Code)
					}

				case 2: // Create new equipment
					equipment := models.Equipment{
						ID:   fmt.Sprintf("TEST_CONCURRENT_%d_%d", workerID, r),
						Name: fmt.Sprintf("Worker %d Equipment %d", workerID, r),
						Type: "sensor",
					}
					resp := s.makeRequest("POST", "/api/v1/equipment", equipment)
					if resp.Code != http.StatusCreated && resp.Code != http.StatusConflict {
						errors <- fmt.Errorf("worker %d: POST failed with status %d", workerID, resp.Code)
					}
				}
			}
		}(w)
	}

	// Wait for all workers to complete
	wg.Wait()
	close(errors)

	// Check for errors
	errorCount := 0
	for err := range errors {
		errorCount++
		s.T().Logf("Concurrent request error: %v", err)
	}

	s.Less(errorCount, numWorkers, "Too many errors during concurrent requests")
}

// TestRateLimiting tests rate limiting on endpoints
func (s *APIIntegrationTestSuite) TestRateLimiting() {
	// Make rapid requests to trigger rate limiting
	const numRequests = 100
	path := "/api/v1/equipment/TEST_RATE_LIMIT"

	rateLimitedCount := 0
	for i := 0; i < numRequests; i++ {
		resp := s.makeRequest("GET", path, nil)
		if resp.Code == http.StatusTooManyRequests {
			rateLimitedCount++
		}
	}

	// Should have some rate limited requests
	s.Greater(rateLimitedCount, 0, "No rate limiting detected")
	s.T().Logf("Rate limited %d out of %d requests", rateLimitedCount, numRequests)
}

// TestAuthenticationFlow tests authentication and authorization
func (s *APIIntegrationTestSuite) TestAuthenticationFlow() {
	// Test unauthenticated access
	resp := s.makeRequest("GET", "/api/v1/secure/data", nil)
	s.Equal(http.StatusUnauthorized, resp.Code)

	// Test login
	loginData := map[string]string{
		"username": "testuser",
		"password": "testpass123",
	}

	resp = s.makeRequest("POST", "/api/v1/auth/login", loginData)
	if resp.Code == http.StatusOK {
		var authResp map[string]interface{}
		err := json.Unmarshal(resp.Body.Bytes(), &authResp)
		s.Require().NoError(err)
		s.Contains(authResp, "token")

		// Test authenticated access
		token := authResp["token"].(string)
		req := httptest.NewRequest("GET", "/api/v1/secure/data", nil)
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", token))

		w := httptest.NewRecorder()
		s.router.ServeHTTP(w, req)
		s.Equal(http.StatusOK, w.Code)
	}
}

// TestDataValidation tests input validation
func (s *APIIntegrationTestSuite) TestDataValidation() {
	testCases := []struct {
		name       string
		path       string
		method     string
		body       interface{}
		wantStatus int
	}{
		{
			name:   "Invalid equipment ID format",
			path:   "/api/v1/equipment",
			method: "POST",
			body: map[string]interface{}{
				"id":   "invalid id with spaces",
				"name": "Test",
				"type": "sensor",
			},
			wantStatus: http.StatusBadRequest,
		},
		{
			name:   "Missing required field",
			path:   "/api/v1/equipment",
			method: "POST",
			body: map[string]interface{}{
				"name": "Missing ID",
				// ID is missing
			},
			wantStatus: http.StatusBadRequest,
		},
		{
			name:   "Invalid position coordinates",
			path:   "/api/v1/equipment/TEST_VALID/position",
			method: "PUT",
			body: map[string]interface{}{
				"position": map[string]interface{}{
					"x": "not a number",
					"y": 100,
					"z": 200,
				},
			},
			wantStatus: http.StatusBadRequest,
		},
	}

	for _, tc := range testCases {
		s.Run(tc.name, func() {
			resp := s.makeRequest(tc.method, tc.path, tc.body)
			s.Equal(tc.wantStatus, resp.Code)
		})
	}
}

// TestBulkOperations tests bulk create/update operations
func (s *APIIntegrationTestSuite) TestBulkOperations() {
	// Prepare bulk equipment data
	const batchSize = 50
	equipment := make([]models.Equipment, batchSize)
	for i := 0; i < batchSize; i++ {
		equipment[i] = models.Equipment{
			ID:   fmt.Sprintf("TEST_BULK_%03d", i),
			Name: fmt.Sprintf("Bulk Equipment %03d", i),
			Type: "sensor",
		}
	}

	// Test bulk create
	resp := s.makeRequest("POST", "/api/v1/equipment/bulk", equipment)
	s.Equal(http.StatusCreated, resp.Code)

	var result map[string]interface{}
	err := json.Unmarshal(resp.Body.Bytes(), &result)
	s.Require().NoError(err)
	s.Equal(float64(batchSize), result["created"])

	// Test bulk update positions
	positions := make([]map[string]interface{}, batchSize)
	for i := 0; i < batchSize; i++ {
		positions[i] = map[string]interface{}{
			"equipment_id": fmt.Sprintf("TEST_BULK_%03d", i),
			"position": map[string]float64{
				"x": float64(i * 100),
				"y": float64(i * 200),
				"z": 0,
			},
			"confidence": "high",
		}
	}

	resp = s.makeRequest("POST", "/api/v1/equipment/positions/bulk", positions)
	s.Equal(http.StatusOK, resp.Code)
}

// TestMetricsEndpoint tests metrics collection
func (s *APIIntegrationTestSuite) TestMetricsEndpoint() {
	// Make some requests to generate metrics
	for i := 0; i < 10; i++ {
		s.makeRequest("GET", "/health", nil)
		s.makeRequest("GET", "/api/v1/equipment", nil)
	}

	// Get metrics
	resp := s.makeRequest("GET", "/metrics", nil)
	s.Equal(http.StatusOK, resp.Code)

	// Check for expected metrics
	body := resp.Body.String()
	s.Contains(body, "http_requests_total")
	s.Contains(body, "http_request_duration_seconds")
	s.Contains(body, "go_memstats")
}
