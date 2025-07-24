package services

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/shirou/gopsutil/v3/disk"
	"github.com/shirou/gopsutil/v3/mem"
	"gorm.io/gorm"
)

// HealthService provides comprehensive health checking capabilities
type HealthService struct {
	db *gorm.DB

	// Health check data
	healthData  map[string]*HealthCheck
	healthMutex sync.RWMutex

	// Health check intervals
	checkIntervals map[string]time.Duration

	// Health check handlers
	healthHandlers map[string]HealthCheckHandler
	handlerMutex   sync.RWMutex

	// Context for graceful shutdown
	ctx    context.Context
	cancel context.CancelFunc
}

// HealthCheck represents a health check result
type HealthCheck struct {
	Name        string                 `json:"name"`
	Status      string                 `json:"status"` // healthy, warning, critical, unknown
	Message     string                 `json:"message"`
	Details     map[string]interface{} `json:"details"`
	LastCheck   time.Time              `json:"last_check"`
	LastSuccess time.Time              `json:"last_success,omitempty"`
	LastFailure time.Time              `json:"last_failure,omitempty"`
	Error       string                 `json:"error,omitempty"`
	Duration    time.Duration          `json:"duration"`
}

// HealthCheckHandler defines the interface for health check handlers
type HealthCheckHandler interface {
	Check() (*HealthCheck, error)
}

// NewHealthService creates a new health service
func NewHealthService(db *gorm.DB) *HealthService {
	ctx, cancel := context.WithCancel(context.Background())

	hs := &HealthService{
		db:             db,
		healthData:     make(map[string]*HealthCheck),
		checkIntervals: make(map[string]time.Duration),
		healthHandlers: make(map[string]HealthCheckHandler),
		ctx:            ctx,
		cancel:         cancel,
	}

	// Initialize default health checks
	hs.initializeDefaultHealthChecks()

	// Start background health checking
	go hs.startHealthChecking()

	return hs
}

// initializeDefaultHealthChecks sets up default health checks
func (hs *HealthService) initializeDefaultHealthChecks() {
	// Database health check
	hs.AddHealthCheck("database", &DatabaseHealthCheck{db: hs.db}, 30*time.Second)

	// Memory health check
	hs.AddHealthCheck("memory", &MemoryHealthCheck{}, 60*time.Second)

	// Disk health check
	hs.AddHealthCheck("disk", &DiskHealthCheck{}, 60*time.Second)

	// Application health check
	hs.AddHealthCheck("application", &ApplicationHealthCheck{}, 30*time.Second)
}

// AddHealthCheck adds a health check with specified interval
func (hs *HealthService) AddHealthCheck(name string, handler HealthCheckHandler, interval time.Duration) {
	hs.handlerMutex.Lock()
	defer hs.handlerMutex.Unlock()

	hs.healthHandlers[name] = handler
	hs.checkIntervals[name] = interval
}

// startHealthChecking runs background health checks
func (hs *HealthService) startHealthChecking() {
	tickers := make(map[string]*time.Ticker)

	// Create tickers for each health check
	hs.handlerMutex.RLock()
	for name, interval := range hs.checkIntervals {
		tickers[name] = time.NewTicker(interval)
	}
	hs.handlerMutex.RUnlock()

	// Start health check goroutines
	for name, ticker := range tickers {
		go hs.runHealthCheck(name, ticker)
	}

	// Wait for context cancellation
	<-hs.ctx.Done()

	// Stop all tickers
	for _, ticker := range tickers {
		ticker.Stop()
	}
}

// runHealthCheck runs a specific health check
func (hs *HealthService) runHealthCheck(name string, ticker *time.Ticker) {
	for {
		select {
		case <-ticker.C:
			hs.performHealthCheck(name)
		case <-hs.ctx.Done():
			return
		}
	}
}

// performHealthCheck performs a specific health check
func (hs *HealthService) performHealthCheck(name string) {
	hs.handlerMutex.RLock()
	handler, exists := hs.healthHandlers[name]
	hs.handlerMutex.RUnlock()

	if !exists {
		return
	}

	startTime := time.Now()
	check, err := handler.Check()
	duration := time.Since(startTime)

	if check == nil {
		check = &HealthCheck{
			Name:      name,
			Status:    "unknown",
			Message:   "Health check failed to return result",
			LastCheck: time.Now(),
			Duration:  duration,
		}
	}

	check.Duration = duration
	check.LastCheck = time.Now()

	if err != nil {
		check.Status = "critical"
		check.Error = err.Error()
		check.LastFailure = time.Now()
	} else {
		check.LastSuccess = time.Now()
	}

	hs.healthMutex.Lock()
	hs.healthData[name] = check
	hs.healthMutex.Unlock()
}

// GetHealthStatus returns overall health status
func (hs *HealthService) GetHealthStatus() map[string]interface{} {
	hs.healthMutex.RLock()
	defer hs.healthMutex.RUnlock()

	// Determine overall status
	overallStatus := "healthy"
	criticalCount := 0
	warningCount := 0
	unknownCount := 0

	healthChecks := make(map[string]*HealthCheck)
	for name, check := range hs.healthData {
		healthChecks[name] = &HealthCheck{
			Name:        check.Name,
			Status:      check.Status,
			Message:     check.Message,
			Details:     check.Details,
			LastCheck:   check.LastCheck,
			LastSuccess: check.LastSuccess,
			LastFailure: check.LastFailure,
			Error:       check.Error,
			Duration:    check.Duration,
		}

		switch check.Status {
		case "critical":
			criticalCount++
		case "warning":
			warningCount++
		case "unknown":
			unknownCount++
		}
	}

	if criticalCount > 0 {
		overallStatus = "critical"
	} else if warningCount > 0 {
		overallStatus = "warning"
	} else if unknownCount > 0 {
		overallStatus = "unknown"
	}

	return map[string]interface{}{
		"status":    overallStatus,
		"timestamp": time.Now(),
		"checks":    healthChecks,
		"summary": map[string]interface{}{
			"total_checks": len(healthChecks),
			"healthy":      len(healthChecks) - criticalCount - warningCount - unknownCount,
			"warning":      warningCount,
			"critical":     criticalCount,
			"unknown":      unknownCount,
		},
	}
}

// GetHealthCheck returns a specific health check
func (hs *HealthService) GetHealthCheck(name string) (*HealthCheck, error) {
	hs.healthMutex.RLock()
	defer hs.healthMutex.RUnlock()

	check, exists := hs.healthData[name]
	if !exists {
		return nil, fmt.Errorf("health check '%s' not found", name)
	}

	return &HealthCheck{
		Name:        check.Name,
		Status:      check.Status,
		Message:     check.Message,
		Details:     check.Details,
		LastCheck:   check.LastCheck,
		LastSuccess: check.LastSuccess,
		LastFailure: check.LastFailure,
		Error:       check.Error,
		Duration:    check.Duration,
	}, nil
}

// PerformHealthCheck performs a health check on demand
func (hs *HealthService) PerformHealthCheck(name string) (*HealthCheck, error) {
	hs.handlerMutex.RLock()
	handler, exists := hs.healthHandlers[name]
	hs.handlerMutex.RUnlock()

	if !exists {
		return nil, fmt.Errorf("health check '%s' not found", name)
	}

	startTime := time.Now()
	check, err := handler.Check()
	duration := time.Since(startTime)

	if check == nil {
		check = &HealthCheck{
			Name:      name,
			Status:    "unknown",
			Message:   "Health check failed to return result",
			LastCheck: time.Now(),
			Duration:  duration,
		}
	}

	check.Duration = duration
	check.LastCheck = time.Now()

	if err != nil {
		check.Status = "critical"
		check.Error = err.Error()
		check.LastFailure = time.Now()
	} else {
		check.LastSuccess = time.Now()
	}

	// Update stored health check
	hs.healthMutex.Lock()
	hs.healthData[name] = check
	hs.healthMutex.Unlock()

	return check, nil
}

// DatabaseHealthCheck implements health check for database
type DatabaseHealthCheck struct {
	db *gorm.DB
}

func (dhc *DatabaseHealthCheck) Check() (*HealthCheck, error) {
	startTime := time.Now()

	// Test database connectivity
	var result int
	err := dhc.db.Raw("SELECT 1").Scan(&result).Error

	duration := time.Since(startTime)

	if err != nil {
		return &HealthCheck{
			Name:      "database",
			Status:    "critical",
			Message:   "Database connection failed",
			Error:     err.Error(),
			LastCheck: time.Now(),
			Duration:  duration,
		}, err
	}

	// Get database stats
	sqlDB, _ := dhc.db.DB()
	stats := sqlDB.Stats()

	return &HealthCheck{
		Name:    "database",
		Status:  "healthy",
		Message: "Database connection successful",
		Details: map[string]interface{}{
			"max_open_connections": stats.MaxOpenConnections,
			"open_connections":     stats.OpenConnections,
			"in_use":               stats.InUse,
			"idle":                 stats.Idle,
			"wait_count":           stats.WaitCount,
			"wait_duration":        stats.WaitDuration,
		},
		LastCheck: time.Now(),
		Duration:  duration,
	}, nil
}

// MemoryHealthCheck implements health check for memory
type MemoryHealthCheck struct{}

func (mhc *MemoryHealthCheck) Check() (*HealthCheck, error) {
	startTime := time.Now()

	memory, err := mem.VirtualMemory()
	duration := time.Since(startTime)

	if err != nil {
		return &HealthCheck{
			Name:      "memory",
			Status:    "unknown",
			Message:   "Failed to get memory information",
			Error:     err.Error(),
			LastCheck: time.Now(),
			Duration:  duration,
		}, err
	}

	status := "healthy"
	if memory.UsedPercent > 90 {
		status = "critical"
	} else if memory.UsedPercent > 80 {
		status = "warning"
	}

	message := "Memory usage is normal"
	if status == "critical" {
		message = "Memory usage is critical"
	} else if status == "warning" {
		message = "Memory usage is high"
	}

	return &HealthCheck{
		Name:    "memory",
		Status:  status,
		Message: message,
		Details: map[string]interface{}{
			"total":     memory.Total,
			"used":      memory.Used,
			"available": memory.Available,
			"percent":   memory.UsedPercent,
		},
		LastCheck: time.Now(),
		Duration:  duration,
	}, nil
}

// DiskHealthCheck implements health check for disk
type DiskHealthCheck struct{}

func (dhc *DiskHealthCheck) Check() (*HealthCheck, error) {
	startTime := time.Now()

	partitions, err := disk.Partitions(false)
	duration := time.Since(startTime)

	if err != nil {
		return &HealthCheck{
			Name:      "disk",
			Status:    "unknown",
			Message:   "Failed to get disk information",
			Error:     err.Error(),
			LastCheck: time.Now(),
			Duration:  duration,
		}, err
	}

	status := "healthy"
	criticalPartitions := []string{}
	warningPartitions := []string{}

	diskDetails := make(map[string]interface{})

	for _, partition := range partitions {
		usage, err := disk.Usage(partition.Mountpoint)
		if err != nil {
			continue
		}

		partitionStatus := "healthy"
		if usage.UsedPercent > 90 {
			partitionStatus = "critical"
			criticalPartitions = append(criticalPartitions, partition.Mountpoint)
		} else if usage.UsedPercent > 80 {
			partitionStatus = "warning"
			warningPartitions = append(warningPartitions, partition.Mountpoint)
		}

		diskDetails[partition.Mountpoint] = map[string]interface{}{
			"total":   usage.Total,
			"used":    usage.Used,
			"free":    usage.Free,
			"percent": usage.UsedPercent,
			"status":  partitionStatus,
		}

		if partitionStatus == "critical" {
			status = "critical"
		} else if partitionStatus == "warning" && status != "critical" {
			status = "warning"
		}
	}

	message := "Disk usage is normal"
	if len(criticalPartitions) > 0 {
		message = fmt.Sprintf("Critical disk usage on: %v", criticalPartitions)
	} else if len(warningPartitions) > 0 {
		message = fmt.Sprintf("High disk usage on: %v", warningPartitions)
	}

	return &HealthCheck{
		Name:      "disk",
		Status:    status,
		Message:   message,
		Details:   diskDetails,
		LastCheck: time.Now(),
		Duration:  duration,
	}, nil
}

// ApplicationHealthCheck implements health check for application
type ApplicationHealthCheck struct{}

func (ahc *ApplicationHealthCheck) Check() (*HealthCheck, error) {
	startTime := time.Now()

	// This is a basic application health check
	// In a real implementation, this would check application-specific health indicators

	duration := time.Since(startTime)

	return &HealthCheck{
		Name:    "application",
		Status:  "healthy",
		Message: "Application is running normally",
		Details: map[string]interface{}{
			"uptime":  duration.String(),
			"version": "1.0.0",
		},
		LastCheck: time.Now(),
		Duration:  duration,
	}, nil
}

// StartHealthServer starts the health check HTTP server
func (hs *HealthService) StartHealthServer(addr string) {
	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		health := hs.GetHealthStatus()
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(health)
	})

	http.HandleFunc("/health/", func(w http.ResponseWriter, r *http.Request) {
		// Extract check name from URL
		checkName := r.URL.Path[len("/health/"):]
		if checkName == "" {
			http.Error(w, "Health check name required", http.StatusBadRequest)
			return
		}

		check, err := hs.GetHealthCheck(checkName)
		if err != nil {
			http.Error(w, err.Error(), http.StatusNotFound)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(check)
	})

	fmt.Printf("Starting health server on %s\n", addr)
	if err := http.ListenAndServe(addr, nil); err != nil {
		fmt.Printf("Health server error: %v\n", err)
	}
}

// Stop stops the health service
func (hs *HealthService) Stop() {
	hs.cancel()
}
