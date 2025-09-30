package config

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// ConfigTemplate represents a configuration template
type ConfigTemplate struct {
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Environment Environment            `json:"environment"`
	Config      map[string]interface{} `json:"config"`
	Variables   []TemplateVariable     `json:"variables"`
}

// TemplateVariable represents a variable in a configuration template
type TemplateVariable struct {
	Name         string      `json:"name"`
	Description  string      `json:"description"`
	DefaultValue interface{} `json:"default_value"`
	Required     bool        `json:"required"`
	Type         string      `json:"type"`
}

// ConfigTemplateManager manages configuration templates
type ConfigTemplateManager struct {
	templatesDir string
	templates    map[string]*ConfigTemplate
}

// NewConfigTemplateManager creates a new template manager
func NewConfigTemplateManager(templatesDir string) *ConfigTemplateManager {
	return &ConfigTemplateManager{
		templatesDir: templatesDir,
		templates:    make(map[string]*ConfigTemplate),
	}
}

// LoadTemplates loads all configuration templates from the templates directory
func (ctm *ConfigTemplateManager) LoadTemplates() error {
	if ctm.templatesDir == "" {
		return fmt.Errorf("templates directory not set")
	}

	// Ensure templates directory exists
	if err := os.MkdirAll(ctm.templatesDir, 0755); err != nil {
		return fmt.Errorf("failed to create templates directory: %w", err)
	}

	// Load built-in templates
	ctm.loadBuiltinTemplates()

	// Load templates from files
	return ctm.loadTemplatesFromFiles()
}

// GetTemplate returns a template by name
func (ctm *ConfigTemplateManager) GetTemplate(name string) (*ConfigTemplate, error) {
	template, exists := ctm.templates[name]
	if !exists {
		return nil, fmt.Errorf("template '%s' not found", name)
	}
	return template, nil
}

// ListTemplates returns all available templates
func (ctm *ConfigTemplateManager) ListTemplates() []*ConfigTemplate {
	templates := make([]*ConfigTemplate, 0, len(ctm.templates))
	for _, template := range ctm.templates {
		templates = append(templates, template)
	}
	return templates
}

// SaveTemplate saves a template to file
func (ctm *ConfigTemplateManager) SaveTemplate(template *ConfigTemplate) error {
	if ctm.templatesDir == "" {
		return fmt.Errorf("templates directory not set")
	}

	filename := fmt.Sprintf("%s.json", template.Name)
	filepath := filepath.Join(ctm.templatesDir, filename)

	data, err := json.MarshalIndent(template, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal template: %w", err)
	}

	if err := os.WriteFile(filepath, data, 0644); err != nil {
		return fmt.Errorf("failed to write template file: %w", err)
	}

	ctm.templates[template.Name] = template
	return nil
}

// CreateTemplate creates a new template
func (ctm *ConfigTemplateManager) CreateTemplate(name, description string, environment Environment) *ConfigTemplate {
	template := &ConfigTemplate{
		Name:        name,
		Description: description,
		Environment: environment,
		Config:      make(map[string]interface{}),
		Variables:   make([]TemplateVariable, 0),
	}

	ctm.templates[name] = template
	return template
}

// Private methods

func (ctm *ConfigTemplateManager) loadBuiltinTemplates() {
	// Development template
	devTemplate := ctm.CreateTemplate("development", "Development environment configuration", EnvDevelopment)
	devTemplate.Config = map[string]interface{}{
		"mode": "local",
		"postgis": map[string]interface{}{
			"host":     "{{db_host}}",
			"port":     "{{db_port}}",
			"database": "{{db_name}}",
			"user":     "{{db_user}}",
			"password": "{{db_password}}",
			"ssl_mode": "disable",
		},
		"api": map[string]interface{}{
			"host": "localhost",
			"port": "{{api_port}}",
		},
		"features": map[string]interface{}{
			"debug_mode":      true,
			"verbose_logging": true,
			"offline_mode":    true,
		},
		"telemetry": map[string]interface{}{
			"enabled": false,
		},
	}
	devTemplate.Variables = []TemplateVariable{
		{Name: "db_host", Description: "Database host", DefaultValue: "localhost", Required: true, Type: "string"},
		{Name: "db_port", Description: "Database port", DefaultValue: 5432, Required: true, Type: "int"},
		{Name: "db_name", Description: "Database name", DefaultValue: "arxos_dev", Required: true, Type: "string"},
		{Name: "db_user", Description: "Database user", DefaultValue: "arxos", Required: true, Type: "string"},
		{Name: "db_password", Description: "Database password", DefaultValue: "", Required: false, Type: "string"},
		{Name: "api_port", Description: "API server port", DefaultValue: 8080, Required: true, Type: "int"},
	}

	// Production template
	prodTemplate := ctm.CreateTemplate("production", "Production environment configuration", EnvProduction)
	prodTemplate.Config = map[string]interface{}{
		"mode": "cloud",
		"postgis": map[string]interface{}{
			"host":     "{{db_host}}",
			"port":     "{{db_port}}",
			"database": "{{db_name}}",
			"user":     "{{db_user}}",
			"password": "{{db_password}}",
			"ssl_mode": "require",
		},
		"api": map[string]interface{}{
			"host": "{{api_host}}",
			"port": "{{api_port}}",
		},
		"features": map[string]interface{}{
			"debug_mode":      false,
			"verbose_logging": false,
			"offline_mode":    false,
		},
		"telemetry": map[string]interface{}{
			"enabled": true,
		},
		"security": map[string]interface{}{
			"require_https":   true,
			"session_timeout": "8h",
		},
	}
	prodTemplate.Variables = []TemplateVariable{
		{Name: "db_host", Description: "Database host", DefaultValue: "", Required: true, Type: "string"},
		{Name: "db_port", Description: "Database port", DefaultValue: 5432, Required: true, Type: "int"},
		{Name: "db_name", Description: "Database name", DefaultValue: "", Required: true, Type: "string"},
		{Name: "db_user", Description: "Database user", DefaultValue: "", Required: true, Type: "string"},
		{Name: "db_password", Description: "Database password", DefaultValue: "", Required: true, Type: "string"},
		{Name: "api_host", Description: "API server host", DefaultValue: "0.0.0.0", Required: true, Type: "string"},
		{Name: "api_port", Description: "API server port", DefaultValue: 8080, Required: true, Type: "int"},
	}

	// Staging template
	stagingTemplate := ctm.CreateTemplate("staging", "Staging environment configuration", EnvStaging)
	stagingTemplate.Config = map[string]interface{}{
		"mode": "hybrid",
		"postgis": map[string]interface{}{
			"host":     "{{db_host}}",
			"port":     "{{db_port}}",
			"database": "{{db_name}}",
			"user":     "{{db_user}}",
			"password": "{{db_password}}",
			"ssl_mode": "prefer",
		},
		"api": map[string]interface{}{
			"host": "{{api_host}}",
			"port": "{{api_port}}",
		},
		"features": map[string]interface{}{
			"debug_mode":      true,
			"verbose_logging": true,
			"offline_mode":    false,
		},
		"telemetry": map[string]interface{}{
			"enabled": true,
		},
		"security": map[string]interface{}{
			"require_https":   true,
			"session_timeout": "4h",
		},
	}
	stagingTemplate.Variables = []TemplateVariable{
		{Name: "db_host", Description: "Database host", DefaultValue: "", Required: true, Type: "string"},
		{Name: "db_port", Description: "Database port", DefaultValue: 5432, Required: true, Type: "int"},
		{Name: "db_name", Description: "Database name", DefaultValue: "", Required: true, Type: "string"},
		{Name: "db_user", Description: "Database user", DefaultValue: "", Required: true, Type: "string"},
		{Name: "db_password", Description: "Database password", DefaultValue: "", Required: true, Type: "string"},
		{Name: "api_host", Description: "API server host", DefaultValue: "0.0.0.0", Required: true, Type: "string"},
		{Name: "api_port", Description: "API server port", DefaultValue: 8080, Required: true, Type: "int"},
	}

	// Docker template
	dockerTemplate := ctm.CreateTemplate("docker", "Docker environment configuration", EnvDevelopment)
	dockerTemplate.Config = map[string]interface{}{
		"mode": "local",
		"postgis": map[string]interface{}{
			"host":     "{{db_host}}",
			"port":     "{{db_port}}",
			"database": "{{db_name}}",
			"user":     "{{db_user}}",
			"password": "{{db_password}}",
			"ssl_mode": "disable",
		},
		"api": map[string]interface{}{
			"host": "0.0.0.0",
			"port": "{{api_port}}",
		},
		"features": map[string]interface{}{
			"debug_mode":      true,
			"verbose_logging": true,
			"offline_mode":    true,
		},
		"telemetry": map[string]interface{}{
			"enabled": false,
		},
	}
	dockerTemplate.Variables = []TemplateVariable{
		{Name: "db_host", Description: "Database host", DefaultValue: "postgres", Required: true, Type: "string"},
		{Name: "db_port", Description: "Database port", DefaultValue: 5432, Required: true, Type: "int"},
		{Name: "db_name", Description: "Database name", DefaultValue: "arxos", Required: true, Type: "string"},
		{Name: "db_user", Description: "Database user", DefaultValue: "arxos", Required: true, Type: "string"},
		{Name: "db_password", Description: "Database password", DefaultValue: "arxos", Required: true, Type: "string"},
		{Name: "api_port", Description: "API server port", DefaultValue: 8080, Required: true, Type: "int"},
	}

	// Kubernetes template
	k8sTemplate := ctm.CreateTemplate("kubernetes", "Kubernetes environment configuration", EnvProduction)
	k8sTemplate.Config = map[string]interface{}{
		"mode": "cloud",
		"postgis": map[string]interface{}{
			"host":     "{{db_host}}",
			"port":     "{{db_port}}",
			"database": "{{db_name}}",
			"user":     "{{db_user}}",
			"password": "{{db_password}}",
			"ssl_mode": "require",
		},
		"api": map[string]interface{}{
			"host": "0.0.0.0",
			"port": "{{api_port}}",
		},
		"features": map[string]interface{}{
			"debug_mode":      false,
			"verbose_logging": false,
			"offline_mode":    false,
		},
		"telemetry": map[string]interface{}{
			"enabled": true,
		},
		"security": map[string]interface{}{
			"require_https":   true,
			"session_timeout": "8h",
		},
	}
	k8sTemplate.Variables = []TemplateVariable{
		{Name: "db_host", Description: "Database host", DefaultValue: "", Required: true, Type: "string"},
		{Name: "db_port", Description: "Database port", DefaultValue: 5432, Required: true, Type: "int"},
		{Name: "db_name", Description: "Database name", DefaultValue: "", Required: true, Type: "string"},
		{Name: "db_user", Description: "Database user", DefaultValue: "", Required: true, Type: "string"},
		{Name: "db_password", Description: "Database password", DefaultValue: "", Required: true, Type: "string"},
		{Name: "api_port", Description: "API server port", DefaultValue: 8080, Required: true, Type: "int"},
	}
}

func (ctm *ConfigTemplateManager) loadTemplatesFromFiles() error {
	if ctm.templatesDir == "" {
		return nil
	}

	entries, err := os.ReadDir(ctm.templatesDir)
	if err != nil {
		return fmt.Errorf("failed to read templates directory: %w", err)
	}

	for _, entry := range entries {
		if entry.IsDir() || !strings.HasSuffix(entry.Name(), ".json") {
			continue
		}

		filepath := filepath.Join(ctm.templatesDir, entry.Name())
		data, err := os.ReadFile(filepath)
		if err != nil {
			continue // Skip files that can't be read
		}

		var template ConfigTemplate
		if err := json.Unmarshal(data, &template); err != nil {
			continue // Skip files that can't be parsed
		}

		ctm.templates[template.Name] = &template
	}

	return nil
}

// GetDefaultTemplateForEnvironment returns the default template for an environment
func (ctm *ConfigTemplateManager) GetDefaultTemplateForEnvironment(env Environment) *ConfigTemplate {
	switch env {
	case EnvDevelopment:
		return ctm.templates["development"]
	case EnvStaging:
		return ctm.templates["staging"]
	case EnvProduction:
		return ctm.templates["production"]
	case EnvInternal:
		return ctm.templates["kubernetes"] // Use k8s template for internal
	default:
		return ctm.templates["development"]
	}
}
