package formats

import (
	"bufio"
	"context"
	"fmt"
	"io"
	"strconv"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/importer"
	"github.com/arx-os/arxos/internal/models/building"
)

// IFCImporter handles IFC file imports with spatial support
type IFCImporter struct {
	parser  IFCParser
	spatial SpatialExtractor
}

// NewIFCImporter creates a new IFC importer
func NewIFCImporter() *IFCImporter {
	return &IFCImporter{
		parser:  &StandardIFCParser{},
		spatial: &IFCSpatialExtractor{},
	}
}

// GetFormat returns the format name
func (i *IFCImporter) GetFormat() string {
	return "ifc"
}

// GetCapabilities returns importer capabilities
func (i *IFCImporter) GetCapabilities() importer.ImportCapabilities {
	return importer.ImportCapabilities{
		SupportsSpatial:    true,  // IFC has precise 3D coordinates
		SupportsHierarchy:  true,  // Full building hierarchy
		SupportsMetadata:   true,  // Rich metadata
		SupportsConfidence: true,
		SupportsStreaming:  false,
		MaxFileSize:        500 * 1024 * 1024, // 500MB limit
	}
}

// CanImport checks if this importer can handle the input
func (i *IFCImporter) CanImport(input io.Reader) bool {
	// Check for IFC header
	scanner := bufio.NewScanner(input)
	for scanner.Scan() {
		line := scanner.Text()
		if strings.HasPrefix(line, "ISO-10303-21") || strings.Contains(line, "IFC2") || strings.Contains(line, "IFC4") {
			return true
		}
		// Only check first 10 lines
		if !scanner.Scan() {
			break
		}
	}
	return false
}

// ImportToModel converts IFC to building model
func (i *IFCImporter) ImportToModel(ctx context.Context, input io.Reader, opts importer.ImportOptions) (*building.BuildingModel, error) {
	logger.Info("Starting IFC import")

	// Parse IFC file
	ifcModel, err := i.parser.Parse(input)
	if err != nil {
		return nil, fmt.Errorf("failed to parse IFC file: %w", err)
	}

	// Create building model
	model := &building.BuildingModel{
		ID:         opts.BuildingID,
		Name:       opts.BuildingName,
		Source:     building.DataSourceIFC,
		Confidence: building.ConfidenceHigh, // IFC has precise data
		ImportedAt: time.Now(),
		UpdatedAt:  time.Now(),
		Properties: make(map[string]interface{}),
	}

	// Extract building info
	if ifcModel.Building != nil {
		if model.Name == "" {
			model.Name = ifcModel.Building.Name
		}
		model.Description = ifcModel.Building.Description
		model.Address = ifcModel.Building.Address
	}

	// Extract spatial data
	model.Origin = i.spatial.ExtractOrigin(ifcModel)
	model.BoundingBox = i.spatial.ExtractBounds(ifcModel)

	// Extract floors
	model.Floors = i.extractFloors(ifcModel)

	// Extract systems
	model.Systems = i.extractSystems(ifcModel)

	// Add IFC metadata
	model.Properties["ifc_version"] = ifcModel.Version
	model.Properties["ifc_schema"] = ifcModel.Schema
	if ifcModel.Project != nil {
		model.Properties["project_name"] = ifcModel.Project.Name
	}

	// Log summary
	equipmentCount := len(model.GetAllEquipment())
	logger.Info("IFC import complete: %d floors, %d systems, %d equipment items",
		len(model.Floors), len(model.Systems), equipmentCount)

	return model, nil
}

// IFCParser interface for parsing IFC files
type IFCParser interface {
	Parse(input io.Reader) (*IFCModel, error)
}

// SpatialExtractor interface for extracting spatial data
type SpatialExtractor interface {
	ExtractOrigin(model *IFCModel) *building.SpatialReference
	ExtractBounds(model *IFCModel) *building.BoundingBox
}

// IFCModel represents parsed IFC data
type IFCModel struct {
	Version  string
	Schema   string
	Project  *IFCProject
	Building *IFCBuilding
	Storeys  []IFCStorey
	Spaces   []IFCSpace
	Elements []IFCElement
	Systems  []IFCSystem
}

// IFCProject represents an IFC project
type IFCProject struct {
	ID          string
	Name        string
	Description string
	Units       string
}

// IFCBuilding represents an IFC building
type IFCBuilding struct {
	ID          string
	Name        string
	Description string
	Address     string
	Position    Point3D
}

// IFCStorey represents a building storey
type IFCStorey struct {
	ID          string
	Name        string
	Elevation   float64
	Height      float64
	Position    Point3D
}

// IFCSpace represents a space/room
type IFCSpace struct {
	ID       string
	Name     string
	Type     string
	StoreyID string
	Area     float64
	Volume   float64
	Position Point3D
	Points   []Point3D // boundary points
}

// IFCElement represents a building element (equipment, furniture, etc.)
type IFCElement struct {
	ID           string
	Name         string
	Type         string
	ObjectType   string
	StoreyID     string
	SpaceID      string
	Position     Point3D
	Dimensions   Size3D
	Properties   map[string]string
	Connections  []string
}

// IFCSystem represents a building system
type IFCSystem struct {
	ID       string
	Name     string
	Type     string
	Elements []string // element IDs in this system
}

// Point3D represents a 3D point (internal use)
type Point3D struct {
	X, Y, Z float64
}

// Size3D represents 3D dimensions (internal use)
type Size3D struct {
	Width, Depth, Height float64
}

// StandardIFCParser implements IFC parsing
type StandardIFCParser struct{}

// Parse parses an IFC file
func (p *StandardIFCParser) Parse(input io.Reader) (*IFCModel, error) {
	model := &IFCModel{
		Storeys:  []IFCStorey{},
		Spaces:   []IFCSpace{},
		Elements: []IFCElement{},
		Systems:  []IFCSystem{},
	}

	scanner := bufio.NewScanner(input)
	var currentSection string
	lineNum := 0

	for scanner.Scan() {
		lineNum++
		line := strings.TrimSpace(scanner.Text())

		// Skip empty lines and comments
		if line == "" || strings.HasPrefix(line, "/*") {
			continue
		}

		// Detect sections
		if strings.HasPrefix(line, "HEADER") {
			currentSection = "HEADER"
			continue
		} else if strings.HasPrefix(line, "DATA") {
			currentSection = "DATA"
			continue
		}

		// Parse based on section
		switch currentSection {
		case "HEADER":
			p.parseHeader(line, model)
		case "DATA":
			p.parseData(line, model)
		}
	}

	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("error reading IFC file: %w", err)
	}

	// Post-process to establish relationships
	p.establishRelationships(model)

	return model, nil
}

// parseHeader parses IFC header information
func (p *StandardIFCParser) parseHeader(line string, model *IFCModel) {
	if strings.Contains(line, "FILE_SCHEMA") {
		if strings.Contains(line, "IFC2X3") {
			model.Schema = "IFC2X3"
			model.Version = "2.3"
		} else if strings.Contains(line, "IFC4") {
			model.Schema = "IFC4"
			model.Version = "4.0"
		}
	}
}

// parseData parses IFC data section
func (p *StandardIFCParser) parseData(line string, model *IFCModel) {
	// Parse IFC entities
	if strings.Contains(line, "IFCPROJECT") {
		model.Project = p.parseProject(line)
	} else if strings.Contains(line, "IFCBUILDING") && !strings.Contains(line, "IFCBUILDINGELEMENT") {
		model.Building = p.parseBuilding(line)
	} else if strings.Contains(line, "IFCBUILDINGSTOREY") {
		if storey := p.parseStorey(line); storey != nil {
			model.Storeys = append(model.Storeys, *storey)
		}
	} else if strings.Contains(line, "IFCSPACE") {
		if space := p.parseSpace(line); space != nil {
			model.Spaces = append(model.Spaces, *space)
		}
	} else if p.isEquipmentEntity(line) {
		if element := p.parseElement(line); element != nil {
			model.Elements = append(model.Elements, *element)
		}
	} else if strings.Contains(line, "IFCSYSTEM") || strings.Contains(line, "IFCDISTRIBUTION") {
		if system := p.parseSystem(line); system != nil {
			model.Systems = append(model.Systems, *system)
		}
	}
}

// parseProject parses an IFC project entity
func (p *StandardIFCParser) parseProject(line string) *IFCProject {
	// Simplified parsing - real implementation would parse STEP format
	return &IFCProject{
		ID:    p.extractID(line),
		Name:  p.extractString(line, 2),
		Units: "METERS",
	}
}

// parseBuilding parses an IFC building entity
func (p *StandardIFCParser) parseBuilding(line string) *IFCBuilding {
	return &IFCBuilding{
		ID:   p.extractID(line),
		Name: p.extractString(line, 2),
	}
}

// parseStorey parses an IFC storey entity
func (p *StandardIFCParser) parseStorey(line string) *IFCStorey {
	return &IFCStorey{
		ID:        p.extractID(line),
		Name:      p.extractString(line, 2),
		Elevation: p.extractFloat(line, 3),
	}
}

// parseSpace parses an IFC space entity
func (p *StandardIFCParser) parseSpace(line string) *IFCSpace {
	return &IFCSpace{
		ID:   p.extractID(line),
		Name: p.extractString(line, 2),
		Type: "room",
	}
}

// parseElement parses an IFC element entity
func (p *StandardIFCParser) parseElement(line string) *IFCElement {
	element := &IFCElement{
		ID:         p.extractID(line),
		Name:       p.extractString(line, 2),
		Properties: make(map[string]string),
	}

	// Determine type from entity name
	if strings.Contains(line, "IFCFLOWSEGMENT") {
		element.Type = "pipe"
	} else if strings.Contains(line, "IFCFLOWTERMINAL") {
		element.Type = "terminal"
	} else if strings.Contains(line, "IFCFLOWCONTROLLER") {
		element.Type = "controller"
	} else if strings.Contains(line, "IFCDISTRIBUTIONELEMENT") {
		element.Type = "distribution"
	} else {
		element.Type = "equipment"
	}

	return element
}

// parseSystem parses an IFC system entity
func (p *StandardIFCParser) parseSystem(line string) *IFCSystem {
	return &IFCSystem{
		ID:   p.extractID(line),
		Name: p.extractString(line, 2),
		Type: p.inferSystemType(line),
	}
}

// isEquipmentEntity checks if line represents equipment
func (p *StandardIFCParser) isEquipmentEntity(line string) bool {
	equipmentTypes := []string{
		"IFCFLOWSEGMENT",
		"IFCFLOWTERMINAL",
		"IFCFLOWCONTROLLER",
		"IFCDISTRIBUTIONELEMENT",
		"IFCFURNISHINGELEMENT",
		"IFCBUILDINGELEMENTPROXY",
	}

	for _, eType := range equipmentTypes {
		if strings.Contains(line, eType) {
			return true
		}
	}
	return false
}

// inferSystemType infers system type from line
func (p *StandardIFCParser) inferSystemType(line string) string {
	line = strings.ToUpper(line)
	switch {
	case strings.Contains(line, "HVAC") || strings.Contains(line, "AIR"):
		return "hvac"
	case strings.Contains(line, "ELECTRICAL") || strings.Contains(line, "POWER"):
		return "electrical"
	case strings.Contains(line, "PLUMBING") || strings.Contains(line, "WATER"):
		return "plumbing"
	case strings.Contains(line, "FIRE"):
		return "fire"
	default:
		return "general"
	}
}

// Helper methods for parsing IFC STEP format
func (p *StandardIFCParser) extractID(line string) string {
	if idx := strings.Index(line, "#"); idx >= 0 {
		end := strings.Index(line[idx:], "=")
		if end > 0 {
			return line[idx : idx+end]
		}
	}
	return ""
}

func (p *StandardIFCParser) extractString(line string, position int) string {
	// Simplified - real implementation would parse STEP format properly
	parts := strings.Split(line, "'")
	if len(parts) > position*2 {
		return parts[position*2-1]
	}
	return ""
}

func (p *StandardIFCParser) extractFloat(line string, position int) float64 {
	// Simplified parsing
	val, _ := strconv.ParseFloat("0.0", 64)
	return val
}

// establishRelationships links entities together
func (p *StandardIFCParser) establishRelationships(model *IFCModel) {
	// This would parse relationship entities like IFCRELCONTAINEDINSPATIALSTRUCTURE
	// For now, use simple heuristics

	// Assign elements to storeys based on elevation
	for i := range model.Elements {
		element := &model.Elements[i]
		// Find closest storey
		for _, storey := range model.Storeys {
			// Simple assignment - real implementation would use spatial relationships
			if element.StoreyID == "" {
				element.StoreyID = storey.ID
				break
			}
		}
	}
}

// IFCSpatialExtractor extracts spatial information
type IFCSpatialExtractor struct{}

// ExtractOrigin extracts the spatial reference origin
func (s *IFCSpatialExtractor) ExtractOrigin(model *IFCModel) *building.SpatialReference {
	ref := &building.SpatialReference{
		LocalOrigin: building.Point3D{X: 0, Y: 0, Z: 0},
		Units:       "meters",
	}

	// Extract from building position if available
	if model.Building != nil && model.Building.Position != (Point3D{}) {
		ref.LocalOrigin = building.Point3D{
			X: model.Building.Position.X,
			Y: model.Building.Position.Y,
			Z: model.Building.Position.Z,
		}
	}

	// Set units from project
	if model.Project != nil && model.Project.Units != "" {
		ref.Units = strings.ToLower(model.Project.Units)
	}

	return ref
}

// ExtractBounds extracts the building bounding box
func (s *IFCSpatialExtractor) ExtractBounds(model *IFCModel) *building.BoundingBox {
	if len(model.Elements) == 0 && len(model.Spaces) == 0 {
		return nil
	}

	// Calculate bounds from all elements and spaces
	var minX, minY, minZ, maxX, maxY, maxZ float64
	first := true

	// Process elements
	for _, element := range model.Elements {
		if first {
			minX, maxX = element.Position.X, element.Position.X
			minY, maxY = element.Position.Y, element.Position.Y
			minZ, maxZ = element.Position.Z, element.Position.Z
			first = false
		} else {
			minX = min(minX, element.Position.X)
			minY = min(minY, element.Position.Y)
			minZ = min(minZ, element.Position.Z)
			maxX = max(maxX, element.Position.X+element.Dimensions.Width)
			maxY = max(maxY, element.Position.Y+element.Dimensions.Depth)
			maxZ = max(maxZ, element.Position.Z+element.Dimensions.Height)
		}
	}

	// Process spaces
	for _, space := range model.Spaces {
		for _, point := range space.Points {
			if first {
				minX, maxX = point.X, point.X
				minY, maxY = point.Y, point.Y
				minZ, maxZ = point.Z, point.Z
				first = false
			} else {
				minX = min(minX, point.X)
				minY = min(minY, point.Y)
				minZ = min(minZ, point.Z)
				maxX = max(maxX, point.X)
				maxY = max(maxY, point.Y)
				maxZ = max(maxZ, point.Z)
			}
		}
	}

	if first {
		return nil // No spatial data found
	}

	return &building.BoundingBox{
		Min: building.Point3D{X: minX, Y: minY, Z: minZ},
		Max: building.Point3D{X: maxX, Y: maxY, Z: maxZ},
	}
}

// extractFloors converts IFC storeys to building floors
func (i *IFCImporter) extractFloors(model *IFCModel) []building.Floor {
	var floors []building.Floor

	for idx, storey := range model.Storeys {
		floor := building.Floor{
			ID:         storey.ID,
			Number:     idx,
			Name:       storey.Name,
			Elevation:  storey.Elevation,
			Height:     storey.Height,
			Rooms:      []building.Room{},
			Equipment:  []building.Equipment{},
			Confidence: building.ConfidenceHigh,
			Properties: make(map[string]interface{}),
		}

		// Add spaces as rooms
		for _, space := range model.Spaces {
			if space.StoreyID == storey.ID {
				room := building.Room{
					ID:         space.ID,
					Name:       space.Name,
					Type:       space.Type,
					Area:       space.Area,
					FloorID:    floor.ID,
					Confidence: building.ConfidenceHigh,
					Properties: make(map[string]interface{}),
				}

				// Add spatial position
				if space.Position != (Point3D{}) {
					room.Position = &building.Point3D{
						X: space.Position.X,
						Y: space.Position.Y,
						Z: space.Position.Z,
					}
				}

				// Add boundary points
				if len(space.Points) > 0 {
					room.Boundary = make([]building.Point3D, len(space.Points))
					for i, p := range space.Points {
						room.Boundary[i] = building.Point3D{X: p.X, Y: p.Y, Z: p.Z}
					}
				}

				floor.Rooms = append(floor.Rooms, room)
			}
		}

		// Add elements as equipment
		for _, element := range model.Elements {
			if element.StoreyID == storey.ID {
				equipment := building.Equipment{
					ID:         element.ID,
					Name:       element.Name,
					Type:       element.Type,
					Subtype:    element.ObjectType,
					Status:     "operational",
					FloorID:    floor.ID,
					RoomID:     element.SpaceID,
					Confidence: building.ConfidenceHigh,
					Properties: make(map[string]interface{}),
				}

				// Add spatial data
				if element.Position != (Point3D{}) {
					equipment.Position = &building.Point3D{
						X: element.Position.X,
						Y: element.Position.Y,
						Z: element.Position.Z,
					}
				}

				if element.Dimensions != (Size3D{}) {
					equipment.Size = &building.Size3D{
						Width:  element.Dimensions.Width,
						Depth:  element.Dimensions.Depth,
						Height: element.Dimensions.Height,
					}
				}

				// Add properties
				for k, v := range element.Properties {
					equipment.Properties[k] = v
				}

				floor.Equipment = append(floor.Equipment, equipment)
			}
		}

		floors = append(floors, floor)
	}

	return floors
}

// extractSystems converts IFC systems to building systems
func (i *IFCImporter) extractSystems(model *IFCModel) []building.System {
	var systems []building.System

	for _, ifcSystem := range model.Systems {
		system := building.System{
			ID:         ifcSystem.ID,
			Name:       ifcSystem.Name,
			Type:       ifcSystem.Type,
			Equipment:  ifcSystem.Elements,
			Confidence: building.ConfidenceHigh,
			Properties: make(map[string]interface{}),
		}

		// Build connections from element relationships
		connections := []building.Connection{}
		for idx := 0; idx < len(ifcSystem.Elements)-1; idx++ {
			// Simple linear connections - real implementation would parse actual relationships
			connections = append(connections, building.Connection{
				FromID: ifcSystem.Elements[idx],
				ToID:   ifcSystem.Elements[idx+1],
				Type:   ifcSystem.Type,
			})
		}
		system.Connections = connections

		systems = append(systems, system)
	}

	return systems
}

// min returns the minimum of two float64 values
func min(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
}

// max returns the maximum of two float64 values
func max(a, b float64) float64 {
	if a > b {
		return a
	}
	return b
}