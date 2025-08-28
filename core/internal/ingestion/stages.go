package ingestion

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"time"
)

// ValidationStage validates input data
type ValidationStage struct {
	maxFileSize int64
	allowedTypes []string
}

// NewValidationStage creates a new validation stage
func NewValidationStage() *ValidationStage {
	return &ValidationStage{
		maxFileSize: 100 * 1024 * 1024, // 100MB
		allowedTypes: []string{"pdf", "png", "jpeg", "jpg", "tiff"},
	}
}

// Name returns the stage name
func (s *ValidationStage) Name() string {
	return "validation"
}

// Process validates the input data
func (s *ValidationStage) Process(ctx context.Context, data interface{}) (interface{}, error) {
	switch input := data.(type) {
	case []byte:
		if int64(len(input)) > s.maxFileSize {
			return nil, fmt.Errorf("file size exceeds maximum of %d bytes", s.maxFileSize)
		}
		return input, nil
	case string:
		// Validate file path or other string input
		return input, nil
	default:
		return nil, fmt.Errorf("unsupported input type: %T", data)
	}
}

// Validate checks if data is valid for this stage
func (s *ValidationStage) Validate(data interface{}) error {
	if data == nil {
		return fmt.Errorf("input data is nil")
	}
	return nil
}

// ExtractionStage handles content extraction
type ExtractionStage struct {
	grpcClient *GRPCClient
}

// NewExtractionStage creates a new extraction stage
func NewExtractionStage(client *GRPCClient) *ExtractionStage {
	return &ExtractionStage{
		grpcClient: client,
	}
}

// Name returns the stage name
func (s *ExtractionStage) Name() string {
	return "extraction"
}

// Process extracts content from documents
func (s *ExtractionStage) Process(ctx context.Context, data interface{}) (interface{}, error) {
	pdfData, ok := data.([]byte)
	if !ok {
		return nil, fmt.Errorf("expected []byte, got %T", data)
	}

	options := &PDFExtractionOptions{
		ExtractText:      true,
		ExtractImages:    true,
		ExtractTables:    true,
		DetectFloorPlans: true,
		DPI:              150,
		OutputFormat:     "json",
	}

	result, err := s.grpcClient.ExtractPDF(ctx, pdfData, options)
	if err != nil {
		return nil, fmt.Errorf("PDF extraction failed: %w", err)
	}

	return result, nil
}

// Validate checks if data is valid for extraction
func (s *ExtractionStage) Validate(data interface{}) error {
	if _, ok := data.([]byte); !ok {
		return fmt.Errorf("extraction stage requires []byte input")
	}
	return nil
}

// DetectionStage detects structural elements
type DetectionStage struct {
	grpcClient *GRPCClient
}

// NewDetectionStage creates a new detection stage
func NewDetectionStage(client *GRPCClient) *DetectionStage {
	return &DetectionStage{
		grpcClient: client,
	}
}

// Name returns the stage name
func (s *DetectionStage) Name() string {
	return "detection"
}

// Process detects walls and other elements
func (s *DetectionStage) Process(ctx context.Context, data interface{}) (interface{}, error) {
	extractionResult, ok := data.(*PDFExtractionResult)
	if !ok {
		// Try direct image processing
		imageData, ok := data.([]byte)
		if !ok {
			return nil, fmt.Errorf("expected PDFExtractionResult or []byte, got %T", data)
		}
		
		options := &WallDetectionOptions{
			ImageFormat:      "png",
			MinWallThickness: 0.1,
			MaxWallThickness: 0.5,
			DetectDoors:      true,
			DetectWindows:    true,
			DetectColumns:    true,
			Units:            "meters",
		}
		
		return s.grpcClient.DetectWalls(ctx, imageData, options)
	}

	// Process floor plans from PDF extraction
	var allResults []WallDetectionResult
	for i, floorPlan := range extractionResult.FloorPlans {
		if i < len(extractionResult.Pages) && len(extractionResult.Pages[i].Images) > 0 {
			imageData := extractionResult.Pages[i].Images[0].Data
			
			options := &WallDetectionOptions{
				ImageFormat:      "png",
				MinWallThickness: 0.1,
				MaxWallThickness: 0.5,
				DetectDoors:      true,
				DetectWindows:    true,
				DetectColumns:    true,
				Units:            "meters",
			}
			
			result, err := s.grpcClient.DetectWalls(ctx, imageData, options)
			if err != nil {
				continue // Skip failed detections
			}
			
			result.FloorPlan = &floorPlan
			allResults = append(allResults, *result)
		}
	}

	return allResults, nil
}

// Validate checks if data is valid for detection
func (s *DetectionStage) Validate(data interface{}) error {
	return nil // Accepts multiple input types
}

// MeasurementStage extracts measurements
type MeasurementStage struct {
	grpcClient *GRPCClient
}

// NewMeasurementStage creates a new measurement stage
func NewMeasurementStage(client *GRPCClient) *MeasurementStage {
	return &MeasurementStage{
		grpcClient: client,
	}
}

// Name returns the stage name
func (s *MeasurementStage) Name() string {
	return "measurement"
}

// Process extracts measurements from drawings
func (s *MeasurementStage) Process(ctx context.Context, data interface{}) (interface{}, error) {
	// This stage is optional and can be skipped if no measurements needed
	detectionResults, ok := data.([]WallDetectionResult)
	if !ok {
		// Single result
		singleResult, ok := data.(*WallDetectionResult)
		if !ok {
			return data, nil // Pass through if not applicable
		}
		detectionResults = []WallDetectionResult{*singleResult}
	}

	// Extract measurements for each detection result
	var allMeasurements []MeasurementResult
	for _, detection := range detectionResults {
		// Skip if no walls detected
		if len(detection.Walls) == 0 {
			continue
		}
		
		// Measurements would be extracted here if image data was available
		// For now, we'll create estimated measurements based on detected walls
		measurements := s.estimateMeasurements(detection.Walls)
		allMeasurements = append(allMeasurements, measurements)
	}

	return allMeasurements, nil
}

// Validate checks if data is valid for measurement
func (s *MeasurementStage) Validate(data interface{}) error {
	return nil // Optional stage
}

// estimateMeasurements creates estimated measurements from walls
func (s *MeasurementStage) estimateMeasurements(walls []Wall) MeasurementResult {
	dimensions := make([]Dimension, 0, len(walls))
	
	for i, wall := range walls {
		// Calculate wall length
		dx := wall.EndX - wall.StartX
		dy := wall.EndY - wall.StartY
		length := float32(math.Sqrt(float64(dx*dx + dy*dy)))
		
		dimensions = append(dimensions, Dimension{
			ID:            fmt.Sprintf("dim_%d", i),
			StartPoint:    Point2D{X: wall.StartX, Y: wall.StartY},
			EndPoint:      Point2D{X: wall.EndX, Y: wall.EndY},
			Value:         length,
			Units:         "meters",
			DimensionType: "linear",
			AssociatedElementID: wall.ID,
		})
	}
	
	return MeasurementResult{
		Dimensions: dimensions,
		Scale: &Scale{
			PixelsPerUnit: 100,
			Units:         "meters",
			Confidence:    0.8,
		},
		Confidence: 0.75,
	}
}

// BIMGenerationStage generates 3D BIM models
type BIMGenerationStage struct {
	grpcClient *GRPCClient
}

// NewBIMGenerationStage creates a new BIM generation stage
func NewBIMGenerationStage(client *GRPCClient) *BIMGenerationStage {
	return &BIMGenerationStage{
		grpcClient: client,
	}
}

// Name returns the stage name
func (s *BIMGenerationStage) Name() string {
	return "bim_generation"
}

// Process generates BIM from detected elements
func (s *BIMGenerationStage) Process(ctx context.Context, data interface{}) (interface{}, error) {
	detectionResults, ok := data.([]WallDetectionResult)
	if !ok {
		singleResult, ok := data.(*WallDetectionResult)
		if !ok {
			return nil, fmt.Errorf("expected WallDetectionResult, got %T", data)
		}
		detectionResults = []WallDetectionResult{*singleResult}
	}

	// Aggregate all walls and rooms
	var allWalls []Wall
	var allRooms []Room
	var floorPlan *FloorPlan
	
	for _, result := range detectionResults {
		allWalls = append(allWalls, result.Walls...)
		allRooms = append(allRooms, result.Rooms...)
		if result.FloorPlan != nil && floorPlan == nil {
			floorPlan = result.FloorPlan
		}
	}

	// Generate BIM
	request := &BIMGenerationRequest{
		FloorPlan: floorPlan,
		Walls:     allWalls,
		Rooms:     allRooms,
		Options: BIMOptions{
			DefaultFloorHeight: 3.0,
			DefaultWallHeight:  3.0,
			GenerateCeiling:    true,
			GenerateRoof:       false,
			CoordinateSystem:   "local",
			LevelOfDetail:      300,
		},
	}

	result, err := s.grpcClient.Generate3DBIM(ctx, request)
	if err != nil {
		return nil, fmt.Errorf("BIM generation failed: %w", err)
	}

	return result, nil
}

// Validate checks if data is valid for BIM generation
func (s *BIMGenerationStage) Validate(data interface{}) error {
	return nil
}

// PersistenceStage saves results to database
type PersistenceStage struct {
	db *sql.DB
}

// NewPersistenceStage creates a new persistence stage
func NewPersistenceStage(db *sql.DB) *PersistenceStage {
	return &PersistenceStage{
		db: db,
	}
}

// Name returns the stage name
func (s *PersistenceStage) Name() string {
	return "persistence"
}

// Process persists results to database
func (s *PersistenceStage) Process(ctx context.Context, data interface{}) (interface{}, error) {
	bimResult, ok := data.(*BIMGenerationResult)
	if !ok {
		return nil, fmt.Errorf("expected BIMGenerationResult, got %T", data)
	}

	// Begin transaction
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	// Save BIM model
	modelQuery := `
		INSERT INTO bim_models (id, name, ifc_version, ifc_data, gltf_data, confidence, created_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
	`
	
	_, err = tx.Exec(modelQuery, 
		bimResult.ModelID,
		bimResult.ModelName,
		bimResult.IFCVersion,
		bimResult.IFCData,
		bimResult.GLTFData,
		bimResult.Confidence,
		time.Now(),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to save BIM model: %w", err)
	}

	// Save BIM elements
	elementQuery := `
		INSERT INTO bim_elements (id, model_id, ifc_class, name, properties, material_id, created_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
	`
	
	for _, element := range bimResult.Elements {
		propertiesJSON, err := json.Marshal(element.Properties)
		if err != nil {
			return nil, fmt.Errorf("failed to marshal properties: %w", err)
		}
		
		_, err = tx.Exec(elementQuery,
			element.ID,
			bimResult.ModelID,
			element.IFCClass,
			element.Name,
			propertiesJSON,
			element.MaterialID,
			time.Now(),
		)
		if err != nil {
			return nil, fmt.Errorf("failed to save BIM element: %w", err)
		}
	}

	// Save BIM spaces
	spaceQuery := `
		INSERT INTO bim_spaces (id, model_id, name, space_type, area, volume, created_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
	`
	
	for _, space := range bimResult.Spaces {
		_, err = tx.Exec(spaceQuery,
			space.ID,
			bimResult.ModelID,
			space.Name,
			space.SpaceType,
			space.Area,
			space.Volume,
			time.Now(),
		)
		if err != nil {
			return nil, fmt.Errorf("failed to save BIM space: %w", err)
		}
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return nil, fmt.Errorf("failed to commit transaction: %w", err)
	}

	// Return persistence result
	result := map[string]interface{}{
		"model_id":       bimResult.ModelID,
		"elements_saved": len(bimResult.Elements),
		"spaces_saved":   len(bimResult.Spaces),
		"timestamp":      time.Now(),
	}

	return result, nil
}

// Validate checks if data is valid for persistence
func (s *PersistenceStage) Validate(data interface{}) error {
	if _, ok := data.(*BIMGenerationResult); !ok {
		return fmt.Errorf("persistence stage requires BIMGenerationResult")
	}
	return nil
}

// Add math import for estimateMeasurements
import "math"