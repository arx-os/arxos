package importer

import (
	"context"
	"fmt"
	"io"
	"time"

	"github.com/google/uuid"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/core/building"
)

// ImportOptions contains options for the import process
type ImportOptions struct {
	// Format hint (optional, will auto-detect if not provided)
	Format string

	// Building identification
	BuildingID   string
	BuildingName string

	// Processing options
	ValidateOnly   bool // Only validate, don't save
	SkipValidation bool // Skip validation checks
	EnhanceSpatial bool // Enhance with spatial data
	MergeExisting  bool // Merge with existing building data

	// Storage targets
	SaveToDatabase bool
	SaveToBIM      bool
	OutputPath     string

	// Progress callback
	ProgressCallback func(stage string, percent int)
}

// StorageTarget represents where to save the imported data
type StorageTarget string

const (
	StorageTargetDatabase StorageTarget = "database"
	StorageTargetBIM      StorageTarget = "bim"
	StorageTargetFile     StorageTarget = "file"
)

// ImportCapabilities describes what an importer can do
type ImportCapabilities struct {
	SupportsSpatial    bool
	SupportsHierarchy  bool
	SupportsMetadata   bool
	SupportsConfidence bool
	SupportsStreaming  bool
	MaxFileSize        int64 // max file size in bytes, 0 = no limit
}

// ImportPipeline is the main interface for importing building data
type ImportPipeline interface {
	// Import performs the full import process
	Import(ctx context.Context, input io.Reader, opts ImportOptions) (*building.BuildingModel, error)

	// Validate checks the model for issues
	Validate(model *building.BuildingModel) []building.ValidationIssue

	// Enhance adds additional data to the model
	Enhance(ctx context.Context, model *building.BuildingModel) error

	// Save persists the model to storage
	Save(ctx context.Context, model *building.BuildingModel, target StorageTarget) error
}

// FormatImporter is the interface for format-specific importers
type FormatImporter interface {
	// CanImport checks if this importer can handle the input
	CanImport(input io.Reader) bool

	// ImportToModel converts the input to a building model
	ImportToModel(ctx context.Context, input io.Reader, opts ImportOptions) (*building.BuildingModel, error)

	// GetFormat returns the format name
	GetFormat() string

	// GetCapabilities returns what this importer supports
	GetCapabilities() ImportCapabilities
}

// Pipeline implements the ImportPipeline interface
type Pipeline struct {
	importers map[string]FormatImporter
	storage   StorageAdapter
	enhancers []Enhancer
}

// NewPipeline creates a new import pipeline
func NewPipeline(storage StorageAdapter) *Pipeline {
	return &Pipeline{
		importers: make(map[string]FormatImporter),
		storage:   storage,
		enhancers: []Enhancer{},
	}
}

// RegisterImporter adds a format importer to the pipeline
func (p *Pipeline) RegisterImporter(importer FormatImporter) {
	p.importers[importer.GetFormat()] = importer
	logger.Debug("Registered importer for format: %s", importer.GetFormat())
}

// RegisterEnhancer adds an enhancer to the pipeline
func (p *Pipeline) RegisterEnhancer(enhancer Enhancer) {
	p.enhancers = append(p.enhancers, enhancer)
}

// Import performs the full import process
func (p *Pipeline) Import(ctx context.Context, input io.Reader, opts ImportOptions) (*building.BuildingModel, error) {
	startTime := time.Now()

	// Report progress
	if opts.ProgressCallback != nil {
		opts.ProgressCallback("Starting import", 0)
	}

	// Find appropriate importer
	var importer FormatImporter
	if opts.Format != "" {
		// Use specified format
		var ok bool
		importer, ok = p.importers[opts.Format]
		if !ok {
			return nil, fmt.Errorf("no importer registered for format: %s", opts.Format)
		}
	} else {
		// Auto-detect format
		for _, imp := range p.importers {
			if imp.CanImport(input) {
				importer = imp
				logger.Debug("Auto-detected format: %s", imp.GetFormat())
				break
			}
		}
		if importer == nil {
			return nil, fmt.Errorf("unable to detect input format")
		}
	}

	// Report progress
	if opts.ProgressCallback != nil {
		opts.ProgressCallback("Importing data", 20)
	}

	// Import to model
	model, err := importer.ImportToModel(ctx, input, opts)
	if err != nil {
		return nil, fmt.Errorf("import failed: %w", err)
	}

	// Set metadata
	model.ImportMetadata.ImportedAt = time.Now()
	model.ImportMetadata.Format = importer.GetFormat()

	// Update building timestamp
	if model.Building != nil {
		model.Building.UpdatedAt = time.Now()

		// Apply building ID and name from options
		if opts.BuildingID != "" {
			model.Building.ArxosID = opts.BuildingID
		}
		if opts.BuildingName != "" {
			model.Building.Name = opts.BuildingName
		}
	}

	// Report progress
	if opts.ProgressCallback != nil {
		opts.ProgressCallback("Validating data", 40)
	}

	// Validate unless skipped
	if !opts.SkipValidation {
		issues := p.Validate(model)
		model.ValidationIssues = issues

		// Check for critical errors
		for _, issue := range issues {
			if issue.Level == "error" {
				if opts.ValidateOnly {
					return model, fmt.Errorf("validation failed: %s", issue.Message)
				}
				logger.Warn("Validation error: %s - %s", issue.Field, issue.Message)
			}
		}
	}

	// If validate only, return here
	if opts.ValidateOnly {
		logger.Info("Validation complete, skipping save (ValidateOnly=true)")
		return model, nil
	}

	// Report progress
	if opts.ProgressCallback != nil {
		opts.ProgressCallback("Enhancing data", 60)
	}

	// Enhance the model
	if opts.EnhanceSpatial {
		if err := p.Enhance(ctx, model); err != nil {
			logger.Warn("Enhancement failed: %v", err)
			// Don't fail import on enhancement errors
		}
	}

	// TODO: Calculate coverage if needed
	// Coverage calculation would go here

	// Report progress
	if opts.ProgressCallback != nil {
		opts.ProgressCallback("Saving data", 80)
	}

	// Save to specified targets
	if opts.SaveToDatabase {
		if err := p.Save(ctx, model, StorageTargetDatabase); err != nil {
			return nil, fmt.Errorf("failed to save to database: %w", err)
		}
	}

	if opts.SaveToBIM && opts.OutputPath != "" {
		if err := p.Save(ctx, model, StorageTargetBIM); err != nil {
			return nil, fmt.Errorf("failed to save to BIM: %w", err)
		}
	}

	// Report completion
	if opts.ProgressCallback != nil {
		opts.ProgressCallback("Complete", 100)
	}

	logger.Info("Import completed in %v", time.Since(startTime))

	buildingName := "Unknown"
	if model.Building != nil {
		buildingName = model.Building.Name
	}
	logger.Info("Building: %s, Floors: %d, Equipment: %d",
		buildingName, len(model.Floors), len(model.Equipment))

	return model, nil
}

// Validate checks the model for issues
func (p *Pipeline) Validate(model *building.BuildingModel) []building.ValidationIssue {
	// Use the model's built-in validation
	issues := model.Validate()

	// Add pipeline-specific validation
	if model.Building != nil && model.Building.ArxosID == "" {
		issues = append(issues, building.ValidationIssue{
			Level:   building.ValidationLevelError,
			Type:    "missing_id",
			Field:   "ArxosID",
			Message: "Building must have an ArxosID",
		})
	}

	// Check for minimum data
	equipment := model.Equipment
	if len(equipment) == 0 {
		issues = append(issues, building.ValidationIssue{
			Level:   building.ValidationLevelWarning,
			Type:    "no_equipment",
			Field:   "Equipment",
			Message: "No equipment found in building",
		})
	}

	return issues
}

// Enhance adds additional data to the model
func (p *Pipeline) Enhance(ctx context.Context, model *building.BuildingModel) error {
	for _, enhancer := range p.enhancers {
		if err := enhancer.Enhance(ctx, model); err != nil {
			logger.Warn("Enhancer %T failed: %v", enhancer, err)
			// Continue with other enhancers
		}
	}
	return nil
}

// Save persists the model to storage
func (p *Pipeline) Save(ctx context.Context, model *building.BuildingModel, target StorageTarget) error {
	if p.storage == nil {
		return fmt.Errorf("no storage adapter configured")
	}

	switch target {
	case StorageTargetDatabase:
		return p.storage.SaveToDatabase(ctx, model)
	case StorageTargetBIM:
		return p.storage.SaveToBIM(ctx, model)
	case StorageTargetFile:
		return p.storage.SaveToFile(ctx, model)
	default:
		return fmt.Errorf("unknown storage target: %s", target)
	}
}

// Enhancer interface for adding data to models
type Enhancer interface {
	Enhance(ctx context.Context, model *building.BuildingModel) error
}

// StorageAdapter interface for saving models
type StorageAdapter interface {
	SaveToDatabase(ctx context.Context, model *building.BuildingModel) error
	SaveToBIM(ctx context.Context, model *building.BuildingModel) error
	SaveToFile(ctx context.Context, model *building.BuildingModel) error
	LoadFromDatabase(ctx context.Context, buildingID string) (*building.BuildingModel, error)
}

// SpatialEnhancer adds spatial data to the model
type SpatialEnhancer struct {
	// Could connect to PostGIS or other spatial services
}

// Enhance adds spatial enhancements
func (s *SpatialEnhancer) Enhance(ctx context.Context, model *building.BuildingModel) error {
	buildingID := "unknown"
	if model.Building != nil {
		buildingID = model.Building.ArxosID
	}
	logger.Debug("Applying spatial enhancements to building %s", buildingID)

	// Add spatial enhancements to equipment positions
	for _, eq := range model.Equipment {
		if eq.Position != nil {
			// Ensure position confidence is set
			if eq.Confidence == 0 {
				eq.Confidence = 1 // Low confidence for imported data
			}
		}

		// Ensure equipment has building reference
		if model.Building != nil && eq.BuildingID == uuid.Nil {
			eq.BuildingID = model.Building.ID
		}
	}

	// Enhance room data
	for i := range model.Rooms {
		room := &model.Rooms[i]
		if model.Building != nil && room.BuildingID == uuid.Nil {
			room.BuildingID = model.Building.ID
		}
	}

	// Enhance floor data
	for i := range model.Floors {
		floor := &model.Floors[i]
		if model.Building != nil && floor.BuildingID == uuid.Nil {
			floor.BuildingID = model.Building.ID
		}
	}

	return nil
}

// ConfidenceEnhancer updates confidence levels based on data completeness
type ConfidenceEnhancer struct{}

// Enhance updates confidence levels
func (c *ConfidenceEnhancer) Enhance(ctx context.Context, model *building.BuildingModel) error {
	buildingID := "unknown"
	if model.Building != nil {
		buildingID = model.Building.ArxosID
	}
	logger.Debug("Updating confidence levels for building %s", buildingID)

	// Update equipment confidence based on position data
	for _, eq := range model.Equipment {
		if eq.Position != nil && eq.Confidence == 0 {
			// Set default confidence for equipment with positions
			eq.Confidence = 1 // Low confidence for imported data
		}
	}

	// Count data completeness
	totalEquipment := len(model.Equipment)
	equipmentWithPositions := 0
	for _, eq := range model.Equipment {
		if eq.Position != nil {
			equipmentWithPositions++
		}
	}

	if totalEquipment > 0 {
		coverage := float64(equipmentWithPositions) * 100.0 / float64(totalEquipment)
		logger.Debug("Equipment position coverage: %.1f%%", coverage)

		// Store confidence level in building metadata if needed
		if model.Building != nil {
			if model.Building.Metadata == nil {
				model.Building.Metadata = make(map[string]interface{})
			}
			if coverage > 70 {
				model.Building.Metadata["confidence"] = "high"
			} else if coverage > 40 {
				model.Building.Metadata["confidence"] = "medium"
			} else {
				model.Building.Metadata["confidence"] = "low"
			}
			model.Building.Metadata["equipment_coverage"] = coverage
		}
	} else if model.Building != nil {
		if model.Building.Metadata == nil {
			model.Building.Metadata = make(map[string]interface{})
		}
		model.Building.Metadata["confidence"] = "estimated"
	}

	return nil
}
