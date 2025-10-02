package usecase

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/arx-os/arxos/internal/infrastructure/ifc"
)

// IFCUseCase implements IFC import and validation business logic using IfcOpenShell service
type IFCUseCase struct {
	repoRepo   building.RepositoryRepository
	ifcRepo    building.IFCRepository
	validator  building.RepositoryValidator
	ifcService *ifc.EnhancedIFCService
	logger     domain.Logger
}

// NewIFCUseCase creates a new IFCUseCase
func NewIFCUseCase(
	repoRepo building.RepositoryRepository,
	ifcRepo building.IFCRepository,
	validator building.RepositoryValidator,
	ifcService *ifc.EnhancedIFCService,
	logger domain.Logger,
) *IFCUseCase {
	return &IFCUseCase{
		repoRepo:   repoRepo,
		ifcRepo:    ifcRepo,
		validator:  validator,
		ifcService: ifcService,
		logger:     logger,
	}
}

// ImportIFC imports IFC data into a repository using IfcOpenShell service
func (uc *IFCUseCase) ImportIFC(ctx context.Context, repoID string, ifcData []byte) (*building.IFCImportResult, error) {
	uc.logger.Info("Importing IFC data", "repository_id", repoID, "size", len(ifcData))

	// Validate repository exists
	repo, err := uc.repoRepo.GetByID(ctx, repoID)
	if err != nil {
		uc.logger.Error("Failed to get repository for IFC import", "error", err)
		return nil, fmt.Errorf("failed to get repository: %w", err)
	}

	// Parse IFC data using IfcOpenShell service
	parseResult, err := uc.ifcService.ParseIFC(ctx, ifcData)
	if err != nil {
		uc.logger.Error("Failed to parse IFC file", "error", err)
		return nil, fmt.Errorf("failed to parse IFC file: %w", err)
	}

	// Create IFC file record with parsed data
	ifcFile := &building.IFCFile{
		ID:         uc.generateIFCFileID(),
		Name:       fmt.Sprintf("import-%d.ifc", time.Now().Unix()),
		Path:       fmt.Sprintf("data/ifc/import-%d.ifc", time.Now().Unix()),
		Version:    parseResult.Metadata.IFCVersion,
		Discipline: "architectural", // TODO: Detect discipline from data
		Size:       int64(len(ifcData)),
		Entities:   parseResult.TotalEntities,
		Validated:  true,
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	// Create import result with actual parsed data
	result := &building.IFCImportResult{
		Success:         true,
		RepositoryID:    repoID,
		IFCFileID:       ifcFile.ID,
		Entities:        parseResult.TotalEntities,
		Properties:      0,          // TODO: Extract from parse result
		Materials:       0,          // TODO: Extract from parse result
		Classifications: 0,          // TODO: Extract from parse result
		Warnings:        []string{}, // TODO: Extract warnings from parse result
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

	uc.logger.Info("IFC import completed",
		"repository_id", repoID,
		"ifc_file_id", ifcFile.ID,
		"entities", parseResult.TotalEntities,
		"buildings", parseResult.Buildings,
		"spaces", parseResult.Spaces,
		"equipment", parseResult.Equipment)

	return result, nil
}

// ValidateIFC validates IFC data against buildingSMART standards using IfcOpenShell service
func (uc *IFCUseCase) ValidateIFC(ctx context.Context, ifcFileID string) (*building.IFCValidationResult, error) {
	uc.logger.Info("Validating IFC file", "ifc_file_id", ifcFileID)

	// Get IFC file
	ifcFile, err := uc.ifcRepo.GetByID(ctx, ifcFileID)
	if err != nil {
		uc.logger.Error("Failed to get IFC file for validation", "error", err)
		return nil, fmt.Errorf("failed to get IFC file: %w", err)
	}

	// Read IFC file data (assuming it's stored in the repository)
	// TODO: Implement actual file reading from repository
	ifcData := []byte{} // Placeholder - would read actual file data

	// Validate IFC data using IfcOpenShell service
	validationResult, err := uc.ifcService.ValidateIFC(ctx, ifcData)
	if err != nil {
		uc.logger.Error("Failed to validate IFC file", "error", err)
		return nil, fmt.Errorf("failed to validate IFC file: %w", err)
	}

	// Create validation result
	result := &building.IFCValidationResult{
		Valid:   validationResult.Valid,
		Version: ifcFile.Version,
		Compliance: building.ComplianceResult{
			Passed:    validationResult.Compliance.BuildingSMART,
			Score:     uc.calculateComplianceScore(validationResult),
			Tests:     []building.TestResult{}, // TODO: Convert validation results to test results
			CreatedAt: time.Now(),
		},
		Schema: building.SchemaResult{
			Passed:    validationResult.Compliance.IFC4,
			Version:   ifcFile.Version,
			Errors:    validationResult.Errors,
			CreatedAt: time.Now(),
		},
		Spatial: building.SpatialResult{
			Passed:    validationResult.Compliance.SpatialConsistency,
			Accuracy:  100.0,      // TODO: Calculate from validation results
			Coverage:  100.0,      // TODO: Calculate from validation results
			Errors:    []string{}, // TODO: Extract spatial errors
			CreatedAt: time.Now(),
		},
		Warnings:  validationResult.Warnings,
		Errors:    validationResult.Errors,
		CreatedAt: time.Now(),
	}

	// Update IFC file validation status
	ifcFile.Validated = result.Valid
	ifcFile.UpdatedAt = time.Now()

	if err := uc.ifcRepo.Update(ctx, ifcFile); err != nil {
		uc.logger.Error("Failed to update IFC file validation status", "error", err)
		return nil, fmt.Errorf("failed to update IFC file: %w", err)
	}

	uc.logger.Info("IFC validation completed",
		"ifc_file_id", ifcFileID,
		"valid", result.Valid,
		"warnings", len(result.Warnings),
		"errors", len(result.Errors))

	return result, nil
}

// GetServiceStatus returns the status of the IfcOpenShell service
func (uc *IFCUseCase) GetServiceStatus(ctx context.Context) map[string]interface{} {
	return uc.ifcService.GetServiceStatus(ctx)
}

// Helper methods

func (uc *IFCUseCase) generateIFCFileID() string {
	return fmt.Sprintf("ifc-%d", time.Now().UnixNano())
}

func (uc *IFCUseCase) calculateComplianceScore(validationResult *ifc.ValidationResult) int {
	score := 100

	// Deduct points for errors
	score -= len(validationResult.Errors) * 10

	// Deduct points for warnings
	score -= len(validationResult.Warnings) * 2

	// Ensure score doesn't go below 0
	if score < 0 {
		score = 0
	}

	return score
}
