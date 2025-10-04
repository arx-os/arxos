//go:build stress
// +build stress

package load

import (
	"context"
	"database/sql"
	"fmt"
	"math/rand"
	"os"
	"sync"
	"testing"
	"time"

	_ "github.com/lib/pq"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestLoad simulates high concurrent load for ArxOS database operations
func TestLoad(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping load tests in short mode")
	}

	// Load testing configuration
	config := LoadTestConfig{
		Duration:              5 * time.Minute,
		MaxWorkers:            50,
		RampUpDelay:           1 * time.Second,
		ThinkTime:             100 * time.Millisecond,
		FailureRateThreshold:  5.0,             // 5% max failure rate
		ResponseTimeThreshold: 2 * time.Second, // Max response time
	}

	t.Logf("Starting load test with %d workers for %v", config.MaxWorkers, config.Duration)

	// Get database connection from environment
	dbURL := getDatabaseURL()
	db, err := sql.Open("postgres", dbURL)
	require.NoError(t, err)
	defer db.Close()

	// Verify database connection
	require.NoError(t, db.Ping())

	// Initialize test data
	err = setupTestData(db)
	require.NoError(t, err)

	// Run load test
	results := runLoadTest(t, db, config)

	// Analyze results
	t.Logf("Load test completed:")
	t.Logf("  Total requests: %d", results.TotalRequests)
	t.Logf("  Successful requests: %d", results.SuccessfulRequests)
	t.Logf("  Failed requests: %d", results.FailedRequests)
	t.Logf("  Average response time: %v", results.AverageResponseTime)
	t.Logf("  95th percentile response time: %v", results.ResponseTime95th)
	t.Logf("  Failure rate: %.2f%%", results.FailureRate()*100)

	// Assert success criteria
	assert.LessOrEqual(t, results.FailureRate()*100, config.FailureRateThreshold,
		"Failure rate (%f%%) exceeds threshold (%f%%)",
		results.FailureRate()*100, config.FailureRateThreshold)

	assert.LessOrEqual(t, results.AverageResponseTime, config.ResponseTimeThreshold,
		"Average response time (%v) exceeds threshold (%v)",
		results.AverageResponseTime, config.ResponseTimeThreshold)

	assert.GreaterOrEqual(t, results.SuccessfulRequests, int64(config.MaxWorkers*10),
		"Successful requests (%d) below minimum threshold (%d)",
		results.SuccessfulRequests, config.MaxWorkers*10)
}

// LoadTestConfig holds load test configuration
type LoadTestConfig struct {
	Duration              time.Duration
	MaxWorkers            int
	RampUpDelay           time.Duration
	ThinkTime             time.Duration
	FailureRateThreshold  float64
	ResponseTimeThreshold time.Duration
}

// LoadTestResults holds load test results
type LoadTestResults struct {
	TotalRequests       int64
	SuccessfulRequests  int64
	FailedRequests      int64
	AverageResponseTime time.Duration
	ResponseTime95th    time.Duration
	StartTime           time.Time
	EndTime             time.Time
	mu                  sync.RWMutex
	responseTimes       []time.Duration
}

// runLoadTest executes the load test
func runLoadTest(t *testing.T, db *sql.DB, config LoadTestConfig) *LoadTestResults {
	results := &LoadTestResults{
		StartTime:     time.Now(),
		responseTimes: make([]time.Duration, 0, 1000),
	}

	ctx, cancel := context.WithTimeout(context.Background(), config.Duration)
	defer cancel()

	// Start workers
	var wg sync.WaitGroup
	workerCount := config.MaxWorkers

	for i := 0; i < workerCount; i++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			workerLoadTest(ctx, t, db, workerID, results, config)
		}(i)

		// Ramp up delay
		if config.RampUpDelay > 0 {
			time.Sleep(config.RampUpDelay / time.Duration(workerCount))
		}
	}

	// Wait for all workers to complete or timeout
	wg.Wait()

	results.EndTime = time.Now()
	results.computeStatistics()

	return results
}

// workerLoadTest runs workload for a single worker
func workerLoadTest(ctx context.Context, t *testing.T, db *sql.DB, workerID int, results *LoadTestResults, config LoadTestConfig) {
	workerStartTime := time.Now()
	requestCount := 0

	ticker := time.NewTicker(config.ThinkTime)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			requestCount++

			// Execute load test operation
			operation := selectRandomOperation()
			metrics := executeDatabaseOperation(db, operation)

			results.recordRequest(metrics)

			// Log progress every 50 requests
			if requestCount%50 == 0 {
				t.Logf("Worker %d: Completed %d requests", workerID, requestCount)
			}
		}
	}
}

// DatabaseOperation types
type OperationType int

const (
	OpCreateBuilding OperationType = iota
	OpReadBuilding
	OpUpdateBuilding
	OpCreateFloor
	OpReadFloor
	OpQueryEquipment
	OpSpatialQuery
	OpHealthCheck
)

// selectRandomOperation selects a random database operation
func selectRandomOperation() OperationType {
	operations := []OperationType{
		OpReadBuilding,   // 30% - Most common operation
		OpCreateBuilding, // 10% - Moderate creation
		OpReadFloor,      // 20% - Floor queries
		OpQueryEquipment, // 20% - Equipment queries
		OpSpatialQuery,   // 15% - Advanced spatial queries
		OpHealthCheck,    // 5%  - Health monitoring
	}

	weights := []int{30, 10, 20, 20, 15, 5}
	randIdx := weightedRandom(weights)

	return operations[randIdx]
}

// weightedRandom selects an index based on weights
func weightedRandom(weights []int) int {
	total := 0
	for _, w := range weights {
		total += w
	}

	r := rand.Intn(total)
	cumsum := 0

	for i, w := range weights {
		cumsum += w
		if r < cumsum {
			return i
		}
	}

	return 0 // Fallback
}

// OperationMetrics holds timing and result metrics
type OperationMetrics struct {
	OperationType OperationType
	Success       bool
	ResponseTime  time.Duration
	Error         error
	RowsAffected  int64
}

// executeDatabaseOperation executes a database operation and measures performance
func executeDatabaseOperation(db *sql.DB, opType OperationType) OperationMetrics {
	start := time.Now()

	metrics := OperationMetrics{
		OperationType: opType,
		Success:       false,
	}

	switch opType {
	case OpCreateBuilding:
		metrics = executeCreateBuilding(db, start)
	case OpReadBuilding:
		metrics = executeReadBuilding(db, start)
	case OpReadFloor:
		metrics = executeReadFloor(db, start)
	case OpQueryEquipment:
		metrics = executeQueryEquipment(db, start)
	case OpSpatialQuery:
		metrics = executeSpatialQuery(db, start)
	case OpHealthCheck:
		metrics = executeHealthCheck(db, start)
	default:
		metrics = executeDefaultOperation(db, start)
	}

	metrics.ResponseTime = time.Since(start)
	return metrics
}

// executeCreateBuilding creates a building
func executeCreateBuilding(db *sql.DB, start time.Time) OperationMetrics {
	metrics := OperationMetrics{OperationType: OpCreateBuilding}

	// Generate test data
	buildingName := fmt.Sprintf("LoadTestBuilding_%d_%d", time.Now().Unix(), rand.Intn(1000))
	buildingID := fmt.Sprintf("B%s_%d", generateRandomID(8), rand.Intn(1000))

	query := `
		INSERT INTO buildings (id, arxos_id, name, description, building_type, 
		                      address, city, state, country, latitude, longitude, 
		                      altitude, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW())
	`

	result, err := db.Exec(query,
		buildingID,
		buildingID,
		buildingName,
		"Load Test Building",
		"Commercial",
		fmt.Sprintf("%d Main St", rand.Intn(9999)),
		"LoadTest City",
		"TS",                         // Test State
		"TE",                         // Test Country
		37.7749+rand.Float64()*0.1,   // Random latitude near SF
		-122.4194+rand.Float64()*0.1, // Random longitude near SF
		rand.Float64()*100,           // Random altitude
	)

	if err != nil {
		metrics.Error = err
		return metrics
	}

	affected, err := result.RowsAffected()
	if err != nil {
		metrics.Error = err
		return metrics
	}

	metrics.Success = true
	metrics.RowsAffected = affected
	return metrics
}

// executeReadBuilding reads building data
func executeReadBuilding(db *sql.DB, start time.Time) OperationMetrics {
	metrics := OperationMetrics{OperationType: OpReadBuilding}

	// Read random building
	query := `
		SELECT id, name, address, created_at, updated_at 
		FROM buildings 
		ORDER BY RANDOM() 
		LIMIT 1
	`

	rows, err := db.Query(query)
	if err != nil {
		metrics.Error = err
		return metrics
	}
	defer rows.Close()

	count := 0
	for rows.Next() {
		var id, name, address string
		var createdAt, updatedAt time.Time

		if err := rows.Scan(&id, &name, &address, &createdAt, &updatedAt); err != nil {
			metrics.Error = err
			return metrics
		}
		count++
	}

	metrics.Success = true
	metrics.RowsAffected = int64(count)
	return metrics
}

// executeReadFloor reads floor data
func executeReadFloor(db *sql.DB, start time.Time) OperationMetrics {
	metrics := OperationMetrics{OperationType: OpReadFloor}

	query := `
		SELECT f.id, f.name, f.floor_number, b.name as building_name
		FROM floors f
		JOIN buildings b ON f.building_id = b.id
		ORDER BY RANDOM()
		LIMIT 1
	`

	rows, err := db.Query(query)
	if err != nil {
		metrics.Error = err
		return metrics
	}
	defer rows.Close()

	count := 0
	for rows.Next() {
		var id, name, buildingName string
		var floorNumber int

		if err := rows.Scan(&id, &name, &floorNumber, &buildingName); err != nil {
			metrics.Error = err
			return metrics
		}
		count++
	}

	metrics.Success = true
	metrics.RowsAffected = int64(count)
	return metrics
}

// executeQueryEquipment queries equipment data
func executeQueryEquipment(db *sql.DB, start time.Time) OperationMetrics {
	metrics := OperationMetrics{OperationType: OpQueryEquipment}

	query := `
		SELECT e.id, e.name, e.type, e.status, f.name as floor_name
		FROM equipment e
		JOIN floors f ON e.floor_id = f.id
		WHERE e.status = $1
		ORDER BY RANDOM()
		LIMIT $2
	`

	statuses := []string{"active", "maintenance", "offline", "normal"}
	status := statuses[rand.Intn(len(statuses))]
	limit := rand.Intn(10) + 1

	rows, err := db.Query(query, status, limit)
	if err != nil {
		metrics.Error = err
		return metrics
	}
	defer rows.Close()

	count := 0
	for rows.Next() {
		var id, name, eqType, status, floorName string

		if err := rows.Scan(&id, &name, &eqType, &status, &floorName); err != nil {
			metrics.Error = err
			return metrics
		}
		count++
	}

	metrics.Success = true
	metrics.RowsAffected = int64(count)
	return metrics
}

// executeSpatialQuery executes PostGIS spatial queries
func executeSpatialQuery(db *sql.DB, start time.Time) OperationMetrics {
	metrics := OperationMetrics{OperationType: OpSpatialQuery}

	// Random coordinates for spatial query
	lat := 37.7749 + (rand.Float64()-0.5)*0.1
	lon := -122.4194 + (rand.Float64()-0.5)*0.1
	radius := float64(rand.Intn(500) + 100) // 100-600 meters

	query := `
		SELECT b.id, b.name, 
		       ST_Distance(b.location, ST_SetSRID(ST_MakePoint($2, $1), 4326)) as distance
		FROM buildings b
		WHERE ST_DWithin(b.location, ST_SetSRID(ST_MakePoint($2, $1), 4326), $3)
		ORDER BY distance
		LIMIT 10
	`

	rows, err := db.Query(query, lat, lon, radius)
	if err != nil {
		// Spatial queries might fail if location column doesn't exist - that's OK
		metrics.Error = err
		return metrics
	}
	defer rows.Close()

	count := 0
	for rows.Next() {
		var id, name string
		var distance float64

		if err := rows.Scan(&id, &name, &distance); err != nil {
			metrics.Error = err
			return metrics
		}
		count++
	}

	metrics.Success = true
	metrics.RowsAffected = int64(count)
	return metrics
}

// executeHealthCheck performs basic health check
func executeHealthCheck(db *sql.DB, start time.Time) OperationMetrics {
	metrics := OperationMetrics{OperationType: OpHealthCheck}

	err := db.Ping()
	if err != nil {
		metrics.Error = err
		return metrics
	}

	metrics.Success = true
	return metrics
}

// executeDefaultOperation executes a basic operation
func executeDefaultOperation(db *sql.DB, start time.Time) OperationMetrics {
	metrics := OperationMetrics{OperationType: OpHealthCheck}

	// Simple query
	query := "SELECT 1"
	var result int

	err := db.QueryRow(query).Scan(&result)
	if err != nil {
		metrics.Error = err
		return metrics
	}

	metrics.Success = true
	metrics.RowsAffected = 1
	return metrics
}

// recordRequest records a request's metrics
func (r *LoadTestResults) recordRequest(metrics OperationMetrics) {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.TotalRequests++

	if metrics.Success {
		r.SuccessfulRequests++
	} else {
		r.FailedRequests++
	}

	// Store response time for percentile calculation
	r.responseTimes = append(r.responseTimes, metrics.ResponseTime)
}

// computeStatistics calculates test statistics
func (r *LoadTestResults) computeStatistics() {
	r.mu.Lock()
	defer r.mu.Unlock()

	if len(r.responseTimes) == 0 {
		return
	}

	// Sort response times for percentile calculation
	times := make([]time.Duration, len(r.responseTimes))
	copy(times, r.responseTimes)

	// Calculate average
	sum := time.Duration(0)
	for _, t := range times {
		sum += t
	}
	r.AverageResponseTime = sum / time.Duration(len(times))

	// Calculate 95th percentile (simple implementation)
	p95Index := int(float64(len(times)) * 0.95)
	if p95Index >= len(times) {
		p95Index = len(times) - 1
	}
	r.ResponseTime95th = times[p95Index]
}

// FailureRate returns the failure rate as a decimal (0.0 to 1.0)
func (r *LoadTestResults) FailureRate() float64 {
	if r.TotalRequests == 0 {
		return 0.0
	}

	r.mu.RLock()
	defer r.mu.RUnlock()

	return float64(r.FailedRequests) / float64(r.TotalRequests)
}

// setupTestData prepares the database for load testing
func setupTestData(db *sql.DB) error {
	// Create test buildings if they don't exist
	countQuery := "SELECT COUNT(*) FROM buildings"
	var count int
	err := db.QueryRow(countQuery).Scan(&count)
	if err != nil {
		return err
	}

	// If we have less than 10 buildings, create some test data
	if count < 10 {
		createTestDataQuery := `
			INSERT INTO buildings (id, arxos_id, name, description, building_type, 
			                      address, city, state, country, latitude, longitude, 
			                      altitude, created_at, updated_at)
			SELECT 
				'b' || generate_series || '_test',
				'b' || generate_series || '_test',
				'Test Building ' || generate_series,
				'Load test building ' || generate_series,
				'Commercial',
				generate_series || ' Test St',
				'Test City',
				'TS',
				'TE',
				37.7749 + (generate_series * 0.01),
				-122.4194 + (generate_series * 0.01),
				generate_series * 10,
				NOW(),
				NOW()
			FROM generate_series(1, 10)
		`

		_, err := db.Exec(createTestDataQuery)
		if err != nil {
			return err
		}
	}

	return nil
}

// getDatabaseURL returns the database URL from environment or defaults
func getDatabaseURL() string {
	// Try environment variable first
	if url := os.Getenv("DATABASE_URL"); url != "" {
		return url
	}

	// Try individual components
	host := os.Getenv("POSTGIS_HOST")
	if host == "" {
		host = "localhost"
	}

	port := os.Getenv("POSTGIS_PORT")
	if port == "" {
		port = "5432"
	}

	user := os.Getenv("POSTGIS_USER")
	if user == "" {
		user = "arxos_stress"
	}

	db := os.Getenv("POSTGIS_DB")
	if db == "" {
		db = "arxos_stress_test"
	}

	password := os.Getenv("POSTGIS_PASSWORD")
	if password == "" {
		password = "stress_password"
	}

	sslMode := os.Getenv("POSTGRES_SSLMODE")
	if sslMode == "" {
		sslMode = "disable"
	}

	return fmt.Sprintf("postgres://%s:%s@%s:%s/%s?sslmode=%s",
		user, password, host, port, db, sslMode)
}

// generateRandomID generates a random alphanumeric ID
func generateRandomID(length int) string {
	const charset = "abcdefghijklmnopqrstuvwxyz0123456789"
	b := make([]byte, length)

	for i := range b {
		b[i] = charset[rand.Intn(len(charset))]
	}

	return string(b)
}

func init() {
	rand.Seed(time.Now().UnixNano())
}
