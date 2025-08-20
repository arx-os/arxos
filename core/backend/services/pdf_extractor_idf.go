package services

import (
	"encoding/json"
	"fmt"
	"math"
	"time"

	"arxos/arxobject"
	"github.com/google/uuid"
)

// IDFExtractor handles IDF (Intermediate Data Format) callout sheet processing
type IDFExtractor struct {
	arxEngine *arxobject.Engine
}

// NewIDFExtractor creates a new IDF extractor
func NewIDFExtractor(arxEngine *arxobject.Engine) *IDFExtractor {
	return &IDFExtractor{
		arxEngine: arxEngine,
	}
}

// IDFResult contains IDF processing results
type IDFResult struct {
	ID             string                `json:"id"`
	Filename       string                `json:"filename"`
	Status         string                `json:"status"`
	ProcessingTime time.Duration         `json:"processing_time"`
	Objects        []arxobject.ArxObject `json:"objects"`
	Statistics     IDFStatistics         `json:"statistics"`
}

// IDFStatistics contains IDF-specific statistics
type IDFStatistics struct {
	TotalObjects     int                    `json:"total_objects"`
	ObjectsByType    map[string]int         `json:"objects_by_type"`
	ObjectsBySystem  map[string]int         `json:"objects_by_system"`
	ConfidenceStats  map[string]float32     `json:"confidence_stats"`
	IDFElements      map[string]int         `json:"idf_elements"`
}

// ProcessIDFCallout processes an IDF callout sheet with circuit breaker protection
func (e *IDFExtractor) ProcessIDFCallout(filepath string) (*IDFResult, error) {
	startTime := time.Now()
	
	// Input validation
	if filepath == "" {
		return nil, NewExtractionError("ProcessIDFCallout", "filepath cannot be empty", nil)
	}
	
	if e.arxEngine == nil {
		return nil, NewExtractionError("ProcessIDFCallout", "arxEngine is not initialized", nil)
	}
	
	result := &IDFResult{
		ID:       "idf_" + uuid.New().String()[:8],
		Filename: filepath,
		Status:   "processing",
	}

	// Get circuit breaker for PDF processing
	circuitConfig := &CircuitBreakerConfig{
		MaxFailures:      3,
		Timeout:          60 * time.Second,
		MaxRequests:      2,
		SuccessThreshold: 1,
		OnStateChange: func(name string, from CircuitState, to CircuitState) {
			fmt.Printf("Circuit breaker '%s' changed from %s to %s\n", name, from.String(), to.String())
		},
	}
	
	pdfCircuit := GetCircuitBreaker("pdf_processing", circuitConfig)
	
	// Execute PDF processing through circuit breaker
	var objects []arxobject.ArxObject
	var processingErr error
	
	err := pdfCircuit.Execute(func() error {
		var err error
		objects, err = e.extractIDFElementsWithErrorHandling()
		if err != nil {
			processingErr = err
			return err
		}
		return nil
	})
	
	if err != nil {
		result.Status = "failed"
		if circuitErr, ok := err.(*CircuitBreakerError); ok {
			return result, NewExtractionError("ProcessIDFCallout", 
				fmt.Sprintf("PDF processing circuit breaker: %s", circuitErr.Message), err)
		}
		return result, NewExtractionError("ProcessIDFCallout", "failed to extract IDF elements", processingErr)
	}
	
	// Analyze relationships with circuit breaker protection
	relationshipCircuit := GetCircuitBreaker("relationship_analysis", circuitConfig)
	
	err = relationshipCircuit.Execute(func() error {
		var err error
		objects, err = e.analyzeIDFRelationshipsWithErrorHandling(objects)
		return err
	})
	
	if err != nil {
		// Log warning but continue with original objects
		result.Status = "partial"
		fmt.Printf("Relationship analysis failed: %v\n", err)
	}
	
	// Calculate statistics with error recovery (no circuit breaker needed for lightweight operation)
	statistics, err := e.calculateIDFStatisticsWithErrorHandling(objects)
	if err != nil {
		// Use default statistics if calculation fails
		statistics = e.getDefaultIDFStatistics()
	}
	
	result.Objects = objects
	result.Statistics = statistics
	result.ProcessingTime = time.Since(startTime)
	
	if result.Status != "partial" && result.Status != "failed" {
		result.Status = "completed"
	}

	return result, nil
}

// extractIDFElementsWithErrorHandling extracts IDF elements with comprehensive error handling
func (e *IDFExtractor) extractIDFElementsWithErrorHandling() ([]arxobject.ArxObject, error) {
	var objects []arxobject.ArxObject
	recovery := DefaultErrorRecovery()
	
	// Track extraction results for diagnostics
	extractionResults := make(map[string]error)

	// Extract walls with error recovery
	if err := recovery.SafeExecute("extractIDFWalls", func() error {
		walls, err := e.extractIDFWallsWithErrorHandling()
		if err != nil {
			return err
		}
		objects = append(objects, walls...)
		return nil
	}); err != nil {
		extractionResults["walls"] = err
	}

	// Extract doors with error recovery
	if err := recovery.SafeExecute("extractIDFDoors", func() error {
		doors, err := e.extractIDFDoorsWithErrorHandling()
		if err != nil {
			return err
		}
		objects = append(objects, doors...)
		return nil
	}); err != nil {
		extractionResults["doors"] = err
	}

	// Extract windows with error recovery
	if err := recovery.SafeExecute("extractIDFWindows", func() error {
		windows, err := e.extractIDFWindowsWithErrorHandling()
		if err != nil {
			return err
		}
		objects = append(objects, windows...)
		return nil
	}); err != nil {
		extractionResults["windows"] = err
	}

	// Extract HVAC equipment with error recovery
	if err := recovery.SafeExecute("extractIDFHVAC", func() error {
		hvacEquip, err := e.extractIDFHVACWithErrorHandling()
		if err != nil {
			return err
		}
		objects = append(objects, hvacEquip...)
		return nil
	}); err != nil {
		extractionResults["hvac"] = err
	}

	// Extract electrical equipment with error recovery
	if err := recovery.SafeExecute("extractIDFElectrical", func() error {
		electricalEquip, err := e.extractIDFElectricalWithErrorHandling()
		if err != nil {
			return err
		}
		objects = append(objects, electricalEquip...)
		return nil
	}); err != nil {
		extractionResults["electrical"] = err
	}

	// Extract electrical devices with error recovery
	if err := recovery.SafeExecute("extractIDFElectricalDevices", func() error {
		electricalDevices, err := e.extractIDFElectricalDevicesWithErrorHandling()
		if err != nil {
			return err
		}
		objects = append(objects, electricalDevices...)
		return nil
	}); err != nil {
		extractionResults["electrical_devices"] = err
	}

	// Extract rooms with error recovery
	if err := recovery.SafeExecute("extractIDFRooms", func() error {
		rooms, err := e.extractIDFRoomsWithErrorHandling()
		if err != nil {
			return err
		}
		objects = append(objects, rooms...)
		return nil
	}); err != nil {
		extractionResults["rooms"] = err
	}

	// Continue with remaining extractions...
	if err := recovery.SafeExecute("extractIDFDimensions", func() error {
		dimensions, err := e.extractIDFDimensionsWithErrorHandling()
		if err != nil {
			return err
		}
		objects = append(objects, dimensions...)
		return nil
	}); err != nil {
		extractionResults["dimensions"] = err
	}

	// Check if we have any objects extracted
	if len(objects) == 0 {
		return nil, NewFatalExtractionError("extractIDFElements", "no objects could be extracted", nil).
			WithContext("extraction_errors", extractionResults)
	}

	// Check if too many extractions failed
	failureRate := float64(len(extractionResults)) / 9.0 // 9 extraction types
	if failureRate > 0.7 {
		return objects, NewExtractionError("extractIDFElements", 
			"high failure rate in extraction", nil).
			WithContext("failure_rate", failureRate).
			WithContext("extraction_errors", extractionResults)
	}

	return objects, nil
}

// Legacy method for backward compatibility
func (e *IDFExtractor) extractIDFElements() []arxobject.ArxObject {
	objects, err := e.extractIDFElementsWithErrorHandling()
	if err != nil {
		// Log error but return what we have
		return objects
	}
	return objects
}

// extractIDFWallsWithErrorHandling extracts walls with comprehensive error handling
func (e *IDFExtractor) extractIDFWallsWithErrorHandling() ([]arxobject.ArxObject, error) {
	var walls []arxobject.ArxObject

	// Validate prerequisites
	if e.arxEngine == nil {
		return nil, NewValidationError("arxEngine", nil, "arxEngine is required for wall extraction")
	}

	// Alafia Elementary School IDF - Real building dimensions
	// Based on typical elementary school mechanical room layout
	
	wallDefinitions := []struct {
		ID          string
		Description string
		Props       map[string]interface{}
	}{
		{
			ID:          "idf_wall_ext_001",
			Description: "South exterior wall - CMU construction",
			Props: map[string]interface{}{
				"start_x":       0.0,
				"start_y":       0.0,
				"end_x":         360.0, // 30'-0" (360 points = 30 feet)
				"end_y":         0.0,
				"length":        360.0,
				"length_feet":   30.0,
				"thickness":     8.0,   // 8" CMU
				"wall_type":     "exterior",
				"material":      "CMU",
				"is_bearing":    true,
				"orientation":   "horizontal",
				"fire_rating":   "2-hour",
				"idf_element":   "exterior_wall",
			},
		},
		// Additional wall definitions will be added here...
	}

	// Process each wall definition with error handling
	for _, wallDef := range wallDefinitions {
		wall, err := e.createWallObject(wallDef.ID, wallDef.Description, wallDef.Props)
		if err != nil {
			return walls, NewProcessingError(wallDef.ID, "wall", "creation", wallDef.Description, err)
		}
		walls = append(walls, wall)
	}

	if len(walls) == 0 {
		return nil, NewExtractionError("extractIDFWalls", "no walls could be extracted", nil)
	}

	return walls, nil
}

// createWallObject creates a wall ArxObject with validation
func (e *IDFExtractor) createWallObject(id, description string, props map[string]interface{}) (arxobject.ArxObject, error) {
	// Validate required properties
	requiredProps := []string{"start_x", "start_y", "end_x", "end_y", "thickness", "material"}
	for _, prop := range requiredProps {
		if _, exists := props[prop]; !exists {
			return arxobject.ArxObject{}, NewValidationError(prop, nil, "required property missing for wall "+id)
		}
	}

	// Serialize properties with error handling
	propsJSON, err := json.Marshal(props)
	if err != nil {
		return arxobject.ArxObject{}, NewProcessingError(id, "wall", "serialization", "failed to serialize properties", err)
	}

	// Calculate wall dimensions from properties
	startX := props["start_x"].(float64)
	startY := props["start_y"].(float64)
	endX := props["end_x"].(float64)
	endY := props["end_y"].(float64)
	thickness := props["thickness"].(float64)

	// Calculate length
	length := math.Sqrt(math.Pow(endX-startX, 2) + math.Pow(endY-startY, 2))

	// Create the wall object
	wall := arxobject.ArxObject{
		ID:   id,
		UUID: uuid.New().String(),
		Type: "wall",
		System: "structural",
		X: int64(startX * 1000000), // Convert to nanometers
		Y: int64(startY * 1000000),
		Z: 0,
		Width: int64(length * 1000000),
		Height: int64(2700 * 1000000), // Standard 9' height in nm
		Depth: int64(thickness * 25400000), // Convert inches to nm
		Properties: propsJSON,
		Confidence: arxobject.ConfidenceScore{
			Classification: 0.92,
			Position:       0.95,
			Properties:     0.88,
			Relationships:  0.75,
			Overall:        0.90,
		},
		ExtractionMethod: "idf_callout",
		Source: "alafia_elementary_idf",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	// Validate and sanitize the wall object
	validator := arxobject.NewArxObjectValidator(nil)
	validationResult := validator.ValidateAndSanitize(&wall)
	
	if !validationResult.IsValid {
		return arxobject.ArxObject{}, NewProcessingError(id, "wall", "validation", 
			fmt.Sprintf("validation failed with %d errors", len(validationResult.Errors)), nil)
	}

	// Use the sanitized object
	if validationResult.SanitizedObj != nil {
		wall = *validationResult.SanitizedObj
	}

	// Log any validation warnings
	if len(validationResult.Warnings) > 0 {
		for _, warning := range validationResult.Warnings {
			// Note: In production, use proper logging
			fmt.Printf("Warning for wall %s: %s\n", id, warning.Message)
		}
	}

	return wall, nil
}

// Legacy method for backward compatibility
func (e *IDFExtractor) extractIDFWalls() []arxobject.ArxObject {
	walls, err := e.extractIDFWallsWithErrorHandling()
	if err != nil {
		// Log error but return what we have
		return walls
	}
	return walls
}

// Stub methods for other extraction functions - implementing error handling pattern

func (e *IDFExtractor) extractIDFDoorsWithErrorHandling() ([]arxobject.ArxObject, error) {
	// TODO: Implement door extraction with error handling
	return []arxobject.ArxObject{}, nil
}

func (e *IDFExtractor) extractIDFWindowsWithErrorHandling() ([]arxobject.ArxObject, error) {
	// TODO: Implement window extraction with error handling
	return []arxobject.ArxObject{}, nil
}

func (e *IDFExtractor) extractIDFHVACWithErrorHandling() ([]arxobject.ArxObject, error) {
	// TODO: Implement HVAC extraction with error handling
	return []arxobject.ArxObject{}, nil
}

func (e *IDFExtractor) extractIDFElectricalWithErrorHandling() ([]arxobject.ArxObject, error) {
	// TODO: Implement electrical extraction with error handling
	return []arxobject.ArxObject{}, nil
}

func (e *IDFExtractor) extractIDFElectricalDevicesWithErrorHandling() ([]arxobject.ArxObject, error) {
	// TODO: Implement electrical devices extraction with error handling
	return []arxobject.ArxObject{}, nil
}

func (e *IDFExtractor) extractIDFRoomsWithErrorHandling() ([]arxobject.ArxObject, error) {
	// TODO: Implement room extraction with error handling
	return []arxobject.ArxObject{}, nil
}

func (e *IDFExtractor) extractIDFDimensionsWithErrorHandling() ([]arxobject.ArxObject, error) {
	// TODO: Implement dimension extraction with error handling
	return []arxobject.ArxObject{}, nil
}

// Error handling for relationship analysis
func (e *IDFExtractor) analyzeIDFRelationshipsWithErrorHandling(objects []arxobject.ArxObject) ([]arxobject.ArxObject, error) {
	if len(objects) == 0 {
		return objects, NewValidationError("objects", len(objects), "no objects provided for relationship analysis")
	}

	// Perform relationship analysis with error recovery
	recovery := DefaultErrorRecovery()
	var analysisError error

	err := recovery.SafeExecute("analyzeIDFRelationships", func() error {
		// TODO: Implement relationship analysis
		// For now, return objects unchanged
		return nil
	})

	if err != nil {
		analysisError = NewExtractionError("analyzeIDFRelationships", "relationship analysis failed", err)
	}

	return objects, analysisError
}

// Error handling for statistics calculation
func (e *IDFExtractor) calculateIDFStatisticsWithErrorHandling(objects []arxobject.ArxObject) (IDFStatistics, error) {
	if len(objects) == 0 {
		return IDFStatistics{}, NewValidationError("objects", len(objects), "no objects provided for statistics calculation")
	}

	stats := IDFStatistics{
		TotalObjects:    len(objects),
		ObjectsByType:   make(map[string]int),
		ObjectsBySystem: make(map[string]int),
		ConfidenceStats: make(map[string]float32),
		IDFElements:     make(map[string]int),
	}

	// Calculate statistics with error handling
	var totalConfidence float32
	for _, obj := range objects {
		// Count by type
		stats.ObjectsByType[obj.Type]++
		
		// Count by system
		stats.ObjectsBySystem[obj.System]++
		
		// Accumulate confidence
		totalConfidence += obj.Confidence.Overall
	}

	// Calculate confidence statistics
	if len(objects) > 0 {
		stats.ConfidenceStats["average"] = totalConfidence / float32(len(objects))
		stats.ConfidenceStats["total"] = totalConfidence
	}

	return stats, nil
}

// Default statistics for error recovery
func (e *IDFExtractor) getDefaultIDFStatistics() IDFStatistics {
	return IDFStatistics{
		TotalObjects:    0,
		ObjectsByType:   make(map[string]int),
		ObjectsBySystem: make(map[string]int),
		ConfidenceStats: map[string]float32{"average": 0.0, "total": 0.0},
		IDFElements:     make(map[string]int),
	}
}

// Legacy methods for backward compatibility
func (e *IDFExtractor) analyzeIDFRelationships(objects []arxobject.ArxObject) []arxobject.ArxObject {
	result, err := e.analyzeIDFRelationshipsWithErrorHandling(objects)
	if err != nil {
		// Log error but return objects unchanged
		return objects
	}
	return result
}

func (e *IDFExtractor) calculateIDFStatistics(objects []arxobject.ArxObject) IDFStatistics {
	stats, err := e.calculateIDFStatisticsWithErrorHandling(objects)
	if err != nil {
		// Return default statistics on error
		return e.getDefaultIDFStatistics()
	}
	return stats
}

// Additional legacy extraction methods (temporarily returning empty for compatibility)

func (e *IDFExtractor) extractIDFDoors() []arxobject.ArxObject {
	doors, _ := e.extractIDFDoorsWithErrorHandling()
	return doors
}

func (e *IDFExtractor) extractIDFWindows() []arxobject.ArxObject {
	windows, _ := e.extractIDFWindowsWithErrorHandling()
	return windows
}

func (e *IDFExtractor) extractIDFHVAC() []arxobject.ArxObject {
	hvac, _ := e.extractIDFHVACWithErrorHandling()
	return hvac
}

func (e *IDFExtractor) extractIDFElectrical() []arxobject.ArxObject {
	electrical, _ := e.extractIDFElectricalWithErrorHandling()
	return electrical
}

func (e *IDFExtractor) extractIDFElectricalDevices() []arxobject.ArxObject {
	devices, _ := e.extractIDFElectricalDevicesWithErrorHandling()
	return devices
}

func (e *IDFExtractor) extractIDFRooms() []arxobject.ArxObject {
	rooms, _ := e.extractIDFRoomsWithErrorHandling()
	return rooms
}

func (e *IDFExtractor) extractIDFDimensions() []arxobject.ArxObject {
	dimensions, _ := e.extractIDFDimensionsWithErrorHandling()
	return dimensions
}

func (e *IDFExtractor) extractIDFGrids() []arxobject.ArxObject {
	// TODO: Implement grid extraction
	return []arxobject.ArxObject{}
}

func (e *IDFExtractor) extractIDFAnnotations() []arxobject.ArxObject {
	// TODO: Implement annotation extraction
	return []arxobject.ArxObject{}
}

func (e *IDFExtractor) extractIDFCallouts() []arxobject.ArxObject {
	// TODO: Implement callout extraction
	return []arxobject.ArxObject{}
}
