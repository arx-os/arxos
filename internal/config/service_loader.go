// Package config provides service configuration loading for ArxOS.
package config

import (
	"fmt"
	"os"
	"path/filepath"

	"gopkg.in/yaml.v3"
)

// ServiceConfigLoader loads service-specific configurations
type ServiceConfigLoader struct {
	configDir string
}

// NewServiceConfigLoader creates a new service config loader
func NewServiceConfigLoader(configDir string) *ServiceConfigLoader {
	return &ServiceConfigLoader{
		configDir: configDir,
	}
}

// LoadServiceConfigs loads all service configurations
func (scl *ServiceConfigLoader) LoadServiceConfigs() (map[string]any, error) {
	serviceConfigs := make(map[string]any)

	servicesDir := filepath.Join(scl.configDir, "services")

	// Load PostGIS config
	if postgisConfig, err := scl.loadYAMLFile(filepath.Join(servicesDir, "postgis.yml")); err == nil {
		serviceConfigs["postgis"] = postgisConfig
	}

	// Load Redis config
	if redisConfig, err := scl.loadYAMLFile(filepath.Join(servicesDir, "redis.yml")); err == nil {
		serviceConfigs["redis"] = redisConfig
	}

	// Load IFC service config
	if ifcConfig, err := scl.loadYAMLFile(filepath.Join(servicesDir, "ifc-service.yml")); err == nil {
		serviceConfigs["ifc_service"] = ifcConfig
	}

	return serviceConfigs, nil
}

// LoadServiceConfig loads a specific service configuration
func (scl *ServiceConfigLoader) LoadServiceConfig(serviceName string) (map[string]any, error) {
	servicePath := filepath.Join(scl.configDir, "services", serviceName+".yml")
	return scl.loadYAMLFile(servicePath)
}

// loadYAMLFile loads a YAML file and returns its contents as a map
func (scl *ServiceConfigLoader) loadYAMLFile(filePath string) (map[string]any, error) {
	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		return nil, fmt.Errorf("service config file not found: %s", filePath)
	}

	data, err := os.ReadFile(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to read service config file %s: %w", filePath, err)
	}

	// Process environment variable substitution
	data = []byte(substituteEnvVars(string(data)))

	var config map[string]any
	if err := yaml.Unmarshal(data, &config); err != nil {
		return nil, fmt.Errorf("failed to parse service config file %s: %w", filePath, err)
	}

	return config, nil
}

// GetServiceConfigValue gets a specific value from a service config
func (scl *ServiceConfigLoader) GetServiceConfigValue(serviceName, key string) (any, error) {
	config, err := scl.LoadServiceConfig(serviceName)
	if err != nil {
		return nil, err
	}

	value, exists := config[key]
	if !exists {
		return nil, fmt.Errorf("key %s not found in service config %s", key, serviceName)
	}

	return value, nil
}

// ListAvailableServices returns a list of available service config files
func (scl *ServiceConfigLoader) ListAvailableServices() ([]string, error) {
	servicesDir := filepath.Join(scl.configDir, "services")

	if _, err := os.Stat(servicesDir); os.IsNotExist(err) {
		return []string{}, nil
	}

	entries, err := os.ReadDir(servicesDir)
	if err != nil {
		return nil, fmt.Errorf("failed to read services directory: %w", err)
	}

	var services []string
	for _, entry := range entries {
		if !entry.IsDir() && filepath.Ext(entry.Name()) == ".yml" {
			serviceName := entry.Name()[:len(entry.Name())-4] // Remove .yml extension
			services = append(services, serviceName)
		}
	}

	return services, nil
}
