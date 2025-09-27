package cache

import (
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// PerformanceManager orchestrates all performance optimization components
type PerformanceManager struct {
	mu                 sync.RWMutex
	advancedCache      *AdvancedCache
	queryOptimizer     *QueryOptimizer
	resourcePool       *ResourcePool
	performanceMonitor *PerformanceMonitor
	config             *PerformanceConfig
	modules            map[string]ModulePerformance
}

// PerformanceConfig defines configuration for the performance manager
type PerformanceConfig struct {
	CacheConfig        *CacheConfig   `json:"cache_config"`
	PoolConfig         *PoolConfig    `json:"pool_config"`
	MonitorConfig      *MonitorConfig `json:"monitor_config"`
	EnableOptimization bool           `json:"enable_optimization"`
	EnableMonitoring   bool           `json:"enable_monitoring"`
	EnableResourcePool bool           `json:"enable_resource_pool"`
}

// ModulePerformance tracks performance for a specific module
type ModulePerformance struct {
	ModuleName   string                 `json:"module_name"`
	RequestCount int64                  `json:"request_count"`
	AverageTime  time.Duration          `json:"average_time"`
	ErrorCount   int64                  `json:"error_count"`
	CacheHits    int64                  `json:"cache_hits"`
	CacheMisses  int64                  `json:"cache_misses"`
	LastUpdated  time.Time              `json:"last_updated"`
	Metrics      map[string]interface{} `json:"metrics"`
}

// PerformanceReport represents a comprehensive performance report
type PerformanceReport struct {
	GeneratedAt     time.Time                    `json:"generated_at"`
	SystemMetrics   *SystemMetrics               `json:"system_metrics"`
	ModuleMetrics   map[string]ModulePerformance `json:"module_metrics"`
	CacheMetrics    *CacheMetrics                `json:"cache_metrics"`
	PoolMetrics     *PoolMetrics                 `json:"pool_metrics"`
	Alerts          []*PerformanceAlert          `json:"alerts"`
	Recommendations []string                     `json:"recommendations"`
}

// NewPerformanceManager creates a new performance manager
func NewPerformanceManager(config *PerformanceConfig) *PerformanceManager {
	if config == nil {
		config = &PerformanceConfig{
			EnableOptimization: true,
			EnableMonitoring:   true,
			EnableResourcePool: true,
		}
	}

	pm := &PerformanceManager{
		config:  config,
		modules: make(map[string]ModulePerformance),
	}

	// Initialize components
	if config.EnableOptimization {
		pm.advancedCache = NewAdvancedCache(config.CacheConfig)
		pm.queryOptimizer = NewQueryOptimizer(pm.advancedCache)
	}

	if config.EnableResourcePool {
		pm.resourcePool = NewResourcePool(config.PoolConfig)
	}

	if config.EnableMonitoring {
		pm.performanceMonitor = NewPerformanceMonitor(config.MonitorConfig)
	}

	logger.Info("Performance Manager initialized with optimization=%t, monitoring=%t, resource_pool=%t",
		config.EnableOptimization, config.EnableMonitoring, config.EnableResourcePool)

	return pm
}

// GetCache returns the advanced cache instance
func (pm *PerformanceManager) GetCache() *AdvancedCache {
	return pm.advancedCache
}

// GetQueryOptimizer returns the query optimizer instance
func (pm *PerformanceManager) GetQueryOptimizer() *QueryOptimizer {
	return pm.queryOptimizer
}

// GetResourcePool returns the resource pool instance
func (pm *PerformanceManager) GetResourcePool() *ResourcePool {
	return pm.resourcePool
}

// GetPerformanceMonitor returns the performance monitor instance
func (pm *PerformanceManager) GetPerformanceMonitor() *PerformanceMonitor {
	return pm.performanceMonitor
}

// RecordModulePerformance records performance metrics for a module
func (pm *PerformanceManager) RecordModulePerformance(moduleName string, duration time.Duration, success bool) {
	pm.mu.Lock()
	defer pm.mu.Unlock()

	module, exists := pm.modules[moduleName]
	if !exists {
		module = ModulePerformance{
			ModuleName: moduleName,
			Metrics:    make(map[string]interface{}),
		}
	}

	module.RequestCount++
	module.LastUpdated = time.Now()

	// Update average time
	if module.RequestCount == 1 {
		module.AverageTime = duration
	} else {
		module.AverageTime = (module.AverageTime + duration) / 2
	}

	if !success {
		module.ErrorCount++
	}

	pm.modules[moduleName] = module

	// Record metric in performance monitor
	if pm.performanceMonitor != nil {
		pm.performanceMonitor.RecordMetric(PerformanceMetric{
			Name:      fmt.Sprintf("%s_request_time", moduleName),
			Value:     float64(duration.Milliseconds()),
			Unit:      "ms",
			Timestamp: time.Now(),
			Tags:      map[string]string{"module": moduleName},
		})
	}
}

// RecordCacheHit records a cache hit for a module
func (pm *PerformanceManager) RecordCacheHit(moduleName string) {
	pm.mu.Lock()
	defer pm.mu.Unlock()

	module, exists := pm.modules[moduleName]
	if !exists {
		module = ModulePerformance{
			ModuleName: moduleName,
			Metrics:    make(map[string]interface{}),
		}
	}

	module.CacheHits++
	pm.modules[moduleName] = module
}

// RecordCacheMiss records a cache miss for a module
func (pm *PerformanceManager) RecordCacheMiss(moduleName string) {
	pm.mu.Lock()
	defer pm.mu.Unlock()

	module, exists := pm.modules[moduleName]
	if !exists {
		module = ModulePerformance{
			ModuleName: moduleName,
			Metrics:    make(map[string]interface{}),
		}
	}

	module.CacheMisses++
	pm.modules[moduleName] = module
}

// GetModulePerformance returns performance metrics for a module
func (pm *PerformanceManager) GetModulePerformance(moduleName string) (ModulePerformance, bool) {
	pm.mu.RLock()
	defer pm.mu.RUnlock()

	module, exists := pm.modules[moduleName]
	return module, exists
}

// GetAllModulePerformance returns performance metrics for all modules
func (pm *PerformanceManager) GetAllModulePerformance() map[string]ModulePerformance {
	pm.mu.RLock()
	defer pm.mu.RUnlock()

	// Return a copy to prevent external modification
	result := make(map[string]ModulePerformance)
	for name, module := range pm.modules {
		result[name] = module
	}
	return result
}

// GeneratePerformanceReport generates a comprehensive performance report
func (pm *PerformanceManager) GeneratePerformanceReport() *PerformanceReport {
	report := &PerformanceReport{
		GeneratedAt:     time.Now(),
		ModuleMetrics:   pm.GetAllModulePerformance(),
		Recommendations: []string{},
	}

	// Add system metrics
	if pm.performanceMonitor != nil {
		report.SystemMetrics = pm.performanceMonitor.GetSystemMetrics()
		report.Alerts = pm.performanceMonitor.GetAlerts(false)
	}

	// Add cache metrics
	if pm.advancedCache != nil {
		report.CacheMetrics = pm.advancedCache.GetMetrics()
	}

	// Add pool metrics
	if pm.resourcePool != nil {
		report.PoolMetrics = pm.resourcePool.GetMetrics()
	}

	// Generate recommendations
	report.Recommendations = pm.generateRecommendations(report)

	return report
}

// OptimizeModule optimizes performance for a specific module
func (pm *PerformanceManager) OptimizeModule(moduleName string) error {
	module, exists := pm.GetModulePerformance(moduleName)
	if !exists {
		return fmt.Errorf("module %s not found", moduleName)
	}

	// Generate optimization recommendations
	recommendations := pm.getModuleRecommendations(module)

	logger.Info("Optimization recommendations for module %s:", moduleName)
	for _, rec := range recommendations {
		logger.Info("  - %s", rec)
	}

	return nil
}

// Close gracefully shuts down the performance manager
func (pm *PerformanceManager) Close() error {
	var errors []error

	if pm.advancedCache != nil {
		if err := pm.advancedCache.Close(); err != nil {
			errors = append(errors, fmt.Errorf("failed to close cache: %w", err))
		}
	}

	if pm.resourcePool != nil {
		if err := pm.resourcePool.Close(); err != nil {
			errors = append(errors, fmt.Errorf("failed to close resource pool: %w", err))
		}
	}

	if pm.performanceMonitor != nil {
		if err := pm.performanceMonitor.Close(); err != nil {
			errors = append(errors, fmt.Errorf("failed to close performance monitor: %w", err))
		}
	}

	if len(errors) > 0 {
		return fmt.Errorf("errors during shutdown: %v", errors)
	}

	return nil
}

// Helper methods

func (pm *PerformanceManager) generateRecommendations(report *PerformanceReport) []string {
	var recommendations []string

	// Cache recommendations
	if report.CacheMetrics != nil {
		if report.CacheMetrics.HitRate < 0.8 {
			recommendations = append(recommendations,
				"Cache hit rate is low. Consider increasing cache size or improving cache key strategies.")
		}
	}

	// Memory recommendations
	if report.SystemMetrics != nil {
		if report.SystemMetrics.MemoryUsage > 512 {
			recommendations = append(recommendations,
				"Memory usage is high. Consider optimizing data structures or increasing memory limits.")
		}
	}

	// Module-specific recommendations
	for moduleName, module := range report.ModuleMetrics {
		if module.AverageTime > 100*time.Millisecond {
			recommendations = append(recommendations,
				fmt.Sprintf("Module %s has high average response time (%.2fms). Consider optimization.",
					moduleName, float64(module.AverageTime.Milliseconds())))
		}

		if module.ErrorCount > 0 && float64(module.ErrorCount)/float64(module.RequestCount) > 0.05 {
			recommendations = append(recommendations,
				fmt.Sprintf("Module %s has high error rate (%.2f%%). Check error handling.",
					moduleName, float64(module.ErrorCount)/float64(module.RequestCount)*100))
		}
	}

	return recommendations
}

func (pm *PerformanceManager) getModuleRecommendations(module ModulePerformance) []string {
	var recommendations []string

	// Response time recommendations
	if module.AverageTime > 500*time.Millisecond {
		recommendations = append(recommendations, "Consider implementing caching for frequently accessed data")
		recommendations = append(recommendations, "Review database queries for optimization opportunities")
	}

	// Error rate recommendations
	if module.ErrorCount > 0 && float64(module.ErrorCount)/float64(module.RequestCount) > 0.1 {
		recommendations = append(recommendations, "High error rate detected. Review error handling and validation")
	}

	// Cache efficiency recommendations
	totalCacheOps := module.CacheHits + module.CacheMisses
	if totalCacheOps > 0 {
		hitRate := float64(module.CacheHits) / float64(totalCacheOps)
		if hitRate < 0.7 {
			recommendations = append(recommendations, "Low cache hit rate. Consider improving cache key strategies")
		}
	}

	return recommendations
}

// PerformanceMiddleware provides middleware for automatic performance tracking
func (pm *PerformanceManager) PerformanceMiddleware(moduleName string) func(func() error) func() error {
	return func(handler func() error) func() error {
		return func() error {
			start := time.Now()
			err := handler()
			duration := time.Since(start)

			pm.RecordModulePerformance(moduleName, duration, err == nil)

			return err
		}
	}
}
