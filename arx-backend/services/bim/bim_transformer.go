package bim

import (
	"fmt"
	"math"
	"strings"
	"time"

	"go.uber.org/zap"
)

// TransformationType represents the type of transformation
type TransformationType string

const (
	TransformationTypeTranslate TransformationType = "translate"
	TransformationTypeRotate    TransformationType = "rotate"
	TransformationTypeScale     TransformationType = "scale"
	TransformationTypeMirror    TransformationType = "mirror"
	TransformationTypeShear     TransformationType = "shear"
	TransformationTypeProject   TransformationType = "project"
	TransformationTypeExtrude   TransformationType = "extrude"
	TransformationTypeRevolve   TransformationType = "revolve"
	TransformationTypeSweep     TransformationType = "sweep"
	TransformationTypeLoft      TransformationType = "loft"
)

// TransformationMatrix represents a 4x4 transformation matrix
type TransformationMatrix struct {
	M11, M12, M13, M14 float64
	M21, M22, M23, M24 float64
	M31, M32, M33, M34 float64
	M41, M42, M43, M44 float64
}

// BIMTransformer provides comprehensive BIM transformation functionality
type BIMTransformer struct {
	logger   *zap.Logger
	matrices map[string]*TransformationMatrix
	history  map[string][]TransformationRecord
}

// TransformationRecord represents a transformation operation record
type TransformationRecord struct {
	ID                 string                 `json:"id"`
	ElementID          string                 `json:"element_id"`
	TransformationType TransformationType     `json:"transformation_type"`
	Parameters         map[string]interface{} `json:"parameters"`
	Matrix             *TransformationMatrix  `json:"matrix"`
	Timestamp          time.Time              `json:"timestamp"`
	Description        string                 `json:"description"`
}

// NewBIMTransformer creates a new BIM transformer
func NewBIMTransformer(logger *zap.Logger) (*BIMTransformer, error) {
	transformer := &BIMTransformer{
		logger:   logger,
		matrices: make(map[string]*TransformationMatrix),
		history:  make(map[string][]TransformationRecord),
	}

	// Initialize identity matrix
	transformer.matrices["identity"] = &TransformationMatrix{
		M11: 1, M12: 0, M13: 0, M14: 0,
		M21: 0, M22: 1, M23: 0, M24: 0,
		M31: 0, M32: 0, M33: 1, M34: 0,
		M41: 0, M42: 0, M43: 0, M44: 1,
	}

	logger.Info("BIM transformer initialized")

	return transformer, nil
}

// TransformElement transforms a BIM element
func (bt *BIMTransformer) TransformElement(element *BIMElement, transformationType string, parameters map[string]interface{}) *BIMTransformationResult {
	result := &BIMTransformationResult{
		Success:         false,
		ElementID:       element.ID,
		Transformations: []string{},
		Properties:      make(map[string]interface{}),
		Timestamp:       time.Now(),
	}

	// Validate transformation type
	transType := TransformationType(transformationType)
	if !bt.isValidTransformationType(transType) {
		result.Properties["error"] = fmt.Sprintf("Invalid transformation type: %s", transformationType)
		return result
	}

	// Apply transformation based on type
	switch transType {
	case TransformationTypeTranslate:
		bt.applyTranslation(element, parameters, result)
	case TransformationTypeRotate:
		bt.applyRotation(element, parameters, result)
	case TransformationTypeScale:
		bt.applyScaling(element, parameters, result)
	case TransformationTypeMirror:
		bt.applyMirroring(element, parameters, result)
	case TransformationTypeShear:
		bt.applyShearing(element, parameters, result)
	case TransformationTypeProject:
		bt.applyProjection(element, parameters, result)
	case TransformationTypeExtrude:
		bt.applyExtrusion(element, parameters, result)
	case TransformationTypeRevolve:
		bt.applyRevolve(element, parameters, result)
	case TransformationTypeSweep:
		bt.applySweep(element, parameters, result)
	case TransformationTypeLoft:
		bt.applyLoft(element, parameters, result)
	default:
		result.Properties["error"] = fmt.Sprintf("Unsupported transformation type: %s", transformationType)
		return result
	}

	// Record transformation
	bt.recordTransformation(element.ID, transType, parameters, result)

	result.Success = true
	result.Transformations = append(result.Transformations, string(transType))

	return result
}

// applyTranslation applies translation transformation
func (bt *BIMTransformer) applyTranslation(element *BIMElement, parameters map[string]interface{}, result *BIMTransformationResult) {
	if element.Geometry == nil {
		result.Properties["error"] = "Element has no geometry to transform"
		return
	}

	// Extract translation parameters
	x, _ := bt.getFloatParameter(parameters, "x", 0.0)
	y, _ := bt.getFloatParameter(parameters, "y", 0.0)
	z, _ := bt.getFloatParameter(parameters, "z", 0.0)

	// Apply translation to geometry
	if element.Geometry.Center != nil {
		element.Geometry.Center.X += x
		element.Geometry.Center.Y += y
		element.Geometry.Center.Z += z
	}

	// Apply translation to coordinates
	if element.Geometry.Coordinates != nil {
		for i, coord := range element.Geometry.Coordinates {
			if len(coord) >= 2 {
				element.Geometry.Coordinates[i][0] += x
				element.Geometry.Coordinates[i][1] += y
				if len(coord) >= 3 {
					element.Geometry.Coordinates[i][2] += z
				}
			}
		}
	}

	result.Properties["translation"] = map[string]float64{"x": x, "y": y, "z": z}
}

// applyRotation applies rotation transformation
func (bt *BIMTransformer) applyRotation(element *BIMElement, parameters map[string]interface{}, result *BIMTransformationResult) {
	if element.Geometry == nil {
		result.Properties["error"] = "Element has no geometry to transform"
		return
	}

	// Extract rotation parameters
	angle, _ := bt.getFloatParameter(parameters, "angle", 0.0)
	axis, _ := bt.getStringParameter(parameters, "axis", "z")
	center, _ := bt.getPointParameter(parameters, "center", &BIMPoint{0, 0, 0})

	// Convert angle to radians
	angleRad := angle * math.Pi / 180.0

	// Create rotation matrix
	matrix := bt.createRotationMatrix(angleRad, axis)

	// Apply rotation to geometry
	if element.Geometry.Center != nil {
		element.Geometry.Center = bt.applyMatrixToPoint(element.Geometry.Center, matrix, center)
	}

	// Apply rotation to coordinates
	if element.Geometry.Coordinates != nil {
		for i, coord := range element.Geometry.Coordinates {
			if len(coord) >= 2 {
				point := &BIMPoint{X: coord[0], Y: coord[1]}
				if len(coord) >= 3 {
					point.Z = coord[2]
				}
				rotatedPoint := bt.applyMatrixToPoint(point, matrix, center)
				element.Geometry.Coordinates[i][0] = rotatedPoint.X
				element.Geometry.Coordinates[i][1] = rotatedPoint.Y
				if len(coord) >= 3 {
					element.Geometry.Coordinates[i][2] = rotatedPoint.Z
				}
			}
		}
	}

	result.Properties["rotation"] = map[string]interface{}{
		"angle":  angle,
		"axis":   axis,
		"center": center,
	}
}

// applyScaling applies scaling transformation
func (bt *BIMTransformer) applyScaling(element *BIMElement, parameters map[string]interface{}, result *BIMTransformationResult) {
	if element.Geometry == nil {
		result.Properties["error"] = "Element has no geometry to transform"
		return
	}

	// Extract scaling parameters
	sx, _ := bt.getFloatParameter(parameters, "sx", 1.0)
	sy, _ := bt.getFloatParameter(parameters, "sy", 1.0)
	sz, _ := bt.getFloatParameter(parameters, "sz", 1.0)
	center, _ := bt.getPointParameter(parameters, "center", &BIMPoint{0, 0, 0})

	// Apply scaling to geometry
	if element.Geometry.Center != nil {
		element.Geometry.Center.X = center.X + (element.Geometry.Center.X-center.X)*sx
		element.Geometry.Center.Y = center.Y + (element.Geometry.Center.Y-center.Y)*sy
		element.Geometry.Center.Z = center.Z + (element.Geometry.Center.Z-center.Z)*sz
	}

	// Apply scaling to coordinates
	if element.Geometry.Coordinates != nil {
		for i, coord := range element.Geometry.Coordinates {
			if len(coord) >= 2 {
				element.Geometry.Coordinates[i][0] = center.X + (coord[0]-center.X)*sx
				element.Geometry.Coordinates[i][1] = center.Y + (coord[1]-center.Y)*sy
				if len(coord) >= 3 {
					element.Geometry.Coordinates[i][2] = center.Z + (coord[2]-center.Z)*sz
				}
			}
		}
	}

	// Apply scaling to dimensions
	if element.Geometry.Dimensions != nil {
		element.Geometry.Dimensions.Width *= sx
		element.Geometry.Dimensions.Height *= sy
		element.Geometry.Dimensions.Depth *= sz
	}

	result.Properties["scaling"] = map[string]float64{"sx": sx, "sy": sy, "sz": sz}
}

// applyMirroring applies mirror transformation
func (bt *BIMTransformer) applyMirroring(element *BIMElement, parameters map[string]interface{}, result *BIMTransformationResult) {
	if element.Geometry == nil {
		result.Properties["error"] = "Element has no geometry to transform"
		return
	}

	// Extract mirror parameters
	plane, _ := bt.getStringParameter(parameters, "plane", "xy")
	center, _ := bt.getPointParameter(parameters, "center", &BIMPoint{0, 0, 0})

	// Apply mirroring based on plane
	switch strings.ToLower(plane) {
	case "xy":
		bt.applyMirrorXY(element, center)
	case "yz":
		bt.applyMirrorYZ(element, center)
	case "xz":
		bt.applyMirrorXZ(element, center)
	default:
		result.Properties["error"] = fmt.Sprintf("Invalid mirror plane: %s", plane)
		return
	}

	result.Properties["mirror"] = map[string]interface{}{
		"plane":  plane,
		"center": center,
	}
}

// applyShearing applies shear transformation
func (bt *BIMTransformer) applyShearing(element *BIMElement, parameters map[string]interface{}, result *BIMTransformationResult) {
	if element.Geometry == nil {
		result.Properties["error"] = "Element has no geometry to transform"
		return
	}

	// Extract shear parameters
	shxy, _ := bt.getFloatParameter(parameters, "shxy", 0.0)
	shxz, _ := bt.getFloatParameter(parameters, "shxz", 0.0)
	shyx, _ := bt.getFloatParameter(parameters, "shyx", 0.0)
	shyz, _ := bt.getFloatParameter(parameters, "shyz", 0.0)
	shzx, _ := bt.getFloatParameter(parameters, "shzx", 0.0)
	shzy, _ := bt.getFloatParameter(parameters, "shzy", 0.0)

	// Create shear matrix
	matrix := &TransformationMatrix{
		M11: 1, M12: shxy, M13: shxz, M14: 0,
		M21: shyx, M22: 1, M23: shyz, M24: 0,
		M31: shzx, M32: shzy, M33: 1, M34: 0,
		M41: 0, M42: 0, M43: 0, M44: 1,
	}

	// Apply shear to geometry
	if element.Geometry.Center != nil {
		element.Geometry.Center = bt.applyMatrixToPoint(element.Geometry.Center, matrix, &BIMPoint{0, 0, 0})
	}

	// Apply shear to coordinates
	if element.Geometry.Coordinates != nil {
		for i, coord := range element.Geometry.Coordinates {
			if len(coord) >= 2 {
				point := &BIMPoint{X: coord[0], Y: coord[1]}
				if len(coord) >= 3 {
					point.Z = coord[2]
				}
				shearedPoint := bt.applyMatrixToPoint(point, matrix, &BIMPoint{0, 0, 0})
				element.Geometry.Coordinates[i][0] = shearedPoint.X
				element.Geometry.Coordinates[i][1] = shearedPoint.Y
				if len(coord) >= 3 {
					element.Geometry.Coordinates[i][2] = shearedPoint.Z
				}
			}
		}
	}

	result.Properties["shear"] = map[string]float64{
		"shxy": shxy, "shxz": shxz, "shyx": shyx,
		"shyz": shyz, "shzx": shzx, "shzy": shzy,
	}
}

// applyProjection applies projection transformation
func (bt *BIMTransformer) applyProjection(element *BIMElement, parameters map[string]interface{}, result *BIMTransformationResult) {
	if element.Geometry == nil {
		result.Properties["error"] = "Element has no geometry to transform"
		return
	}

	// Extract projection parameters
	plane, _ := bt.getStringParameter(parameters, "plane", "xy")
	direction, _ := bt.getStringParameter(parameters, "direction", "z")

	// Apply projection based on plane and direction
	switch strings.ToLower(plane) {
	case "xy":
		bt.applyProjectionXY(element, direction)
	case "yz":
		bt.applyProjectionYZ(element, direction)
	case "xz":
		bt.applyProjectionXZ(element, direction)
	default:
		result.Properties["error"] = fmt.Sprintf("Invalid projection plane: %s", plane)
		return
	}

	result.Properties["projection"] = map[string]string{
		"plane":     plane,
		"direction": direction,
	}
}

// applyExtrusion applies extrusion transformation
func (bt *BIMTransformer) applyExtrusion(element *BIMElement, parameters map[string]interface{}, result *BIMTransformationResult) {
	if element.Geometry == nil {
		result.Properties["error"] = "Element has no geometry to transform"
		return
	}

	// Extract extrusion parameters
	distance, _ := bt.getFloatParameter(parameters, "distance", 1.0)
	direction, _ := bt.getStringParameter(parameters, "direction", "z")

	// Apply extrusion
	switch strings.ToLower(direction) {
	case "x":
		bt.applyExtrusionX(element, distance)
	case "y":
		bt.applyExtrusionY(element, distance)
	case "z":
		bt.applyExtrusionZ(element, distance)
	default:
		result.Properties["error"] = fmt.Sprintf("Invalid extrusion direction: %s", direction)
		return
	}

	result.Properties["extrusion"] = map[string]interface{}{
		"distance":  distance,
		"direction": direction,
	}
}

// applyRevolve applies revolve transformation
func (bt *BIMTransformer) applyRevolve(element *BIMElement, parameters map[string]interface{}, result *BIMTransformationResult) {
	if element.Geometry == nil {
		result.Properties["error"] = "Element has no geometry to transform"
		return
	}

	// Extract revolve parameters
	angle, _ := bt.getFloatParameter(parameters, "angle", 360.0)
	axis, _ := bt.getStringParameter(parameters, "axis", "z")
	center, _ := bt.getPointParameter(parameters, "center", &BIMPoint{0, 0, 0})

	// Apply revolve transformation
	bt.applyRevolveTransformation(element, angle, axis, center)

	result.Properties["revolve"] = map[string]interface{}{
		"angle":  angle,
		"axis":   axis,
		"center": center,
	}
}

// applySweep applies sweep transformation
func (bt *BIMTransformer) applySweep(element *BIMElement, parameters map[string]interface{}, result *BIMTransformationResult) {
	if element.Geometry == nil {
		result.Properties["error"] = "Element has no geometry to transform"
		return
	}

	// Extract sweep parameters
	path, _ := bt.getPathParameter(parameters, "path")
	orientation, _ := bt.getStringParameter(parameters, "orientation", "normal")

	// Apply sweep transformation
	bt.applySweepTransformation(element, path, orientation)

	result.Properties["sweep"] = map[string]interface{}{
		"path":        path,
		"orientation": orientation,
	}
}

// applyLoft applies loft transformation
func (bt *BIMTransformer) applyLoft(element *BIMElement, parameters map[string]interface{}, result *BIMTransformationResult) {
	if element.Geometry == nil {
		result.Properties["error"] = "Element has no geometry to transform"
		return
	}

	// Extract loft parameters
	profiles, _ := bt.getProfilesParameter(parameters, "profiles")
	method, _ := bt.getStringParameter(parameters, "method", "linear")

	// Apply loft transformation
	bt.applyLoftTransformation(element, profiles, method)

	result.Properties["loft"] = map[string]interface{}{
		"profiles": profiles,
		"method":   method,
	}
}

// Helper methods for specific transformations
func (bt *BIMTransformer) applyMirrorXY(element *BIMElement, center *BIMPoint) {
	if element.Geometry.Center != nil {
		element.Geometry.Center.Z = center.Z - (element.Geometry.Center.Z - center.Z)
	}
	if element.Geometry.Coordinates != nil {
		for i, coord := range element.Geometry.Coordinates {
			if len(coord) >= 3 {
				element.Geometry.Coordinates[i][2] = center.Z - (coord[2] - center.Z)
			}
		}
	}
}

func (bt *BIMTransformer) applyMirrorYZ(element *BIMElement, center *BIMPoint) {
	if element.Geometry.Center != nil {
		element.Geometry.Center.X = center.X - (element.Geometry.Center.X - center.X)
	}
	if element.Geometry.Coordinates != nil {
		for i, coord := range element.Geometry.Coordinates {
			if len(coord) >= 1 {
				element.Geometry.Coordinates[i][0] = center.X - (coord[0] - center.X)
			}
		}
	}
}

func (bt *BIMTransformer) applyMirrorXZ(element *BIMElement, center *BIMPoint) {
	if element.Geometry.Center != nil {
		element.Geometry.Center.Y = center.Y - (element.Geometry.Center.Y - center.Y)
	}
	if element.Geometry.Coordinates != nil {
		for i, coord := range element.Geometry.Coordinates {
			if len(coord) >= 2 {
				element.Geometry.Coordinates[i][1] = center.Y - (coord[1] - center.Y)
			}
		}
	}
}

func (bt *BIMTransformer) applyProjectionXY(element *BIMElement, direction string) {
	if element.Geometry.Coordinates != nil {
		for i, coord := range element.Geometry.Coordinates {
			if len(coord) >= 3 {
				element.Geometry.Coordinates[i][2] = 0
			}
		}
	}
	if element.Geometry.Center != nil {
		element.Geometry.Center.Z = 0
	}
}

func (bt *BIMTransformer) applyProjectionYZ(element *BIMElement, direction string) {
	if element.Geometry.Coordinates != nil {
		for i, coord := range element.Geometry.Coordinates {
			if len(coord) >= 1 {
				element.Geometry.Coordinates[i][0] = 0
			}
		}
	}
	if element.Geometry.Center != nil {
		element.Geometry.Center.X = 0
	}
}

func (bt *BIMTransformer) applyProjectionXZ(element *BIMElement, direction string) {
	if element.Geometry.Coordinates != nil {
		for i, coord := range element.Geometry.Coordinates {
			if len(coord) >= 2 {
				element.Geometry.Coordinates[i][1] = 0
			}
		}
	}
	if element.Geometry.Center != nil {
		element.Geometry.Center.Y = 0
	}
}

func (bt *BIMTransformer) applyExtrusionX(element *BIMElement, distance float64) {
	if element.Geometry.Dimensions != nil {
		element.Geometry.Dimensions.Width += distance
	}
}

func (bt *BIMTransformer) applyExtrusionY(element *BIMElement, distance float64) {
	if element.Geometry.Dimensions != nil {
		element.Geometry.Dimensions.Height += distance
	}
}

func (bt *BIMTransformer) applyExtrusionZ(element *BIMElement, distance float64) {
	if element.Geometry.Dimensions != nil {
		element.Geometry.Dimensions.Depth += distance
	}
}

func (bt *BIMTransformer) applyRevolveTransformation(element *BIMElement, angle, axis string, center *BIMPoint) {
	// Implementation for revolve transformation
	// This would create a 3D surface by revolving a 2D profile around an axis
}

func (bt *BIMTransformer) applySweepTransformation(element *BIMElement, path interface{}, orientation string) {
	// Implementation for sweep transformation
	// This would create a 3D surface by sweeping a 2D profile along a path
}

func (bt *BIMTransformer) applyLoftTransformation(element *BIMElement, profiles interface{}, method string) {
	// Implementation for loft transformation
	// This would create a 3D surface by lofting between multiple 2D profiles
}

// Matrix operations
func (bt *BIMTransformer) createRotationMatrix(angle float64, axis string) *TransformationMatrix {
	cos := math.Cos(angle)
	sin := math.Sin(angle)

	switch strings.ToLower(axis) {
	case "x":
		return &TransformationMatrix{
			M11: 1, M12: 0, M13: 0, M14: 0,
			M21: 0, M22: cos, M23: -sin, M24: 0,
			M31: 0, M32: sin, M33: cos, M34: 0,
			M41: 0, M42: 0, M43: 0, M44: 1,
		}
	case "y":
		return &TransformationMatrix{
			M11: cos, M12: 0, M13: sin, M14: 0,
			M21: 0, M22: 1, M23: 0, M24: 0,
			M31: -sin, M32: 0, M33: cos, M34: 0,
			M41: 0, M42: 0, M43: 0, M44: 1,
		}
	case "z":
		return &TransformationMatrix{
			M11: cos, M12: -sin, M13: 0, M14: 0,
			M21: sin, M22: cos, M23: 0, M24: 0,
			M31: 0, M32: 0, M33: 1, M34: 0,
			M41: 0, M42: 0, M43: 0, M44: 1,
		}
	default:
		return bt.matrices["identity"]
	}
}

func (bt *BIMTransformer) applyMatrixToPoint(point *BIMPoint, matrix *TransformationMatrix, center *BIMPoint) *BIMPoint {
	// Translate to origin
	x := point.X - center.X
	y := point.Y - center.Y
	z := point.Z - center.Z

	// Apply transformation
	newX := matrix.M11*x + matrix.M12*y + matrix.M13*z + matrix.M14
	newY := matrix.M21*x + matrix.M22*y + matrix.M23*z + matrix.M24
	newZ := matrix.M31*x + matrix.M32*y + matrix.M33*z + matrix.M34

	// Translate back
	return &BIMPoint{
		X: newX + center.X,
		Y: newY + center.Y,
		Z: newZ + center.Z,
	}
}

// Utility methods
func (bt *BIMTransformer) isValidTransformationType(transType TransformationType) bool {
	validTypes := map[TransformationType]bool{
		TransformationTypeTranslate: true,
		TransformationTypeRotate:    true,
		TransformationTypeScale:     true,
		TransformationTypeMirror:    true,
		TransformationTypeShear:     true,
		TransformationTypeProject:   true,
		TransformationTypeExtrude:   true,
		TransformationTypeRevolve:   true,
		TransformationTypeSweep:     true,
		TransformationTypeLoft:      true,
	}
	return validTypes[transType]
}

func (bt *BIMTransformer) getFloatParameter(parameters map[string]interface{}, key string, defaultValue float64) (float64, bool) {
	if value, exists := parameters[key]; exists {
		if floatValue, ok := value.(float64); ok {
			return floatValue, true
		}
		if intValue, ok := value.(int); ok {
			return float64(intValue), true
		}
	}
	return defaultValue, false
}

func (bt *BIMTransformer) getStringParameter(parameters map[string]interface{}, key string, defaultValue string) (string, bool) {
	if value, exists := parameters[key]; exists {
		if stringValue, ok := value.(string); ok {
			return stringValue, true
		}
	}
	return defaultValue, false
}

func (bt *BIMTransformer) getPointParameter(parameters map[string]interface{}, key string, defaultValue *BIMPoint) (*BIMPoint, bool) {
	if value, exists := parameters[key]; exists {
		if pointValue, ok := value.(*BIMPoint); ok {
			return pointValue, true
		}
		if pointMap, ok := value.(map[string]interface{}); ok {
			x, _ := bt.getFloatParameter(pointMap, "x", 0.0)
			y, _ := bt.getFloatParameter(pointMap, "y", 0.0)
			z, _ := bt.getFloatParameter(pointMap, "z", 0.0)
			return &BIMPoint{X: x, Y: y, Z: z}, true
		}
	}
	return defaultValue, false
}

func (bt *BIMTransformer) getPathParameter(parameters map[string]interface{}, key string) (interface{}, bool) {
	if value, exists := parameters[key]; exists {
		return value, true
	}
	return nil, false
}

func (bt *BIMTransformer) getProfilesParameter(parameters map[string]interface{}, key string) (interface{}, bool) {
	if value, exists := parameters[key]; exists {
		return value, true
	}
	return nil, false
}

func (bt *BIMTransformer) recordTransformation(elementID string, transType TransformationType, parameters map[string]interface{}, result *BIMTransformationResult) {
	record := TransformationRecord{
		ID:                 fmt.Sprintf("trans_%d", time.Now().Unix()),
		ElementID:          elementID,
		TransformationType: transType,
		Parameters:         parameters,
		Timestamp:          time.Now(),
		Description:        fmt.Sprintf("Applied %s transformation", transType),
	}

	bt.history[elementID] = append(bt.history[elementID], record)
}

// GetTransformationHistory returns the transformation history for an element
func (bt *BIMTransformer) GetTransformationHistory(elementID string) []TransformationRecord {
	return bt.history[elementID]
}

// ClearTransformationHistory clears the transformation history for an element
func (bt *BIMTransformer) ClearTransformationHistory(elementID string) {
	delete(bt.history, elementID)
}
