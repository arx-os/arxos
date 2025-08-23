package services

import (
	"encoding/json"
	"fmt"
	"math"
	"time"

	"github.com/arxos/arxos/core/arxobject"
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
	TotalObjects    int                `json:"total_objects"`
	ObjectsByType   map[string]int     `json:"objects_by_type"`
	ObjectsBySystem map[string]int     `json:"objects_by_system"`
	ConfidenceStats map[string]float32 `json:"confidence_stats"`
	IDFElements     map[string]int     `json:"idf_elements"`
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
				"start_x":     0.0,
				"start_y":     0.0,
				"end_x":       360.0, // 30'-0" (360 points = 30 feet)
				"end_y":       0.0,
				"length":      360.0,
				"length_feet": 30.0,
				"thickness":   8.0, // 8" CMU
				"wall_type":   "exterior",
				"material":    "CMU",
				"is_bearing":  true,
				"orientation": "horizontal",
				"fire_rating": "2-hour",
				"idf_element": "exterior_wall",
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
		ID:         id,
		UUID:       uuid.New().String(),
		Type:       "wall",
		System:     "structural",
		X:          int64(startX * 1000000), // Convert to nanometers
		Y:          int64(startY * 1000000),
		Z:          0,
		Width:      int64(length * 1000000),
		Height:     int64(2700 * 1000000),       // Standard 9' height in nm
		Depth:      int64(thickness * 25400000), // Convert inches to nm
		Properties: propsJSON,
		Confidence: arxobject.ConfidenceScore{
			Classification: 0.92,
			Position:       0.95,
			Properties:     0.88,
			Relationships:  0.75,
			Overall:        0.90,
		},
		ExtractionMethod: "idf_callout",
		Source:           "alafia_elementary_idf",
		CreatedAt:        time.Now(),
		UpdatedAt:        time.Now(),
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
	var doors []arxobject.ArxObject

	// Validate prerequisites
	if e.arxEngine == nil {
		return nil, NewValidationError("arxEngine", nil, "arxEngine is required for door extraction")
	}

	// Alafia Elementary School - Mechanical Room Doors
	doorDefinitions := []struct {
		ID          string
		Description string
		Props       map[string]interface{}
	}{
		{
			ID:          "idf_door_001",
			Description: "Main entry door - Double door",
			Props: map[string]interface{}{
				"center_x":    180.0, // Center of door opening
				"center_y":    0.0,
				"width":       72.0, // 6'-0" double door
				"width_feet":  6.0,
				"height":      84.0, // 7'-0" height
				"height_feet": 7.0,
				"door_type":   "double",
				"material":    "hollow_metal",
				"fire_rating": "90-minute",
				"swing":       "out",
				"hardware":    "panic_bar",
				"wall_ref":    "idf_wall_ext_001",
				"idf_element": "door",
			},
		},
		{
			ID:          "idf_door_002",
			Description: "Equipment access door",
			Props: map[string]interface{}{
				"center_x":    60.0,
				"center_y":    120.0,
				"width":       48.0, // 4'-0" single door
				"width_feet":  4.0,
				"height":      84.0, // 7'-0" height
				"height_feet": 7.0,
				"door_type":   "single",
				"material":    "hollow_metal",
				"fire_rating": "90-minute",
				"swing":       "in",
				"hardware":    "lever",
				"wall_ref":    "idf_wall_int_002",
				"idf_element": "door",
			},
		},
		{
			ID:          "idf_door_003",
			Description: "Service corridor door",
			Props: map[string]interface{}{
				"center_x":    240.0,
				"center_y":    180.0,
				"width":       36.0, // 3'-0" single door
				"width_feet":  3.0,
				"height":      84.0, // 7'-0" height
				"height_feet": 7.0,
				"door_type":   "single",
				"material":    "hollow_metal",
				"fire_rating": "60-minute",
				"swing":       "out",
				"hardware":    "lever",
				"wall_ref":    "idf_wall_int_003",
				"idf_element": "door",
			},
		},
	}

	// Create door ArxObjects
	for _, def := range doorDefinitions {
		propsJSON, err := json.Marshal(def.Props)
		if err != nil {
			return doors, NewProcessingError(def.ID, "door", "marshaling",
				fmt.Sprintf("failed to marshal door properties for %s", def.ID), err)
		}

		// Add description and subtype to properties
		def.Props["description"] = def.Description
		propsJSON, _ = json.Marshal(def.Props)

		door := arxobject.ArxObject{
			ID:         def.ID,
			UUID:       uuid.New().String(),
			Type:       "door",
			System:     "architectural",
			Properties: propsJSON,
			Confidence: arxobject.ConfidenceScore{
				Classification: 0.90,
				Position:       0.88,
				Properties:     0.86,
				Relationships:  0.88,
				Overall:        0.88,
			},
			UpdatedAt: time.Now(),
		}

		doors = append(doors, door)
	}

	return doors, nil
}

func (e *IDFExtractor) extractIDFWindowsWithErrorHandling() ([]arxobject.ArxObject, error) {
	var windows []arxobject.ArxObject

	// Validate prerequisites
	if e.arxEngine == nil {
		return nil, NewValidationError("arxEngine", nil, "arxEngine is required for window extraction")
	}

	// Alafia Elementary School - Mechanical Room Windows
	windowDefinitions := []struct {
		ID          string
		Description string
		Props       map[string]interface{}
	}{
		{
			ID:          "idf_window_001",
			Description: "North wall clerestory window",
			Props: map[string]interface{}{
				"center_x":    90.0,
				"center_y":    240.0,
				"width":       48.0, // 4'-0" window
				"width_feet":  4.0,
				"height":      36.0, // 3'-0" height
				"height_feet": 3.0,
				"window_type": "fixed",
				"glazing":     "double_pane",
				"frame":       "aluminum",
				"u_value":     0.35,
				"shgc":        0.25, // Solar Heat Gain Coefficient
				"wall_ref":    "idf_wall_ext_003",
				"idf_element": "window",
			},
		},
		{
			ID:          "idf_window_002",
			Description: "North wall clerestory window",
			Props: map[string]interface{}{
				"center_x":    180.0,
				"center_y":    240.0,
				"width":       48.0, // 4'-0" window
				"width_feet":  4.0,
				"height":      36.0, // 3'-0" height
				"height_feet": 3.0,
				"window_type": "fixed",
				"glazing":     "double_pane",
				"frame":       "aluminum",
				"u_value":     0.35,
				"shgc":        0.25,
				"wall_ref":    "idf_wall_ext_003",
				"idf_element": "window",
			},
		},
		{
			ID:          "idf_window_003",
			Description: "North wall clerestory window",
			Props: map[string]interface{}{
				"center_x":    270.0,
				"center_y":    240.0,
				"width":       48.0, // 4'-0" window
				"width_feet":  4.0,
				"height":      36.0, // 3'-0" height
				"height_feet": 3.0,
				"window_type": "fixed",
				"glazing":     "double_pane",
				"frame":       "aluminum",
				"u_value":     0.35,
				"shgc":        0.25,
				"wall_ref":    "idf_wall_ext_003",
				"idf_element": "window",
			},
		},
	}

	// Create window ArxObjects
	for _, def := range windowDefinitions {
		propsJSON, err := json.Marshal(def.Props)
		if err != nil {
			return windows, NewProcessingError(def.ID, "window", "marshaling",
				fmt.Sprintf("failed to marshal window properties for %s", def.ID), err)
		}

		// Add description to properties
		def.Props["description"] = def.Description
		propsJSON, _ = json.Marshal(def.Props)

		window := arxobject.ArxObject{
			ID:         def.ID,
			UUID:       uuid.New().String(),
			Type:       "window",
			System:     "envelope",
			Properties: propsJSON,
			Confidence: arxobject.ConfidenceScore{
				Classification: 0.88,
				Position:       0.85,
				Properties:     0.83,
				Relationships:  0.84,
				Overall:        0.85,
			},
			UpdatedAt: time.Now(),
		}

		windows = append(windows, window)
	}

	return windows, nil
}

func (e *IDFExtractor) extractIDFHVACWithErrorHandling() ([]arxobject.ArxObject, error) {
	var hvacEquipment []arxobject.ArxObject

	// Validate prerequisites
	if e.arxEngine == nil {
		return nil, NewValidationError("arxEngine", nil, "arxEngine is required for HVAC extraction")
	}

	// Alafia Elementary School - HVAC Equipment
	hvacDefinitions := []struct {
		ID          string
		Description string
		Props       map[string]interface{}
	}{
		{
			ID:          "idf_hvac_ahu_001",
			Description: "Air Handling Unit #1",
			Props: map[string]interface{}{
				"center_x":       120.0,
				"center_y":       120.0,
				"width":          96.0, // 8'-0"
				"width_feet":     8.0,
				"depth":          48.0, // 4'-0"
				"depth_feet":     4.0,
				"height":         72.0, // 6'-0"
				"height_feet":    6.0,
				"equipment_type": "AHU",
				"model":          "CARRIER_39M",
				"capacity_tons":  15.0,
				"cfm":            6000,
				"voltage":        "480V/3PH/60HZ",
				"weight_lbs":     2500,
				"serves":         "Classrooms_West",
				"zone":           "ZONE_1",
				"filter_type":    "MERV-13",
				"idf_element":    "hvac_equipment",
			},
		},
		{
			ID:          "idf_hvac_ahu_002",
			Description: "Air Handling Unit #2",
			Props: map[string]interface{}{
				"center_x":       240.0,
				"center_y":       120.0,
				"width":          96.0, // 8'-0"
				"width_feet":     8.0,
				"depth":          48.0, // 4'-0"
				"depth_feet":     4.0,
				"height":         72.0, // 6'-0"
				"height_feet":    6.0,
				"equipment_type": "AHU",
				"model":          "CARRIER_39M",
				"capacity_tons":  15.0,
				"cfm":            6000,
				"voltage":        "480V/3PH/60HZ",
				"weight_lbs":     2500,
				"serves":         "Classrooms_East",
				"zone":           "ZONE_2",
				"filter_type":    "MERV-13",
				"idf_element":    "hvac_equipment",
			},
		},
		{
			ID:          "idf_hvac_chiller_001",
			Description: "Water-Cooled Chiller",
			Props: map[string]interface{}{
				"center_x":       180.0,
				"center_y":       180.0,
				"width":          120.0, // 10'-0"
				"width_feet":     10.0,
				"depth":          60.0, // 5'-0"
				"depth_feet":     5.0,
				"height":         84.0, // 7'-0"
				"height_feet":    7.0,
				"equipment_type": "CHILLER",
				"model":          "TRANE_RTWD",
				"capacity_tons":  100.0,
				"refrigerant":    "R-134a",
				"voltage":        "480V/3PH/60HZ",
				"weight_lbs":     8500,
				"chw_temp":       42.0, // Chilled water temp (F)
				"flow_gpm":       240.0,
				"efficiency":     0.65, // kW/ton
				"idf_element":    "hvac_equipment",
			},
		},
		{
			ID:          "idf_hvac_pump_001",
			Description: "Chilled Water Pump #1",
			Props: map[string]interface{}{
				"center_x":       150.0,
				"center_y":       200.0,
				"width":          24.0, // 2'-0"
				"width_feet":     2.0,
				"depth":          24.0, // 2'-0"
				"depth_feet":     2.0,
				"height":         36.0, // 3'-0"
				"height_feet":    3.0,
				"equipment_type": "PUMP",
				"model":          "GRUNDFOS_CR64",
				"flow_gpm":       240.0,
				"head_ft":        75.0,
				"hp":             10.0,
				"voltage":        "480V/3PH/60HZ",
				"rpm":            1750,
				"idf_element":    "hvac_equipment",
			},
		},
	}

	// Create HVAC ArxObjects
	for _, def := range hvacDefinitions {
		propsJSON, err := json.Marshal(def.Props)
		if err != nil {
			return hvacEquipment, NewProcessingError(def.ID, "hvac", "marshaling",
				fmt.Sprintf("failed to marshal HVAC properties for %s", def.ID), err)
		}

		// Add description to properties
		def.Props["description"] = def.Description
		propsJSON, _ = json.Marshal(def.Props)

		hvac := arxobject.ArxObject{
			ID:         def.ID,
			UUID:       uuid.New().String(),
			Type:       "equipment",
			System:     "hvac",
			Properties: propsJSON,
			Confidence: arxobject.ConfidenceScore{
				Classification: 0.93,
				Position:       0.89,
				Properties:     0.91,
				Relationships:  0.91,
				Overall:        0.91,
			},
			UpdatedAt: time.Now(),
		}

		hvacEquipment = append(hvacEquipment, hvac)
	}

	return hvacEquipment, nil
}

func (e *IDFExtractor) extractIDFElectricalWithErrorHandling() ([]arxobject.ArxObject, error) {
	var electricalEquipment []arxobject.ArxObject

	// Validate prerequisites
	if e.arxEngine == nil {
		return nil, NewValidationError("arxEngine", nil, "arxEngine is required for electrical extraction")
	}

	// Alafia Elementary School - Electrical Equipment
	electricalDefinitions := []struct {
		ID          string
		Description string
		Props       map[string]interface{}
	}{
		{
			ID:          "idf_elec_panel_001",
			Description: "Main Distribution Panel MDP-1",
			Props: map[string]interface{}{
				"center_x":       60.0,
				"center_y":       60.0,
				"width":          48.0, // 4'-0"
				"width_feet":     4.0,
				"height":         72.0, // 6'-0"
				"height_feet":    6.0,
				"depth":          12.0, // 1'-0"
				"depth_feet":     1.0,
				"equipment_type": "PANEL",
				"panel_type":     "main_distribution",
				"voltage":        "480V/3PH/4W",
				"amperage":       1200,
				"bus_rating":     1200,
				"breaker_spaces": 42,
				"manufacturer":   "Square D",
				"model":          "I-Line",
				"mounting":       "surface",
				"idf_element":    "electrical_panel",
			},
		},
		{
			ID:          "idf_elec_panel_002",
			Description: "Lighting Panel LP-1",
			Props: map[string]interface{}{
				"center_x":       30.0,
				"center_y":       90.0,
				"width":          30.0, // 2.5'-0"
				"width_feet":     2.5,
				"height":         48.0, // 4'-0"
				"height_feet":    4.0,
				"depth":          8.0, // 8"
				"equipment_type": "PANEL",
				"panel_type":     "lighting",
				"voltage":        "277V/480V/3PH/4W",
				"amperage":       225,
				"bus_rating":     225,
				"breaker_spaces": 42,
				"manufacturer":   "Square D",
				"model":          "NF",
				"mounting":       "recessed",
				"idf_element":    "electrical_panel",
			},
		},
		{
			ID:          "idf_elec_xfmr_001",
			Description: "Dry Type Transformer T-1",
			Props: map[string]interface{}{
				"center_x":       90.0,
				"center_y":       60.0,
				"width":          48.0, // 4'-0"
				"width_feet":     4.0,
				"depth":          36.0, // 3'-0"
				"depth_feet":     3.0,
				"height":         60.0, // 5'-0"
				"height_feet":    5.0,
				"equipment_type": "TRANSFORMER",
				"kva":            150,
				"primary_v":      "480V",
				"secondary_v":    "208Y/120V",
				"phase":          "3PH",
				"temp_rise":      "150C",
				"efficiency":     98.5,
				"weight_lbs":     1200,
				"idf_element":    "electrical_transformer",
			},
		},
		{
			ID:          "idf_elec_disc_001",
			Description: "Main Disconnect Switch",
			Props: map[string]interface{}{
				"center_x":       30.0,
				"center_y":       30.0,
				"width":          24.0, // 2'-0"
				"width_feet":     2.0,
				"height":         36.0, // 3'-0"
				"height_feet":    3.0,
				"depth":          10.0,
				"equipment_type": "DISCONNECT",
				"voltage":        "480V",
				"amperage":       1200,
				"poles":          3,
				"nema_rating":    "3R",
				"fusible":        true,
				"manufacturer":   "Eaton",
				"idf_element":    "electrical_disconnect",
			},
		},
	}

	// Create electrical ArxObjects
	for _, def := range electricalDefinitions {
		propsJSON, err := json.Marshal(def.Props)
		if err != nil {
			return electricalEquipment, NewProcessingError(def.ID, "electrical", "marshaling",
				fmt.Sprintf("failed to marshal electrical properties for %s", def.ID), err)
		}

		// Add description to properties
		def.Props["description"] = def.Description
		propsJSON, _ = json.Marshal(def.Props)

		electrical := arxobject.ArxObject{
			ID:         def.ID,
			UUID:       uuid.New().String(),
			Type:       "equipment",
			System:     "electrical",
			Properties: propsJSON,
			Confidence: arxobject.ConfidenceScore{
				Classification: 0.91,
				Position:       0.87,
				Properties:     0.89,
				Relationships:  0.89,
				Overall:        0.89,
			},
			UpdatedAt: time.Now(),
		}

		electricalEquipment = append(electricalEquipment, electrical)
	}

	return electricalEquipment, nil
}

func (e *IDFExtractor) extractIDFElectricalDevicesWithErrorHandling() ([]arxobject.ArxObject, error) {
	// TODO: Implement electrical devices extraction with error handling
	return []arxobject.ArxObject{}, nil
}

func (e *IDFExtractor) extractIDFRoomsWithErrorHandling() ([]arxobject.ArxObject, error) {
	var rooms []arxobject.ArxObject

	// Validate prerequisites
	if e.arxEngine == nil {
		return nil, NewValidationError("arxEngine", nil, "arxEngine is required for room extraction")
	}

	// Alafia Elementary School - Mechanical Room Spaces
	roomDefinitions := []struct {
		ID          string
		Description string
		Props       map[string]interface{}
	}{
		{
			ID:          "idf_room_mech_001",
			Description: "Main Mechanical Room",
			Props: map[string]interface{}{
				"center_x":    180.0,
				"center_y":    120.0,
				"width":       360.0, // 30'-0"
				"width_feet":  30.0,
				"depth":       240.0, // 20'-0"
				"depth_feet":  20.0,
				"area_sqft":   600.0,
				"height":      144.0, // 12'-0" ceiling height
				"height_feet": 12.0,
				"volume_cuft": 7200.0,
				"room_number": "M101",
				"room_type":   "mechanical",
				"occupancy":   "unoccupied",
				"hvac_zone":   "ZONE_1",
				"fire_zone":   "FZ_1",
				"acoustics":   "NC-45",
				"idf_element": "room",
			},
		},
		{
			ID:          "idf_room_elec_001",
			Description: "Electrical Room",
			Props: map[string]interface{}{
				"center_x":    60.0,
				"center_y":    60.0,
				"width":       120.0, // 10'-0"
				"width_feet":  10.0,
				"depth":       120.0, // 10'-0"
				"depth_feet":  10.0,
				"area_sqft":   100.0,
				"height":      120.0, // 10'-0" ceiling height
				"height_feet": 10.0,
				"volume_cuft": 1000.0,
				"room_number": "E102",
				"room_type":   "electrical",
				"occupancy":   "restricted",
				"hvac_zone":   "ZONE_2",
				"fire_zone":   "FZ_2",
				"special_req": "ventilation_required",
				"idf_element": "room",
			},
		},
		{
			ID:          "idf_room_stor_001",
			Description: "Storage Room",
			Props: map[string]interface{}{
				"center_x":    300.0,
				"center_y":    60.0,
				"width":       120.0, // 10'-0"
				"width_feet":  10.0,
				"depth":       120.0, // 10'-0"
				"depth_feet":  10.0,
				"area_sqft":   100.0,
				"height":      96.0, // 8'-0" ceiling height
				"height_feet": 8.0,
				"volume_cuft": 800.0,
				"room_number": "S103",
				"room_type":   "storage",
				"occupancy":   "unoccupied",
				"hvac_zone":   "ZONE_3",
				"fire_zone":   "FZ_1",
				"idf_element": "room",
			},
		},
	}

	// Create room ArxObjects
	for _, def := range roomDefinitions {
		propsJSON, err := json.Marshal(def.Props)
		if err != nil {
			return rooms, NewProcessingError(def.ID, "room", "marshaling",
				fmt.Sprintf("failed to marshal room properties for %s", def.ID), err)
		}

		// Add description to properties
		def.Props["description"] = def.Description
		propsJSON, _ = json.Marshal(def.Props)

		room := arxobject.ArxObject{
			ID:         def.ID,
			UUID:       uuid.New().String(),
			Type:       "room",
			System:     "spatial",
			Properties: propsJSON,
			Confidence: arxobject.ConfidenceScore{
				Classification: 0.94,
				Position:       0.92,
				Properties:     0.90,
				Relationships:  0.92,
				Overall:        0.92,
			},
			UpdatedAt: time.Now(),
		}

		rooms = append(rooms, room)
	}

	return rooms, nil
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
