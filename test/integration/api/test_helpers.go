package integration

import (
	"context"
	"net/http/httptest"
	"os"
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
		Storage: config.StorageConfig{
			Backend:   "local",
			LocalPath: tmpDir + "/data",
			Data: config.DataConfig{
				BasePath:        stateDir,
				RepositoriesDir: "repositories",
				CacheDir:        "cache",
				LogsDir:         "logs",
				TempDir:         "temp",
			},
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
		IFC: config.IFCConfig{
			Service: config.IFCServiceConfig{
				Enabled: true,
				URL:     "http://localhost:5001", // Default IFC service URL
				Timeout: "30s",
				Retries: 3,
			},
		},
	}

	// Override IFC service URL from environment if set
	if ifcURL := os.Getenv("ARXOS_IFC_SERVICE_URL"); ifcURL != "" {
		cfg.IFC.Service.URL = ifcURL
	}

	// Initialize container
	container := app.NewContainer()
	err := container.Initialize(context.Background(), cfg)
	if err != nil {
		t.Skipf("Cannot initialize container (database may not be available): %v", err)
		return nil, nil
	}

	// Create JWT manager for authentication
	jwtManager := container.GetJWTManager()
	if jwtManager == nil {
		t.Skip("JWT manager not available in container")
		return nil, nil
	}

	// Create router config with JWT manager
	routerConfig := &httpRouter.RouterConfig{
		Container:  container,
		JWTManager: jwtManager,
	}
	r := httpRouter.NewRouter(routerConfig)

	// Create test server
	server := httptest.NewServer(r)

	return server, container
}
