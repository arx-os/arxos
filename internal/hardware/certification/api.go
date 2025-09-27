package certification

import (
	"context"
	"encoding/json"
	"net/http"
	"strconv"
	"time"
)

// CertificationAPI provides HTTP API for certification management
type CertificationAPI struct {
	manager    *CertificationManager
	testRunner *TestRunner
	reportGen  *ReportGenerator
}

// NewCertificationAPI creates a new certification API
func NewCertificationAPI(manager *CertificationManager) *CertificationAPI {
	return &CertificationAPI{
		manager:    manager,
		testRunner: NewTestRunner(manager),
		reportGen:  NewReportGenerator(),
	}
}

// RegisterRoutes registers HTTP routes for the certification API
func (api *CertificationAPI) RegisterRoutes(mux *http.ServeMux) {
	// Test management routes
	mux.HandleFunc("/api/v1/certification/tests", api.handleTests)
	mux.HandleFunc("/api/v1/certification/tests/", api.handleTestByID)

	// Test execution routes
	mux.HandleFunc("/api/v1/certification/execute", api.handleExecuteTest)
	mux.HandleFunc("/api/v1/certification/execute/suite", api.handleExecuteTestSuite)
	mux.HandleFunc("/api/v1/certification/executions/", api.handleExecutionByID)

	// Results and reports routes
	mux.HandleFunc("/api/v1/certification/results/", api.handleResultsByDevice)
	mux.HandleFunc("/api/v1/certification/reports/", api.handleReportByDevice)

	// Standards and compliance routes
	mux.HandleFunc("/api/v1/certification/standards", api.handleStandards)
	mux.HandleFunc("/api/v1/certification/standards/", api.handleStandardByID)

	// Metrics and statistics routes
	mux.HandleFunc("/api/v1/certification/metrics", api.handleMetrics)
	mux.HandleFunc("/api/v1/certification/stats", api.handleStats)
}

// handleTests handles test management requests
func (api *CertificationAPI) handleTests(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getTests(w, r)
	case http.MethodPost:
		api.createTest(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// handleTestByID handles individual test requests
func (api *CertificationAPI) handleTestByID(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getTestByID(w, r)
	case http.MethodPut:
		api.updateTest(w, r)
	case http.MethodDelete:
		api.deleteTest(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// handleExecuteTest handles test execution requests
func (api *CertificationAPI) handleExecuteTest(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		DeviceID string                 `json:"device_id"`
		TestID   string                 `json:"test_id"`
		Config   map[string]interface{} `json:"config"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	execution, err := api.testRunner.RunTest(context.Background(), req.DeviceID, req.TestID, req.Config)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(execution)
}

// handleExecuteTestSuite handles test suite execution requests
func (api *CertificationAPI) handleExecuteTestSuite(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		DeviceID string                 `json:"device_id"`
		TestIDs  []string               `json:"test_ids"`
		Config   map[string]interface{} `json:"config"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	execution, err := api.testRunner.RunTestSuite(context.Background(), req.DeviceID, req.TestIDs, req.Config)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(execution)
}

// handleExecutionByID handles execution status requests
func (api *CertificationAPI) handleExecutionByID(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	executionID := r.URL.Path[len("/api/v1/certification/executions/"):]
	if executionID == "" {
		http.Error(w, "Execution ID required", http.StatusBadRequest)
		return
	}

	execution, err := api.testRunner.GetExecution(executionID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(execution)
}

// handleResultsByDevice handles device results requests
func (api *CertificationAPI) handleResultsByDevice(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	deviceID := r.URL.Path[len("/api/v1/certification/results/"):]
	if deviceID == "" {
		http.Error(w, "Device ID required", http.StatusBadRequest)
		return
	}

	results, err := api.manager.GetDeviceCertification(deviceID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(results)
}

// handleReportByDevice handles device report requests
func (api *CertificationAPI) handleReportByDevice(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	deviceID := r.URL.Path[len("/api/v1/certification/reports/"):]
	if deviceID == "" {
		http.Error(w, "Device ID required", http.StatusBadRequest)
		return
	}

	// Get device results
	results, err := api.manager.GetDeviceCertification(deviceID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Get format from query parameter
	format := r.URL.Query().Get("format")
	if format == "" {
		format = "json"
	}

	var data []byte
	switch format {
	case "json":
		data, err = api.reportGen.GenerateJSONReport(deviceID, results)
	case "html":
		data, err = api.reportGen.GenerateHTMLReport(deviceID, results)
	case "pdf":
		data, err = api.reportGen.GeneratePDFReport(deviceID, results)
	default:
		http.Error(w, "Unsupported format", http.StatusBadRequest)
		return
	}

	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Set appropriate content type
	switch format {
	case "json":
		w.Header().Set("Content-Type", "application/json")
	case "html":
		w.Header().Set("Content-Type", "text/html")
	case "pdf":
		w.Header().Set("Content-Type", "application/pdf")
	}

	w.Write(data)
}

// handleStandards handles standards management requests
func (api *CertificationAPI) handleStandards(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getStandards(w, r)
	case http.MethodPost:
		api.createStandard(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// handleStandardByID handles individual standard requests
func (api *CertificationAPI) handleStandardByID(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	standardID := r.URL.Path[len("/api/v1/certification/standards/"):]
	if standardID == "" {
		http.Error(w, "Standard ID required", http.StatusBadRequest)
		return
	}

	// Get standard by ID
	standards := api.manager.ListStandards()
	for _, standard := range standards {
		if standard.ID == standardID {
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(standard)
			return
		}
	}

	http.Error(w, "Standard not found", http.StatusNotFound)
}

// handleMetrics handles metrics requests
func (api *CertificationAPI) handleMetrics(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	metrics := api.manager.GetMetrics()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(metrics)
}

// handleStats handles statistics requests
func (api *CertificationAPI) handleStats(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Get test runner metrics
	testMetrics := api.testRunner.GetMetrics()

	// Get certification manager metrics
	certMetrics := api.manager.GetMetrics()

	stats := map[string]interface{}{
		"certification": certMetrics,
		"test_runner":   testMetrics,
		"timestamp":     time.Now(),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(stats)
}

// getTests returns all tests
func (api *CertificationAPI) getTests(w http.ResponseWriter, r *http.Request) {
	tests := api.manager.ListTests()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(tests)
}

// createTest creates a new test
func (api *CertificationAPI) createTest(w http.ResponseWriter, r *http.Request) {
	var test CertificationTest
	if err := json.NewDecoder(r.Body).Decode(&test); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.manager.RegisterTest(&test); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(test)
}

// getTestByID returns a specific test
func (api *CertificationAPI) getTestByID(w http.ResponseWriter, r *http.Request) {
	testID := r.URL.Path[len("/api/v1/certification/tests/"):]
	if testID == "" {
		http.Error(w, "Test ID required", http.StatusBadRequest)
		return
	}

	// Find test by ID
	tests := api.manager.ListTests()
	for _, test := range tests {
		if test.ID == testID {
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(test)
			return
		}
	}

	http.Error(w, "Test not found", http.StatusNotFound)
}

// updateTest updates a test
func (api *CertificationAPI) updateTest(w http.ResponseWriter, r *http.Request) {
	testID := r.URL.Path[len("/api/v1/certification/tests/"):]
	if testID == "" {
		http.Error(w, "Test ID required", http.StatusBadRequest)
		return
	}

	var updates map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&updates); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// In a real implementation, would update the test
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "updated"})
}

// deleteTest deletes a test
func (api *CertificationAPI) deleteTest(w http.ResponseWriter, r *http.Request) {
	testID := r.URL.Path[len("/api/v1/certification/tests/"):]
	if testID == "" {
		http.Error(w, "Test ID required", http.StatusBadRequest)
		return
	}

	// In a real implementation, would delete the test
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "deleted"})
}

// getStandards returns all standards
func (api *CertificationAPI) getStandards(w http.ResponseWriter, r *http.Request) {
	standards := api.manager.ListStandards()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(standards)
}

// createStandard creates a new standard
func (api *CertificationAPI) createStandard(w http.ResponseWriter, r *http.Request) {
	var standard CertificationStandard
	if err := json.NewDecoder(r.Body).Decode(&standard); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.manager.RegisterStandard(&standard); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(standard)
}

// Helper function to extract query parameters
func (api *CertificationAPI) getQueryParam(r *http.Request, key string, defaultValue string) string {
	if value := r.URL.Query().Get(key); value != "" {
		return value
	}
	return defaultValue
}

// Helper function to parse integer query parameters
func (api *CertificationAPI) getIntQueryParam(r *http.Request, key string, defaultValue int) int {
	if value := r.URL.Query().Get(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return defaultValue
}

// Helper function to parse boolean query parameters
func (api *CertificationAPI) getBoolQueryParam(r *http.Request, key string, defaultValue bool) bool {
	if value := r.URL.Query().Get(key); value != "" {
		if boolValue, err := strconv.ParseBool(value); err == nil {
			return boolValue
		}
	}
	return defaultValue
}
