package symbols

import (
	"fmt"
	"math"
	"regexp"
	"strings"
	"time"

	"github.com/google/uuid"
)

// RenderedSymbol represents a rendered symbol in SVG
type RenderedSymbol struct {
	ObjectID    string                 `json:"object_id"`
	SymbolID    string                 `json:"symbol_id"`
	SymbolName  string                 `json:"symbol_name"`
	System      string                 `json:"system"`
	Category    string                 `json:"category"`
	Position    Point                  `json:"position"`
	Confidence  float64                `json:"confidence"`
	MatchType   string                 `json:"match_type"`
	RenderedAt  time.Time              `json:"rendered_at"`
	BuildingID  string                 `json:"building_id"`
	FloorLabel  string                 `json:"floor_label"`
	Properties  map[string]interface{} `json:"properties"`
	Connections []Connection           `json:"connections"`
	Tags        []string               `json:"tags"`
}

// RenderResult represents the result of rendering symbols
type RenderResult struct {
	SVG             string           `json:"svg"`
	RenderedSymbols []RenderedSymbol `json:"rendered_symbols"`
	TotalRecognized int              `json:"total_recognized"`
	TotalRendered   int              `json:"total_rendered"`
	BuildingID      string           `json:"building_id"`
	FloorLabel      string           `json:"floor_label"`
	Error           string           `json:"error,omitempty"`
}

// SymbolRenderer provides rendering functionality for symbols
type SymbolRenderer struct {
	svgNamespace string
	arxNamespace string
}

// NewSymbolRenderer creates a new symbol renderer
func NewSymbolRenderer() *SymbolRenderer {
	return &SymbolRenderer{
		svgNamespace: "http://www.w3.org/2000/svg",
		arxNamespace: "http://arxos.io/svg",
	}
}

// RenderRecognizedSymbols renders recognized symbols into SVG-BIM
func (r *SymbolRenderer) RenderRecognizedSymbols(svgContent string, recognizedSymbols []map[string]interface{},
	buildingID string, floorLabel string) RenderResult {

	result := RenderResult{
		SVG:             svgContent,
		RenderedSymbols: []RenderedSymbol{},
		TotalRecognized: len(recognizedSymbols),
		TotalRendered:   0,
		BuildingID:      buildingID,
		FloorLabel:      floorLabel,
	}

	// Parse SVG content
	svgData, err := r.parseSVG(svgContent)
	if err != nil {
		result.Error = fmt.Sprintf("Failed to parse SVG: %v", err)
		return result
	}

	// Find or create arx-objects group
	arxGroup := r.findOrCreateArxGroup(svgData)

	// Render each recognized symbol
	for _, symbolInfo := range recognizedSymbols {
		confidence, _ := symbolInfo["confidence"].(float64)

		// Only render high-confidence matches
		if confidence >= 0.5 {
			renderedSymbol := r.renderSingleSymbol(arxGroup, symbolInfo, buildingID, floorLabel)
			if renderedSymbol != nil {
				result.RenderedSymbols = append(result.RenderedSymbols, *renderedSymbol)
				result.TotalRendered++
			}
		}
	}

	// Convert back to string
	result.SVG = r.svgToString(svgData)

	return result
}

// UpdateSymbolPosition updates the position of an existing symbol
func (r *SymbolRenderer) UpdateSymbolPosition(svgContent string, objectID string, newPosition Point) string {
	svgData, err := r.parseSVG(svgContent)
	if err != nil {
		return svgContent
	}

	// Find the symbol element
	symbolElem := r.findSymbolElement(svgData, objectID)
	if symbolElem != nil {
		// Update transform
		symbolElem.Attributes["transform"] = fmt.Sprintf("translate(%.2f,%.2f)", newPosition.X, newPosition.Y)

		// Update metadata
		symbolElem.Attributes["data-updated-at"] = time.Now().Format(time.RFC3339)
	}

	return r.svgToString(svgData)
}

// RemoveSymbol removes a symbol from the SVG
func (r *SymbolRenderer) RemoveSymbol(svgContent string, objectID string) string {
	svgData, err := r.parseSVG(svgContent)
	if err != nil {
		return svgContent
	}

	// Find and remove the symbol element
	r.removeSymbolElement(svgData, objectID)

	return r.svgToString(svgData)
}

// GetRenderedSymbols extracts metadata from rendered symbols in SVG
func (r *SymbolRenderer) GetRenderedSymbols(svgContent string) []RenderedSymbol {
	var symbols []RenderedSymbol

	svgData, err := r.parseSVG(svgContent)
	if err != nil {
		return symbols
	}

	// Find all arx-symbol groups
	arxGroups := r.findArxSymbolGroups(svgData)
	for _, group := range arxGroups {
		symbol := r.extractSymbolMetadata(group)
		if symbol != nil {
			symbols = append(symbols, *symbol)
		}
	}

	return symbols
}

// Helper methods

func (r *SymbolRenderer) parseSVG(svgContent string) (*SVGData, error) {
	// This is a simplified SVG parser
	// In a real implementation, you would use a proper XML/SVG parser

	svgData := &SVGData{
		Elements: []SVGElement{},
	}

	// Basic parsing - extract groups and elements
	// This is a placeholder implementation
	// In practice, you'd use an XML parser like encoding/xml

	return svgData, nil
}

func (r *SymbolRenderer) findOrCreateArxGroup(svgData *SVGData) *SVGElement {
	// Look for existing arx-objects group
	for i := range svgData.Elements {
		if svgData.Elements[i].Tag == "g" && svgData.Elements[i].Attributes["id"] == "arx-objects" {
			return &svgData.Elements[i]
		}
	}

	// Create new arx-objects group
	arxGroup := SVGElement{
		Tag: "g",
		Attributes: map[string]string{
			"id":    "arx-objects",
			"class": "arx-dynamic-objects",
		},
		Children: []SVGElement{},
	}

	svgData.Elements = append(svgData.Elements, arxGroup)
	return &svgData.Elements[len(svgData.Elements)-1]
}

func (r *SymbolRenderer) renderSingleSymbol(arxGroup *SVGElement, symbolInfo map[string]interface{},
	buildingID string, floorLabel string) *RenderedSymbol {

	symbolID, _ := symbolInfo["symbol_id"].(string)
	symbolData, _ := symbolInfo["symbol_data"].(map[string]interface{})
	confidence, _ := symbolInfo["confidence"].(float64)
	matchType, _ := symbolInfo["match_type"].(string)

	// Generate unique object ID
	objectID := fmt.Sprintf("%s_%s", symbolID, uuid.New().String()[:8])

	// Determine position
	position := r.determineSymbolPosition(symbolInfo, arxGroup)

	// Create the symbol element
	symbolElement := r.createSymbolElement(symbolID, symbolData, objectID, position, confidence, matchType)

	// Add to arx-group
	arxGroup.Children = append(arxGroup.Children, *symbolElement)

	// Create metadata
	metadata := RenderedSymbol{
		ObjectID:    objectID,
		SymbolID:    symbolID,
		SymbolName:  r.getStringValue(symbolData, "display_name", symbolID),
		System:      r.getStringValue(symbolData, "system", "unknown"),
		Category:    r.getStringValue(symbolData, "category", ""),
		Position:    position,
		Confidence:  confidence,
		MatchType:   matchType,
		RenderedAt:  time.Now(),
		BuildingID:  buildingID,
		FloorLabel:  floorLabel,
		Properties:  r.getMapValue(symbolData, "properties"),
		Connections: r.getConnections(symbolData),
		Tags:        r.getStringSlice(symbolData, "tags"),
	}

	return &metadata
}

func (r *SymbolRenderer) determineSymbolPosition(symbolInfo map[string]interface{}, arxGroup *SVGElement) Point {
	// If we have a position from SVG text recognition, use it
	if pos, exists := symbolInfo["position"]; exists {
		if posMap, ok := pos.(map[string]interface{}); ok {
			x, _ := posMap["x"].(float64)
			y, _ := posMap["y"].(float64)
			return Point{X: x, Y: y}
		}
	}

	// Calculate position based on existing symbols
	return r.calculateAutoPosition(arxGroup, symbolInfo)
}

func (r *SymbolRenderer) calculateAutoPosition(arxGroup *SVGElement, symbolInfo map[string]interface{}) Point {
	// Get existing symbol positions
	existingPositions := r.getExistingPositions(arxGroup)

	// Calculate new position
	if len(existingPositions) > 0 {
		// Find a position that doesn't overlap
		baseX, baseY := existingPositions[len(existingPositions)-1].X, existingPositions[len(existingPositions)-1].Y
		offset := 50.0

		// Try positions in a grid pattern
		for i := 0; i < 10; i++ {
			x := baseX + float64(i%3)*offset
			y := baseY + float64(i/3)*offset

			// Check if position is far enough from existing symbols
			if !r.isPositionOverlapping(x, y, existingPositions) {
				return Point{X: x, Y: y}
			}
		}

		// If no good position found, just offset from last
		lastPos := existingPositions[len(existingPositions)-1]
		return Point{X: lastPos.X + offset, Y: lastPos.Y + offset}
	}

	// First symbol - place at origin
	return Point{X: 100, Y: 100}
}

func (r *SymbolRenderer) getExistingPositions(arxGroup *SVGElement) []Point {
	var positions []Point

	for _, child := range arxGroup.Children {
		if transform, exists := child.Attributes["transform"]; exists {
			if pos := r.extractPositionFromTransform(transform); pos != nil {
				positions = append(positions, *pos)
			}
		}
	}

	return positions
}

func (r *SymbolRenderer) extractPositionFromTransform(transform string) *Point {
	// Parse translate(x,y) from transform
	re := regexp.MustCompile(`translate\(([^,]+),([^)]+)\)`)
	matches := re.FindStringSubmatch(transform)
	if len(matches) == 3 {
		if x, err := r.parseFloat(matches[1]); err == nil {
			if y, err := r.parseFloat(matches[2]); err == nil {
				return &Point{X: x, Y: y}
			}
		}
	}
	return nil
}

func (r *SymbolRenderer) parseFloat(s string) (float64, error) {
	// Simple float parsing - in practice you'd use strconv.ParseFloat
	return 0, fmt.Errorf("not implemented")
}

func (r *SymbolRenderer) isPositionOverlapping(x, y float64, existingPositions []Point) bool {
	for _, pos := range existingPositions {
		distance := math.Sqrt(math.Pow(x-pos.X, 2) + math.Pow(y-pos.Y, 2))
		if distance < 30 {
			return true
		}
	}
	return false
}

func (r *SymbolRenderer) createSymbolElement(symbolID string, symbolData map[string]interface{},
	objectID string, position Point, confidence float64, matchType string) *SVGElement {

	// Get the symbol's SVG content
	symbolSVG := r.getStringValue(symbolData, "svg", "")

	// Create the main group element
	groupAttrs := map[string]string{
		"id":               objectID,
		"class":            fmt.Sprintf("arx-symbol arx-%s", symbolID),
		"transform":        fmt.Sprintf("translate(%.2f,%.2f)", position.X, position.Y),
		"data-symbol-id":   symbolID,
		"data-symbol-name": r.getStringValue(symbolData, "display_name", symbolID),
		"data-system":      r.getStringValue(symbolData, "system", "unknown"),
		"data-category":    r.getStringValue(symbolData, "category", ""),
		"data-confidence":  fmt.Sprintf("%.2f", confidence),
		"data-match-type":  matchType,
		"data-rendered-at": time.Now().Format(time.RFC3339),
	}

	group := &SVGElement{
		Tag:        "g",
		Attributes: groupAttrs,
		Children:   []SVGElement{},
	}

	// Add the symbol SVG content
	if symbolSVG != "" {
		if symbolRoot, err := r.parseSVG(symbolSVG); err == nil {
			// Copy all child elements
			group.Children = append(group.Children, symbolRoot.Elements...)
		} else {
			// Fallback: add as text
			textElem := SVGElement{
				Tag: "text",
				Attributes: map[string]string{
					"x":           "0",
					"y":           "0",
					"font-size":   "12",
					"text-anchor": "middle",
				},
				Text: r.getStringValue(symbolData, "display_name", symbolID),
			}
			group.Children = append(group.Children, textElem)
		}
	}

	// Add confidence indicator
	if confidence < 0.8 {
		confidenceColor := "#ff6b6b"
		if confidence >= 0.6 {
			confidenceColor = "#ffd93d"
		}

		confidenceIndicator := SVGElement{
			Tag: "circle",
			Attributes: map[string]string{
				"cx":               "0",
				"cy":               "0",
				"r":                "15",
				"fill":             "none",
				"stroke":           confidenceColor,
				"stroke-width":     "2",
				"stroke-dasharray": "5,5",
				"opacity":          "0.7",
			},
		}
		group.Children = append(group.Children, confidenceIndicator)
	}

	// Add metadata text
	metadataText := SVGElement{
		Tag: "text",
		Attributes: map[string]string{
			"x":           "0",
			"y":           "25",
			"font-size":   "8",
			"text-anchor": "middle",
			"fill":        "#666",
			"class":       "arx-metadata",
		},
		Text: fmt.Sprintf("%s (%.1f)", r.getStringValue(symbolData, "display_name", symbolID), confidence),
	}
	group.Children = append(group.Children, metadataText)

	return group
}

func (r *SymbolRenderer) findSymbolElement(svgData *SVGData, objectID string) *SVGElement {
	// Recursively search for element with matching ID
	return r.findElementByID(svgData.Elements, objectID)
}

func (r *SymbolRenderer) findElementByID(elements []SVGElement, objectID string) *SVGElement {
	for i := range elements {
		if elements[i].Attributes["id"] == objectID {
			return &elements[i]
		}
		if len(elements[i].Children) > 0 {
			if found := r.findElementByID(elements[i].Children, objectID); found != nil {
				return found
			}
		}
	}
	return nil
}

func (r *SymbolRenderer) removeSymbolElement(svgData *SVGData, objectID string) {
	// Remove element by ID from the SVG data structure
	r.removeElementByID(&svgData.Elements, objectID)
}

func (r *SymbolRenderer) removeElementByID(elements *[]SVGElement, objectID string) {
	for i := len(*elements) - 1; i >= 0; i-- {
		if (*elements)[i].Attributes["id"] == objectID {
			// Remove element
			*elements = append((*elements)[:i], (*elements)[i+1:]...)
			return
		}
		if len((*elements)[i].Children) > 0 {
			r.removeElementByID(&(*elements)[i].Children, objectID)
		}
	}
}

func (r *SymbolRenderer) findArxSymbolGroups(svgData *SVGData) []*SVGElement {
	var groups []*SVGElement
	r.findGroupsByClass(svgData.Elements, "arx-symbol", &groups)
	return groups
}

func (r *SymbolRenderer) findGroupsByClass(elements []SVGElement, className string, groups *[]*SVGElement) {
	for i := range elements {
		if elements[i].Tag == "g" && strings.Contains(elements[i].Attributes["class"], className) {
			*groups = append(*groups, &elements[i])
		}
		if len(elements[i].Children) > 0 {
			r.findGroupsByClass(elements[i].Children, className, groups)
		}
	}
}

func (r *SymbolRenderer) extractSymbolMetadata(group *SVGElement) *RenderedSymbol {
	symbolData := RenderedSymbol{
		ObjectID:   group.Attributes["id"],
		SymbolID:   group.Attributes["data-symbol-id"],
		SymbolName: group.Attributes["data-symbol-name"],
		System:     group.Attributes["data-system"],
		Category:   group.Attributes["data-category"],
		MatchType:  group.Attributes["data-match-type"],
	}

	// Parse confidence
	if confidenceStr := group.Attributes["data-confidence"]; confidenceStr != "" {
		if confidence, err := r.parseFloat(confidenceStr); err == nil {
			symbolData.Confidence = confidence
		}
	}

	// Parse position from transform
	if transform := group.Attributes["transform"]; transform != "" {
		if pos := r.extractPositionFromTransform(transform); pos != nil {
			symbolData.Position = *pos
		}
	}

	// Parse rendered_at
	if renderedAtStr := group.Attributes["data-rendered-at"]; renderedAtStr != "" {
		if renderedAt, err := time.Parse(time.RFC3339, renderedAtStr); err == nil {
			symbolData.RenderedAt = renderedAt
		}
	}

	return &symbolData
}

func (r *SymbolRenderer) svgToString(svgData *SVGData) string {
	// Convert SVG data structure back to string
	// This is a placeholder implementation
	return "<svg>...</svg>"
}

// Helper methods for data extraction

func (r *SymbolRenderer) getStringValue(data map[string]interface{}, key string, defaultValue string) string {
	if value, exists := data[key]; exists {
		if str, ok := value.(string); ok {
			return str
		}
	}
	return defaultValue
}

func (r *SymbolRenderer) getMapValue(data map[string]interface{}, key string) map[string]interface{} {
	if value, exists := data[key]; exists {
		if mapValue, ok := value.(map[string]interface{}); ok {
			return mapValue
		}
	}
	return make(map[string]interface{})
}

func (r *SymbolRenderer) getStringSlice(data map[string]interface{}, key string) []string {
	if value, exists := data[key]; exists {
		if slice, ok := value.([]interface{}); ok {
			var result []string
			for _, item := range slice {
				if str, ok := item.(string); ok {
					result = append(result, str)
				}
			}
			return result
		}
	}
	return []string{}
}

func (r *SymbolRenderer) getConnections(data map[string]interface{}) []Connection {
	if value, exists := data["connections"]; exists {
		if slice, ok := value.([]interface{}); ok {
			var connections []Connection
			for _, item := range slice {
				if connMap, ok := item.(map[string]interface{}); ok {
					conn := Connection{
						ID:   r.getStringValue(connMap, "id", ""),
						Type: r.getStringValue(connMap, "type", ""),
					}
					if posData, exists := connMap["position"]; exists {
						if posMap, ok := posData.(map[string]interface{}); ok {
							x, _ := posMap["x"].(float64)
							y, _ := posMap["y"].(float64)
							conn.Position = Point{X: x, Y: y}
						}
					}
					connections = append(connections, conn)
				}
			}
			return connections
		}
	}
	return []Connection{}
}

// SVGData represents the structure of SVG data
type SVGData struct {
	Elements []SVGElement
}

// SVGElement represents an SVG element
type SVGElement struct {
	Tag        string            `json:"tag"`
	Attributes map[string]string `json:"attributes"`
	Text       string            `json:"text,omitempty"`
	Children   []SVGElement      `json:"children,omitempty"`
}
