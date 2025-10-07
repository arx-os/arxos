package building

import (
	"context"
	"time"
)

// RepositoryValidator defines the contract for repository validation
type RepositoryValidator interface {
	ValidateRepository(ctx context.Context, repo *BuildingRepository) (*ValidationResult, error)
	ValidateStructure(ctx context.Context, structure *RepositoryStructure) (*ValidationResult, error)
	ValidateIFC(ctx context.Context, ifcFile *IFCFile) (*IFCValidationResult, error)
}

// ValidationResult represents the result of repository validation
type ValidationResult struct {
	Valid     bool          `json:"valid"`
	Score     int           `json:"score"` // 0-100
	Checks    []CheckResult `json:"checks"`
	Warnings  []string      `json:"warnings"`
	Errors    []string      `json:"errors"`
	CreatedAt time.Time     `json:"created_at"`
}

// CheckResult represents a single validation check
type CheckResult struct {
	Name      string    `json:"name"`
	Passed    bool      `json:"passed"`
	Message   string    `json:"message"`
	Severity  Severity  `json:"severity"`
	CreatedAt time.Time `json:"created_at"`
}

// Severity represents the severity of a validation issue
type Severity string

const (
	SeverityInfo     Severity = "info"
	SeverityWarning  Severity = "warning"
	SeverityError    Severity = "error"
	SeverityCritical Severity = "critical"
)

// ValidationRequest represents a request to validate a repository
type ValidationRequest struct {
	RepositoryID string            `json:"repository_id" validate:"required"`
	Options      ValidationOptions `json:"options"`
}

// ValidationOptions represents options for validation
type ValidationOptions struct {
	CheckStructure     bool `json:"check_structure"`
	CheckIFCCompliance bool `json:"check_ifc_compliance"`
	CheckDataIntegrity bool `json:"check_data_integrity"`
	CheckSpatial       bool `json:"check_spatial"`
	StrictMode         bool `json:"strict_mode"`
}

// RepositoryValidationRules defines validation rules for repositories
type RepositoryValidationRules struct {
	RequiredDirectories []string `json:"required_directories"`
	RequiredFiles       []string `json:"required_files"`
	MaxFileSize         int64    `json:"max_file_size"`
	AllowedFormats      []string `json:"allowed_formats"`
	MaxEntities         int      `json:"max_entities"`
}

// DefaultValidationRules returns default validation rules
func DefaultValidationRules() *RepositoryValidationRules {
	return &RepositoryValidationRules{
		RequiredDirectories: []string{
			".arxos",
			"data",
			"data/ifc",
			"data/plans",
			"data/equipment",
			"data/spatial",
			"operations",
			"operations/maintenance",
			"operations/energy",
			"operations/occupancy",
			"integrations",
			"documentation",
			"versions",
		},
		RequiredFiles: []string{
			".arxos/config.yaml",
			"documentation/README.md",
		},
		MaxFileSize:    500 * 1024 * 1024, // 500MB
		AllowedFormats: []string{"ifc", "csv", "json", "yaml"},
		MaxEntities:    1000000,
	}
}
