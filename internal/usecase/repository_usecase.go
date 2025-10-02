package usecase

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/google/uuid"
)

// RepositoryUseCase implements the building repository business logic
// This is the main use case for the "Git of Buildings" concept
type RepositoryUseCase struct {
	repoRepo    building.RepositoryRepository
	versionRepo building.VersionRepository
	ifcRepo     building.IFCRepository
	validator   building.RepositoryValidator
	logger      domain.Logger
}

// NewRepositoryUseCase creates a new RepositoryUseCase
func NewRepositoryUseCase(
	repoRepo building.RepositoryRepository,
	versionRepo building.VersionRepository,
	ifcRepo building.IFCRepository,
	validator building.RepositoryValidator,
	logger domain.Logger,
) *RepositoryUseCase {
	return &RepositoryUseCase{
		repoRepo:    repoRepo,
		versionRepo: versionRepo,
		ifcRepo:     ifcRepo,
		validator:   validator,
		logger:      logger,
	}
}

// CreateRepository creates a new building repository
func (uc *RepositoryUseCase) CreateRepository(ctx context.Context, req *building.CreateRepositoryRequest) (*building.BuildingRepository, error) {
	uc.logger.Info("Creating building repository", "name", req.Name)

	// Validate business rules
	if err := uc.validateCreateRepository(req); err != nil {
		uc.logger.Error("Repository validation failed", "error", err)
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// Generate repository ID
	repoID := uc.generateRepositoryID()

	// Create repository entity
	repo := &building.BuildingRepository{
		ID:        repoID,
		Name:      req.Name,
		Type:      req.Type,
		Floors:    req.Floors,
		Structure: building.RepositoryStructure{}, // Will be populated by filesystem service
		Versions:  []building.Version{},
		Current:   nil,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	// Save to repository
	if err := uc.repoRepo.Create(ctx, repo); err != nil {
		uc.logger.Error("Failed to create repository", "error", err)
		return nil, fmt.Errorf("failed to create repository: %w", err)
	}

	// Create initial version
	initialVersion := &building.Version{
		ID:           uc.generateVersionID(),
		RepositoryID: repoID,
		Tag:          "v1.0.0",
		Message:      "Initial repository creation",
		Author:       req.Author,
		Hash:         uc.generateHash(),
		Parent:       "",
		Changes:      []building.Change{},
		CreatedAt:    time.Now(),
	}

	if err := uc.versionRepo.Create(ctx, initialVersion); err != nil {
		uc.logger.Error("Failed to create initial version", "error", err)
		return nil, fmt.Errorf("failed to create initial version: %w", err)
	}

	// Update repository with current version
	repo.Current = initialVersion
	repo.Versions = []building.Version{*initialVersion}

	if err := uc.repoRepo.Update(ctx, repo); err != nil {
		uc.logger.Error("Failed to update repository with initial version", "error", err)
		return nil, fmt.Errorf("failed to update repository: %w", err)
	}

	uc.logger.Info("Repository created successfully", "repository_id", repo.ID)
	return repo, nil
}

// GetRepository retrieves a repository by ID
func (uc *RepositoryUseCase) GetRepository(ctx context.Context, id string) (*building.BuildingRepository, error) {
	uc.logger.Info("Getting repository", "id", id)

	repo, err := uc.repoRepo.GetByID(ctx, id)
	if err != nil {
		uc.logger.Error("Failed to get repository", "error", err)
		return nil, fmt.Errorf("failed to get repository: %w", err)
	}

	// Load versions
	versions, err := uc.versionRepo.ListByRepository(ctx, id)
	if err != nil {
		uc.logger.Error("Failed to get repository versions", "error", err)
		return nil, fmt.Errorf("failed to get repository versions: %w", err)
	}

	repo.Versions = versions

	// Set current version
	if len(versions) > 0 {
		latest, err := uc.versionRepo.GetLatest(ctx, id)
		if err != nil {
			uc.logger.Error("Failed to get latest version", "error", err)
			return nil, fmt.Errorf("failed to get latest version: %w", err)
		}
		repo.Current = latest
	}

	return repo, nil
}

// UpdateRepository updates an existing repository
func (uc *RepositoryUseCase) UpdateRepository(ctx context.Context, id string, req *building.UpdateRepositoryRequest) error {
	uc.logger.Info("Updating repository", "id", id)

	// Get existing repository
	repo, err := uc.repoRepo.GetByID(ctx, id)
	if err != nil {
		uc.logger.Error("Failed to get repository for update", "error", err)
		return fmt.Errorf("failed to get repository: %w", err)
	}

	// Apply updates
	if req.Name != nil {
		repo.Name = *req.Name
	}
	if req.Type != nil {
		repo.Type = *req.Type
	}
	if req.Floors != nil {
		repo.Floors = *req.Floors
	}

	repo.UpdatedAt = time.Now()

	// Save updated repository
	if err := uc.repoRepo.Update(ctx, repo); err != nil {
		uc.logger.Error("Failed to update repository", "error", err)
		return fmt.Errorf("failed to update repository: %w", err)
	}

	uc.logger.Info("Repository updated successfully", "repository_id", repo.ID)
	return nil
}

// DeleteRepository deletes a repository
func (uc *RepositoryUseCase) DeleteRepository(ctx context.Context, id string) error {
	uc.logger.Info("Deleting repository", "id", id)

	// TODO: Implement cascade deletion of versions and IFC files
	// This would typically involve:
	// 1. Delete all versions
	// 2. Delete all IFC files
	// 3. Delete repository files from filesystem
	// 4. Delete repository record

	if err := uc.repoRepo.Delete(ctx, id); err != nil {
		uc.logger.Error("Failed to delete repository", "error", err)
		return fmt.Errorf("failed to delete repository: %w", err)
	}

	uc.logger.Info("Repository deleted successfully", "repository_id", id)
	return nil
}

// ListRepositories lists all repositories
func (uc *RepositoryUseCase) ListRepositories(ctx context.Context) ([]*building.BuildingRepository, error) {
	uc.logger.Info("Listing repositories")

	repos, err := uc.repoRepo.List(ctx)
	if err != nil {
		uc.logger.Error("Failed to list repositories", "error", err)
		return nil, fmt.Errorf("failed to list repositories: %w", err)
	}

	uc.logger.Info("Repositories listed successfully", "count", len(repos))
	return repos, nil
}

// ValidateRepository validates a repository
func (uc *RepositoryUseCase) ValidateRepository(ctx context.Context, repoID string) (*building.ValidationResult, error) {
	uc.logger.Info("Validating repository", "repository_id", repoID)

	// Get repository
	repo, err := uc.repoRepo.GetByID(ctx, repoID)
	if err != nil {
		uc.logger.Error("Failed to get repository for validation", "error", err)
		return nil, fmt.Errorf("failed to get repository: %w", err)
	}

	// Validate repository
	result, err := uc.validator.ValidateRepository(ctx, repo)
	if err != nil {
		uc.logger.Error("Repository validation failed", "error", err)
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	uc.logger.Info("Repository validation completed", "repository_id", repoID, "valid", result.Valid)
	return result, nil
}

// Helper methods

func (uc *RepositoryUseCase) validateCreateRepository(req *building.CreateRepositoryRequest) error {
	if req.Name == "" {
		return fmt.Errorf("repository name is required")
	}
	if req.Type == "" {
		return fmt.Errorf("repository type is required")
	}
	if req.Floors < 1 {
		return fmt.Errorf("repository must have at least 1 floor")
	}
	if req.Author == "" {
		return fmt.Errorf("author is required")
	}
	return nil
}

func (uc *RepositoryUseCase) generateRepositoryID() string {
	return uuid.New().String()
}

func (uc *RepositoryUseCase) generateVersionID() string {
	return uuid.New().String()
}

func (uc *RepositoryUseCase) generateHash() string {
	// TODO: Implement proper hash generation
	return fmt.Sprintf("hash-%d", time.Now().UnixNano())
}
