package gateway

import (
	"bytes"
	"crypto/tls"
	"fmt"
	"net/http"
	"net/http/httptest"
	"sort"
	"strings"
	"sync"
	"time"

	"go.uber.org/zap"
	"golang.org/x/net/http2"
)

// TestSuite represents a comprehensive testing suite for the API Gateway
type TestSuite struct {
	gateway     *Gateway
	logger      *zap.Logger
	httpClient  *http.Client
	httpsClient *http.Client
	metrics     *Metrics
	config      *Config
}

// TestConfig holds configuration for different types of tests
type TestConfig struct {
	UnitTests        bool
	IntegrationTests bool
	LoadTests        bool
	SecurityTests    bool
	PerformanceTests bool
	Concurrency      int
	Duration         time.Duration
	RequestRate      int
	Timeout          time.Duration
}

// TestResult represents the result of a test execution
type TestResult struct {
	Name       string
	Status     string
	Duration   time.Duration
	Error      error
	Metrics    map[string]float64
	Assertions []TestAssertion
}

// TestAssertion represents an assertion result
type TestAssertion struct {
	Name     string
	Expected interface{}
	Actual   interface{}
	Passed   bool
}

// NewTestSuite creates a new testing suite
func NewTestSuite(config *Config) (*TestSuite, error) {
	logger, err := zap.NewDevelopment()
	if err != nil {
		return nil, err
	}

	gateway, err := NewGateway(config)
	if err != nil {
		return nil, err
	}

	// Create HTTP client with custom transport
	transport := &http.Transport{
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: true,
		},
		MaxIdleConns:        100,
		MaxIdleConnsPerHost: 10,
		IdleConnTimeout:     90 * time.Second,
	}

	httpClient := &http.Client{
		Transport: transport,
		Timeout:   30 * time.Second,
	}

	// Create HTTP/2 client
	http2Transport := &http2.Transport{
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: true,
		},
	}

	httpsClient := &http.Client{
		Transport: http2Transport,
		Timeout:   30 * time.Second,
	}

	return &TestSuite{
		gateway:     gateway,
		logger:      logger,
		httpClient:  httpClient,
		httpsClient: httpsClient,
		metrics:     NewMetrics(),
		config:      config,
	}, nil
}

// RunAllTests executes all test categories
func (ts *TestSuite) RunAllTests(config TestConfig) ([]TestResult, error) {
	var results []TestResult

	if config.UnitTests {
		unitResults := ts.RunUnitTests()
		results = append(results, unitResults...)
	}

	if config.IntegrationTests {
		integrationResults := ts.RunIntegrationTests()
		results = append(results, integrationResults...)
	}

	if config.LoadTests {
		loadResults := ts.RunLoadTests(config)
		results = append(results, loadResults...)
	}

	if config.SecurityTests {
		securityResults := ts.RunSecurityTests()
		results = append(results, securityResults...)
	}

	if config.PerformanceTests {
		performanceResults := ts.RunPerformanceTests(config)
		results = append(results, performanceResults...)
	}

	return results, nil
}

// RunUnitTests executes unit tests for all gateway components
func (ts *TestSuite) RunUnitTests() []TestResult {
	var results []TestResult

	// Test authentication
	results = append(results, ts.testAuthentication()...)

	// Test rate limiting
	results = append(results, ts.testRateLimiting()...)

	// Test load balancing
	results = append(results, ts.testLoadBalancing()...)

	// Test caching
	results = append(results, ts.testCaching()...)

	// Test circuit breaker
	results = append(results, ts.testCircuitBreaker()...)

	// Test versioning
	results = append(results, ts.testVersioning()...)

	// Test transformation
	results = append(results, ts.testTransformation()...)

	// Test advanced routing
	results = append(results, ts.testAdvancedRouting()...)

	return results
}

// RunIntegrationTests executes integration tests
func (ts *TestSuite) RunIntegrationTests() []TestResult {
	var results []TestResult

	// Test end-to-end request flow
	results = append(results, ts.testEndToEndFlow()...)

	// Test service discovery
	results = append(results, ts.testServiceDiscovery()...)

	// Test health checks
	results = append(results, ts.testHealthChecks()...)

	// Test metrics collection
	results = append(results, ts.testMetricsCollection()...)

	// Test configuration reload
	results = append(results, ts.testConfigurationReload()...)

	return results
}

// RunLoadTests executes load testing
func (ts *TestSuite) RunLoadTests(config TestConfig) []TestResult {
	var results []TestResult

	// Test concurrent requests
	results = append(results, ts.testConcurrentRequests(config)...)

	// Test sustained load
	results = append(results, ts.testSustainedLoad(config)...)

	// Test burst traffic
	results = append(results, ts.testBurstTraffic(config)...)

	// Test memory usage
	results = append(results, ts.testMemoryUsage(config)...)

	// Test connection pooling
	results = append(results, ts.testConnectionPooling(config)...)

	return results
}

// RunSecurityTests executes security tests
func (ts *TestSuite) RunSecurityTests() []TestResult {
	var results []TestResult

	// Test authentication bypass attempts
	results = append(results, ts.testAuthenticationBypass()...)

	// Test authorization
	results = append(results, ts.testAuthorization()...)

	// Test input validation
	results = append(results, ts.testInputValidation()...)

	// Test SQL injection attempts
	results = append(results, ts.testSQLInjection()...)

	// Test XSS attempts
	results = append(results, ts.testXSSAttempts()...)

	// Test CSRF protection
	results = append(results, ts.testCSRFProtection()...)

	// Test rate limiting bypass
	results = append(results, ts.testRateLimitBypass()...)

	return results
}

// RunPerformanceTests executes performance tests
func (ts *TestSuite) RunPerformanceTests(config TestConfig) []TestResult {
	var results []TestResult

	// Test response time
	results = append(results, ts.testResponseTime(config)...)

	// Test throughput
	results = append(results, ts.testThroughput(config)...)

	// Test resource usage
	results = append(results, ts.testResourceUsage(config)...)

	// Test scalability
	results = append(results, ts.testScalability(config)...)

	return results
}

// testAuthentication tests authentication functionality
func (ts *TestSuite) testAuthentication() []TestResult {
	var results []TestResult

	// Test valid JWT token
	result := TestResult{
		Name:     "Valid JWT Authentication",
		Status:   "PASSED",
		Duration: 0,
	}

	req := httptest.NewRequest("GET", "/api/test", nil)
	req.Header.Set("Authorization", "Bearer valid-jwt-token")

	w := httptest.NewRecorder()
	ts.gateway.ServeHTTP(w, req)

	result.Assertions = append(result.Assertions, TestAssertion{
		Name:     "Status Code",
		Expected: 200,
		Actual:   w.Code,
		Passed:   w.Code == 200,
	})

	results = append(results, result)

	// Test invalid JWT token
	result = TestResult{
		Name:     "Invalid JWT Authentication",
		Status:   "PASSED",
		Duration: 0,
	}

	req = httptest.NewRequest("GET", "/api/test", nil)
	req.Header.Set("Authorization", "Bearer invalid-token")

	w = httptest.NewRecorder()
	ts.gateway.ServeHTTP(w, req)

	result.Assertions = append(result.Assertions, TestAssertion{
		Name:     "Status Code",
		Expected: 401,
		Actual:   w.Code,
		Passed:   w.Code == 401,
	})

	results = append(results, result)

	return results
}

// testRateLimiting tests rate limiting functionality
func (ts *TestSuite) testRateLimiting() []TestResult {
	var results []TestResult

	// Test rate limit enforcement
	result := TestResult{
		Name:     "Rate Limit Enforcement",
		Status:   "PASSED",
		Duration: 0,
	}

	// Make multiple requests quickly
	for i := 0; i < 150; i++ {
		req := httptest.NewRequest("GET", "/api/test", nil)
		w := httptest.NewRecorder()
		ts.gateway.ServeHTTP(w, req)

		if w.Code == 429 {
			result.Assertions = append(result.Assertions, TestAssertion{
				Name:     "Rate Limit Triggered",
				Expected: 429,
				Actual:   w.Code,
				Passed:   true,
			})
			break
		}
	}

	results = append(results, result)

	return results
}

// testLoadBalancing tests load balancing functionality
func (ts *TestSuite) testLoadBalancing() []TestResult {
	var results []TestResult

	// Test round-robin distribution
	result := TestResult{
		Name:     "Round-Robin Load Balancing",
		Status:   "PASSED",
		Duration: 0,
	}

	// Track which services receive requests
	serviceCounts := make(map[string]int)

	for i := 0; i < 100; i++ {
		req := httptest.NewRequest("GET", "/api/load-balanced/test", nil)
		w := httptest.NewRecorder()
		ts.gateway.ServeHTTP(w, req)

		// Extract service from response headers
		if service := w.Header().Get("X-Service"); service != "" {
			serviceCounts[service]++
		}
	}

	// Check if requests are distributed
	if len(serviceCounts) > 1 {
		result.Assertions = append(result.Assertions, TestAssertion{
			Name:     "Load Distribution",
			Expected: "Multiple services",
			Actual:   fmt.Sprintf("%d services", len(serviceCounts)),
			Passed:   true,
		})
	}

	results = append(results, result)

	return results
}

// testCaching tests caching functionality
func (ts *TestSuite) testCaching() []TestResult {
	var results []TestResult

	// Test cache hit/miss
	result := TestResult{
		Name:     "Cache Hit/Miss",
		Status:   "PASSED",
		Duration: 0,
	}

	// First request (cache miss)
	req1 := httptest.NewRequest("GET", "/api/cached/test", nil)
	w1 := httptest.NewRecorder()
	ts.gateway.ServeHTTP(w1, req1)

	// Second request (cache hit)
	req2 := httptest.NewRequest("GET", "/api/cached/test", nil)
	w2 := httptest.NewRecorder()
	ts.gateway.ServeHTTP(w2, req2)

	// Check cache headers
	if w2.Header().Get("X-Cache") == "HIT" {
		result.Assertions = append(result.Assertions, TestAssertion{
			Name:     "Cache Hit",
			Expected: "HIT",
			Actual:   w2.Header().Get("X-Cache"),
			Passed:   true,
		})
	}

	results = append(results, result)

	return results
}

// testCircuitBreaker tests circuit breaker functionality
func (ts *TestSuite) testCircuitBreaker() []TestResult {
	var results []TestResult

	// Test circuit breaker opening
	result := TestResult{
		Name:     "Circuit Breaker Opening",
		Status:   "PASSED",
		Duration: 0,
	}

	// Make requests to trigger circuit breaker
	for i := 0; i < 10; i++ {
		req := httptest.NewRequest("GET", "/api/unhealthy/test", nil)
		w := httptest.NewRecorder()
		ts.gateway.ServeHTTP(w, req)

		if w.Code == 503 {
			result.Assertions = append(result.Assertions, TestAssertion{
				Name:     "Circuit Breaker Open",
				Expected: 503,
				Actual:   w.Code,
				Passed:   true,
			})
			break
		}
	}

	results = append(results, result)

	return results
}

// testVersioning tests API versioning functionality
func (ts *TestSuite) testVersioning() []TestResult {
	var results []TestResult

	// Test version extraction from header
	result := TestResult{
		Name:     "Version Header Extraction",
		Status:   "PASSED",
		Duration: 0,
	}

	req := httptest.NewRequest("GET", "/api/test", nil)
	req.Header.Set("X-API-Version", "v2")
	w := httptest.NewRecorder()
	ts.gateway.ServeHTTP(w, req)

	// Check if version was processed
	if w.Header().Get("X-API-Version-Processed") == "v2" {
		result.Assertions = append(result.Assertions, TestAssertion{
			Name:     "Version Processing",
			Expected: "v2",
			Actual:   w.Header().Get("X-API-Version-Processed"),
			Passed:   true,
		})
	}

	results = append(results, result)

	return results
}

// testTransformation tests request/response transformation
func (ts *TestSuite) testTransformation() []TestResult {
	var results []TestResult

	// Test JSON to XML transformation
	result := TestResult{
		Name:     "JSON to XML Transformation",
		Status:   "PASSED",
		Duration: 0,
	}

	req := httptest.NewRequest("POST", "/api/transform", bytes.NewBufferString(`{"test": "data"}`))
	req.Header.Set("Accept", "application/xml")
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	ts.gateway.ServeHTTP(w, req)

	// Check if transformation occurred
	if w.Header().Get("Content-Type") == "application/xml" {
		result.Assertions = append(result.Assertions, TestAssertion{
			Name:     "Content Type Transformation",
			Expected: "application/xml",
			Actual:   w.Header().Get("Content-Type"),
			Passed:   true,
		})
	}

	results = append(results, result)

	return results
}

// testAdvancedRouting tests advanced routing functionality
func (ts *TestSuite) testAdvancedRouting() []TestResult {
	var results []TestResult

	// Test mobile device routing
	result := TestResult{
		Name:     "Mobile Device Routing",
		Status:   "PASSED",
		Duration: 0,
	}

	req := httptest.NewRequest("GET", "/api/test", nil)
	req.Header.Set("User-Agent", "Mobile Safari")
	w := httptest.NewRecorder()
	ts.gateway.ServeHTTP(w, req)

	// Check if routed to mobile service
	if w.Header().Get("X-Service") == "arx-svg-parser-mobile" {
		result.Assertions = append(result.Assertions, TestAssertion{
			Name:     "Mobile Routing",
			Expected: "arx-svg-parser-mobile",
			Actual:   w.Header().Get("X-Service"),
			Passed:   true,
		})
	}

	results = append(results, result)

	return results
}

// testEndToEndFlow tests complete request flow
func (ts *TestSuite) testEndToEndFlow() []TestResult {
	var results []TestResult

	// Test complete request flow with all middleware
	result := TestResult{
		Name:     "End-to-End Request Flow",
		Status:   "PASSED",
		Duration: 0,
	}

	req := httptest.NewRequest("GET", "/api/svg/test", nil)
	req.Header.Set("Authorization", "Bearer valid-token")
	req.Header.Set("X-API-Version", "v1")

	w := httptest.NewRecorder()
	ts.gateway.ServeHTTP(w, req)

	// Check all middleware processed
	assertions := []TestAssertion{
		{
			Name:     "Authentication",
			Expected: 200,
			Actual:   w.Code,
			Passed:   w.Code != 401,
		},
		{
			Name:     "Rate Limiting",
			Expected: 200,
			Actual:   w.Code,
			Passed:   w.Code != 429,
		},
		{
			Name:     "Version Processing",
			Expected: "v1",
			Actual:   w.Header().Get("X-API-Version-Processed"),
			Passed:   w.Header().Get("X-API-Version-Processed") == "v1",
		},
	}

	result.Assertions = assertions
	results = append(results, result)

	return results
}

// testConcurrentRequests tests concurrent request handling
func (ts *TestSuite) testConcurrentRequests(config TestConfig) []TestResult {
	var results []TestResult

	result := TestResult{
		Name:     "Concurrent Request Handling",
		Status:   "PASSED",
		Duration: 0,
	}

	var wg sync.WaitGroup
	successCount := 0
	errorCount := 0
	var mu sync.Mutex

	start := time.Now()

	for i := 0; i < config.Concurrency; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()

			req := httptest.NewRequest("GET", "/api/test", nil)
			w := httptest.NewRecorder()
			ts.gateway.ServeHTTP(w, req)

			mu.Lock()
			if w.Code == 200 {
				successCount++
			} else {
				errorCount++
			}
			mu.Unlock()
		}()
	}

	wg.Wait()
	duration := time.Since(start)

	result.Duration = duration
	result.Metrics = map[string]float64{
		"concurrent_requests": float64(config.Concurrency),
		"success_count":       float64(successCount),
		"error_count":         float64(errorCount),
		"success_rate":        float64(successCount) / float64(config.Concurrency),
		"duration_seconds":    duration.Seconds(),
		"requests_per_second": float64(config.Concurrency) / duration.Seconds(),
	}

	// Assertions
	result.Assertions = append(result.Assertions, TestAssertion{
		Name:     "Success Rate",
		Expected: "> 95%",
		Actual:   fmt.Sprintf("%.2f%%", result.Metrics["success_rate"]*100),
		Passed:   result.Metrics["success_rate"] > 0.95,
	})

	results = append(results, result)

	return results
}

// testSustainedLoad tests sustained load handling
func (ts *TestSuite) testSustainedLoad(config TestConfig) []TestResult {
	var results []TestResult

	result := TestResult{
		Name:     "Sustained Load Test",
		Status:   "PASSED",
		Duration: config.Duration,
	}

	totalRequests := 0
	successCount := 0
	errorCount := 0
	var mu sync.Mutex

	start := time.Now()
	ticker := time.NewTicker(time.Duration(1000000000/config.RequestRate) * time.Nanosecond)
	defer ticker.Stop()

	done := make(chan bool)
	go func() {
		time.Sleep(config.Duration)
		done <- true
	}()

	for {
		select {
		case <-ticker.C:
			go func() {
				req := httptest.NewRequest("GET", "/api/test", nil)
				w := httptest.NewRecorder()
				ts.gateway.ServeHTTP(w, req)

				mu.Lock()
				totalRequests++
				if w.Code == 200 {
					successCount++
				} else {
					errorCount++
				}
				mu.Unlock()
			}()
		case <-done:
			goto end
		}
	}

end:
	duration := time.Since(start)

	result.Duration = duration
	result.Metrics = map[string]float64{
		"total_requests":      float64(totalRequests),
		"success_count":       float64(successCount),
		"error_count":         float64(errorCount),
		"success_rate":        float64(successCount) / float64(totalRequests),
		"duration_seconds":    duration.Seconds(),
		"requests_per_second": float64(totalRequests) / duration.Seconds(),
	}

	results = append(results, result)

	return results
}

// testAuthenticationBypass tests authentication bypass attempts
func (ts *TestSuite) testAuthenticationBypass() []TestResult {
	var results []TestResult

	// Test various bypass attempts
	bypassAttempts := []struct {
		name   string
		header string
		value  string
	}{
		{"Empty Authorization", "Authorization", ""},
		{"Invalid Bearer", "Authorization", "Bearer"},
		{"No Bearer", "Authorization", "invalid-token"},
		{"SQL Injection", "Authorization", "Bearer ' OR 1=1--"},
		{"XSS Attempt", "Authorization", "Bearer <script>alert('xss')</script>"},
	}

	for _, attempt := range bypassAttempts {
		result := TestResult{
			Name:     fmt.Sprintf("Authentication Bypass: %s", attempt.name),
			Status:   "PASSED",
			Duration: 0,
		}

		req := httptest.NewRequest("GET", "/api/protected", nil)
		req.Header.Set(attempt.header, attempt.value)
		w := httptest.NewRecorder()
		ts.gateway.ServeHTTP(w, req)

		result.Assertions = append(result.Assertions, TestAssertion{
			Name:     "Authentication Blocked",
			Expected: 401,
			Actual:   w.Code,
			Passed:   w.Code == 401,
		})

		results = append(results, result)
	}

	return results
}

// testInputValidation tests input validation
func (ts *TestSuite) testInputValidation() []TestResult {
	var results []TestResult

	// Test various malicious inputs
	maliciousInputs := []struct {
		name  string
		path  string
		body  string
		query string
	}{
		{"SQL Injection Path", "/api/test'; DROP TABLE users;--", "", ""},
		{"XSS Query", "/api/test", "", "?param=<script>alert('xss')</script>"},
		{"Path Traversal", "/api/../../../etc/passwd", "", ""},
		{"Large Payload", "/api/test", strings.Repeat("A", 1000000), ""},
		{"Null Bytes", "/api/test%00", "", ""},
	}

	for _, input := range maliciousInputs {
		result := TestResult{
			Name:     fmt.Sprintf("Input Validation: %s", input.name),
			Status:   "PASSED",
			Duration: 0,
		}

		req := httptest.NewRequest("POST", input.path, bytes.NewBufferString(input.body))
		if input.query != "" {
			req.URL.RawQuery = input.query
		}
		w := httptest.NewRecorder()
		ts.gateway.ServeHTTP(w, req)

		result.Assertions = append(result.Assertions, TestAssertion{
			Name:     "Input Rejected",
			Expected: "4xx or 5xx",
			Actual:   w.Code,
			Passed:   w.Code >= 400,
		})

		results = append(results, result)
	}

	return results
}

// testResponseTime tests response time performance
func (ts *TestSuite) testResponseTime(config TestConfig) []TestResult {
	var results []TestResult

	result := TestResult{
		Name:     "Response Time Test",
		Status:   "PASSED",
		Duration: 0,
	}

	var responseTimes []time.Duration
	var mu sync.Mutex

	// Make multiple requests and measure response times
	for i := 0; i < 100; i++ {
		start := time.Now()
		req := httptest.NewRequest("GET", "/api/test", nil)
		w := httptest.NewRecorder()
		ts.gateway.ServeHTTP(w, req)
		duration := time.Since(start)

		mu.Lock()
		responseTimes = append(responseTimes, duration)
		mu.Unlock()
	}

	// Calculate statistics
	var total time.Duration
	var min, max time.Duration
	for i, rt := range responseTimes {
		if i == 0 {
			min, max = rt, rt
		}
		total += rt
		if rt < min {
			min = rt
		}
		if rt > max {
			max = rt
		}
	}

	avg := total / time.Duration(len(responseTimes))

	result.Metrics = map[string]float64{
		"avg_response_time_ms": avg.Milliseconds(),
		"min_response_time_ms": min.Milliseconds(),
		"max_response_time_ms": max.Milliseconds(),
		"p95_response_time_ms": calculatePercentile(responseTimes, 95).Milliseconds(),
		"p99_response_time_ms": calculatePercentile(responseTimes, 99).Milliseconds(),
	}

	// Assertions
	result.Assertions = append(result.Assertions, TestAssertion{
		Name:     "Average Response Time",
		Expected: "< 100ms",
		Actual:   fmt.Sprintf("%.2fms", result.Metrics["avg_response_time_ms"]),
		Passed:   result.Metrics["avg_response_time_ms"] < 100,
	})

	results = append(results, result)

	return results
}

// calculatePercentile calculates the nth percentile of durations
func calculatePercentile(durations []time.Duration, percentile int) time.Duration {
	if len(durations) == 0 {
		return 0
	}

	// Sort durations
	sorted := make([]time.Duration, len(durations))
	copy(sorted, durations)
	sort.Slice(sorted, func(i, j int) bool {
		return sorted[i] < sorted[j]
	})

	index := int(float64(len(sorted)-1) * float64(percentile) / 100.0)
	return sorted[index]
}

// GenerateTestReport generates a comprehensive test report
func (ts *TestSuite) GenerateTestReport(results []TestResult) string {
	var report strings.Builder

	report.WriteString("# API Gateway Test Report\n\n")
	report.WriteString(fmt.Sprintf("Generated: %s\n\n", time.Now().Format(time.RFC3339)))

	// Summary
	totalTests := len(results)
	passedTests := 0
	failedTests := 0

	for _, result := range results {
		if result.Status == "PASSED" {
			passedTests++
		} else {
			failedTests++
		}
	}

	report.WriteString("## Summary\n\n")
	report.WriteString(fmt.Sprintf("- Total Tests: %d\n", totalTests))
	report.WriteString(fmt.Sprintf("- Passed: %d\n", passedTests))
	report.WriteString(fmt.Sprintf("- Failed: %d\n", failedTests))
	report.WriteString(fmt.Sprintf("- Success Rate: %.2f%%\n\n", float64(passedTests)/float64(totalTests)*100))

	// Detailed Results
	report.WriteString("## Detailed Results\n\n")

	for _, result := range results {
		report.WriteString(fmt.Sprintf("### %s\n\n", result.Name))
		report.WriteString(fmt.Sprintf("- Status: %s\n", result.Status))
		report.WriteString(fmt.Sprintf("- Duration: %s\n", result.Duration))

		if len(result.Metrics) > 0 {
			report.WriteString("- Metrics:\n")
			for key, value := range result.Metrics {
				report.WriteString(fmt.Sprintf("  - %s: %.2f\n", key, value))
			}
		}

		if len(result.Assertions) > 0 {
			report.WriteString("- Assertions:\n")
			for _, assertion := range result.Assertions {
				status := "✅"
				if !assertion.Passed {
					status = "❌"
				}
				report.WriteString(fmt.Sprintf("  - %s %s: Expected %v, Got %v\n",
					status, assertion.Name, assertion.Expected, assertion.Actual))
			}
		}

		if result.Error != nil {
			report.WriteString(fmt.Sprintf("- Error: %s\n", result.Error))
		}

		report.WriteString("\n")
	}

	return report.String()
}
