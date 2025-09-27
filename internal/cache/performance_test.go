package cache

import (
	"context"
	"fmt"
	"testing"
	"time"
)

func TestAdvancedCache(t *testing.T) {
	config := &CacheConfig{
		Strategy:        StrategyLRU,
		MaxEntries:      1000,
		MaxSizeBytes:    10 * 1024 * 1024, // 10MB
		DefaultTTL:      5 * time.Minute,
		CleanupInterval: 1 * time.Minute,
		EnableMetrics:   true,
	}

	cache := NewAdvancedCache(config)
	defer cache.Close()

	ctx := context.Background()

	// Test basic operations
	err := cache.Set(ctx, "key1", "value1", &CacheOptions{TTL: time.Minute})
	if err != nil {
		t.Fatalf("Failed to set cache value: %v", err)
	}

	value, found := cache.Get(ctx, "key1")
	if !found {
		t.Fatal("Expected to find cached value")
	}
	if value != "value1" {
		t.Errorf("Expected 'value1', got %v", value)
	}

	// Test cache miss
	_, found = cache.Get(ctx, "nonexistent")
	if found {
		t.Fatal("Expected cache miss")
	}

	// Test metrics
	metrics := cache.GetMetrics()
	if metrics.Hits != 1 || metrics.Misses != 1 {
		t.Errorf("Expected 1 hit and 1 miss, got %d hits and %d misses", metrics.Hits, metrics.Misses)
	}
}

func TestQueryOptimizer(t *testing.T) {
	cache := NewAdvancedCache(nil)
	defer cache.Close()

	optimizer := NewQueryOptimizer(cache)

	// Test query optimization
	profile, err := optimizer.OptimizeQuery(context.Background(), QueryTypeSpatial,
		"SELECT * FROM equipment WHERE ST_Contains(geometry, $1)", []interface{}{"POINT(0 0)"})
	if err != nil {
		t.Fatalf("Failed to optimize query: %v", err)
	}

	if profile.QueryType != QueryTypeSpatial {
		t.Errorf("Expected QueryTypeSpatial, got %s", profile.QueryType)
	}

	// Test complexity analysis
	complexity := optimizer.analyzeComplexity(profile)
	if complexity == "" {
		t.Error("Expected complexity analysis")
	}

	// Test stats
	stats := optimizer.GetQueryStats(QueryTypeSpatial)
	if stats == nil {
		t.Error("Expected query stats")
	}
}

func TestResourcePool(t *testing.T) {
	config := &PoolConfig{
		MaxTotalResources: 10,
		MaxMemoryMB:       100,
		CleanupInterval:   1 * time.Minute,
		IdleTimeout:       5 * time.Minute,
		ResourceConfigs: map[ResourceType]ResourceConfig{
			ResourceTypeDatabase: {
				MaxSize:     5,
				IdleTimeout: 5 * time.Minute,
			},
		},
	}

	pool := NewResourcePool(config)
	defer pool.Close()

	ctx := context.Background()

	// Test resource acquisition
	resource, err := pool.AcquireResource(ctx, ResourceTypeDatabase, map[string]interface{}{"test": true})
	if err != nil {
		t.Fatalf("Failed to acquire resource: %v", err)
	}

	if resource.Type != ResourceTypeDatabase {
		t.Errorf("Expected ResourceTypeDatabase, got %s", resource.Type)
	}

	// Test resource release
	err = pool.ReleaseResource(resource)
	if err != nil {
		t.Fatalf("Failed to release resource: %v", err)
	}

	// Test metrics
	metrics := pool.GetMetrics()
	if metrics.TotalResources == 0 {
		t.Error("Expected total resources > 0")
	}
}

func TestPerformanceMonitor(t *testing.T) {
	config := &MonitorConfig{
		CollectionInterval: 100 * time.Millisecond,
		RetentionPeriod:    1 * time.Minute,
		MaxMetrics:         1000,
		EnableAlerts:       true,
		Thresholds: []PerformanceThreshold{
			{
				MetricName: "test_metric",
				Warning:    50.0,
				Critical:   100.0,
				Unit:       "count",
			},
		},
	}

	monitor := NewPerformanceMonitor(config)
	defer monitor.Close()

	// Test metric recording
	monitor.RecordMetric(PerformanceMetric{
		Name:      "test_metric",
		Value:     75.0,
		Unit:      "count",
		Timestamp: time.Now(),
		Tags:      map[string]string{"test": "true"},
	})

	// Test metric retrieval
	metrics := monitor.GetMetrics("test_metric", 10)
	if len(metrics) == 0 {
		t.Error("Expected metrics")
	}

	// Test system metrics
	systemMetrics := monitor.GetSystemMetrics()
	if systemMetrics == nil {
		t.Error("Expected system metrics")
	}

	// Test alerts
	alerts := monitor.GetAlerts(false)
	if len(alerts) == 0 {
		t.Error("Expected alerts for exceeded threshold")
	}

	// Test alert resolution
	if len(alerts) > 0 {
		err := monitor.ResolveAlert(alerts[0].ID)
		if err != nil {
			t.Fatalf("Failed to resolve alert: %v", err)
		}
	}
}

func TestPerformanceManager(t *testing.T) {
	config := &PerformanceConfig{
		EnableOptimization: true,
		EnableMonitoring:   true,
		EnableResourcePool: true,
	}

	manager := NewPerformanceManager(config)
	defer manager.Close()

	// Test module performance recording
	manager.RecordModulePerformance("test_module", 100*time.Millisecond, true)
	manager.RecordCacheHit("test_module")
	manager.RecordCacheMiss("test_module")

	// Test module performance retrieval
	module, exists := manager.GetModulePerformance("test_module")
	if !exists {
		t.Fatal("Expected module performance data")
	}

	if module.RequestCount != 1 {
		t.Errorf("Expected 1 request, got %d", module.RequestCount)
	}

	if module.CacheHits != 1 || module.CacheMisses != 1 {
		t.Errorf("Expected 1 cache hit and 1 miss, got %d hits and %d misses",
			module.CacheHits, module.CacheMisses)
	}

	// Test performance report generation
	report := manager.GeneratePerformanceReport()
	if report == nil {
		t.Fatal("Expected performance report")
	}

	if len(report.ModuleMetrics) == 0 {
		t.Error("Expected module metrics in report")
	}

	// Test optimization
	err := manager.OptimizeModule("test_module")
	if err != nil {
		t.Fatalf("Failed to optimize module: %v", err)
	}
}

func TestCacheStrategies(t *testing.T) {
	// Test LRU strategy
	lruConfig := &CacheConfig{
		Strategy:     StrategyLRU,
		MaxEntries:   3,
		MaxSizeBytes: 1024 * 1024, // 1MB
		DefaultTTL:   time.Minute,
	}

	lruCache := NewAdvancedCache(lruConfig)
	defer lruCache.Close()

	ctx := context.Background()

	// Fill cache to capacity
	lruCache.Set(ctx, "key1", "value1", nil)
	lruCache.Set(ctx, "key2", "value2", nil)
	lruCache.Set(ctx, "key3", "value3", nil)

	// Access key1 to make it most recently used
	_, found := lruCache.Get(ctx, "key1")
	if !found {
		t.Error("Expected key1 to be found after setting")
	}

	// Add new key, should evict key2 (least recently used)
	lruCache.Set(ctx, "key4", "value4", nil)

	// key2 should be evicted
	_, found = lruCache.Get(ctx, "key2")
	if found {
		t.Error("Expected key2 to be evicted")
	}

	// key1 should still be there
	_, found = lruCache.Get(ctx, "key1")
	if !found {
		t.Error("Expected key1 to still be in cache")
	}

	// key3 should still be there
	_, found = lruCache.Get(ctx, "key3")
	if !found {
		t.Error("Expected key3 to still be in cache")
	}

	// key4 should be there
	_, found = lruCache.Get(ctx, "key4")
	if !found {
		t.Error("Expected key4 to be in cache")
	}
}

func TestTagBasedInvalidation(t *testing.T) {
	cache := NewAdvancedCache(nil)
	defer cache.Close()

	ctx := context.Background()

	// Set values with tags
	cache.Set(ctx, "key1", "value1", &CacheOptions{Tags: []string{"group1", "type1"}})
	cache.Set(ctx, "key2", "value2", &CacheOptions{Tags: []string{"group1", "type2"}})
	cache.Set(ctx, "key3", "value3", &CacheOptions{Tags: []string{"group2", "type1"}})

	// Verify all keys exist
	_, found := cache.Get(ctx, "key1")
	if !found {
		t.Error("Expected key1 to exist")
	}

	// Invalidate by tag
	err := cache.InvalidateByTag(ctx, "group1")
	if err != nil {
		t.Fatalf("Failed to invalidate by tag: %v", err)
	}

	// key1 and key2 should be gone (group1), key3 should remain
	_, found = cache.Get(ctx, "key1")
	if found {
		t.Error("Expected key1 to be invalidated")
	}

	_, found = cache.Get(ctx, "key2")
	if found {
		t.Error("Expected key2 to be invalidated")
	}

	_, found = cache.Get(ctx, "key3")
	if !found {
		t.Error("Expected key3 to still exist")
	}
}

func TestPerformanceThresholds(t *testing.T) {
	config := &MonitorConfig{
		EnableAlerts: true,
		Thresholds: []PerformanceThreshold{
			{
				MetricName: "response_time",
				Warning:    100.0,
				Critical:   500.0,
				Unit:       "ms",
			},
		},
	}

	monitor := NewPerformanceMonitor(config)
	defer monitor.Close()

	// Record metric below threshold
	monitor.RecordMetric(PerformanceMetric{
		Name:      "response_time",
		Value:     50.0,
		Unit:      "ms",
		Timestamp: time.Now(),
	})

	alerts := monitor.GetAlerts(false)
	if len(alerts) > 0 {
		t.Error("Expected no alerts for value below threshold")
	}

	// Record metric above warning threshold
	monitor.RecordMetric(PerformanceMetric{
		Name:      "response_time",
		Value:     200.0,
		Unit:      "ms",
		Timestamp: time.Now(),
	})

	alerts = monitor.GetAlerts(false)
	if len(alerts) == 0 {
		t.Error("Expected alert for value above warning threshold")
	}

	// Record metric above critical threshold
	monitor.RecordMetric(PerformanceMetric{
		Name:      "response_time",
		Value:     600.0,
		Unit:      "ms",
		Timestamp: time.Now(),
	})

	alerts = monitor.GetAlerts(false)
	criticalAlerts := 0
	for _, alert := range alerts {
		if alert.Severity == SeverityCritical {
			criticalAlerts++
		}
	}

	if criticalAlerts == 0 {
		t.Error("Expected critical alert for value above critical threshold")
	}
}

func TestConcurrentAccess(t *testing.T) {
	cache := NewAdvancedCache(nil)
	defer cache.Close()

	ctx := context.Background()

	// Test concurrent reads and writes
	done := make(chan bool)
	numGoroutines := 10

	for i := 0; i < numGoroutines; i++ {
		go func(id int) {
			for j := 0; j < 100; j++ {
				key := fmt.Sprintf("key_%d_%d", id, j)
				value := fmt.Sprintf("value_%d_%d", id, j)

				// Set value
				cache.Set(ctx, key, value, nil)

				// Get value
				cache.Get(ctx, key)
			}
			done <- true
		}(i)
	}

	// Wait for all goroutines to complete
	for i := 0; i < numGoroutines; i++ {
		<-done
	}

	// Verify cache is still functional
	metrics := cache.GetMetrics()
	if metrics.Hits == 0 {
		t.Error("Expected cache hits from concurrent access")
	}
}
