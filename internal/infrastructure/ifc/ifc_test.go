package ifc

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestIfcOpenShellClient_ParseIFC(t *testing.T) {
	// Create a mock server
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/api/parse" {
			t.Errorf("Expected path /api/parse, got %s", r.URL.Path)
		}
		if r.Method != "POST" {
			t.Errorf("Expected POST method, got %s", r.Method)
		}

		// Return mock response
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{
			"success": true,
			"buildings": 1,
			"spaces": 10,
			"equipment": 25,
			"walls": 50,
			"doors": 15,
			"windows": 20,
			"total_entities": 121,
			"metadata": {
				"ifc_version": "IFC4",
				"file_size": 1024,
				"processing_time": "1.5s",
				"timestamp": "2024-01-01T00:00:00Z"
			}
		}`))
	}))
	defer server.Close()

	// Create client
	client := NewIfcOpenShellClient(server.URL, 30*time.Second, 3)

	// Test data
	testData := []byte("ISO-10303-21; HEADER; ... END-ISO-10303-21;")

	// Parse IFC
	result, err := client.ParseIFC(context.Background(), testData)
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	// Verify result
	if !result.Success {
		t.Error("Expected success to be true")
	}
	if result.Buildings != 1 {
		t.Errorf("Expected 1 building, got %d", result.Buildings)
	}
	if result.Spaces != 10 {
		t.Errorf("Expected 10 spaces, got %d", result.Spaces)
	}
	if result.Equipment != 25 {
		t.Errorf("Expected 25 equipment, got %d", result.Equipment)
	}
	if result.Metadata.IFCVersion != "IFC4" {
		t.Errorf("Expected IFC4 version, got %s", result.Metadata.IFCVersion)
	}
}

func TestIfcOpenShellClient_ValidateIFC(t *testing.T) {
	// Create a mock server
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/api/validate" {
			t.Errorf("Expected path /api/validate, got %s", r.URL.Path)
		}

		// Return mock response
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{
			"success": true,
			"valid": true,
			"warnings": ["No spaces found in IFC file"],
			"errors": [],
			"compliance": {
				"buildingSMART": true,
				"ifc4": true,
				"spatial_consistency": false
			},
			"metadata": {
				"ifc_version": "IFC4",
				"file_size": 1024,
				"processing_time": "0.5s",
				"timestamp": "2024-01-01T00:00:00Z"
			}
		}`))
	}))
	defer server.Close()

	// Create client
	client := NewIfcOpenShellClient(server.URL, 30*time.Second, 3)

	// Test data
	testData := []byte("ISO-10303-21; HEADER; ... END-ISO-10303-21;")

	// Validate IFC
	result, err := client.ValidateIFC(context.Background(), testData)
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	// Verify result
	if !result.Success {
		t.Error("Expected success to be true")
	}
	if !result.Valid {
		t.Error("Expected valid to be true")
	}
	if len(result.Warnings) != 1 {
		t.Errorf("Expected 1 warning, got %d", len(result.Warnings))
	}
	if len(result.Errors) != 0 {
		t.Errorf("Expected 0 errors, got %d", len(result.Errors))
	}
	if !result.Compliance.BuildingSMART {
		t.Error("Expected buildingSMART compliance to be true")
	}
}

func TestIfcOpenShellClient_Health(t *testing.T) {
	// Create a mock server
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/health" {
			t.Errorf("Expected path /health, got %s", r.URL.Path)
		}

		// Return mock response
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{
			"status": "healthy",
			"service": "ifcopenshell",
			"version": "0.8.3",
			"timestamp": "2024-01-01T00:00:00Z",
			"cache_enabled": true,
			"max_file_size": 104857600
		}`))
	}))
	defer server.Close()

	// Create client
	client := NewIfcOpenShellClient(server.URL, 30*time.Second, 3)

	// Check health
	result, err := client.Health(context.Background())
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	// Verify result
	if result.Status != "healthy" {
		t.Errorf("Expected status 'healthy', got %s", result.Status)
	}
	if result.Service != "ifcopenshell" {
		t.Errorf("Expected service 'ifcopenshell', got %s", result.Service)
	}
	if result.Version != "0.8.3" {
		t.Errorf("Expected version '0.8.3', got %s", result.Version)
	}
	if !result.CacheEnabled {
		t.Error("Expected cache to be enabled")
	}
	if result.MaxFileSize != 104857600 {
		t.Errorf("Expected max file size 104857600, got %d", result.MaxFileSize)
	}
}

func TestIfcOpenShellClient_IsAvailable(t *testing.T) {
	// Test available service
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status": "healthy"}`))
	}))
	defer server.Close()

	client := NewIfcOpenShellClient(server.URL, 30*time.Second, 3)

	if !client.IsAvailable(context.Background()) {
		t.Error("Expected service to be available")
	}

	// Test unavailable service
	unavailableClient := NewIfcOpenShellClient("http://localhost:9999", 1*time.Second, 1)

	if unavailableClient.IsAvailable(context.Background()) {
		t.Error("Expected service to be unavailable")
	}
}

func TestNativeParser_ParseIFC(t *testing.T) {
	parser := NewNativeParser(100 * 1024 * 1024) // 100MB

	// Test valid IFC data
	validIFC := []byte(`ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('test.ifc','2024-01-01T00:00:00',('Test User'),('Test Organization'),'Test Software','Test Software Version','Test Identifier');
FILE_SCHEMA(('IFC4'));
ENDSEC;

DATA;
#1=IFCPROJECT('0',$,$,$,(#2),#3);
#2=IFCOWNERHISTORY($,$,$,$,$,$,$,$,$);
#3=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.0E-5,$,$);
ENDSEC;

END-ISO-10303-21;`)

	result, err := parser.ParseIFC(context.Background(), validIFC)
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	if !result.Success {
		t.Error("Expected success to be true")
	}
	// Native parser is a basic fallback - doesn't extract buildings, just validates format
	// For full parsing, use IfcOpenShell service
	t.Logf("Native parser result: %d buildings, %d entities total", result.Buildings, result.TotalEntities)

	if result.Metadata.IFCVersion == "Unknown" {
		t.Error("Expected IFC version to be detected")
	}

	// Test invalid IFC data
	invalidIFC := []byte("Not an IFC file")

	_, err = parser.ParseIFC(context.Background(), invalidIFC)
	if err == nil {
		t.Error("Expected error for invalid IFC data")
	}

	// Test file size limit
	largeData := make([]byte, 200*1024*1024) // 200MB

	_, err = parser.ParseIFC(context.Background(), largeData)
	if err == nil {
		t.Error("Expected error for file exceeding size limit")
	}
}

func TestNativeParser_ValidateIFC(t *testing.T) {
	parser := NewNativeParser(100 * 1024 * 1024) // 100MB

	// Test valid IFC data
	validIFC := []byte(`ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('test.ifc','2024-01-01T00:00:00',('Test User'),('Test Organization'),'Test Software','Test Software Version','Test Identifier');
FILE_SCHEMA(('IFC4'));
ENDSEC;

DATA;
#1=IFCPROJECT('0',$,$,$,(#2),#3);
#2=IFCOWNERHISTORY($,$,$,$,$,$,$,$,$);
#3=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.0E-5,$,$);
ENDSEC;

END-ISO-10303-21;`)

	result, err := parser.ValidateIFC(context.Background(), validIFC)
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	if !result.Success {
		t.Error("Expected success to be true")
	}
	if !result.Valid {
		t.Error("Expected valid to be true")
	}
	if len(result.Errors) > 0 {
		t.Errorf("Expected no errors, got %d", len(result.Errors))
	}

	// Test invalid IFC data
	invalidIFC := []byte("Not an IFC file")

	result, err = parser.ValidateIFC(context.Background(), invalidIFC)
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	if result.Valid {
		t.Error("Expected valid to be false for invalid IFC")
	}
	if len(result.Errors) == 0 {
		t.Error("Expected errors for invalid IFC")
	}
}

func TestIFCService_ParseIFC(t *testing.T) {
	// Create mock IfcOpenShell client
	mockServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"success": true, "buildings": 1, "spaces": 10}`))
	}))
	defer mockServer.Close()

	client := NewIfcOpenShellClient(mockServer.URL, 30*time.Second, 3)
	nativeParser := NewNativeParser(100 * 1024 * 1024)

	// Test with service enabled
	service := NewIFCService(client, nativeParser, true, true, 3, 60*time.Second)

	// Use valid IFC data for testing
	testData := []byte(`ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('test.ifc','2024-01-01T00:00:00',(),(),'Test','Test','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPROJECT('0',$,$,$,(#2),#3);
#2=IFCOWNERHISTORY($,$,$,$,$,$,$,$,$);
#3=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.0E-5,$,$);
ENDSEC;
END-ISO-10303-21;`)

	result, err := service.ParseIFC(context.Background(), testData)
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	if !result.Success {
		t.Error("Expected success to be true")
	}

	// Test with service disabled
	serviceDisabled := NewIFCService(client, nativeParser, false, true, 3, 60*time.Second)

	result, err = serviceDisabled.ParseIFC(context.Background(), testData)
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	if !result.Success {
		t.Error("Expected success to be true")
	}

	// Test with both disabled
	serviceBothDisabled := NewIFCService(client, nativeParser, false, false, 3, 60*time.Second)

	_, err = serviceBothDisabled.ParseIFC(context.Background(), testData)
	if err == nil {
		t.Error("Expected error when both service and fallback are disabled")
	}
}

func TestCircuitBreaker(t *testing.T) {
	cb := &CircuitBreaker{
		failureThreshold: 3,
		recoveryTimeout:  100 * time.Millisecond,
		state:            Closed,
		failures:         0,
	}

	// Test successful calls
	for i := 0; i < 5; i++ {
		cb.recordSuccess()
		if cb.state != Closed {
			t.Errorf("Expected state to be Closed, got %v", cb.state)
		}
		if cb.failures != 0 {
			t.Errorf("Expected failures to be 0, got %d", cb.failures)
		}
	}

	// Test failure threshold
	for i := 0; i < 3; i++ {
		cb.recordFailure()
	}

	if cb.state != Open {
		t.Errorf("Expected state to be Open, got %v", cb.state)
	}

	// Test recovery
	time.Sleep(150 * time.Millisecond)
	cb.state = HalfOpen

	cb.recordSuccess()
	if cb.state != Closed {
		t.Errorf("Expected state to be Closed after recovery, got %v", cb.state)
	}
	if cb.failures != 0 {
		t.Errorf("Expected failures to be 0 after recovery, got %d", cb.failures)
	}
}
