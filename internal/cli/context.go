package cli

import (
	"context"
	"fmt"
	"io"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/arx-os/arxos/internal/domain/component"
	"github.com/arx-os/arxos/internal/domain/design"
	"github.com/arx-os/arxos/internal/infrastructure/filesystem"
	"github.com/arx-os/arxos/internal/usecase"
)

// ServiceContext provides access to services for CLI commands
type ServiceContext struct {
	container *app.Container
}

// NewServiceContext creates a new service context
func NewServiceContext(container *app.Container) *ServiceContext {
	return &ServiceContext{
		container: container,
	}
}

// GetRepositoryService returns the repository service
func (sc *ServiceContext) GetRepositoryService() building.RepositoryService {
	// Return a service that wraps the use cases
	return &RepositoryServiceImpl{
		repositoryUC: sc.container.GetRepositoryUseCase(),
		ifcUC:        sc.container.GetIFCUseCase(),
		versionUC:    sc.container.GetVersionUseCase(),
		filesystem:   sc.container.GetFilesystemService(),
	}
}

// GetComponentService returns the component service
func (sc *ServiceContext) GetComponentService() component.ComponentService {
	return sc.container.GetComponentUseCase()
}

// GetDesignService returns the design service
func (sc *ServiceContext) GetDesignService() design.DesignInterface {
	return sc.container.GetDesignUseCase()
}

// RepositoryServiceImpl implements building.RepositoryService interface
type RepositoryServiceImpl struct {
	repositoryUC *usecase.RepositoryUseCase
	ifcUC        *usecase.IFCUseCase
	versionUC    *usecase.VersionUseCase
	filesystem   *filesystem.RepositoryFilesystemService
}

// CreateRepository creates a new building repository
func (s *RepositoryServiceImpl) CreateRepository(ctx context.Context, req building.CreateRepositoryRequest) (*building.BuildingRepository, error) {
	// Create repository in database
	repo, err := s.repositoryUC.CreateRepository(ctx, &req)
	if err != nil {
		return nil, err
	}

	// Create filesystem structure
	if err := s.filesystem.CreateRepositoryStructure(ctx, repo); err != nil {
		return nil, fmt.Errorf("failed to create repository structure: %w", err)
	}

	return repo, nil
}

// GetRepository retrieves a repository by ID
func (s *RepositoryServiceImpl) GetRepository(ctx context.Context, id string) (*building.BuildingRepository, error) {
	return s.repositoryUC.GetRepository(ctx, id)
}

// UpdateRepository updates an existing repository
func (s *RepositoryServiceImpl) UpdateRepository(ctx context.Context, id string, req building.UpdateRepositoryRequest) error {
	return s.repositoryUC.UpdateRepository(ctx, id, &req)
}

// DeleteRepository deletes a repository
func (s *RepositoryServiceImpl) DeleteRepository(ctx context.Context, id string) error {
	return s.repositoryUC.DeleteRepository(ctx, id)
}

// ListRepositories lists all repositories
func (s *RepositoryServiceImpl) ListRepositories(ctx context.Context) ([]*building.BuildingRepository, error) {
	return s.repositoryUC.ListRepositories(ctx)
}

// ImportIFC imports IFC data into a repository
func (s *RepositoryServiceImpl) ImportIFC(ctx context.Context, repoID string, ifcData io.Reader) (*building.IFCImportResult, error) {
	// TODO: Convert io.Reader to []byte
	data, err := io.ReadAll(ifcData)
	if err != nil {
		return nil, err
	}
	return s.ifcUC.ImportIFC(ctx, repoID, data)
}

// ValidateRepository validates a repository
func (s *RepositoryServiceImpl) ValidateRepository(ctx context.Context, repoID string) (*building.ValidationResult, error) {
	return s.repositoryUC.ValidateRepository(ctx, repoID)
}

// CreateVersion creates a new version snapshot
func (s *RepositoryServiceImpl) CreateVersion(ctx context.Context, repoID string, message string) (*building.Version, error) {
	return s.versionUC.CreateVersion(ctx, repoID, message)
}

// GetVersion retrieves a version by ID
func (s *RepositoryServiceImpl) GetVersion(ctx context.Context, repoID string, version string) (*building.Version, error) {
	return s.versionUC.GetVersion(ctx, repoID, version)
}

// ListVersions lists all versions for a repository
func (s *RepositoryServiceImpl) ListVersions(ctx context.Context, repoID string) ([]building.Version, error) {
	return s.versionUC.ListVersions(ctx, repoID)
}

// CompareVersions compares two versions
func (s *RepositoryServiceImpl) CompareVersions(ctx context.Context, repoID string, v1, v2 string) (*building.VersionDiff, error) {
	return s.versionUC.CompareVersions(ctx, repoID, v1, v2)
}

// RollbackVersion rolls back to a specific version
func (s *RepositoryServiceImpl) RollbackVersion(ctx context.Context, repoID string, version string) error {
	return s.versionUC.RollbackVersion(ctx, repoID, version)
}
