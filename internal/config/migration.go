// Package config provides configuration migration utilities for ArxOS.
package config

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"gopkg.in/yaml.v3"
)

// MigrationResult represents the result of a configuration migration
type MigrationResult struct {
	SourcePath string
	TargetPath string
	Success    bool
	Error      error
	Warnings   []string
	Changes    []string
}

// ConfigMigrator handles configuration migrations
type ConfigMigrator struct {
	configDir string
}

// NewConfigMigrator creates a new configuration migrator
func NewConfigMigrator(configDir string) *ConfigMigrator {
	return &ConfigMigrator{
		configDir: configDir,
	}
}

// MigrateAllConfigs migrates all configuration files to the new format
func (cm *ConfigMigrator) MigrateAllConfigs() ([]MigrationResult, error) {
	var results []MigrationResult

	// Migrate environment configs
	envResults, err := cm.migrateEnvironmentConfigs()
	if err != nil {
		return results, fmt.Errorf("failed to migrate environment configs: %w", err)
	}
	results = append(results, envResults...)

	// Migrate service configs
	serviceResults, err := cm.migrateServiceConfigs()
	if err != nil {
		return results, fmt.Errorf("failed to migrate service configs: %w", err)
	}
	results = append(results, serviceResults...)

	return results, nil
}

// MigrateConfig migrates a specific configuration file
func (cm *ConfigMigrator) MigrateConfig(sourcePath, targetPath string) (*MigrationResult, error) {
	result := &MigrationResult{
		SourcePath: sourcePath,
		TargetPath: targetPath,
	}

	// Check if source file exists
	if _, err := os.Stat(sourcePath); os.IsNotExist(err) {
		result.Error = fmt.Errorf("source file does not exist: %s", sourcePath)
		return result, result.Error
	}

	// Read source file
	data, err := os.ReadFile(sourcePath)
	if err != nil {
		result.Error = fmt.Errorf("failed to read source file: %w", err)
		return result, result.Error
	}

	// Parse source file
	var sourceConfig map[string]any
	if err := yaml.Unmarshal(data, &sourceConfig); err != nil {
		result.Error = fmt.Errorf("failed to parse source file: %w", err)
		return result, result.Error
	}

	// Migrate configuration
	migratedConfig, warnings, changes, err := cm.migrateConfigData(sourceConfig, sourcePath)
	if err != nil {
		result.Error = fmt.Errorf("failed to migrate config data: %w", err)
		return result, result.Error
	}

	result.Warnings = warnings
	result.Changes = changes

	// Create target directory if it doesn't exist
	if err := os.MkdirAll(filepath.Dir(targetPath), 0755); err != nil {
		result.Error = fmt.Errorf("failed to create target directory: %w", err)
		return result, result.Error
	}

	// Write migrated configuration
	migratedData, err := yaml.Marshal(migratedConfig)
	if err != nil {
		result.Error = fmt.Errorf("failed to marshal migrated config: %w", err)
		return result, result.Error
	}

	if err := os.WriteFile(targetPath, migratedData, 0644); err != nil {
		result.Error = fmt.Errorf("failed to write target file: %w", err)
		return result, result.Error
	}

	result.Success = true
	return result, nil
}

// migrateEnvironmentConfigs migrates environment configuration files
func (cm *ConfigMigrator) migrateEnvironmentConfigs() ([]MigrationResult, error) {
	var results []MigrationResult

	environments := []string{"development", "production", "test"}
	for _, env := range environments {
		sourcePath := filepath.Join(cm.configDir, fmt.Sprintf("%s.yml", env))
		targetPath := filepath.Join(cm.configDir, "environments", fmt.Sprintf("%s.yml", env))

		if _, err := os.Stat(sourcePath); os.IsNotExist(err) {
			continue // Skip if source doesn't exist
		}

		result, err := cm.MigrateConfig(sourcePath, targetPath)
		if err != nil {
			results = append(results, *result)
			continue
		}

		results = append(results, *result)
	}

	return results, nil
}

// migrateServiceConfigs migrates service configuration files
func (cm *ConfigMigrator) migrateServiceConfigs() ([]MigrationResult, error) {
	var results []MigrationResult

	services := []string{"postgis", "redis", "ifc-service"}
	for _, service := range services {
		sourcePath := filepath.Join(cm.configDir, "services", fmt.Sprintf("%s.yml", service))
		targetPath := filepath.Join(cm.configDir, "services", fmt.Sprintf("%s.yml", service))

		if _, err := os.Stat(sourcePath); os.IsNotExist(err) {
			continue // Skip if source doesn't exist
		}

		result, err := cm.MigrateConfig(sourcePath, targetPath)
		if err != nil {
			results = append(results, *result)
			continue
		}

		results = append(results, *result)
	}

	return results, nil
}

// migrateConfigData migrates configuration data from old format to new format
func (cm *ConfigMigrator) migrateConfigData(source map[string]any, sourcePath string) (map[string]any, []string, []string, error) {
	var warnings []string
	var changes []string
	migrated := make(map[string]any)

	// Copy all fields from source
	for key, value := range source {
		migrated[key] = value
	}

	// Apply specific migrations based on file type
	if strings.Contains(sourcePath, "development") || strings.Contains(sourcePath, "production") || strings.Contains(sourcePath, "test") {
		// Environment config migrations
		envWarnings, envChanges := cm.migrateEnvironmentConfig(migrated)
		warnings = append(warnings, envWarnings...)
		changes = append(changes, envChanges...)
	} else if strings.Contains(sourcePath, "postgis") {
		// PostGIS config migrations
		pgWarnings, pgChanges := cm.migratePostGISConfig(migrated)
		warnings = append(warnings, pgWarnings...)
		changes = append(changes, pgChanges...)
	} else if strings.Contains(sourcePath, "redis") {
		// Redis config migrations
		redisWarnings, redisChanges := cm.migrateRedisConfig(migrated)
		warnings = append(warnings, redisWarnings...)
		changes = append(changes, redisChanges...)
	} else if strings.Contains(sourcePath, "ifc") {
		// IFC service config migrations
		ifcWarnings, ifcChanges := cm.migrateIFCConfig(migrated)
		warnings = append(warnings, ifcWarnings...)
		changes = append(changes, ifcChanges...)
	}

	return migrated, warnings, changes, nil
}

// migrateEnvironmentConfig migrates environment-specific configuration
func (cm *ConfigMigrator) migrateEnvironmentConfig(config map[string]any) ([]string, []string) {
	var warnings []string
	var changes []string

	// Migrate mode field
	if mode, exists := config["mode"]; exists {
		if modeStr, ok := mode.(string); ok {
			switch modeStr {
			case "hybrid":
				config["mode"] = "local" // Default hybrid to local for development
				changes = append(changes, "Changed mode from 'hybrid' to 'local'")
			}
		}
	}

	// Ensure required fields exist
	if _, exists := config["version"]; !exists {
		config["version"] = "0.1.0"
		changes = append(changes, "Added default version")
	}

	if _, exists := config["state_dir"]; !exists {
		config["state_dir"] = ".arxos"
		changes = append(changes, "Added default state_dir")
	}

	if _, exists := config["cache_dir"]; !exists {
		config["cache_dir"] = ".arxos/cache"
		changes = append(changes, "Added default cache_dir")
	}

	return warnings, changes
}

// migratePostGISConfig migrates PostGIS configuration
func (cm *ConfigMigrator) migratePostGISConfig(config map[string]any) ([]string, []string) {
	var warnings []string
	var changes []string

	// Ensure postgis section exists
	if _, exists := config["postgis"]; !exists {
		config["postgis"] = make(map[string]any)
		changes = append(changes, "Added postgis section")
	}

	postgis, ok := config["postgis"].(map[string]any)
	if !ok {
		postgis = make(map[string]any)
		config["postgis"] = postgis
	}

	// Set defaults for required fields
	if _, exists := postgis["host"]; !exists {
		postgis["host"] = "localhost"
		changes = append(changes, "Added default PostGIS host")
	}

	if _, exists := postgis["port"]; !exists {
		postgis["port"] = 5432
		changes = append(changes, "Added default PostGIS port")
	}

	if _, exists := postgis["database"]; !exists {
		postgis["database"] = "arxos"
		changes = append(changes, "Added default PostGIS database")
	}

	if _, exists := postgis["user"]; !exists {
		postgis["user"] = "arxos"
		changes = append(changes, "Added default PostGIS user")
	}

	if _, exists := postgis["ssl_mode"]; !exists {
		postgis["ssl_mode"] = "disable"
		changes = append(changes, "Added default PostGIS SSL mode")
	}

	if _, exists := postgis["srid"]; !exists {
		postgis["srid"] = 900913
		changes = append(changes, "Added default PostGIS SRID")
	}

	return warnings, changes
}

// migrateRedisConfig migrates Redis configuration
func (cm *ConfigMigrator) migrateRedisConfig(config map[string]any) ([]string, []string) {
	var warnings []string
	var changes []string

	// Ensure redis section exists
	if _, exists := config["redis"]; !exists {
		config["redis"] = make(map[string]any)
		changes = append(changes, "Added redis section")
	}

	redis, ok := config["redis"].(map[string]any)
	if !ok {
		redis = make(map[string]any)
		config["redis"] = redis
	}

	// Set defaults for required fields
	if _, exists := redis["host"]; !exists {
		redis["host"] = "localhost"
		changes = append(changes, "Added default Redis host")
	}

	if _, exists := redis["port"]; !exists {
		redis["port"] = 6379
		changes = append(changes, "Added default Redis port")
	}

	if _, exists := redis["db"]; !exists {
		redis["db"] = 0
		changes = append(changes, "Added default Redis database")
	}

	return warnings, changes
}

// migrateIFCConfig migrates IFC service configuration
func (cm *ConfigMigrator) migrateIFCConfig(config map[string]any) ([]string, []string) {
	var warnings []string
	var changes []string

	// Ensure ifc_service section exists
	if _, exists := config["ifc_service"]; !exists {
		config["ifc_service"] = make(map[string]any)
		changes = append(changes, "Added ifc_service section")
	}

	ifc, ok := config["ifc_service"].(map[string]any)
	if !ok {
		ifc = make(map[string]any)
		config["ifc_service"] = ifc
	}

	// Set defaults for required fields
	if _, exists := ifc["enabled"]; !exists {
		ifc["enabled"] = true
		changes = append(changes, "Added default IFC service enabled")
	}

	if _, exists := ifc["url"]; !exists {
		ifc["url"] = "http://localhost:5000"
		changes = append(changes, "Added default IFC service URL")
	}

	if _, exists := ifc["timeout"]; !exists {
		ifc["timeout"] = "30s"
		changes = append(changes, "Added default IFC service timeout")
	}

	if _, exists := ifc["retries"]; !exists {
		ifc["retries"] = 3
		changes = append(changes, "Added default IFC service retries")
	}

	return warnings, changes
}
