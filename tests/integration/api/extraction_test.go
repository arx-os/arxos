package tests

import (
	"encoding/json"
	"testing"
	"time"

	"arxos/arxobject"
	"arxos/services"
)

// TestIDFExtractorCreation tests basic IDF extractor creation
func TestIDFExtractorCreation(t *testing.T) {
	engine := arxobject.NewEngine(nil)
	extractor := services.NewIDFExtractor(engine)
	
	if extractor == nil {
		t.Fatal("IDF extractor should not be nil")
	}
}

// TestProcessIDFCalloutInputValidation tests input validation for ProcessIDFCallout
func TestProcessIDFCalloutInputValidation(t *testing.T) {
	engine := arxobject.NewEngine(nil)
	extractor := services.NewIDFExtractor(engine)
	
	// Test empty filepath
	result, err := extractor.ProcessIDFCallout("")
	if err == nil {
		t.Error("Expected error for empty filepath")
	}
	if result != nil {
		t.Error("Result should be nil for invalid input")
	}
	
	// Test with nil engine
	nilExtractor := services.NewIDFExtractor(nil)
	result, err = nilExtractor.ProcessIDFCallout("test.pdf")
	if err == nil {
		t.Error("Expected error for nil engine")
	}
}

// TestArxObjectValidation tests ArxObject validation and sanitization
func TestArxObjectValidation(t *testing.T) {
	// Test valid object
	validObj := &arxobject.ArxObject{
		ID:     "test_wall_001",
		UUID:   "123e4567-e89b-12d3-a456-426614174000",
		Type:   "wall",
		System: "structural",
		X:      1000000, // 1mm in nanometers
		Y:      2000000, // 2mm in nanometers
		Z:      0,
		Width:  3000000000, // 3m in nanometers
		Height: 2700000000, // 2.7m in nanometers
		Depth:  200000000,  // 200mm in nanometers
		Confidence: arxobject.ConfidenceScore{
			Classification: 0.9,
			Position:       0.8,
			Properties:     0.7,
			Relationships:  0.6,
			Overall:        0.75,
		},
		ExtractionMethod: "test",
		Source:          "unit_test",
		CreatedAt:       time.Now(),
		UpdatedAt:       time.Now(),
	}
	
	// Add valid properties
	props := map[string]interface{}{
		"material":   "concrete",
		"thickness":  200,
		"fire_rating": "2-hour",
	}
	propsJSON, _ := json.Marshal(props)
	validObj.Properties = propsJSON
	
	validator := arxobject.NewArxObjectValidator(nil)
	result := validator.ValidateAndSanitize(validObj)
	
	if !result.IsValid {
		t.Errorf("Valid object should pass validation, got %d errors", len(result.Errors))
		for _, err := range result.Errors {
			t.Logf("Validation error: %s - %s", err.Field, err.Message)
		}
	}
	
	if result.SanitizedObj == nil {
		t.Error("Sanitized object should not be nil for valid input")
	}
}

// TestArxObjectValidationErrors tests validation error cases
func TestArxObjectValidationErrors(t *testing.T) {
	validator := arxobject.NewArxObjectValidator(nil)
	
	// Test nil object
	result := validator.ValidateAndSanitize(nil)
	if result.IsValid {
		t.Error("Nil object should fail validation")
	}
	
	// Test empty ID
	invalidObj := &arxobject.ArxObject{
		ID:     "", // Invalid: empty ID
		Type:   "wall",
		System: "structural",
	}
	
	result = validator.ValidateAndSanitize(invalidObj)
	if result.IsValid {
		t.Error("Object with empty ID should fail validation")
	}
	
	// Check for specific error
	foundIDError := false
	for _, err := range result.Errors {
		if err.Field == "ID" && err.Code == "REQUIRED_FIELD" {
			foundIDError = true
			break
		}
	}
	if !foundIDError {
		t.Error("Expected ID required field error")
	}
}

// TestArxObjectSanitization tests sanitization functionality
func TestArxObjectSanitization(t *testing.T) {
	validator := arxobject.NewArxObjectValidator(nil)
	
	// Test object that needs sanitization
	obj := &arxobject.ArxObject{
		ID:     "  test_wall_001  ", // Needs trimming
		Type:   "WALL",             // Needs lowercasing
		System: "STRUCTURAL",       // Needs lowercasing
		Width:  -1000,              // Negative dimension (should be sanitized to 0)
		Confidence: arxobject.ConfidenceScore{
			Classification: 1.5,  // Above max, should be clamped
			Position:       -0.1, // Below min, should be clamped
			Properties:     0.5,
			Relationships:  0.5,
		},
	}
	
	result := validator.ValidateAndSanitize(obj)
	
	if !result.IsValid {
		t.Errorf("Object should be valid after sanitization, got %d errors", len(result.Errors))
	}
	
	if len(result.Warnings) == 0 {
		t.Error("Expected warnings for sanitized fields")
	}
	
	sanitized := result.SanitizedObj
	if sanitized == nil {
		t.Fatal("Sanitized object should not be nil")
	}
	
	// Check sanitization results
	if sanitized.ID != "test_wall_001" {
		t.Errorf("ID should be trimmed, got: %s", sanitized.ID)
	}
	
	if sanitized.Type != "wall" {
		t.Errorf("Type should be lowercase, got: %s", sanitized.Type)
	}
	
	if sanitized.System != "structural" {
		t.Errorf("System should be lowercase, got: %s", sanitized.System)
	}
	
	if sanitized.Width != 0 {
		t.Errorf("Negative width should be sanitized to 0, got: %d", sanitized.Width)
	}
	
	if sanitized.Confidence.Classification > 1.0 {
		t.Errorf("Classification confidence should be clamped to 1.0, got: %f", sanitized.Confidence.Classification)
	}
	
	if sanitized.Confidence.Position < 0.0 {
		t.Errorf("Position confidence should be clamped to 0.0, got: %f", sanitized.Confidence.Position)
	}
}

// TestExtractionErrorTypes tests different extraction error types
func TestExtractionErrorTypes(t *testing.T) {
	// Test basic extraction error
	err := services.NewExtractionError("test_operation", "test message", nil)
	if err == nil {
		t.Fatal("Extraction error should not be nil")
	}
	
	if err.Operation != "test_operation" {
		t.Errorf("Expected operation 'test_operation', got: %s", err.Operation)
	}
	
	if err.Message != "test message" {
		t.Errorf("Expected message 'test message', got: %s", err.Message)
	}
	
	if !err.Recoverable {
		t.Error("Default extraction error should be recoverable")
	}
	
	// Test fatal extraction error
	fatalErr := services.NewFatalExtractionError("fatal_operation", "fatal message", nil)
	if fatalErr.Recoverable {
		t.Error("Fatal extraction error should not be recoverable")
	}
	
	// Test error with context
	errWithContext := services.NewExtractionError("context_operation", "context message", nil)
	errWithContext.WithContext("test_key", "test_value")
	
	if errWithContext.Context["test_key"] != "test_value" {
		t.Error("Context should be properly set")
	}
}

// TestValidationError tests validation error functionality
func TestValidationError(t *testing.T) {
	err := services.NewValidationError("test_field", "test_value", "test error message")
	
	if err.Field != "test_field" {
		t.Errorf("Expected field 'test_field', got: %s", err.Field)
	}
	
	if err.Value != "test_value" {
		t.Errorf("Expected value 'test_value', got: %v", err.Value)
	}
	
	if err.Message != "test error message" {
		t.Errorf("Expected message 'test error message', got: %s", err.Message)
	}
	
	errStr := err.Error()
	if errStr == "" {
		t.Error("Error string should not be empty")
	}
}

// TestProcessingError tests processing error functionality
func TestProcessingError(t *testing.T) {
	err := services.NewProcessingError("obj_001", "wall", "validation", "validation failed", nil)
	
	if err.ObjectID != "obj_001" {
		t.Errorf("Expected ObjectID 'obj_001', got: %s", err.ObjectID)
	}
	
	if err.ObjectType != "wall" {
		t.Errorf("Expected ObjectType 'wall', got: %s", err.ObjectType)
	}
	
	if err.Stage != "validation" {
		t.Errorf("Expected Stage 'validation', got: %s", err.Stage)
	}
	
	errStr := err.Error()
	if errStr == "" {
		t.Error("Error string should not be empty")
	}
}

// TestCircuitBreakerBasicFunctionality tests basic circuit breaker operations
func TestCircuitBreakerBasicFunctionality(t *testing.T) {
	config := &services.CircuitBreakerConfig{
		MaxFailures:      2,
		Timeout:          100 * time.Millisecond,
		MaxRequests:      1,
		SuccessThreshold: 1,
	}
	
	cb := services.NewCircuitBreaker("test_circuit", config)
	
	// Test initial state
	if cb.GetState() != services.StateClosed {
		t.Error("Initial state should be CLOSED")
	}
	
	// Test successful execution
	err := cb.Execute(func() error {
		return nil // Success
	})
	
	if err != nil {
		t.Errorf("Successful execution should not return error: %v", err)
	}
	
	// Test failure
	err = cb.Execute(func() error {
		return services.NewExtractionError("test", "simulated failure", nil)
	})
	
	if err == nil {
		t.Error("Failed execution should return error")
	}
	
	// Test multiple failures to trigger circuit opening
	cb.Execute(func() error {
		return services.NewExtractionError("test", "failure 2", nil)
	})
	
	if cb.GetState() != services.StateOpen {
		t.Error("Circuit should be OPEN after max failures")
	}
	
	// Test circuit breaker blocking requests
	err = cb.Execute(func() error {
		return nil
	})
	
	if err == nil {
		t.Error("Circuit breaker should block requests when OPEN")
	}
	
	_, ok := err.(*services.CircuitBreakerError)
	if !ok {
		t.Error("Error should be CircuitBreakerError type")
	}
}

// TestCircuitBreakerRecovery tests circuit breaker recovery functionality
func TestCircuitBreakerRecovery(t *testing.T) {
	config := &services.CircuitBreakerConfig{
		MaxFailures:      1,
		Timeout:          50 * time.Millisecond,
		MaxRequests:      1,
		SuccessThreshold: 1,
	}
	
	cb := services.NewCircuitBreaker("recovery_test", config)
	
	// Trigger failure to open circuit
	cb.Execute(func() error {
		return services.NewExtractionError("test", "failure", nil)
	})
	
	if cb.GetState() != services.StateOpen {
		t.Error("Circuit should be OPEN after failure")
	}
	
	// Wait for timeout
	time.Sleep(60 * time.Millisecond)
	
	// Next execution should transition to HALF_OPEN
	err := cb.Execute(func() error {
		return nil // Success
	})
	
	if err != nil {
		t.Errorf("Execution after timeout should succeed: %v", err)
	}
	
	if cb.GetState() != services.StateClosed {
		t.Error("Circuit should be CLOSED after successful recovery")
	}
}

// BenchmarkArxObjectValidation benchmarks ArxObject validation performance
func BenchmarkArxObjectValidation(b *testing.B) {
	validator := arxobject.NewArxObjectValidator(nil)
	
	obj := &arxobject.ArxObject{
		ID:     "benchmark_wall_001",
		UUID:   "123e4567-e89b-12d3-a456-426614174000",
		Type:   "wall",
		System: "structural",
		X:      1000000,
		Y:      2000000,
		Z:      0,
		Width:  3000000000,
		Height: 2700000000,
		Depth:  200000000,
		Confidence: arxobject.ConfidenceScore{
			Classification: 0.9,
			Position:       0.8,
			Properties:     0.7,
			Relationships:  0.6,
			Overall:        0.75,
		},
		ExtractionMethod: "benchmark",
		Source:          "performance_test",
		CreatedAt:       time.Now(),
		UpdatedAt:       time.Now(),
	}
	
	// Add properties
	props := map[string]interface{}{
		"material":    "concrete",
		"thickness":   200,
		"fire_rating": "2-hour",
	}
	propsJSON, _ := json.Marshal(props)
	obj.Properties = propsJSON
	
	b.ResetTimer()
	
	for i := 0; i < b.N; i++ {
		result := validator.ValidateAndSanitize(obj)
		if !result.IsValid {
			b.Fatalf("Validation should succeed in benchmark")
		}
	}
}

// BenchmarkCircuitBreakerExecution benchmarks circuit breaker execution performance
func BenchmarkCircuitBreakerExecution(b *testing.B) {
	cb := services.NewCircuitBreaker("benchmark_circuit", services.DefaultCircuitBreakerConfig())
	
	b.ResetTimer()
	
	for i := 0; i < b.N; i++ {
		cb.Execute(func() error {
			return nil // Successful operation
		})
	}
}