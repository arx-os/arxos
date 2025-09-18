package importer

import (
	"context"
	"fmt"
	"io"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/models/building"
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
	model.ImportedAt = time.Now()
	model.UpdatedAt = time.Now()
	if model.Source == "" {
		model.Source = building.DataSource(importer.GetFormat())
	}

	// Apply building ID and name from options
	if opts.BuildingID != "" {
		model.ID = opts.BuildingID
	}
	if opts.BuildingName != "" {
		model.Name = opts.BuildingName
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

	// Calculate coverage
	model.Coverage = model.CalculateCoverage()

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
	logger.Info("Building: %s, Floors: %d, Equipment: %d, Coverage: %.1f%%",
		model.Name, len(model.Floors), len(model.GetAllEquipment()), model.Coverage)

	return model, nil
}

// Validate checks the model for issues
func (p *Pipeline) Validate(model *building.BuildingModel) []building.ValidationIssue {
	// Use the model's built-in validation
	issues := model.Validate()

	// Add pipeline-specific validation
	if model.ID == "" && model.UUID == "" {
		issues = append(issues, building.ValidationIssue{
			Level:   "error",
			Field:   "ID/UUID",
			Message: "Building must have either ID or UUID",
		})
	}

	// Check for minimum data
	equipment := model.GetAllEquipment()
	if len(equipment) == 0 {
		issues = append(issues, building.ValidationIssue{
			Level:   "warning",
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
	logger.Debug("Applying spatial enhancements to building %s", model.ID)

	// Calculate bounding box if not present
	if model.BoundingBox == nil && len(model.Floors) > 0 {
		// Calculate from floor bounding boxes
		var minX, minY, minZ, maxX, maxY, maxZ float64
		first := true

		for _, floor := range model.Floors {
			if floor.BoundingBox != nil {
				if first {
					minX = floor.BoundingBox.Min.X
					minY = floor.BoundingBox.Min.Y
					minZ = floor.BoundingBox.Min.Z
					maxX = floor.BoundingBox.Max.X
					maxY = floor.BoundingBox.Max.Y
					maxZ = floor.BoundingBox.Max.Z
					first = false
				} else {
					if floor.BoundingBox.Min.X < minX {
						minX = floor.BoundingBox.Min.X
					}
					if floor.BoundingBox.Min.Y < minY {
						minY = floor.BoundingBox.Min.Y
					}
					if floor.BoundingBox.Min.Z < minZ {
						minZ = floor.BoundingBox.Min.Z
					}
					if floor.BoundingBox.Max.X > maxX {
						maxX = floor.BoundingBox.Max.X
					}
					if floor.BoundingBox.Max.Y > maxY {
						maxY = floor.BoundingBox.Max.Y
					}
					if floor.BoundingBox.Max.Z > maxZ {
						maxZ = floor.BoundingBox.Max.Z
					}
				}
			}
		}

		if !first {
			model.BoundingBox = &building.BoundingBox{
				Min: building.Point3D{X: minX, Y: minY, Z: minZ},
				Max: building.Point3D{X: maxX, Y: maxY, Z: maxZ},
			}
		}
	}

	// Add equipment positions if missing
	for i := range model.Floors {
		floor := &model.Floors[i]
		for j := range floor.Equipment {
			equipment := &floor.Equipment[j]
			if equipment.Position == nil {
				// Try to derive from room position
				if equipment.RoomID != "" {
					for _, room := range floor.Rooms {
						if room.ID == equipment.RoomID && room.Position != nil {
							equipment.Position = room.Position
							equipment.Confidence = building.ConfidenceEstimated
							break
						}
					}
				}
			}
		}
	}

	return nil
}

// ConfidenceEnhancer updates confidence levels based on data completeness
type ConfidenceEnhancer struct{}

// Enhance updates confidence levels
func (c *ConfidenceEnhancer) Enhance(ctx context.Context, model *building.BuildingModel) error {
	logger.Debug("Updating confidence levels for building %s", model.ID)

	// Update model confidence based on completeness
	coverage := model.CalculateCoverage()
	if coverage > 80 {
		model.Confidence = building.ConfidenceHigh
	} else if coverage > 60 {
		model.Confidence = building.ConfidenceMedium
	} else if coverage > 40 {
		model.Confidence = building.ConfidenceLow
	} else {
		model.Confidence = building.ConfidenceEstimated
	}

	return nil
}
