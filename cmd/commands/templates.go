package commands

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

// BuildingTemplate represents a predefined building configuration
type BuildingTemplate struct {
	Name          string                      `json:"name"`
	Description   string                      `json:"description"`
	Version       string                      `json:"version"`
	Category      string                      `json:"category"`
	BuildingType  string                      `json:"building_type"`
	DefaultFloors int                         `json:"default_floors"`
	DefaultArea   string                      `json:"default_area"`
	Systems       map[string]SystemTemplate   `json:"systems"`
	Zones         map[string]ZoneTemplate     `json:"zones"`
	Materials     map[string]MaterialTemplate `json:"materials"`
	Standards     []string                    `json:"standards"`
	Tags          []string                    `json:"tags"`
	CreatedAt     time.Time                   `json:"created_at"`
	UpdatedAt     time.Time                   `json:"updated_at"`
}

// SystemTemplate defines a building system configuration
type SystemTemplate struct {
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	Description string                 `json:"description"`
	Components  []ComponentTemplate    `json:"components"`
	Properties  map[string]interface{} `json:"properties"`
	Standards   []string               `json:"standards"`
	Required    bool                   `json:"required"`
}

// ComponentTemplate defines individual system components
type ComponentTemplate struct {
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	Quantity    int                    `json:"quantity"`
	Properties  map[string]interface{} `json:"properties"`
	Location    string                 `json:"location"`
	Connections []string               `json:"connections"`
}

// ZoneTemplate defines building zones and areas
type ZoneTemplate struct {
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	Description string                 `json:"description"`
	Area        string                 `json:"area"`
	Height      string                 `json:"height"`
	Usage       string                 `json:"usage"`
	Properties  map[string]interface{} `json:"properties"`
}

// MaterialTemplate defines building materials and specifications
type MaterialTemplate struct {
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	Description string                 `json:"description"`
	Properties  map[string]interface{} `json:"properties"`
	Standards   []string               `json:"standards"`
	Cost        float64                `json:"cost"`
	Unit        string                 `json:"unit"`
}

// TemplateManager handles building template operations
type TemplateManager struct {
	TemplatesDir string
	Templates    map[string]*BuildingTemplate
}

// NewTemplateManager creates a new template manager
func NewTemplateManager(templatesDir string) *TemplateManager {
	return &TemplateManager{
		TemplatesDir: templatesDir,
		Templates:    make(map[string]*BuildingTemplate),
	}
}

// LoadTemplates loads all available building templates
func (tm *TemplateManager) LoadTemplates() error {
	// Create templates directory if it doesn't exist
	if err := os.MkdirAll(tm.TemplatesDir, 0755); err != nil {
		return fmt.Errorf("failed to create templates directory: %w", err)
	}

	// Load predefined templates
	if err := tm.loadPredefinedTemplates(); err != nil {
		return fmt.Errorf("failed to load predefined templates: %w", err)
	}

	// Load custom templates from filesystem
	if err := tm.loadCustomTemplates(); err != nil {
		return fmt.Errorf("failed to load custom templates: %w", err)
	}

	return nil
}

// loadPredefinedTemplates creates built-in building templates
func (tm *TemplateManager) loadPredefinedTemplates() error {
	templates := []*BuildingTemplate{
		createStandardOfficeTemplate(),
		createResidentialTemplate(),
		createIndustrialTemplate(),
		createRetailTemplate(),
		createHealthcareTemplate(),
		createEducationalTemplate(),
	}

	for _, template := range templates {
		tm.Templates[template.Name] = template

		// Save predefined template to filesystem
		templatePath := filepath.Join(tm.TemplatesDir, fmt.Sprintf("%s.json", template.Name))
		if err := writeJSON(templatePath, template); err != nil {
			return fmt.Errorf("failed to save template %s: %w", template.Name, err)
		}
	}

	return nil
}

// loadCustomTemplates loads user-defined templates from filesystem
func (tm *TemplateManager) loadCustomTemplates() error {
	entries, err := os.ReadDir(tm.TemplatesDir)
	if err != nil {
		return fmt.Errorf("failed to read templates directory: %w", err)
	}

	for _, entry := range entries {
		if entry.IsDir() || filepath.Ext(entry.Name()) != ".json" {
			continue
		}

		templatePath := filepath.Join(tm.TemplatesDir, entry.Name())
		template, err := tm.loadTemplateFromFile(templatePath)
		if err != nil {
			// Log error but continue loading other templates
			fmt.Printf("Warning: Failed to load template %s: %v\n", entry.Name(), err)
			continue
		}

		tm.Templates[template.Name] = template
	}

	return nil
}

// loadTemplateFromFile loads a template from a JSON file
func (tm *TemplateManager) loadTemplateFromFile(filepath string) (*BuildingTemplate, error) {
	data, err := os.ReadFile(filepath)
	if err != nil {
		return nil, fmt.Errorf("failed to read template file: %w", err)
	}

	var template BuildingTemplate
	if err := json.Unmarshal(data, &template); err != nil {
		return nil, fmt.Errorf("failed to unmarshal template: %w", err)
	}

	return &template, nil
}

// GetTemplate retrieves a template by name
func (tm *TemplateManager) GetTemplate(name string) (*BuildingTemplate, error) {
	template, exists := tm.Templates[name]
	if !exists {
		return nil, fmt.Errorf("template not found: %s", name)
	}
	return template, nil
}

// ListTemplates returns all available template names
func (tm *TemplateManager) ListTemplates() []string {
	names := make([]string, 0, len(tm.Templates))
	for name := range tm.Templates {
		names = append(names, name)
	}
	return names
}

// CreateCustomTemplate creates a new custom building template
func (tm *TemplateManager) CreateCustomTemplate(template *BuildingTemplate) error {
	// Validate template
	if err := tm.validateTemplate(template); err != nil {
		return fmt.Errorf("template validation failed: %w", err)
	}

	// Set metadata
	template.CreatedAt = time.Now()
	template.UpdatedAt = time.Now()

	// Save template
	templatePath := filepath.Join(tm.TemplatesDir, fmt.Sprintf("%s.json", template.Name))
	if err := writeJSON(templatePath, template); err != nil {
		return fmt.Errorf("failed to save template: %w", err)
	}

	// Add to loaded templates
	tm.Templates[template.Name] = template

	return nil
}

// validateTemplate validates template structure and data
func (tm *TemplateManager) validateTemplate(template *BuildingTemplate) error {
	if template.Name == "" {
		return fmt.Errorf("template name is required")
	}

	if template.BuildingType == "" {
		return fmt.Errorf("building type is required")
	}

	if template.DefaultFloors <= 0 {
		return fmt.Errorf("default floors must be greater than 0")
	}

	if template.DefaultArea == "" {
		return fmt.Errorf("default area is required")
	}

	return nil
}

// createStandardOfficeTemplate creates a standard office building template
func createStandardOfficeTemplate() *BuildingTemplate {
	return &BuildingTemplate{
		Name:          "standard_office",
		Description:   "Standard office building with modern amenities",
		Version:       "1.0.0",
		Category:      "commercial",
		BuildingType:  "office",
		DefaultFloors: 5,
		DefaultArea:   "25,000 sq ft",
		Systems: map[string]SystemTemplate{
			"electrical": {
				Name:        "Electrical System",
				Type:        "electrical",
				Description: "Main electrical distribution system",
				Required:    true,
				Components: []ComponentTemplate{
					{Name: "Main Panel", Type: "panel", Quantity: 1, Location: "basement"},
					{Name: "Sub Panel", Type: "panel", Quantity: 2, Location: "per floor"},
					{Name: "Outlet", Type: "outlet", Quantity: 8, Location: "per room"},
					{Name: "Light Fixture", Type: "light", Quantity: 12, Location: "per floor"},
				},
				Properties: map[string]interface{}{
					"voltage":      "480V",
					"capacity":     "800A",
					"backup_power": true,
				},
				Standards: []string{"NEC", "NFPA 70"},
			},
			"hvac": {
				Name:        "HVAC System",
				Type:        "hvac",
				Description: "Heating, ventilation, and air conditioning",
				Required:    true,
				Components: []ComponentTemplate{
					{Name: "Air Handler", Type: "ahu", Quantity: 2, Location: "roof"},
					{Name: "VAV Box", Type: "vav", Quantity: 4, Location: "per floor"},
					{Name: "Thermostat", Type: "thermostat", Quantity: 6, Location: "per floor"},
				},
				Properties: map[string]interface{}{
					"type":             "vav",
					"cooling_capacity": "50 tons",
					"heating_type":     "electric",
				},
				Standards: []string{"ASHRAE 90.1", "ASHRAE 62.1"},
			},
			"plumbing": {
				Name:        "Plumbing System",
				Type:        "plumbing",
				Description: "Water supply and drainage",
				Required:    true,
				Components: []ComponentTemplate{
					{Name: "Water Riser", Type: "riser", Quantity: 2, Location: "core"},
					{Name: "Bathroom", Type: "bathroom", Quantity: 3, Location: "per floor"},
					{Name: "Kitchen", Type: "kitchen", Quantity: 1, Location: "ground floor"},
				},
				Properties: map[string]interface{}{
					"water_supply": "municipal",
					"drainage":     "gravity",
					"hot_water":    true,
				},
				Standards: []string{"IPC", "UPC"},
			},
		},
		Zones: map[string]ZoneTemplate{
			"lobby": {
				Name:        "Lobby",
				Type:        "public",
				Description: "Main entrance and reception area",
				Area:        "1,500 sq ft",
				Height:      "12 ft",
				Usage:       "reception",
			},
			"office": {
				Name:        "Office Space",
				Type:        "work",
				Description: "Standard office work areas",
				Area:        "3,000 sq ft",
				Height:      "9 ft",
				Usage:       "office",
			},
			"conference": {
				Name:        "Conference Room",
				Type:        "meeting",
				Description: "Meeting and presentation space",
				Area:        "800 sq ft",
				Height:      "9 ft",
				Usage:       "meeting",
			},
		},
		Materials: map[string]MaterialTemplate{
			"exterior_wall": {
				Name:        "Exterior Wall",
				Type:        "wall",
				Description: "Exterior wall assembly",
				Properties: map[string]interface{}{
					"r_value":     "20",
					"thickness":   "8 inches",
					"fire_rating": "2 hour",
				},
				Standards: []string{"IBC", "ASTM"},
				Cost:      45.0,
				Unit:      "sq ft",
			},
			"roof": {
				Name:        "Roof Assembly",
				Type:        "roof",
				Description: "Roof system with insulation",
				Properties: map[string]interface{}{
					"r_value":  "30",
					"slope":    "1/4:12",
					"membrane": "TPO",
				},
				Standards: []string{"IBC", "ASTM"},
				Cost:      35.0,
				Unit:      "sq ft",
			},
		},
		Standards: []string{"IBC", "ASHRAE", "NEC", "NFPA"},
		Tags:      []string{"office", "commercial", "modern", "efficient"},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}

// createResidentialTemplate creates a residential building template
func createResidentialTemplate() *BuildingTemplate {
	return &BuildingTemplate{
		Name:          "residential",
		Description:   "Standard residential building template",
		Version:       "1.0.0",
		Category:      "residential",
		BuildingType:  "residential",
		DefaultFloors: 3,
		DefaultArea:   "15,000 sq ft",
		Systems: map[string]SystemTemplate{
			"electrical": {
				Name:        "Residential Electrical",
				Type:        "electrical",
				Description: "Residential electrical system",
				Required:    true,
				Components: []ComponentTemplate{
					{Name: "Main Panel", Type: "panel", Quantity: 1, Location: "garage"},
					{Name: "Outlet", Type: "outlet", Quantity: 6, Location: "per room"},
					{Name: "Light Fixture", Type: "light", Quantity: 8, Location: "per floor"},
				},
				Properties: map[string]interface{}{
					"voltage":  "240V",
					"capacity": "200A",
				},
				Standards: []string{"NEC"},
			},
			"hvac": {
				Name:        "Residential HVAC",
				Type:        "hvac",
				Description: "Residential heating and cooling",
				Required:    true,
				Components: []ComponentTemplate{
					{Name: "Furnace", Type: "furnace", Quantity: 1, Location: "basement"},
					{Name: "AC Unit", Type: "ac", Quantity: 1, Location: "exterior"},
					{Name: "Thermostat", Type: "thermostat", Quantity: 2, Location: "main floor"},
				},
				Properties: map[string]interface{}{
					"heating_type": "gas",
					"cooling_type": "electric",
				},
				Standards: []string{"ASHRAE"},
			},
		},
		Zones: map[string]ZoneTemplate{
			"living": {
				Name:        "Living Room",
				Type:        "living",
				Description: "Main living area",
				Area:        "400 sq ft",
				Height:      "9 ft",
				Usage:       "living",
			},
			"bedroom": {
				Name:        "Bedroom",
				Type:        "sleeping",
				Description: "Standard bedroom",
				Area:        "200 sq ft",
				Height:      "9 ft",
				Usage:       "sleeping",
			},
		},
		Standards: []string{"IRC", "ASHRAE", "NEC"},
		Tags:      []string{"residential", "home", "family"},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}

// createIndustrialTemplate creates an industrial building template
func createIndustrialTemplate() *BuildingTemplate {
	return &BuildingTemplate{
		Name:          "industrial",
		Description:   "Industrial warehouse and manufacturing facility",
		Version:       "1.0.0",
		Category:      "industrial",
		BuildingType:  "industrial",
		DefaultFloors: 1,
		DefaultArea:   "100,000 sq ft",
		Systems: map[string]SystemTemplate{
			"electrical": {
				Name:        "Industrial Electrical",
				Type:        "electrical",
				Description: "High-capacity industrial electrical system",
				Required:    true,
				Components: []ComponentTemplate{
					{Name: "Main Switchgear", Type: "switchgear", Quantity: 1, Location: "electrical room"},
					{Name: "Distribution Panel", Type: "panel", Quantity: 8, Location: "throughout"},
					{Name: "Industrial Outlet", Type: "outlet", Quantity: 20, Location: "per area"},
				},
				Properties: map[string]interface{}{
					"voltage":      "480V",
					"capacity":     "2000A",
					"backup_power": true,
				},
				Standards: []string{"NEC", "NFPA 70"},
			},
			"fire_protection": {
				Name:        "Fire Protection",
				Type:        "fire_protection",
				Description: "Industrial fire suppression system",
				Required:    true,
				Components: []ComponentTemplate{
					{Name: "Sprinkler Head", Type: "sprinkler", Quantity: 200, Location: "ceiling"},
					{Name: "Pull Station", Type: "pull_station", Quantity: 12, Location: "exits"},
					{Name: "Fire Alarm", Type: "alarm", Quantity: 15, Location: "throughout"},
				},
				Properties: map[string]interface{}{
					"type":       "wet_sprinkler",
					"coverage":   "complete",
					"alarm_type": "addressable",
				},
				Standards: []string{"NFPA 13", "NFPA 72"},
			},
		},
		Zones: map[string]ZoneTemplate{
			"warehouse": {
				Name:        "Warehouse",
				Type:        "storage",
				Description: "Main storage area",
				Area:        "80,000 sq ft",
				Height:      "24 ft",
				Usage:       "storage",
			},
			"office": {
				Name:        "Office Area",
				Type:        "work",
				Description: "Administrative offices",
				Area:        "5,000 sq ft",
				Height:      "12 ft",
				Usage:       "office",
			},
		},
		Standards: []string{"IBC", "NFPA", "OSHA"},
		Tags:      []string{"industrial", "warehouse", "manufacturing"},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}

// createRetailTemplate creates a retail building template
func createRetailTemplate() *BuildingTemplate {
	return &BuildingTemplate{
		Name:          "retail",
		Description:   "Retail store and shopping facility",
		Version:       "1.0.0",
		Category:      "commercial",
		BuildingType:  "retail",
		DefaultFloors: 2,
		DefaultArea:   "50,000 sq ft",
		Systems: map[string]SystemTemplate{
			"electrical": {
				Name:        "Retail Electrical",
				Type:        "electrical",
				Description: "Retail electrical system with lighting",
				Required:    true,
				Components: []ComponentTemplate{
					{Name: "Main Panel", Type: "panel", Quantity: 1, Location: "electrical room"},
					{Name: "Lighting Panel", Type: "panel", Quantity: 2, Location: "ceiling"},
					{Name: "Display Outlet", Type: "outlet", Quantity: 30, Location: "sales floor"},
				},
				Properties: map[string]interface{}{
					"voltage":  "480V",
					"capacity": "1000A",
					"lighting": "LED",
				},
				Standards: []string{"NEC", "ASHRAE 90.1"},
			},
			"hvac": {
				Name:        "Retail HVAC",
				Type:        "hvac",
				Description: "Retail heating and cooling system",
				Required:    true,
				Components: []ComponentTemplate{
					{Name: "Air Handler", Type: "ahu", Quantity: 3, Location: "roof"},
					{Name: "VAV Box", Type: "vav", Quantity: 6, Location: "sales floor"},
					{Name: "Thermostat", Type: "thermostat", Quantity: 8, Location: "zones"},
				},
				Properties: map[string]interface{}{
					"type":             "vav",
					"cooling_capacity": "75 tons",
					"heating_type":     "gas",
				},
				Standards: []string{"ASHRAE 90.1", "ASHRAE 62.1"},
			},
		},
		Zones: map[string]ZoneTemplate{
			"sales_floor": {
				Name:        "Sales Floor",
				Type:        "retail",
				Description: "Main sales area",
				Area:        "35,000 sq ft",
				Height:      "12 ft",
				Usage:       "retail",
			},
			"stockroom": {
				Name:        "Stockroom",
				Type:        "storage",
				Description: "Inventory storage",
				Area:        "10,000 sq ft",
				Height:      "12 ft",
				Usage:       "storage",
			},
		},
		Standards: []string{"IBC", "ASHRAE", "NEC"},
		Tags:      []string{"retail", "commercial", "shopping"},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}

// createHealthcareTemplate creates a healthcare facility template
func createHealthcareTemplate() *BuildingTemplate {
	return &BuildingTemplate{
		Name:          "healthcare",
		Description:   "Healthcare facility and medical center",
		Version:       "1.0.0",
		Category:      "healthcare",
		BuildingType:  "healthcare",
		DefaultFloors: 4,
		DefaultArea:   "75,000 sq ft",
		Systems: map[string]SystemTemplate{
			"electrical": {
				Name:        "Healthcare Electrical",
				Type:        "electrical",
				Description: "Critical care electrical system",
				Required:    true,
				Components: []ComponentTemplate{
					{Name: "Main Switchgear", Type: "switchgear", Quantity: 1, Location: "electrical room"},
					{Name: "Emergency Panel", Type: "panel", Quantity: 2, Location: "separate rooms"},
					{Name: "Normal Panel", Type: "panel", Quantity: 4, Location: "electrical rooms"},
				},
				Properties: map[string]interface{}{
					"voltage":         "480V",
					"capacity":        "1500A",
					"emergency_power": true,
					"ups":             true,
				},
				Standards: []string{"NEC", "NFPA 99", "NFPA 70"},
			},
			"medical_gas": {
				Name:        "Medical Gas",
				Type:        "medical_gas",
				Description: "Medical gas distribution system",
				Required:    true,
				Components: []ComponentTemplate{
					{Name: "Oxygen Manifold", Type: "manifold", Quantity: 1, Location: "medical gas room"},
					{Name: "Nitrogen Manifold", Type: "manifold", Quantity: 1, Location: "medical gas room"},
					{Name: "Medical Outlet", Type: "outlet", Quantity: 50, Location: "patient rooms"},
				},
				Properties: map[string]interface{}{
					"oxygen":     true,
					"nitrogen":   true,
					"vacuum":     true,
					"monitoring": true,
				},
				Standards: []string{"NFPA 99", "CGA"},
			},
		},
		Zones: map[string]ZoneTemplate{
			"patient_room": {
				Name:        "Patient Room",
				Type:        "patient_care",
				Description: "Standard patient room",
				Area:        "300 sq ft",
				Height:      "10 ft",
				Usage:       "patient_care",
			},
			"operating_room": {
				Name:        "Operating Room",
				Type:        "surgical",
				Description: "Surgical operating room",
				Area:        "600 sq ft",
				Height:      "12 ft",
				Usage:       "surgical",
			},
		},
		Standards: []string{"IBC", "NFPA 99", "ASHRAE 170", "FGI"},
		Tags:      []string{"healthcare", "medical", "hospital"},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}

// createEducationalTemplate creates an educational facility template
func createEducationalTemplate() *BuildingTemplate {
	return &BuildingTemplate{
		Name:          "educational",
		Description:   "Educational facility and school building",
		Version:       "1.0.0",
		Category:      "educational",
		BuildingType:  "educational",
		DefaultFloors: 3,
		DefaultArea:   "60,000 sq ft",
		Systems: map[string]SystemTemplate{
			"electrical": {
				Name:        "Educational Electrical",
				Type:        "electrical",
				Description: "School electrical system",
				Required:    true,
				Components: []ComponentTemplate{
					{Name: "Main Panel", Type: "panel", Quantity: 1, Location: "electrical room"},
					{Name: "Classroom Panel", Type: "panel", Quantity: 3, Location: "per floor"},
					{Name: "Classroom Outlet", Type: "outlet", Quantity: 8, Location: "per classroom"},
				},
				Properties: map[string]interface{}{
					"voltage":    "480V",
					"capacity":   "800A",
					"technology": true,
				},
				Standards: []string{"NEC", "NFPA 70"},
			},
			"security": {
				Name:        "Security System",
				Type:        "security",
				Description: "School security and access control",
				Required:    true,
				Components: []ComponentTemplate{
					{Name: "Camera", Type: "camera", Quantity: 25, Location: "throughout"},
					{Name: "Card Reader", Type: "reader", Quantity: 12, Location: "entrances"},
					{Name: "Intercom", Type: "intercom", Quantity: 8, Location: "classrooms"},
				},
				Properties: map[string]interface{}{
					"access_control": true,
					"surveillance":   true,
					"emergency":      true,
				},
				Standards: []string{"NFPA 72", "UL"},
			},
		},
		Zones: map[string]ZoneTemplate{
			"classroom": {
				Name:        "Classroom",
				Type:        "learning",
				Description: "Standard classroom",
				Area:        "800 sq ft",
				Height:      "10 ft",
				Usage:       "learning",
			},
			"gymnasium": {
				Name:        "Gymnasium",
				Type:        "athletic",
				Description: "Physical education facility",
				Area:        "5,000 sq ft",
				Height:      "20 ft",
				Usage:       "athletic",
			},
		},
		Standards: []string{"IBC", "NFPA", "ASHRAE"},
		Tags:      []string{"educational", "school", "learning"},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}
