/**
 * Test Server Helper - Manages test server lifecycle
 */

package helpers

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/internal/config"
)

// TestServer manages the test server lifecycle
type TestServer struct {
	app        *app.Container
	config     *config.Config
	server     *http.Server
	httpClient *http.Client
	baseURL    string
}

// NewTestServer creates a new test server
func NewTestServer(cfg *config.Config) (*TestServer, error) {
	// Initialize application container
	container := app.NewContainer()

	// Initialize the container with configuration
	ctx := context.Background()
	err := container.Initialize(ctx, cfg)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize app container: %w", err)
	}

	// Create HTTP client
	httpClient := &http.Client{
		Timeout: 30 * time.Second,
	}

	return &TestServer{
		app:        container,
		config:     cfg,
		httpClient: httpClient,
		baseURL:    "http://localhost:8080", // Simplified for testing
	}, nil
}

// Start starts the test server
func (ts *TestServer) Start() error {
	// Create HTTP server
	ts.server = &http.Server{
		Addr:        "localhost:8080",
		Handler:     http.NewServeMux(), // Placeholder handler
		ReadTimeout: 30 * time.Second,
	}

	// Start server in goroutine
	go func() {
		if err := ts.server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			// Log error but don't fail the test
			fmt.Printf("Test server error: %v\n", err)
		}
	}()

	// Wait for server to be ready
	return ts.waitForServer()
}

// Stop stops the test server
func (ts *TestServer) Stop() error {
	if ts.server != nil {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		return ts.server.Shutdown(ctx)
	}
	return nil
}

// Close closes the test server and cleans up resources
func (ts *TestServer) Close() error {
	if ts.server != nil {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := ts.server.Shutdown(ctx); err != nil {
			return err
		}
	}

	// Note: Container doesn't have Close method, it's managed by Go's GC
	return nil
}

// GetHTTPClient returns the HTTP client
func (ts *TestServer) GetHTTPClient() *http.Client {
	return ts.httpClient
}

// GetBaseURL returns the base URL of the test server
func (ts *TestServer) GetBaseURL() string {
	return ts.baseURL
}

// GetApp returns the application container
func (ts *TestServer) GetApp() *app.Container {
	return ts.app
}

// waitForServer waits for the server to be ready
func (ts *TestServer) waitForServer() error {
	maxRetries := 30
	retryInterval := 1 * time.Second

	for i := 0; i < maxRetries; i++ {
		resp, err := ts.httpClient.Get(ts.baseURL + "/health")
		if err == nil && resp.StatusCode == http.StatusOK {
			resp.Body.Close()
			return nil
		}
		if resp != nil {
			resp.Body.Close()
		}
		time.Sleep(retryInterval)
	}

	return fmt.Errorf("server failed to start within %d seconds", maxRetries)
}

// TestServerManager manages multiple test servers
type TestServerManager struct {
	servers []*TestServer
}

// NewTestServerManager creates a new test server manager
func NewTestServerManager() *TestServerManager {
	return &TestServerManager{
		servers: make([]*TestServer, 0),
	}
}

// AddServer adds a test server to the manager
func (tsm *TestServerManager) AddServer(server *TestServer) {
	tsm.servers = append(tsm.servers, server)
}

// StartAll starts all managed servers
func (tsm *TestServerManager) StartAll() error {
	for i, server := range tsm.servers {
		if err := server.Start(); err != nil {
			// Stop already started servers
			for j := 0; j < i; j++ {
				tsm.servers[j].Stop()
			}
			return fmt.Errorf("failed to start server %d: %w", i, err)
		}
	}
	return nil
}

// StopAll stops all managed servers
func (tsm *TestServerManager) StopAll() error {
	var lastErr error
	for i, server := range tsm.servers {
		if err := server.Stop(); err != nil {
			lastErr = fmt.Errorf("failed to stop server %d: %w", i, err)
		}
	}
	return lastErr
}

// CloseAll closes all managed servers
func (tsm *TestServerManager) CloseAll() error {
	var lastErr error
	for i, server := range tsm.servers {
		if err := server.Close(); err != nil {
			lastErr = fmt.Errorf("failed to close server %d: %w", i, err)
		}
	}
	return lastErr
}

// GetServer returns a server by index
func (tsm *TestServerManager) GetServer(index int) *TestServer {
	if index >= 0 && index < len(tsm.servers) {
		return tsm.servers[index]
	}
	return nil
}

// GetServerCount returns the number of managed servers
func (tsm *TestServerManager) GetServerCount() int {
	return len(tsm.servers)
}
