package converter

import (
	"fmt"
	"math"
	"strconv"
	"strings"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/spatial"
)

// IFCSpatialExtractor extracts precise 3D coordinates and spatial data from IFC entities
type IFCSpatialExtractor struct {
	entities         map[string]*IFCEntity
	placements       map[string]*IFCPlacement
	representations  map[string]*IFCRepresentation
	coordinateSystem *IFCCoordinateSystem
	unitScale        float64
}

// IFCPlacement represents object placement in 3D space
type IFCPlacement struct {
	ID              string
	Type            string
	Location        spatial.Point3D
	RefDirection    *Vector3D
	Axis            *Vector3D
	RelativeTo      string // Reference to parent placement
	TransformMatrix Matrix4x4
}

// IFCRepresentation contains geometric representation data
type IFCRepresentation struct {
	ID          string
	Type        string
	BoundingBox *spatial.BoundingBox
	Vertices    []spatial.Point3D
	Faces       [][]int
}

// IFCCoordinateSystem defines the project coordinate system
type IFCCoordinateSystem struct {
	Origin     spatial.Point3D
	XAxis      Vector3D
	YAxis      Vector3D
	ZAxis      Vector3D
	Scale      float64
	NorthAngle float64 // Rotation from true north in radians
}

// Vector3D represents a 3D vector
type Vector3D struct {
	X, Y, Z float64
}

// Matrix4x4 represents a 4x4 transformation matrix
type Matrix4x4 [16]float64

// NewIFCSpatialExtractor creates a new spatial extractor
func NewIFCSpatialExtractor() *IFCSpatialExtractor {
	return &IFCSpatialExtractor{
		entities:        make(map[string]*IFCEntity),
		placements:      make(map[string]*IFCPlacement),
		representations: make(map[string]*IFCRepresentation),
		unitScale:       1.0, // Default to meters
	}
}

// ExtractSpatialData extracts all spatial information from IFC entities
func (e *IFCSpatialExtractor) ExtractSpatialData(entities map[string]*IFCEntity) (map[string]*SpatialData, error) {
	e.entities = entities

	logger.Info("Extracting spatial data from %d IFC entities", len(entities))

	// Step 1: Extract project coordinate system and units
	if err := e.extractCoordinateSystem(); err != nil {
		logger.Warn("Failed to extract coordinate system: %v", err)
		// Continue with default coordinate system
		e.coordinateSystem = e.defaultCoordinateSystem()
	}

	// Step 2: Extract unit definitions
	e.extractUnits()

	// Step 3: Extract all placements
	e.extractPlacements()

	// Step 4: Extract geometric representations
	e.extractRepresentations()

	// Step 5: Calculate global coordinates for all entities
	spatialData := make(map[string]*SpatialData)

	for id, entity := range entities {
		if spatial := e.extractEntitySpatialData(entity); spatial != nil {
			spatialData[id] = spatial
		}
	}

	logger.Info("Extracted spatial data for %d entities", len(spatialData))

	return spatialData, nil
}

// extractCoordinateSystem extracts the project coordinate system
func (e *IFCSpatialExtractor) extractCoordinateSystem() error {
	// Look for IFCGEOMETRICREPRESENTATIONCONTEXT
	for _, entity := range e.entities {
		if entity.Type == "IFCGEOMETRICREPRESENTATIONCONTEXT" {
			rawProps, exists := entity.Properties["raw"]
			if !exists {
				continue
			}
			props := parseIFCPropertiesGeneric(rawProps)

			// Extract coordinate space dimension (usually 3)
			if len(props) > 5 {
				// Parse world coordinate system if available
				if wcsProp := props[5]; wcsProp != "$" && wcsProp != "" {
					if wcsRef := extractReference(wcsProp); wcsRef != "" {
						if wcs, exists := e.entities[wcsRef]; exists {
							e.coordinateSystem = e.parseCoordinateSystem(wcs)
						}
					}
				}
			}

			// Extract true north if available
			if len(props) > 6 {
				if northProp := props[6]; northProp != "$" && northProp != "" {
					if northRef := extractReference(northProp); northRef != "" {
						if north, exists := e.entities[northRef]; exists {
							e.extractTrueNorth(north)
						}
					}
				}
			}

			return nil
		}
	}

	return fmt.Errorf("no geometric representation context found")
}

// parseCoordinateSystem parses an IFC coordinate system entity
func (e *IFCSpatialExtractor) parseCoordinateSystem(entity *IFCEntity) *IFCCoordinateSystem {
	cs := &IFCCoordinateSystem{
		Origin: spatial.Point3D{X: 0, Y: 0, Z: 0},
		XAxis:  Vector3D{X: 1, Y: 0, Z: 0},
		YAxis:  Vector3D{X: 0, Y: 1, Z: 0},
		ZAxis:  Vector3D{X: 0, Y: 0, Z: 1},
		Scale:  1.0,
	}

	if entity.Type == "IFCAXIS2PLACEMENT3D" {
		rawProps, exists := entity.Properties["raw"]
		if !exists {
			return cs
		}
		props := parseIFCPropertiesGeneric(rawProps)

		// Extract location (origin)
		if len(props) > 0 && props[0] != "$" {
			if locRef := extractReference(props[0]); locRef != "" {
				if loc, exists := e.entities[locRef]; exists {
					cs.Origin = e.parsePoint3D(loc)
				}
			}
		}

		// Extract axis (Z-axis)
		if len(props) > 1 && props[1] != "$" {
			if axisRef := extractReference(props[1]); axisRef != "" {
				if axis, exists := e.entities[axisRef]; exists {
					cs.ZAxis = e.parseDirection(axis)
				}
			}
		}

		// Extract ref direction (X-axis)
		if len(props) > 2 && props[2] != "$" {
			if refRef := extractReference(props[2]); refRef != "" {
				if ref, exists := e.entities[refRef]; exists {
					cs.XAxis = e.parseDirection(ref)
				}
			}
		}

		// Calculate Y-axis as cross product of Z and X
		cs.YAxis = crossProduct(cs.ZAxis, cs.XAxis)
	}

	return cs
}

// extractUnits extracts unit definitions from the project
func (e *IFCSpatialExtractor) extractUnits() {
	// Look for IFCUNITASSIGNMENT
	for _, entity := range e.entities {
		if entity.Type == "IFCUNITASSIGNMENT" {
			rawProps, exists := entity.Properties["raw"]
			if !exists {
				continue
			}
			props := parseIFCPropertiesGeneric(rawProps)

			if len(props) > 0 {
				// Parse unit list
				unitRefs := extractReferenceList(props[0])
				for _, unitRef := range unitRefs {
					if unit, exists := e.entities[unitRef]; exists {
						e.parseUnit(unit)
					}
				}
			}
		}
	}

	logger.Debug("Unit scale: %f", e.unitScale)
}

// parseUnit parses a unit definition
func (e *IFCSpatialExtractor) parseUnit(entity *IFCEntity) {
	if entity.Type == "IFCSIUNIT" {
		rawProps, exists := entity.Properties["raw"]
		if !exists {
			return
		}
		props := parseIFCPropertiesGeneric(rawProps)

		// Check if this is a length unit
		if len(props) > 1 && props[1] == ".LENGTHUNIT." {
			// Check for prefix (milli, centi, etc.)
			if len(props) > 2 && props[2] != "$" {
				prefix := strings.Trim(props[2], ".")
				switch prefix {
				case "MILLI":
					e.unitScale = 0.001
				case "CENTI":
					e.unitScale = 0.01
				case "DECI":
					e.unitScale = 0.1
				case "KILO":
					e.unitScale = 1000.0
				default:
					e.unitScale = 1.0
				}
			}
		}
	}
}

// extractPlacements extracts all placement data
func (e *IFCSpatialExtractor) extractPlacements() {
	for id, entity := range e.entities {
		if strings.Contains(entity.Type, "PLACEMENT") {
			placement := e.parsePlacement(entity)
			if placement != nil {
				e.placements[id] = placement
			}
		}
	}

	logger.Debug("Extracted %d placements", len(e.placements))
}

// parsePlacement parses a placement entity
func (e *IFCSpatialExtractor) parsePlacement(entity *IFCEntity) *IFCPlacement {
	placement := &IFCPlacement{
		ID:   entity.ID,
		Type: entity.Type,
	}

	rawProps, exists := entity.Properties["raw"]
	if !exists {
		return placement
	}
	props := parseIFCPropertiesGeneric(rawProps)

	switch entity.Type {
	case "IFCLOCALPLACEMENT":
		// Local placement relative to another placement
		if len(props) > 0 && props[0] != "$" {
			placement.RelativeTo = extractReference(props[0])
		}
		if len(props) > 1 && props[1] != "$" {
			if relRef := extractReference(props[1]); relRef != "" {
				if rel, exists := e.entities[relRef]; exists {
					e.parseAxis2Placement3D(rel, placement)
				}
			}
		}

	case "IFCAXIS2PLACEMENT3D":
		e.parseAxis2Placement3D(entity, placement)

	case "IFCCARTESIANTRANSFORMATIONOPERATOR3D":
		e.parseTransformOperator(entity, placement)
	}

	// Calculate transformation matrix
	placement.TransformMatrix = e.calculateTransformMatrix(placement)

	return placement
}

// parseAxis2Placement3D parses 3D axis placement
func (e *IFCSpatialExtractor) parseAxis2Placement3D(entity *IFCEntity, placement *IFCPlacement) {
	rawProps, exists := entity.Properties["raw"]
	if !exists {
		return
	}
	props := parseIFCPropertiesGeneric(rawProps)

	// Extract location
	if len(props) > 0 && props[0] != "$" {
		if locRef := extractReference(props[0]); locRef != "" {
			if loc, exists := e.entities[locRef]; exists {
				placement.Location = e.parsePoint3D(loc)
			}
		}
	}

	// Extract axis (Z-direction)
	if len(props) > 1 && props[1] != "$" {
		if axisRef := extractReference(props[1]); axisRef != "" {
			if axis, exists := e.entities[axisRef]; exists {
				dir := e.parseDirection(axis)
				placement.Axis = &dir
			}
		}
	}

	// Extract ref direction (X-direction)
	if len(props) > 2 && props[2] != "$" {
		if refRef := extractReference(props[2]); refRef != "" {
			if ref, exists := e.entities[refRef]; exists {
				dir := e.parseDirection(ref)
				placement.RefDirection = &dir
			}
		}
	}
}

// parsePoint3D parses a 3D point
func (e *IFCSpatialExtractor) parsePoint3D(entity *IFCEntity) spatial.Point3D {
	point := spatial.Point3D{}

	if entity.Type == "IFCCARTESIANPOINT" {
		rawProps, exists := entity.Properties["raw"]
		if !exists {
			return point
		}
		props := parseIFCPropertiesGeneric(rawProps)

		if len(props) > 0 {
			// Parse coordinate list
			coords := parseCoordinateList(props[0])
			if len(coords) >= 2 {
				point.X = coords[0] * e.unitScale
				point.Y = coords[1] * e.unitScale
			}
			if len(coords) >= 3 {
				point.Z = coords[2] * e.unitScale
			}
		}
	}

	return point
}

// parseDirection parses a direction vector
func (e *IFCSpatialExtractor) parseDirection(entity *IFCEntity) Vector3D {
	dir := Vector3D{X: 1, Y: 0, Z: 0} // Default to X-axis

	if entity.Type == "IFCDIRECTION" {
		rawProps, exists := entity.Properties["raw"]
		if !exists {
			return dir
		}
		props := parseIFCPropertiesGeneric(rawProps)

		if len(props) > 0 {
			// Parse direction ratios
			coords := parseCoordinateList(props[0])
			if len(coords) >= 2 {
				dir.X = coords[0]
				dir.Y = coords[1]
			}
			if len(coords) >= 3 {
				dir.Z = coords[2]
			}

			// Normalize the direction vector
			dir = normalizeVector(dir)
		}
	}

	return dir
}

// extractEntitySpatialData extracts spatial data for a single entity
func (e *IFCSpatialExtractor) extractEntitySpatialData(entity *IFCEntity) *SpatialData {
	// Look for placement reference in entity properties
	placementRef := e.findPlacementReference(entity)
	if placementRef == "" {
		return nil
	}

	placement, exists := e.placements[placementRef]
	if !exists {
		return nil
	}

	// Calculate global position
	globalPos := e.calculateGlobalPosition(placement)

	// Get bounding box if available
	var bbox *spatial.BoundingBox
	if reprRef := e.findRepresentationReference(entity); reprRef != "" {
		if repr, exists := e.representations[reprRef]; exists {
			bbox = repr.BoundingBox
		}
	}

	// Determine confidence based on available data
	confidence := e.determineConfidence(placement, bbox != nil)

	spatialData := &SpatialData{
		Position:     globalPos,
		LocalCoords:  placement.Location,
		GlobalCoords: globalPos,
		Confidence:   confidence,
	}

	if bbox != nil {
		spatialData.BoundingBox = *bbox
	}

	// Calculate transform
	spatialData.Transform = e.calculateTransform(placement)

	return spatialData
}

// calculateGlobalPosition calculates the global position by following the placement hierarchy
func (e *IFCSpatialExtractor) calculateGlobalPosition(placement *IFCPlacement) spatial.Point3D {
	pos := placement.Location

	// Follow the placement hierarchy
	current := placement
	for current.RelativeTo != "" {
		parent, exists := e.placements[current.RelativeTo]
		if !exists {
			break
		}

		// Apply parent transformation
		pos = e.applyTransformation(pos, parent.TransformMatrix)
		current = parent
	}

	// Apply coordinate system transformation
	if e.coordinateSystem != nil {
		pos = e.applyCoordinateSystemTransform(pos)
	}

	return pos
}

// calculateTransformMatrix calculates the transformation matrix for a placement
func (e *IFCSpatialExtractor) calculateTransformMatrix(placement *IFCPlacement) Matrix4x4 {
	// Create identity matrix
	m := identityMatrix()

	// Apply translation
	m[12] = placement.Location.X
	m[13] = placement.Location.Y
	m[14] = placement.Location.Z

	// Apply rotation if axes are defined
	if placement.RefDirection != nil && placement.Axis != nil {
		// X-axis
		m[0] = placement.RefDirection.X
		m[1] = placement.RefDirection.Y
		m[2] = placement.RefDirection.Z

		// Z-axis
		m[8] = placement.Axis.X
		m[9] = placement.Axis.Y
		m[10] = placement.Axis.Z

		// Y-axis (cross product of Z and X)
		yAxis := crossProduct(*placement.Axis, *placement.RefDirection)
		m[4] = yAxis.X
		m[5] = yAxis.Y
		m[6] = yAxis.Z
	}

	return m
}

// applyTransformation applies a transformation matrix to a point
func (e *IFCSpatialExtractor) applyTransformation(point spatial.Point3D, matrix Matrix4x4) spatial.Point3D {
	// Homogeneous coordinates
	x := point.X*matrix[0] + point.Y*matrix[4] + point.Z*matrix[8] + matrix[12]
	y := point.X*matrix[1] + point.Y*matrix[5] + point.Z*matrix[9] + matrix[13]
	z := point.X*matrix[2] + point.Y*matrix[6] + point.Z*matrix[10] + matrix[14]

	return spatial.Point3D{X: x, Y: y, Z: z}
}

// Helper functions

func (e *IFCSpatialExtractor) defaultCoordinateSystem() *IFCCoordinateSystem {
	return &IFCCoordinateSystem{
		Origin: spatial.Point3D{X: 0, Y: 0, Z: 0},
		XAxis:  Vector3D{X: 1, Y: 0, Z: 0},
		YAxis:  Vector3D{X: 0, Y: 1, Z: 0},
		ZAxis:  Vector3D{X: 0, Y: 0, Z: 1},
		Scale:  1.0,
	}
}

func (e *IFCSpatialExtractor) extractTrueNorth(entity *IFCEntity) {
	if entity.Type == "IFCDIRECTION" {
		dir := e.parseDirection(entity)
		// Calculate angle from Y-axis (north in IFC)
		e.coordinateSystem.NorthAngle = math.Atan2(dir.X, dir.Y)
	}
}

func (e *IFCSpatialExtractor) applyCoordinateSystemTransform(point spatial.Point3D) spatial.Point3D {
	cs := e.coordinateSystem

	// Apply scale
	point.X *= cs.Scale
	point.Y *= cs.Scale
	point.Z *= cs.Scale

	// Apply rotation for true north if needed
	if cs.NorthAngle != 0 {
		cos := math.Cos(cs.NorthAngle)
		sin := math.Sin(cs.NorthAngle)
		x := point.X*cos - point.Y*sin
		y := point.X*sin + point.Y*cos
		point.X = x
		point.Y = y
	}

	// Apply origin offset
	point.X += cs.Origin.X
	point.Y += cs.Origin.Y
	point.Z += cs.Origin.Z

	return point
}

func (e *IFCSpatialExtractor) findPlacementReference(entity *IFCEntity) string {
	if raw, exists := entity.Properties["raw"]; exists {
		props := parseIFCPropertiesGeneric(raw)

		// Placement is typically in position 5 or 6 for building elements
		for i := 5; i <= 6 && i < len(props); i++ {
			if ref := extractReference(props[i]); ref != "" {
				if _, exists := e.placements[ref]; exists {
					return ref
				}
			}
		}
	}

	return ""
}

func (e *IFCSpatialExtractor) findRepresentationReference(entity *IFCEntity) string {
	if raw, exists := entity.Properties["raw"]; exists {
		props := parseIFCPropertiesGeneric(raw)

		// Representation is typically in position 7 for building elements
		if len(props) > 7 {
			return extractReference(props[7])
		}
	}

	return ""
}

func (e *IFCSpatialExtractor) determineConfidence(placement *IFCPlacement, hasGeometry bool) spatial.ConfidenceLevel {
	// High confidence if we have both placement and geometry
	if hasGeometry && placement.Axis != nil && placement.RefDirection != nil {
		return spatial.ConfidenceHigh
	}

	// Medium confidence if we have placement with orientation
	if placement.Axis != nil || placement.RefDirection != nil {
		return spatial.ConfidenceMedium
	}

	// Low confidence for basic placement only
	return spatial.ConfidenceLow
}

func (e *IFCSpatialExtractor) calculateTransform(placement *IFCPlacement) spatial.Transform {
	transform := spatial.Transform{
		Translation: placement.Location,
		Scale:       e.unitScale,
	}

	// Calculate rotation angle if axes are defined
	if placement.RefDirection != nil {
		// Rotation around Z-axis from X-axis direction
		transform.Rotation = math.Atan2(placement.RefDirection.Y, placement.RefDirection.X)
	}

	return transform
}

func (e *IFCSpatialExtractor) parseTransformOperator(entity *IFCEntity, placement *IFCPlacement) {
	// Parse transformation operator for more complex transformations
	rawProps, exists := entity.Properties["raw"]
	if !exists {
		return
	}
	_ = parseIFCPropertiesGeneric(rawProps)

	// Implementation would parse scale, rotation, translation, etc.
	// This is a placeholder for more complex transformation handling
}

func (e *IFCSpatialExtractor) extractRepresentations() {
	// Extract geometric representations
	// This would parse IFCSHAPEREPRESENTATION, IFCBOUNDINGBOX, etc.
	// Placeholder for geometric extraction
}

// Utility functions

func parseIFCPropertiesGeneric(raw string) []string {
	// Remove outer parentheses and split by commas
	raw = strings.TrimSpace(raw)
	raw = strings.TrimPrefix(raw, "(")
	raw = strings.TrimSuffix(raw, ")")

	// Handle nested parentheses properly
	var props []string
	var current strings.Builder
	depth := 0

	for _, char := range raw {
		switch char {
		case '(':
			depth++
			current.WriteRune(char)
		case ')':
			depth--
			current.WriteRune(char)
		case ',':
			if depth == 0 {
				props = append(props, strings.TrimSpace(current.String()))
				current.Reset()
			} else {
				current.WriteRune(char)
			}
		default:
			current.WriteRune(char)
		}
	}

	// Add the last property
	if current.Len() > 0 {
		props = append(props, strings.TrimSpace(current.String()))
	}

	return props
}

func extractReference(prop string) string {
	// Extract reference ID from #123 format
	prop = strings.TrimSpace(prop)
	if strings.HasPrefix(prop, "#") {
		return strings.TrimPrefix(prop, "#")
	}
	return ""
}

func extractReferenceList(prop string) []string {
	// Extract list of references from (list,of,#refs)
	prop = strings.TrimSpace(prop)
	prop = strings.TrimPrefix(prop, "(")
	prop = strings.TrimSuffix(prop, ")")

	var refs []string
	for _, part := range strings.Split(prop, ",") {
		if ref := extractReference(part); ref != "" {
			refs = append(refs, ref)
		}
	}

	return refs
}

func parseCoordinateList(prop string) []float64 {
	// Parse coordinate list like (1.0, 2.0, 3.0)
	prop = strings.TrimSpace(prop)
	prop = strings.TrimPrefix(prop, "(")
	prop = strings.TrimSuffix(prop, ")")

	var coords []float64
	for _, part := range strings.Split(prop, ",") {
		part = strings.TrimSpace(part)
		if val, err := strconv.ParseFloat(part, 64); err == nil {
			coords = append(coords, val)
		}
	}

	return coords
}

func crossProduct(a, b Vector3D) Vector3D {
	return Vector3D{
		X: a.Y*b.Z - a.Z*b.Y,
		Y: a.Z*b.X - a.X*b.Z,
		Z: a.X*b.Y - a.Y*b.X,
	}
}

func normalizeVector(v Vector3D) Vector3D {
	length := math.Sqrt(v.X*v.X + v.Y*v.Y + v.Z*v.Z)
	if length == 0 {
		return v
	}

	return Vector3D{
		X: v.X / length,
		Y: v.Y / length,
		Z: v.Z / length,
	}
}

func identityMatrix() Matrix4x4 {
	return Matrix4x4{
		1, 0, 0, 0,
		0, 1, 0, 0,
		0, 0, 1, 0,
		0, 0, 0, 1,
	}
}

// cleanString removes quotes and special characters from IFC strings
func cleanString(s string) string {
	// Remove quotes
	s = strings.Trim(s, "'\"")
	// Replace $ (null) with empty string
	if s == "$" {
		return ""
	}
	return s
}
