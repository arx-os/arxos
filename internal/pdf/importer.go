package pdf

import (
	"context"
	"fmt"
	"io"
	"time"

	"github.com/google/uuid"
	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/internal/logger"
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
	parseResult, err := i.parser.Parse(ctx, reader)
	if err != nil {
		return nil, fmt.Errorf("failed to parse PDF: %w", err)
	}

	// Extract building name from metadata or options
	buildingName := options.BuildingName
	if buildingName == "" && parseResult.Metadata["title"] != "" {
		buildingName = parseResult.Metadata["title"]
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

	// Convert to ArxOS models
	floorPlan := &models.FloorPlan{
		Name:     buildingName,
		Building: buildingName,
		Level:    options.Level,
		Rooms:    []models.Room{},
		Equipment: []models.Equipment{},
	}

	// Process extracted floor plan data
	if parseResult.FloorPlanData != nil {
		// Convert rooms
		for idx, room := range parseResult.FloorPlanData.Rooms {
			roomID := fmt.Sprintf("%s_room_%d", buildingID, idx+1)
			if room.ID != "" {
				roomID = room.ID
			}

			arxRoom := models.Room{
				ID:   roomID,
				Name: room.Name,
				Bounds: models.Bounds{
					MinX: room.Bounds.MinX,
					MinY: room.Bounds.MinY,
					MaxX: room.Bounds.MaxX,
					MaxY: room.Bounds.MaxY,
				},
			}
			floorPlan.Rooms = append(floorPlan.Rooms, arxRoom)
			result.RoomsImported++
		}

		// Convert equipment
		for idx, equip := range parseResult.FloorPlanData.Equipment {
			equipID := fmt.Sprintf("%s_equip_%d", buildingID, idx+1)
			if equip.ID != "" {
				equipID = equip.ID
			}

			equipment := models.Equipment{
				ID:       equipID,
				Name:     equip.Label,
				Type:     equip.Type,
				Location: models.Point{
					X: equip.Position.X,
					Y: equip.Position.Y,
				},
				Status:   models.StatusNormal,
				MarkedAt: time.Now(),
			}

			// Add to floor plan
			floorPlan.Equipment = append(floorPlan.Equipment, equipment)
			result.EquipImported++
		}
	} else {
		// No floor plan detected, create basic structure from text
		result.Warnings = append(result.Warnings, 
			"No floor plan structure detected, importing text labels only")

		// Try to extract room names from text
		for pageNum := range parseResult.Text {
			logger.Debug("Processing page %d text for room extraction", pageNum)
			// This is a simplified extraction - in production would need better parsing
			if len(floorPlan.Rooms) == 0 {
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
			break // Process only first page for now
		}
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
	config := &ParserConfig{
		MaxFileSize:    100 * 1024 * 1024, // 100MB
		ExtractText:    false,
		ExtractImages:  false,
		ExtractVectors: false,
	}
	
	parser := NewParser(config)
	_, err := parser.Parse(ctx, reader)
	if err != nil {
		return fmt.Errorf("PDF validation failed: %w", err)
	}
	
	return nil
}