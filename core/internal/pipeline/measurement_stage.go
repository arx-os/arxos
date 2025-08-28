// Package pipeline - Measurements processing stage for Progressive Construction Pipeline
package pipeline

import (
	"context"
	"fmt"
	"math"
	"regexp"
	"strconv"
	"strings"

	"github.com/arxos/arxos/core/internal/arxobject"
	"github.com/arxos/arxos/core/internal/confidence"
)

// MeasurementStage handles measurement extraction, validation, and standardization
type MeasurementStage struct {
	// Standards and tolerances
	buildingCodes    map[string]BuildingStandard
	tolerances       ToleranceSettings
	
	// Measurement patterns for text recognition
	measurementRegexes []*regexp.Regexp
}

// BuildingStandard represents building code requirements
type BuildingStandard struct {
	Name             string             `json:"name"`
	MinDoorWidth     float64           `json:"min_door_width"`     // mm
	MinCeilingHeight float64           `json:"min_ceiling_height"` // mm
	MinRoomArea      float64           `json:"min_room_area"`      // sq mm
	MaxWallThickness float64           `json:"max_wall_thickness"` // mm
	Requirements     map[string]float64 `json:"requirements"`
}

// ToleranceSettings defines acceptable measurement tolerances
type ToleranceSettings struct {
	DimensionalTolerance float64 `json:"dimensional_tolerance"`  // ±mm
	AngleTolerance       float64 `json:"angle_tolerance"`        // ±degrees
	AreaTolerance        float64 `json:"area_tolerance"`         // ±percentage
	ScaleTolerance       float64 `json:"scale_tolerance"`        // ±percentage
}

// MeasurementCalibration contains calibration information
type MeasurementCalibration struct {
	ScaleFactor          float64            `json:"scale_factor"`
	Unit                 string             `json:"unit"`
	ReferencePoints      []ReferencePoint   `json:"reference_points"`
	Accuracy             float64            `json:"accuracy"`
	CalibrationMethod    string             `json:"calibration_method"`
	ValidationMeasurements []ValidationMeasurement `json:"validation_measurements"`
}

// ReferencePoint represents a known measurement point for calibration
type ReferencePoint struct {
	PDFCoordinate   [2]float64 `json:"pdf_coordinate"`
	RealWorldValue  float64    `json:"real_world_value"` // mm
	MeasurementType string     `json:"measurement_type"` // "length", "width", "height"
	Confidence      float64    `json:"confidence"`
}

// ValidationMeasurement represents a measurement used for validation
type ValidationMeasurement struct {
	ExpectedValue   float64 `json:"expected_value"`  // mm
	MeasuredValue   float64 `json:"measured_value"`  // mm
	Tolerance       float64 `json:"tolerance"`       // mm
	IsValid         bool    `json:"is_valid"`
	ErrorPercentage float64 `json:"error_percentage"`
}

// NewMeasurementStage creates a new measurement processing stage
func NewMeasurementStage() *MeasurementStage {
	ms := &MeasurementStage{
		buildingCodes: make(map[string]BuildingStandard),
		tolerances: ToleranceSettings{
			DimensionalTolerance: 5.0,    // ±5mm
			AngleTolerance:       2.0,    // ±2 degrees
			AreaTolerance:        0.05,   // ±5%
			ScaleTolerance:       0.02,   // ±2%
		},
	}
	
	// Initialize measurement regex patterns
	ms.initializeMeasurementPatterns()
	
	// Load building standards
	ms.loadBuildingStandards()
	
	return ms
}

// Process processes ArxObjects to extract and validate measurements
func (ms *MeasurementStage) Process(ctx context.Context, objects []*arxobject.ArxObjectUnified) ([]*arxobject.ArxObjectUnified, error) {
	// Step 1: Extract scale information from objects
	calibration, err := ms.extractCalibration(objects)
	if err != nil {
		return nil, fmt.Errorf("failed to extract calibration: %w", err)
	}
	
	// Step 2: Apply calibration to all objects
	calibratedObjects, err := ms.applyCalibration(objects, calibration)
	if err != nil {
		return nil, fmt.Errorf("failed to apply calibration: %w", err)
	}
	
	// Step 3: Validate measurements against building codes
	validatedObjects, err := ms.validateMeasurements(calibratedObjects)
	if err != nil {
		return nil, fmt.Errorf("failed to validate measurements: %w", err)
	}
	
	// Step 4: Enhance confidence based on measurement quality
	enhancedObjects := ms.enhanceMeasurementConfidence(validatedObjects, calibration)
	
	return enhancedObjects, nil
}

// extractCalibration extracts scale and measurement calibration information
func (ms *MeasurementStage) extractCalibration(objects []*arxobject.ArxObjectUnified) (*MeasurementCalibration, error) {
	calibration := &MeasurementCalibration{
		ReferencePoints:      []ReferencePoint{},
		ValidationMeasurements: []ValidationMeasurement{},
		CalibrationMethod:    "auto_scale_detection",
	}
	
	// Look for known dimensions in object properties
	var referencePoints []ReferencePoint
	
	for _, obj := range objects {
		if measurements, exists := obj.Properties["pdf_measurements"]; exists {
			if measurementList, ok := measurements.([]interface{}); ok {
				for _, m := range measurementList {
					if measurement, ok := m.(map[string]interface{}); ok {
						refPoint, err := ms.createReferencePoint(obj, measurement)
						if err == nil {
							referencePoints = append(referencePoints, refPoint)
						}
					}
				}
			}
		}
		
		// Look for standard door/window dimensions
		if obj.Type == arxobject.TypeDoor || obj.Type == arxobject.TypeWindow {
			refPoint := ms.inferStandardDimensions(obj)
			if refPoint != nil {
				referencePoints = append(referencePoints, *refPoint)
			}
		}
	}
	
	if len(referencePoints) == 0 {
		// Use default scale assumptions
		calibration.ScaleFactor = 1.0
		calibration.Unit = "mm"
		calibration.Accuracy = 0.5 // 50% accuracy for assumed scale
	} else {
		// Calculate scale factor from reference points
		calibration.ReferencePoints = referencePoints
		calibration.ScaleFactor = ms.calculateScaleFactor(referencePoints)
		calibration.Unit = "mm"
		calibration.Accuracy = ms.calculateCalibrationAccuracy(referencePoints)
	}
	
	return calibration, nil
}

// createReferencePoint creates a reference point from object measurements
func (ms *MeasurementStage) createReferencePoint(obj *arxobject.ArxObjectUnified, measurement map[string]interface{}) (ReferencePoint, error) {
	value, valueExists := measurement["value"].(float64)
	unit, unitExists := measurement["unit"].(string)
	position, posExists := measurement["position"].([]interface{})
	
	if !valueExists || !unitExists || !posExists {
		return ReferencePoint{}, fmt.Errorf("incomplete measurement data")
	}
	
	// Convert to millimeters
	valueInMM := ms.convertToMillimeters(value, unit)
	
	refPoint := ReferencePoint{
		PDFCoordinate:   [2]float64{position[0].(float64), position[1].(float64)},
		RealWorldValue:  valueInMM,
		MeasurementType: "length",
		Confidence:      0.8, // Good confidence for explicit measurements
	}
	
	return refPoint, nil
}

// inferStandardDimensions infers standard dimensions for doors/windows
func (ms *MeasurementStage) inferStandardDimensions(obj *arxobject.ArxObjectUnified) *ReferencePoint {
	if obj.Geometry.Width == 0 {
		return nil
	}
	
	var standardWidth float64
	var confidence float64
	
	switch obj.Type {
	case arxobject.TypeDoor:
		// Standard door widths: 610mm, 762mm, 813mm, 864mm
		standardWidth = ms.findClosestStandardDoorWidth(obj.Geometry.Width)
		confidence = 0.7
	case arxobject.TypeWindow:
		// Standard window widths vary more, lower confidence
		standardWidth = obj.Geometry.Width // Use as-is for now
		confidence = 0.4
	default:
		return nil
	}
	
	return &ReferencePoint{
		PDFCoordinate:   [2]float64{obj.Geometry.Coordinates[0], obj.Geometry.Coordinates[1]},
		RealWorldValue:  standardWidth,
		MeasurementType: "width",
		Confidence:      confidence,
	}
}

// findClosestStandardDoorWidth finds the closest standard door width
func (ms *MeasurementStage) findClosestStandardDoorWidth(width float64) float64 {
	standardWidths := []float64{610, 686, 762, 813, 864, 915} // mm
	
	closest := standardWidths[0]
	minDiff := math.Abs(width - closest)
	
	for _, standard := range standardWidths[1:] {
		diff := math.Abs(width - standard)
		if diff < minDiff {
			closest = standard
			minDiff = diff
		}
	}
	
	return closest
}

// calculateScaleFactor calculates the scale factor from reference points
func (ms *MeasurementStage) calculateScaleFactor(refPoints []ReferencePoint) float64 {
	if len(refPoints) == 0 {
		return 1.0
	}
	
	totalScale := 0.0
	weightSum := 0.0
	
	for _, point := range refPoints {
		// Calculate scale as real_world_value / pdf_coordinate_distance
		// This is simplified - in practice would need more sophisticated calculation
		pdfDistance := math.Sqrt(point.PDFCoordinate[0]*point.PDFCoordinate[0] + 
		                       point.PDFCoordinate[1]*point.PDFCoordinate[1])
		if pdfDistance > 0 {
			scale := point.RealWorldValue / pdfDistance
			weight := point.Confidence
			
			totalScale += scale * weight
			weightSum += weight
		}
	}
	
	if weightSum > 0 {
		return totalScale / weightSum
	}
	
	return 1.0
}

// calculateCalibrationAccuracy calculates the accuracy of calibration
func (ms *MeasurementStage) calculateCalibrationAccuracy(refPoints []ReferencePoint) float64 {
	if len(refPoints) == 0 {
		return 0.5 // 50% for no reference points
	}
	
	totalConfidence := 0.0
	for _, point := range refPoints {
		totalConfidence += point.Confidence
	}
	
	avgConfidence := totalConfidence / float64(len(refPoints))
	
	// Accuracy improves with number of reference points
	redundancyBonus := math.Min(0.2, float64(len(refPoints)-1)*0.05)
	
	return math.Min(0.95, avgConfidence+redundancyBonus)
}

// applyCalibration applies measurement calibration to all objects
func (ms *MeasurementStage) applyCalibration(objects []*arxobject.ArxObjectUnified, calibration *MeasurementCalibration) ([]*arxobject.ArxObjectUnified, error) {
	calibratedObjects := make([]*arxobject.ArxObjectUnified, len(objects))
	
	for i, obj := range objects {
		// Create a copy of the object
		calibratedObj := *obj
		
		// Apply scale factor to geometry
		calibratedObj.Geometry = ms.applyScaleToGeometry(obj.Geometry, calibration.ScaleFactor)
		
		// Update properties with calibration info
		if calibratedObj.Properties == nil {
			calibratedObj.Properties = make(arxobject.Properties)
		}
		calibratedObj.Properties["calibration_applied"] = true
		calibratedObj.Properties["scale_factor"] = calibration.ScaleFactor
		calibratedObj.Properties["calibration_accuracy"] = calibration.Accuracy
		calibratedObj.Properties["measurement_unit"] = calibration.Unit
		
		calibratedObjects[i] = &calibratedObj
	}
	
	return calibratedObjects, nil
}

// applyScaleToGeometry applies scale factor to geometry coordinates
func (ms *MeasurementStage) applyScaleToGeometry(geom arxobject.Geometry, scaleFactor float64) arxobject.Geometry {
	scaledGeom := geom
	
	// Scale coordinates
	if len(geom.Coordinates) > 0 {
		scaledCoords := make([]float64, len(geom.Coordinates))
		for i, coord := range geom.Coordinates {
			scaledCoords[i] = coord * scaleFactor
		}
		scaledGeom.Coordinates = scaledCoords
	}
	
	// Scale dimensions
	scaledGeom.Width *= scaleFactor
	scaledGeom.Height *= scaleFactor
	scaledGeom.Area *= scaleFactor * scaleFactor
	
	return scaledGeom
}

// validateMeasurements validates measurements against building codes
func (ms *MeasurementStage) validateMeasurements(objects []*arxobject.ArxObjectUnified) ([]*arxobject.ArxObjectUnified, error) {
	validatedObjects := make([]*arxobject.ArxObjectUnified, len(objects))
	
	// Use IBC (International Building Code) as default
	ibc := ms.buildingCodes["IBC"]
	
	for i, obj := range objects {
		validatedObj := *obj
		validationResults := ms.validateObjectMeasurements(&validatedObj, &ibc)
		
		// Add validation results to properties
		if validatedObj.Properties == nil {
			validatedObj.Properties = make(arxobject.Properties)
		}
		validatedObj.Properties["validation_results"] = validationResults
		validatedObj.Properties["code_compliant"] = ms.isCodeCompliant(validationResults)
		
		validatedObjects[i] = &validatedObj
	}
	
	return validatedObjects, nil
}

// validateObjectMeasurements validates a single object's measurements
func (ms *MeasurementStage) validateObjectMeasurements(obj *arxobject.ArxObjectUnified, standard *BuildingStandard) map[string]interface{} {
	results := make(map[string]interface{})
	
	switch obj.Type {
	case arxobject.TypeDoor:
		results["door_width"] = ms.validateDoorWidth(obj.Geometry.Width, standard.MinDoorWidth)
	case arxobject.TypeRoom:
		results["room_area"] = ms.validateRoomArea(obj.Geometry.Area, standard.MinRoomArea)
	case arxobject.TypeWall:
		results["wall_thickness"] = ms.validateWallThickness(obj.Geometry.Width, standard.MaxWallThickness)
	}
	
	return results
}

// validateDoorWidth validates door width against building code
func (ms *MeasurementStage) validateDoorWidth(width float64, minWidth float64) map[string]interface{} {
	isValid := width >= minWidth
	tolerance := width - minWidth
	
	return map[string]interface{}{
		"measured_width": width,
		"required_min":   minWidth,
		"is_valid":       isValid,
		"tolerance":      tolerance,
		"severity":       ms.getSeverity(isValid, tolerance),
	}
}

// validateRoomArea validates room area against building code
func (ms *MeasurementStage) validateRoomArea(area float64, minArea float64) map[string]interface{} {
	isValid := area >= minArea
	tolerance := area - minArea
	
	return map[string]interface{}{
		"measured_area": area,
		"required_min":  minArea,
		"is_valid":      isValid,
		"tolerance":     tolerance,
		"severity":      ms.getSeverity(isValid, tolerance),
	}
}

// validateWallThickness validates wall thickness
func (ms *MeasurementStage) validateWallThickness(thickness float64, maxThickness float64) map[string]interface{} {
	isValid := thickness <= maxThickness
	tolerance := maxThickness - thickness
	
	return map[string]interface{}{
		"measured_thickness": thickness,
		"required_max":       maxThickness,
		"is_valid":           isValid,
		"tolerance":          tolerance,
		"severity":           ms.getSeverity(isValid, tolerance),
	}
}

// getSeverity determines severity of validation result
func (ms *MeasurementStage) getSeverity(isValid bool, tolerance float64) string {
	if isValid {
		if tolerance > 100 { // > 100mm tolerance
			return "good"
		}
		return "acceptable"
	}
	
	if math.Abs(tolerance) < 50 { // < 50mm violation
		return "warning"
	}
	return "error"
}

// isCodeCompliant checks if all validation results are compliant
func (ms *MeasurementStage) isCodeCompliant(results map[string]interface{}) bool {
	for _, result := range results {
		if resultMap, ok := result.(map[string]interface{}); ok {
			if isValid, exists := resultMap["is_valid"].(bool); exists && !isValid {
				if severity, exists := resultMap["severity"].(string); exists && severity == "error" {
					return false
				}
			}
		}
	}
	return true
}

// enhanceMeasurementConfidence enhances confidence based on measurement quality
func (ms *MeasurementStage) enhanceMeasurementConfidence(objects []*arxobject.ArxObjectUnified, calibration *MeasurementCalibration) []*arxobject.ArxObjectUnified {
	enhancedObjects := make([]*arxobject.ArxObjectUnified, len(objects))
	
	for i, obj := range objects {
		enhancedObj := *obj
		
		// Calculate measurement confidence boost
		measurementBoost := ms.calculateMeasurementConfidenceBoost(&enhancedObj, calibration)
		
		// Update confidence
		if enhancedObj.Confidence != nil {
			// Boost geometry confidence based on calibration quality
			geomConfidence := enhancedObj.Confidence.GetGeometryConfidence()
			boostedGeomConfidence := math.Min(0.95, geomConfidence*measurementBoost)
			
			enhancedObj.Confidence.UpdateGeometry(boostedGeomConfidence, "measurement_calibration", map[string]interface{}{
				"calibration_accuracy": calibration.Accuracy,
				"measurement_boost":    measurementBoost,
			})
		}
		
		enhancedObjects[i] = &enhancedObj
	}
	
	return enhancedObjects
}

// calculateMeasurementConfidenceBoost calculates confidence boost from measurements
func (ms *MeasurementStage) calculateMeasurementConfidenceBoost(obj *arxobject.ArxObjectUnified, calibration *MeasurementCalibration) float64 {
	baseBoost := 1.0
	
	// Boost based on calibration accuracy
	calibrationBoost := 1.0 + (calibration.Accuracy-0.5)*0.4 // 0.8 to 1.2 multiplier
	
	// Boost based on code compliance
	codeCompliant, exists := obj.Properties["code_compliant"].(bool)
	complianceBoost := 1.0
	if exists && codeCompliant {
		complianceBoost = 1.1 // 10% boost for compliance
	}
	
	return baseBoost * calibrationBoost * complianceBoost
}

// convertToMillimeters converts a value to millimeters
func (ms *MeasurementStage) convertToMillimeters(value float64, unit string) float64 {
	switch strings.ToLower(unit) {
	case "mm", "millimeter", "millimeters":
		return value
	case "cm", "centimeter", "centimeters":
		return value * 10
	case "m", "meter", "meters":
		return value * 1000
	case "in", "inch", "inches":
		return value * 25.4
	case "ft", "foot", "feet":
		return value * 304.8
	default:
		return value // Assume millimeters
	}
}

// initializeMeasurementPatterns initializes regex patterns for measurement detection
func (ms *MeasurementStage) initializeMeasurementPatterns() {
	patterns := []string{
		`(\d+(?:\.\d+)?)\s*['"]`, // Feet and inches: 8'6"
		`(\d+(?:\.\d+)?)\s*ft`,   // Feet: 8.5ft
		`(\d+(?:\.\d+)?)\s*mm`,   // Millimeters: 2400mm
		`(\d+(?:\.\d+)?)\s*cm`,   // Centimeters: 240cm
		`(\d+(?:\.\d+)?)\s*m`,    // Meters: 2.4m
		`(\d+(?:\.\d+)?)\s*in`,   // Inches: 96in
	}
	
	ms.measurementRegexes = make([]*regexp.Regexp, len(patterns))
	for i, pattern := range patterns {
		ms.measurementRegexes[i] = regexp.MustCompile(pattern)
	}
}

// loadBuildingStandards loads building code standards
func (ms *MeasurementStage) loadBuildingStandards() {
	// International Building Code (IBC) standards
	ms.buildingCodes["IBC"] = BuildingStandard{
		Name:             "International Building Code",
		MinDoorWidth:     810,    // 32 inches
		MinCeilingHeight: 2400,   // 8 feet
		MinRoomArea:      6500000, // 70 sq ft in sq mm
		MaxWallThickness: 300,    // 12 inches
		Requirements: map[string]float64{
			"corridor_width":     1067, // 42 inches
			"stair_width":        1118, // 44 inches
			"handrail_height":    865,  // 34 inches
		},
	}
}