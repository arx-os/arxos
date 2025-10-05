package config

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewServiceConfigLoader(t *testing.T) {
	loader := NewServiceConfigLoader("test-configs")
	assert.Equal(t, "test-configs", loader.configDir)
}

func TestLoadServiceConfigs(t *testing.T) {
	// Create temporary directory structure
	tmpDir := t.TempDir()
	servicesDir := filepath.Join(tmpDir, "services")
	err := os.MkdirAll(servicesDir, 0755)
	require.NoError(t, err)

	// Create test service config files
	postgisConfig := `postgis:
  host: localhost
  port: 5432
  database: test_db
  user: test_user
  ssl_mode: disable
  srid: 900913`

	redisConfig := `redis:
  host: localhost
  port: 6379
  db: 0
  password: test_password`

	ifcConfig := `ifc_service:
  enabled: true
  url: http://localhost:5000
  timeout: 30s
  retries: 3`

	// Write config files
	err = os.WriteFile(filepath.Join(servicesDir, "postgis.yml"), []byte(postgisConfig), 0644)
	require.NoError(t, err)
	err = os.WriteFile(filepath.Join(servicesDir, "redis.yml"), []byte(redisConfig), 0644)
	require.NoError(t, err)
	err = os.WriteFile(filepath.Join(servicesDir, "ifc-service.yml"), []byte(ifcConfig), 0644)
	require.NoError(t, err)

	// Test loading service configs
	loader := NewServiceConfigLoader(tmpDir)
	configs, err := loader.LoadServiceConfigs()
	require.NoError(t, err)

	// Verify all services were loaded
	assert.Contains(t, configs, "postgis")
	assert.Contains(t, configs, "redis")
	assert.Contains(t, configs, "ifc_service")

	// Verify postgis config structure
	postgis, ok := configs["postgis"].(map[string]interface{})
	require.True(t, ok)
	postgisData, ok := postgis["postgis"].(map[string]interface{})
	require.True(t, ok)
	assert.Equal(t, "localhost", postgisData["host"])
	assert.Equal(t, 5432, postgisData["port"])
	assert.Equal(t, "test_db", postgisData["database"])

	// Verify redis config structure
	redis, ok := configs["redis"].(map[string]interface{})
	require.True(t, ok)
	redisData, ok := redis["redis"].(map[string]interface{})
	require.True(t, ok)
	assert.Equal(t, "localhost", redisData["host"])
	assert.Equal(t, 6379, redisData["port"])

	// Verify ifc config structure
	ifc, ok := configs["ifc_service"].(map[string]interface{})
	require.True(t, ok)
	ifcData, ok := ifc["ifc_service"].(map[string]interface{})
	require.True(t, ok)
	assert.Equal(t, true, ifcData["enabled"])
	assert.Equal(t, "http://localhost:5000", ifcData["url"])
}

func TestLoadServiceConfig(t *testing.T) {
	// Create temporary directory structure
	tmpDir := t.TempDir()
	servicesDir := filepath.Join(tmpDir, "services")
	err := os.MkdirAll(servicesDir, 0755)
	require.NoError(t, err)

	// Create test service config file
	configContent := `postgis:
  host: test-host
  port: 5433
  database: test_database
  user: test_user
  ssl_mode: require
  srid: 4326`

	err = os.WriteFile(filepath.Join(servicesDir, "postgis.yml"), []byte(configContent), 0644)
	require.NoError(t, err)

	// Test loading specific service config
	loader := NewServiceConfigLoader(tmpDir)
	config, err := loader.LoadServiceConfig("postgis")
	require.NoError(t, err)

	// Verify config structure
	postgis, ok := config["postgis"].(map[string]interface{})
	require.True(t, ok)
	assert.Equal(t, "test-host", postgis["host"])
	assert.Equal(t, 5433, postgis["port"])
	assert.Equal(t, "test_database", postgis["database"])
	assert.Equal(t, "test_user", postgis["user"])
	assert.Equal(t, "require", postgis["ssl_mode"])
	assert.Equal(t, 4326, postgis["srid"])
}

func TestLoadServiceConfig_NotFound(t *testing.T) {
	tmpDir := t.TempDir()
	loader := NewServiceConfigLoader(tmpDir)

	_, err := loader.LoadServiceConfig("nonexistent")
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "service config file not found")
}

func TestLoadServiceConfig_InvalidYAML(t *testing.T) {
	// Create temporary directory structure
	tmpDir := t.TempDir()
	servicesDir := filepath.Join(tmpDir, "services")
	err := os.MkdirAll(servicesDir, 0755)
	require.NoError(t, err)

	// Create invalid YAML file
	invalidYAML := `postgis:
  host: localhost
  port: 5432
  database: test_db
  user: test_user
  ssl_mode: disable
  srid: 900913
invalid_yaml: [unclosed`

	err = os.WriteFile(filepath.Join(servicesDir, "postgis.yml"), []byte(invalidYAML), 0644)
	require.NoError(t, err)

	// Test loading invalid config
	loader := NewServiceConfigLoader(tmpDir)
	_, err = loader.LoadServiceConfig("postgis")
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "failed to parse service config file")
}

func TestGetServiceConfigValue(t *testing.T) {
	// Create temporary directory structure
	tmpDir := t.TempDir()
	servicesDir := filepath.Join(tmpDir, "services")
	err := os.MkdirAll(servicesDir, 0755)
	require.NoError(t, err)

	// Create test service config file
	configContent := `postgis:
  host: test-host
  port: 5432
  database: test_db`

	err = os.WriteFile(filepath.Join(servicesDir, "postgis.yml"), []byte(configContent), 0644)
	require.NoError(t, err)

	// Test getting specific values
	loader := NewServiceConfigLoader(tmpDir)

	// Test getting existing value
	host, err := loader.GetServiceConfigValue("postgis", "host")
	require.NoError(t, err)
	assert.Equal(t, "test-host", host)

	// Test getting non-existent key
	_, err = loader.GetServiceConfigValue("postgis", "nonexistent")
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "key nonexistent not found")

	// Test getting from non-existent service
	_, err = loader.GetServiceConfigValue("nonexistent", "host")
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "service config file not found")
}

func TestListAvailableServices(t *testing.T) {
	// Create temporary directory structure
	tmpDir := t.TempDir()
	servicesDir := filepath.Join(tmpDir, "services")
	err := os.MkdirAll(servicesDir, 0755)
	require.NoError(t, err)

	// Create test service config files
	services := []string{"postgis", "redis", "ifc-service", "nginx"}
	for _, service := range services {
		configContent := service + ":\n  enabled: true"
		err = os.WriteFile(filepath.Join(servicesDir, service+".yml"), []byte(configContent), 0644)
		require.NoError(t, err)
	}

	// Create a non-YAML file (should be ignored)
	err = os.WriteFile(filepath.Join(servicesDir, "readme.txt"), []byte("This is a readme"), 0644)
	require.NoError(t, err)

	// Test listing services
	loader := NewServiceConfigLoader(tmpDir)
	availableServices, err := loader.ListAvailableServices()
	require.NoError(t, err)

	// Verify all services are listed
	assert.Len(t, availableServices, 4)
	assert.Contains(t, availableServices, "postgis")
	assert.Contains(t, availableServices, "redis")
	assert.Contains(t, availableServices, "ifc-service")
	assert.Contains(t, availableServices, "nginx")
}

func TestListAvailableServices_NoServicesDir(t *testing.T) {
	tmpDir := t.TempDir()
	loader := NewServiceConfigLoader(tmpDir)

	services, err := loader.ListAvailableServices()
	require.NoError(t, err)
	assert.Empty(t, services)
}

func TestLoadServiceConfigs_EmptyServicesDir(t *testing.T) {
	tmpDir := t.TempDir()
	servicesDir := filepath.Join(tmpDir, "services")
	err := os.MkdirAll(servicesDir, 0755)
	require.NoError(t, err)

	loader := NewServiceConfigLoader(tmpDir)
	configs, err := loader.LoadServiceConfigs()
	require.NoError(t, err)
	assert.Empty(t, configs)
}

func TestLoadServiceConfigs_EnvironmentVariableSubstitution(t *testing.T) {
	// Set environment variable
	os.Setenv("TEST_DB_HOST", "env-host")
	os.Setenv("TEST_DB_PORT", "5433")
	defer func() {
		os.Unsetenv("TEST_DB_HOST")
		os.Unsetenv("TEST_DB_PORT")
	}()

	// Create temporary directory structure
	tmpDir := t.TempDir()
	servicesDir := filepath.Join(tmpDir, "services")
	err := os.MkdirAll(servicesDir, 0755)
	require.NoError(t, err)

	// Create config with environment variable substitution
	configContent := `postgis:
  host: "${TEST_DB_HOST:-localhost}"
  port: ${TEST_DB_PORT:-5432}
  database: test_db`

	err = os.WriteFile(filepath.Join(servicesDir, "postgis.yml"), []byte(configContent), 0644)
	require.NoError(t, err)

	// Test loading with environment variable substitution
	loader := NewServiceConfigLoader(tmpDir)
	config, err := loader.LoadServiceConfig("postgis")
	require.NoError(t, err)

	// Verify environment variables were substituted
	postgis, ok := config["postgis"].(map[string]interface{})
	require.True(t, ok)
	assert.Equal(t, "env-host", postgis["host"])
	assert.Equal(t, 5433, postgis["port"])
}
