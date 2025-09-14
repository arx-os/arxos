package commands

import (
	"context"
	"encoding/json"
	"fmt"
	"os"

	"github.com/joelpate/arxos/internal/bim"
	"github.com/joelpate/arxos/internal/common/logger"
	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/internal/importer"
	"github.com/joelpate/arxos/pkg/models"
)

// ExecuteImport handles the import command
func ExecuteImport(opts ImportOptions) error {
	ctx := context.Background()

	switch opts.Format {
	case "pdf":
		return importPDF(ctx, opts)
	case "bim":
		return importBIM(ctx, opts)
	case "ifc":
		return fmt.Errorf("IFC import not yet implemented")
	default:
		return fmt.Errorf("unsupported format: %s", opts.Format)
	}
}

func importPDF(ctx context.Context, opts ImportOptions) error {
	// Use existing PDF importer
	extractor := importer.NewSimplePDFExtractor()

	file, err := os.Open(opts.InputFile)
	if err != nil {
		return fmt.Errorf("failed to open PDF: %w", err)
	}
	defer file.Close()

	logger.Info("Extracting equipment from PDF...")
	extractedData, err := extractor.ExtractText(file)
	if err != nil {
		return fmt.Errorf("failed to extract from PDF: %w", err)
	}

	logger.Info("Found %d equipment items", len(extractedData.Equipment))

	// Convert extracted equipment to models
	equipment := make([]*models.Equipment, 0, len(extractedData.Equipment))
	for _, e := range extractedData.Equipment {
		equipment = append(equipment, &models.Equipment{
			ID:     e.ID,
			Type:   e.Type,
			Name:   e.ID, // Use ID as name if Name not available
			Status: models.StatusOperational,
		})
	}

	// Create building model with UUID
	building := &models.FloorPlan{
		ID:          opts.BuildingID,
		UUID:        opts.BuildingID, // Use BuildingID as UUID if it follows format
		Name:        opts.BuildingName,
		Building:    opts.BuildingName, // Required field
		Level:       1,
		Description: fmt.Sprintf("Imported from %s", opts.InputFile),
		Equipment:   equipment,
		Rooms:       []*models.Room{}, // Initialize empty
	}

	// Save to database if requested
	if opts.ToDatabase {
		db, err := database.NewSQLiteDBFromPath("arxos.db")
		if err != nil {
			return fmt.Errorf("failed to connect to database: %w", err)
		}
		defer db.Close()

		if err := db.SaveFloorPlan(ctx, building); err != nil {
			return fmt.Errorf("failed to save to database: %w", err)
		}

		logger.Info("Saved building %s to database", opts.BuildingID)
	}

	// Output as BIM if requested
	if opts.ToBIM {
		bimBuilding := convertToSimpleBIM(building)

		output := os.Stdout
		if opts.OutputFile != "" {
			output, err = os.Create(opts.OutputFile)
			if err != nil {
				return fmt.Errorf("failed to create output file: %w", err)
			}
			defer output.Close()
		}

		// Write as JSON for SimpleBuilding
		encoder := json.NewEncoder(output)
		encoder.SetIndent("", "  ")
		if err := encoder.Encode(bimBuilding); err != nil {
			return fmt.Errorf("failed to write BIM: %w", err)
		}

		logger.Info("Exported to BIM format")
	}

	return nil
}

func importBIM(ctx context.Context, opts ImportOptions) error {
	// Parse BIM file
	parser := bim.NewParser()

	file, err := os.Open(opts.InputFile)
	if err != nil {
		return fmt.Errorf("failed to open BIM file: %w", err)
	}
	defer file.Close()

	_, err = parser.Parse(file) // TODO: Use parsed building data
	if err != nil {
		return fmt.Errorf("failed to parse BIM file: %w", err)
	}

	// Convert to database model
	// TODO: Convert from parsed BIM building to FloorPlan
	dbModel := &models.FloorPlan{
		ID:   opts.BuildingID,
		Name: opts.BuildingName,
	}

	// Save to database if requested
	if opts.ToDatabase {
		db, err := database.NewSQLiteDBFromPath("arxos.db")
		if err != nil {
			return fmt.Errorf("failed to connect to database: %w", err)
		}
		defer db.Close()

		if err := db.SaveFloorPlan(ctx, dbModel); err != nil {
			return fmt.Errorf("failed to save to database: %w", err)
		}

		logger.Info("Imported BIM file to database")
	}

	return nil
}

// convertToSimpleBIM converts FloorPlan to SimpleBuilding (defined in export.go)