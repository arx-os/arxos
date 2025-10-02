package building

import (
	"context"
	"io"
)

// RepositoryService defines the contract for building repository management
// This implements the core service interface from BUILDING_REPOSITORY_DESIGN.md
type RepositoryService interface {
	// Repository management
	CreateRepository(ctx context.Context, req CreateRepositoryRequest) (*BuildingRepository, error)
	GetRepository(ctx context.Context, id string) (*BuildingRepository, error)
	UpdateRepository(ctx context.Context, id string, req UpdateRepositoryRequest) error
	DeleteRepository(ctx context.Context, id string) error
	ListRepositories(ctx context.Context) ([]*BuildingRepository, error)

	// IFC import (PRIMARY FORMAT)
	ImportIFC(ctx context.Context, repoID string, ifcData io.Reader) (*IFCImportResult, error)

	// Repository validation
	ValidateRepository(ctx context.Context, repoID string) (*ValidationResult, error)

	// Version control
	CreateVersion(ctx context.Context, repoID string, message string) (*Version, error)
	GetVersion(ctx context.Context, repoID string, version string) (*Version, error)
	ListVersions(ctx context.Context, repoID string) ([]Version, error)
	CompareVersions(ctx context.Context, repoID string, v1, v2 string) (*VersionDiff, error)
	RollbackVersion(ctx context.Context, repoID string, version string) error
}

// CreateRepositoryRequest represents a request to create a new repository
type CreateRepositoryRequest struct {
	Name        string       `json:"name" validate:"required"`
	Type        BuildingType `json:"type" validate:"required"`
	Floors      int          `json:"floors" validate:"required,min=1"`
	Description string       `json:"description,omitempty"`
	Template    string       `json:"template,omitempty"`
	Author      string       `json:"author" validate:"required"`
}

// UpdateRepositoryRequest represents a request to update a repository
type UpdateRepositoryRequest struct {
	Name        *string       `json:"name,omitempty"`
	Type        *BuildingType `json:"type,omitempty"`
	Floors      *int          `json:"floors,omitempty"`
	Description *string       `json:"description,omitempty"`
}

// RepositoryRepository defines the contract for repository data access
type RepositoryRepository interface {
	Create(ctx context.Context, repo *BuildingRepository) error
	GetByID(ctx context.Context, id string) (*BuildingRepository, error)
	GetByName(ctx context.Context, name string) (*BuildingRepository, error)
	List(ctx context.Context) ([]*BuildingRepository, error)
	Update(ctx context.Context, repo *BuildingRepository) error
	Delete(ctx context.Context, id string) error
}

// VersionRepository defines the contract for version data access
type VersionRepository interface {
	Create(ctx context.Context, version *Version) error
	GetByID(ctx context.Context, id string) (*Version, error)
	GetByRepositoryAndTag(ctx context.Context, repoID, tag string) (*Version, error)
	ListByRepository(ctx context.Context, repoID string) ([]Version, error)
	GetLatest(ctx context.Context, repoID string) (*Version, error)
	Update(ctx context.Context, version *Version) error
	Delete(ctx context.Context, id string) error
}

// IFCRepository defines the contract for IFC data access
type IFCRepository interface {
	Create(ctx context.Context, ifcFile *IFCFile) error
	GetByID(ctx context.Context, id string) (*IFCFile, error)
	GetByRepository(ctx context.Context, repoID string) ([]IFCFile, error)
	Update(ctx context.Context, ifcFile *IFCFile) error
	Delete(ctx context.Context, id string) error
}
