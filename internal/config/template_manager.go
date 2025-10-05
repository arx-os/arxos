package config

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
)

// ConfigTemplateManager manages configuration templates
type ConfigTemplateManager struct {
	templatesDir string
	templates    map[string]*ConfigTemplate
	mu           sync.RWMutex
}

// NewConfigTemplateManager creates a new template manager
func NewConfigTemplateManager(templatesDir string) *ConfigTemplateManager {
	return &ConfigTemplateManager{
		templatesDir: templatesDir,
		templates:    make(map[string]*ConfigTemplate),
	}
}

// LoadTemplates loads all templates from the templates directory
func (ctm *ConfigTemplateManager) LoadTemplates() error {
	ctm.mu.Lock()
	defer ctm.mu.Unlock()

	// Ensure templates directory exists
	if err := os.MkdirAll(ctm.templatesDir, 0755); err != nil {
		return fmt.Errorf("failed to create templates directory: %w", err)
	}

	// Load built-in templates
	builtInTemplates := GetConfigTemplates()
	for _, template := range builtInTemplates {
		ctm.templates[template.Name] = &template
	}

	// Load custom templates from files
	return ctm.loadCustomTemplates()
}

// loadCustomTemplates loads custom templates from JSON files
func (ctm *ConfigTemplateManager) loadCustomTemplates() error {
	entries, err := os.ReadDir(ctm.templatesDir)
	if err != nil {
		return fmt.Errorf("failed to read templates directory: %w", err)
	}

	for _, entry := range entries {
		if entry.IsDir() || filepath.Ext(entry.Name()) != ".json" {
			continue
		}

		templatePath := filepath.Join(ctm.templatesDir, entry.Name())
		template, err := ctm.loadTemplateFromFile(templatePath)
		if err != nil {
			// Log error but continue loading other templates
			continue
		}

		ctm.templates[template.Name] = template
	}

	return nil
}

// loadTemplateFromFile loads a template from a JSON file
func (ctm *ConfigTemplateManager) loadTemplateFromFile(path string) (*ConfigTemplate, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read template file: %w", err)
	}

	var template ConfigTemplate
	if err := json.Unmarshal(data, &template); err != nil {
		return nil, fmt.Errorf("failed to unmarshal template: %w", err)
	}

	return &template, nil
}

// CreateTemplate creates a new template
func (ctm *ConfigTemplateManager) CreateTemplate(name, description string, environment Environment) *ConfigTemplate {
	ctm.mu.Lock()
	defer ctm.mu.Unlock()

	template := &ConfigTemplate{
		Name:        name,
		Description: description,
		Environment: environment,
		Variables:   []TemplateVariable{},
		Config:      &Config{},
	}

	ctm.templates[name] = template
	return template
}

// GetTemplate returns a template by name
func (ctm *ConfigTemplateManager) GetTemplate(name string) (*ConfigTemplate, error) {
	ctm.mu.RLock()
	defer ctm.mu.RUnlock()

	template, exists := ctm.templates[name]
	if !exists {
		return nil, fmt.Errorf("template %s not found", name)
	}

	return template, nil
}

// ListTemplates returns all available templates
func (ctm *ConfigTemplateManager) ListTemplates() []*ConfigTemplate {
	ctm.mu.RLock()
	defer ctm.mu.RUnlock()

	templates := make([]*ConfigTemplate, 0, len(ctm.templates))
	for _, template := range ctm.templates {
		templates = append(templates, template)
	}

	return templates
}

// SaveTemplate saves a template to disk
func (ctm *ConfigTemplateManager) SaveTemplate(template *ConfigTemplate) error {
	ctm.mu.Lock()
	defer ctm.mu.Unlock()

	// Ensure templates directory exists
	if err := os.MkdirAll(ctm.templatesDir, 0755); err != nil {
		return fmt.Errorf("failed to create templates directory: %w", err)
	}

	// Save template to file
	templatePath := filepath.Join(ctm.templatesDir, template.Name+".json")
	data, err := json.MarshalIndent(template, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal template: %w", err)
	}

	if err := os.WriteFile(templatePath, data, 0644); err != nil {
		return fmt.Errorf("failed to write template file: %w", err)
	}

	// Update in-memory cache
	ctm.templates[template.Name] = template

	return nil
}

// DeleteTemplate deletes a template
func (ctm *ConfigTemplateManager) DeleteTemplate(name string) error {
	ctm.mu.Lock()
	defer ctm.mu.Unlock()

	// Remove from memory
	delete(ctm.templates, name)

	// Remove file
	templatePath := filepath.Join(ctm.templatesDir, name+".json")
	if err := os.Remove(templatePath); err != nil && !os.IsNotExist(err) {
		return fmt.Errorf("failed to remove template file: %w", err)
	}

	return nil
}

// GetDefaultTemplateForEnvironment returns the default template for an environment
func (ctm *ConfigTemplateManager) GetDefaultTemplateForEnvironment(environment Environment) *ConfigTemplate {
	ctm.mu.RLock()
	defer ctm.mu.RUnlock()

	// Look for templates matching the environment
	for _, template := range ctm.templates {
		if template.Environment == environment {
			return template
		}
	}

	// Fallback to local template
	if localTemplate, exists := ctm.templates["local"]; exists {
		return localTemplate
	}

	// If no templates exist, return nil
	return nil
}

// ValidateTemplate validates a template
func (ctm *ConfigTemplateManager) ValidateTemplate(template *ConfigTemplate) error {
	if template.Name == "" {
		return fmt.Errorf("template name is required")
	}

	if template.Description == "" {
		return fmt.Errorf("template description is required")
	}

	if template.Config == nil {
		return fmt.Errorf("template configuration is required")
	}

	// Validate variables
	for i, variable := range template.Variables {
		if variable.Name == "" {
			return fmt.Errorf("variable %d name is required", i)
		}
		if variable.Description == "" {
			return fmt.Errorf("variable %d description is required", i)
		}
	}

	return nil
}

// GetTemplateNames returns all template names
func (ctm *ConfigTemplateManager) GetTemplateNames() []string {
	ctm.mu.RLock()
	defer ctm.mu.RUnlock()

	names := make([]string, 0, len(ctm.templates))
	for name := range ctm.templates {
		names = append(names, name)
	}

	return names
}

// TemplateExists checks if a template exists
func (ctm *ConfigTemplateManager) TemplateExists(name string) bool {
	ctm.mu.RLock()
	defer ctm.mu.RUnlock()

	_, exists := ctm.templates[name]
	return exists
}

// GetTemplatesByEnvironment returns templates for a specific environment
func (ctm *ConfigTemplateManager) GetTemplatesByEnvironment(environment Environment) []*ConfigTemplate {
	ctm.mu.RLock()
	defer ctm.mu.RUnlock()

	var templates []*ConfigTemplate
	for _, template := range ctm.templates {
		if template.Environment == environment {
			templates = append(templates, template)
		}
	}

	return templates
}
