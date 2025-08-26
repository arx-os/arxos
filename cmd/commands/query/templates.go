package query

import (
	"fmt"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

var templatesCmd = &cobra.Command{
	Use:   "templates [category]",
	Short: "Show and use AQL query templates",
	Long: `Show and use pre-built AQL query templates for common building operations.
Templates provide quick access to frequently used queries with customizable parameters.

Categories:
  - equipment: HVAC, electrical, mechanical equipment queries
  - spatial: Room, floor, building spatial queries
  - maintenance: Maintenance schedules and work orders
  - energy: Energy consumption and efficiency
  - validation: Field validation and quality checks
  - all: Show all available templates

Examples:
  arx query templates equipment
  arx query templates --use=hvac_maintenance --params="floor=3,status=active"
  arx query templates --list --category=spatial`,
	Args: cobra.MaximumNArgs(1),
	RunE: runTemplates,
}

func init() {
	QueryCmd.AddCommand(templatesCmd)

	// Template flags
	templatesCmd.Flags().String("use", "", "Use a specific template by name")
	templatesCmd.Flags().String("params", "", "Template parameters (key=value,key=value)")
	templatesCmd.Flags().Bool("list", false, "List available templates")
	templatesCmd.Flags().String("category", "", "Filter templates by category")
	templatesCmd.Flags().String("format", "table", "Output format for template results")
}

func runTemplates(cmd *cobra.Command, args []string) error {
	category := ""
	if len(args) > 0 {
		category = args[0]
	}

	useTemplate, _ := cmd.Flags().GetString("use")
	params, _ := cmd.Flags().GetString("params")
	listMode, _ := cmd.Flags().GetBool("list")
	filterCategory, _ := cmd.Flags().GetString("category")
	format, _ := cmd.Flags().GetString("format")

	// Handle different modes
	if useTemplate != "" {
		return useTemplate(useTemplate, params, format)
	} else if listMode {
		return listTemplates(category, filterCategory)
	} else {
		return showTemplates(category)
	}
}

// QueryTemplate represents a pre-built AQL query template
type QueryTemplate struct {
	Name        string
	Category    string
	Description string
	Query       string
	Parameters  []TemplateParameter
	Examples    []string
	Tags        []string
}

// TemplateParameter represents a template parameter
type TemplateParameter struct {
	Name        string
	Type        string
	Description string
	Required    bool
	Default     string
	Options     []string
}

// QueryTemplateManager manages query templates
type QueryTemplateManager struct {
	templates map[string]*QueryTemplate
}

// NewQueryTemplateManager creates a new template manager
func NewQueryTemplateManager() *QueryTemplateManager {
	tm := &QueryTemplateManager{
		templates: make(map[string]*QueryTemplate),
	}
	tm.initializeTemplates()
	return tm
}

// initializeTemplates populates the template manager with built-in templates
func (tm *QueryTemplateManager) initializeTemplates() {
	// Equipment templates
	tm.addTemplate(&QueryTemplate{
		Name:        "hvac_equipment",
		Category:    "equipment",
		Description: "Find HVAC equipment with optional filters",
		Query:       "SELECT * FROM equipment WHERE type IN ('hvac', 'air_conditioning') {filters}",
		Parameters: []TemplateParameter{
			{Name: "floor", Type: "int", Description: "Floor number", Required: false, Default: ""},
			{Name: "status", Type: "string", Description: "Equipment status", Required: false, Default: "active", Options: []string{"active", "maintenance", "inactive"}},
			{Name: "type", Type: "string", Description: "Specific HVAC type", Required: false, Default: "", Options: []string{"hvac", "air_conditioning", "heating", "ventilation"}},
		},
		Examples: []string{
			"arx query templates --use=hvac_equipment --params=\"floor=3,status=active\"",
			"arx query templates --use=hvac_equipment --params=\"type=heating\"",
		},
		Tags: []string{"hvac", "equipment", "climate"},
	})

	tm.addTemplate(&QueryTemplate{
		Name:        "electrical_panels",
		Category:    "equipment",
		Description: "Find electrical panels and distribution equipment",
		Query:       "SELECT * FROM equipment WHERE type = 'electrical_panel' {filters}",
		Parameters: []TemplateParameter{
			{Name: "building", Type: "string", Description: "Building identifier", Required: false, Default: ""},
			{Name: "voltage", Type: "int", Description: "Voltage rating", Required: false, Default: ""},
			{Name: "status", Type: "string", Description: "Panel status", Required: false, Default: "active", Options: []string{"active", "maintenance", "inactive"}},
		},
		Examples: []string{
			"arx query templates --use=electrical_panels --params=\"building=hq,voltage=480\"",
		},
		Tags: []string{"electrical", "equipment", "power"},
	})

	// Spatial templates
	tm.addTemplate(&QueryTemplate{
		Name:        "room_contents",
		Category:    "spatial",
		Description: "Find all objects within a specific room",
		Query:       "SELECT * FROM arxobjects WHERE room = '{room}' {filters}",
		Parameters: []TemplateParameter{
			{Name: "room", Type: "string", Description: "Room identifier", Required: true, Default: ""},
			{Name: "type", Type: "string", Description: "Object type filter", Required: false, Default: ""},
			{Name: "confidence", Type: "float", Description: "Minimum confidence threshold", Required: false, Default: "0.5"},
		},
		Examples: []string{
			"arx query templates --use=room_contents --params=\"room=305\"",
			"arx query templates --use=room_contents --params=\"room=305,type=equipment,confidence=0.8\"",
		},
		Tags: []string{"spatial", "room", "contents"},
	})

	tm.addTemplate(&QueryTemplate{
		Name:        "floor_overview",
		Category:    "spatial",
		Description: "Get overview of all objects on a specific floor",
		Query:       "SELECT type, COUNT(*) as count, AVG(confidence) as avg_confidence FROM arxobjects WHERE floor = {floor} GROUP BY type",
		Parameters: []TemplateParameter{
			{Name: "floor", Type: "int", Description: "Floor number", Required: true, Default: ""},
			{Name: "building", Type: "string", Description: "Building identifier", Required: false, Default: ""},
		},
		Examples: []string{
			"arx query templates --use=floor_overview --params=\"floor=3\"",
		},
		Tags: []string{"spatial", "floor", "overview"},
	})

	// Maintenance templates
	tm.addTemplate(&QueryTemplate{
		Name:        "maintenance_schedule",
		Category:    "maintenance",
		Description: "Find equipment requiring maintenance",
		Query:       "SELECT * FROM equipment WHERE maintenance_due <= NOW() + INTERVAL '{days} days' {filters}",
		Parameters: []TemplateParameter{
			{Name: "days", Type: "int", Description: "Days ahead to check", Required: false, Default: "30"},
			{Name: "priority", Type: "string", Description: "Priority level", Required: false, Default: "", Options: []string{"low", "medium", "high", "critical"}},
			{Name: "type", Type: "string", Description: "Equipment type", Required: false, Default: ""},
		},
		Examples: []string{
			"arx query templates --use=maintenance_schedule --params=\"days=7,priority=high\"",
		},
		Tags: []string{"maintenance", "schedule", "equipment"},
	})

	// Energy templates
	tm.addTemplate(&QueryTemplate{
		Name:        "energy_consumption",
		Category:    "energy",
		Description: "Analyze energy consumption patterns",
		Query:       "SELECT DATE(timestamp) as date, AVG(consumption_kwh) as avg_consumption, SUM(consumption_kwh) as total_consumption FROM energy_consumption WHERE timestamp >= NOW() - INTERVAL '{period}' GROUP BY DATE(timestamp) ORDER BY date DESC",
		Parameters: []TemplateParameter{
			{Name: "period", Type: "string", Description: "Time period", Required: false, Default: "7 days", Options: []string{"1 day", "7 days", "30 days", "90 days"}},
			{Name: "building", Type: "string", Description: "Building filter", Required: false, Default: ""},
			{Name: "floor", Type: "int", Description: "Floor filter", Required: false, Default: ""},
		},
		Examples: []string{
			"arx query templates --use=energy_consumption --params=\"period=30 days,building=hq\"",
		},
		Tags: []string{"energy", "consumption", "analysis"},
	})

	// Validation templates
	tm.addTemplate(&QueryTemplate{
		Name:        "validation_status",
		Category:    "validation",
		Description: "Check field validation status of objects",
		Query:       "SELECT * FROM arxobjects WHERE confidence < {threshold} {filters}",
		Parameters: []TemplateParameter{
			{Name: "threshold", Type: "float", Description: "Confidence threshold", Required: false, Default: "0.8"},
			{Name: "type", Type: "string", Description: "Object type", Required: false, Default: ""},
			{Name: "last_updated", Type: "string", Description: "Last updated filter", Required: false, Default: "", Options: []string{"today", "week", "month"}},
		},
		Examples: []string{
			"arx query templates --use=validation_status --params=\"threshold=0.7,type=wall\"",
		},
		Tags: []string{"validation", "quality", "confidence"},
	})
}

// addTemplate adds a template to the manager
func (tm *QueryTemplateManager) addTemplate(template *QueryTemplate) {
	tm.templates[template.Name] = template
}

// getTemplate retrieves a template by name
func (tm *QueryTemplateManager) getTemplate(name string) (*QueryTemplate, bool) {
	template, exists := tm.templates[name]
	return template, exists
}

// getTemplatesByCategory returns templates filtered by category
func (tm *QueryTemplateManager) getTemplatesByCategory(category string) []*QueryTemplate {
	var result []*QueryTemplate
	for _, template := range tm.templates {
		if category == "" || template.Category == category {
			result = append(result, template)
		}
	}
	return result
}

// getAllTemplates returns all templates
func (tm *QueryTemplateManager) getAllTemplates() []*QueryTemplate {
	var result []*QueryTemplate
	for _, template := range tm.templates {
		result = append(result, template)
	}
	return result
}

// Global template manager instance
var globalTemplateManager = NewQueryTemplateManager()

// Template functions for the command
func useTemplate(templateName, params, format string) error {
	template, exists := globalTemplateManager.getTemplate(templateName)
	if !exists {
		return fmt.Errorf("template '%s' not found", templateName)
	}

	// Parse parameters
	paramMap := parseTemplateParams(params)

	// Apply template
	query := applyTemplate(template, paramMap)

	// Execute query (mock for now)
	result := executeTemplateQuery(query, templateName, paramMap)

	// Display results
	display := NewResultDisplay(format, "default")
	return display.DisplayResult(result)
}

func listTemplates(category, filterCategory string) error {
	var templates []*QueryTemplate

	if filterCategory != "" {
		templates = globalTemplateManager.getTemplatesByCategory(filterCategory)
	} else if category != "" {
		templates = globalTemplateManager.getTemplatesByCategory(category)
	} else {
		templates = globalTemplateManager.getAllTemplates()
	}

	// Convert templates to displayable format
	var objects []interface{}
	for _, template := range templates {
		objects = append(objects, map[string]interface{}{
			"name":        template.Name,
			"category":    template.Category,
			"description": template.Description,
			"parameters":  len(template.Parameters),
			"tags":        strings.Join(template.Tags, ", "),
		})
	}

	result := &AQLResult{
		Type:    "TEMPLATES",
		Objects: objects,
		Count:   len(objects),
		Message: fmt.Sprintf("Found %d templates", len(objects)),
		Metadata: map[string]interface{}{
			"category_filter": filterCategory,
			"total_templates": len(globalTemplateManager.getAllTemplates()),
		},
		ExecutedAt: time.Now(),
	}

	display := NewResultDisplay("table", "default")
	return display.DisplayResult(result)
}

func showTemplates(category string) error {
	templates := globalTemplateManager.getTemplatesByCategory(category)

	if len(templates) == 0 {
		fmt.Printf("No templates found for category: %s\n", category)
		return nil
	}

	fmt.Printf("=== Query Templates: %s ===\n", category)
	fmt.Println()

	for _, template := range templates {
		fmt.Printf("Template: %s\n", template.Name)
		fmt.Printf("Category: %s\n", template.Category)
		fmt.Printf("Description: %s\n", template.Description)
		fmt.Printf("Query: %s\n", template.Query)

		if len(template.Parameters) > 0 {
			fmt.Println("Parameters:")
			for _, param := range template.Parameters {
				required := ""
				if param.Required {
					required = " (required)"
				}
				fmt.Printf("  - %s (%s): %s%s\n", param.Name, param.Type, param.Description, required)
			}
		}

		if len(template.Examples) > 0 {
			fmt.Println("Examples:")
			for _, example := range template.Examples {
				fmt.Printf("  %s\n", example)
			}
		}

		fmt.Printf("Tags: %s\n", strings.Join(template.Tags, ", "))
		fmt.Println()
	}

	return nil
}

// Helper functions
func parseTemplateParams(params string) map[string]string {
	result := make(map[string]string)
	if params == "" {
		return result
	}

	pairs := strings.Split(params, ",")
	for _, pair := range pairs {
		kv := strings.SplitN(pair, "=", 2)
		if len(kv) == 2 {
			result[strings.TrimSpace(kv[0])] = strings.TrimSpace(kv[1])
		}
	}
	return result
}

func applyTemplate(template *QueryTemplate, params map[string]string) string {
	query := template.Query

	// Replace parameter placeholders
	for _, param := range template.Parameters {
		placeholder := "{" + param.Name + "}"
		value := params[param.Name]

		if value == "" {
			value = param.Default
		}

		// Handle different parameter types
		switch param.Type {
		case "string":
			if value != "" {
				query = strings.ReplaceAll(query, placeholder, "'"+value+"'")
			}
		case "int", "float":
			if value != "" {
				query = strings.ReplaceAll(query, placeholder, value)
			}
		}
	}

	// Handle special filters placeholder
	if strings.Contains(query, "{filters}") {
		filters := buildFilters(params, template.Parameters)
		query = strings.ReplaceAll(query, "{filters}", filters)
	}

	return query
}

func buildFilters(params map[string]string, templateParams []TemplateParameter) string {
	var filters []string

	for _, param := range templateParams {
		if value, exists := params[param.Name]; exists && value != "" {
			switch param.Type {
			case "string":
				filters = append(filters, fmt.Sprintf("AND %s = '%s'", param.Name, value))
			case "int", "float":
				filters = append(filters, fmt.Sprintf("AND %s = %s", param.Name, value))
			}
		}
	}

	if len(filters) > 0 {
		return strings.Join(filters, " ")
	}
	return ""
}

func executeTemplateQuery(query, templateName string, params map[string]string) *AQLResult {
	// For now, generate mock results based on the template
	// In production, this would execute the actual AQL query

	var objects []interface{}
	var message string

	// Generate mock results based on template category
	switch {
	case strings.Contains(templateName, "hvac"):
		objects = generateMockHVACResults()
		message = "HVAC equipment query executed"
	case strings.Contains(templateName, "electrical"):
		objects = generateMockElectricalResults()
		message = "Electrical equipment query executed"
	case strings.Contains(templateName, "maintenance"):
		objects = generateMockMaintenanceResults()
		message = "Maintenance query executed"
	case strings.Contains(templateName, "energy"):
		objects = generateMockEnergyResults()
		message = "Energy consumption query executed"
	default:
		objects = generateMockGenericResults(query)
		message = "Template query executed successfully"
	}

	return &AQLResult{
		Type:    "TEMPLATE",
		Objects: objects,
		Count:   len(objects),
		Message: message,
		Metadata: map[string]interface{}{
			"template":        templateName,
			"generated_query": query,
			"parameters":      params,
			"execution_time":  "0.001s",
		},
		ExecutedAt: time.Now(),
	}
}
