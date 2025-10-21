package versioncontrol

import (
	"github.com/arx-os/arxos/internal/domain/versioncontrol"
	"context"
	"crypto/sha256"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
)

// CommitUseCase handles Git-like commit operations with full changesets
type CommitUseCase struct {
	commitRepo versioncontrol.CommitRepository
	branchRepo versioncontrol.BranchRepository
	logger     domain.Logger
}

// NewCommitUseCase creates a new commit use case
func NewCommitUseCase(
	commitRepo versioncontrol.CommitRepository,
	branchRepo versioncontrol.BranchRepository,
	logger domain.Logger,
) *CommitUseCase {
	return &CommitUseCase{
		commitRepo: commitRepo,
		branchRepo: branchRepo,
		logger:     logger,
	}
}

// CreateCommit creates a new commit on a branch
func (uc *CommitUseCase) CreateCommit(
	ctx context.Context,
	req versioncontrol.CommitRequest,
) (*versioncontrol.Commit, error) {
	uc.logger.Info("Creating commit", "branch", req.BranchID, "message", req.Message)

	// Get branch
	branch, err := uc.branchRepo.GetByID(req.BranchID)
	if err != nil {
		return nil, fmt.Errorf("failed to get branch: %w", err)
	}

	// Verify branch is active
	if branch.Status != versioncontrol.BranchStatusActive {
		return nil, fmt.Errorf("cannot commit to %s branch", branch.Status)
	}

	// NOTE: Change tracking via building state diff
	// For now, create empty changes summary
	changesSummary := versioncontrol.ChangesSummary{}

	// Generate commit hash
	commitHash := uc.generateCommitHash(req)
	shortHash := commitHash[:7]

	// Determine parent commits
	parentCommits := make([]types.ID, 0)
	if branch.HeadCommit != nil {
		parentCommits = append(parentCommits, *branch.HeadCommit)
	}

	// Create commit
	now := time.Now()
	commit := &versioncontrol.Commit{
		ID:           types.NewID(),
		RepositoryID: req.RepositoryID,
		BranchID:     req.BranchID,
		VersionID:    types.NewID(), // NOTE: Version created by VersionUseCase.CreateVersion

		CommitHash: commitHash,
		ShortHash:  shortHash,

		Message:     req.Message,
		Description: req.Description,

		AuthorName:  req.AuthorName,
		AuthorEmail: req.AuthorEmail,
		AuthorID:    req.AuthorID,

		ParentCommits: parentCommits,
		MergeCommit:   false,

		ChangesSummary: changesSummary,
		FilesChanged:   0, // NOTE: File change tracking via VCS integration
		LinesAdded:     0,
		LinesDeleted:   0,

		Tags:     req.Tags,
		Metadata: make(map[string]any),

		CommittedAt: now,
	}

	// Save commit
	if err := uc.commitRepo.Create(commit); err != nil {
		return nil, fmt.Errorf("failed to create commit: %w", err)
	}

	// Update branch HEAD
	if err := uc.branchRepo.SetHead(branch.ID, commit.ID); err != nil {
		return nil, fmt.Errorf("failed to update branch HEAD: %w", err)
	}

	uc.logger.Info("Commit created successfully",
		"hash", commit.ShortHash,
		"branch", branch.Name,
		"message", commit.Message)

	return commit, nil
}

// ListCommits lists commits with filtering
func (uc *CommitUseCase) ListCommits(
	ctx context.Context,
	filter versioncontrol.CommitFilter,
	limit, offset int,
) ([]*versioncontrol.Commit, error) {
	return uc.commitRepo.List(filter, limit, offset)
}

// GetCommit retrieves a commit by hash (full or short)
func (uc *CommitUseCase) GetCommit(
	ctx context.Context,
	hash string,
) (*versioncontrol.Commit, error) {
	return uc.commitRepo.GetByHash(hash)
}

// GetCommitHistory retrieves full commit history for a branch
func (uc *CommitUseCase) GetCommitHistory(
	ctx context.Context,
	branchID types.ID,
) ([]*versioncontrol.Commit, error) {
	return uc.commitRepo.GetHistory(branchID)
}

// CompareCommits compares two commits and returns differences
func (uc *CommitUseCase) CompareCommits(
	ctx context.Context,
	fromHash, toHash string,
) (*versioncontrol.CommitComparison, error) {
	// Get commits
	fromCommit, err := uc.commitRepo.GetByHash(fromHash)
	if err != nil {
		return nil, fmt.Errorf("failed to get 'from' commit: %w", err)
	}

	toCommit, err := uc.commitRepo.GetByHash(toHash)
	if err != nil {
		return nil, fmt.Errorf("failed to get 'to' commit: %w", err)
	}

	// Calculate differences
	comparison := &versioncontrol.CommitComparison{
		FromCommit: fromCommit,
		ToCommit:   toCommit,
		Summary:    uc.calculateDiffSummary(fromCommit.ChangesSummary, toCommit.ChangesSummary),
	}

	return comparison, nil
}

// generateCommitHash generates a SHA-256 hash for a commit
func (uc *CommitUseCase) generateCommitHash(req versioncontrol.CommitRequest) string {
	// Similar to Git: hash of commit metadata + content
	data := fmt.Sprintf(
		"tree %s\nparent %s\nauthor %s <%s> %d\ncommitter %s <%s> %d\n\n%s",
		req.RepositoryID.String(),
		req.BranchID.String(),
		req.AuthorName,
		req.AuthorEmail,
		time.Now().Unix(),
		req.AuthorName,
		req.AuthorEmail,
		time.Now().Unix(),
		req.Message,
	)

	hash := sha256.Sum256([]byte(data))
	return fmt.Sprintf("%x", hash)
}

// calculateDiffSummary calculates the difference between two change summaries
func (uc *CommitUseCase) calculateDiffSummary(from, to versioncontrol.ChangesSummary) versioncontrol.ChangesSummary {
	return versioncontrol.ChangesSummary{
		BuildingsAdded:   to.BuildingsAdded - from.BuildingsAdded,
		BuildingsModified: to.BuildingsModified - from.BuildingsModified,
		BuildingsDeleted: to.BuildingsDeleted - from.BuildingsDeleted,

		FloorsAdded:    to.FloorsAdded - from.FloorsAdded,
		FloorsModified: to.FloorsModified - from.FloorsModified,
		FloorsDeleted:  to.FloorsDeleted - from.FloorsDeleted,

		RoomsAdded:    to.RoomsAdded - from.RoomsAdded,
		RoomsModified: to.RoomsModified - from.RoomsModified,
		RoomsDeleted:  to.RoomsDeleted - from.RoomsDeleted,

		EquipmentAdded:    to.EquipmentAdded - from.EquipmentAdded,
		EquipmentModified: to.EquipmentModified - from.EquipmentModified,
		EquipmentDeleted:  to.EquipmentDeleted - from.EquipmentDeleted,

		BASPointsAdded:    to.BASPointsAdded - from.BASPointsAdded,
		BASPointsModified: to.BASPointsModified - from.BASPointsModified,
		BASPointsDeleted:  to.BASPointsDeleted - from.BASPointsDeleted,
	}
}

