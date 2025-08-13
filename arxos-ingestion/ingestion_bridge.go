package ingestion

import (
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/arxos/arxos-core"
)

// IngestionBridge connects the existing symbol recognition to ArxObject creation
type IngestionBridge struct {
	symbolRecognizer *SymbolRecognizer
	arxRepo          *arxoscore.ArxObjectRepository
	symbolLibrary    map[string]*SymbolDefinition
}

// SymbolDefinition represents a recognized symbol from the library
type SymbolDefinition struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	System      string                 `json:"system"`
	Category    string                 `json:"category"`
	DisplayName string                 `json:"display_name"`
	Tags        []string               `json:"tags"`
	Properties  map[string]interface{} `json:"properties"`
	SVG         string                 `json:"svg"`
	Confidence  float64                `json:"confidence"`
}

// RecognizedSymbol represents a symbol found in a document
type RecognizedSymbol struct {
	Definition   *SymbolDefinition
	Position     Position
	Rotation     float64
	Scale        float64
	Context      string
	SourcePage   int
	Confidence   float64
	Connections  []Connection
	ParentSpace  string // room or area this symbol belongs to
}

// Position represents 3D coordinates
type Position struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

// Connection represents a relationship between symbols
type Connection struct {
	ToSymbolID string
	Type       string // electrical_feed, control, data, physical
	Properties map[string]interface{}
}

// NewIngestionBridge creates a new ingestion bridge
func NewIngestionBridge(arxRepo *arxoscore.ArxObjectRepository) (*IngestionBridge, error) {
	recognizer, err := NewSymbolRecognizer()
	if err != nil {
		return nil, fmt.Errorf("failed to create symbol recognizer: %w", err)
	}

	bridge := &IngestionBridge{
		symbolRecognizer: recognizer,
		arxRepo:          arxRepo,
		symbolLibrary:    make(map[string]*SymbolDefinition),
	}

	// Load symbol library
	if err := bridge.loadSymbolLibrary(); err != nil {
		return nil, fmt.Errorf("failed to load symbol library: %w", err)
	}

	return bridge, nil
}

// loadSymbolLibrary loads the existing symbol definitions
func (b *IngestionBridge) loadSymbolLibrary() error {
	// This would connect to the Python symbol recognition engine
	// For now, we'll define the core symbols that exist in the Python code
	
	// Electrical symbols
	b.symbolLibrary["electrical_outlet"] = &SymbolDefinition{
		ID:          "electrical_outlet",
		Name:        "Electrical Outlet",
		System:      "electrical",
		Category:    "electrical",
		DisplayName: "Electrical Outlet",
		Tags:        []string{"outlet", "electrical", "power"},
	}

	b.symbolLibrary["light_fixture"] = &SymbolDefinition{
		ID:          "light_fixture",
		Name:        "Light Fixture",
		System:      "electrical",
		Category:    "electrical",
		DisplayName: "Light Fixture",
		Tags:        []string{"light", "fixture", "electrical", "illumination"},
	}

	// HVAC symbols
	b.symbolLibrary["hvac_duct"] = &SymbolDefinition{
		ID:          "hvac_duct",
		Name:        "HVAC Duct",
		System:      "mechanical",
		Category:    "mechanical",
		DisplayName: "HVAC Duct",
		Tags:        []string{"duct", "hvac", "air", "mechanical"},
	}

	// Plumbing symbols
	b.symbolLibrary["pipe"] = &SymbolDefinition{
		ID:          "pipe",
		Name:        "Pipe",
		System:      "plumbing",
		Category:    "plumbing",
		DisplayName: "Pipe",
		Tags:        []string{"pipe", "plumbing", "water", "gas"},
	}

	// Fire protection symbols
	b.symbolLibrary["sprinkler"] = &SymbolDefinition{
		ID:          "sprinkler",
		Name:        "Sprinkler",
		System:      "fire_protection",
		Category:    "fire_protection",
		DisplayName: "Sprinkler",
		Tags:        []string{"sprinkler", "fire", "protection", "water"},
	}

	// Structural symbols
	b.symbolLibrary["wall"] = &SymbolDefinition{
		ID:          "wall",
		Name:        "Wall",
		System:      "structural",
		Category:    "structural",
		DisplayName: "Wall",
		Tags:        []string{"wall", "partition", "structural"},
	}

	b.symbolLibrary["door"] = &SymbolDefinition{
		ID:          "door",
		Name:        "Door",
		System:      "architectural",
		Category:    "architectural",
		DisplayName: "Door",
		Tags:        []string{"door", "entrance", "exit"},
	}

	b.symbolLibrary["window"] = &SymbolDefinition{
		ID:          "window",
		Name:        "Window",
		System:      "architectural",
		Category:    "architectural",
		DisplayName: "Window",
		Tags:        []string{"window", "glazing", "opening"},
	}

	return nil
}

// ConvertToArxObject converts a recognized symbol into an ArxObject
func (b *IngestionBridge) ConvertToArxObject(symbol *RecognizedSymbol, parentID string) (*arxoscore.ArxObject, error) {
	// Generate hierarchical ID
	id := b.generateArxID(parentID, symbol)

	// Determine object type from symbol
	objType := b.getObjectType(symbol.Definition)

	// Calculate scale visibility based on object type
	scaleMin, scaleMax := b.calculateScaleRange(objType)

	// Create ArxObject
	arxObj := arxoscore.NewArxObject(
		id,
		objType,
		symbol.Definition.Name,
		symbol.Definition.System,
	)

	// Set position
	arxObj.Position = arxoscore.Position{
		X: symbol.Position.X,
		Y: symbol.Position.Y,
		Z: symbol.Position.Z,
	}

	// Set rotation
	arxObj.Rotation = arxoscore.Rotation{
		X: 0,
		Y: 0,
		Z: symbol.Rotation,
	}

	// Set scale visibility
	arxObj.ScaleMin = scaleMin
	arxObj.ScaleMax = scaleMax
	arxObj.OptimalScale = (scaleMin + scaleMax) / 2

	// Set parent
	arxObj.ParentID = parentID

	// Determine system plane based on system type
	arxObj.SystemPlane = b.getSystemPlane(symbol.Definition.System)

	// Set visual representation
	arxObj.SVGPath = symbol.Definition.SVG
	arxObj.Icon = b.getIcon(symbol.Definition.System)

	// Set symbol recognition metadata
	arxObj.SymbolID = symbol.Definition.ID
	arxObj.Source = b.getSourceType(symbol.Context)
	arxObj.Confidence = symbol.Confidence

	// Add properties from symbol definition
	if symbol.Definition.Properties != nil {
		arxObj.Properties = symbol.Definition.Properties
	}

	// Add tags
	arxObj.Tags = symbol.Definition.Tags

	// Set contribution tracking
	arxObj.CreatedBy = "ingestion_system"
	arxObj.CreatedAt = time.Now()
	arxObj.UpdatedAt = time.Now()

	// Calculate BILT reward based on contribution
	arxObj.BILTReward = arxoscore.CalculateBILTReward("symbol_recognition", symbol.Definition.System)

	return arxObj, nil
}

// generateArxID creates a hierarchical ID for the ArxObject
func (b *IngestionBridge) generateArxID(parentID string, symbol *RecognizedSymbol) string {
	// If no parent, start new hierarchy
	if parentID == "" {
		return fmt.Sprintf("arx:%s_%d", symbol.Definition.ID, time.Now().Unix())
	}

	// Extract parent hierarchy
	parts := strings.Split(parentID, ":")
	
	// Add this object to hierarchy
	objectID := fmt.Sprintf("%s_%d", symbol.Definition.ID, time.Now().UnixNano())
	parts = append(parts, objectID)

	return strings.Join(parts, ":")
}

// getObjectType determines the ArxObject type from symbol
func (b *IngestionBridge) getObjectType(def *SymbolDefinition) string {
	// Map symbol categories to ArxObject types
	switch def.Category {
	case "electrical":
		if strings.Contains(def.ID, "outlet") {
			return "outlet"
		}
		if strings.Contains(def.ID, "light") {
			return "light_fixture"
		}
		return "electrical_component"
	case "mechanical", "hvac":
		if strings.Contains(def.ID, "duct") {
			return "hvac_duct"
		}
		return "mechanical_component"
	case "plumbing":
		if strings.Contains(def.ID, "pipe") {
			return "pipe"
		}
		return "plumbing_fixture"
	case "fire_protection":
		return "fire_protection_device"
	case "structural":
		if def.ID == "wall" {
			return "wall"
		}
		if def.ID == "column" {
			return "column"
		}
		return "structural_element"
	case "architectural":
		if def.ID == "door" {
			return "door"
		}
		if def.ID == "window" {
			return "window"
		}
		return "architectural_element"
	default:
		return "component"
	}
}

// calculateScaleRange determines zoom visibility based on object type
func (b *IngestionBridge) calculateScaleRange(objType string) (min, max float64) {
	// Define scale ranges for different object types
	// Scale: 100=campus, 10=building, 1=floor, 0.1=room, 0.01=wall, 0.001=component
	
	switch objType {
	case "building":
		return 100, 1
	case "floor":
		return 10, 0.1
	case "room":
		return 5, 0.05
	case "wall", "door", "window":
		return 2, 0.01
	case "outlet", "light_fixture", "hvac_duct":
		return 1, 0.001
	case "pipe", "wire", "component":
		return 0.5, 0.0001
	default:
		return 1, 0.001
	}
}

// getSystemPlane determines the Z-order plane for a system
func (b *IngestionBridge) getSystemPlane(system string) arxoscore.Plane {
	planes := map[string]arxoscore.Plane{
		"structural":      {Layer: "structural", ZOrder: 0, Elevation: "floor"},
		"architectural":   {Layer: "architectural", ZOrder: 1, Elevation: "floor"},
		"plumbing":        {Layer: "plumbing", ZOrder: 2, Elevation: "floor"},
		"mechanical":      {Layer: "mechanical", ZOrder: 3, Elevation: "ceiling"},
		"electrical":      {Layer: "electrical", ZOrder: 4, Elevation: "wall"},
		"fire_protection": {Layer: "fire_protection", ZOrder: 5, Elevation: "ceiling"},
		"data":            {Layer: "data", ZOrder: 6, Elevation: "above_ceiling"},
		"controls":        {Layer: "controls", ZOrder: 7, Elevation: "wall"},
	}

	if plane, exists := planes[system]; exists {
		return plane
	}

	return arxoscore.Plane{Layer: "default", ZOrder: 99, Elevation: "floor"}
}

// getIcon returns an appropriate emoji/icon for the system
func (b *IngestionBridge) getIcon(system string) string {
	icons := map[string]string{
		"electrical":      "⚡",
		"mechanical":      "⚙️",
		"plumbing":        "🚰",
		"fire_protection": "🔥",
		"structural":      "🏗️",
		"architectural":   "🚪",
		"hvac":            "🌡️",
		"data":            "📡",
		"controls":        "🎛️",
	}

	if icon, exists := icons[system]; exists {
		return icon
	}
	return "📍"
}

// getSourceType determines the ingestion source type
func (b *IngestionBridge) getSourceType(context string) string {
	context = strings.ToLower(context)
	
	if strings.Contains(context, "pdf") {
		return "pdf"
	}
	if strings.Contains(context, "photo") || strings.Contains(context, "image") {
		return "photo"
	}
	if strings.Contains(context, "lidar") || strings.Contains(context, "scan") {
		return "lidar"
	}
	if strings.Contains(context, "ifc") {
		return "ifc"
	}
	
	return "manual"
}

// ProcessRecognizedSymbols converts multiple recognized symbols to ArxObjects
func (b *IngestionBridge) ProcessRecognizedSymbols(symbols []*RecognizedSymbol, buildingID string) ([]*arxoscore.ArxObject, error) {
	var arxObjects []*arxoscore.ArxObject
	
	// Group symbols by parent space (room/area)
	symbolsBySpace := make(map[string][]*RecognizedSymbol)
	for _, symbol := range symbols {
		space := symbol.ParentSpace
		if space == "" {
			space = "unassigned"
		}
		symbolsBySpace[space] = append(symbolsBySpace[space], symbol)
	}

	// Process each space group
	for space, spaceSymbols := range symbolsBySpace {
		// Create parent ID for space
		parentID := buildingID
		if space != "unassigned" {
			parentID = fmt.Sprintf("%s:%s", buildingID, space)
		}

		// Convert each symbol
		for _, symbol := range spaceSymbols {
			arxObj, err := b.ConvertToArxObject(symbol, parentID)
			if err != nil {
				return nil, fmt.Errorf("failed to convert symbol %s: %w", symbol.Definition.ID, err)
			}
			arxObjects = append(arxObjects, arxObj)
		}
	}

	// Detect and resolve overlaps
	b.resolveOverlaps(arxObjects)

	// Establish connections between objects
	b.establishConnections(arxObjects, symbols)

	return arxObjects, nil
}

// resolveOverlaps detects and resolves overlapping objects
func (b *IngestionBridge) resolveOverlaps(objects []*arxoscore.ArxObject) {
	threshold := 50.0 // 50mm threshold for overlap detection

	for i, obj1 := range objects {
		for j, obj2 := range objects {
			if i >= j {
				continue
			}

			// Calculate distance between objects
			dx := obj1.Position.X - obj2.Position.X
			dy := obj1.Position.Y - obj2.Position.Y
			distance := dx*dx + dy*dy

			if distance < threshold*threshold {
				// Objects overlap - determine relationship
				relationship := b.determineRelationship(obj1, obj2)
				
				// Add to overlaps
				obj1.Overlaps = append(obj1.Overlaps, arxoscore.Overlap{
					ObjectID:     obj2.ID,
					Relationship: relationship,
				})
				
				obj2.Overlaps = append(obj2.Overlaps, arxoscore.Overlap{
					ObjectID:     obj1.ID,
					Relationship: b.inverseRelationship(relationship),
				})
			}
		}
	}
}

// determineRelationship determines the relationship between overlapping objects
func (b *IngestionBridge) determineRelationship(obj1, obj2 *arxoscore.ArxObject) string {
	// Outlet on wall
	if obj1.Type == "outlet" && obj2.Type == "wall" {
		return "mounted_on"
	}
	if obj1.Type == "wall" && obj2.Type == "outlet" {
		return "supports"
	}

	// Light in ceiling
	if obj1.Type == "light_fixture" && obj2.SystemPlane.Elevation == "ceiling" {
		return "mounted_in"
	}

	// Thermostat controls HVAC
	if strings.Contains(obj1.Type, "thermostat") && obj2.System == "mechanical" {
		return "controls"
	}

	// Switch controls light
	if obj1.Type == "switch" && obj2.Type == "light_fixture" {
		return "controls"
	}

	// Default relationship
	if obj1.SystemPlane.ZOrder < obj2.SystemPlane.ZOrder {
		return "below"
	}
	return "adjacent"
}

// inverseRelationship returns the inverse of a relationship
func (b *IngestionBridge) inverseRelationship(rel string) string {
	inverses := map[string]string{
		"mounted_on":   "supports",
		"supports":     "mounted_on",
		"mounted_in":   "contains",
		"contains":     "mounted_in",
		"controls":     "controlled_by",
		"controlled_by": "controls",
		"below":        "above",
		"above":        "below",
		"adjacent":     "adjacent",
	}

	if inv, exists := inverses[rel]; exists {
		return inv
	}
	return rel
}

// establishConnections creates connections between related objects
func (b *IngestionBridge) establishConnections(objects []*arxoscore.ArxObject, symbols []*RecognizedSymbol) {
	// Map objects by ID for quick lookup
	objMap := make(map[string]*arxoscore.ArxObject)
	for _, obj := range objects {
		objMap[obj.ID] = obj
	}

	// Create connections from symbol data
	for i, symbol := range symbols {
		if len(symbol.Connections) == 0 {
			continue
		}

		sourceObj := objects[i]
		
		for _, conn := range symbol.Connections {
			// Find target object
			var targetObj *arxoscore.ArxObject
			for j, sym := range symbols {
				if sym.Definition.ID == conn.ToSymbolID {
					targetObj = objects[j]
					break
				}
			}

			if targetObj != nil {
				// Add connection to source object
				sourceObj.Connections = append(sourceObj.Connections, arxoscore.Connection{
					ToID:       targetObj.ID,
					Type:       conn.Type,
					Properties: conn.Properties,
				})
			}
		}
	}
}