package certification

import (
	"context"
	"fmt"
	"testing"
	"time"
)

func TestCertificationManager(t *testing.T) {
	manager := NewCertificationManager()

	// Test registering a test
	test := &CertificationTest{
		ID:          "test_001",
		Name:        "Test 1",
		Description: "Test Description",
		Category:    TestCategorySafety,
		Standard:    "IEC 61010-1",
		Version:     "1.0",
	}

	err := manager.RegisterTest(test)
	if err != nil {
		t.Fatalf("Failed to register test: %v", err)
	}

	// Test registering a standard
	standard := &CertificationStandard{
		ID:           "standard_001",
		Name:         "Test Standard",
		Version:      "1.0",
		Description:  "Test Standard Description",
		Requirements: []string{"test_001"},
		Tests:        []string{"test_001"},
	}

	err = manager.RegisterStandard(standard)
	if err != nil {
		t.Fatalf("Failed to register standard: %v", err)
	}

	// Test running a test
	result, err := manager.RunTest(context.Background(), "device_001", "test_001")
	if err != nil {
		t.Fatalf("Failed to run test: %v", err)
	}

	if result.Status != TestStatusPassed {
		t.Errorf("Expected test status to be passed, got %s", result.Status)
	}

	if result.Score < 80.0 {
		t.Errorf("Expected test score to be >= 80.0, got %.2f", result.Score)
	}

	// Test getting device certification
	results, err := manager.GetDeviceCertification("device_001")
	if err != nil {
		t.Fatalf("Failed to get device certification: %v", err)
	}

	if len(results) == 0 {
		t.Error("Expected at least one test result")
	}

	// Test checking if device is certified
	certified, err := manager.IsDeviceCertified("device_001")
	if err != nil {
		t.Fatalf("Failed to check device certification: %v", err)
	}

	if !certified {
		t.Error("Expected device to be certified")
	}
}

func TestTestRunner(t *testing.T) {
	manager := NewCertificationManager()
	runner := NewTestRunner(manager)

	// Test registering a custom executor
	executor := &MockTestExecutor{
		name:    "Mock Executor",
		version: "1.0.0",
	}

	err := runner.RegisterExecutor(TestCategorySafety, executor)
	if err != nil {
		t.Fatalf("Failed to register executor: %v", err)
	}

	// Test running a test
	execution, err := runner.RunTest(context.Background(), "device_001", "safety_basic", map[string]interface{}{})
	if err != nil {
		t.Fatalf("Failed to run test: %v", err)
	}

	if execution.DeviceID != "device_001" {
		t.Errorf("Expected device ID to be device_001, got %s", execution.DeviceID)
	}

	if execution.Status != TestExecutionStatusRunning {
		t.Errorf("Expected execution status to be running, got %s", execution.Status)
	}

	// Wait for test to complete
	time.Sleep(100 * time.Millisecond)

	// Get execution result
	execution, err = runner.GetExecution(execution.ID)
	if err != nil {
		t.Fatalf("Failed to get execution: %v", err)
	}

	if execution.Status != TestExecutionStatusCompleted {
		t.Errorf("Expected execution status to be completed, got %s", execution.Status)
	}
}

func TestReportGenerator(t *testing.T) {
	generator := NewReportGenerator()

	// Create some test results
	results := []*CertificationResult{
		{
			ID:       "result_001",
			DeviceID: "device_001",
			TestID:   "safety_basic",
			Status:   TestStatusPassed,
			Score:    85.0,
			Details: map[string]interface{}{
				"electrical_safety": 85.0,
				"fire_safety":       90.0,
			},
			Errors:   []string{},
			Warnings: []string{},
			Duration: 30 * time.Second,
			TestedAt: time.Now(),
		},
		{
			ID:       "result_002",
			DeviceID: "device_001",
			TestID:   "performance_basic",
			Status:   TestStatusPassed,
			Score:    92.0,
			Details: map[string]interface{}{
				"response_time": 15.0,
				"throughput":    1000.0,
			},
			Errors:   []string{},
			Warnings: []string{},
			Duration: 45 * time.Second,
			TestedAt: time.Now(),
		},
	}

	// Test generating JSON report
	jsonData, err := generator.GenerateJSONReport("device_001", results)
	if err != nil {
		t.Fatalf("Failed to generate JSON report: %v", err)
	}

	if len(jsonData) == 0 {
		t.Error("Expected JSON report to have content")
	}

	// Test generating HTML report
	htmlData, err := generator.GenerateHTMLReport("device_001", results)
	if err != nil {
		t.Fatalf("Failed to generate HTML report: %v", err)
	}

	if len(htmlData) == 0 {
		t.Error("Expected HTML report to have content")
	}

	// Test generating PDF report
	pdfData, err := generator.GeneratePDFReport("device_001", results)
	if err != nil {
		t.Fatalf("Failed to generate PDF report: %v", err)
	}

	if len(pdfData) == 0 {
		t.Error("Expected PDF report to have content")
	}
}

func TestSafetyTestExecutor(t *testing.T) {
	executor := NewSafetyTestExecutor()

	if executor.GetName() != "Safety Test Executor" {
		t.Errorf("Expected name to be 'Safety Test Executor', got %s", executor.GetName())
	}

	if executor.GetVersion() != "1.0.0" {
		t.Errorf("Expected version to be '1.0.0', got %s", executor.GetVersion())
	}

	capabilities := executor.GetCapabilities()
	if len(capabilities) == 0 {
		t.Error("Expected capabilities to be non-empty")
	}

	// Test executing a safety test
	test := &CertificationTest{
		ID:       "safety_test",
		Name:     "Safety Test",
		Category: TestCategorySafety,
	}

	result, err := executor.Execute(context.Background(), test, "device_001")
	if err != nil {
		t.Fatalf("Failed to execute safety test: %v", err)
	}

	if result.TestID != "safety_test" {
		t.Errorf("Expected test ID to be 'safety_test', got %s", result.TestID)
	}

	if result.DeviceID != "device_001" {
		t.Errorf("Expected device ID to be 'device_001', got %s", result.DeviceID)
	}

	if result.Score < 0 || result.Score > 100 {
		t.Errorf("Expected score to be between 0 and 100, got %.2f", result.Score)
	}
}

func TestPerformanceTestExecutor(t *testing.T) {
	executor := NewPerformanceTestExecutor()

	// Test executing a performance test
	test := &CertificationTest{
		ID:       "performance_test",
		Name:     "Performance Test",
		Category: TestCategoryPerformance,
	}

	result, err := executor.Execute(context.Background(), test, "device_001")
	if err != nil {
		t.Fatalf("Failed to execute performance test: %v", err)
	}

	if result.TestID != "performance_test" {
		t.Errorf("Expected test ID to be 'performance_test', got %s", result.TestID)
	}

	if result.Score < 0 || result.Score > 100 {
		t.Errorf("Expected score to be between 0 and 100, got %.2f", result.Score)
	}

	// Check that key metrics are present
	details := result.Details
	if _, exists := details["response_time"]; !exists {
		t.Error("Expected response_time in details")
	}
	if _, exists := details["throughput"]; !exists {
		t.Error("Expected throughput in details")
	}
	if _, exists := details["memory_usage"]; !exists {
		t.Error("Expected memory_usage in details")
	}
}

func TestCompatibilityTestExecutor(t *testing.T) {
	executor := NewCompatibilityTestExecutor()

	// Test executing a compatibility test
	test := &CertificationTest{
		ID:       "compatibility_test",
		Name:     "Compatibility Test",
		Category: TestCategoryCompatibility,
	}

	result, err := executor.Execute(context.Background(), test, "device_001")
	if err != nil {
		t.Fatalf("Failed to execute compatibility test: %v", err)
	}

	if result.TestID != "compatibility_test" {
		t.Errorf("Expected test ID to be 'compatibility_test', got %s", result.TestID)
	}

	if result.Score < 0 || result.Score > 100 {
		t.Errorf("Expected score to be between 0 and 100, got %.2f", result.Score)
	}
}

func TestSecurityTestExecutor(t *testing.T) {
	executor := NewSecurityTestExecutor()

	// Test executing a security test
	test := &CertificationTest{
		ID:       "security_test",
		Name:     "Security Test",
		Category: TestCategorySecurity,
	}

	result, err := executor.Execute(context.Background(), test, "device_001")
	if err != nil {
		t.Fatalf("Failed to execute security test: %v", err)
	}

	if result.TestID != "security_test" {
		t.Errorf("Expected test ID to be 'security_test', got %s", result.TestID)
	}

	if result.Score < 0 || result.Score > 100 {
		t.Errorf("Expected score to be between 0 and 100, got %.2f", result.Score)
	}
}

func TestReliabilityTestExecutor(t *testing.T) {
	executor := NewReliabilityTestExecutor()

	// Test executing a reliability test
	test := &CertificationTest{
		ID:       "reliability_test",
		Name:     "Reliability Test",
		Category: TestCategoryReliability,
	}

	result, err := executor.Execute(context.Background(), test, "device_001")
	if err != nil {
		t.Fatalf("Failed to execute reliability test: %v", err)
	}

	if result.TestID != "reliability_test" {
		t.Errorf("Expected test ID to be 'reliability_test', got %s", result.TestID)
	}

	if result.Score < 0 || result.Score > 100 {
		t.Errorf("Expected score to be between 0 and 100, got %.2f", result.Score)
	}
}

func TestInteroperabilityTestExecutor(t *testing.T) {
	executor := NewInteroperabilityTestExecutor()

	// Test executing an interoperability test
	test := &CertificationTest{
		ID:       "interop_test",
		Name:     "Interoperability Test",
		Category: TestCategoryInteroperability,
	}

	result, err := executor.Execute(context.Background(), test, "device_001")
	if err != nil {
		t.Fatalf("Failed to execute interoperability test: %v", err)
	}

	if result.TestID != "interop_test" {
		t.Errorf("Expected test ID to be 'interop_test', got %s", result.TestID)
	}

	if result.Score < 0 || result.Score > 100 {
		t.Errorf("Expected score to be between 0 and 100, got %.2f", result.Score)
	}
}

// MockTestExecutor is a mock test executor for testing
type MockTestExecutor struct {
	name         string
	version      string
	capabilities []string
}

func (m *MockTestExecutor) Execute(ctx context.Context, test *CertificationTest, deviceID string) (*TestResult, error) {
	// Simulate test execution
	time.Sleep(10 * time.Millisecond)

	return &TestResult{
		ID:        fmt.Sprintf("mock_%d", time.Now().UnixNano()),
		TestID:    test.ID,
		DeviceID:  deviceID,
		Status:    TestStatusPassed,
		Score:     85.0,
		MaxScore:  100.0,
		Details:   map[string]interface{}{"mock": true},
		Errors:    []string{},
		Warnings:  []string{},
		StartTime: time.Now(),
		EndTime:   time.Now().Add(10 * time.Millisecond),
		Duration:  10 * time.Millisecond,
		Measurements: []Measurement{
			{
				Name:      "mock_measurement",
				Value:     85.0,
				Unit:      "score",
				Timestamp: time.Now(),
			},
		},
	}, nil
}

func (m *MockTestExecutor) GetName() string {
	return m.name
}

func (m *MockTestExecutor) GetVersion() string {
	return m.version
}

func (m *MockTestExecutor) GetCapabilities() []string {
	return m.capabilities
}

func TestCertificationMetrics(t *testing.T) {
	manager := NewCertificationManager()

	// Run some tests to generate metrics
	_, err := manager.RunTest(context.Background(), "device_001", "safety_basic")
	if err != nil {
		t.Fatalf("Failed to run test: %v", err)
	}

	_, err = manager.RunTest(context.Background(), "device_002", "performance_basic")
	if err != nil {
		t.Fatalf("Failed to run test: %v", err)
	}

	// Get metrics
	metrics := manager.GetMetrics()

	if metrics.TotalTests == 0 {
		t.Error("Expected total tests to be greater than 0")
	}

	if metrics.PassedTests == 0 {
		t.Error("Expected passed tests to be greater than 0")
	}

	if metrics.AverageScore <= 0 {
		t.Error("Expected average score to be greater than 0")
	}
}

func TestTestExecutionStatus(t *testing.T) {
	// Test status transitions
	statuses := []TestExecutionStatus{
		TestExecutionStatusPending,
		TestExecutionStatusRunning,
		TestExecutionStatusCompleted,
		TestExecutionStatusFailed,
		TestExecutionStatusCancelled,
		TestExecutionStatusTimeout,
	}

	for _, status := range statuses {
		if status == "" {
			t.Error("Expected status to be non-empty")
		}
	}
}

func TestTestLogLevels(t *testing.T) {
	// Test log levels
	levels := []LogLevel{
		LogLevelDebug,
		LogLevelInfo,
		LogLevelWarning,
		LogLevelError,
		LogLevelFatal,
	}

	for _, level := range levels {
		if level == "" {
			t.Error("Expected log level to be non-empty")
		}
	}
}

func TestCertificationLevels(t *testing.T) {
	// Test certification level determination
	generator := NewReportGenerator()

	// Test high score
	highScore := 95.0
	summary := ReportSummary{
		CriticalIssues: 0,
		Warnings:       1,
	}
	level := generator.determineCertificationLevel(highScore, summary)
	if level != "Platinum" {
		t.Errorf("Expected Platinum level for score %.2f, got %s", highScore, level)
	}

	// Test medium score
	mediumScore := 85.0
	summary.CriticalIssues = 0
	summary.Warnings = 3
	level = generator.determineCertificationLevel(mediumScore, summary)
	if level != "Gold" {
		t.Errorf("Expected Gold level for score %.2f, got %s", mediumScore, level)
	}

	// Test low score
	lowScore := 60.0
	summary.CriticalIssues = 2
	summary.Warnings = 10
	level = generator.determineCertificationLevel(lowScore, summary)
	if level != "Not Certified" {
		t.Errorf("Expected Not Certified level for score %.2f, got %s", lowScore, level)
	}
}
