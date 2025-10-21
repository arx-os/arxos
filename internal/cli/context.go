package cli

import (
	"context"
	"fmt"
	"io"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/arx-os/arxos/internal/domain/component"
	"github.com/arx-os/arxos/internal/domain/design"
	"github.com/arx-os/arxos/internal/infrastructure/filesystem"
	"github.com/arx-os/arxos/internal/usecase/auth"
	"github.com/arx-os/arxos/internal/usecase/integration"
	"github.com/arx-os/arxos/internal/usecase/versioncontrol"
	buildinguc "github.com/arx-os/arxos/internal/usecase/building"
)

// RepositoryServiceProvider interface for repository services
type RepositoryServiceProvider interface {
	GetRepositoryService() building.RepositoryService
}

// IFCServiceProvider interface for IFC import services
type IFCServiceProvider interface {
	GetIFCService() *integration.IFCUseCase
}

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

// Repository Services
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

// Component Services
// GetComponentService returns the component service
func (sc *ServiceContext) GetComponentService() component.ComponentService {
	return sc.container.GetComponentUseCase()
}

// Design Services
// GetDesignService returns the design service
func (sc *ServiceContext) GetDesignService() design.DesignInterface {
	return sc.container.GetDesignUseCase()
}

// Building Services
// GetBuildingService returns the building service
func (sc *ServiceContext) GetBuildingService() *buildinguc.BuildingUseCase {
	return sc.container.GetBuildingUseCase()
}

// Equipment Services
// GetEquipmentService returns the equipment service
func (sc *ServiceContext) GetEquipmentService() *buildinguc.EquipmentUseCase {
	return sc.container.GetEquipmentUseCase()
}

// User Services
// GetUserService returns the user service
func (sc *ServiceContext) GetUserService() *auth.UserUseCase {
	return sc.container.GetUserUseCase()
}

// Organization Services
// GetOrganizationService returns the organization service
func (sc *ServiceContext) GetOrganizationService() *auth.OrganizationUseCase {
	return sc.container.GetOrganizationUseCase()
}

// IFC Services
// GetIFCService returns the IFC service
func (sc *ServiceContext) GetIFCService() *integration.IFCUseCase {
	return sc.container.GetIFCUseCase()
}

// Version Services
// GetVersionService returns the version service
func (sc *ServiceContext) GetVersionService() *versioncontrol.VersionUseCase {
	return sc.container.GetVersionUseCase()
}

// Infrastructure Services
// GetDatabaseService returns the database service
func (sc *ServiceContext) GetDatabaseService() domain.Database {
	return sc.container.GetDatabase()
}

// GetCacheService returns the cache service
func (sc *ServiceContext) GetCacheService() domain.Cache {
	return sc.container.GetCache()
}

// GetLoggerService returns the logger service
func (sc *ServiceContext) GetLoggerService() domain.Logger {
	return sc.container.GetLogger()
}

// GetFilesystemService returns the filesystem service
func (sc *ServiceContext) GetFilesystemService() *filesystem.RepositoryFilesystemService {
	return sc.container.GetFilesystemService()
}

// Health Services
// GetHealthService returns a health check service
func (sc *ServiceContext) GetHealthService() *HealthServiceImpl {
	return &HealthServiceImpl{
		database: sc.container.GetDatabase(),
		cache:    sc.container.GetCache(),
		logger:   sc.container.GetLogger(),
	}
}

// RepositoryServiceImpl implements building.RepositoryService interface
type RepositoryServiceImpl struct {
	repositoryUC *versioncontrol.RepositoryUseCase
	ifcUC        *integration.IFCUseCase
	versionUC    *versioncontrol.VersionUseCase
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
	// Convert io.Reader to []byte for IFC use case
	data, err := io.ReadAll(ifcData)
	if err != nil {
		return nil, fmt.Errorf("failed to read IFC data: %w", err)
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

// HealthServiceImpl implements health check functionality
type HealthServiceImpl struct {
	database domain.Database
	cache    domain.Cache
	logger   domain.Logger
}

// CheckHealth performs comprehensive health checks
func (h *HealthServiceImpl) CheckHealth(ctx context.Context) (*HealthStatus, error) {
	status := &HealthStatus{
		Overall: "healthy",
		Checks:  make(map[string]string),
	}

	// Check database connectivity
	if h.database != nil {
		if err := h.database.Ping(); err != nil {
			status.Checks["database"] = "unhealthy"
			status.Overall = "unhealthy"
			h.logger.Error("Database health check failed", "error", err)
		} else {
			status.Checks["database"] = "healthy"
		}
	} else {
		status.Checks["database"] = "not_configured"
	}

	// Check cache connectivity
	if h.cache != nil {
		// Test cache with a simple operation
		testKey := "health_check_test"
		if err := h.cache.Set(ctx, testKey, "test", 1); err != nil {
			status.Checks["cache"] = "unhealthy"
			status.Overall = "unhealthy"
			h.logger.Error("Cache health check failed", "error", err)
		} else {
			// Clean up test key
			h.cache.Delete(ctx, testKey)
			status.Checks["cache"] = "healthy"
		}
	} else {
		status.Checks["cache"] = "not_configured"
	}

	return status, nil
}

// HealthStatus represents the health status of system components
type HealthStatus struct {
	Overall string            `json:"overall"`
	Checks  map[string]string `json:"checks"`
}
