package filesystem

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/arx-os/arxos/internal/domain/building"
)

// RepositoryFilesystemService manages building repository filesystem operations
type RepositoryFilesystemService struct {
	basePath string
}

// NewRepositoryFilesystemService creates a new filesystem service
func NewRepositoryFilesystemService(basePath string) *RepositoryFilesystemService {
	return &RepositoryFilesystemService{
		basePath: basePath,
	}
}

// CreateRepositoryStructure creates the standardized directory structure for a building repository
func (s *RepositoryFilesystemService) CreateRepositoryStructure(ctx context.Context, repo *building.BuildingRepository) error {
	repoPath := filepath.Join(s.basePath, repo.Name)

	// Create main directories following BUILDING_REPOSITORY_DESIGN.md structure
	directories := []string{
		".arxos",
		".arxos/hooks",
		".arxos/templates",
		"data",
		"data/ifc",
		"data/plans",
		"data/equipment",
		"data/spatial",
		"operations",
		"operations/maintenance",
		"operations/maintenance/work-orders",
		"operations/maintenance/inspections",
		"operations/energy",
		"operations/energy/optimization",
		"operations/occupancy",
		"integrations",
		"integrations/bms",
		"integrations/sensors",
		"integrations/apis",
		"documentation",
		"documentation/emergency",
		"versions",
	}

	// Create directories
	for _, dir := range directories {
		fullPath := filepath.Join(repoPath, dir)
		if err := os.MkdirAll(fullPath, 0755); err != nil {
			return fmt.Errorf("failed to create directory %s: %w", dir, err)
		}
	}

	// Create configuration files
	if err := s.createConfigFiles(ctx, repoPath, repo); err != nil {
		return fmt.Errorf("failed to create config files: %w", err)
	}

	// Create documentation files
	if err := s.createDocumentationFiles(ctx, repoPath, repo); err != nil {
		return fmt.Errorf("failed to create documentation files: %w", err)
	}

	// Create .gitignore
	if err := s.createGitignore(ctx, repoPath); err != nil {
		return fmt.Errorf("failed to create .gitignore: %w", err)
	}

	return nil
}

// createConfigFiles creates the .arxos/config.yaml file
func (s *RepositoryFilesystemService) createConfigFiles(ctx context.Context, repoPath string, repo *building.BuildingRepository) error {
	configPath := filepath.Join(repoPath, ".arxos", "config.yaml")

	configContent := fmt.Sprintf(`# ArxOS Building Repository Configuration
# Generated on %s

repository:
  id: "%s"
  name: "%s"
  type: "%s"
  floors: %d
  created_at: "%s"
  updated_at: "%s"

structure:
  version: "1.0.0"
  standard: "BUILDING_REPOSITORY_DESIGN.md"

directories:
  data:
    ifc: "data/ifc"
    plans: "data/plans"
    equipment: "data/equipment"
    spatial: "data/spatial"
  operations:
    maintenance: "operations/maintenance"
    energy: "operations/energy"
    occupancy: "operations/occupancy"
  integrations:
    bms: "integrations/bms"
    sensors: "integrations/sensors"
    apis: "integrations/apis"
  documentation: "documentation"
  versions: "versions"

validation:
  enabled: true
  strict_mode: false
  check_structure: true
  check_ifc_compliance: true
  check_data_integrity: true
  check_spatial: true

import:
  auto_validate: true
  create_backup: true
  max_file_size_mb: 500
  allowed_formats: ["ifc", "pdf", "csv", "json", "yaml"]
`,
		time.Now().Format(time.RFC3339),
		repo.ID,
		repo.Name,
		string(repo.Type),
		repo.Floors,
		repo.CreatedAt.Format(time.RFC3339),
		repo.UpdatedAt.Format(time.RFC3339),
	)

	return os.WriteFile(configPath, []byte(configContent), 0644)
}

// createDocumentationFiles creates the documentation files
func (s *RepositoryFilesystemService) createDocumentationFiles(ctx context.Context, repoPath string, repo *building.BuildingRepository) error {
	// Create README.md
	readmePath := filepath.Join(repoPath, "documentation", "README.md")
	readmeContent := fmt.Sprintf(`# %s

## Building Overview

- **Type**: %s
- **Floors**: %d
- **Created**: %s
- **Repository ID**: %s

## Repository Structure

This building repository follows the ArxOS Building Repository Design standard.

### Data Directory
- data/ifc/ - IFC building models (PRIMARY FORMAT)
- data/plans/ - Floor plans & drawings
- data/equipment/ - Equipment specifications
- data/spatial/ - Spatial reference data

### Operations Directory
- operations/maintenance/ - Maintenance records & schedules
- operations/energy/ - Energy data & optimization
- operations/occupancy/ - Occupancy & usage data

### Integrations Directory
- integrations/bms/ - Building Management System configs
- integrations/sensors/ - IoT sensor configurations
- integrations/apis/ - External API integrations

### Documentation Directory
- documentation/ - Building documentation and procedures

### Versions Directory
- versions/ - Versioned building snapshots

## Usage

### Import IFC Files
arx import --repository %s --ifc data/ifc/building-model.ifc

### Validate Repository
arx validate --repository %s

### Create Version
arx version --repository %s --message "Updated building model"

## Standards

This repository follows:
- ArxOS Building Repository Design
- buildingSMART IFC standards
- PostGIS spatial data standards
`,
		repo.Name,
		string(repo.Type),
		repo.Floors,
		repo.CreatedAt.Format(time.RFC3339),
		repo.ID,
		repo.ID,
		repo.ID,
		repo.ID,
	)

	if err := os.WriteFile(readmePath, []byte(readmeContent), 0644); err != nil {
		return err
	}

	// Create equipment-list.md
	equipmentPath := filepath.Join(repoPath, "documentation", "equipment-list.md")
	equipmentContent := `# Equipment List

## Overview
This document lists all equipment in the building.

## Equipment Categories

### HVAC Equipment
- Air Handling Units
- Chillers
- Boilers
- Pumps
- Fans

### Electrical Equipment
- Panels
- Transformers
- Generators
- UPS Systems

### Plumbing Equipment
- Water Heaters
- Pumps
- Valves
- Fixtures

## Equipment Data Files
Equipment specifications are stored in CSV format in the data/equipment/ directory.

## Maintenance
Equipment maintenance schedules are managed in the operations/maintenance/ directory.
`

	return os.WriteFile(equipmentPath, []byte(equipmentContent), 0644)
}

// createGitignore creates the .gitignore file
func (s *RepositoryFilesystemService) createGitignore(ctx context.Context, repoPath string) error {
	gitignorePath := filepath.Join(repoPath, ".gitignore")

	gitignoreContent := `# ArxOS Building Repository .gitignore

# Temporary files
*.tmp
*.temp
*~
.DS_Store
Thumbs.db

# Backup files
*.bak
*.backup
*.old

# Log files
*.log
logs/

# Cache files
.cache/
*.cache

# Large binary files (keep IFC files but ignore other large binaries)
*.dwg
*.dxf
*.rvt
*.rfa
*.max
*.3ds

# Sensitive data
*.key
*.pem
*.p12
secrets/
credentials/

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# IDE files
.vscode/
.idea/
*.swp
*.swo

# Node modules (if any)
node_modules/

# Python cache (if any)
__pycache__/
*.pyc
*.pyo

# Keep important files
!data/ifc/*.ifc
!data/plans/*.pdf
!data/equipment/*.csv
!data/spatial/*.json
!data/spatial/*.geojson
!operations/**/*.yaml
!operations/**/*.csv
!integrations/**/*.json
!integrations/**/*.yaml
!documentation/**/*.md
!.arxos/config.yaml
`

	return os.WriteFile(gitignorePath, []byte(gitignoreContent), 0644)
}

// GetRepositoryPath returns the filesystem path for a repository
func (s *RepositoryFilesystemService) GetRepositoryPath(repoName string) string {
	return filepath.Join(s.basePath, repoName)
}

// RepositoryExists checks if a repository directory exists
func (s *RepositoryFilesystemService) RepositoryExists(repoName string) bool {
	repoPath := s.GetRepositoryPath(repoName)
	configPath := filepath.Join(repoPath, ".arxos", "config.yaml")
	_, err := os.Stat(configPath)
	return err == nil
}
