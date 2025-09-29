package di

import (
	"context"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestGetServiceLocator(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	
	locator1 := GetServiceLocator()
	locator2 := GetServiceLocator()
	
	// Should return the same instance
	assert.Equal(t, locator1, locator2)
	assert.NotNil(t, locator1)
}

func TestServiceLocator_SetContainer(t *testing.T) {
	locator := GetServiceLocator()
	container := NewContainer(DefaultConfig())
	
	locator.SetContainer(container)
	
	assert.Equal(t, container, locator.container)
}

func TestServiceLocator_Initialize(t *testing.T) {
	tests := []struct {
		name    string
		config  *Config
		wantErr bool
	}{
		{
			name:    "successful initialization",
			config:  DefaultConfig(),
			wantErr: false,
		},
		{
			name:    "custom configuration",
			config:  &Config{Development: false},
			wantErr: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Reset global locator
			globalLocator = nil
			locator := GetServiceLocator()
			ctx := context.Background()
			
			err := locator.Initialize(ctx, tt.config)
			
			if tt.wantErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.True(t, locator.IsInitialized())
				assert.NotNil(t, locator.container)
			}
		})
	}
}

func TestServiceLocator_Initialize_DoubleInitialization(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	ctx := context.Background()
	config := DefaultConfig()
	
	// First initialization should succeed
	err := locator.Initialize(ctx, config)
	require.NoError(t, err)
	
	// Second initialization should fail
	err = locator.Initialize(ctx, config)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "already initialized")
}

func TestServiceLocator_InitializeWithBuilder(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	ctx := context.Background()
	config := DefaultConfig()
	
	err := locator.InitializeWithBuilder(ctx, config)
	
	assert.NoError(t, err)
	assert.True(t, locator.IsInitialized())
	assert.NotNil(t, locator.container)
	
	// Verify services are available
	services := locator.GetServices()
	assert.NotNil(t, services)
}

func TestServiceLocator_InitializeWithBuilder_DoubleInitialization(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	ctx := context.Background()
	config := DefaultConfig()
	
	// First initialization should succeed
	err := locator.InitializeWithBuilder(ctx, config)
	require.NoError(t, err)
	
	// Second initialization should fail
	err = locator.InitializeWithBuilder(ctx, config)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "already initialized")
}

func TestServiceLocator_GetServices_NotInitialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	
	// GetServices should panic if not initialized
	assert.Panics(t, func() {
		locator.GetServices()
	})
}

func TestServiceLocator_GetWebSocketHub_NotInitialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	
	// GetWebSocketHub should panic if not initialized
	assert.Panics(t, func() {
		locator.GetWebSocketHub()
	})
}

func TestServiceLocator_GetDatabase_NotInitialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	
	// GetDatabase should panic if not initialized
	assert.Panics(t, func() {
		locator.GetDatabase()
	})
}

func TestServiceLocator_GetCache_NotInitialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	
	// GetCache should panic if not initialized
	assert.Panics(t, func() {
		locator.GetCache()
	})
}

func TestServiceLocator_GetStorage_NotInitialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	
	// GetStorage should panic if not initialized
	assert.Panics(t, func() {
		locator.GetStorage()
	})
}

func TestServiceLocator_GetMessaging_NotInitialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	
	// GetMessaging should panic if not initialized
	assert.Panics(t, func() {
		locator.GetMessaging()
	})
}

func TestServiceLocator_GetBuildingService_NotInitialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	
	// GetBuildingService should panic if not initialized
	assert.Panics(t, func() {
		locator.GetBuildingService()
	})
}

func TestServiceLocator_GetEquipmentService_NotInitialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	
	// GetEquipmentService should panic if not initialized
	assert.Panics(t, func() {
		locator.GetEquipmentService()
	})
}

func TestServiceLocator_GetSpatialService_NotInitialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	
	// GetSpatialService should panic if not initialized
	assert.Panics(t, func() {
		locator.GetSpatialService()
	})
}

func TestServiceLocator_GetAnalyticsService_NotInitialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	
	// GetAnalyticsService should panic if not initialized
	assert.Panics(t, func() {
		locator.GetAnalyticsService()
	})
}

func TestServiceLocator_GetWorkflowService_NotInitialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	
	// GetWorkflowService should panic if not initialized
	assert.Panics(t, func() {
		locator.GetWorkflowService()
	})
}

func TestServiceLocator_GetServices_Initialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	ctx := context.Background()
	config := DefaultConfig()
	
	err := locator.Initialize(ctx, config)
	require.NoError(t, err)
	
	services := locator.GetServices()
	assert.NotNil(t, services)
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

func TestServiceLocator_GetWebSocketHub_Initialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	ctx := context.Background()
	config := DefaultConfig()
	
	err := locator.Initialize(ctx, config)
	require.NoError(t, err)
	
	hub := locator.GetWebSocketHub()
	assert.NotNil(t, hub)
	assert.True(t, hub.IsHealthy())
}

func TestServiceLocator_GetDatabase_Initialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	ctx := context.Background()
	config := DefaultConfig()
	
	err := locator.Initialize(ctx, config)
	require.NoError(t, err)
	
	db := locator.GetDatabase()
	assert.NotNil(t, db)
	assert.True(t, db.IsHealthy())
}

func TestServiceLocator_GetCache_Initialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	ctx := context.Background()
	config := DefaultConfig()
	
	err := locator.Initialize(ctx, config)
	require.NoError(t, err)
	
	cache := locator.GetCache()
	assert.NotNil(t, cache)
	assert.True(t, cache.IsHealthy())
}

func TestServiceLocator_GetStorage_Initialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	ctx := context.Background()
	config := DefaultConfig()
	
	err := locator.Initialize(ctx, config)
	require.NoError(t, err)
	
	storage := locator.GetStorage()
	assert.NotNil(t, storage)
	assert.True(t, storage.IsHealthy())
}

func TestServiceLocator_GetMessaging_Initialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	ctx := context.Background()
	config := DefaultConfig()
	
	err := locator.Initialize(ctx, config)
	require.NoError(t, err)
	
	messaging := locator.GetMessaging()
	assert.NotNil(t, messaging)
	assert.True(t, messaging.IsHealthy())
}

func TestServiceLocator_GetBuildingService_Initialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	ctx := context.Background()
	config := DefaultConfig()
	
	err := locator.Initialize(ctx, config)
	require.NoError(t, err)
	
	building := locator.GetBuildingService()
	assert.NotNil(t, building)
}

func TestServiceLocator_GetEquipmentService_Initialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	ctx := context.Background()
	config := DefaultConfig()
	
	err := locator.Initialize(ctx, config)
	require.NoError(t, err)
	
	equipment := locator.GetEquipmentService()
	assert.NotNil(t, equipment)
}

func TestServiceLocator_GetSpatialService_Initialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	ctx := context.Background()
	config := DefaultConfig()
	
	err := locator.Initialize(ctx, config)
	require.NoError(t, err)
	
	spatial := locator.GetSpatialService()
	assert.NotNil(t, spatial)
}

func TestServiceLocator_GetAnalyticsService_Initialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	ctx := context.Background()
	config := DefaultConfig()
	
	err := locator.Initialize(ctx, config)
	require.NoError(t, err)
	
	analytics := locator.GetAnalyticsService()
	assert.NotNil(t, analytics)
}

func TestServiceLocator_GetWorkflowService_Initialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	ctx := context.Background()
	config := DefaultConfig()
	
	err := locator.Initialize(ctx, config)
	require.NoError(t, err)
	
	workflow := locator.GetWorkflowService()
	assert.NotNil(t, workflow)
}

func TestServiceLocator_Close(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	ctx := context.Background()
	config := DefaultConfig()
	
	err := locator.Initialize(ctx, config)
	require.NoError(t, err)
	
	err = locator.Close()
	assert.NoError(t, err)
	assert.False(t, locator.IsInitialized())
	assert.Nil(t, locator.container)
}

func TestServiceLocator_Close_NotInitialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	
	err := locator.Close()
	assert.NoError(t, err)
}

func TestServiceLocator_IsInitialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	
	// Initially not initialized
	assert.False(t, locator.IsInitialized())
	
	// Initialize
	ctx := context.Background()
	config := DefaultConfig()
	err := locator.Initialize(ctx, config)
	require.NoError(t, err)
	
	// Now initialized
	assert.True(t, locator.IsInitialized())
	
	// Close
	err = locator.Close()
	require.NoError(t, err)
	
	// Not initialized again
	assert.False(t, locator.IsInitialized())
}

func TestServiceLocator_GetStats_NotInitialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	
	stats := locator.GetStats()
	assert.Equal(t, "not_initialized", stats["status"])
}

func TestServiceLocator_GetStats_Initialized(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	ctx := context.Background()
	config := DefaultConfig()
	
	err := locator.Initialize(ctx, config)
	require.NoError(t, err)
	
	stats := locator.GetStats()
	assert.Equal(t, "initialized", stats["status"])
	assert.Contains(t, stats, "services")
	
	services := stats["services"].(map[string]interface{})
	assert.Contains(t, services, "database")
	assert.Contains(t, services, "cache")
	assert.Contains(t, services, "storage")
	assert.Contains(t, services, "messaging")
	assert.Contains(t, services, "websocket")
}

func TestServiceLocator_ConcurrentAccess(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	ctx := context.Background()
	config := DefaultConfig()
	
	err := locator.Initialize(ctx, config)
	require.NoError(t, err)
	
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
		}()
	}
	
	// Wait for all goroutines to complete
	for i := 0; i < 10; i++ {
		<-done
	}
}

// Test global convenience functions
func TestGlobalConvenienceFunctions(t *testing.T) {
	// Reset global locator
	globalLocator = nil
	ctx := context.Background()
	config := DefaultConfig()
	
	locator := GetServiceLocator()
	err := locator.Initialize(ctx, config)
	require.NoError(t, err)
	
	// Test global functions
	assert.NotNil(t, GetDatabase())
	assert.NotNil(t, GetCache())
	assert.NotNil(t, GetStorage())
	assert.NotNil(t, GetMessaging())
	assert.NotNil(t, GetBuildingService())
	assert.NotNil(t, GetEquipmentService())
	assert.NotNil(t, GetSpatialService())
	assert.NotNil(t, GetAnalyticsService())
	assert.NotNil(t, GetWorkflowService())
	assert.NotNil(t, GetWebSocketHub())
	assert.NotNil(t, GetServices())
}

func BenchmarkServiceLocator_GetServices(b *testing.B) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	ctx := context.Background()
	config := DefaultConfig()
	
	err := locator.Initialize(ctx, config)
	if err != nil {
		b.Fatal(err)
	}
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		services := locator.GetServices()
		_ = services
	}
}

func BenchmarkServiceLocator_GetDatabase(b *testing.B) {
	// Reset global locator
	globalLocator = nil
	locator := GetServiceLocator()
	ctx := context.Background()
	config := DefaultConfig()
	
	err := locator.Initialize(ctx, config)
	if err != nil {
		b.Fatal(err)
	}
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		db := locator.GetDatabase()
		_ = db
	}
}
