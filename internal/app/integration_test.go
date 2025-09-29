package app

import (
	"context"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/app/di"
	"github.com/arx-os/arxos/internal/domain/messaging"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestCompleteSystemIntegration(t *testing.T) {
	// Create configuration
	config := di.DefaultConfig()
	config.Database.Host = "localhost"
	config.Database.Port = 5432
	config.Database.Database = "arxos_test"

	// Initialize service locator
	locator := di.GetServiceLocator()
	ctx := context.Background()

	err := locator.Initialize(ctx, config)
	require.NoError(t, err)
	defer locator.Close()

	// Test all services are available
	services := locator.GetServices()
	assert.NotNil(t, services.Building)
	assert.NotNil(t, services.Equipment)
	assert.NotNil(t, services.Spatial)
	assert.NotNil(t, services.Analytics)
	assert.NotNil(t, services.Workflow)
	assert.NotNil(t, services.Database)
	assert.NotNil(t, services.Cache)
	assert.NotNil(t, services.Storage)
	assert.NotNil(t, services.Messaging)

	// Test WebSocket hub
	hub := locator.GetWebSocketHub()
	assert.NotNil(t, hub)
	assert.True(t, hub.IsHealthy())

	// Test service health
	assert.True(t, services.Database.IsHealthy())
	assert.True(t, services.Cache.IsHealthy())
	assert.True(t, services.Storage.IsHealthy())
	assert.True(t, services.Messaging.IsHealthy())

	// Test service stats
	dbStats := services.Database.GetStats()
	assert.NotNil(t, dbStats)

	cacheStats := services.Cache.GetStats()
	assert.NotNil(t, cacheStats)

	storageStats := services.Storage.GetStats()
	assert.NotNil(t, storageStats)

	messagingStats := services.Messaging.GetStats()
	assert.NotNil(t, messagingStats)

	hubStats := hub.GetStats()
	assert.NotNil(t, hubStats)
}

func TestServiceBuilderIntegration(t *testing.T) {
	// Create configuration
	config := di.DefaultConfig()
	config.Development = true

	// Use service builder
	factory := di.NewFactory(nil)
	ctx := context.Background()

	builder := di.NewServiceBuilder(factory, ctx, config)
	container, err := builder.BuildAll()
	require.NoError(t, err)
	defer container.Close()

	// Test all services are built
	services := container.GetServices()
	assert.NotNil(t, services.Building)
	assert.NotNil(t, services.Equipment)
	assert.NotNil(t, services.Spatial)
	assert.NotNil(t, services.Analytics)
	assert.NotNil(t, services.Workflow)
	assert.NotNil(t, services.Database)
	assert.NotNil(t, services.Cache)
	assert.NotNil(t, services.Storage)
	assert.NotNil(t, services.Messaging)

	// Test WebSocket hub
	hub := container.GetWebSocketHub()
	assert.NotNil(t, hub)
	assert.True(t, hub.IsHealthy())
}

func TestWebSocketIntegration(t *testing.T) {
	// Create configuration
	config := di.DefaultConfig()

	// Initialize service locator
	locator := di.GetServiceLocator()
	ctx := context.Background()

	err := locator.Initialize(ctx, config)
	require.NoError(t, err)
	defer locator.Close()

	// Get WebSocket hub
	hub := locator.GetWebSocketHub()
	assert.NotNil(t, hub)

	// Test WebSocket operations
	messagingService := locator.GetMessaging()

	// Test subscribing to building updates
	err = messagingService.SubscribeToBuilding(ctx, "test-user", "test-building")
	assert.NoError(t, err)

	// Test publishing building update
	update := messaging.CreateBuildingUpdate(
		"test-building",
		"status_changed",
		map[string]interface{}{
			"status":    "active",
			"occupancy": 75,
		},
		"test-service",
	)

	err = messagingService.PublishBuildingUpdate(ctx, "test-building", update)
	assert.NoError(t, err)

	// Test subscribing to equipment updates
	err = messagingService.SubscribeToEquipment(ctx, "test-user", "test-equipment")
	assert.NoError(t, err)

	// Test publishing equipment update
	equipmentUpdate := messaging.CreateEquipmentUpdate(
		"test-equipment",
		"test-building",
		"status_changed",
		map[string]interface{}{
			"status":      "running",
			"temperature": 22.5,
		},
		"equipment-service",
	)

	err = messagingService.PublishEquipmentUpdate(ctx, "test-equipment", equipmentUpdate)
	assert.NoError(t, err)

	// Test subscribing to spatial queries
	err = messagingService.SubscribeToSpatialQueries(ctx, "test-user", "nearby_equipment")
	assert.NoError(t, err)

	// Test publishing spatial update
	spatialUpdate := messaging.CreateSpatialUpdate(
		"nearby_equipment",
		map[string]interface{}{
			"center": map[string]float64{"x": 10.5, "y": 20.3, "z": 0.0},
			"radius": 5.0,
			"equipment": []map[string]interface{}{
				{"id": "equipment-1", "distance": 2.1},
				{"id": "equipment-2", "distance": 3.5},
			},
		},
		"spatial-service",
	)

	err = messagingService.PublishSpatialUpdate(ctx, "nearby_equipment", spatialUpdate)
	assert.NoError(t, err)

	// Test subscribing to analytics
	err = messagingService.SubscribeToAnalytics(ctx, "test-user", "energy", "test-building")
	assert.NoError(t, err)

	// Test publishing analytics update
	analyticsUpdate := messaging.CreateAnalyticsUpdate(
		"energy",
		"test-building",
		map[string]interface{}{
			"consumption": 1250.5,
			"efficiency":  85.2,
			"trend":       "decreasing",
		},
		"analytics-service",
	)

	err = messagingService.PublishAnalyticsUpdate(ctx, "energy", "test-building", analyticsUpdate)
	assert.NoError(t, err)

	// Test subscribing to workflow updates
	err = messagingService.SubscribeToWorkflow(ctx, "test-user", "test-workflow")
	assert.NoError(t, err)

	// Test publishing workflow update
	workflowUpdate := messaging.CreateWorkflowUpdate(
		"test-workflow",
		"started",
		map[string]interface{}{
			"workflow_name": "Maintenance Workflow",
			"assigned_to":   "technician-001",
		},
		"workflow-service",
	)

	err = messagingService.PublishWorkflowUpdate(ctx, "test-workflow", workflowUpdate)
	assert.NoError(t, err)

	// Test sending notification
	notification := messaging.CreateNotification(
		"test-user",
		"info",
		"Test Notification",
		"This is a test notification",
		map[string]interface{}{
			"test": true,
		},
	)

	err = messagingService.SendNotification(ctx, "test-user", notification)
	assert.NoError(t, err)

	// Test sending bulk notification
	userIDs := []string{"user-1", "user-2", "user-3"}
	bulkNotification := messaging.CreateNotification(
		"",
		"alert",
		"System Alert",
		"This is a system alert",
		map[string]interface{}{
			"alert_type": "system",
		},
	)

	err = messagingService.SendBulkNotification(ctx, userIDs, bulkNotification)
	assert.NoError(t, err)
}

func TestServiceHealthIntegration(t *testing.T) {
	// Create configuration
	config := di.DefaultConfig()

	// Initialize service locator
	locator := di.GetServiceLocator()
	ctx := context.Background()

	err := locator.Initialize(ctx, config)
	require.NoError(t, err)
	defer locator.Close()

	// Test all services are healthy
	services := locator.GetServices()
	assert.True(t, services.Database.IsHealthy())
	assert.True(t, services.Cache.IsHealthy())
	assert.True(t, services.Storage.IsHealthy())
	assert.True(t, services.Messaging.IsHealthy())

	// Test WebSocket hub health
	hub := locator.GetWebSocketHub()
	assert.True(t, hub.IsHealthy())

	// Test service stats
	stats := locator.GetStats()
	assert.Equal(t, "initialized", stats["status"])
	assert.Contains(t, stats, "services")

	servicesStats := stats["services"].(map[string]interface{})
	assert.Contains(t, servicesStats, "database")
	assert.Contains(t, servicesStats, "cache")
	assert.Contains(t, servicesStats, "storage")
	assert.Contains(t, servicesStats, "messaging")
	assert.Contains(t, servicesStats, "websocket")
}

func TestConcurrentAccessIntegration(t *testing.T) {
	// Create configuration
	config := di.DefaultConfig()

	// Initialize service locator
	locator := di.GetServiceLocator()
	ctx := context.Background()

	err := locator.Initialize(ctx, config)
	require.NoError(t, err)
	defer locator.Close()

	// Test concurrent access
	done := make(chan bool, 10)

	for i := 0; i < 10; i++ {
		go func() {
			defer func() { done <- true }()

			// Concurrent reads should not panic
			services := locator.GetServices()
			assert.NotNil(t, services)

			hub := locator.GetWebSocketHub()
			assert.NotNil(t, hub)

			db := locator.GetDatabase()
			assert.NotNil(t, db)

			cache := locator.GetCache()
			assert.NotNil(t, cache)

			storage := locator.GetStorage()
			assert.NotNil(t, storage)

			messaging := locator.GetMessaging()
			assert.NotNil(t, messaging)
		}()
	}

	// Wait for all goroutines to complete
	for i := 0; i < 10; i++ {
		<-done
	}
}

func TestGracefulShutdownIntegration(t *testing.T) {
	// Create configuration
	config := di.DefaultConfig()

	// Initialize service locator
	locator := di.GetServiceLocator()
	ctx := context.Background()

	err := locator.Initialize(ctx, config)
	require.NoError(t, err)

	// Use services
	services := locator.GetServices()
	assert.NotNil(t, services)

	// Simulate some work
	time.Sleep(10 * time.Millisecond)

	// Gracefully shutdown
	err = locator.Close()
	assert.NoError(t, err)
	assert.False(t, locator.IsInitialized())
}

func TestErrorHandlingIntegration(t *testing.T) {
	// Test with invalid configuration
	config := &di.Config{
		Database: di.DatabaseConfig{
			Host:     "invalid-host",
			Port:     9999,
			Database: "nonexistent",
		},
	}

	// Initialize service locator
	locator := di.GetServiceLocator()
	ctx := context.Background()

	err := locator.Initialize(ctx, config)
	// Should not error with placeholder implementations
	assert.NoError(t, err)
	defer locator.Close()

	// Test accessing services before initialization
	locator2 := di.GetServiceLocator()

	// This should panic
	assert.Panics(t, func() {
		locator2.GetServices()
	})
}

func BenchmarkCompleteSystemIntegration(b *testing.B) {
	config := di.DefaultConfig()
	locator := di.GetServiceLocator()
	ctx := context.Background()

	err := locator.Initialize(ctx, config)
	if err != nil {
		b.Fatal(err)
	}
	defer locator.Close()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		services := locator.GetServices()
		_ = services

		hub := locator.GetWebSocketHub()
		_ = hub

		db := locator.GetDatabase()
		_ = db
	}
}

func BenchmarkWebSocketOperations(b *testing.B) {
	config := di.DefaultConfig()
	locator := di.GetServiceLocator()
	ctx := context.Background()

	err := locator.Initialize(ctx, config)
	if err != nil {
		b.Fatal(err)
	}
	defer locator.Close()

	messagingService := locator.GetMessaging()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		// Test subscribing
		messagingService.SubscribeToBuilding(ctx, "test-user", "test-building")

		// Test publishing
		update := messaging.CreateBuildingUpdate(
			"test-building",
			"status_changed",
			map[string]interface{}{
				"status": "active",
			},
			"test-service",
		)
		messagingService.PublishBuildingUpdate(ctx, "test-building", update)
	}
}
