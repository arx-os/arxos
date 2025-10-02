package usecase

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/arx-os/arxos/internal/infrastructure/ifc"
)

// IFCUseCase implements IFC import and validation business logic
type IFCUseCase struct {
	repoRepo  building.RepositoryRepository
	ifcRepo   building.IFCRepository
	validator building.RepositoryValidator
	parser    *ifc.IFCParser
	logger    domain.Logger
}

// NewIFCUseCase creates a new IFCUseCase
func NewIFCUseCase(
	repoRepo building.RepositoryRepository,
	ifcRepo building.IFCRepository,
	validator building.RepositoryValidator,
	logger domain.Logger,
) *IFCUseCase {
	return &IFCUseCase{
		repoRepo:  repoRepo,
		ifcRepo:   ifcRepo,
		validator: validator,
		parser:    ifc.NewIFCParser(),
		logger:    logger,
	}
}

// ImportIFC imports IFC data into a repository
func (uc *IFCUseCase) ImportIFC(ctx context.Context, repoID string, ifcData []byte) (*building.IFCImportResult, error) {
	uc.logger.Info("Importing IFC data", "repository_id", repoID, "size", len(ifcData))

	// Validate repository exists
	repo, err := uc.repoRepo.GetByID(ctx, repoID)
	if err != nil {
		uc.logger.Error("Failed to get repository for IFC import", "error", err)
		return nil, fmt.Errorf("failed to get repository: %w", err)
	}

	// Create IFC file record
	ifcFile := &building.IFCFile{
		ID:         uc.generateIFCFileID(),
		Name:       fmt.Sprintf("import-%d.ifc", time.Now().Unix()),
		Path:       fmt.Sprintf("data/ifc/import-%d.ifc", time.Now().Unix()),
		Version:    "4.0",           // TODO: Detect IFC version from data
		Discipline: "architectural", // TODO: Detect discipline from data
		Size:       int64(len(ifcData)),
		Entities:   0, // TODO: Count entities after parsing
		Validated:  false,
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	// Parse IFC data using the parser
	ifcBuilding, err := uc.parser.ParseIFC(strings.NewReader(string(ifcData)))
	if err != nil {
		uc.logger.Error("Failed to parse IFC file", "error", err)
		return nil, fmt.Errorf("failed to parse IFC file: %w", err)
	}

	// Update IFC file record with parsed data
	ifcFile.Entities = len(ifcBuilding.Entities)
	ifcFile.Validated = true

	// Create import result with actual parsed data
	result := &building.IFCImportResult{
		Success:         true,
		RepositoryID:    repoID,
		IFCFileID:       ifcFile.ID,
		Entities:        len(ifcBuilding.Entities),
		Properties:      len(ifcBuilding.Properties),
		Materials:       len(ifcBuilding.Materials),
		Classifications: len(ifcBuilding.Classifications),
		Warnings:        []string{}, // No warnings for now
		Errors:          []string{},
		CreatedAt:       time.Now(),
	}

	// Save IFC file record
	if err := uc.ifcRepo.Create(ctx, ifcFile); err != nil {
		uc.logger.Error("Failed to save IFC file record", "error", err)
		return nil, fmt.Errorf("failed to save IFC file: %w", err)
	}

	// Update repository structure
	repo.Structure.IFCFiles = append(repo.Structure.IFCFiles, *ifcFile)
	repo.UpdatedAt = time.Now()

	if err := uc.repoRepo.Update(ctx, repo); err != nil {
		uc.logger.Error("Failed to update repository with IFC file", "error", err)
		return nil, fmt.Errorf("failed to update repository: %w", err)
	}

	uc.logger.Info("IFC import completed", "repository_id", repoID, "ifc_file_id", ifcFile.ID)
	return result, nil
}

// ValidateIFC validates IFC data against buildingSMART standards
func (uc *IFCUseCase) ValidateIFC(ctx context.Context, ifcFileID string) (*building.IFCValidationResult, error) {
	uc.logger.Info("Validating IFC file", "ifc_file_id", ifcFileID)

	// Get IFC file
	ifcFile, err := uc.ifcRepo.GetByID(ctx, ifcFileID)
	if err != nil {
		uc.logger.Error("Failed to get IFC file for validation", "error", err)
		return nil, fmt.Errorf("failed to get IFC file: %w", err)
	}

	// TODO: Implement actual IFC validation
	// This would typically involve:
	// 1. Schema validation against IFC schema
	// 2. buildingSMART compliance checking
	// 3. Spatial validation
	// 4. Data integrity checks

	// For now, create a placeholder result
	result := &building.IFCValidationResult{
		Valid:   true,
		Version: ifcFile.Version,
		Compliance: building.ComplianceResult{
			Passed:    true,
			Score:     100,
			Tests:     []building.TestResult{},
			CreatedAt: time.Now(),
		},
		Schema: building.SchemaResult{
			Passed:    true,
			Version:   ifcFile.Version,
			Errors:    []string{},
			CreatedAt: time.Now(),
		},
		Spatial: building.SpatialResult{
			Passed:    true,
			Accuracy:  100.0,
			Coverage:  100.0,
			Errors:    []string{},
			CreatedAt: time.Now(),
		},
		Warnings:  []string{"IFC validation not yet implemented"},
		Errors:    []string{},
		CreatedAt: time.Now(),
	}

	// Update IFC file validation status
	ifcFile.Validated = result.Valid
	ifcFile.UpdatedAt = time.Now()

	if err := uc.ifcRepo.Update(ctx, ifcFile); err != nil {
		uc.logger.Error("Failed to update IFC file validation status", "error", err)
		return nil, fmt.Errorf("failed to update IFC file: %w", err)
	}

	uc.logger.Info("IFC validation completed", "ifc_file_id", ifcFileID, "valid", result.Valid)
	return result, nil
}

// Helper methods

func (uc *IFCUseCase) generateIFCFileID() string {
	// TODO: Implement proper ID generation
	return fmt.Sprintf("ifc-%d", time.Now().UnixNano())
}
