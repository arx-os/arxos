package monitoring

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// HealthChecker defines the interface for health checking
type HealthChecker interface {
	CheckHealth(ctx context.Context) HealthStatus
	GetName() string
	GetDescription() string
}

// HealthStatus represents the health status of a component
type HealthStatus struct {
	Name      string                 `json:"name"`
	Status    string                 `json:"status"` // "healthy", "unhealthy", "degraded"
	Message   string                 `json:"message"`
	Timestamp time.Time              `json:"timestamp"`
	Duration  time.Duration          `json:"duration"`
	Details   map[string]interface{} `json:"details"`
	Error     error                  `json:"error,omitempty"`
}

// HealthMonitor manages health checks for all components
type HealthMonitor struct {
	mu            sync.RWMutex
	checkers      map[string]HealthChecker
	statuses      map[string]HealthStatus
	lastCheck     time.Time
	checkInterval time.Duration
	timeout       time.Duration
}

// NewHealthMonitor creates a new health monitor
func NewHealthMonitor(checkInterval, timeout time.Duration) *HealthMonitor {
	return &HealthMonitor{
		checkers:      make(map[string]HealthChecker),
		statuses:      make(map[string]HealthStatus),
		checkInterval: checkInterval,
		timeout:       timeout,
	}
}

// RegisterHealthChecker registers a health checker
func (hm *HealthMonitor) RegisterHealthChecker(checker HealthChecker) {
	hm.mu.Lock()
	defer hm.mu.Unlock()

	name := checker.GetName()
	hm.checkers[name] = checker
	logger.Info("Registered health checker: %s", name)
}

// UnregisterHealthChecker removes a health checker
func (hm *HealthMonitor) UnregisterHealthChecker(name string) {
	hm.mu.Lock()
	defer hm.mu.Unlock()

	delete(hm.checkers, name)
	delete(hm.statuses, name)
	logger.Info("Unregistered health checker: %s", name)
}

// CheckHealth performs health checks for all registered checkers
func (hm *HealthMonitor) CheckHealth(ctx context.Context) map[string]HealthStatus {
	hm.mu.RLock()
	checkers := make(map[string]HealthChecker)
	for name, checker := range hm.checkers {
		checkers[name] = checker
	}
	hm.mu.RUnlock()

	statuses := make(map[string]HealthStatus)

	for name, checker := range checkers {
		status := hm.checkSingleHealth(ctx, checker)
		statuses[name] = status

		hm.mu.Lock()
		hm.statuses[name] = status
		hm.mu.Unlock()
	}

	hm.mu.Lock()
	hm.lastCheck = time.Now()
	hm.mu.Unlock()

	return statuses
}

// checkSingleHealth performs a health check for a single component
func (hm *HealthMonitor) checkSingleHealth(ctx context.Context, checker HealthChecker) HealthStatus {
	start := time.Now()

	// Create timeout context
	timeoutCtx, cancel := context.WithTimeout(ctx, hm.timeout)
	defer cancel()

	// Perform health check
	status := checker.CheckHealth(timeoutCtx)
	status.Duration = time.Since(start)
	status.Timestamp = time.Now()

	// Log health check result
	if status.Status == "healthy" {
		logger.Debug("Health check passed for %s: %s", checker.GetName(), status.Message)
	} else {
		logger.Warn("Health check failed for %s: %s", checker.GetName(), status.Message)
		if status.Error != nil {
			logger.Error("Health check error for %s: %v", checker.GetName(), status.Error)
		}
	}

	return status
}

// GetHealthStatus returns the current health status for a component
func (hm *HealthMonitor) GetHealthStatus(name string) (HealthStatus, bool) {
	hm.mu.RLock()
	defer hm.mu.RUnlock()

	status, exists := hm.statuses[name]
	return status, exists
}

// GetAllHealthStatuses returns all current health statuses
func (hm *HealthMonitor) GetAllHealthStatuses() map[string]HealthStatus {
	hm.mu.RLock()
	defer hm.mu.RUnlock()

	statuses := make(map[string]HealthStatus)
	for name, status := range hm.statuses {
		statuses[name] = status
	}
	return statuses
}

// GetOverallHealth returns the overall system health
func (hm *HealthMonitor) GetOverallHealth() HealthStatus {
	hm.mu.RLock()
	defer hm.mu.RUnlock()

	if len(hm.statuses) == 0 {
		return HealthStatus{
			Name:      "overall",
			Status:    "unknown",
			Message:   "No health checkers registered",
			Timestamp: time.Now(),
		}
	}

	healthyCount := 0
	unhealthyCount := 0
	degradedCount := 0
	var messages []string

	for _, status := range hm.statuses {
		switch status.Status {
		case "healthy":
			healthyCount++
		case "unhealthy":
			unhealthyCount++
			messages = append(messages, fmt.Sprintf("%s: %s", status.Name, status.Message))
		case "degraded":
			degradedCount++
			messages = append(messages, fmt.Sprintf("%s: %s", status.Name, status.Message))
		}
	}

	total := len(hm.statuses)
	overallStatus := "healthy"
	message := "All components are healthy"

	if unhealthyCount > 0 {
		overallStatus = "unhealthy"
		message = fmt.Sprintf("%d/%d components unhealthy", unhealthyCount, total)
	} else if degradedCount > 0 {
		overallStatus = "degraded"
		message = fmt.Sprintf("%d/%d components degraded", degradedCount, total)
	}

	return HealthStatus{
		Name:      "overall",
		Status:    overallStatus,
		Message:   message,
		Timestamp: time.Now(),
		Details: map[string]interface{}{
			"total_components": total,
			"healthy":          healthyCount,
			"unhealthy":        unhealthyCount,
			"degraded":         degradedCount,
			"issues":           messages,
		},
	}
}

// StartHealthMonitoring starts background health monitoring
func (hm *HealthMonitor) StartHealthMonitoring(ctx context.Context) {
	ticker := time.NewTicker(hm.checkInterval)
	defer ticker.Stop()

	logger.Info("Started health monitoring with interval %v", hm.checkInterval)

	for {
		select {
		case <-ctx.Done():
			logger.Info("Stopped health monitoring")
			return
		case <-ticker.C:
			hm.CheckHealth(ctx)
		}
	}
}

// GetLastCheckTime returns the time of the last health check
func (hm *HealthMonitor) GetLastCheckTime() time.Time {
	hm.mu.RLock()
	defer hm.mu.RUnlock()
	return hm.lastCheck
}

// DatabaseHealthChecker implements health checking for database
type DatabaseHealthChecker struct {
	name string
	db   interface {
		IsHealthy() bool
		GetStats() map[string]interface{}
	}
}

// NewDatabaseHealthChecker creates a new database health checker
func NewDatabaseHealthChecker(name string, db interface {
	IsHealthy() bool
	GetStats() map[string]interface{}
}) *DatabaseHealthChecker {
	return &DatabaseHealthChecker{
		name: name,
		db:   db,
	}
}

// CheckHealth performs database health check
func (dhc *DatabaseHealthChecker) CheckHealth(ctx context.Context) HealthStatus {
	status := "healthy"
	message := "Database is healthy"
	var err error

	if !dhc.db.IsHealthy() {
		status = "unhealthy"
		message = "Database is not healthy"
		err = fmt.Errorf("database health check failed")
	}

	stats := dhc.db.GetStats()

	return HealthStatus{
		Name:      dhc.name,
		Status:    status,
		Message:   message,
		Timestamp: time.Now(),
		Details:   stats,
		Error:     err,
	}
}

// GetName returns the checker name
func (dhc *DatabaseHealthChecker) GetName() string {
	return dhc.name
}

// GetDescription returns the checker description
func (dhc *DatabaseHealthChecker) GetDescription() string {
	return fmt.Sprintf("Health checker for %s database", dhc.name)
}

// CacheHealthChecker implements health checking for cache
type CacheHealthChecker struct {
	name  string
	cache interface {
		IsHealthy() bool
		GetStats() map[string]interface{}
	}
}

// NewCacheHealthChecker creates a new cache health checker
func NewCacheHealthChecker(name string, cache interface {
	IsHealthy() bool
	GetStats() map[string]interface{}
}) *CacheHealthChecker {
	return &CacheHealthChecker{
		name:  name,
		cache: cache,
	}
}

// CheckHealth performs cache health check
func (chc *CacheHealthChecker) CheckHealth(ctx context.Context) HealthStatus {
	status := "healthy"
	message := "Cache is healthy"
	var err error

	if !chc.cache.IsHealthy() {
		status = "unhealthy"
		message = "Cache is not healthy"
		err = fmt.Errorf("cache health check failed")
	}

	stats := chc.cache.GetStats()

	return HealthStatus{
		Name:      chc.name,
		Status:    status,
		Message:   message,
		Timestamp: time.Now(),
		Details:   stats,
		Error:     err,
	}
}

// GetName returns the checker name
func (chc *CacheHealthChecker) GetName() string {
	return chc.name
}

// GetDescription returns the checker description
func (chc *CacheHealthChecker) GetDescription() string {
	return fmt.Sprintf("Health checker for %s cache", chc.name)
}

// StorageHealthChecker implements health checking for storage
type StorageHealthChecker struct {
	name    string
	storage interface {
		IsHealthy() bool
		GetStats() map[string]interface{}
	}
}

// NewStorageHealthChecker creates a new storage health checker
func NewStorageHealthChecker(name string, storage interface {
	IsHealthy() bool
	GetStats() map[string]interface{}
}) *StorageHealthChecker {
	return &StorageHealthChecker{
		name:    name,
		storage: storage,
	}
}

// CheckHealth performs storage health check
func (shc *StorageHealthChecker) CheckHealth(ctx context.Context) HealthStatus {
	status := "healthy"
	message := "Storage is healthy"
	var err error

	if !shc.storage.IsHealthy() {
		status = "unhealthy"
		message = "Storage is not healthy"
		err = fmt.Errorf("storage health check failed")
	}

	stats := shc.storage.GetStats()

	return HealthStatus{
		Name:      shc.name,
		Status:    status,
		Message:   message,
		Timestamp: time.Now(),
		Details:   stats,
		Error:     err,
	}
}

// GetName returns the checker name
func (shc *StorageHealthChecker) GetName() string {
	return shc.name
}

// GetDescription returns the checker description
func (shc *StorageHealthChecker) GetDescription() string {
	return fmt.Sprintf("Health checker for %s storage", shc.name)
}

// Global health monitor instance
var globalHealthMonitor *HealthMonitor
var healthOnce sync.Once

// GetGlobalHealthMonitor returns the global health monitor instance
func GetGlobalHealthMonitor() *HealthMonitor {
	healthOnce.Do(func() {
		globalHealthMonitor = NewHealthMonitor(30*time.Second, 5*time.Second)
	})
	return globalHealthMonitor
}
