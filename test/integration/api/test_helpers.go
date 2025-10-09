package integration

import (
	"context"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/internal/config"
	httpRouter "github.com/arx-os/arxos/internal/interfaces/http"
)

// setupTestServerWithConfig creates a test server with proper test configuration
func setupTestServerWithConfig(t *testing.T) (*httptest.Server, *app.Container) {
	t.Helper()

	// Create temporary directories for test
	tmpDir := t.TempDir()
	stateDir := tmpDir + "/state"
	cacheDir := tmpDir + "/cache"

	// Load test configuration with proper directories
	cfg := &config.Config{
		Mode:     "test",
		Version:  "test",
		StateDir: stateDir,
		CacheDir: cacheDir,
		PostGIS: config.PostGISConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "arxos_test",
			User:     "arxos_test",
			Password: "test_password",
			SSLMode:  "disable",
		},
		Security: config.SecurityConfig{
			JWTSecret:  "test-secret-key-for-testing-only",
			JWTExpiry:  24 * time.Hour,
			EnableAuth: false, // Disable auth for simpler testing
			EnableTLS:  false,
		},
		Database: config.DatabaseConfig{
			MaxOpenConns:    10,
			MaxIdleConns:    5,
			ConnMaxLifetime: 5 * time.Minute,
		},
		TUI: config.TUIConfig{
			Enabled:        false, // Not needed for API tests
			Theme:          "dark",
			UpdateInterval: "5s",
		},
		Features: config.FeatureFlags{
			Analytics: false,
		},
		Cloud: config.CloudConfig{
			Enabled:     false,
			BaseURL:     "",
			SyncEnabled: false,
		},
	}

	// Initialize container
	container := app.NewContainer()
	err := container.Initialize(context.Background(), cfg)
	if err != nil {
		t.Skipf("Cannot initialize container (database may not be available): %v", err)
		return nil, nil
	}

	// Create router config
	routerConfig := &httpRouter.RouterConfig{
		Container: container,
	}
	r := httpRouter.NewRouter(routerConfig)

	// Create test server
	server := httptest.NewServer(r)

	return server, container
}
