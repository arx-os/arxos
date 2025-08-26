package commands

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"
)

func TestNewTemplateManager(t *testing.T) {
	templatesDir := "test_templates"
	tm := NewTemplateManager(templatesDir)

	if tm.TemplatesDir != templatesDir {
		t.Errorf("Expected templates directory %s, got %s", templatesDir, tm.TemplatesDir)
	}

	if tm.Templates == nil {
		t.Error("Templates map should not be nil")
	}

	if len(tm.Templates) != 0 {
		t.Errorf("Expected empty templates map, got %d templates", len(tm.Templates))
	}
}

func TestLoadTemplates(t *testing.T) {
	// Create a temporary directory for testing
	tempDir, err := os.MkdirTemp("", "arxos-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Create template manager
	tm := NewTemplateManager(tempDir)

	// Load templates
	if err := tm.LoadTemplates(); err != nil {
		t.Fatalf("LoadTemplates() failed: %v", err)
	}

	// Verify predefined templates were loaded
	expectedTemplates := []string{
		"standard_office",
		"residential",
		"industrial",
		"retail",
		"healthcare",
		"educational",
	}

	for _, expected := range expectedTemplates {
		if _, exists := tm.Templates[expected]; !exists {
			t.Errorf("Expected template %s not found", expected)
		}
	}

	// Verify template files were created
	for _, expected := range expectedTemplates {
		templatePath := filepath.Join(tempDir, fmt.Sprintf("%s.json", expected))
		if _, err := os.Stat(templatePath); os.IsNotExist(err) {
			t.Errorf("Template file not created: %s", templatePath)
		}
	}
}

func TestGetTemplate(t *testing.T) {
	// Create a temporary directory for testing
	tempDir, err := os.MkdirTemp("", "arxos-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Create template manager
	tm := NewTemplateManager(tempDir)

	// Load templates
	if err := tm.LoadTemplates(); err != nil {
		t.Fatalf("LoadTemplates() failed: %v", err)
	}

	// Test getting existing template
	template, err := tm.GetTemplate("standard_office")
	if err != nil {
		t.Fatalf("GetTemplate() failed: %v", err)
	}

	if template.Name != "standard_office" {
		t.Errorf("Expected template name 'standard_office', got '%s'", template.Name)
	}

	if template.BuildingType != "office" {
		t.Errorf("Expected building type 'office', got '%s'", template.BuildingType)
	}

	// Test getting non-existent template
	_, err = tm.GetTemplate("non_existent")
	if err == nil {
		t.Error("Expected error when getting non-existent template")
	}
}

func TestListTemplates(t *testing.T) {
	// Create a temporary directory for testing
	tempDir, err := os.MkdirTemp("", "arxos-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Create template manager
	tm := NewTemplateManager(tempDir)

	// Load templates
	if err := tm.LoadTemplates(); err != nil {
		t.Fatalf("LoadTemplates() failed: %v", err)
	}

	// List templates
	templates := tm.ListTemplates()

	// Verify all expected templates are listed
	expectedTemplates := []string{
		"standard_office",
		"residential",
		"industrial",
		"retail",
		"healthcare",
		"educational",
	}

	if len(templates) != len(expectedTemplates) {
		t.Errorf("Expected %d templates, got %d", len(expectedTemplates), len(templates))
	}

	// Verify each expected template is in the list
	for _, expected := range expectedTemplates {
		found := false
		for _, template := range templates {
			if template == expected {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("Expected template %s not found in list", expected)
		}
	}
}

func TestCreateCustomTemplate(t *testing.T) {
	// Create a temporary directory for testing
	tempDir, err := os.MkdirTemp("", "arxos-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Create template manager
	tm := NewTemplateManager(tempDir)

	// Create custom template
	customTemplate := &BuildingTemplate{
		Name:          "custom_warehouse",
		Description:   "Custom warehouse template",
		Version:       "1.0.0",
		Category:      "industrial",
		BuildingType:  "warehouse",
		DefaultFloors: 2,
		DefaultArea:   "80,000 sq ft",
		Systems: map[string]SystemTemplate{
			"electrical": {
				Name:        "Custom Electrical",
				Type:        "electrical",
				Description: "Custom electrical system",
				Required:    true,
				Components: []ComponentTemplate{
					{Name: "Main Panel", Type: "panel", Quantity: 1, Location: "electrical room"},
				},
				Properties: map[string]interface{}{
					"voltage":  "480V",
					"capacity": "1000A",
				},
				Standards: []string{"NEC"},
			},
		},
		Standards: []string{"IBC", "NFPA"},
		Tags:      []string{"custom", "warehouse"},
	}

	// Create custom template
	if err := tm.CreateCustomTemplate(customTemplate); err != nil {
		t.Fatalf("CreateCustomTemplate() failed: %v", err)
	}

	// Verify template was saved
	templatePath := filepath.Join(tempDir, "custom_warehouse.json")
	if _, err := os.Stat(templatePath); os.IsNotExist(err) {
		t.Errorf("Custom template file not created: %s", templatePath)
	}

	// Verify template is in loaded templates
	if _, exists := tm.Templates["custom_warehouse"]; !exists {
		t.Error("Custom template not added to loaded templates")
	}
}

func TestValidateTemplate(t *testing.T) {
	// Create a temporary directory for testing
	tempDir, err := os.MkdirTemp("", "arxos-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Create template manager
	tm := NewTemplateManager(tempDir)

	// Test valid template
	validTemplate := &BuildingTemplate{
		Name:          "valid_template",
		BuildingType:  "office",
		DefaultFloors: 3,
		DefaultArea:   "20,000 sq ft",
	}

	if err := tm.validateTemplate(validTemplate); err != nil {
		t.Errorf("Valid template validation failed: %v", err)
	}

	// Test invalid templates
	invalidTemplates := []*BuildingTemplate{
		{Name: "", BuildingType: "office", DefaultFloors: 3, DefaultArea: "20,000 sq ft"},
		{Name: "no_type", BuildingType: "", DefaultFloors: 3, DefaultArea: "20,000 sq ft"},
		{Name: "no_floors", BuildingType: "office", DefaultFloors: 0, DefaultArea: "20,000 sq ft"},
		{Name: "no_area", BuildingType: "office", DefaultFloors: 3, DefaultArea: ""},
	}

	for i, template := range invalidTemplates {
		if err := tm.validateTemplate(template); err == nil {
			t.Errorf("Invalid template %d validation should have failed", i)
		}
	}
}

func TestTemplateStructures(t *testing.T) {
	// Test SystemTemplate
	systemTemplate := SystemTemplate{
		Name:        "Test System",
		Type:        "electrical",
		Description: "Test electrical system",
		Required:    true,
		Components: []ComponentTemplate{
			{Name: "Test Component", Type: "panel", Quantity: 1, Location: "test"},
		},
		Properties: map[string]interface{}{
			"voltage": "120V",
		},
		Standards: []string{"NEC"},
	}

	if systemTemplate.Name == "" {
		t.Error("SystemTemplate Name not set")
	}
	if systemTemplate.Type == "" {
		t.Error("SystemTemplate Type not set")
	}
	if len(systemTemplate.Components) == 0 {
		t.Error("SystemTemplate Components not set")
	}

	// Test ComponentTemplate
	componentTemplate := ComponentTemplate{
		Name:        "Test Component",
		Type:        "panel",
		Quantity:    5,
		Location:    "electrical room",
		Connections: []string{"main", "sub"},
		Properties: map[string]interface{}{
			"capacity": "200A",
		},
	}

	if componentTemplate.Name == "" {
		t.Error("ComponentTemplate Name not set")
	}
	if componentTemplate.Type == "" {
		t.Error("ComponentTemplate Type not set")
	}
	if componentTemplate.Quantity <= 0 {
		t.Error("ComponentTemplate Quantity not set")
	}

	// Test ZoneTemplate
	zoneTemplate := ZoneTemplate{
		Name:        "Test Zone",
		Type:        "office",
		Description: "Test office zone",
		Area:        "1000 sq ft",
		Height:      "10 ft",
		Usage:       "office",
		Properties: map[string]interface{}{
			"occupancy": 20,
		},
	}

	if zoneTemplate.Name == "" {
		t.Error("ZoneTemplate Name not set")
	}
	if zoneTemplate.Type == "" {
		t.Error("ZoneTemplate Type not set")
	}
	if zoneTemplate.Area == "" {
		t.Error("ZoneTemplate Area not set")
	}

	// Test MaterialTemplate
	materialTemplate := MaterialTemplate{
		Name:        "Test Material",
		Type:        "wall",
		Description: "Test wall material",
		Cost:        25.0,
		Unit:        "sq ft",
		Properties: map[string]interface{}{
			"r_value": "15",
		},
		Standards: []string{"ASTM"},
	}

	if materialTemplate.Name == "" {
		t.Error("MaterialTemplate Name not set")
	}
	if materialTemplate.Type == "" {
		t.Error("MaterialTemplate Type not set")
	}
	if materialTemplate.Cost <= 0 {
		t.Error("MaterialTemplate Cost not set")
	}
}

func TestPredefinedTemplates(t *testing.T) {
	// Test standard office template
	officeTemplate := createStandardOfficeTemplate()
	if officeTemplate.Name != "standard_office" {
		t.Errorf("Expected office template name 'standard_office', got '%s'", officeTemplate.Name)
	}
	if officeTemplate.BuildingType != "office" {
		t.Errorf("Expected office building type 'office', got '%s'", officeTemplate.BuildingType)
	}
	if officeTemplate.DefaultFloors != 5 {
		t.Errorf("Expected office default floors 5, got %d", officeTemplate.DefaultFloors)
	}
	if len(officeTemplate.Systems) == 0 {
		t.Error("Office template should have systems defined")
	}
	if len(officeTemplate.Zones) == 0 {
		t.Error("Office template should have zones defined")
	}

	// Test residential template
	residentialTemplate := createResidentialTemplate()
	if residentialTemplate.Name != "residential" {
		t.Errorf("Expected residential template name 'residential', got '%s'", residentialTemplate.Name)
	}
	if residentialTemplate.BuildingType != "residential" {
		t.Errorf("Expected residential building type 'residential', got '%s'", residentialTemplate.BuildingType)
	}
	if residentialTemplate.DefaultFloors != 3 {
		t.Errorf("Expected residential default floors 3, got %d", residentialTemplate.DefaultFloors)
	}

	// Test industrial template
	industrialTemplate := createIndustrialTemplate()
	if industrialTemplate.Name != "industrial" {
		t.Errorf("Expected industrial template name 'industrial', got '%s'", industrialTemplate.Name)
	}
	if industrialTemplate.BuildingType != "industrial" {
		t.Errorf("Expected industrial building type 'industrial', got '%s'", industrialTemplate.BuildingType)
	}
	if industrialTemplate.DefaultFloors != 1 {
		t.Errorf("Expected industrial default floors 1, got %d", industrialTemplate.DefaultFloors)
	}
	if industrialTemplate.DefaultArea != "100,000 sq ft" {
		t.Errorf("Expected industrial default area '100,000 sq ft', got '%s'", industrialTemplate.DefaultArea)
	}

	// Test healthcare template
	healthcareTemplate := createHealthcareTemplate()
	if healthcareTemplate.Name != "healthcare" {
		t.Errorf("Expected healthcare template name 'healthcare', got '%s'", healthcareTemplate.Name)
	}
	if healthcareTemplate.BuildingType != "healthcare" {
		t.Errorf("Expected healthcare building type 'healthcare', got '%s'", healthcareTemplate.BuildingType)
	}
	if healthcareTemplate.DefaultFloors != 4 {
		t.Errorf("Expected healthcare default floors 4, got %d", healthcareTemplate.DefaultFloors)
	}

	// Test educational template
	educationalTemplate := createEducationalTemplate()
	if educationalTemplate.Name != "educational" {
		t.Errorf("Expected educational template name 'educational', got '%s'", educationalTemplate.Name)
	}
	if educationalTemplate.BuildingType != "educational" {
		t.Errorf("Expected educational building type 'educational', got '%s'", educationalTemplate.BuildingType)
	}
	if educationalTemplate.DefaultFloors != 3 {
		t.Errorf("Expected educational default floors 3, got %d", educationalTemplate.DefaultFloors)
	}
}

func TestTemplateIntegration(t *testing.T) {
	// Create a temporary directory for testing
	tempDir, err := os.MkdirTemp("", "arxos-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Test complete template workflow
	tm := NewTemplateManager(tempDir)

	// Load templates
	if err := tm.LoadTemplates(); err != nil {
		t.Fatalf("LoadTemplates() failed: %v", err)
	}

	// List available templates
	availableTemplates := tm.ListTemplates()
	if len(availableTemplates) == 0 {
		t.Fatal("No templates available")
	}

	// Get a specific template
	templateName := availableTemplates[0]
	template, err := tm.GetTemplate(templateName)
	if err != nil {
		t.Fatalf("Failed to get template %s: %v", templateName, err)
	}

	// Verify template structure
	if template.Name == "" {
		t.Error("Template name is empty")
	}
	if template.BuildingType == "" {
		t.Error("Template building type is empty")
	}
	if template.DefaultFloors <= 0 {
		t.Error("Template default floors is invalid")
	}
	if template.DefaultArea == "" {
		t.Error("Template default area is empty")
	}

	// Test template validation
	if err := tm.validateTemplate(template); err != nil {
		t.Errorf("Template validation failed: %v", err)
	}

	// Verify template file exists
	templatePath := filepath.Join(tempDir, fmt.Sprintf("%s.json", templateName))
	if _, err := os.Stat(templatePath); os.IsNotExist(err) {
		t.Errorf("Template file not found: %s", templatePath)
	}
}

func TestTemplateFileOperations(t *testing.T) {
	// Create a temporary directory for testing
	tempDir, err := os.MkdirTemp("", "arxos-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Create template manager
	tm := NewTemplateManager(tempDir)

	// Test loading from non-existent directory
	if err := tm.LoadTemplates(); err != nil {
		t.Fatalf("LoadTemplates() should create directory: %v", err)
	}

	// Verify directory was created
	if _, err := os.Stat(tempDir); os.IsNotExist(err) {
		t.Error("Templates directory was not created")
	}

	// Test loading custom template from file
	customTemplate := &BuildingTemplate{
		Name:          "file_test_template",
		BuildingType:  "test",
		DefaultFloors: 1,
		DefaultArea:   "1000 sq ft",
	}

	// Save template manually
	templatePath := filepath.Join(tempDir, "file_test_template.json")
	if err := writeJSON(templatePath, customTemplate); err != nil {
		t.Fatalf("Failed to save test template: %v", err)
	}

	// Load template from file
	loadedTemplate, err := tm.loadTemplateFromFile(templatePath)
	if err != nil {
		t.Fatalf("Failed to load template from file: %v", err)
	}

	if loadedTemplate.Name != customTemplate.Name {
		t.Errorf("Expected template name %s, got %s", customTemplate.Name, loadedTemplate.Name)
	}

	if loadedTemplate.BuildingType != customTemplate.BuildingType {
		t.Errorf("Expected building type %s, got %s", customTemplate.BuildingType, loadedTemplate.BuildingType)
	}
}
