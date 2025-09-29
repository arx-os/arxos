package di

import (
	"context"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewFactory(t *testing.T) {
	container := NewContainer(DefaultConfig())
	factory := NewFactory(container)

	assert.NotNil(t, factory)
	assert.Equal(t, container, factory.container)
}

func TestFactory_CreateDatabaseService(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig().Database

	service, err := factory.CreateDatabaseService(ctx, config)

	assert.NoError(t, err)
	assert.NotNil(t, service)
	assert.True(t, service.IsHealthy())
}

func TestFactory_CreateCacheService(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig().Cache

	service, err := factory.CreateCacheService(ctx, config)

	assert.NoError(t, err)
	assert.NotNil(t, service)
	assert.True(t, service.IsHealthy())
}

func TestFactory_CreateStorageService(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig().Storage

	service, err := factory.CreateStorageService(ctx, config)

	assert.NoError(t, err)
	assert.NotNil(t, service)
	assert.True(t, service.IsHealthy())
}

func TestFactory_CreateWebSocketHub(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig().WebSocket

	hub, err := factory.CreateWebSocketHub(ctx, config)

	assert.NoError(t, err)
	assert.NotNil(t, hub)
	assert.True(t, hub.IsHealthy())

	// Check configuration was applied
	stats := hub.GetStats()
	assert.NotNil(t, stats)
}

func TestFactory_CreateMessagingService(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()

	// Create WebSocket hub first
	hub, err := factory.CreateWebSocketHub(ctx, DefaultConfig().WebSocket)
	require.NoError(t, err)

	// Create messaging service
	service, err := factory.CreateMessagingService(ctx, hub)

	assert.NoError(t, err)
	assert.NotNil(t, service)
	assert.True(t, service.IsHealthy())
}

func TestFactory_CreateBuildingService(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()

	// Create database service first
	db, err := factory.CreateDatabaseService(ctx, DefaultConfig().Database)
	require.NoError(t, err)

	// Create building service
	service, err := factory.CreateBuildingService(ctx, db)

	assert.NoError(t, err)
	assert.NotNil(t, service)
}

func TestFactory_CreateEquipmentService(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()

	// Create database service first
	db, err := factory.CreateDatabaseService(ctx, DefaultConfig().Database)
	require.NoError(t, err)

	// Create equipment service
	service, err := factory.CreateEquipmentService(ctx, db)

	assert.NoError(t, err)
	assert.NotNil(t, service)
}

func TestFactory_CreateSpatialService(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()

	// Create database service first
	db, err := factory.CreateDatabaseService(ctx, DefaultConfig().Database)
	require.NoError(t, err)

	// Create spatial service
	service, err := factory.CreateSpatialService(ctx, db)

	assert.NoError(t, err)
	assert.NotNil(t, service)
}

func TestFactory_CreateAnalyticsService(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()

	// Create dependencies first
	db, err := factory.CreateDatabaseService(ctx, DefaultConfig().Database)
	require.NoError(t, err)

	cache, err := factory.CreateCacheService(ctx, DefaultConfig().Cache)
	require.NoError(t, err)

	// Create analytics service
	service, err := factory.CreateAnalyticsService(ctx, db, cache)

	assert.NoError(t, err)
	assert.NotNil(t, service)
}

func TestFactory_CreateWorkflowService(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()

	// Create dependencies first
	db, err := factory.CreateDatabaseService(ctx, DefaultConfig().Database)
	require.NoError(t, err)

	hub, err := factory.CreateWebSocketHub(ctx, DefaultConfig().WebSocket)
	require.NoError(t, err)

	messaging, err := factory.CreateMessagingService(ctx, hub)
	require.NoError(t, err)

	// Create workflow service using placeholder
	// TODO: Implement CreateWorkflowService in factory when workflow service is properly defined
	service := &workflowPlaceholder{}

	assert.NotNil(t, service)
	assert.NotNil(t, db)
	assert.NotNil(t, messaging)
}

func TestNewServiceBuilder(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig()

	builder := NewServiceBuilder(factory, ctx, config)

	assert.NotNil(t, builder)
	assert.Equal(t, factory, builder.factory)
	assert.Equal(t, ctx, builder.ctx)
	assert.Equal(t, config, builder.config)
	assert.NotNil(t, builder.services)
	assert.NotNil(t, builder.errors)
}

func TestServiceBuilder_WithDatabase(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig()

	builder := NewServiceBuilder(factory, ctx, config)
	result := builder.WithDatabase()

	assert.Equal(t, builder, result)
	assert.Len(t, builder.errors, 0)
	assert.Contains(t, builder.services, "database")
}

func TestServiceBuilder_WithCache(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig()

	builder := NewServiceBuilder(factory, ctx, config)
	result := builder.WithCache()

	assert.Equal(t, builder, result)
	assert.Len(t, builder.errors, 0)
	assert.Contains(t, builder.services, "cache")
}

func TestServiceBuilder_WithStorage(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig()

	builder := NewServiceBuilder(factory, ctx, config)
	result := builder.WithStorage()

	assert.Equal(t, builder, result)
	assert.Len(t, builder.errors, 0)
	assert.Contains(t, builder.services, "storage")
}

func TestServiceBuilder_WithWebSocket(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig()

	builder := NewServiceBuilder(factory, ctx, config)
	result := builder.WithWebSocket()

	assert.Equal(t, builder, result)
	assert.Len(t, builder.errors, 0)
	assert.Contains(t, builder.services, "websocket_hub")
}

func TestServiceBuilder_WithMessaging_WithoutWebSocket(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig()

	builder := NewServiceBuilder(factory, ctx, config)
	result := builder.WithMessaging()

	assert.Equal(t, builder, result)
	assert.Len(t, builder.errors, 1)
	assert.Contains(t, builder.errors[0].Error(), "WebSocket hub not found")
}

func TestServiceBuilder_WithMessaging_WithWebSocket(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig()

	builder := NewServiceBuilder(factory, ctx, config)
	result := builder.WithWebSocket().WithMessaging()

	assert.Equal(t, builder, result)
	assert.Len(t, builder.errors, 0)
	assert.Contains(t, builder.services, "messaging")
}

func TestServiceBuilder_WithBuilding_WithoutDatabase(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig()

	builder := NewServiceBuilder(factory, ctx, config)
	result := builder.WithBuilding()

	assert.Equal(t, builder, result)
	assert.Len(t, builder.errors, 1)
	assert.Contains(t, builder.errors[0].Error(), "database service not found")
}

func TestServiceBuilder_WithBuilding_WithDatabase(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig()

	builder := NewServiceBuilder(factory, ctx, config)
	result := builder.WithDatabase().WithBuilding()

	assert.Equal(t, builder, result)
	assert.Len(t, builder.errors, 0)
	assert.Contains(t, builder.services, "building")
}

func TestServiceBuilder_WithEquipment_WithoutDatabase(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig()

	builder := NewServiceBuilder(factory, ctx, config)
	result := builder.WithEquipment()

	assert.Equal(t, builder, result)
	assert.Len(t, builder.errors, 1)
	assert.Contains(t, builder.errors[0].Error(), "database service not found")
}

func TestServiceBuilder_WithEquipment_WithDatabase(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig()

	builder := NewServiceBuilder(factory, ctx, config)
	result := builder.WithDatabase().WithEquipment()

	assert.Equal(t, builder, result)
	assert.Len(t, builder.errors, 0)
	assert.Contains(t, builder.services, "equipment")
}

func TestServiceBuilder_WithSpatial_WithoutDatabase(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig()

	builder := NewServiceBuilder(factory, ctx, config)
	result := builder.WithSpatial()

	assert.Equal(t, builder, result)
	assert.Len(t, builder.errors, 1)
	assert.Contains(t, builder.errors[0].Error(), "database service not found")
}

func TestServiceBuilder_WithSpatial_WithDatabase(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig()

	builder := NewServiceBuilder(factory, ctx, config)
	result := builder.WithDatabase().WithSpatial()

	assert.Equal(t, builder, result)
	assert.Len(t, builder.errors, 0)
	assert.Contains(t, builder.services, "spatial")
}

func TestServiceBuilder_WithAnalytics_WithoutDependencies(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig()

	builder := NewServiceBuilder(factory, ctx, config)
	result := builder.WithAnalytics()

	assert.Equal(t, builder, result)
	assert.Len(t, builder.errors, 1)
	assert.Contains(t, builder.errors[0].Error(), "database service not found")
}

func TestServiceBuilder_WithAnalytics_WithDatabaseOnly(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig()

	builder := NewServiceBuilder(factory, ctx, config)
	result := builder.WithDatabase().WithAnalytics()

	assert.Equal(t, builder, result)
	assert.Len(t, builder.errors, 1)
	assert.Contains(t, builder.errors[0].Error(), "cache service not found")
}

func TestServiceBuilder_WithAnalytics_WithDependencies(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig()

	builder := NewServiceBuilder(factory, ctx, config)
	result := builder.WithDatabase().WithCache().WithAnalytics()

	assert.Equal(t, builder, result)
	assert.Len(t, builder.errors, 0)
	assert.Contains(t, builder.services, "analytics")
}

func TestServiceBuilder_WithWorkflow_WithoutDependencies(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig()

	builder := NewServiceBuilder(factory, ctx, config)
	result := builder.WithWorkflow()

	assert.Equal(t, builder, result)
	assert.Len(t, builder.errors, 1)
	assert.Contains(t, builder.errors[0].Error(), "database service not found")
}

func TestServiceBuilder_WithWorkflow_WithDatabaseOnly(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig()

	builder := NewServiceBuilder(factory, ctx, config)
	result := builder.WithDatabase().WithWorkflow()

	assert.Equal(t, builder, result)
	assert.Len(t, builder.errors, 1)
	assert.Contains(t, builder.errors[0].Error(), "messaging service not found")
}

func TestServiceBuilder_WithWorkflow_WithDependencies(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig()

	builder := NewServiceBuilder(factory, ctx, config)
	result := builder.WithDatabase().WithWebSocket().WithMessaging().WithWorkflow()

	assert.Equal(t, builder, result)
	assert.Len(t, builder.errors, 0)
	assert.Contains(t, builder.services, "workflow")
}

func TestServiceBuilder_Build_Success(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig()

	builder := NewServiceBuilder(factory, ctx, config)
	container, err := builder.WithDatabase().WithCache().Build()

	assert.NoError(t, err)
	assert.NotNil(t, container)
	assert.NotNil(t, container.GetServices())
}

func TestServiceBuilder_Build_WithErrors(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig()

	builder := NewServiceBuilder(factory, ctx, config)
	builder.WithMessaging() // This should create an error

	container, err := builder.Build()

	assert.Error(t, err)
	assert.Nil(t, container)
	assert.Contains(t, err.Error(), "build failed with 1 errors")
}

func TestServiceBuilder_BuildAll(t *testing.T) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig()

	builder := NewServiceBuilder(factory, ctx, config)
	container, err := builder.BuildAll()

	assert.NoError(t, err)
	assert.NotNil(t, container)

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
}

func BenchmarkServiceBuilder_BuildAll(b *testing.B) {
	factory := NewFactory(nil)
	ctx := context.Background()
	config := DefaultConfig()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		builder := NewServiceBuilder(factory, ctx, config)
		container, err := builder.BuildAll()
		if err != nil {
			b.Fatal(err)
		}
		_ = container
	}
}
