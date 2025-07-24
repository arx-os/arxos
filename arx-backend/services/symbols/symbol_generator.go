package symbols

import (
	"fmt"
	"math/rand"
	"strings"
	"time"

	"github.com/google/uuid"
)

// GenerationTemplate represents a template for symbol generation
type GenerationTemplate struct {
	ID         string                 `json:"id"`
	Name       string                 `json:"name"`
	System     string                 `json:"system"`
	Category   string                 `json:"category"`
	BaseSVG    string                 `json:"base_svg"`
	Parameters []GenerationParameter  `json:"parameters"`
	Variations []string               `json:"variations"`
	Metadata   map[string]interface{} `json:"metadata"`
}

// GenerationParameter represents a parameter for symbol generation
type GenerationParameter struct {
	Name        string   `json:"name"`
	Type        string   `json:"type"`
	Default     string   `json:"default"`
	Description string   `json:"description"`
	Required    bool     `json:"required"`
	Min         float64  `json:"min,omitempty"`
	Max         float64  `json:"max,omitempty"`
	Options     []string `json:"options,omitempty"`
}

// GenerationRequest represents a request to generate symbols
type GenerationRequest struct {
	TemplateID string                 `json:"template_id"`
	Count      int                    `json:"count"`
	Parameters map[string]interface{} `json:"parameters"`
	System     string                 `json:"system"`
	Category   string                 `json:"category"`
	Tags       []string               `json:"tags"`
	Metadata   map[string]interface{} `json:"metadata"`
}

// GenerationResult represents the result of symbol generation
type GenerationResult struct {
	GeneratedSymbols []*Symbol              `json:"generated_symbols"`
	TemplateUsed     string                 `json:"template_used"`
	Parameters       map[string]interface{} `json:"parameters"`
	GenerationTime   time.Duration          `json:"generation_time"`
	Errors           []string               `json:"errors,omitempty"`
}

// SymbolGenerator provides functionality for generating symbols
type SymbolGenerator struct {
	templates map[string]*GenerationTemplate
	random    *rand.Rand
}

// NewSymbolGenerator creates a new symbol generator
func NewSymbolGenerator() *SymbolGenerator {
	return &SymbolGenerator{
		templates: make(map[string]*GenerationTemplate),
		random:    rand.New(rand.NewSource(time.Now().UnixNano())),
	}
}

// RegisterTemplate registers a generation template
func (g *SymbolGenerator) RegisterTemplate(template *GenerationTemplate) error {
	if template.ID == "" {
		return fmt.Errorf("template ID is required")
	}

	if template.Name == "" {
		return fmt.Errorf("template name is required")
	}

	if template.BaseSVG == "" {
		return fmt.Errorf("template base SVG is required")
	}

	g.templates[template.ID] = template
	return nil
}

// GenerateSymbols generates symbols based on a template and parameters
func (g *SymbolGenerator) GenerateSymbols(request GenerationRequest) GenerationResult {
	startTime := time.Now()
	result := GenerationResult{
		GeneratedSymbols: []*Symbol{},
		TemplateUsed:     request.TemplateID,
		Parameters:       request.Parameters,
		Errors:           []string{},
	}

	// Validate request
	if err := g.validateGenerationRequest(request); err != nil {
		result.Errors = append(result.Errors, err.Error())
		return result
	}

	// Get template
	template, exists := g.templates[request.TemplateID]
	if !exists {
		result.Errors = append(result.Errors, fmt.Sprintf("template '%s' not found", request.TemplateID))
		return result
	}

	// Generate symbols
	for i := 0; i < request.Count; i++ {
		symbol, err := g.generateSingleSymbol(template, request, i)
		if err != nil {
			result.Errors = append(result.Errors, fmt.Sprintf("symbol %d: %v", i+1, err))
			continue
		}
		result.GeneratedSymbols = append(result.GeneratedSymbols, symbol)
	}

	result.GenerationTime = time.Since(startTime)
	return result
}

// GenerateFromPattern generates symbols based on a pattern
func (g *SymbolGenerator) GenerateFromPattern(pattern string, count int, system string) GenerationResult {
	startTime := time.Now()
	result := GenerationResult{
		GeneratedSymbols: []*Symbol{},
		TemplateUsed:     "pattern_based",
		Parameters:       map[string]interface{}{"pattern": pattern},
		Errors:           []string{},
	}

	// Parse pattern and generate symbols
	for i := 0; i < count; i++ {
		symbol, err := g.generateFromPattern(pattern, system, i)
		if err != nil {
			result.Errors = append(result.Errors, fmt.Sprintf("symbol %d: %v", i+1, err))
			continue
		}
		result.GeneratedSymbols = append(result.GeneratedSymbols, symbol)
	}

	result.GenerationTime = time.Since(startTime)
	return result
}

// GenerateVariations generates variations of an existing symbol
func (g *SymbolGenerator) GenerateVariations(baseSymbol *Symbol, count int) GenerationResult {
	startTime := time.Now()
	result := GenerationResult{
		GeneratedSymbols: []*Symbol{},
		TemplateUsed:     "variation_based",
		Parameters:       map[string]interface{}{"base_symbol_id": baseSymbol.ID},
		Errors:           []string{},
	}

	// Generate variations
	for i := 0; i < count; i++ {
		variation, err := g.generateVariation(baseSymbol, i)
		if err != nil {
			result.Errors = append(result.Errors, fmt.Sprintf("variation %d: %v", i+1, err))
			continue
		}
		result.GeneratedSymbols = append(result.GeneratedSymbols, variation)
	}

	result.GenerationTime = time.Since(startTime)
	return result
}

// GetTemplates returns all registered templates
func (g *SymbolGenerator) GetTemplates() []*GenerationTemplate {
	var templates []*GenerationTemplate
	for _, template := range g.templates {
		templates = append(templates, template)
	}
	return templates
}

// GetTemplate returns a specific template by ID
func (g *SymbolGenerator) GetTemplate(templateID string) (*GenerationTemplate, error) {
	template, exists := g.templates[templateID]
	if !exists {
		return nil, fmt.Errorf("template '%s' not found", templateID)
	}
	return template, nil
}

// Helper methods

func (g *SymbolGenerator) validateGenerationRequest(request GenerationRequest) error {
	if request.TemplateID == "" {
		return fmt.Errorf("template ID is required")
	}

	if request.Count <= 0 {
		return fmt.Errorf("count must be greater than 0")
	}

	if request.Count > 100 {
		return fmt.Errorf("count cannot exceed 100")
	}

	return nil
}

func (g *SymbolGenerator) generateSingleSymbol(template *GenerationTemplate, request GenerationRequest, index int) (*Symbol, error) {
	// Generate unique ID
	symbolID := fmt.Sprintf("%s_%s_%d", template.ID, uuid.New().String()[:8], index)

	// Generate name
	name := g.generateSymbolName(template, request, index)

	// Generate SVG content
	svgContent := g.generateSVGContent(template, request, index)

	// Create symbol
	symbol := &Symbol{
		ID:          symbolID,
		Name:        name,
		System:      request.System,
		Category:    request.Category,
		Description: g.generateDescription(template, request),
		SVG: SVGContent{
			Content: svgContent,
			Width:   g.generateDimension(template, "width", request),
			Height:  g.generateDimension(template, "height", request),
			Scale:   g.generateDimension(template, "scale", request),
		},
		Properties:  g.generateProperties(template, request),
		Connections: g.generateConnections(template, request),
		Tags:        request.Tags,
		Metadata:    g.generateMetadata(template, request),
		Version:     "1.0",
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	return symbol, nil
}

func (g *SymbolGenerator) generateSymbolName(template *GenerationTemplate, request GenerationRequest, index int) string {
	if len(template.Variations) > 0 {
		variation := template.Variations[index%len(template.Variations)]
		return fmt.Sprintf("%s %s", template.Name, variation)
	}

	// Generate based on pattern
	if pattern, exists := request.Parameters["name_pattern"]; exists {
		if patternStr, ok := pattern.(string); ok {
			return g.applyPattern(patternStr, index)
		}
	}

	// Default naming
	return fmt.Sprintf("%s %d", template.Name, index+1)
}

func (g *SymbolGenerator) generateSVGContent(template *GenerationTemplate, request GenerationRequest, index int) string {
	svgContent := template.BaseSVG

	// Apply parameter substitutions
	for paramName, paramValue := range request.Parameters {
		placeholder := fmt.Sprintf("{{%s}}", paramName)
		valueStr := fmt.Sprintf("%v", paramValue)
		svgContent = strings.ReplaceAll(svgContent, placeholder, valueStr)
	}

	// Apply random variations
	svgContent = g.applyRandomVariations(svgContent, index)

	return svgContent
}

func (g *SymbolGenerator) generateDescription(template *GenerationTemplate, request GenerationRequest) string {
	if desc, exists := request.Parameters["description"]; exists {
		if descStr, ok := desc.(string); ok {
			return descStr
		}
	}

	return fmt.Sprintf("Generated %s symbol", template.Name)
}

func (g *SymbolGenerator) generateDimension(template *GenerationTemplate, dimType string, request GenerationRequest) float64 {
	// Check if dimension is specified in parameters
	if dim, exists := request.Parameters[dimType]; exists {
		if dimFloat, ok := dim.(float64); ok {
			return dimFloat
		}
	}

	// Generate random dimension within reasonable bounds
	switch dimType {
	case "width":
		return float64(g.random.Intn(50) + 20) // 20-70
	case "height":
		return float64(g.random.Intn(50) + 20) // 20-70
	case "scale":
		return 0.5 + g.random.Float64()*1.5 // 0.5-2.0
	default:
		return 1.0
	}
}

func (g *SymbolGenerator) generateProperties(template *GenerationTemplate, request GenerationRequest) map[string]interface{} {
	properties := make(map[string]interface{})

	// Copy template properties
	if template.Metadata != nil {
		if templateProps, exists := template.Metadata["properties"]; exists {
			if propsMap, ok := templateProps.(map[string]interface{}); ok {
				for k, v := range propsMap {
					properties[k] = v
				}
			}
		}
	}

	// Override with request properties
	for k, v := range request.Parameters {
		if strings.HasPrefix(k, "prop_") {
			propName := strings.TrimPrefix(k, "prop_")
			properties[propName] = v
		}
	}

	return properties
}

func (g *SymbolGenerator) generateConnections(template *GenerationTemplate, request GenerationRequest) []Connection {
	var connections []Connection

	// Generate connections based on template
	if template.Metadata != nil {
		if templateConns, exists := template.Metadata["connections"]; exists {
			if connsSlice, ok := templateConns.([]interface{}); ok {
				for _, conn := range connsSlice {
					if connMap, ok := conn.(map[string]interface{}); ok {
						connection := Connection{
							ID:   g.getStringValue(connMap, "id", ""),
							Type: g.getStringValue(connMap, "type", ""),
						}
						if posData, exists := connMap["position"]; exists {
							if posMap, ok := posData.(map[string]interface{}); ok {
								x, _ := posMap["x"].(float64)
								y, _ := posMap["y"].(float64)
								connection.Position = Point{X: x, Y: y}
							}
						}
						connections = append(connections, connection)
					}
				}
			}
		}
	}

	return connections
}

func (g *SymbolGenerator) generateMetadata(template *GenerationTemplate, request GenerationRequest) map[string]interface{} {
	metadata := make(map[string]interface{})

	// Copy template metadata
	if template.Metadata != nil {
		for k, v := range template.Metadata {
			if k != "properties" && k != "connections" {
				metadata[k] = v
			}
		}
	}

	// Add generation metadata
	metadata["generated_by"] = "symbol_generator"
	metadata["template_id"] = template.ID
	metadata["generation_parameters"] = request.Parameters

	// Override with request metadata
	for k, v := range request.Metadata {
		metadata[k] = v
	}

	return metadata
}

func (g *SymbolGenerator) generateFromPattern(pattern string, system string, index int) (*Symbol, error) {
	// Parse pattern and generate symbol
	symbolID := fmt.Sprintf("pattern_%s_%d", uuid.New().String()[:8], index)

	name := g.applyPattern(pattern, index)
	svgContent := g.generatePatternSVG(pattern, index)

	symbol := &Symbol{
		ID:          symbolID,
		Name:        name,
		System:      system,
		Category:    "pattern_generated",
		Description: fmt.Sprintf("Generated from pattern: %s", pattern),
		SVG: SVGContent{
			Content: svgContent,
			Width:   float64(g.random.Intn(50) + 20),
			Height:  float64(g.random.Intn(50) + 20),
			Scale:   1.0,
		},
		Properties:  make(map[string]interface{}),
		Connections: []Connection{},
		Tags:        []string{"pattern_generated"},
		Metadata: map[string]interface{}{
			"generated_by": "pattern_generator",
			"pattern":      pattern,
		},
		Version:   "1.0",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	return symbol, nil
}

func (g *SymbolGenerator) generateVariation(baseSymbol *Symbol, index int) (*Symbol, error) {
	// Create variation of base symbol
	variationID := fmt.Sprintf("%s_var_%d", baseSymbol.ID, index)

	// Modify SVG content
	variedSVG := g.applyVariationToSVG(baseSymbol.SVG.Content, index)

	variation := &Symbol{
		ID:          variationID,
		Name:        fmt.Sprintf("%s Variation %d", baseSymbol.Name, index+1),
		System:      baseSymbol.System,
		Category:    baseSymbol.Category,
		Description: fmt.Sprintf("Variation of %s", baseSymbol.Name),
		SVG: SVGContent{
			Content: variedSVG,
			Width:   baseSymbol.SVG.Width * (0.8 + g.random.Float64()*0.4),  // ±20%
			Height:  baseSymbol.SVG.Height * (0.8 + g.random.Float64()*0.4), // ±20%
			Scale:   baseSymbol.SVG.Scale,
		},
		Properties:  baseSymbol.Properties,
		Connections: baseSymbol.Connections,
		Tags:        append(baseSymbol.Tags, "variation"),
		Metadata: map[string]interface{}{
			"generated_by":    "variation_generator",
			"base_symbol_id":  baseSymbol.ID,
			"variation_index": index,
		},
		Version:   "1.0",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	return variation, nil
}

func (g *SymbolGenerator) applyPattern(pattern string, index int) string {
	// Replace pattern placeholders
	result := pattern
	result = strings.ReplaceAll(result, "{{index}}", fmt.Sprintf("%d", index+1))
	result = strings.ReplaceAll(result, "{{random}}", fmt.Sprintf("%d", g.random.Intn(1000)))
	result = strings.ReplaceAll(result, "{{uuid}}", uuid.New().String()[:8])
	return result
}

func (g *SymbolGenerator) generatePatternSVG(pattern string, index int) string {
	// Generate basic SVG based on pattern
	return fmt.Sprintf(`<svg width="50" height="50" xmlns="http://www.w3.org/2000/svg">
		<rect width="50" height="50" fill="none" stroke="black" stroke-width="2"/>
		<text x="25" y="30" text-anchor="middle" font-size="12">%s</text>
	</svg>`, pattern)
}

func (g *SymbolGenerator) applyRandomVariations(svgContent string, index int) string {
	// Apply random color variations
	colors := []string{"#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#feca57", "#ff9ff3"}
	color := colors[index%len(colors)]

	// Replace color placeholders
	svgContent = strings.ReplaceAll(svgContent, "{{color}}", color)
	svgContent = strings.ReplaceAll(svgContent, "{{stroke_color}}", color)

	return svgContent
}

func (g *SymbolGenerator) applyVariationToSVG(svgContent string, index int) string {
	// Apply simple variations to SVG content
	// This is a placeholder implementation
	// In practice, you'd apply more sophisticated transformations

	// Add a small random offset
	offsetX := g.random.Intn(10) - 5
	offsetY := g.random.Intn(10) - 5

	// Simple transformation
	if strings.Contains(svgContent, "transform=") {
		// Add to existing transform
		svgContent = strings.ReplaceAll(svgContent, "transform=\"", fmt.Sprintf("transform=\"translate(%d,%d) ", offsetX, offsetY))
	} else {
		// Add new transform
		svgContent = strings.ReplaceAll(svgContent, "<svg", fmt.Sprintf("<svg transform=\"translate(%d,%d)\"", offsetX, offsetY))
	}

	return svgContent
}

func (g *SymbolGenerator) getStringValue(data map[string]interface{}, key string, defaultValue string) string {
	if value, exists := data[key]; exists {
		if str, ok := value.(string); ok {
			return str
		}
	}
	return defaultValue
}
