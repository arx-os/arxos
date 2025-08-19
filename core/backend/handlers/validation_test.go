package handlers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/arxos/arxos/core/arxobject"
	"github.com/arxos/arxos/core/backend/models"
	"github.com/arxos/arxos/core/backend/services"
	"github.com/gorilla/websocket"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// MockValidationService for testing
type MockValidationService struct {
	mock.Mock
}

func (m *MockValidationService) GetPendingValidations(priority, objectType, limit string) ([]*models.ValidationTask, error) {
	args := m.Called(priority, objectType, limit)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*models.ValidationTask), args.Error(1)
}

func (m *MockValidationService) CreateValidationTask(task *models.ValidationTask) error {
	args := m.Called(task)
	return args.Error(0)
}

func (m *MockValidationService) SaveValidation(submission *models.ValidationSubmission, impact *models.ValidationImpact) error {
	args := m.Called(submission, impact)
	return args.Error(0)
}

func (m *MockValidationService) GetValidationHistory(objectID, validator, startDate, endDate string) ([]models.ValidationRecord, error) {
	args := m.Called(objectID, validator, startDate, endDate)
	return args.Get(0).([]models.ValidationRecord), args.Error(1)
}

func (m *MockValidationService) GetLeaderboard(period string) ([]models.ValidatorStats, error) {
	args := m.Called(period)
	return args.Get(0).([]models.ValidatorStats), args.Error(1)
}

func (m *MockValidationService) LearnPattern(validated *arxobject.ArxObject, similar []*arxobject.ArxObject, submission models.ValidationSubmission) bool {
	args := m.Called(validated, similar, submission)
	return args.Bool(0)
}

// Test GetPendingValidations
func TestGetPendingValidations(t *testing.T) {
	// Setup
	mockService := new(MockValidationService)
	engine := arxobject.NewEngine(100)
	handler := NewValidationHandler(mockService, engine)
	
	// Create test tasks
	tasks := []*models.ValidationTask{
		{
			ID:         1,
			ObjectID:   "wall_001",
			ObjectType: "wall",
			Confidence: 0.45,
			Priority:   8,
			CreatedAt:  time.Now(),
		},
		{
			ID:         2,
			ObjectID:   "door_001",
			ObjectType: "door",
			Confidence: 0.55,
			Priority:   6,
			CreatedAt:  time.Now(),
		},
	}
	
	mockService.On("GetPendingValidations", "", "", "").Return(tasks, nil)
	
	// Create request
	req, err := http.NewRequest("GET", "/api/validations/pending", nil)
	assert.NoError(t, err)
	
	// Record response
	rr := httptest.NewRecorder()
	handler.GetPendingValidations(rr, req)
	
	// Check response
	assert.Equal(t, http.StatusOK, rr.Code)
	
	var response map[string]interface{}
	err = json.Unmarshal(rr.Body.Bytes(), &response)
	assert.NoError(t, err)
	
	validations := response["validations"].([]interface{})
	assert.Len(t, validations, 2)
	assert.Equal(t, float64(2), response["total"])
	
	mockService.AssertExpectations(t)
}

// Test FlagForValidation
func TestFlagForValidation(t *testing.T) {
	// Setup
	mockService := new(MockValidationService)
	engine := arxobject.NewEngine(100)
	handler := NewValidationHandler(mockService, engine)
	
	// Create test object in engine
	objID := engine.CreateObject(arxobject.StructuralWall, 10, 20, 0)
	
	// Mock service expectation
	mockService.On("CreateValidationTask", mock.AnythingOfType("*models.ValidationTask")).Return(nil)
	
	// Create request
	reqBody := map[string]interface{}{
		"object_id": fmt.Sprintf("%d", objID),
		"reason":    "Low confidence detected",
		"priority":  7,
	}
	
	body, _ := json.Marshal(reqBody)
	req, err := http.NewRequest("POST", "/api/validations/flag", bytes.NewBuffer(body))
	assert.NoError(t, err)
	
	// Record response
	rr := httptest.NewRecorder()
	handler.FlagForValidation(rr, req)
	
	// Check response
	assert.Equal(t, http.StatusOK, rr.Code)
	
	var response map[string]interface{}
	err = json.Unmarshal(rr.Body.Bytes(), &response)
	assert.NoError(t, err)
	
	assert.True(t, response["success"].(bool))
	assert.NotNil(t, response["validation"])
	
	mockService.AssertExpectations(t)
}

// Test SubmitValidation
func TestSubmitValidation(t *testing.T) {
	// Setup
	mockService := new(MockValidationService)
	engine := arxobject.NewEngine(100)
	handler := NewValidationHandler(mockService, engine)
	
	// Create test objects
	objID := engine.CreateObjectWithConfidence(
		arxobject.StructuralWall, 10, 20, 0,
		arxobject.NewConfidenceScore(0.5, 0.5, 0.5, 0.5),
	)
	
	// Create similar objects for cascade
	similar1 := engine.CreateObject(arxobject.StructuralWall, 15, 20, 0)
	similar2 := engine.CreateObject(arxobject.StructuralWall, 20, 20, 0)
	
	// Mock service expectations
	mockService.On("SaveValidation", 
		mock.AnythingOfType("*models.ValidationSubmission"),
		mock.AnythingOfType("*models.ValidationImpact"),
	).Return(nil)
	
	mockService.On("LearnPattern",
		mock.AnythingOfType("*arxobject.ArxObject"),
		mock.AnythingOfType("[]*arxobject.ArxObject"),
		mock.AnythingOfType("models.ValidationSubmission"),
	).Return(true)
	
	// Create validation submission
	submission := ValidationSubmission{
		ObjectID:       fmt.Sprintf("%d", objID),
		ValidationType: "dimension",
		Data: map[string]interface{}{
			"length":    10.5,
			"thickness": 0.15,
		},
		Validator:  "test_user",
		Confidence: 0.95,
		Timestamp:  time.Now(),
	}
	
	body, _ := json.Marshal(submission)
	req, err := http.NewRequest("POST", "/api/validations/submit", bytes.NewBuffer(body))
	assert.NoError(t, err)
	
	// Record response
	rr := httptest.NewRecorder()
	handler.SubmitValidation(rr, req)
	
	// Check response
	assert.Equal(t, http.StatusOK, rr.Code)
	
	var response map[string]interface{}
	err = json.Unmarshal(rr.Body.Bytes(), &response)
	assert.NoError(t, err)
	
	assert.True(t, response["success"].(bool))
	
	impact := response["impact"].(map[string]interface{})
	assert.NotNil(t, impact)
	assert.Greater(t, impact["new_confidence"].(float64), impact["old_confidence"].(float64))
	
	mockService.AssertExpectations(t)
}

// Test confidence improvement calculation
func TestConfidenceImprovement(t *testing.T) {
	engine := arxobject.NewEngine(100)
	
	// Create object with low confidence
	obj, _ := engine.GetObject(
		engine.CreateObjectWithConfidence(
			arxobject.StructuralWall, 10, 20, 0,
			arxobject.NewConfidenceScore(0.4, 0.4, 0.4, 0.4),
		),
	)
	
	oldConfidence := obj.Confidence.Overall
	
	// Simulate validation
	submission := &ValidationSubmission{
		ValidationType: "dimension",
		Confidence:     0.95,
		Validator:      "expert",
	}
	
	handler := &ValidationHandler{arxEngine: engine}
	handler.updateObjectConfidence(obj, submission)
	
	// Check confidence improved
	assert.Greater(t, obj.Confidence.Overall, oldConfidence)
	assert.Greater(t, obj.Confidence.Position, float32(0.6))
	assert.Greater(t, obj.Confidence.Properties, float32(0.5))
}

// Test cascade validation
func TestCascadeValidation(t *testing.T) {
	engine := arxobject.NewEngine(100)
	handler := &ValidationHandler{arxEngine: engine}
	
	// Create validated object
	validated, _ := engine.GetObject(
		engine.CreateObjectWithConfidence(
			arxobject.StructuralWall, 10, 20, 0,
			arxobject.NewConfidenceScore(0.9, 0.9, 0.9, 0.9),
		),
	)
	
	// Create similar objects with lower confidence
	similar := []*arxobject.ArxObject{}
	for i := 0; i < 3; i++ {
		obj, _ := engine.GetObject(
			engine.CreateObjectWithConfidence(
				arxobject.StructuralWall, float32(10+i*5), 20, 0,
				arxobject.NewConfidenceScore(0.4, 0.4, 0.4, 0.4),
			),
		)
		similar = append(similar, obj)
	}
	
	// Apply cascade
	cascaded := handler.applyCascadeValidation(validated, similar, 0.95)
	
	// Check cascaded objects improved
	assert.Len(t, cascaded, 3)
	for _, obj := range cascaded {
		assert.Greater(t, obj.Confidence.Overall, float32(0.4))
	}
}

// Test WebSocket connection
func TestWebSocketConnection(t *testing.T) {
	// Setup
	mockService := new(MockValidationService)
	engine := arxobject.NewEngine(100)
	handler := NewValidationHandler(mockService, engine)
	
	// Create test server
	server := httptest.NewServer(http.HandlerFunc(handler.WebSocketHandler))
	defer server.Close()
	
	// Convert http to ws URL
	wsURL := "ws" + server.URL[4:]
	
	// Connect to WebSocket
	ws, _, err := websocket.DefaultDialer.Dial(wsURL, nil)
	assert.NoError(t, err)
	defer ws.Close()
	
	// Send ping
	err = ws.WriteMessage(websocket.PingMessage, []byte{})
	assert.NoError(t, err)
	
	// Should receive pong
	ws.SetPongHandler(func(string) error {
		return nil
	})
}

// Benchmark validation submission
func BenchmarkValidationSubmission(b *testing.B) {
	// Setup
	mockService := new(MockValidationService)
	engine := arxobject.NewEngine(1000)
	handler := NewValidationHandler(mockService, engine)
	
	// Create test objects
	for i := 0; i < 100; i++ {
		engine.CreateObject(arxobject.StructuralWall, float32(i*10), 20, 0)
	}
	
	mockService.On("SaveValidation", mock.Anything, mock.Anything).Return(nil)
	mockService.On("LearnPattern", mock.Anything, mock.Anything, mock.Anything).Return(false)
	
	submission := ValidationSubmission{
		ObjectID:       "1",
		ValidationType: "dimension",
		Data:           map[string]interface{}{"length": 10.5},
		Validator:      "test",
		Confidence:     0.95,
		Timestamp:      time.Now(),
	}
	
	body, _ := json.Marshal(submission)
	
	b.ResetTimer()
	
	for i := 0; i < b.N; i++ {
		req, _ := http.NewRequest("POST", "/api/validations/submit", bytes.NewBuffer(body))
		rr := httptest.NewRecorder()
		handler.SubmitValidation(rr, req)
	}
}

// Test validation priority calculation
func TestValidationPriorityCalculation(t *testing.T) {
	engine := arxobject.NewEngine(100)
	handler := &ValidationHandler{arxEngine: engine}
	
	tests := []struct {
		name           string
		objectType     arxobject.ArxObjectType
		confidence     float32
		userPriority   int
		expectedMin    int
	}{
		{
			name:         "Structural low confidence",
			objectType:   arxobject.StructuralWall,
			confidence:   0.2,
			expectedMin:  8, // High criticality + low confidence
		},
		{
			name:         "MEP medium confidence",
			objectType:   arxobject.HVACUnit,
			confidence:   0.5,
			expectedMin:  6,
		},
		{
			name:         "User override priority",
			objectType:   arxobject.ElectricalOutlet,
			confidence:   0.7,
			userPriority: 10,
			expectedMin:  10,
		},
	}
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			obj, _ := engine.GetObject(
				engine.CreateObjectWithConfidence(
					tt.objectType, 10, 20, 0,
					arxobject.NewConfidenceScore(tt.confidence, tt.confidence, tt.confidence, tt.confidence),
				),
			)
			
			priority := handler.calculatePriority(obj, tt.userPriority)
			assert.GreaterOrEqual(t, priority, tt.expectedMin)
		})
	}
}