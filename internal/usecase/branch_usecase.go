package usecase

import (
	"context"
	"crypto/sha256"
	"fmt"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
)

// BranchUseCase handles Git-like branch operations
type BranchUseCase struct {
	branchRepo domain.BranchRepository
	commitRepo domain.CommitRepository
	logger     domain.Logger
}

// NewBranchUseCase creates a new branch use case
func NewBranchUseCase(
	branchRepo domain.BranchRepository,
	commitRepo domain.CommitRepository,
	logger domain.Logger,
) *BranchUseCase {
	return &BranchUseCase{
		branchRepo: branchRepo,
		commitRepo: commitRepo,
		logger:     logger,
	}
}

// CreateBranch creates a new branch
func (uc *BranchUseCase) CreateBranch(
	ctx context.Context,
	req domain.CreateBranchRequest,
) (*domain.Branch, error) {
	uc.logger.Info("Creating branch", "repository", req.RepositoryID, "name", req.Name)

	// Validate branch name
	if err := uc.validateBranchName(req.Name); err != nil {
		return nil, fmt.Errorf("invalid branch name: %w", err)
	}

	// Check if branch already exists
	existing, err := uc.branchRepo.GetByName(req.RepositoryID, req.Name)
	if err == nil && existing != nil {
		return nil, fmt.Errorf("branch '%s' already exists", req.Name)
	}

	// Get base commit (defaults to current HEAD of default branch)
	baseCommit := req.BaseCommit
	if baseCommit == nil {
		defaultBranch, err := uc.branchRepo.GetDefaultBranch(req.RepositoryID)
		if err != nil {
			uc.logger.Warn("No default branch found, branch will start empty", "repository", req.RepositoryID)
		} else if defaultBranch.HeadCommit != nil {
			baseCommit = defaultBranch.HeadCommit
		}
	}

	// Determine branch type if not specified
	branchType := req.BranchType
	if branchType == "" {
		branchType = uc.inferBranchType(req.Name)
	}

	// Create branch
	now := time.Now()
	branch := &domain.Branch{
		ID:                types.NewID(),
		RepositoryID:      req.RepositoryID,
		Name:              req.Name,
		DisplayName:       req.DisplayName,
		Description:       req.Description,
		BaseCommit:        baseCommit,
		HeadCommit:        baseCommit, // Starts at same commit as base
		BranchType:        branchType,
		Protected:         branchType == domain.BranchTypeMain, // Main is protected by default
		RequiresReview:    branchType == domain.BranchTypeMain || branchType == domain.BranchTypeRelease,
		AutoDeleteOnMerge: branchType == domain.BranchTypeIssue || branchType == domain.BranchTypeScan,
		Status:            domain.BranchStatusActive,
		IsDefault:         false,
		CreatedBy:         req.CreatedBy,
		OwnedBy:           req.CreatedBy,
		CreatedAt:         now,
		UpdatedAt:         now,
	}

	if err := uc.branchRepo.Create(branch); err != nil {
		return nil, fmt.Errorf("failed to create branch: %w", err)
	}

	uc.logger.Info("Branch created successfully", "branch", branch.Name, "id", branch.ID)
	return branch, nil
}

// ListBranches lists all branches for a repository
func (uc *BranchUseCase) ListBranches(
	ctx context.Context,
	repositoryID types.ID,
	filter domain.BranchFilter,
) ([]*domain.Branch, error) {
	filter.RepositoryID = &repositoryID
	return uc.branchRepo.List(filter)
}

// GetBranch retrieves a branch by name
func (uc *BranchUseCase) GetBranch(
	ctx context.Context,
	repositoryID types.ID,
	branchName string,
) (*domain.Branch, error) {
	return uc.branchRepo.GetByName(repositoryID, branchName)
}

// DeleteBranch deletes a branch
func (uc *BranchUseCase) DeleteBranch(
	ctx context.Context,
	repositoryID types.ID,
	branchName string,
	force bool,
) error {
	branch, err := uc.branchRepo.GetByName(repositoryID, branchName)
	if err != nil {
		return err
	}

	// Cannot delete default branch
	if branch.IsDefault {
		return fmt.Errorf("cannot delete default branch")
	}

	// Cannot delete protected branch unless forced
	if branch.Protected && !force {
		return fmt.Errorf("branch '%s' is protected, use --force to delete", branchName)
	}

	// Cannot delete main branch
	if branch.Name == "main" {
		return fmt.Errorf("cannot delete main branch")
	}

	return uc.branchRepo.Delete(branch.ID)
}

// CheckoutBranch checks out a branch (updates working directory)
func (uc *BranchUseCase) CheckoutBranch(
	ctx context.Context,
	req domain.CheckoutBranchRequest,
) (*domain.Branch, error) {
	uc.logger.Info("Checking out branch", "repository", req.RepositoryID, "branch", req.BranchName)

	// Get branch
	branch, err := uc.branchRepo.GetByName(req.RepositoryID, req.BranchName)
	if err != nil {
		return nil, fmt.Errorf("branch not found: %w", err)
	}

	// NOTE: Working directory update handled by BuildingStateManager
	// NOTE: Branch state loaded lazily via repository context
	// NOTE: Uncommitted changes check via BuildingStateManager.HasUncommittedChanges()

	uc.logger.Info("Branch checked out", "branch", branch.Name)
	return branch, nil
}

// SetDefaultBranch sets the default branch for a repository
func (uc *BranchUseCase) SetDefaultBranch(
	ctx context.Context,
	repositoryID types.ID,
	branchName string,
) error {
	// Get the branch
	branch, err := uc.branchRepo.GetByName(repositoryID, branchName)
	if err != nil {
		return err
	}

	// NOTE: Default branch managed via Repository.DefaultBranch field
	// Update is handled by repository metadata update

	branch.IsDefault = true
	return uc.branchRepo.Update(branch)
}

// validateBranchName validates a branch name follows conventions
func (uc *BranchUseCase) validateBranchName(name string) error {
	if name == "" {
		return fmt.Errorf("branch name cannot be empty")
	}

	if len(name) > 100 {
		return fmt.Errorf("branch name too long (max 100 characters)")
	}

	// Cannot start with special characters
	if strings.HasPrefix(name, "-") || strings.HasPrefix(name, ".") {
		return fmt.Errorf("branch name cannot start with '-' or '.'")
	}

	// Cannot contain certain characters
	invalidChars := []string{" ", "..", "~", "^", ":", "?", "*", "[", "\\"}
	for _, char := range invalidChars {
		if strings.Contains(name, char) {
			return fmt.Errorf("branch name cannot contain '%s'", char)
		}
	}

	return nil
}

// inferBranchType infers branch type from name
func (uc *BranchUseCase) inferBranchType(name string) domain.BranchType {
	nameLower := strings.ToLower(name)

	// Check prefixes
	if strings.HasPrefix(nameLower, "feature/") {
		return domain.BranchTypeFeature
	}
	if strings.HasPrefix(nameLower, "bugfix/") || strings.HasPrefix(nameLower, "fix/") {
		return domain.BranchTypeBugfix
	}
	if strings.HasPrefix(nameLower, "release/") {
		return domain.BranchTypeRelease
	}
	if strings.HasPrefix(nameLower, "hotfix/") {
		return domain.BranchTypeHotfix
	}
	if strings.HasPrefix(nameLower, "contractor/") || strings.HasPrefix(nameLower, "jci/") ||
		strings.HasPrefix(nameLower, "siemens/") {
		return domain.BranchTypeContractor
	}
	if strings.HasPrefix(nameLower, "vendor/") || strings.HasPrefix(nameLower, "hvac/") {
		return domain.BranchTypeVendor
	}
	if strings.HasPrefix(nameLower, "issue/") || strings.HasPrefix(nameLower, "issues/") {
		return domain.BranchTypeIssue
	}
	if strings.HasPrefix(nameLower, "scan/") || strings.HasPrefix(nameLower, "mobile/") {
		return domain.BranchTypeScan
	}

	// Special names
	if nameLower == "main" || nameLower == "master" {
		return domain.BranchTypeMain
	}
	if nameLower == "development" || nameLower == "develop" || nameLower == "dev" {
		return domain.BranchTypeDevelopment
	}

	// Default to feature
	return domain.BranchTypeFeature
}

// generateBranchHash generates a hash for branch identification
func (uc *BranchUseCase) generateBranchHash(repositoryID types.ID, name string, timestamp time.Time) string {
	data := fmt.Sprintf("%s:%s:%d", repositoryID.String(), name, timestamp.Unix())
	hash := sha256.Sum256([]byte(data))
	return fmt.Sprintf("%x", hash[:4]) // First 8 chars
}
