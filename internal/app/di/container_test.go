package di

import (
	"context"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewContainer(t *testing.T) {
	tests := []struct {
		name   string
		config *Config
		want   *Container
	}{
		{
			name:   "with nil config",
			config: nil,
			want: &Container{
				config:     DefaultConfig(),
				services:   make(map[string]interface{}),
				singletons: make(map[string]interface{}),
				cleanup:    make([]func() error, 0),
			},
		},
		{
			name:   "with custom config",
			config: &Config{Development: true},
			want: &Container{
				config:     &Config{Development: true},
				services:   make(map[string]interface{}),
				singletons: make(map[string]interface{}),
				cleanup:    make([]func() error, 0),
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := NewContainer(tt.config)
			assert.Equal(t, tt.want.config, got.config)
			assert.NotNil(t, got.services)
			assert.NotNil(t, got.singletons)
			assert.NotNil(t, got.cleanup)
			assert.False(t, got.initialized)
		})
	}
}

func TestDefaultConfig(t *testing.T) {
	config := DefaultConfig()

	assert.Equal(t, "localhost", config.Database.Host)
	assert.Equal(t, 5432, config.Database.Port)
	assert.Equal(t, "arxos", config.Database.Database)
	assert.Equal(t, "arxos", config.Database.Username)
	assert.Equal(t, "arxos", config.Database.Password)
	assert.Equal(t, "disable", config.Database.SSLMode)

	assert.Equal(t, "localhost", config.Cache.Host)
	assert.Equal(t, 6379, config.Cache.Port)
	assert.Equal(t, "", config.Cache.Password)
	assert.Equal(t, 0, config.Cache.DB)

	assert.Equal(t, "local", config.Storage.Type)
	assert.Equal(t, "./storage", config.Storage.Path)

	assert.Equal(t, 1024, config.WebSocket.ReadBufferSize)
	assert.Equal(t, 1024, config.WebSocket.WriteBufferSize)
	assert.Equal(t, 54, config.WebSocket.PingPeriod)
	assert.Equal(t, 60, config.WebSocket.PongWait)
	assert.Equal(t, 10, config.WebSocket.WriteWait)
	assert.Equal(t, 512, config.WebSocket.MaxMessageSize)

	assert.True(t, config.Development)
}

func TestContainer_Initialize(t *testing.T) {
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
			container := NewContainer(tt.config)
			ctx := context.Background()

			err := container.Initialize(ctx)

			if tt.wantErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.True(t, container.initialized)

				// Verify services are registered
				services := container.GetServices()
				assert.NotNil(t, services)

				webSocketHub := container.GetWebSocketHub()
				assert.NotNil(t, webSocketHub)
			}
		})
	}
}

func TestContainer_Initialize_DoubleInitialization(t *testing.T) {
	container := NewContainer(DefaultConfig())
	ctx := context.Background()

	// First initialization should succeed
	err := container.Initialize(ctx)
	require.NoError(t, err)

	// Second initialization should fail
	err = container.Initialize(ctx)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "already initialized")
}

func TestContainer_Register(t *testing.T) {
	container := NewContainer(DefaultConfig())

	// Register a service
	service := "test-service"
	container.Register("test", service)

	// Retrieve the service
	retrieved, err := container.Get("test")
	require.NoError(t, err)
	assert.Equal(t, service, retrieved)
}

func TestContainer_RegisterSingleton(t *testing.T) {
	container := NewContainer(DefaultConfig())

	// Register a singleton
	service := "singleton-service"
	container.RegisterSingleton("singleton", service)

	// Retrieve the singleton
	retrieved, err := container.Get("singleton")
	require.NoError(t, err)
	assert.Equal(t, service, retrieved)
}

func TestContainer_Get_NotFound(t *testing.T) {
	container := NewContainer(DefaultConfig())

	// Try to get non-existent service
	_, err := container.Get("nonexistent")
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "not found")
}

func TestContainer_MustGet_Panic(t *testing.T) {
	container := NewContainer(DefaultConfig())

	// MustGet should panic for non-existent service
	assert.Panics(t, func() {
		container.MustGet("nonexistent")
	})
}

func TestContainer_Close(t *testing.T) {
	container := NewContainer(DefaultConfig())
	ctx := context.Background()

	// Initialize container
	err := container.Initialize(ctx)
	require.NoError(t, err)

	// Close container
	err = container.Close()
	assert.NoError(t, err)
	assert.False(t, container.initialized)
}

func TestContainer_Close_NotInitialized(t *testing.T) {
	container := NewContainer(DefaultConfig())

	// Close uninitialized container should not error
	err := container.Close()
	assert.NoError(t, err)
}

func TestContainer_GetServices_NotInitialized(t *testing.T) {
	container := NewContainer(DefaultConfig())

	// GetServices should panic if not initialized
	assert.Panics(t, func() {
		container.GetServices()
	})
}

func TestContainer_GetWebSocketHub_NotInitialized(t *testing.T) {
	container := NewContainer(DefaultConfig())

	// GetWebSocketHub should panic if not initialized
	assert.Panics(t, func() {
		container.GetWebSocketHub()
	})
}

func TestContainer_ConcurrentAccess(t *testing.T) {
	container := NewContainer(DefaultConfig())
	ctx := context.Background()

	// Initialize container
	err := container.Initialize(ctx)
	require.NoError(t, err)

	// Test concurrent access
	done := make(chan bool, 10)

	for i := 0; i < 10; i++ {
		go func() {
			defer func() { done <- true }()

			// Concurrent reads should not panic
			services := container.GetServices()
			assert.NotNil(t, services)

			webSocketHub := container.GetWebSocketHub()
			assert.NotNil(t, webSocketHub)
		}()
	}

	// Wait for all goroutines to complete
	for i := 0; i < 10; i++ {
		<-done
	}
}

func TestContainer_ServiceHealth(t *testing.T) {
	container := NewContainer(DefaultConfig())
	ctx := context.Background()

	// Initialize container
	err := container.Initialize(ctx)
	require.NoError(t, err)

	// Get services and check health
	services := container.GetServices()

	// All services should be healthy (placeholder implementations)
	assert.True(t, services.Database.IsHealthy())
	assert.True(t, services.Cache.IsHealthy())
	assert.True(t, services.Storage.IsHealthy())
	assert.True(t, services.Messaging.IsHealthy())
}

func TestContainer_ServiceStats(t *testing.T) {
	container := NewContainer(DefaultConfig())
	ctx := context.Background()

	// Initialize container
	err := container.Initialize(ctx)
	require.NoError(t, err)

	// Get services and check stats
	services := container.GetServices()

	// All services should return stats
	dbStats := services.Database.GetStats()
	assert.NotNil(t, dbStats)

	cacheStats := services.Cache.GetStats()
	assert.NotNil(t, cacheStats)

	storageStats := services.Storage.GetStats()
	assert.NotNil(t, storageStats)

	messagingStats := services.Messaging.GetStats()
	assert.NotNil(t, messagingStats)
}

func BenchmarkContainer_Initialize(b *testing.B) {
	config := DefaultConfig()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		container := NewContainer(config)
		ctx := context.Background()
		container.Initialize(ctx)
	}
}

func BenchmarkContainer_GetServices(b *testing.B) {
	container := NewContainer(DefaultConfig())
	ctx := context.Background()
	container.Initialize(ctx)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		services := container.GetServices()
		_ = services
	}
}

func BenchmarkContainer_Register(b *testing.B) {
	container := NewContainer(DefaultConfig())

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		container.Register("test", "service")
	}
}
