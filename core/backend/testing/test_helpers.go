// Package testing provides common test utilities and helpers
package testing

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/arxos/arxos/core/arxobject"
	"github.com/arxos/arxos/core/backend/models"
	"github.com/stretchr/testify/assert"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

// TestDatabase creates an in-memory SQLite database for testing
func SetupTestDB(t *testing.T) *gorm.DB {
	db, err := gorm.Open(sqlite.Open(":memory:"), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Silent),
	})
	assert.NoError(t, err)

	// Auto-migrate test tables
	err = db.AutoMigrate(
		&models.ValidationTask{},
		&models.ValidationSubmission{},
		&models.ValidationImpact{},
		&models.ValidationRecord{},
		&models.ValidatorStats{},
	)
	assert.NoError(t, err)

	return db
}

// TestEngine creates a test ArxObject engine with sample data
func SetupTestEngine() *arxobject.Engine {
	engine := arxobject.NewEngine(1000)
	
	// Create sample objects for testing
	engine.CreateObjectWithConfidence(
		arxobject.StructuralWall, 10, 20, 0,
		arxobject.NewConfidenceScore(0.45, 0.5, 0.4, 0.48),
	)
	
	engine.CreateObjectWithConfidence(
		arxobject.StructuralColumn, 15, 25, 0,
		arxobject.NewConfidenceScore(0.65, 0.7, 0.6, 0.68),
	)
	
	engine.CreateObjectWithConfidence(
		arxobject.ElectricalOutlet, 5, 10, 0,
		arxobject.NewConfidenceScore(0.35, 0.4, 0.3, 0.38),
	)
	
	return engine
}

// HTTPTestRequest creates a test HTTP request with JSON body
func HTTPTestRequest(method, url string, body interface{}) (*http.Request, error) {
	var bodyReader *bytes.Buffer
	
	if body != nil {
		jsonBody, err := json.Marshal(body)
		if err != nil {
			return nil, err
		}
		bodyReader = bytes.NewBuffer(jsonBody)
	} else {
		bodyReader = bytes.NewBuffer([]byte{})
	}
	
	req, err := http.NewRequest(method, url, bodyReader)
	if err != nil {
		return nil, err
	}
	
	req.Header.Set("Content-Type", "application/json")
	return req, nil
}

// AssertJSONResponse validates HTTP response as JSON
func AssertJSONResponse(t *testing.T, rr *httptest.ResponseRecorder, expectedCode int) map[string]interface{} {
	assert.Equal(t, expectedCode, rr.Code)
	assert.Equal(t, "application/json", rr.Header().Get("Content-Type"))
	
	var response map[string]interface{}
	err := json.Unmarshal(rr.Body.Bytes(), &response)
	assert.NoError(t, err)
	
	return response
}

// AssertErrorResponse validates error response format
func AssertErrorResponse(t *testing.T, rr *httptest.ResponseRecorder, expectedCode int, expectedMessage string) {
	response := AssertJSONResponse(t, rr, expectedCode)
	assert.Contains(t, response["error"].(string), expectedMessage)
}

// AssertSuccessResponse validates success response format
func AssertSuccessResponse(t *testing.T, rr *httptest.ResponseRecorder) map[string]interface{} {
	response := AssertJSONResponse(t, rr, http.StatusOK)
	assert.True(t, response["success"].(bool))
	return response
}

// CreateTestValidationTasks creates sample validation tasks
func CreateTestValidationTasks() []*models.ValidationTask {
	return []*models.ValidationTask{
		{
			ID:              1,
			ObjectID:        "wall_001",
			ObjectType:      "wall",
			Confidence:      0.45,
			Priority:        8,
			PotentialImpact: 0.75,
			SimilarCount:    5,
			CreatedAt:       time.Now(),
		},
		{
			ID:              2,
			ObjectID:        "door_001", 
			ObjectType:      "door",
			Confidence:      0.55,
			Priority:        6,
			PotentialImpact: 0.6,
			SimilarCount:    3,
			CreatedAt:       time.Now(),
		},
		{
			ID:              3,
			ObjectID:        "outlet_001",
			ObjectType:      "electrical_outlet",
			Confidence:      0.35,
			Priority:        9,
			PotentialImpact: 0.8,
			SimilarCount:    8,
			CreatedAt:       time.Now(),
		},
	}
}

// CreateTestValidationSubmission creates a sample validation submission
func CreateTestValidationSubmission(objectID string) models.ValidationSubmission {
	return models.ValidationSubmission{
		ObjectID:       objectID,
		ValidationType: "dimension",
		Data: map[string]interface{}{
			"length":    10.5,
			"width":     0.15,
			"height":    3.0,
			"material":  "concrete",
		},
		Validator:  "test_validator",
		Confidence: 0.95,
		Timestamp:  time.Now(),
		PhotoURL:   "https://example.com/photo.jpg",
		Notes:      "Measured with laser scanner",
	}
}

// CreateTestValidationImpact creates a sample validation impact
func CreateTestValidationImpact(objectID string) models.ValidationImpact {
	return models.ValidationImpact{
		ObjectID:              objectID,
		OldConfidence:         0.45,
		NewConfidence:         0.85,
		ConfidenceImprovement: 0.40,
		CascadedObjects:       []string{"wall_002", "wall_003", "wall_004"},
		CascadedCount:         3,
		PatternLearned:        true,
		TotalConfidenceGain:   1.2,
		TimeSaved:             7.5,
	}
}

// BenchmarkHelper provides utilities for benchmark tests
type BenchmarkHelper struct {
	Engine    *arxobject.Engine
	DB        *gorm.DB
	ObjectIDs []uint64
}

// SetupBenchmark creates a benchmark testing environment
func SetupBenchmark(b *testing.B, objectCount int) *BenchmarkHelper {
	engine := arxobject.NewEngine(objectCount * 2)
	db, _ := gorm.Open(sqlite.Open(":memory:"), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Silent),
	})
	
	// Create test objects
	objectIDs := make([]uint64, objectCount)
	for i := 0; i < objectCount; i++ {
		objectIDs[i] = engine.CreateObject(
			arxobject.StructuralWall,
			float32(i*10), float32(i*5), 0,
		)
	}
	
	return &BenchmarkHelper{
		Engine:    engine,
		DB:        db,
		ObjectIDs: objectIDs,
	}
}

// TestContext creates a test context with timeout
func TestContext(t *testing.T) context.Context {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	t.Cleanup(cancel)
	return ctx
}

// SkipIfIntegration skips test if running integration tests
func SkipIfIntegration(t *testing.T) {
	if os.Getenv("INTEGRATION_TESTS") == "1" {
		t.Skip("Skipping unit test in integration test mode")
	}
}

// SkipIfUnit skips test if running unit tests
func SkipIfUnit(t *testing.T) {
	if os.Getenv("INTEGRATION_TESTS") != "1" {
		t.Skip("Skipping integration test in unit test mode")
	}
}

// AssertPerformance checks that operation completes within expected time
func AssertPerformance(t *testing.T, expectedMaxDuration time.Duration, operation func()) {
	start := time.Now()
	operation()
	duration := time.Since(start)
	
	if duration > expectedMaxDuration {
		t.Errorf("Operation took %v, expected max %v", duration, expectedMaxDuration)
	}
}

// RandomString generates random string for testing
func RandomString(length int) string {
	const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	b := make([]byte, length)
	for i := range b {
		b[i] = charset[time.Now().UnixNano()%int64(len(charset))]
	}
	return string(b)
}

// TableTest represents a table-driven test case
type TableTest struct {
	Name           string
	Input          interface{}
	ExpectedOutput interface{}
	ExpectedError  error
	Setup          func()
	Cleanup        func()
}

// RunTableTests executes table-driven tests
func RunTableTests(t *testing.T, tests []TableTest, testFunc func(t *testing.T, test TableTest)) {
	for _, tt := range tests {
		t.Run(tt.Name, func(t *testing.T) {
			if tt.Setup != nil {
				tt.Setup()
			}
			if tt.Cleanup != nil {
				defer tt.Cleanup()
			}
			testFunc(t, tt)
		})
	}
}

// AssertFloat32Equal asserts two float32 values are approximately equal
func AssertFloat32Equal(t *testing.T, expected, actual float32, delta float32) {
	diff := expected - actual
	if diff < 0 {
		diff = -diff
	}
	assert.LessOrEqual(t, diff, delta, 
		fmt.Sprintf("Expected %f, got %f (delta: %f)", expected, actual, delta))
}

// AssertContainsSubstring checks if string contains substring (case insensitive)
func AssertContainsSubstring(t *testing.T, haystack, needle string) {
	assert.True(t, strings.Contains(strings.ToLower(haystack), strings.ToLower(needle)),
		fmt.Sprintf("String '%s' should contain '%s'", haystack, needle))
}

// MockHTTPClient for testing HTTP requests
type MockHTTPClient struct {
	responses map[string]*http.Response
	requests  []*http.Request
}

// NewMockHTTPClient creates a new mock HTTP client
func NewMockHTTPClient() *MockHTTPClient {
	return &MockHTTPClient{
		responses: make(map[string]*http.Response),
		requests:  make([]*http.Request, 0),
	}
}

// SetResponse sets a mock response for a URL
func (m *MockHTTPClient) SetResponse(url string, response *http.Response) {
	m.responses[url] = response
}

// Do executes the mock HTTP request
func (m *MockHTTPClient) Do(req *http.Request) (*http.Response, error) {
	m.requests = append(m.requests, req)
	
	if response, exists := m.responses[req.URL.String()]; exists {
		return response, nil
	}
	
	return &http.Response{
		StatusCode: http.StatusNotFound,
		Body:       http.NoBody,
	}, nil
}

// GetRequests returns all captured requests
func (m *MockHTTPClient) GetRequests() []*http.Request {
	return m.requests
}