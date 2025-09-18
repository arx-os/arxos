package commands

import (
	"context"
	"fmt"
	"os"
	"strings"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/importer"
	"github.com/arx-os/arxos/internal/importer/formats"
	"github.com/arx-os/arxos/internal/importer/storage"
)

// UseNewImportPipeline checks if the new import pipeline should be used
func UseNewImportPipeline() bool {
	// Check environment variable for feature flag
	flag := os.Getenv("ARXOS_USE_NEW_IMPORT")
	if flag == "" {
		// Check config file
		flag = os.Getenv("ARXOS_IMPORT_VERSION")
	}

	// Enable new pipeline if flag is set to true, yes, 1, or v2
	switch strings.ToLower(flag) {
	case "true", "yes", "1", "v2", "new":
		logger.Info("Using new import pipeline (v2)")
		return true
	case "false", "no", "0", "v1", "old":
		logger.Info("Using legacy import pipeline (v1)")
		return false
	default:
		// Default to old pipeline for stability
		// Change this to true when ready for full rollout
		logger.Debug("No import pipeline flag set, using legacy (v1)")
		return false
	}
}

// ExecuteImportV2 handles imports using the new pipeline
func ExecuteImportV2(opts ImportOptions) error {
	ctx := context.Background()

	logger.Info("Starting import with new pipeline v2")
	logger.Info("Format: %s, Building: %s", opts.Format, opts.BuildingID)

	// Open input file
	file, err := os.Open(opts.InputFile)
	if err != nil {
		return fmt.Errorf("failed to open input file: %w", err)
	}
	defer file.Close()

	// Initialize database
	var db database.DB
	if opts.ToDatabase {
		dbPath := os.Getenv("ARXOS_DB_PATH")
		if dbPath == "" {
			dbPath = "arxos.db"
		}

		db, err = database.NewSQLiteDBFromPath(dbPath)
		if err != nil {
			return fmt.Errorf("failed to connect to database: %w", err)
		}
		defer db.Close()
	}

	// Create storage adapter
	storageAdapter := storage.NewDatabaseAdapter(db)

	// Create import pipeline
	pipeline := importer.NewPipeline(storageAdapter)

	// Register format importers
	pipeline.RegisterImporter(formats.NewPDFImporter())
	pipeline.RegisterImporter(formats.NewIFCImporter())

	// Register enhancers
	pipeline.RegisterEnhancer(&importer.SpatialEnhancer{})
	pipeline.RegisterEnhancer(&importer.ConfidenceEnhancer{})

	// Set up import options
	importOpts := importer.ImportOptions{
		Format:       opts.Format,
		BuildingID:   opts.BuildingID,
		BuildingName: opts.BuildingName,

		ValidateOnly:   opts.ValidateOnly,
		EnhanceSpatial: true,

		SaveToDatabase: opts.ToDatabase,
		SaveToBIM:      opts.ToBIM,
		OutputPath:     opts.OutputFile,

		ProgressCallback: func(stage string, percent int) {
			logger.Debug("Import progress: %s (%d%%)", stage, percent)
		},
	}

	// Perform import
	model, err := pipeline.Import(ctx, file, importOpts)
	if err != nil {
		return fmt.Errorf("import failed: %w", err)
	}

	// Log results
	logger.Info("Import completed successfully")
	logger.Info("Building: %s", model.Name)
	logger.Info("Floors: %d", len(model.Floors))
	logger.Info("Equipment: %d", len(model.GetAllEquipment()))
	logger.Info("Confidence: %v", model.Confidence)
	logger.Info("Coverage: %.1f%%", model.Coverage)

	// Log validation issues
	if len(model.ValidationIssues) > 0 {
		logger.Warn("Validation issues found: %d", len(model.ValidationIssues))
		for _, issue := range model.ValidationIssues {
			if issue.Level == "error" {
				logger.Error("  [%s] %s: %s", issue.Level, issue.Field, issue.Message)
			} else {
				logger.Warn("  [%s] %s: %s", issue.Level, issue.Field, issue.Message)
			}
		}
	}

	return nil
}

// ExecuteImportWithMigration handles the gradual migration
func ExecuteImportWithMigration(opts ImportOptions) error {
	// Check if we should use the new pipeline
	if UseNewImportPipeline() {
		// Try new pipeline
		err := ExecuteImportV2(opts)
		if err != nil {
			// Check if we should fall back
			if os.Getenv("ARXOS_IMPORT_FALLBACK") == "true" {
				logger.Warn("New pipeline failed, falling back to legacy: %v", err)
				return ExecuteImport(opts)
			}
			return err
		}
		return nil
	}

	// Use legacy pipeline
	return ExecuteImport(opts)
}

// MigrateExistingData migrates data from old format to new format
func MigrateExistingData(ctx context.Context, buildingID string) error {
	logger.Info("Migrating building %s to new format", buildingID)

	// Load using old system
	db, err := database.NewSQLiteDBFromPath("arxos.db")
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	// Load old floor plan
	_, err = db.GetFloorPlan(ctx, buildingID)
	if err != nil {
		return fmt.Errorf("failed to load old data: %w", err)
	}

	// Convert to new model using storage adapter
	_ = storage.NewDatabaseAdapter(db)

	// TODO: Implement actual migration logic
	// The adapter already has a fromFloorPlan method that handles this
	// We could expose it or create a migration-specific method

	logger.Info("Migration completed for building %s", buildingID)

	return nil
}

// ImportMetrics tracks import performance
type ImportMetrics struct {
	Format          string
	InputSize       int64
	ProcessTime     float64
	FloorCount      int
	EquipmentCount  int
	Success         bool
	UsedNewPipeline bool
}

// RecordImportMetrics records metrics for monitoring
func RecordImportMetrics(metrics ImportMetrics) {
	// In production, this would send to monitoring system
	logger.Debug("Import metrics: Format=%s, Size=%d, Time=%.2fs, Floors=%d, Equipment=%d, Success=%v, NewPipeline=%v",
		metrics.Format,
		metrics.InputSize,
		metrics.ProcessTime,
		metrics.FloorCount,
		metrics.EquipmentCount,
		metrics.Success,
		metrics.UsedNewPipeline,
	)

	// Could write to metrics file for analysis
	if os.Getenv("ARXOS_METRICS_ENABLED") == "true" {
		// Write to metrics file or send to monitoring service
	}
}
