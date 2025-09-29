package di

import (
	"context"
	"fmt"
	"sync"

	"github.com/arx-os/arxos/internal/app/types"
	"github.com/arx-os/arxos/internal/domain/analytics"
	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/arx-os/arxos/internal/domain/equipment"
	"github.com/arx-os/arxos/internal/domain/messaging"
	"github.com/arx-os/arxos/internal/domain/spatial"
	"github.com/arx-os/arxos/internal/domain/workflow"
	"github.com/arx-os/arxos/internal/infra/cache"
	"github.com/arx-os/arxos/internal/infra/database"
	inframessaging "github.com/arx-os/arxos/internal/infra/messaging"
	"github.com/arx-os/arxos/internal/infra/storage"
)

// ServiceLocator provides a global service locator following Clean Architecture principles
// This is a singleton pattern for easy access to services throughout the application
type ServiceLocator struct {
	container *Container
	mutex     sync.RWMutex
}

var (
	// Global service locator instance
	globalLocator *ServiceLocator
	locatorMutex  sync.Mutex
)

// GetServiceLocator returns the global service locator instance
func GetServiceLocator() *ServiceLocator {
	locatorMutex.Lock()
	defer locatorMutex.Unlock()

	if globalLocator == nil {
		globalLocator = &ServiceLocator{}
	}
	return globalLocator
}

// SetContainer sets the container for the service locator
func (sl *ServiceLocator) SetContainer(container *Container) {
	sl.mutex.Lock()
	defer sl.mutex.Unlock()

	sl.container = container
}

// Initialize initializes the service locator with a container
func (sl *ServiceLocator) Initialize(ctx context.Context, config *Config) error {
	sl.mutex.Lock()
	defer sl.mutex.Unlock()

	if sl.container != nil {
		return fmt.Errorf("service locator already initialized")
	}

	container := NewContainer(config)
	if err := container.Initialize(ctx); err != nil {
		return fmt.Errorf("failed to initialize container: %w", err)
	}

	sl.container = container
	return nil
}

// InitializeWithBuilder initializes the service locator using the service builder
func (sl *ServiceLocator) InitializeWithBuilder(ctx context.Context, config *Config) error {
	sl.mutex.Lock()
	defer sl.mutex.Unlock()

	if sl.container != nil {
		return fmt.Errorf("service locator already initialized")
	}

	factory := NewFactory(nil)
	builder := NewServiceBuilder(factory, ctx, config)

	container, err := builder.BuildAll()
	if err != nil {
		return fmt.Errorf("failed to build services: %w", err)
	}

	sl.container = container
	return nil
}

// GetServices returns the services container
func (sl *ServiceLocator) GetServices() *types.Services {
	sl.mutex.RLock()
	defer sl.mutex.RUnlock()

	if sl.container == nil {
		panic("service locator not initialized")
	}

	return sl.container.GetServices()
}

// GetWebSocketHub returns the WebSocket hub
func (sl *ServiceLocator) GetWebSocketHub() *inframessaging.WebSocketHub {
	sl.mutex.RLock()
	defer sl.mutex.RUnlock()

	if sl.container == nil {
		panic("service locator not initialized")
	}

	return sl.container.GetWebSocketHub()
}

// GetDatabase returns the database service
func (sl *ServiceLocator) GetDatabase() database.Interface {
	sl.mutex.RLock()
	defer sl.mutex.RUnlock()

	if sl.container == nil {
		panic("service locator not initialized")
	}

	db, ok := sl.container.MustGet("database").(database.Interface)
	if !ok {
		panic("database service not properly initialized")
	}
	return db
}

// GetCache returns the cache service
func (sl *ServiceLocator) GetCache() cache.Interface {
	sl.mutex.RLock()
	defer sl.mutex.RUnlock()

	if sl.container == nil {
		panic("service locator not initialized")
	}

	cache, ok := sl.container.MustGet("cache").(cache.Interface)
	if !ok {
		panic("cache service not properly initialized")
	}
	return cache
}

// GetStorage returns the storage service
func (sl *ServiceLocator) GetStorage() storage.Interface {
	sl.mutex.RLock()
	defer sl.mutex.RUnlock()

	if sl.container == nil {
		panic("service locator not initialized")
	}

	storage, ok := sl.container.MustGet("storage").(storage.Interface)
	if !ok {
		panic("storage service not properly initialized")
	}
	return storage
}

// GetMessaging returns the messaging service
func (sl *ServiceLocator) GetMessaging() messaging.Service {
	sl.mutex.RLock()
	defer sl.mutex.RUnlock()

	if sl.container == nil {
		panic("service locator not initialized")
	}

	messaging, ok := sl.container.MustGet("messaging").(messaging.Service)
	if !ok {
		panic("messaging service not properly initialized")
	}
	return messaging
}

// GetBuildingService returns the building service
func (sl *ServiceLocator) GetBuildingService() building.Service {
	sl.mutex.RLock()
	defer sl.mutex.RUnlock()

	if sl.container == nil {
		panic("service locator not initialized")
	}

	building, ok := sl.container.MustGet("building_service").(building.Service)
	if !ok {
		panic("building service not properly initialized")
	}
	return building
}

// GetEquipmentService returns the equipment service
func (sl *ServiceLocator) GetEquipmentService() equipment.Service {
	sl.mutex.RLock()
	defer sl.mutex.RUnlock()

	if sl.container == nil {
		panic("service locator not initialized")
	}

	equipment, ok := sl.container.MustGet("equipment_service").(equipment.Service)
	if !ok {
		panic("equipment service not properly initialized")
	}
	return equipment
}

// GetSpatialService returns the spatial service
func (sl *ServiceLocator) GetSpatialService() spatial.Service {
	sl.mutex.RLock()
	defer sl.mutex.RUnlock()

	if sl.container == nil {
		panic("service locator not initialized")
	}

	spatial, ok := sl.container.MustGet("spatial_service").(spatial.Service)
	if !ok {
		panic("spatial service not properly initialized")
	}
	return spatial
}

// GetAnalyticsService returns the analytics service
func (sl *ServiceLocator) GetAnalyticsService() analytics.Service {
	sl.mutex.RLock()
	defer sl.mutex.RUnlock()

	if sl.container == nil {
		panic("service locator not initialized")
	}

	analytics, ok := sl.container.MustGet("analytics_service").(analytics.Service)
	if !ok {
		panic("analytics service not properly initialized")
	}
	return analytics
}

// GetWorkflowService returns the workflow service
func (sl *ServiceLocator) GetWorkflowService() workflow.Service {
	sl.mutex.RLock()
	defer sl.mutex.RUnlock()

	if sl.container == nil {
		panic("service locator not initialized")
	}

	workflow, ok := sl.container.MustGet("workflow_service").(workflow.Service)
	if !ok {
		panic("workflow service not properly initialized")
	}
	return workflow
}

// Close gracefully shuts down the service locator and all its dependencies
func (sl *ServiceLocator) Close() error {
	sl.mutex.Lock()
	defer sl.mutex.Unlock()

	if sl.container == nil {
		return nil
	}

	err := sl.container.Close()
	sl.container = nil
	return err
}

// IsInitialized checks if the service locator is initialized
func (sl *ServiceLocator) IsInitialized() bool {
	sl.mutex.RLock()
	defer sl.mutex.RUnlock()

	return sl.container != nil
}

// GetStats returns statistics about all services
func (sl *ServiceLocator) GetStats() map[string]interface{} {
	sl.mutex.RLock()
	defer sl.mutex.RUnlock()

	if sl.container == nil {
		return map[string]interface{}{
			"status": "not_initialized",
		}
	}

	stats := map[string]interface{}{
		"status": "initialized",
		"services": map[string]interface{}{
			"database":  sl.GetDatabase().GetStats(),
			"cache":     sl.GetCache().GetStats(),
			"storage":   sl.GetStorage().GetStats(),
			"messaging": sl.GetMessaging().GetStats(),
			"websocket": sl.GetWebSocketHub().GetStats(),
		},
	}

	return stats
}

// Convenience functions for global access
func GetDatabase() database.Interface {
	return GetServiceLocator().GetDatabase()
}

func GetCache() cache.Interface {
	return GetServiceLocator().GetCache()
}

func GetStorage() storage.Interface {
	return GetServiceLocator().GetStorage()
}

func GetMessaging() messaging.Service {
	return GetServiceLocator().GetMessaging()
}

func GetBuildingService() building.Service {
	return GetServiceLocator().GetBuildingService()
}

func GetEquipmentService() equipment.Service {
	return GetServiceLocator().GetEquipmentService()
}

func GetSpatialService() spatial.Service {
	return GetServiceLocator().GetSpatialService()
}

func GetAnalyticsService() analytics.Service {
	return GetServiceLocator().GetAnalyticsService()
}

func GetWorkflowService() workflow.Service {
	return GetServiceLocator().GetWorkflowService()
}

func GetWebSocketHub() *inframessaging.WebSocketHub {
	return GetServiceLocator().GetWebSocketHub()
}

func GetServices() *types.Services {
	return GetServiceLocator().GetServices()
}
