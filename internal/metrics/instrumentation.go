package metrics

import (
	"context"
	"database/sql"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// InstrumentedDB wraps a database connection with metrics
type InstrumentedDB struct {
	db        *sql.DB
	collector *Collector
}

// NewInstrumentedDB creates a new instrumented database connection
func NewInstrumentedDB(db *sql.DB) *InstrumentedDB {
	return &InstrumentedDB{
		db:        db,
		collector: GetCollector(),
	}
}

// QueryContext executes a query with metrics
func (i *InstrumentedDB) QueryContext(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error) {
	start := time.Now()
	i.collector.dbQueries.Inc()

	rows, err := i.db.QueryContext(ctx, query, args...)

	duration := time.Since(start).Seconds()
	i.collector.dbDuration.Observe(duration)

	if err != nil {
		i.collector.dbErrors.Inc()
		logger.Debug("Query error after %.3fs: %v", duration, err)
	}

	return rows, err
}

// ExecContext executes a statement with metrics
func (i *InstrumentedDB) ExecContext(ctx context.Context, query string, args ...interface{}) (sql.Result, error) {
	start := time.Now()
	i.collector.dbQueries.Inc()

	result, err := i.db.ExecContext(ctx, query, args...)

	duration := time.Since(start).Seconds()
	i.collector.dbDuration.Observe(duration)

	if err != nil {
		i.collector.dbErrors.Inc()
		logger.Debug("Exec error after %.3fs: %v", duration, err)
	}

	return result, err
}

// Close closes the database connection
func (i *InstrumentedDB) Close() error {
	return i.db.Close()
}

// Stats returns database statistics
func (i *InstrumentedDB) Stats() sql.DBStats {
	stats := i.db.Stats()

	// Update gauge metrics
	i.collector.activeConnections.Set(float64(stats.OpenConnections))

	return stats
}

// InstrumentedCache wraps a cache with metrics
type InstrumentedCache struct {
	cache     Cache
	collector *Collector
}

// Cache interface for any cache implementation
type Cache interface {
	Get(ctx context.Context, key string) (interface{}, error)
	Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error
	Delete(ctx context.Context, key string) error
}

// NewInstrumentedCache creates a new instrumented cache
func NewInstrumentedCache(cache Cache) *InstrumentedCache {
	return &InstrumentedCache{
		cache:     cache,
		collector: GetCollector(),
	}
}

// Get retrieves a value from cache with metrics
func (i *InstrumentedCache) Get(ctx context.Context, key string) (interface{}, error) {
	value, err := i.cache.Get(ctx, key)

	if err != nil {
		i.collector.cacheMisses.Inc()
	} else {
		i.collector.cacheHits.Inc()
	}

	return value, err
}

// Set stores a value in cache with metrics
func (i *InstrumentedCache) Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error {
	return i.cache.Set(ctx, key, value, ttl)
}

// Delete removes a value from cache with metrics
func (i *InstrumentedCache) Delete(ctx context.Context, key string) error {
	return i.cache.Delete(ctx, key)
}

// RecordAPICall records metrics for an API call
func RecordAPICall(endpoint string, method string, duration time.Duration, statusCode int) {
	collector := GetCollector()

	// Record in histogram
	collector.httpDuration.Observe(duration.Seconds())

	// Count errors
	if statusCode >= 400 {
		collector.httpErrors.Inc()
	}

	logger.Debug("API %s %s: %d in %.3fs", method, endpoint, statusCode, duration.Seconds())
}

// RecordDatabaseOperation records metrics for a database operation
func RecordDatabaseOperation(operation string, duration time.Duration, err error) {
	collector := GetCollector()

	collector.dbQueries.Inc()
	collector.dbDuration.Observe(duration.Seconds())

	if err != nil {
		collector.dbErrors.Inc()
		logger.Debug("DB %s error after %.3fs: %v", operation, duration.Seconds(), err)
	}
}

// RecordCacheOperation records metrics for a cache operation
func RecordCacheOperation(operation string, hit bool) {
	collector := GetCollector()

	if hit {
		collector.cacheHits.Inc()
	} else {
		collector.cacheMisses.Inc()
	}
}

// RecordBusinessMetric records a custom business metric
func RecordBusinessMetric(name string, value float64, labels map[string]string) {
	collector := GetCollector()

	metric, exists := collector.metrics[name]
	if !exists {
		// Auto-register as gauge
		metric = collector.RegisterGauge(name, "Business metric: "+name, labels)
	}

	metric.Set(value)
}

// StartTimer starts a timer for measuring duration
type Timer struct {
	start time.Time
	name  string
}

// NewTimer creates a new timer
func NewTimer(name string) *Timer {
	return &Timer{
		start: time.Now(),
		name:  name,
	}
}

// ObserveDuration records the duration since timer start
func (t *Timer) ObserveDuration() {
	duration := time.Since(t.start)
	collector := GetCollector()

	// Try to find a histogram metric for this timer
	metricName := t.name + "_duration"
	metric, exists := collector.metrics[metricName]
	if !exists {
		// Auto-register histogram with default buckets
		buckets := []float64{0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10}
		metric = collector.RegisterHistogram(metricName, "Duration of "+t.name, buckets)
	}

	metric.Observe(duration.Seconds())
}

// MonitorGoroutines periodically updates goroutine count
func MonitorGoroutines(ctx context.Context, interval time.Duration) {
	collector := GetCollector()
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			collector.UpdateGoroutineCount()
		}
	}
}