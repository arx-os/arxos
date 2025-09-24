//go:build integration
// +build integration

package integration

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
	"time"

	"github.com/stretchr/testify/require"

	"github.com/arx-os/arxos/internal/api"
	"github.com/arx-os/arxos/internal/api/services"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/handlers/web"
)

// TestConfig holds configuration for integration tests
type TestConfig struct {
	Database *database.DatabaseConfig
	Services *api.Services
	Handler  *web.Handler
	Router   http.Handler
	Server   *httptest.Server
}

// setupTestEnvironment creates a complete test environment
func setupTestEnvironment(t *testing.T) *TestConfig {
	ctx := context.Background()

	// Setup test database
	dbConfig := setupTestDatabase(t)

	// Create database connection
	db, err := database.NewPostGISDB(dbConfig)
	require.NoError(t, err)

	err = db.Connect(ctx)
	require.NoError(t, err)

	// Initialize database schema
	err = db.InitializeSchema(ctx)
	require.NoError(t, err)

	// Create services
	services := setupTestServices(t, db)

	// Create web handler
	handler, err := web.NewHandler(services)
	require.NoError(t, err)

	// Create router
	router := web.NewAuthenticatedRouter(handler)

	// Create test server
	server := httptest.NewServer(router)

	return &TestConfig{
		Database: dbConfig,
		Services: services,
		Handler:  handler,
		Router:   router,
		Server:   server,
	}
}

// setupTestDatabase creates database configuration for testing
func setupTestDatabase(t *testing.T) *database.DatabaseConfig {
	// Check for test database environment variables
	host := os.Getenv("POSTGIS_HOST")
	if host == "" {
		host = "localhost"
	}

	port := 5432
	if portStr := os.Getenv("POSTGIS_PORT"); portStr != "" {
		fmt.Sscanf(portStr, "%d", &port)
	}

	database := os.Getenv("POSTGIS_DB")
	if database == "" {
		database = "arxos_test"
	}

	user := os.Getenv("POSTGIS_USER")
	if user == "" {
		user = "postgres"
	}

	password := os.Getenv("POSTGIS_PASSWORD")
	if password == "" {
		t.Skip("POSTGIS_PASSWORD not set, skipping integration test")
	}

	return &database.DatabaseConfig{
		Type:     "postgis",
		Host:     host,
		Port:     port,
		Database: database,
		User:     user,
		Password: password,
		SSLMode:  "disable",
	}
}

// setupTestServices creates all required services for testing
func setupTestServices(t *testing.T, db database.Database) *api.Services {
	ctx := context.Background()

	// Create auth service
	authService := services.NewAuthService(db)

	// Create user service
	userService := services.NewUserService(authService)

	// Create building service
	buildingService := services.NewBuildingService(db)

	// Create equipment service
	equipmentService := services.NewEquipmentService(db)

	// Create spatial service
	spatialService := services.NewSpatialService(db)

	// Create organization service
	orgService := services.NewOrganizationService(db)

	// Create services struct
	services := &api.Services{
		DB:           db,
		Auth:         authService,
		User:         userService,
		Building:     buildingService,
		Equipment:    equipmentService,
		Spatial:      spatialService,
		Organization: orgService,
	}

	// Create test users
	createTestUsers(t, ctx, services)

	return services
}

// createTestUsers creates test users for integration tests
func createTestUsers(t *testing.T, ctx context.Context, services *api.Services) {
	// Create regular user
	userReq := api.CreateUserRequest{
		Email:    "test@arxos.io",
		Name:     "Test User",
		Password: "test_password",
		Role:     "user",
	}

	_, err := services.User.CreateUser(ctx, userReq)
	require.NoError(t, err)

	// Create admin user
	adminReq := api.CreateUserRequest{
		Email:    "admin@arxos.io",
		Name:     "Admin User",
		Password: "admin_password",
		Role:     "admin",
	}

	_, err = services.User.CreateUser(ctx, adminReq)
	require.NoError(t, err)

	// Create manager user
	managerReq := api.CreateUserRequest{
		Email:    "manager@arxos.io",
		Name:     "Manager User",
		Password: "manager_password",
		Role:     "manager",
	}

	_, err = services.User.CreateUser(ctx, managerReq)
	require.NoError(t, err)
}

// cleanupTestEnvironment cleans up test environment
func (tc *TestConfig) cleanupTestEnvironment() {
	if tc.Server != nil {
		tc.Server.Close()
	}
	if tc.Services != nil && tc.Services.DB != nil {
		tc.Services.DB.Close()
	}
}

// getTestAuthToken gets authentication token for a test user
func (tc *TestConfig) getTestAuthToken(t *testing.T, email, password string) string {
	loginReq := map[string]string{
		"email":    email,
		"password": password,
	}

	resp, err := tc.makeRequest("POST", "/api/auth/login", loginReq, "")
	require.NoError(t, err)
	require.Equal(t, http.StatusOK, resp.StatusCode)

	var loginResp map[string]interface{}
	err = tc.parseJSONResponse(resp, &loginResp)
	require.NoError(t, err)

	token, ok := loginResp["token"].(string)
	require.True(t, ok)
	require.NotEmpty(t, token)

	return token
}

// makeRequest makes an HTTP request to the test server
func (tc *TestConfig) makeRequest(method, path string, body interface{}, token string) (*http.Response, error) {
	var req *http.Request
	var err error

	if body != nil {
		jsonBody, err := json.Marshal(body)
		if err != nil {
			return nil, err
		}
		req, err = http.NewRequest(method, tc.Server.URL+path, bytes.NewReader(jsonBody))
		if err != nil {
			return nil, err
		}
		req.Header.Set("Content-Type", "application/json")
	} else {
		req, err = http.NewRequest(method, tc.Server.URL+path, nil)
		if err != nil {
			return nil, err
		}
	}

	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}

	client := &http.Client{Timeout: 30 * time.Second}
	return client.Do(req)
}

// parseJSONResponse parses JSON response body
func (tc *TestConfig) parseJSONResponse(resp *http.Response, target interface{}) error {
	defer resp.Body.Close()
	return json.NewDecoder(resp.Body).Decode(target)
}

// TestUser represents a test user for integration tests
type TestUser struct {
	Email    string
	Password string
	Role     string
	Token    string
}

// getTestUsers returns test users with their tokens
func (tc *TestConfig) getTestUsers(t *testing.T) map[string]*TestUser {
	users := map[string]*TestUser{
		"user": {
			Email:    "test@arxos.io",
			Password: "test_password",
			Role:     "user",
		},
		"admin": {
			Email:    "admin@arxos.io",
			Password: "admin_password",
			Role:     "admin",
		},
		"manager": {
			Email:    "manager@arxos.io",
			Password: "manager_password",
			Role:     "manager",
		},
	}

	// Get tokens for all users
	for _, user := range users {
		user.Token = tc.getTestAuthToken(t, user.Email, user.Password)
	}

	return users
}
