package config

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

// Manager manages configuration loading, validation, and updates
type Manager struct {
	config          *Config
	templateManager *ConfigTemplateManager
	loader          *ConfigLoader
	validator       *ConfigValidator
	mu              sync.RWMutex
	configPath      string
	watchEnabled    bool
	watchInterval   time.Duration
	updateChan      chan *Config
	stopChan        chan struct{}
}

// NewManager creates a new configuration manager
func NewManager(configPath string) *Manager {
	return &Manager{
		templateManager: NewConfigTemplateManager(filepath.Join(filepath.Dir(configPath), "templates")),
		loader:          NewConfigLoader(),
		validator:       NewConfigValidator(),
		configPath:      configPath,
		watchEnabled:    false,
		watchInterval:   5 * time.Second,
		updateChan:      make(chan *Config, 1),
		stopChan:        make(chan struct{}),
	}
}

// Initialize initializes the configuration manager
func (cm *Manager) Initialize(ctx context.Context) error {
	// Load templates
	if err := cm.templateManager.LoadTemplates(); err != nil {
		return fmt.Errorf("failed to load configuration templates: %w", err)
	}

	// Load configuration
	if err := cm.LoadConfiguration(); err != nil {
		return fmt.Errorf("failed to load configuration: %w", err)
	}

	// Start watching if enabled
	if cm.watchEnabled {
		go cm.watchConfiguration()
	}

	return nil
}

// LoadConfiguration loads configuration from all sources
func (cm *Manager) LoadConfiguration() error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	// Set up configuration sources
	cm.setupConfigurationSources()

	// Load configuration
	config, err := cm.loader.Load()
	if err != nil {
		return fmt.Errorf("failed to load configuration: %w", err)
	}

	// Validate configuration
	if errors := cm.validator.Validate(config); len(errors) > 0 {
		return fmt.Errorf("configuration validation failed: %v", errors)
	}

	cm.config = config
	return nil
}

// GetConfiguration returns the current configuration
func (cm *Manager) GetConfiguration() *Config {
	cm.mu.RLock()
	defer cm.mu.RUnlock()
	return cm.config
}

// UpdateConfiguration updates the configuration
func (cm *Manager) UpdateConfiguration(config *Config) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	// Validate new configuration
	if errors := cm.validator.Validate(config); len(errors) > 0 {
		return fmt.Errorf("configuration validation failed: %v", errors)
	}

	cm.config = config
	return nil
}

// SaveConfiguration saves the current configuration to file
func (cm *Manager) SaveConfiguration() error {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if cm.config == nil {
		return fmt.Errorf("no configuration to save")
	}

	return cm.saveConfigurationToFile(cm.config, cm.configPath)
}

// LoadFromTemplate loads configuration from a template
func (cm *Manager) LoadFromTemplate(templateName string, variables map[string]any) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	// Get template
	template, err := cm.templateManager.GetTemplate(templateName)
	if err != nil {
		return fmt.Errorf("failed to get template: %w", err)
	}

	// Generate configuration from template
	config, err := cm.generateConfigFromTemplate(template, variables)
	if err != nil {
		return fmt.Errorf("failed to generate configuration from template: %w", err)
	}

	// Validate configuration
	if errors := cm.validator.Validate(config); len(errors) > 0 {
		return fmt.Errorf("configuration validation failed: %v", errors)
	}

	cm.config = config
	return nil
}

// CreateTemplate creates a new configuration template
func (cm *Manager) CreateTemplate(name, description string, environment Environment) (*ConfigTemplate, error) {
	template := cm.templateManager.CreateTemplate(name, description, environment)

	// Save template
	if err := cm.templateManager.SaveTemplate(template); err != nil {
		return nil, fmt.Errorf("failed to save template: %w", err)
	}

	return template, nil
}

// GetTemplate returns a configuration template
func (cm *Manager) GetTemplate(name string) (*ConfigTemplate, error) {
	return cm.templateManager.GetTemplate(name)
}

// ListTemplates returns all available templates
func (cm *Manager) ListTemplates() []*ConfigTemplate {
	return cm.templateManager.ListTemplates()
}

// ValidateConfiguration validates the current configuration
func (cm *Manager) ValidateConfiguration() []ValidationError {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if cm.config == nil {
		return []ValidationError{{
			Field:   "config",
			Value:   "",
			Message: "No configuration loaded",
			Code:    "NO_CONFIG",
		}}
	}

	return cm.validator.Validate(cm.config)
}

// WatchConfiguration enables configuration file watching
func (cm *Manager) WatchConfiguration(interval time.Duration) {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	cm.watchEnabled = true
	cm.watchInterval = interval

	if interval > 0 {
		go cm.watchConfiguration()
	}
}

// StopWatching stops configuration file watching
func (cm *Manager) StopWatching() {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	cm.watchEnabled = false
	close(cm.stopChan)
}

// GetUpdateChannel returns the configuration update channel
func (cm *Manager) GetUpdateChannel() <-chan *Config {
	return cm.updateChan
}

// SetConfigurationPath sets the configuration file path
func (cm *Manager) SetConfigurationPath(path string) {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	cm.configPath = path
}

// GetConfigurationPath returns the configuration file path
func (cm *Manager) GetConfigurationPath() string {
	cm.mu.RLock()
	defer cm.mu.RUnlock()
	return cm.configPath
}

// Private methods

func (cm *Manager) setupConfigurationSources() {
	// Clear existing sources
	cm.loader = NewConfigLoader()

	// Add default source
	cm.loader.AddSource(&DefaultConfigSource{priority: 1})

	// Add environment variables source
	cm.loader.AddSource(&EnvironmentConfigSource{
		prefix:   "ARXOS_",
		priority: 50,
	})

	// Add configuration file source if file exists
	if cm.configPath != "" && cm.fileExists(cm.configPath) {
		cm.loader.AddSource(&FileConfigSource{
			path:     cm.configPath,
			priority: 100,
		})
	}
}

func (cm *Manager) generateConfigFromTemplate(template *ConfigTemplate, variables map[string]any) (*Config, error) {
	// Convert template config to JSON
	templateData, err := json.Marshal(template.Config)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal template config: %w", err)
	}

	// Replace template variables
	templateStr := string(templateData)
	for _, variable := range template.Variables {
		placeholder := fmt.Sprintf("{{%s}}", variable.Name)
		value := variables[variable.Name]

		if value == nil {
			value = variable.Default
		}

		if value == nil && variable.Required {
			return nil, fmt.Errorf("required variable '%s' not provided", variable.Name)
		}

		if value != nil {
			templateStr = strings.ReplaceAll(templateStr, placeholder, fmt.Sprintf("%v", value))
		}
	}

	// Parse the generated configuration
	var config Config
	if err := json.Unmarshal([]byte(templateStr), &config); err != nil {
		return nil, fmt.Errorf("failed to parse generated configuration: %w", err)
	}

	// Set mode based on template environment
	switch template.Environment {
	case EnvDevelopment:
		config.Mode = ModeLocal
	case EnvStaging, EnvInternal, EnvProduction:
		config.Mode = ModeCloud
	default:
		config.Mode = ModeLocal
	}

	return &config, nil
}

func (cm *Manager) saveConfigurationToFile(config *Config, filePath string) error {
	// Ensure directory exists
	dir := filepath.Dir(filePath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create config directory: %w", err)
	}

	// Marshal configuration
	data, err := json.MarshalIndent(config, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal configuration: %w", err)
	}

	// Write to file
	if err := os.WriteFile(filePath, data, 0644); err != nil {
		return fmt.Errorf("failed to write configuration file: %w", err)
	}

	return nil
}

func (cm *Manager) watchConfiguration() {
	ticker := time.NewTicker(cm.watchInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			if err := cm.checkForConfigurationUpdates(); err != nil {
				// Log error but continue watching
				continue
			}
		case <-cm.stopChan:
			return
		}
	}
}

func (cm *Manager) checkForConfigurationUpdates() error {
	// Check if configuration file has been modified
	if !cm.fileExists(cm.configPath) {
		return nil
	}

	// Load configuration
	if err := cm.LoadConfiguration(); err != nil {
		return err
	}

	// Notify about configuration update
	select {
	case cm.updateChan <- cm.config:
	default:
		// Channel is full, skip this update
	}

	return nil
}

func (cm *Manager) fileExists(path string) bool {
	_, err := os.Stat(path)
	return !os.IsNotExist(err)
}

// GetDefaultTemplateForEnvironment returns the default template for an environment
func (cm *Manager) GetDefaultTemplateForEnvironment(environment Environment) *ConfigTemplate {
	return cm.templateManager.GetDefaultTemplateForEnvironment(environment)
}

// ExportConfiguration exports the current configuration to a file
func (cm *Manager) ExportConfiguration(filePath string) error {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if cm.config == nil {
		return fmt.Errorf("no configuration to export")
	}

	return cm.saveConfigurationToFile(cm.config, filePath)
}

// ImportConfiguration imports configuration from a file
func (cm *Manager) ImportConfiguration(filePath string) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	// Load configuration from file
	config, err := cm.loader.LoadFromFile(filePath)
	if err != nil {
		return fmt.Errorf("failed to load configuration from file: %w", err)
	}

	// Validate configuration
	if errors := cm.validator.Validate(config); len(errors) > 0 {
		return fmt.Errorf("configuration validation failed: %v", errors)
	}

	cm.config = config
	return nil
}

// ResetToDefaults resets configuration to default values
func (cm *Manager) ResetToDefaults() error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	// Load default configuration
	config, err := cm.loader.LoadFromMultipleSources([]ConfigSource{
		&DefaultConfigSource{priority: 100},
	})
	if err != nil {
		return fmt.Errorf("failed to load default configuration: %w", err)
	}

	cm.config = config
	return nil
}

// GetConfigurationSummary returns a summary of the current configuration
func (cm *Manager) GetConfigurationSummary() *ConfigurationSummary {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if cm.config == nil {
		return &ConfigurationSummary{
			Mode:        "",
			HasDatabase: false,
			HasAPI:      false,
		}
	}

	summary := &ConfigurationSummary{
		Mode:        string(cm.config.Mode),
		HasDatabase: cm.config.PostGIS.Host != "",
		HasAPI:      cm.config.API.Timeout != 0,
	}

	if cm.config.PostGIS.Host != "" {
		summary.DatabaseHost = cm.config.PostGIS.Host
		summary.DatabasePort = cm.config.PostGIS.Port
		summary.DatabaseName = cm.config.PostGIS.Database
	}

	return summary
}

// ConfigurationSummary provides a summary of the current configuration
type ConfigurationSummary struct {
	Mode         string `json:"mode"`
	HasDatabase  bool   `json:"has_database"`
	HasAPI       bool   `json:"has_api"`
	DatabaseHost string `json:"database_host,omitempty"`
	DatabasePort int    `json:"database_port,omitempty"`
	DatabaseName string `json:"database_name,omitempty"`
}
