package cache

import (
	"context"
	"fmt"
	"runtime"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// ResourceType defines different types of resources
type ResourceType string

const (
	ResourceTypeDatabase  ResourceType = "database"
	ResourceTypeCache     ResourceType = "cache"
	ResourceTypeHTTP      ResourceType = "http"
	ResourceTypeFile      ResourceType = "file"
	ResourceTypeMemory    ResourceType = "memory"
	ResourceTypeGoroutine ResourceType = "goroutine"
)

// ResourcePool manages a pool of resources
type ResourcePool struct {
	mu        sync.RWMutex
	resources map[ResourceType]*ResourceManager
	config    *PoolConfig
	metrics   *PoolMetrics
	stopChan  chan struct{}
}

// ResourceManager manages a specific type of resource
type ResourceManager struct {
	Type        ResourceType      `json:"type"`
	MaxSize     int               `json:"max_size"`
	CurrentSize int               `json:"current_size"`
	Resources   []Resource        `json:"resources"`
	WaitQueue   []ResourceRequest `json:"wait_queue"`
	mu          sync.RWMutex
}

// Resource represents a pooled resource
type Resource struct {
	ID          string                 `json:"id"`
	Type        ResourceType           `json:"type"`
	CreatedAt   time.Time              `json:"created_at"`
	LastUsed    time.Time              `json:"last_used"`
	UseCount    int64                  `json:"use_count"`
	IsActive    bool                   `json:"is_active"`
	Metadata    map[string]interface{} `json:"metadata"`
	CleanupFunc func() error           `json:"-"`
}

// ResourceRequest represents a request for a resource
type ResourceRequest struct {
	ID       string                 `json:"id"`
	Type     ResourceType           `json:"type"`
	Priority int                    `json:"priority"`
	Timeout  time.Duration          `json:"timeout"`
	Context  context.Context        `json:"-"`
	Response chan ResourceResponse  `json:"-"`
	Metadata map[string]interface{} `json:"metadata"`
}

// ResourceResponse represents a response to a resource request
type ResourceResponse struct {
	Resource *Resource `json:"resource"`
	Error    error     `json:"error"`
}

// PoolConfig defines configuration for the resource pool
type PoolConfig struct {
	MaxTotalResources int                             `json:"max_total_resources"`
	MaxMemoryMB       int64                           `json:"max_memory_mb"`
	CleanupInterval   time.Duration                   `json:"cleanup_interval"`
	IdleTimeout       time.Duration                   `json:"idle_timeout"`
	ResourceConfigs   map[ResourceType]ResourceConfig `json:"resource_configs"`
}

// ResourceConfig defines configuration for a specific resource type
type ResourceConfig struct {
	MaxSize     int           `json:"max_size"`
	IdleTimeout time.Duration `json:"idle_timeout"`
	CleanupFunc func() error  `json:"-"`
}

// PoolMetrics tracks resource pool performance
type PoolMetrics struct {
	TotalResources  int64         `json:"total_resources"`
	ActiveResources int64         `json:"active_resources"`
	IdleResources   int64         `json:"idle_resources"`
	MemoryUsageMB   int64         `json:"memory_usage_mb"`
	RequestCount    int64         `json:"request_count"`
	WaitTime        time.Duration `json:"avg_wait_time"`
	UtilizationRate float64       `json:"utilization_rate"`
	ErrorCount      int64         `json:"error_count"`
}

// NewResourcePool creates a new resource pool
func NewResourcePool(config *PoolConfig) *ResourcePool {
	if config == nil {
		config = &PoolConfig{
			MaxTotalResources: 1000,
			MaxMemoryMB:       1024, // 1GB
			CleanupInterval:   5 * time.Minute,
			IdleTimeout:       10 * time.Minute,
			ResourceConfigs:   make(map[ResourceType]ResourceConfig),
		}
	}

	pool := &ResourcePool{
		resources: make(map[ResourceType]*ResourceManager),
		config:    config,
		metrics:   &PoolMetrics{},
		stopChan:  make(chan struct{}),
	}

	// Initialize resource managers
	for resourceType, resourceConfig := range config.ResourceConfigs {
		pool.resources[resourceType] = &ResourceManager{
			Type:      resourceType,
			MaxSize:   resourceConfig.MaxSize,
			Resources: make([]Resource, 0),
			WaitQueue: make([]ResourceRequest, 0),
		}
	}

	// Start cleanup goroutine
	go pool.cleanupRoutine()

	// Start memory monitoring
	go pool.memoryMonitor()

	return pool
}

// AcquireResource acquires a resource from the pool
func (rp *ResourcePool) AcquireResource(ctx context.Context, resourceType ResourceType, metadata map[string]interface{}) (*Resource, error) {
	rp.mu.RLock()
	manager, exists := rp.resources[resourceType]
	rp.mu.RUnlock()

	if !exists {
		return nil, fmt.Errorf("resource type %s not configured", resourceType)
	}

	// Try to get an existing resource
	resource := rp.tryGetResource(manager)
	if resource != nil {
		rp.updateResourceUsage(resource)
		rp.metrics.RequestCount++
		return resource, nil
	}

	// Create new resource if under limit
	if rp.canCreateResource(manager) {
		resource, err := rp.createResource(resourceType, metadata)
		if err != nil {
			return nil, fmt.Errorf("failed to create resource: %w", err)
		}
		rp.updateResourceUsage(resource)
		rp.metrics.RequestCount++
		return resource, nil
	}

	// Wait for resource to become available
	return rp.waitForResource(ctx, manager, metadata)
}

// ReleaseResource releases a resource back to the pool
func (rp *ResourcePool) ReleaseResource(resource *Resource) error {
	if resource == nil {
		return nil
	}

	rp.mu.RLock()
	manager, exists := rp.resources[resource.Type]
	rp.mu.RUnlock()

	if !exists {
		return fmt.Errorf("resource type %s not configured", resource.Type)
	}

	manager.mu.Lock()
	defer manager.mu.Unlock()

	// Update resource metadata
	resource.LastUsed = time.Now()
	resource.IsActive = false

	// Check if we should keep the resource or clean it up
	if rp.shouldKeepResource(resource) {
		manager.Resources = append(manager.Resources, *resource)
		manager.CurrentSize++
	} else {
		// Clean up the resource
		if resource.CleanupFunc != nil {
			resource.CleanupFunc()
		}
		manager.CurrentSize--
	}

	// Process waiting requests
	rp.processWaitQueue(manager)

	return nil
}

// GetMetrics returns resource pool metrics
func (rp *ResourcePool) GetMetrics() *PoolMetrics {
	rp.mu.RLock()
	defer rp.mu.RUnlock()

	metrics := *rp.metrics

	// Update current metrics
	var totalResources, activeResources, idleResources int64
	for _, manager := range rp.resources {
		manager.mu.RLock()
		totalResources += int64(manager.CurrentSize)
		for _, resource := range manager.Resources {
			if resource.IsActive {
				activeResources++
			} else {
				idleResources++
			}
		}
		manager.mu.RUnlock()
	}

	metrics.TotalResources = totalResources
	metrics.ActiveResources = activeResources
	metrics.IdleResources = idleResources
	metrics.MemoryUsageMB = rp.getMemoryUsage()

	if totalResources > 0 {
		metrics.UtilizationRate = float64(activeResources) / float64(totalResources)
	}

	return &metrics
}

// Close gracefully shuts down the resource pool
func (rp *ResourcePool) Close() error {
	close(rp.stopChan)

	// Clean up all resources
	rp.mu.Lock()
	defer rp.mu.Unlock()

	for _, manager := range rp.resources {
		manager.mu.Lock()
		for _, resource := range manager.Resources {
			if resource.CleanupFunc != nil {
				resource.CleanupFunc()
			}
		}
		manager.Resources = nil
		manager.mu.Unlock()
	}

	return nil
}

// Helper methods

func (rp *ResourcePool) tryGetResource(manager *ResourceManager) *Resource {
	manager.mu.Lock()
	defer manager.mu.Unlock()

	for i, resource := range manager.Resources {
		if !resource.IsActive {
			// Mark as active and remove from pool
			resource.IsActive = true
			resource.LastUsed = time.Now()
			resource.UseCount++

			// Remove from slice
			manager.Resources = append(manager.Resources[:i], manager.Resources[i+1:]...)
			manager.CurrentSize--

			return &resource
		}
	}

	return nil
}

func (rp *ResourcePool) canCreateResource(manager *ResourceManager) bool {
	rp.mu.RLock()
	defer rp.mu.RUnlock()

	return manager.CurrentSize < manager.MaxSize &&
		rp.getTotalResources() < rp.config.MaxTotalResources &&
		rp.getMemoryUsage() < rp.config.MaxMemoryMB
}

func (rp *ResourcePool) createResource(resourceType ResourceType, metadata map[string]interface{}) (*Resource, error) {
	resource := &Resource{
		ID:        fmt.Sprintf("%s_%d", resourceType, time.Now().UnixNano()),
		Type:      resourceType,
		CreatedAt: time.Now(),
		LastUsed:  time.Now(),
		UseCount:  1,
		IsActive:  true,
		Metadata:  metadata,
	}

	// Set cleanup function based on resource type
	resource.CleanupFunc = rp.getCleanupFunc(resourceType)

	// Add to manager
	rp.mu.RLock()
	manager := rp.resources[resourceType]
	rp.mu.RUnlock()

	manager.mu.Lock()
	manager.CurrentSize++
	manager.mu.Unlock()

	return resource, nil
}

func (rp *ResourcePool) waitForResource(ctx context.Context, manager *ResourceManager, metadata map[string]interface{}) (*Resource, error) {
	request := ResourceRequest{
		ID:       fmt.Sprintf("req_%d", time.Now().UnixNano()),
		Type:     manager.Type,
		Priority: 1,
		Timeout:  30 * time.Second,
		Context:  ctx,
		Response: make(chan ResourceResponse, 1),
		Metadata: metadata,
	}

	manager.mu.Lock()
	manager.WaitQueue = append(manager.WaitQueue, request)
	manager.mu.Unlock()

	select {
	case response := <-request.Response:
		return response.Resource, response.Error
	case <-ctx.Done():
		// Remove from wait queue
		manager.mu.Lock()
		for i, req := range manager.WaitQueue {
			if req.ID == request.ID {
				manager.WaitQueue = append(manager.WaitQueue[:i], manager.WaitQueue[i+1:]...)
				break
			}
		}
		manager.mu.Unlock()
		return nil, ctx.Err()
	}
}

func (rp *ResourcePool) shouldKeepResource(resource *Resource) bool {
	// Keep resource if it's been used recently and we're under capacity
	idleTime := time.Since(resource.LastUsed)
	return idleTime < rp.config.IdleTimeout
}

func (rp *ResourcePool) processWaitQueue(manager *ResourceManager) {
	if len(manager.WaitQueue) == 0 {
		return
	}

	// Get the first waiting request
	request := manager.WaitQueue[0]
	manager.WaitQueue = manager.WaitQueue[1:]

	// Try to get a resource for the request
	resource := rp.tryGetResource(manager)
	if resource != nil {
		request.Response <- ResourceResponse{Resource: resource, Error: nil}
	} else {
		// Put request back at the front
		manager.WaitQueue = append([]ResourceRequest{request}, manager.WaitQueue...)
	}
}

func (rp *ResourcePool) getTotalResources() int {
	var total int
	for _, manager := range rp.resources {
		total += manager.CurrentSize
	}
	return total
}

func (rp *ResourcePool) getMemoryUsage() int64 {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	return int64(m.Alloc / 1024 / 1024) // Convert to MB
}

func (rp *ResourcePool) getCleanupFunc(resourceType ResourceType) func() error {
	// Return appropriate cleanup function based on resource type
	switch resourceType {
	case ResourceTypeDatabase:
		return func() error {
			logger.Debug("Cleaning up database resource")
			return nil
		}
	case ResourceTypeCache:
		return func() error {
			logger.Debug("Cleaning up cache resource")
			return nil
		}
	case ResourceTypeHTTP:
		return func() error {
			logger.Debug("Cleaning up HTTP resource")
			return nil
		}
	default:
		return func() error {
			logger.Debug("Cleaning up %s resource", resourceType)
			return nil
		}
	}
}

func (rp *ResourcePool) updateResourceUsage(resource *Resource) {
	resource.LastUsed = time.Now()
	resource.UseCount++
}

func (rp *ResourcePool) cleanupRoutine() {
	ticker := time.NewTicker(rp.config.CleanupInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			rp.cleanupIdleResources()
		case <-rp.stopChan:
			return
		}
	}
}

func (rp *ResourcePool) cleanupIdleResources() {
	rp.mu.RLock()
	defer rp.mu.RUnlock()

	for _, manager := range rp.resources {
		manager.mu.Lock()
		var activeResources []Resource

		for _, resource := range manager.Resources {
			if time.Since(resource.LastUsed) > rp.config.IdleTimeout {
				// Clean up idle resource
				if resource.CleanupFunc != nil {
					resource.CleanupFunc()
				}
				manager.CurrentSize--
			} else {
				activeResources = append(activeResources, resource)
			}
		}

		manager.Resources = activeResources
		manager.mu.Unlock()
	}
}

func (rp *ResourcePool) memoryMonitor() {
	ticker := time.NewTicker(1 * time.Minute)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			memoryUsage := rp.getMemoryUsage()
			if memoryUsage > rp.config.MaxMemoryMB {
				logger.Warn("Memory usage %dMB exceeds limit %dMB", memoryUsage, rp.config.MaxMemoryMB)
				// Trigger garbage collection
				runtime.GC()
			}
		case <-rp.stopChan:
			return
		}
	}
}
