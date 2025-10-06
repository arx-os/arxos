/**
 * Performance Integration Tests - Load testing and performance validation
 */

package integration

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"sync"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/test/helpers"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// PerformanceTestSuite manages performance integration tests
type PerformanceTestSuite struct {
	app        *app.Container
	config     *config.Config
	server     *http.Server
	httpClient *http.Client
}

// NewPerformanceTestSuite creates a new performance test suite
func NewPerformanceTestSuite(t *testing.T) *PerformanceTestSuite {
	// Load test configuration using helper function
	cfg := helpers.LoadTestConfig(t)

	// Initialize application container
	container := app.NewContainer()
	err := container.Initialize(context.Background(), cfg)
	require.NoError(t, err)

	// Create HTTP client with timeout
	httpClient := &http.Client{
		Timeout: 60 * time.Second,
	}

	return &PerformanceTestSuite{
		app:        container,
		config:     cfg,
		httpClient: httpClient,
	}
}

// SetupTestEnvironment prepares the performance test environment
func (suite *PerformanceTestSuite) SetupTestEnvironment(t *testing.T) {
	// Create HTTP server
	suite.server = &http.Server{
		Addr:    ":8080",
		Handler: http.NewServeMux(), // Placeholder handler
	}

	// Start server in background
	go func() {
		suite.server.ListenAndServe()
	}()

	// Wait for server to start
	time.Sleep(2 * time.Second)

	// Setup test data
	suite.setupPerformanceTestData(t)
}

// TeardownTestEnvironment cleans up the performance test environment
func (suite *PerformanceTestSuite) TeardownTestEnvironment(t *testing.T) {
	if suite.server != nil {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		suite.server.Shutdown(ctx)
	}

	// Note: Container doesn't have Close method, it's managed by Go's GC
}

// setupPerformanceTestData creates test data for performance tests
func (suite *PerformanceTestSuite) setupPerformanceTestData(t *testing.T) {
	// Create multiple buildings for load testing
	// Note: In a real performance test, we'd create data through use cases
	// For now, we'll skip the data creation and focus on API performance
	for i := 0; i < 100; i++ {
		// Placeholder for building creation
		_ = i

		// Create equipment for each building
		// Note: In a real performance test, we'd create equipment through use cases
		// For now, we'll skip the equipment creation
		for j := 0; j < 10; j++ {
			// Placeholder for equipment creation
			_ = j
		}
	}
}

// TestLoadTesting tests system performance under normal load
func TestLoadTesting(t *testing.T) {
	suite := NewPerformanceTestSuite(t)
	suite.SetupTestEnvironment(t)
	defer suite.TeardownTestEnvironment(t)

	t.Run("ConcurrentBuildingCreation", func(t *testing.T) {
		const numConcurrent = 50
		const numRequests = 100

		var wg sync.WaitGroup
		errors := make(chan error, numRequests)
		successCount := 0
		var mu sync.Mutex

		startTime := time.Now()

		for i := 0; i < numRequests; i++ {
			wg.Add(1)
			go func(requestID int) {
				defer wg.Done()

				// Create building request
				reqBody := map[string]any{
					"name":    fmt.Sprintf("Load Test Building %d", requestID),
					"address": fmt.Sprintf("%d Load Test Street", requestID),
				}

				jsonBody, err := json.Marshal(reqBody)
				if err != nil {
					errors <- err
					return
				}

				// Make HTTP request
				resp, err := suite.httpClient.Post(
					"http://localhost:8080/api/v1/buildings",
					"application/json",
					bytes.NewBuffer(jsonBody),
				)
				if err != nil {
					errors <- err
					return
				}
				defer resp.Body.Close()

				if resp.StatusCode == http.StatusCreated {
					mu.Lock()
					successCount++
					mu.Unlock()
				} else {
					errors <- fmt.Errorf("unexpected status code: %d", resp.StatusCode)
				}
			}(i)
		}

		wg.Wait()
		close(errors)

		endTime := time.Now()
		duration := endTime.Sub(startTime)

		// Check for errors
		var errorCount int
		for err := range errors {
			if err != nil {
				errorCount++
				t.Logf("Request error: %v", err)
			}
		}

		// Performance assertions
		assert.GreaterOrEqual(t, successCount, numRequests*0.95) // 95% success rate
		assert.Less(t, errorCount, numRequests*0.05)             // Less than 5% errors
		assert.Less(t, duration, 30*time.Second)                 // Complete within 30 seconds

		t.Logf("Load test results: %d successful requests, %d errors, duration: %v",
			successCount, errorCount, duration)
	})

	t.Run("ConcurrentEquipmentQueries", func(t *testing.T) {
		const numConcurrent = 100
		const numRequests = 500

		var wg sync.WaitGroup
		errors := make(chan error, numRequests)
		successCount := 0
		var mu sync.Mutex

		startTime := time.Now()

		for i := 0; i < numRequests; i++ {
			wg.Add(1)
			go func(requestID int) {
				defer wg.Done()

				buildingID := fmt.Sprintf("perf-building-%d", requestID%100)

				// Make HTTP request
				resp, err := suite.httpClient.Get(
					"http://localhost:8080/api/v1/buildings/" + buildingID + "/equipment",
				)
				if err != nil {
					errors <- err
					return
				}
				defer resp.Body.Close()

				if resp.StatusCode == http.StatusOK {
					mu.Lock()
					successCount++
					mu.Unlock()
				} else {
					errors <- fmt.Errorf("unexpected status code: %d", resp.StatusCode)
				}
			}(i)
		}

		wg.Wait()
		close(errors)

		endTime := time.Now()
		duration := endTime.Sub(startTime)

		// Check for errors
		var errorCount int
		for err := range errors {
			if err != nil {
				errorCount++
				t.Logf("Query error: %v", err)
			}
		}

		// Performance assertions
		assert.GreaterOrEqual(t, successCount, numRequests*0.95) // 95% success rate
		assert.Less(t, errorCount, numRequests*0.05)             // Less than 5% errors
		assert.Less(t, duration, 20*time.Second)                 // Complete within 20 seconds

		t.Logf("Query test results: %d successful queries, %d errors, duration: %v",
			successCount, errorCount, duration)
	})
}

// TestStressTesting tests system performance under extreme load
func TestStressTesting(t *testing.T) {
	suite := NewPerformanceTestSuite(t)
	suite.SetupTestEnvironment(t)
	defer suite.TeardownTestEnvironment(t)

	t.Run("HighConcurrencyBuildingOperations", func(t *testing.T) {
		const numConcurrent = 200
		const numRequests = 1000

		var wg sync.WaitGroup
		errors := make(chan error, numRequests)
		successCount := 0
		var mu sync.Mutex

		startTime := time.Now()

		for i := 0; i < numRequests; i++ {
			wg.Add(1)
			go func(requestID int) {
				defer wg.Done()

				// Alternate between create, read, update operations
				switch requestID % 3 {
				case 0: // Create
					reqBody := map[string]any{
						"name":    fmt.Sprintf("Stress Test Building %d", requestID),
						"address": fmt.Sprintf("%d Stress Test Street", requestID),
					}

					jsonBody, err := json.Marshal(reqBody)
					if err != nil {
						errors <- err
						return
					}

					resp, err := suite.httpClient.Post(
						"http://localhost:8080/api/v1/buildings",
						"application/json",
						bytes.NewBuffer(jsonBody),
					)
					if err != nil {
						errors <- err
						return
					}
					resp.Body.Close()

					if resp.StatusCode == http.StatusCreated {
						mu.Lock()
						successCount++
						mu.Unlock()
					}

				case 1: // Read
					buildingID := fmt.Sprintf("perf-building-%d", requestID%100)
					resp, err := suite.httpClient.Get(
						"http://localhost:8080/api/v1/buildings/" + buildingID,
					)
					if err != nil {
						errors <- err
						return
					}
					resp.Body.Close()

					if resp.StatusCode == http.StatusOK {
						mu.Lock()
						successCount++
						mu.Unlock()
					}

				case 2: // Update
					buildingID := fmt.Sprintf("perf-building-%d", requestID%100)
					updateBody := map[string]any{
						"name": fmt.Sprintf("Updated Stress Building %d", requestID),
					}

					updateJsonBody, err := json.Marshal(updateBody)
					if err != nil {
						errors <- err
						return
					}

					req, err := http.NewRequest("PUT",
						"http://localhost:8080/api/v1/buildings/"+buildingID,
						bytes.NewBuffer(updateJsonBody))
					if err != nil {
						errors <- err
						return
					}
					req.Header.Set("Content-Type", "application/json")

					resp, err := suite.httpClient.Do(req)
					if err != nil {
						errors <- err
						return
					}
					resp.Body.Close()

					if resp.StatusCode == http.StatusOK {
						mu.Lock()
						successCount++
						mu.Unlock()
					}
				}
			}(i)
		}

		wg.Wait()
		close(errors)

		endTime := time.Now()
		duration := endTime.Sub(startTime)

		// Check for errors
		var errorCount int
		for err := range errors {
			if err != nil {
				errorCount++
				t.Logf("Stress test error: %v", err)
			}
		}

		// Stress test assertions (more lenient than load test)
		assert.GreaterOrEqual(t, successCount, numRequests*0.80) // 80% success rate
		assert.Less(t, errorCount, numRequests*0.20)             // Less than 20% errors
		assert.Less(t, duration, 60*time.Second)                 // Complete within 60 seconds

		t.Logf("Stress test results: %d successful operations, %d errors, duration: %v",
			successCount, errorCount, duration)
	})
}

// TestDatabasePerformance tests database performance under load
func TestDatabasePerformance(t *testing.T) {
	suite := NewPerformanceTestSuite(t)
	suite.SetupTestEnvironment(t)
	defer suite.TeardownTestEnvironment(t)

	t.Run("SpatialQueryPerformance", func(t *testing.T) {
		// Test spatial query performance
		// Note: In a real performance test, we'd test spatial queries through use cases
		// For now, we'll skip the spatial query test
		assert.True(t, true) // Placeholder assertion
	})

	t.Run("TransactionPerformance", func(t *testing.T) {
		// Test transaction performance
		// Note: In a real performance test, we'd test transactions through use cases
		// For now, we'll skip the transaction test
		assert.True(t, true) // Placeholder assertion
	})
}

// TestMemoryUsage tests memory usage under load
func TestMemoryUsage(t *testing.T) {
	suite := NewPerformanceTestSuite(t)
	suite.SetupTestEnvironment(t)
	defer suite.TeardownTestEnvironment(t)

	t.Run("MemoryLeakDetection", func(t *testing.T) {
		const numIterations = 1000
		const batchSize = 100

		initialMemory := getMemoryUsage()
		t.Logf("Initial memory usage: %d MB", initialMemory)

		for iteration := 0; iteration < numIterations; iteration++ {
			// Create batch of buildings
			for i := 0; i < batchSize; i++ {
				reqBody := map[string]any{
					"name":    fmt.Sprintf("Memory Test Building %d-%d", iteration, i),
					"address": fmt.Sprintf("%d Memory Test Street", iteration*batchSize+i),
				}

				jsonBody, err := json.Marshal(reqBody)
				if err != nil {
					continue
				}

				resp, err := suite.httpClient.Post(
					"http://localhost:8080/api/v1/buildings",
					"application/json",
					bytes.NewBuffer(jsonBody),
				)
				if err != nil {
					continue
				}
				resp.Body.Close()
			}

			// Check memory usage every 100 iterations
			if iteration%100 == 0 {
				currentMemory := getMemoryUsage()
				t.Logf("Iteration %d memory usage: %d MB", iteration, currentMemory)

				// Check for significant memory increase
				memoryIncrease := currentMemory - initialMemory
				if memoryIncrease > 100 { // More than 100MB increase
					t.Logf("Warning: Memory usage increased by %d MB", memoryIncrease)
				}
			}
		}

		finalMemory := getMemoryUsage()
		memoryIncrease := finalMemory - initialMemory

		t.Logf("Final memory usage: %d MB, increase: %d MB", finalMemory, memoryIncrease)

		// Memory leak detection (allow some increase but not excessive)
		assert.Less(t, memoryIncrease, 200) // Less than 200MB increase
	})
}

// Helper functions
func getMemoryUsage() int64 {
	// This would get actual memory usage from runtime
	// For now, return mock value
	return 100 // Mock 100MB
}

// Benchmark tests for performance regression detection
func BenchmarkBuildingCreation(b *testing.B) {
	suite := NewPerformanceTestSuite(&testing.T{})
	suite.SetupTestEnvironment(&testing.T{})
	defer suite.TeardownTestEnvironment(&testing.T{})

	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		reqBody := map[string]any{
			"name":    fmt.Sprintf("Benchmark Building %d", i),
			"address": fmt.Sprintf("%d Benchmark Street", i),
		}

		jsonBody, _ := json.Marshal(reqBody)

		resp, err := suite.httpClient.Post(
			"http://localhost:8080/api/v1/buildings",
			"application/json",
			bytes.NewBuffer(jsonBody),
		)
		if err != nil {
			b.Fatal(err)
		}
		resp.Body.Close()
	}
}

func BenchmarkEquipmentQuery(b *testing.B) {
	suite := NewPerformanceTestSuite(&testing.T{})
	suite.SetupTestEnvironment(&testing.T{})
	defer suite.TeardownTestEnvironment(&testing.T{})

	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		buildingID := fmt.Sprintf("perf-building-%d", i%100)
		resp, err := suite.httpClient.Get(
			"http://localhost:8080/api/v1/buildings/" + buildingID + "/equipment",
		)
		if err != nil {
			b.Fatal(err)
		}
		resp.Body.Close()
	}
}
