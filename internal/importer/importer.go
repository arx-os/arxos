// Package importer provides PDF import and data extraction capabilities for ArxOS.
// It handles parsing building floor plans from PDF files and converting them into
// ArxOS data models including rooms, equipment, and spatial relationships.
package importer

import (
	"context"
	"fmt"
	"io"
	"time"

	"github.com/google/uuid"
	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/internal/common/logger"
	"github.com/joelpate/arxos/pkg/models"
)

// Importer handles PDF import and conversion to ArxOS data models
type Importer struct {
	parser *Parser
	db     database.DB
}

// NewImporter creates a new PDF importer
func NewImporter(db database.DB) *Importer {
	return &Importer{
		parser: NewParser(DefaultParserConfig()),
		db:     db,
	}
}

// ImportOptions configures the import process
type ImportOptions struct {
	BuildingName string
	BuildingID   string
	Level        int
	UserID       string
	Overwrite    bool
}

// ImportResult contains the results of an import operation
type ImportResult struct {
	BuildingID    string
	RoomsImported int
	EquipImported int
	Errors        []string
	Warnings      []string
	Duration      time.Duration
}

// Import processes a PDF file and imports it as a building
func (i *Importer) Import(ctx context.Context, reader io.Reader, options ImportOptions) (*ImportResult, error) {
	startTime := time.Now()
	result := &ImportResult{
		Errors:   []string{},
		Warnings: []string{},
	}

	// Parse PDF
	parseResult, err := i.parser.Parse(reader)
	if err != nil {
		return nil, fmt.Errorf("failed to parse PDF: %w", err)
	}

	// Extract building name from metadata or options
	buildingName := options.BuildingName
	if buildingName == "" {
		buildingName = parseResult.Building
	}
	if buildingName == "" {
		buildingName = fmt.Sprintf("Imported Building %s", time.Now().Format("2006-01-02"))
	}

	// Generate or use provided building ID
	buildingID := options.BuildingID
	if buildingID == "" {
		buildingID = "bldg_" + uuid.New().String()[:8]
	}
	result.BuildingID = buildingID

	// Check if building exists
	if !options.Overwrite {
		existing, err := i.db.GetFloorPlan(ctx, buildingID)
		if err == nil && existing != nil {
			return nil, fmt.Errorf("building with ID %s already exists", buildingID)
		}
	}

	// Use the parsed floor plan directly
	floorPlan := parseResult
	floorPlan.Name = buildingName
	floorPlan.Building = buildingName
	if options.Level > 0 {
		floorPlan.Level = options.Level
	}

	// Count imported items
	result.RoomsImported = len(floorPlan.Rooms)
	result.EquipImported = len(floorPlan.Equipment)

	if result.RoomsImported == 0 {
		// No floor plan detected, create basic structure
		result.Warnings = append(result.Warnings, 
			"No rooms detected in imported file")
		// Create at least one default room
		floorPlan.Rooms = append(floorPlan.Rooms, models.Room{
			ID:   buildingID + "_default",
			Name: "Main Floor",
			Bounds: models.Bounds{
				MinX: 0, MinY: 0,
				MaxX: 100, MaxY: 100,
			},
		})
		result.RoomsImported = 1
	}

	// Save floor plan to database
	if err := i.db.SaveFloorPlan(ctx, floorPlan); err != nil {
		if options.Overwrite {
			// Try update instead
			if err := i.db.UpdateFloorPlan(ctx, floorPlan); err != nil {
				return nil, fmt.Errorf("failed to update floor plan: %w", err)
			}
		} else {
			return nil, fmt.Errorf("failed to save floor plan: %w", err)
		}
	}

	result.Duration = time.Since(startTime)
	
	logger.Info("PDF import completed: %d rooms, %d equipment items in %v", 
		result.RoomsImported, result.EquipImported, result.Duration)

	return result, nil
}

// ValidatePDF checks if a PDF is suitable for import
func (i *Importer) ValidatePDF(ctx context.Context, reader io.Reader) error {
	config := DefaultParserConfig()
	
	parser := NewParser(config)
	_, err := parser.Parse(reader)
	if err != nil {
		return fmt.Errorf("PDF validation failed: %w", err)
	}
	
	return nil
}