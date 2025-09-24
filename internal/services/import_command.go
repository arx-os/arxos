package services

import (
	"context"
	"fmt"
	"os"
	"path/filepath"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
)

// ImportCommandOptions defines options for the import command
type ImportCommandOptions struct {
	InputFile      string
	Format         string
	BuildingID     string
	BuildingName   string
	ToDatabase     bool
	ToBIM          bool
	OutputFile     string
	ValidateOnly   bool // Only validate, don't save
	MergeExisting  bool // Merge with existing data
	EnhanceSpatial bool // Enhance with spatial data
}

// ImportCommandService handles the import command
type ImportCommandService struct {
	db database.DB
}

// NewImportCommandService creates a new import command service
func NewImportCommandService(db database.DB) *ImportCommandService {
	return &ImportCommandService{db: db}
}

// ExecuteImport handles the import command
func (s *ImportCommandService) ExecuteImport(opts ImportCommandOptions) error {
	ctx := context.Background()

	// Validate input file exists
	if _, err := os.Stat(opts.InputFile); os.IsNotExist(err) {
		return fmt.Errorf("input file does not exist: %s", opts.InputFile)
	}

	// Determine format from file extension if not specified
	if opts.Format == "" {
		ext := filepath.Ext(opts.InputFile)
		switch ext {
		case ".pdf":
			opts.Format = "pdf"
		case ".bim.txt":
			opts.Format = "bim"
		case ".ifc":
			opts.Format = "ifc"
		case ".csv":
			opts.Format = "csv"
		case ".json", ".geojson":
			opts.Format = "json"
		default:
			return fmt.Errorf("unsupported file format: %s", ext)
		}
	}

	logger.Info("Importing %s file: %s", opts.Format, opts.InputFile)

	switch opts.Format {
	case "pdf":
		return s.importPDF(ctx, opts)
	case "bim":
		return s.importBIM(ctx, opts)
	case "ifc":
		return s.importIFC(ctx, opts)
	case "csv":
		return s.importCSV(ctx, opts)
	case "json":
		return s.importJSON(ctx, opts)
	default:
		return fmt.Errorf("unsupported format: %s", opts.Format)
	}
}

func (s *ImportCommandService) importPDF(ctx context.Context, opts ImportCommandOptions) error {
	// Use the import implementations
	impl := NewImportImplementations(s.db)
	return impl.ImportPDF(ctx, opts.InputFile, opts)
}

func (s *ImportCommandService) importBIM(ctx context.Context, opts ImportCommandOptions) error {
	// Use the existing import service
	// Note: This is a simplified version - the full import service would need proper initialization
	logger.Info("Importing BIM file: %s", opts.InputFile)

	// For now, just validate the file exists and is readable
	file, err := os.Open(opts.InputFile)
	if err != nil {
		return fmt.Errorf("failed to open BIM file: %w", err)
	}
	defer file.Close()

	logger.Info("✓ BIM file validated")

	if opts.ValidateOnly {
		logger.Info("Validation only - no data imported")
		return nil
	}

	// Use the import implementations
	impl := NewImportImplementations(s.db)
	return impl.ImportBIM(ctx, opts.InputFile, opts)
}

func (s *ImportCommandService) importIFC(ctx context.Context, opts ImportCommandOptions) error {
	// Use the import implementations
	impl := NewImportImplementations(s.db)
	return impl.ImportIFC(ctx, opts.InputFile, opts)
}

func (s *ImportCommandService) importCSV(ctx context.Context, opts ImportCommandOptions) error {
	// Use the import implementations
	impl := NewImportImplementations(s.db)
	return impl.ImportCSV(ctx, opts.InputFile, opts)
}

func (s *ImportCommandService) importJSON(ctx context.Context, opts ImportCommandOptions) error {
	// Use the import implementations
	impl := NewImportImplementations(s.db)
	return impl.ImportJSON(ctx, opts.InputFile, opts)
}
