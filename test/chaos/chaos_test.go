//go:build chaos
// +build chaos

package chaos

import (
	"context"
	"database/sql"
	"fmt"
	"math/rand"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/infrastructure"
	"github.com/arx-os/arxos/internal/infrastructure/services"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// ChaosTestConfig defines configuration for chaos tests
type ChaosTestConfig struct {
	DatabaseURL            string
	NumWorkers             int
	TestDuration           time.Duration
	ConnectionDropRate     float64 // Probability of dropping a connection
	SlowQueryRate          float64 // Probability of introducing query delay
	DataCorruptionRate     float64 // Probability of data corruption simulation
	NetworkPartitionRate   float64 // Probability of network partition
	ResourceExhaustionRate float64 // Probability of resource exhaustion
}

// ChaosTestRunner manages chaos test execution
type ChaosTestRunner struct {
	config          *ChaosTestConfig
	db              *infrastructure.PostGISDatabase
	services        *services.DaemonService
	ctx             context.Context
	cancel          context.CancelFunc
	failureInjector *FailureInjector
	metrics         *ChaosMetrics
}

// ChaosMetrics tracks chaos test metrics
type ChaosMetrics struct {
	TotalOperations       int64
	SuccessfulRecoveries  int64
	FailedRecoveries      int64
	DataInconsistencies   int64
	ConnectionFailures    int64
	TimeoutErrors         int64
	DataIntegrityFailures int64
}

// FailureInjector simulates various failure conditions
type FailureInjector struct {
	config *ChaosTestConfig
	mu     sync.RWMutex
	active map[string]bool
}

func NewChaosTestRunner(config *ChaosTestConfig) (*ChaosTestRunner, error) {
	dbConfig := database.PostGISConfig{
		Host:     "localhost",
		Port:     5432,
		Database: "arxos_chaos_test",
		User:     "arxos",
		Password: "testpass",
		SSLMode:  "disable",
		MaxConns: config.NumWorkers * 2,
	}

	db := database.NewPostGISDB(dbConfig)
	ctx := context.Background()

	if err := db.Connect(ctx); err != nil {
		return nil, fmt.Errorf("failed to connect to database: %w", err)
	}

	if err := db.InitializeSchema(ctx); err != nil {
		return nil, fmt.Errorf("failed to initialize schema: %w", err)
	}

	// TODO: Implement when ServiceRegistry is available
	// services := services.NewServiceRegistry(db)
	var services *services.DaemonService // Placeholder

	ctx, cancel := context.WithCancel(context.Background())

	return &ChaosTestRunner{
		config:   config,
		db:       db,
		services: services,
		ctx:      ctx,
		cancel:   cancel,
		failureInjector: &FailureInjector{
			config: config,
			active: make(map[string]bool),
		},
		metrics: &ChaosMetrics{},
	}, nil
}

// TestDatabaseResilience tests database resilience under failure conditions
func TestDatabaseResilience(t *testing.T) {
	config := &ChaosTestConfig{
		NumWorkers:             20,
		TestDuration:           5 * time.Minute,
		ConnectionDropRate:     0.1,  // 10% chance
		SlowQueryRate:          0.15, // 15% chance
		DataCorruptionRate:     0.05, // 5% chance
		NetworkPartitionRate:   0.02, // 2% chance
		ResourceExhaustionRate: 0.05, // 5% chance
	}

	runner, err := NewChaosTestRunner(config)
	require.NoError(t, err)
	defer runner.Cleanup()

	// Pre-populate test data
	runner.PrepareTestData(t)

	// Run chaos test
	runner.RunChaosTest(t)

	// Verify system integrity
	runner.VerifySystemIntegrity(t)

	// Report results
	runner.ReportChaosMetrics(t)
}

func (r *ChaosTestRunner) PrepareTestData(t *testing.T) {
	// Create initial consistent state
	for i := 0; i < 100; i++ {
		equipment := models.Equipment{
			ID:       fmt.Sprintf("CHAOS_BASE_%d", i),
			Name:     fmt.Sprintf("Chaos Test Equipment %d", i),
			Type:     "sensor",
			Status:   "active",
			Metadata: map[string]any{"checksum": i},
		}

		// TODO: Implement when EquipmentService is available
		// err := r.services.EquipmentService.CreateEquipment(r.ctx, &equipment)
		// require.NoError(t, err)

		// TODO: Implement when SpatialService is available
		// position := spatial.Point3D{
		// 	X: float64(i * 100),
		// 	Y: float64(i * 100),
		// 	Z: 0,
		// }
		// err = r.services.SpatialService.UpdateEquipmentPosition(
		// 	r.ctx, equipment.ID, position, spatial.ConfidenceHigh, "initial",
		// )
		// require.NoError(t, err)
	}
}

func (r *ChaosTestRunner) RunChaosTest(t *testing.T) {
	var wg sync.WaitGroup

	// Start chaos workers
	for w := 0; w < r.config.NumWorkers; w++ {
		wg.Add(1)
		go r.chaosWorker(&wg, w)
	}

	// Start failure injector
	wg.Add(1)
	go r.runFailureInjector(&wg)

	// Run for specified duration
	time.Sleep(r.config.TestDuration)
	r.cancel()

	// Wait for all workers to complete
	wg.Wait()
}

func (r *ChaosTestRunner) chaosWorker(wg *sync.WaitGroup, workerID int) {
	defer wg.Done()

	for {
		select {
		case <-r.ctx.Done():
			return
		default:
			// Inject failures randomly
			if r.shouldInjectFailure() {
				r.injectRandomFailure()
			}

			// Attempt normal operations
			atomic.AddInt64(&r.metrics.TotalOperations, 1)

			if err := r.performResilientOperation(workerID); err != nil {
				// Try to recover from failure
				if r.attemptRecovery(err) {
					atomic.AddInt64(&r.metrics.SuccessfulRecoveries, 1)
				} else {
					atomic.AddInt64(&r.metrics.FailedRecoveries, 1)
				}
			}

			// Random delay
			time.Sleep(time.Duration(rand.Intn(100)) * time.Millisecond)
		}
	}
}

func (r *ChaosTestRunner) shouldInjectFailure() bool {
	return rand.Float64() < 0.3 // 30% chance of failure injection
}

func (r *ChaosTestRunner) injectRandomFailure() {
	failureTypes := []func(){
		r.injectConnectionDrop,
		r.injectSlowQuery,
		r.injectDataCorruption,
		r.injectNetworkPartition,
		r.injectResourceExhaustion,
	}

	// Randomly select a failure type
	failureTypes[rand.Intn(len(failureTypes))]()
}

func (r *ChaosTestRunner) injectConnectionDrop() {
	if rand.Float64() < r.config.ConnectionDropRate {
		r.failureInjector.mu.Lock()
		r.failureInjector.active["connection_drop"] = true
		r.failureInjector.mu.Unlock()

		atomic.AddInt64(&r.metrics.ConnectionFailures, 1)

		// Simulate connection drop by closing and reopening
		r.db.Close()
		time.Sleep(time.Duration(rand.Intn(1000)) * time.Millisecond)

		// Attempt to reconnect
		ctx, cancel := context.WithTimeout(r.ctx, 5*time.Second)
		defer cancel()
		_ = r.db.Connect(ctx)

		r.failureInjector.mu.Lock()
		r.failureInjector.active["connection_drop"] = false
		r.failureInjector.mu.Unlock()
	}
}

func (r *ChaosTestRunner) injectSlowQuery() {
	if rand.Float64() < r.config.SlowQueryRate {
		r.failureInjector.mu.Lock()
		r.failureInjector.active["slow_query"] = true
		r.failureInjector.mu.Unlock()

		// Simulate slow query
		time.Sleep(time.Duration(rand.Intn(5000)) * time.Millisecond)

		r.failureInjector.mu.Lock()
		r.failureInjector.active["slow_query"] = false
		r.failureInjector.mu.Unlock()
	}
}

func (r *ChaosTestRunner) injectDataCorruption() {
	if rand.Float64() < r.config.DataCorruptionRate {
		r.failureInjector.mu.Lock()
		r.failureInjector.active["data_corruption"] = true
		r.failureInjector.mu.Unlock()

		// Simulate data corruption by updating random equipment with invalid data
		equipmentID := fmt.Sprintf("CHAOS_BASE_%d", rand.Intn(100))

		// Try to set invalid position (NaN values)
		_, _ = r.db.GetDB().ExecContext(r.ctx,
			"UPDATE equipment_positions SET position = ST_GeomFromText('POINT(NaN NaN NaN)', 900913) WHERE equipment_id = $1",
			equipmentID,
		)

		atomic.AddInt64(&r.metrics.DataIntegrityFailures, 1)

		r.failureInjector.mu.Lock()
		r.failureInjector.active["data_corruption"] = false
		r.failureInjector.mu.Unlock()
	}
}

func (r *ChaosTestRunner) injectNetworkPartition() {
	if rand.Float64() < r.config.NetworkPartitionRate {
		r.failureInjector.mu.Lock()
		r.failureInjector.active["network_partition"] = true
		r.failureInjector.mu.Unlock()

		// Simulate network partition by making database unreachable
		originalDB := r.db.GetDB()
		r.db.Close()

		time.Sleep(time.Duration(rand.Intn(10000)) * time.Millisecond)

		// Restore connection
		ctx, cancel := context.WithTimeout(r.ctx, 10*time.Second)
		defer cancel()
		_ = r.db.Connect(ctx)

		// If reconnection failed, restore original connection
		if r.db.GetDB() == nil && originalDB != nil {
			// Attempt to restore using original connection
			_ = r.db.Connect(r.ctx)
		}

		r.failureInjector.mu.Lock()
		r.failureInjector.active["network_partition"] = false
		r.failureInjector.mu.Unlock()
	}
}

func (r *ChaosTestRunner) injectResourceExhaustion() {
	if rand.Float64() < r.config.ResourceExhaustionRate {
		r.failureInjector.mu.Lock()
		r.failureInjector.active["resource_exhaustion"] = true
		r.failureInjector.mu.Unlock()

		// Simulate resource exhaustion by creating many connections
		connections := make([]*sql.DB, 0, 50)
		for i := 0; i < 50; i++ {
			conn, err := sql.Open("postgres",
				"host=localhost port=5432 user=arxos password=testpass dbname=arxos_chaos_test sslmode=disable")
			if err == nil {
				connections = append(connections, conn)
			}
		}

		time.Sleep(time.Duration(rand.Intn(3000)) * time.Millisecond)

		// Clean up connections
		for _, conn := range connections {
			conn.Close()
		}

		r.failureInjector.mu.Lock()
		r.failureInjector.active["resource_exhaustion"] = false
		r.failureInjector.mu.Unlock()
	}
}

func (r *ChaosTestRunner) performResilientOperation(workerID int) error {
	operations := []func(int) error{
		r.resilientCreateOperation,
		r.resilientUpdateOperation,
		r.resilientQueryOperation,
		r.resilientTransactionOperation,
	}

	// Randomly select an operation
	op := operations[rand.Intn(len(operations))]
	return op(workerID)
}

func (r *ChaosTestRunner) resilientCreateOperation(workerID int) error {
	equipment := models.Equipment{
		ID:     fmt.Sprintf("CHAOS_%d_%s", workerID, uuid.New().String()[:8]),
		Name:   fmt.Sprintf("Chaos Equipment %d", workerID),
		Type:   "sensor",
		Status: "active",
	}

	// TODO: Implement when EquipmentService is available
	// Retry logic with exponential backoff
	// maxRetries := 3
	// for i := 0; i < maxRetries; i++ {
	// 	err := r.services.EquipmentService.CreateEquipment(r.ctx, &equipment)
	// 	if err == nil {
	// 		return nil
	// 	}
	// 	// Check if error is retryable
	// 	if !r.isRetryableError(err) {
	// 		return err
	// 	}
	// 	// Exponential backoff
	// 	time.Sleep(time.Duration(1<<uint(i)) * time.Second)
	// }
	return nil // Placeholder
}

func (r *ChaosTestRunner) resilientUpdateOperation(workerID int) error {
	// TODO: Implement when SpatialService is available
	// equipmentID := fmt.Sprintf("CHAOS_BASE_%d", rand.Intn(100))
	// position := spatial.Point3D{
	// 	X: rand.Float64() * 10000,
	// 	Y: rand.Float64() * 10000,
	// 	Z: rand.Float64() * 1000,
	// }
	// // Use context with timeout
	// ctx, cancel := context.WithTimeout(r.ctx, 5*time.Second)
	// defer cancel()
	// err := r.services.SpatialService.UpdateEquipmentPosition(
	// 	ctx, equipmentID, position, spatial.ConfidenceMedium, "chaos_test",
	// )
	// if err != nil && r.isTimeoutError(err) {
	// 	atomic.AddInt64(&r.metrics.TimeoutErrors, 1)
	// }
	// return err
	return nil // Placeholder
}

func (r *ChaosTestRunner) resilientQueryOperation(workerID int) error {
	// TODO: Implement when SpatialService is available
	// center := spatial.Point3D{
	// 	X: rand.Float64() * 10000,
	// 	Y: rand.Float64() * 10000,
	// 	Z: 0,
	// }
	// // Add circuit breaker pattern
	// if r.isCircuitOpen() {
	// 	return fmt.Errorf("circuit breaker open")
	// }
	// ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	// defer cancel()
	// _, err := r.services.SpatialService.FindEquipmentNearPoint(ctx, center, 1000)
	// if err != nil {
	// 	r.recordCircuitFailure()
	// } else {
	// 	r.recordCircuitSuccess()
	// }
	// return err
	return nil // Placeholder
}

func (r *ChaosTestRunner) resilientTransactionOperation(workerID int) error {
	// Perform a complex transaction with rollback on failure
	tx, err := r.db.GetDB().BeginTx(r.ctx, &sql.TxOptions{
		Isolation: sql.LevelSerializable,
	})
	if err != nil {
		return err
	}

	defer func() {
		if p := recover(); p != nil {
			tx.Rollback()
			panic(p)
		}
	}()

	// Multiple operations in transaction
	equipmentID := fmt.Sprintf("CHAOS_TX_%d_%s", workerID, uuid.New().String()[:8])

	_, err = tx.ExecContext(r.ctx,
		"INSERT INTO equipment (id, name, type, status) VALUES ($1, $2, $3, $4)",
		equipmentID, "Transaction Test", "sensor", "active",
	)
	if err != nil {
		tx.Rollback()
		return err
	}

	// TODO: Implement when spatial package is available
	// _, err = tx.ExecContext(r.ctx,
	// 	"INSERT INTO equipment_positions (equipment_id, position, confidence, source) "+
	// 		"VALUES ($1, ST_GeomFromText('POINT(1000 2000 3000)', 900913), $2, $3)",
	// 	equipmentID, spatial.ConfidenceHigh, "transaction",
	// )
	// if err != nil {
	// 	tx.Rollback()
	// 	return err
	// }
	var err error // Placeholder

	// Randomly fail some transactions
	if rand.Float64() < 0.1 {
		tx.Rollback()
		return fmt.Errorf("simulated transaction failure")
	}

	return tx.Commit()
}

func (r *ChaosTestRunner) attemptRecovery(err error) bool {
	if err == nil {
		return true
	}

	// Implement recovery strategies based on error type
	if r.isConnectionError(err) {
		// Attempt reconnection
		ctx, cancel := context.WithTimeout(r.ctx, 10*time.Second)
		defer cancel()

		if reconnectErr := r.db.Connect(ctx); reconnectErr == nil {
			return true
		}
	}

	if r.isDataIntegrityError(err) {
		// Attempt to fix data integrity issues
		return r.repairDataIntegrity()
	}

	return false
}

func (r *ChaosTestRunner) isRetryableError(err error) bool {
	// Check if error is retryable (connection issues, timeouts, etc.)
	if err == nil {
		return false
	}

	errMsg := err.Error()
	retryableErrors := []string{
		"connection refused",
		"connection reset",
		"timeout",
		"deadlock",
		"too many connections",
	}

	for _, retryable := range retryableErrors {
		if contains(errMsg, retryable) {
			return true
		}
	}

	return false
}

func (r *ChaosTestRunner) isTimeoutError(err error) bool {
	return err != nil && contains(err.Error(), "timeout")
}

func (r *ChaosTestRunner) isConnectionError(err error) bool {
	return err != nil && (contains(err.Error(), "connection") || contains(err.Error(), "closed"))
}

func (r *ChaosTestRunner) isDataIntegrityError(err error) bool {
	return err != nil && (contains(err.Error(), "constraint") || contains(err.Error(), "integrity"))
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(substr) == 0 ||
		(len(s) > 0 && len(substr) > 0 && s[0:len(substr)] == substr) ||
		(len(s) > len(substr) && contains(s[1:], substr)))
}

// Circuit breaker implementation
var (
	circuitFailures  int32
	circuitOpen      int32
	circuitThreshold int32 = 5
)

func (r *ChaosTestRunner) isCircuitOpen() bool {
	return atomic.LoadInt32(&circuitOpen) == 1
}

func (r *ChaosTestRunner) recordCircuitFailure() {
	failures := atomic.AddInt32(&circuitFailures, 1)
	if failures >= circuitThreshold {
		atomic.StoreInt32(&circuitOpen, 1)
		// Reset circuit after timeout
		go func() {
			time.Sleep(10 * time.Second)
			atomic.StoreInt32(&circuitOpen, 0)
			atomic.StoreInt32(&circuitFailures, 0)
		}()
	}
}

func (r *ChaosTestRunner) recordCircuitSuccess() {
	atomic.StoreInt32(&circuitFailures, 0)
}

func (r *ChaosTestRunner) repairDataIntegrity() bool {
	// Attempt to repair data integrity issues
	ctx, cancel := context.WithTimeout(r.ctx, 30*time.Second)
	defer cancel()

	// Remove invalid data
	_, err := r.db.GetDB().ExecContext(ctx,
		"DELETE FROM equipment_positions WHERE position IS NULL OR NOT ST_IsValid(position)",
	)

	return err == nil
}

func (r *ChaosTestRunner) runFailureInjector(wg *sync.WaitGroup) {
	defer wg.Done()

	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-r.ctx.Done():
			return
		case <-ticker.C:
			// Periodically inject system-wide failures
			if rand.Float64() < 0.1 { // 10% chance every 5 seconds
				r.injectRandomFailure()
			}
		}
	}
}

func (r *ChaosTestRunner) VerifySystemIntegrity(t *testing.T) {
	t.Log("Verifying system integrity after chaos testing...")

	// Check data consistency
	var inconsistencies int64

	// Verify all equipment have valid positions
	rows, err := r.db.GetDB().QueryContext(r.ctx,
		"SELECT COUNT(*) FROM equipment e "+
			"LEFT JOIN equipment_positions ep ON e.id = ep.equipment_id "+
			"WHERE ep.position IS NULL OR NOT ST_IsValid(ep.position)",
	)
	if err == nil && rows.Next() {
		rows.Scan(&inconsistencies)
		rows.Close()
	}

	if inconsistencies > 0 {
		atomic.AddInt64(&r.metrics.DataInconsistencies, inconsistencies)
		t.Logf("Found %d data inconsistencies", inconsistencies)
	}

	// Verify referential integrity
	rows, err = r.db.GetDB().QueryContext(r.ctx,
		"SELECT COUNT(*) FROM equipment_positions ep "+
			"WHERE NOT EXISTS (SELECT 1 FROM equipment e WHERE e.id = ep.equipment_id)",
	)
	if err == nil && rows.Next() {
		var orphaned int64
		rows.Scan(&orphaned)
		rows.Close()
		if orphaned > 0 {
			atomic.AddInt64(&r.metrics.DataInconsistencies, orphaned)
			t.Logf("Found %d orphaned position records", orphaned)
		}
	}

	// Verify no duplicate primary keys
	rows, err = r.db.GetDB().QueryContext(r.ctx,
		"SELECT equipment_id, COUNT(*) FROM equipment_positions "+
			"GROUP BY equipment_id HAVING COUNT(*) > 1",
	)
	if err == nil {
		duplicates := 0
		for rows.Next() {
			duplicates++
		}
		rows.Close()
		if duplicates > 0 {
			atomic.AddInt64(&r.metrics.DataInconsistencies, int64(duplicates))
			t.Logf("Found %d duplicate position records", duplicates)
		}
	}

	assert.Equal(t, int64(0), atomic.LoadInt64(&r.metrics.DataInconsistencies),
		"System should maintain data integrity despite chaos")
}

func (r *ChaosTestRunner) ReportChaosMetrics(t *testing.T) {
	t.Log("=== Chaos Test Results ===")
	t.Logf("Total Operations: %d", atomic.LoadInt64(&r.metrics.TotalOperations))
	t.Logf("Successful Recoveries: %d", atomic.LoadInt64(&r.metrics.SuccessfulRecoveries))
	t.Logf("Failed Recoveries: %d", atomic.LoadInt64(&r.metrics.FailedRecoveries))
	t.Logf("Connection Failures: %d", atomic.LoadInt64(&r.metrics.ConnectionFailures))
	t.Logf("Timeout Errors: %d", atomic.LoadInt64(&r.metrics.TimeoutErrors))
	t.Logf("Data Integrity Failures: %d", atomic.LoadInt64(&r.metrics.DataIntegrityFailures))
	t.Logf("Data Inconsistencies Found: %d", atomic.LoadInt64(&r.metrics.DataInconsistencies))

	// Calculate recovery rate
	totalFailures := atomic.LoadInt64(&r.metrics.SuccessfulRecoveries) +
		atomic.LoadInt64(&r.metrics.FailedRecoveries)

	if totalFailures > 0 {
		recoveryRate := float64(atomic.LoadInt64(&r.metrics.SuccessfulRecoveries)) /
			float64(totalFailures) * 100
		t.Logf("Recovery Rate: %.2f%%", recoveryRate)

		assert.Greater(t, recoveryRate, 80.0,
			"System should successfully recover from at least 80% of failures")
	}
}

func (r *ChaosTestRunner) Cleanup() {
	if r.db != nil {
		// Clean up test data
		ctx := context.Background()
		queries := []string{
			"DELETE FROM equipment_positions WHERE equipment_id LIKE 'CHAOS_%'",
			"DELETE FROM equipment WHERE id LIKE 'CHAOS_%'",
		}

		for _, q := range queries {
			_, _ = r.db.GetDB().ExecContext(ctx, q)
		}

		r.db.Close()
	}
}
