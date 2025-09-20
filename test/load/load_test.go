//go:build load
// +build load

package load

import (
	"context"
	"fmt"
	"math/rand"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/services"
	"github.com/arx-os/arxos/internal/spatial"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// LoadTestConfig defines configuration for load tests
type LoadTestConfig struct {
	DatabaseURL      string
	NumWorkers       int
	OperationsPerSec int
	TestDuration     time.Duration
	RampUpTime       time.Duration
}

// LoadTestMetrics tracks test metrics
type LoadTestMetrics struct {
	TotalOperations   int64
	SuccessOperations int64
	FailedOperations  int64
	TotalLatency      int64
	MaxLatency        int64
	MinLatency        int64
	Percentile95      int64
	Percentile99      int64
	StartTime         time.Time
	EndTime           time.Time
}

// LoadTestRunner manages load test execution
type LoadTestRunner struct {
	config   *LoadTestConfig
	db       *database.PostGISDB
	services *services.ServiceRegistry
	metrics  *LoadTestMetrics
	ctx      context.Context
	cancel   context.CancelFunc
}

func NewLoadTestRunner(config *LoadTestConfig) (*LoadTestRunner, error) {
	dbConfig := database.PostGISConfig{
		Host:     "localhost",
		Port:     5432,
		Database: "arxos_load_test",
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

	services := services.NewServiceRegistry(db)

	ctx, cancel := context.WithCancel(context.Background())

	return &LoadTestRunner{
		config:   config,
		db:       db,
		services: services,
		metrics:  &LoadTestMetrics{MinLatency: int64(time.Hour)},
		ctx:      ctx,
		cancel:   cancel,
	}, nil
}

// TestEquipmentLoadTest performs load testing on equipment operations
func TestEquipmentLoadTest(t *testing.T) {
	config := &LoadTestConfig{
		NumWorkers:       100,
		OperationsPerSec: 1000,
		TestDuration:     5 * time.Minute,
		RampUpTime:       30 * time.Second,
	}

	runner, err := NewLoadTestRunner(config)
	require.NoError(t, err)
	defer runner.Cleanup()

	// Run the load test
	runner.RunEquipmentLoadTest(t)

	// Report metrics
	runner.ReportMetrics(t)
}

func (r *LoadTestRunner) RunEquipmentLoadTest(t *testing.T) {
	var wg sync.WaitGroup

	r.metrics.StartTime = time.Now()

	// Calculate operations per worker
	opsPerWorker := r.config.OperationsPerSec / r.config.NumWorkers
	interval := time.Second / time.Duration(opsPerWorker)

	// Ramp up workers gradually
	rampUpInterval := r.config.RampUpTime / time.Duration(r.config.NumWorkers)

	for w := 0; w < r.config.NumWorkers; w++ {
		wg.Add(1)
		go r.equipmentWorker(&wg, w, interval)
		time.Sleep(rampUpInterval)
	}

	// Run for specified duration
	time.Sleep(r.config.TestDuration)
	r.cancel()

	// Wait for all workers to complete
	wg.Wait()
	r.metrics.EndTime = time.Now()
}

func (r *LoadTestRunner) equipmentWorker(wg *sync.WaitGroup, workerID int, interval time.Duration) {
	defer wg.Done()

	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	operations := []func(int) error{
		r.createEquipmentOp,
		r.updatePositionOp,
		r.queryProximityOp,
		r.queryBoundingBoxOp,
		r.getEquipmentOp,
	}

	for {
		select {
		case <-r.ctx.Done():
			return
		case <-ticker.C:
			// Randomly select an operation
			op := operations[rand.Intn(len(operations))]

			start := time.Now()
			err := op(workerID)
			latency := time.Since(start).Nanoseconds()

			atomic.AddInt64(&r.metrics.TotalOperations, 1)
			atomic.AddInt64(&r.metrics.TotalLatency, latency)

			if err != nil {
				atomic.AddInt64(&r.metrics.FailedOperations, 1)
			} else {
				atomic.AddInt64(&r.metrics.SuccessOperations, 1)
				r.updateLatencyMetrics(latency)
			}
		}
	}
}

func (r *LoadTestRunner) createEquipmentOp(workerID int) error {
	equipment := models.Equipment{
		ID:       fmt.Sprintf("LOAD_%d_%s", workerID, uuid.New().String()[:8]),
		Name:     fmt.Sprintf("Load Test Equipment %d", workerID),
		Type:     "sensor",
		Status:   "active",
		Metadata: map[string]interface{}{"worker": workerID},
	}

	return r.services.EquipmentService.CreateEquipment(r.ctx, &equipment)
}

func (r *LoadTestRunner) updatePositionOp(workerID int) error {
	equipmentID := fmt.Sprintf("LOAD_%d_BASE", workerID)
	position := spatial.Point3D{
		X: rand.Float64() * 10000,
		Y: rand.Float64() * 10000,
		Z: rand.Float64() * 1000,
	}

	return r.services.SpatialService.UpdateEquipmentPosition(
		r.ctx, equipmentID, position, spatial.ConfidenceMedium, "load_test",
	)
}

func (r *LoadTestRunner) queryProximityOp(workerID int) error {
	center := spatial.Point3D{
		X: rand.Float64() * 10000,
		Y: rand.Float64() * 10000,
		Z: rand.Float64() * 1000,
	}

	_, err := r.services.SpatialService.FindEquipmentNearPoint(r.ctx, center, 1000)
	return err
}

func (r *LoadTestRunner) queryBoundingBoxOp(workerID int) error {
	minX := rand.Float64() * 5000
	minY := rand.Float64() * 5000

	bbox := spatial.BoundingBox{
		Min: spatial.Point3D{X: minX, Y: minY, Z: 0},
		Max: spatial.Point3D{X: minX + 2000, Y: minY + 2000, Z: 1000},
	}

	_, err := r.services.SpatialService.FindEquipmentInBoundingBox(r.ctx, bbox)
	return err
}

func (r *LoadTestRunner) getEquipmentOp(workerID int) error {
	equipmentID := fmt.Sprintf("LOAD_%d_BASE", workerID)
	_, err := r.services.EquipmentService.GetEquipment(r.ctx, equipmentID)
	return err
}

func (r *LoadTestRunner) updateLatencyMetrics(latency int64) {
	// Update max latency
	for {
		max := atomic.LoadInt64(&r.metrics.MaxLatency)
		if latency <= max || atomic.CompareAndSwapInt64(&r.metrics.MaxLatency, max, latency) {
			break
		}
	}

	// Update min latency
	for {
		min := atomic.LoadInt64(&r.metrics.MinLatency)
		if latency >= min || atomic.CompareAndSwapInt64(&r.metrics.MinLatency, min, latency) {
			break
		}
	}
}

func (r *LoadTestRunner) ReportMetrics(t *testing.T) {
	total := atomic.LoadInt64(&r.metrics.TotalOperations)
	success := atomic.LoadInt64(&r.metrics.SuccessOperations)
	failed := atomic.LoadInt64(&r.metrics.FailedOperations)

	duration := r.metrics.EndTime.Sub(r.metrics.StartTime)
	throughput := float64(total) / duration.Seconds()
	avgLatency := time.Duration(atomic.LoadInt64(&r.metrics.TotalLatency) / total)

	t.Logf("=== Load Test Results ===")
	t.Logf("Duration: %v", duration)
	t.Logf("Total Operations: %d", total)
	t.Logf("Successful: %d (%.2f%%)", success, float64(success)/float64(total)*100)
	t.Logf("Failed: %d (%.2f%%)", failed, float64(failed)/float64(total)*100)
	t.Logf("Throughput: %.2f ops/sec", throughput)
	t.Logf("Avg Latency: %v", avgLatency)
	t.Logf("Min Latency: %v", time.Duration(atomic.LoadInt64(&r.metrics.MinLatency)))
	t.Logf("Max Latency: %v", time.Duration(atomic.LoadInt64(&r.metrics.MaxLatency)))

	// Assert performance requirements
	assert.Less(t, float64(failed)/float64(total), 0.01, "Error rate should be less than 1%")
	assert.Greater(t, throughput, float64(r.config.OperationsPerSec)*0.9, "Should achieve at least 90% of target throughput")
}

func (r *LoadTestRunner) Cleanup() {
	if r.db != nil {
		// Clean up test data
		ctx := context.Background()
		queries := []string{
			"DELETE FROM equipment_positions WHERE equipment_id LIKE 'LOAD_%'",
			"DELETE FROM equipment WHERE id LIKE 'LOAD_%'",
		}

		for _, q := range queries {
			_, _ = r.db.GetDB().ExecContext(ctx, q)
		}

		r.db.Close()
	}
}

// TestSpatialLoadTest performs load testing on spatial operations
func TestSpatialLoadTest(t *testing.T) {
	config := &LoadTestConfig{
		NumWorkers:       50,
		OperationsPerSec: 500,
		TestDuration:     3 * time.Minute,
		RampUpTime:       20 * time.Second,
	}

	runner, err := NewLoadTestRunner(config)
	require.NoError(t, err)
	defer runner.Cleanup()

	// Pre-populate with test data
	runner.PrePopulateSpatialData(t, 10000)

	// Run the load test
	runner.RunSpatialLoadTest(t)

	// Report metrics
	runner.ReportMetrics(t)
}

func (r *LoadTestRunner) PrePopulateSpatialData(t *testing.T, numEquipment int) {
	t.Logf("Pre-populating %d equipment items...", numEquipment)

	for i := 0; i < numEquipment; i++ {
		equipment := models.Equipment{
			ID:     fmt.Sprintf("SPATIAL_BASE_%d", i),
			Name:   fmt.Sprintf("Spatial Test Equipment %d", i),
			Type:   "sensor",
			Status: "active",
		}

		err := r.services.EquipmentService.CreateEquipment(r.ctx, &equipment)
		require.NoError(t, err)

		position := spatial.Point3D{
			X: rand.Float64() * 100000,
			Y: rand.Float64() * 100000,
			Z: rand.Float64() * 10000,
		}

		err = r.services.SpatialService.UpdateEquipmentPosition(
			r.ctx, equipment.ID, position, spatial.ConfidenceHigh, "pre_populate",
		)
		require.NoError(t, err)
	}

	t.Log("Pre-population complete")
}

func (r *LoadTestRunner) RunSpatialLoadTest(t *testing.T) {
	var wg sync.WaitGroup

	r.metrics.StartTime = time.Now()

	// Calculate operations per worker
	opsPerWorker := r.config.OperationsPerSec / r.config.NumWorkers
	interval := time.Second / time.Duration(opsPerWorker)

	for w := 0; w < r.config.NumWorkers; w++ {
		wg.Add(1)
		go r.spatialWorker(&wg, w, interval)
	}

	// Run for specified duration
	time.Sleep(r.config.TestDuration)
	r.cancel()

	// Wait for all workers to complete
	wg.Wait()
	r.metrics.EndTime = time.Now()
}

func (r *LoadTestRunner) spatialWorker(wg *sync.WaitGroup, workerID int, interval time.Duration) {
	defer wg.Done()

	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-r.ctx.Done():
			return
		case <-ticker.C:
			var err error
			start := time.Now()

			switch rand.Intn(3) {
			case 0: // Complex proximity search
				err = r.complexProximitySearch()
			case 1: // Path finding
				err = r.pathFindingOp()
			case 2: // Clustering
				err = r.clusteringOp()
			}

			latency := time.Since(start).Nanoseconds()

			atomic.AddInt64(&r.metrics.TotalOperations, 1)
			atomic.AddInt64(&r.metrics.TotalLatency, latency)

			if err != nil {
				atomic.AddInt64(&r.metrics.FailedOperations, 1)
			} else {
				atomic.AddInt64(&r.metrics.SuccessOperations, 1)
				r.updateLatencyMetrics(latency)
			}
		}
	}
}

func (r *LoadTestRunner) complexProximitySearch() error {
	// Multiple proximity searches with different radii
	center := spatial.Point3D{
		X: rand.Float64() * 50000 + 25000,
		Y: rand.Float64() * 50000 + 25000,
		Z: rand.Float64() * 5000,
	}

	radii := []float64{500, 1000, 2000, 5000}
	for _, radius := range radii {
		_, err := r.services.SpatialService.FindEquipmentNearPoint(r.ctx, center, radius)
		if err != nil {
			return err
		}
	}

	return nil
}

func (r *LoadTestRunner) pathFindingOp() error {
	startID := fmt.Sprintf("SPATIAL_BASE_%d", rand.Intn(1000))
	endID := fmt.Sprintf("SPATIAL_BASE_%d", rand.Intn(1000)+9000)

	_, _, err := r.services.SpatialService.FindPath(r.ctx, startID, endID)
	return err
}

func (r *LoadTestRunner) clusteringOp() error {
	radius := float64(rand.Intn(5000) + 1000)
	_, err := r.services.SpatialService.ClusterEquipment(r.ctx, radius)
	return err
}