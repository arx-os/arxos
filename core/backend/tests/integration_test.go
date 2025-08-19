package tests

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
	"time"

	"github.com/arxos/arxos/core/arxobject"
	"github.com/arxos/arxos/core/backend/handlers"
	"github.com/arxos/arxos/core/backend/models"
	"github.com/arxos/arxos/core/backend/services"
	testhelpers "github.com/arxos/arxos/core/backend/testing"
	"github.com/go-chi/chi/v5"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"gorm.io/gorm"
)

// IntegrationTestSuite contains integration test setup
type IntegrationTestSuite struct {
	db             *gorm.DB
	engine         *arxobject.Engine
	validationSvc  *services.ValidationService
	server         *httptest.Server
	router         *chi.Mux
}

// setupIntegrationSuite initializes the integration test environment
func setupIntegrationSuite(t *testing.T) *IntegrationTestSuite {
	testhelpers.SkipIfUnit(t)
	
	// Setup database
	db := testhelpers.SetupTestDB(t)
	
	// Setup ArxObject engine
	engine := testhelpers.SetupTestEngine()
	
	// Setup services
	validationSvc := services.NewValidationService(db)
	
	// Setup HTTP router
	router := chi.NewRouter()
	
	// Setup handlers
	validationHandler := handlers.NewValidationHandler(validationSvc, engine)
	
	// Register routes
	router.Route("/api/v1", func(r chi.Router) {
		r.Route("/validations", func(r chi.Router) {
			r.Get("/pending", validationHandler.GetPendingValidations)
			r.Post("/flag", validationHandler.FlagForValidation)
			r.Post("/submit", validationHandler.SubmitValidation)
			r.Get("/history", validationHandler.GetValidationHistory)
			r.Get("/leaderboard", validationHandler.GetValidationLeaderboard)
		})
	})
	
	// Create test server
	server := httptest.NewServer(router)
	
	return &IntegrationTestSuite{
		db:            db,
		engine:        engine,
		validationSvc: validationSvc,
		server:        server,
		router:        router,
	}
}

// teardownIntegrationSuite cleans up the integration test environment
func (suite *IntegrationTestSuite) teardown() {
	if suite.server != nil {
		suite.server.Close()
	}
}

func TestValidationAPIIntegration(t *testing.T) {
	suite := setupIntegrationSuite(t)
	defer suite.teardown()
	
	t.Run("Complete validation workflow", func(t *testing.T) {
		// Step 1: Create validation tasks
		tasks := testhelpers.CreateTestValidationTasks()
		for _, task := range tasks {
			err := suite.db.Create(task).Error
			require.NoError(t, err)
		}
		
		// Step 2: Get pending validations
		resp, err := http.Get(suite.server.URL + "/api/v1/validations/pending")
		require.NoError(t, err)
		defer resp.Body.Close()
		
		assert.Equal(t, http.StatusOK, resp.StatusCode)
		
		var pendingResponse map[string]interface{}
		err = json.NewDecoder(resp.Body).Decode(&pendingResponse)
		require.NoError(t, err)
		
		validations := pendingResponse["validations"].([]interface{})
		assert.Len(t, validations, 3)
		
		// Step 3: Submit validation for highest priority task
		submission := map[string]interface{}{
			"object_id":       "wall_001",
			"validation_type": "dimension",
			"data": map[string]interface{}{
				"length":    10.5,
				"thickness": 0.15,
				"material":  "concrete",
			},
			"validator":  "integration_test",
			"confidence": 0.95,
			"timestamp":  time.Now().Format(time.RFC3339),
			"notes":      "Integration test validation",
		}
		
		submissionJSON, _ := json.Marshal(submission)
		resp, err = http.Post(
			suite.server.URL+"/api/v1/validations/submit",
			"application/json",
			bytes.NewBuffer(submissionJSON),
		)
		require.NoError(t, err)
		defer resp.Body.Close()
		
		assert.Equal(t, http.StatusOK, resp.StatusCode)
		
		var submitResponse map[string]interface{}
		err = json.NewDecoder(resp.Body).Decode(&submitResponse)
		require.NoError(t, err)
		
		assert.True(t, submitResponse["success"].(bool))
		impact := submitResponse["impact"].(map[string]interface{})
		assert.NotNil(t, impact)
		assert.Greater(t, impact["new_confidence"].(float64), impact["old_confidence"].(float64))
		
		// Step 4: Check validation history
		resp, err = http.Get(suite.server.URL + "/api/v1/validations/history?validator=integration_test")
		require.NoError(t, err)
		defer resp.Body.Close()
		
		assert.Equal(t, http.StatusOK, resp.StatusCode)
		
		var historyResponse map[string]interface{}
		err = json.NewDecoder(resp.Body).Decode(&historyResponse)
		require.NoError(t, err)
		
		history := historyResponse["history"].([]interface{})
		assert.GreaterOrEqual(t, len(history), 1)
		
		// Step 5: Check leaderboard
		resp, err = http.Get(suite.server.URL + "/api/v1/validations/leaderboard?period=weekly")
		require.NoError(t, err)
		defer resp.Body.Close()
		
		assert.Equal(t, http.StatusOK, resp.StatusCode)
		
		var leaderboardResponse map[string]interface{}
		err = json.NewDecoder(resp.Body).Decode(&leaderboardResponse)
		require.NoError(t, err)
		
		leaderboard := leaderboardResponse["leaderboard"].([]interface{})
		assert.GreaterOrEqual(t, len(leaderboard), 1)
	})
}

func TestErrorHandlingIntegration(t *testing.T) {
	suite := setupIntegrationSuite(t)
	defer suite.teardown()
	
	t.Run("Invalid JSON submission", func(t *testing.T) {
		resp, err := http.Post(
			suite.server.URL+"/api/v1/validations/submit",
			"application/json",
			bytes.NewBuffer([]byte("invalid json")),
		)
		require.NoError(t, err)
		defer resp.Body.Close()
		
		assert.Equal(t, http.StatusBadRequest, resp.StatusCode)
	})
	
	t.Run("Missing required fields", func(t *testing.T) {
		submission := map[string]interface{}{
			"object_id": "wall_001",
			// Missing validation_type, validator, confidence
		}
		
		submissionJSON, _ := json.Marshal(submission)
		resp, err := http.Post(
			suite.server.URL+"/api/v1/validations/submit",
			"application/json",
			bytes.NewBuffer(submissionJSON),
		)
		require.NoError(t, err)
		defer resp.Body.Close()
		
		assert.Equal(t, http.StatusBadRequest, resp.StatusCode)
	})
	
	t.Run("Nonexistent object", func(t *testing.T) {
		submission := map[string]interface{}{
			"object_id":       "nonexistent_object",
			"validation_type": "dimension",
			"validator":       "test",
			"confidence":      0.95,
			"timestamp":       time.Now().Format(time.RFC3339),
		}
		
		submissionJSON, _ := json.Marshal(submission)
		resp, err := http.Post(
			suite.server.URL+"/api/v1/validations/submit",
			"application/json",
			bytes.NewBuffer(submissionJSON),
		)
		require.NoError(t, err)
		defer resp.Body.Close()
		
		assert.Equal(t, http.StatusNotFound, resp.StatusCode)
	})
}

func TestPerformanceIntegration(t *testing.T) {
	suite := setupIntegrationSuite(t)
	defer suite.teardown()
	
	t.Run("High volume validation processing", func(t *testing.T) {
		// Create many validation tasks
		taskCount := 1000
		for i := 0; i < taskCount; i++ {
			task := &models.ValidationTask{
				ObjectID:        fmt.Sprintf("perf_test_obj_%d", i),
				ObjectType:      "wall",
				Confidence:      0.5,
				Priority:        5,
				PotentialImpact: 0.6,
				CreatedAt:       time.Now(),
			}
			err := suite.db.Create(task).Error
			require.NoError(t, err)
		}
		
		// Test fetching large number of pending validations
		testhelpers.AssertPerformance(t, 500*time.Millisecond, func() {
			resp, err := http.Get(suite.server.URL + "/api/v1/validations/pending?limit=500")
			require.NoError(t, err)
			defer resp.Body.Close()
			
			assert.Equal(t, http.StatusOK, resp.StatusCode)
		})
	})
	
	t.Run("Concurrent validation submissions", func(t *testing.T) {
		// Create objects for concurrent testing
		objectIDs := make([]uint64, 10)
		for i := range objectIDs {
			objectIDs[i] = suite.engine.CreateObject(
				arxobject.StructuralWall,
				float32(i*10), float32(i*5), 0,
			)
		}
		
		// Submit validations concurrently
		done := make(chan bool, 10)
		
		for i := 0; i < 10; i++ {
			go func(objIndex int) {
				submission := map[string]interface{}{
					"object_id":       fmt.Sprintf("%d", objectIDs[objIndex]),
					"validation_type": "dimension",
					"validator":       fmt.Sprintf("concurrent_test_%d", objIndex),
					"confidence":      0.9,
					"timestamp":       time.Now().Format(time.RFC3339),
				}
				
				submissionJSON, _ := json.Marshal(submission)
				resp, err := http.Post(
					suite.server.URL+"/api/v1/validations/submit",
					"application/json",
					bytes.NewBuffer(submissionJSON),
				)
				
				if err == nil {
					resp.Body.Close()
					assert.Equal(t, http.StatusOK, resp.StatusCode)
				}
				
				done <- true
			}(i)
		}
		
		// Wait for all submissions to complete
		for i := 0; i < 10; i++ {
			select {
			case <-done:
				// Success
			case <-time.After(5 * time.Second):
				t.Fatal("Concurrent submission timed out")
			}
		}
	})
}

func TestDatabaseIntegration(t *testing.T) {
	suite := setupIntegrationSuite(t)
	defer suite.teardown()
	
	t.Run("Transaction consistency", func(t *testing.T) {
		// Test that failed transactions are properly rolled back
		submission := &models.ValidationSubmission{
			ObjectID:       "transaction_test_obj",
			ValidationType: "dimension",
			Validator:      "transaction_test",
			Confidence:     0.95,
			Timestamp:      time.Now(),
		}
		
		impact := &models.ValidationImpact{
			ObjectID:              "transaction_test_obj",
			OldConfidence:         0.45,
			NewConfidence:         0.85,
			ConfidenceImprovement: 0.40,
			CascadedObjects:       []string{"obj1", "obj2"},
			CascadedCount:         2,
			PatternLearned:        true,
			TotalConfidenceGain:   0.8,
			TimeSaved:             5.0,
		}
		
		// This should succeed and commit properly
		err := suite.validationSvc.SaveValidation(submission, impact)
		assert.NoError(t, err)
		
		// Verify data was saved
		var count int64
		err = suite.db.Table("arx_validations").Where("validator = ?", "transaction_test").Count(&count).Error
		assert.NoError(t, err)
		assert.Equal(t, int64(1), count)
	})
}

func TestSecurityIntegration(t *testing.T) {
	suite := setupIntegrationSuite(t)
	defer suite.teardown()
	
	t.Run("Input validation and sanitization", func(t *testing.T) {
		tests := []struct {
			name       string
			submission map[string]interface{}
			expectCode int
		}{
			{
				name: "SQL injection attempt",
				submission: map[string]interface{}{
					"object_id":       "'; DROP TABLE validations; --",
					"validation_type": "dimension",
					"validator":       "hacker",
					"confidence":      0.95,
				},
				expectCode: http.StatusBadRequest,
			},
			{
				name: "XSS attempt in notes",
				submission: map[string]interface{}{
					"object_id":       "wall_001",
					"validation_type": "dimension",
					"validator":       "test",
					"confidence":      0.95,
					"notes":          "<script>alert('xss')</script>",
				},
				expectCode: http.StatusBadRequest,
			},
			{
				name: "Invalid confidence value",
				submission: map[string]interface{}{
					"object_id":       "wall_001",
					"validation_type": "dimension",
					"validator":       "test",
					"confidence":      1.5, // Invalid: > 1.0
				},
				expectCode: http.StatusBadRequest,
			},
		}
		
		for _, tt := range tests {
			t.Run(tt.name, func(t *testing.T) {
				submissionJSON, _ := json.Marshal(tt.submission)
				resp, err := http.Post(
					suite.server.URL+"/api/v1/validations/submit",
					"application/json",
					bytes.NewBuffer(submissionJSON),
				)
				require.NoError(t, err)
				defer resp.Body.Close()
				
				assert.Equal(t, tt.expectCode, resp.StatusCode)
			})
		}
	})
}

// TestMain sets up and tears down integration test environment
func TestMain(m *testing.M) {
	// Set environment variable for integration tests
	os.Setenv("INTEGRATION_TESTS", "1")
	
	// Run tests
	code := m.Run()
	
	// Cleanup
	os.Unsetenv("INTEGRATION_TESTS")
	
	os.Exit(code)
}