package certification

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// TestRunner executes certification tests on hardware devices
type TestRunner struct {
	manager   *CertificationManager
	executors map[TestCategory]TestExecutor
	results   map[string]*TestExecution
	mu        sync.RWMutex
	metrics   *TestRunnerMetrics
}

// TestExecutor defines the interface for executing specific test categories
type TestExecutor interface {
	Execute(ctx context.Context, test *CertificationTest, deviceID string) (*TestResult, error)
	GetName() string
	GetVersion() string
	GetCapabilities() []string
}

// TestExecution represents a test execution session
type TestExecution struct {
	ID          string                 `json:"id"`
	DeviceID    string                 `json:"device_id"`
	TestID      string                 `json:"test_id"`
	Status      TestExecutionStatus    `json:"status"`
	StartTime   time.Time              `json:"start_time"`
	EndTime     *time.Time             `json:"end_time,omitempty"`
	Duration    time.Duration          `json:"duration"`
	Results     []*TestResult          `json:"results"`
	Logs        []TestLog              `json:"logs"`
	Config      map[string]interface{} `json:"config"`
	Environment TestEnvironment        `json:"environment"`
}

// TestExecutionStatus represents the status of a test execution
type TestExecutionStatus string

const (
	TestExecutionStatusPending   TestExecutionStatus = "pending"
	TestExecutionStatusRunning   TestExecutionStatus = "running"
	TestExecutionStatusCompleted TestExecutionStatus = "completed"
	TestExecutionStatusFailed    TestExecutionStatus = "failed"
	TestExecutionStatusCancelled TestExecutionStatus = "cancelled"
	TestExecutionStatusTimeout   TestExecutionStatus = "timeout"
)

// TestResult represents the result of a single test execution
type TestResult struct {
	ID           string                 `json:"id"`
	TestID       string                 `json:"test_id"`
	DeviceID     string                 `json:"device_id"`
	Status       TestStatus             `json:"status"`
	Score        float64                `json:"score"`
	MaxScore     float64                `json:"max_score"`
	Details      map[string]interface{} `json:"details"`
	Errors       []string               `json:"errors"`
	Warnings     []string               `json:"warnings"`
	StartTime    time.Time              `json:"start_time"`
	EndTime      time.Time              `json:"end_time"`
	Duration     time.Duration          `json:"duration"`
	Measurements []Measurement          `json:"measurements"`
}

// TestLog represents a log entry during test execution
type TestLog struct {
	Timestamp time.Time              `json:"timestamp"`
	Level     LogLevel               `json:"level"`
	Message   string                 `json:"message"`
	Category  string                 `json:"category"`
	Data      map[string]interface{} `json:"data,omitempty"`
}

// LogLevel represents the severity level of a log entry
type LogLevel string

const (
	LogLevelDebug   LogLevel = "debug"
	LogLevelInfo    LogLevel = "info"
	LogLevelWarning LogLevel = "warning"
	LogLevelError   LogLevel = "error"
	LogLevelFatal   LogLevel = "fatal"
)

// TestEnvironment represents the test environment configuration
type TestEnvironment struct {
	Temperature    float64   `json:"temperature"`
	Humidity       float64   `json:"humidity"`
	Pressure       float64   `json:"pressure"`
	Voltage        float64   `json:"voltage"`
	Current        float64   `json:"current"`
	SignalStrength int       `json:"signal_strength"`
	NetworkLatency int       `json:"network_latency"`
	Timestamp      time.Time `json:"timestamp"`
}

// Measurement represents a measurement taken during testing
type Measurement struct {
	Name      string                 `json:"name"`
	Value     float64                `json:"value"`
	Unit      string                 `json:"unit"`
	Timestamp time.Time              `json:"timestamp"`
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
}

// TestRunnerMetrics tracks test runner performance
type TestRunnerMetrics struct {
	TotalExecutions     int64         `json:"total_executions"`
	CompletedExecutions int64         `json:"completed_executions"`
	FailedExecutions    int64         `json:"failed_executions"`
	TimeoutExecutions   int64         `json:"timeout_executions"`
	AverageDuration     time.Duration `json:"average_duration"`
	TotalTestsRun       int64         `json:"total_tests_run"`
	PassedTests         int64         `json:"passed_tests"`
	FailedTests         int64         `json:"failed_tests"`
}

// NewTestRunner creates a new test runner
func NewTestRunner(manager *CertificationManager) *TestRunner {
	tr := &TestRunner{
		manager:   manager,
		executors: make(map[TestCategory]TestExecutor),
		results:   make(map[string]*TestExecution),
		metrics:   &TestRunnerMetrics{},
	}

	// Register default executors
	tr.registerDefaultExecutors()
	return tr
}

// RegisterExecutor registers a test executor for a specific category
func (tr *TestRunner) RegisterExecutor(category TestCategory, executor TestExecutor) error {
	tr.mu.Lock()
	defer tr.mu.Unlock()

	tr.executors[category] = executor
	logger.Info("Test executor registered: %s for category %s", executor.GetName(), category)
	return nil
}

// RunTest executes a single test on a device
func (tr *TestRunner) RunTest(ctx context.Context, deviceID, testID string, config map[string]interface{}) (*TestExecution, error) {
	// Get test definition
	test, exists := tr.manager.tests[testID]
	if !exists {
		return nil, fmt.Errorf("test %s not found", testID)
	}

	// Create test execution
	execution := &TestExecution{
		ID:          fmt.Sprintf("exec_%d", time.Now().UnixNano()),
		DeviceID:    deviceID,
		TestID:      testID,
		Status:      TestExecutionStatusPending,
		StartTime:   time.Now(),
		Config:      config,
		Environment: tr.getTestEnvironment(),
		Results:     make([]*TestResult, 0),
		Logs:        make([]TestLog, 0),
	}

	// Store execution
	tr.mu.Lock()
	tr.results[execution.ID] = execution
	tr.mu.Unlock()

	// Execute test asynchronously
	go tr.executeTest(ctx, execution, test)

	return execution, nil
}

// RunTestSuite executes multiple tests on a device
func (tr *TestRunner) RunTestSuite(ctx context.Context, deviceID string, testIDs []string, config map[string]interface{}) (*TestExecution, error) {
	// Create test suite execution
	execution := &TestExecution{
		ID:          fmt.Sprintf("suite_%d", time.Now().UnixNano()),
		DeviceID:    deviceID,
		TestID:      "test_suite",
		Status:      TestExecutionStatusPending,
		StartTime:   time.Now(),
		Config:      config,
		Environment: tr.getTestEnvironment(),
		Results:     make([]*TestResult, 0),
		Logs:        make([]TestLog, 0),
	}

	// Store execution
	tr.mu.Lock()
	tr.results[execution.ID] = execution
	tr.mu.Unlock()

	// Execute test suite asynchronously
	go tr.executeTestSuite(ctx, execution, testIDs)

	return execution, nil
}

// GetExecution retrieves a test execution by ID
func (tr *TestRunner) GetExecution(executionID string) (*TestExecution, error) {
	tr.mu.RLock()
	defer tr.mu.RUnlock()

	execution, exists := tr.results[executionID]
	if !exists {
		return nil, fmt.Errorf("execution %s not found", executionID)
	}
	return execution, nil
}

// CancelExecution cancels a running test execution
func (tr *TestRunner) CancelExecution(executionID string) error {
	tr.mu.Lock()
	defer tr.mu.Unlock()

	execution, exists := tr.results[executionID]
	if !exists {
		return fmt.Errorf("execution %s not found", executionID)
	}

	if execution.Status == TestExecutionStatusRunning {
		execution.Status = TestExecutionStatusCancelled
		now := time.Now()
		execution.EndTime = &now
		execution.Duration = now.Sub(execution.StartTime)
		tr.addLog(execution, LogLevelInfo, "Test execution cancelled by user", "system", nil)
	}

	return nil
}

// GetMetrics returns test runner metrics
func (tr *TestRunner) GetMetrics() *TestRunnerMetrics {
	tr.mu.RLock()
	defer tr.mu.RUnlock()

	return tr.metrics
}

// executeTest executes a single test
func (tr *TestRunner) executeTest(ctx context.Context, execution *TestExecution, test *CertificationTest) {
	tr.mu.Lock()
	execution.Status = TestExecutionStatusRunning
	tr.mu.Unlock()

	tr.addLog(execution, LogLevelInfo, fmt.Sprintf("Starting test: %s", test.Name), "test", nil)

	// Get executor for test category
	executor, exists := tr.executors[test.Category]
	if !exists {
		tr.failExecution(execution, fmt.Errorf("no executor found for category %s", test.Category))
		return
	}

	// Execute test with timeout
	timeout := 30 * time.Minute // Default timeout
	if testTimeout, ok := test.Config["timeout"].(int); ok {
		timeout = time.Duration(testTimeout) * time.Minute
	}

	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	// Execute test
	result, err := executor.Execute(ctx, test, execution.DeviceID)
	if err != nil {
		tr.failExecution(execution, err)
		return
	}

	// Store result
	tr.mu.Lock()
	execution.Results = append(execution.Results, result)
	tr.mu.Unlock()

	// Complete execution
	tr.completeExecution(execution)
}

// executeTestSuite executes multiple tests
func (tr *TestRunner) executeTestSuite(ctx context.Context, execution *TestExecution, testIDs []string) {
	tr.mu.Lock()
	execution.Status = TestExecutionStatusRunning
	tr.mu.Unlock()

	tr.addLog(execution, LogLevelInfo, fmt.Sprintf("Starting test suite with %d tests", len(testIDs)), "suite", nil)

	allPassed := true
	for i, testID := range testIDs {
		tr.addLog(execution, LogLevelInfo, fmt.Sprintf("Running test %d/%d: %s", i+1, len(testIDs), testID), "suite", nil)

		test, exists := tr.manager.tests[testID]
		if !exists {
			tr.addLog(execution, LogLevelError, fmt.Sprintf("Test %s not found", testID), "suite", nil)
			allPassed = false
			continue
		}

		executor, exists := tr.executors[test.Category]
		if !exists {
			tr.addLog(execution, LogLevelError, fmt.Sprintf("No executor for category %s", test.Category), "suite", nil)
			allPassed = false
			continue
		}

		// Execute test
		result, err := executor.Execute(ctx, test, execution.DeviceID)
		if err != nil {
			tr.addLog(execution, LogLevelError, fmt.Sprintf("Test %s failed: %v", testID, err), "suite", nil)
			allPassed = false
		} else {
			tr.mu.Lock()
			execution.Results = append(execution.Results, result)
			tr.mu.Unlock()
		}
	}

	// Complete execution
	if allPassed {
		tr.completeExecution(execution)
	} else {
		tr.failExecution(execution, fmt.Errorf("one or more tests in suite failed"))
	}
}

// completeExecution marks an execution as completed
func (tr *TestRunner) completeExecution(execution *TestExecution) {
	tr.mu.Lock()
	defer tr.mu.Unlock()

	execution.Status = TestExecutionStatusCompleted
	now := time.Now()
	execution.EndTime = &now
	execution.Duration = now.Sub(execution.StartTime)

	tr.addLog(execution, LogLevelInfo, "Test execution completed successfully", "test", nil)

	// Update metrics
	tr.metrics.TotalExecutions++
	tr.metrics.CompletedExecutions++
	tr.updateAverageDuration(execution.Duration)

	// Update test results in manager
	for _, result := range execution.Results {
		tr.metrics.TotalTestsRun++
		if result.Status == TestStatusPassed {
			tr.metrics.PassedTests++
		} else {
			tr.metrics.FailedTests++
		}

		// Store result in manager
		tr.manager.results[result.ID] = &CertificationResult{
			ID:          result.ID,
			DeviceID:    result.DeviceID,
			TestID:      result.TestID,
			Status:      result.Status,
			Score:       result.Score,
			Details:     result.Details,
			Errors:      result.Errors,
			Warnings:    result.Warnings,
			Duration:    result.Duration,
			TestedAt:    result.StartTime,
			CertifiedAt: &result.EndTime,
		}
	}
}

// failExecution marks an execution as failed
func (tr *TestRunner) failExecution(execution *TestExecution, err error) {
	tr.mu.Lock()
	defer tr.mu.Unlock()

	execution.Status = TestExecutionStatusFailed
	now := time.Now()
	execution.EndTime = &now
	execution.Duration = now.Sub(execution.StartTime)

	tr.addLog(execution, LogLevelError, fmt.Sprintf("Test execution failed: %v", err), "test", nil)

	// Update metrics
	tr.metrics.TotalExecutions++
	tr.metrics.FailedExecutions++
	tr.updateAverageDuration(execution.Duration)
}

// addLog adds a log entry to an execution
func (tr *TestRunner) addLog(execution *TestExecution, level LogLevel, message, category string, data map[string]interface{}) {
	log := TestLog{
		Timestamp: time.Now(),
		Level:     level,
		Message:   message,
		Category:  category,
		Data:      data,
	}

	execution.Logs = append(execution.Logs, log)

	// Also log to system logger
	switch level {
	case LogLevelDebug:
		logger.Debug("[%s] %s: %s", category, execution.ID, message)
	case LogLevelInfo:
		logger.Info("[%s] %s: %s", category, execution.ID, message)
	case LogLevelWarning:
		logger.Warn("[%s] %s: %s", category, execution.ID, message)
	case LogLevelError:
		logger.Error("[%s] %s: %s", category, execution.ID, message)
	case LogLevelFatal:
		logger.Error("[%s] %s: %s", category, execution.ID, message)
	}
}

// getTestEnvironment returns the current test environment
func (tr *TestRunner) getTestEnvironment() TestEnvironment {
	// In a real implementation, this would read from actual sensors
	return TestEnvironment{
		Temperature:    22.0 + float64(time.Now().Unix()%100)/10.0,
		Humidity:       45.0 + float64(time.Now().Unix()%200)/10.0,
		Pressure:       1013.25 + float64(time.Now().Unix()%100)/10.0,
		Voltage:        3.3 + float64(time.Now().Unix()%20)/100.0,
		Current:        0.1 + float64(time.Now().Unix()%50)/1000.0,
		SignalStrength: -50 + int(time.Now().Unix()%50),
		NetworkLatency: 10 + int(time.Now().Unix()%50),
		Timestamp:      time.Now(),
	}
}

// updateAverageDuration updates the average execution duration
func (tr *TestRunner) updateAverageDuration(duration time.Duration) {
	if tr.metrics.TotalExecutions > 0 {
		totalDuration := tr.metrics.AverageDuration * time.Duration(tr.metrics.TotalExecutions-1)
		tr.metrics.AverageDuration = (totalDuration + duration) / time.Duration(tr.metrics.TotalExecutions)
	} else {
		tr.metrics.AverageDuration = duration
	}
}

// registerDefaultExecutors registers default test executors
func (tr *TestRunner) registerDefaultExecutors() {
	// Register safety test executor
	tr.RegisterExecutor(TestCategorySafety, NewSafetyTestExecutor())

	// Register performance test executor
	tr.RegisterExecutor(TestCategoryPerformance, NewPerformanceTestExecutor())

	// Register compatibility test executor
	tr.RegisterExecutor(TestCategoryCompatibility, NewCompatibilityTestExecutor())

	// Register security test executor
	tr.RegisterExecutor(TestCategorySecurity, NewSecurityTestExecutor())

	// Register reliability test executor
	tr.RegisterExecutor(TestCategoryReliability, NewReliabilityTestExecutor())

	// Register interoperability test executor
	tr.RegisterExecutor(TestCategoryInteroperability, NewInteroperabilityTestExecutor())
}
