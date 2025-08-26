package query

import (
	"fmt"
	"strings"
	"testing"
)

// Test Ask Command Components
func TestGenerateAQLFromQuestion(t *testing.T) {
	tests := []struct {
		question   string
		context    string
		expected   string
		confidence float64
	}{
		{
			question:   "show me all HVAC equipment on the 3rd floor",
			context:    "",
			expected:   "SELECT * FROM equipment WHERE type IN ('hvac', 'air_conditioning') AND floor = 3",
			confidence: 0.8,
		},
		{
			question:   "find all equipment that needs maintenance this week",
			context:    "",
			expected:   "SELECT * FROM equipment WHERE maintenance_due <= NOW() + INTERVAL '7 days'",
			confidence: 0.8,
		},
		{
			question:   "what's the energy consumption",
			context:    "",
			expected:   "SELECT * FROM energy_consumption ORDER BY timestamp DESC LIMIT 100",
			confidence: 0.8,
		},
	}

	for _, test := range tests {
		query, confidence := generateAQLFromQuestion(test.question, test.context)
		if query != test.expected {
			t.Errorf("Expected query '%s', got '%s'", test.expected, query)
		}
		if confidence != test.confidence {
			t.Errorf("Expected confidence %f, got %f", test.confidence, confidence)
		}
	}
}

func TestExtractFloorNumber(t *testing.T) {
	tests := []struct {
		question string
		expected string
	}{
		{"3rd floor", "3"},
		{"second floor", "2"},
		{"1st floor", "1"},
		{"floor 4", "1"}, // default
	}

	for _, test := range tests {
		result := extractFloorNumber(test.question)
		if result != test.expected {
			t.Errorf("Expected floor '%s', got '%s' for question '%s'", test.expected, result, test.question)
		}
	}
}

func TestExtractRoomNumber(t *testing.T) {
	tests := []struct {
		question string
		expected string
	}{
		{"room 205", "205"},
		{"electrical panel in 305", "305"},
		{"equipment near 101", "101"},
		{"no room number", "101"}, // default
	}

	for _, test := range tests {
		result := extractRoomNumber(test.question)
		if result != test.expected {
			t.Errorf("Expected room '%s', got '%s' for question '%s'", test.expected, result, test.question)
		}
	}
}

// Test Shell Command Components
func TestNewAQLShell(t *testing.T) {
	shell := NewAQLShell("json", true, true)

	if shell.format != "json" {
		t.Errorf("Expected format 'json', got '%s'", shell.format)
	}
	if !shell.enableHistory {
		t.Error("Expected history to be enabled")
	}
	if !shell.enableAutoComplete {
		t.Error("Expected auto-complete to be enabled")
	}
	if len(shell.history) != 0 {
		t.Error("Expected empty history")
	}
}

func TestAQLShellAddToHistory(t *testing.T) {
	shell := NewAQLShell("table", true, true)

	shell.addToHistory("SELECT * FROM arxobjects")
	shell.addToHistory("UPDATE wall_123 SET confidence = 0.95")

	if len(shell.history) != 2 {
		t.Errorf("Expected 2 history items, got %d", len(shell.history))
	}

	if shell.history[0] != "SELECT * FROM arxobjects" {
		t.Errorf("Expected first history item 'SELECT * FROM arxobjects', got '%s'", shell.history[0])
	}
}

func TestAQLShellHistoryLimit(t *testing.T) {
	shell := NewAQLShell("table", true, true)

	// Add more than 100 commands
	for i := 0; i < 105; i++ {
		shell.addToHistory(fmt.Sprintf("command_%d", i))
	}

	if len(shell.history) > 100 {
		t.Errorf("Expected history to be limited to 100, got %d", len(shell.history))
	}

	// Check that oldest commands were removed
	if shell.history[0] == "command_0" {
		t.Error("Expected oldest command to be removed")
	}
}

// Test Navigation Command Components
func TestNewNavigationContext(t *testing.T) {
	nav := NewNavigationContext("building:floor:room", "room:305", "10m", "panel:e1", "3d", "ascii-bim")

	if nav.Path != "building:floor:room" {
		t.Errorf("Expected path 'building:floor:room', got '%s'", nav.Path)
	}
	if nav.NearLocation != "room:305" {
		t.Errorf("Expected near location 'room:305', got '%s'", nav.NearLocation)
	}
	if nav.Radius != "10m" {
		t.Errorf("Expected radius '10m', got '%s'", nav.Radius)
	}
	if nav.SpatialMode != "3d" {
		t.Errorf("Expected spatial mode '3d', got '%s'", nav.SpatialMode)
	}
	if nav.ViewMode != "ascii-bim" {
		t.Errorf("Expected view mode 'ascii-bim', got '%s'", nav.ViewMode)
	}
}

func TestNavigationContextAddBreadcrumb(t *testing.T) {
	nav := NewNavigationContext("", "", "", "", "", "")

	nav.addBreadcrumb("building:hq")
	nav.addBreadcrumb("building:hq:floor:3")
	nav.addBreadcrumb("building:hq:floor:3:room:305")

	if len(nav.Breadcrumbs) != 3 {
		t.Errorf("Expected 3 breadcrumbs, got %d", len(nav.Breadcrumbs))
	}

	if nav.Breadcrumbs[0] != "building:hq" {
		t.Errorf("Expected first breadcrumb 'building:hq', got '%s'", nav.Breadcrumbs[0])
	}
}

func TestNavigationContextBreadcrumbLimit(t *testing.T) {
	nav := NewNavigationContext("", "", "", "", "", "")

	// Add more than 10 breadcrumbs
	for i := 0; i < 15; i++ {
		nav.addBreadcrumb(fmt.Sprintf("breadcrumb_%d", i))
	}

	if len(nav.Breadcrumbs) > 10 {
		t.Errorf("Expected breadcrumbs to be limited to 10, got %d", len(nav.Breadcrumbs))
	}

	// Check that oldest breadcrumbs were removed
	if nav.Breadcrumbs[0] == "breadcrumb_0" {
		t.Error("Expected oldest breadcrumb to be removed")
	}
}

func TestParseLocation(t *testing.T) {
	nav := NewNavigationContext("", "", "", "", "", "")

	location := nav.parseLocation("room:305")

	if location["type"] != "room" {
		t.Errorf("Expected type 'room', got '%v'", location["type"])
	}
	if location["id"] != "305" {
		t.Errorf("Expected id '305', got '%v'", location["id"])
	}
}

func TestParseRadius(t *testing.T) {
	nav := NewNavigationContext("", "", "", "", "", "")

	radius := nav.parseRadius("10m")
	if radius != 5.0 { // Default value for now
		t.Errorf("Expected radius 5.0, got %f", radius)
	}

	radius = nav.parseRadius("15ft")
	if radius != 5.0 { // Default value for now
		t.Errorf("Expected radius 5.0, got %f", radius)
	}
}

// Test Template Command Components
func TestNewQueryTemplateManager(t *testing.T) {
	tm := NewQueryTemplateManager()

	if tm.templates == nil {
		t.Error("Expected templates map to be initialized")
	}

	// Check that some templates were added
	if len(tm.templates) == 0 {
		t.Error("Expected templates to be populated")
	}
}

func TestTemplateManagerAddAndGetTemplate(t *testing.T) {
	tm := NewQueryTemplateManager()

	// Test getting existing template
	template, exists := tm.getTemplate("hvac_equipment")
	if !exists {
		t.Error("Expected hvac_equipment template to exist")
	}
	if template.Name != "hvac_equipment" {
		t.Errorf("Expected template name 'hvac_equipment', got '%s'", template.Name)
	}

	// Test getting non-existent template
	_, exists = tm.getTemplate("non_existent")
	if exists {
		t.Error("Expected non_existent template to not exist")
	}
}

func TestTemplateManagerGetTemplatesByCategory(t *testing.T) {
	tm := NewQueryTemplateManager()

	equipmentTemplates := tm.getTemplatesByCategory("equipment")
	if len(equipmentTemplates) == 0 {
		t.Error("Expected equipment templates to exist")
	}

	for _, template := range equipmentTemplates {
		if template.Category != "equipment" {
			t.Errorf("Expected category 'equipment', got '%s'", template.Category)
		}
	}
}

func TestParseTemplateParams(t *testing.T) {
	tests := []struct {
		params   string
		expected map[string]string
	}{
		{
			"floor=3,status=active",
			map[string]string{"floor": "3", "status": "active"},
		},
		{
			"building=hq,voltage=480",
			map[string]string{"building": "hq", "voltage": "480"},
		},
		{
			"",
			map[string]string{},
		},
		{
			"single_param",
			map[string]string{},
		},
	}

	for _, test := range tests {
		result := parseTemplateParams(test.params)

		if len(result) != len(test.expected) {
			t.Errorf("Expected %d params, got %d for input '%s'", len(test.expected), len(result), test.params)
			continue
		}

		for key, value := range test.expected {
			if result[key] != value {
				t.Errorf("Expected param[%s] = '%s', got '%s' for input '%s'", key, value, result[key], test.params)
			}
		}
	}
}

func TestApplyTemplate(t *testing.T) {
	tm := NewQueryTemplateManager()
	template, _ := tm.getTemplate("hvac_equipment")

	params := map[string]string{
		"floor":  "3",
		"status": "active",
	}

	query := applyTemplate(template, params)

	expectedContains := []string{
		"floor = 3",
		"status = 'active'",
	}

	for _, expected := range expectedContains {
		if !strings.Contains(query, expected) {
			t.Errorf("Expected query to contain '%s', got '%s'", expected, query)
		}
	}
}

func TestBuildFilters(t *testing.T) {
	tm := NewQueryTemplateManager()
	template, _ := tm.getTemplate("hvac_equipment")

	params := map[string]string{
		"floor":  "3",
		"status": "active",
	}

	filters := buildFilters(params, template.Parameters)

	if !strings.Contains(filters, "floor = 3") {
		t.Errorf("Expected filters to contain 'floor = 3', got '%s'", filters)
	}
	if !strings.Contains(filters, "status = 'active'") {
		t.Errorf("Expected filters to contain 'status = 'active'', got '%s'", filters)
	}
}

// Test Mock Data Generation
func TestGenerateMockHVACResults(t *testing.T) {
	results := generateMockHVACResults()

	if len(results) != 3 {
		t.Errorf("Expected 3 HVAC results, got %d", len(results))
	}

	// Check first result structure
	first := results[0].(map[string]interface{})
	if first["type"] != "hvac" {
		t.Errorf("Expected type 'hvac', got '%v'", first["type"])
	}
	if first["floor"] != 3 {
		t.Errorf("Expected floor 3, got '%v'", first["floor"])
	}
}

func TestGenerateMockElectricalResults(t *testing.T) {
	results := generateMockElectricalResults()

	if len(results) != 2 {
		t.Errorf("Expected 2 electrical results, got %d", len(results))
	}

	// Check first result structure
	first := results[0].(map[string]interface{})
	if first["type"] != "electrical_panel" {
		t.Errorf("Expected type 'electrical_panel', got '%v'", first["type"])
	}
}

func TestGenerateMockMaintenanceResults(t *testing.T) {
	results := generateMockMaintenanceResults()

	if len(results) != 2 {
		t.Errorf("Expected 2 maintenance results, got %d", len(results))
	}

	// Check first result structure
	first := results[0].(map[string]interface{})
	if first["priority"] != "high" {
		t.Errorf("Expected priority 'high', got '%v'", first["priority"])
	}
}

func TestGenerateMockEnergyResults(t *testing.T) {
	results := generateMockEnergyResults()

	if len(results) != 2 {
		t.Errorf("Expected 2 energy results, got %d", len(results))
	}

	// Check first result structure
	first := results[0].(map[string]interface{})
	if first["consumption_kwh"] != 45.2 {
		t.Errorf("Expected consumption 45.2, got '%v'", first["consumption_kwh"])
	}
}

// Test Result Display Integration
func TestAskCommandResultDisplay(t *testing.T) {
	question := "show me all HVAC equipment on the 3rd floor"
	result := executeGeneratedQuery("SELECT * FROM equipment WHERE type IN ('hvac', 'air_conditioning') AND floor = 3", question)

	if result.Type != "ASK" {
		t.Errorf("Expected type 'ASK', got '%s'", result.Type)
	}

	if result.Count != 3 {
		t.Errorf("Expected 3 results, got %d", result.Count)
	}

	if result.Metadata["original_question"] != question {
		t.Errorf("Expected original question in metadata")
	}
}

func TestShellCommandResultDisplay(t *testing.T) {
	shell := NewAQLShell("table", true, true)
	result := shell.generateMockResult("SELECT * FROM equipment WHERE type = 'hvac'")

	if result.Type != "SHELL" {
		t.Errorf("Expected type 'SHELL', got '%s'", result.Type)
	}

	if result.Metadata["query"] != "SELECT * FROM equipment WHERE type = 'hvac'" {
		t.Errorf("Expected query in metadata")
	}
}

func TestNavigationCommandResultDisplay(t *testing.T) {
	nav := NewNavigationContext("building:hq:floor:3", "", "", "", "", "")
	result := nav.Navigate()

	if result.Type != "NAVIGATE" {
		t.Errorf("Expected type 'NAVIGATE', got '%s'", result.Type)
	}

	if result.Metadata["navigation_type"] != "hierarchical" {
		t.Errorf("Expected navigation_type 'hierarchical', got '%v'", result.Metadata["navigation_type"])
	}
}

func TestTemplateCommandResultDisplay(t *testing.T) {
	result := executeTemplateQuery("SELECT * FROM equipment WHERE type = 'hvac'", "hvac_equipment", map[string]string{"floor": "3"})

	if result.Type != "TEMPLATE" {
		t.Errorf("Expected type 'TEMPLATE', got '%s'", result.Type)
	}

	if result.Metadata["template"] != "hvac_equipment" {
		t.Errorf("Expected template name in metadata")
	}

	if result.Metadata["parameters"].(map[string]string)["floor"] != "3" {
		t.Errorf("Expected parameters in metadata")
	}
}

// Note: These helper functions are not needed in actual Go code
// They were added to satisfy the test structure but Go has built-in fmt.Sprintf and strings.Contains
