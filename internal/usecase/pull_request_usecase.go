package usecase

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
)

// PullRequestUseCase handles pull request operations (CMMS workflow)
type PullRequestUseCase struct {
	prRepo         domain.PullRequestRepository
	branchRepo     domain.BranchRepository
	commitRepo     domain.CommitRepository
	assignmentRepo domain.PRAssignmentRuleRepository
	logger         domain.Logger
}

// NewPullRequestUseCase creates a new pull request use case
func NewPullRequestUseCase(
	prRepo domain.PullRequestRepository,
	branchRepo domain.BranchRepository,
	commitRepo domain.CommitRepository,
	assignmentRepo domain.PRAssignmentRuleRepository,
	logger domain.Logger,
) *PullRequestUseCase {
	return &PullRequestUseCase{
		prRepo:         prRepo,
		branchRepo:     branchRepo,
		commitRepo:     commitRepo,
		assignmentRepo: assignmentRepo,
		logger:         logger,
	}
}

// CreatePullRequest creates a new pull request
func (uc *PullRequestUseCase) CreatePullRequest(
	ctx context.Context,
	req domain.CreatePRRequest,
) (*domain.PullRequest, error) {
	uc.logger.Info("Creating pull request",
		"repository", req.RepositoryID,
		"title", req.Title,
		"source", req.SourceBranchID,
		"target", req.TargetBranchID)

	// Validate branches exist
	sourceBranch, err := uc.branchRepo.GetByID(req.SourceBranchID)
	if err != nil {
		return nil, fmt.Errorf("source branch not found: %w", err)
	}

	targetBranch, err := uc.branchRepo.GetByID(req.TargetBranchID)
	if err != nil {
		return nil, fmt.Errorf("target branch not found: %w", err)
	}

	// Validate same repository
	if !sourceBranch.RepositoryID.Equal(targetBranch.RepositoryID) {
		return nil, fmt.Errorf("branches must be in same repository")
	}

	// Determine PR type if not specified
	prType := req.PRType
	if prType == "" {
		prType = uc.inferPRType(sourceBranch)
	}

	// Auto-assign if no assignee specified
	assignedTo := req.AssignedTo
	autoAssigned := false
	if assignedTo == nil {
		assignedTo, autoAssigned = uc.autoAssignPR(ctx, req.RepositoryID, prType, req.Priority)
	}

	// Determine if review required (target branch protection)
	requiresReview := targetBranch.RequiresReview || targetBranch.Protected
	requiredReviewers := 1
	if targetBranch.Protected {
		requiredReviewers = 2 // Main branch requires 2 approvals
	}

	// Create pull request
	now := time.Now()
	pr := &domain.PullRequest{
		ID:           types.NewID(),
		RepositoryID: req.RepositoryID,
		Title:        req.Title,
		Description:  req.Description,

		SourceBranchID: req.SourceBranchID,
		TargetBranchID: req.TargetBranchID,

		PRType:   prType,
		Status:   domain.PRStatusOpen,
		Priority: req.Priority,

		RequiresReview:    requiresReview,
		RequiredReviewers: requiredReviewers,
		ApprovedCount:     0,

		AssignedTo:   assignedTo,
		AutoAssigned: autoAssigned,

		EstimatedHours: req.EstimatedHours,
		BudgetAmount:   req.BudgetAmount,
		DueDate:        req.DueDate,

		Labels: req.Labels,

		CreatedBy: req.CreatedBy,
		CreatedAt: now,
		UpdatedAt: now,
	}

	// Save PR
	if err := uc.prRepo.Create(pr); err != nil {
		return nil, fmt.Errorf("failed to create PR: %w", err)
	}

	uc.logger.Info("Pull request created",
		"id", pr.ID,
		"number", pr.Number,
		"assigned_to", assignedTo,
		"auto_assigned", autoAssigned)

	// NOTE: Reviewers and activity logging happen via separate operations:
	// - Add reviewers: UpdatePullRequest() or AddReviewers()
	// - Activity logging: Tracked via audit middleware when implemented

	return pr, nil
}

// ListPullRequests lists pull requests with filtering
func (uc *PullRequestUseCase) ListPullRequests(
	ctx context.Context,
	filter domain.PRFilter,
	limit, offset int,
) ([]*domain.PullRequest, error) {
	return uc.prRepo.List(filter, limit, offset)
}

// GetPullRequest retrieves a PR by number
func (uc *PullRequestUseCase) GetPullRequest(
	ctx context.Context,
	repositoryID types.ID,
	number int,
) (*domain.PullRequest, error) {
	return uc.prRepo.GetByNumber(repositoryID, number)
}

// ApprovePullRequest approves a PR
func (uc *PullRequestUseCase) ApprovePullRequest(
	ctx context.Context,
	prID, reviewerID types.ID,
	comment string,
) error {
	uc.logger.Info("Approving PR", "pr", prID, "reviewer", reviewerID)

	pr, err := uc.prRepo.GetByID(prID)
	if err != nil {
		return err
	}

	// Increment approved count
	pr.ApprovedCount++

	// Check if ready to merge
	if pr.ApprovedCount >= pr.RequiredReviewers {
		pr.Status = domain.PRStatusApproved
		uc.logger.Info("PR approved and ready to merge", "pr", prID)
	} else {
		pr.Status = domain.PRStatusInReview
	}

	return uc.prRepo.Update(pr)
}

// MergePullRequest merges a PR
func (uc *PullRequestUseCase) MergePullRequest(
	ctx context.Context,
	req domain.MergePRRequest,
) error {
	uc.logger.Info("Merging PR", "pr", req.PRID, "merged_by", req.MergedBy)

	pr, err := uc.prRepo.GetByID(req.PRID)
	if err != nil {
		return err
	}

	// Validate PR status
	if pr.Status != domain.PRStatusApproved && pr.RequiresReview {
		return fmt.Errorf("PR must be approved before merging (current status: %s)", pr.Status)
	}

	// NOTE: Actual merge logic delegated to BranchUseCase and CommitUseCase:
	// 1. BranchUseCase.MergeBranch(source, target) - performs merge
	// 2. CommitUseCase.CreateMergeCommit() - creates commit record
	// 3. Repository state updated via version snapshots
	// This keeps separation of concerns clean

	// Mark PR as merged
	if err := uc.prRepo.Merge(pr.ID, req.MergedBy); err != nil {
		return fmt.Errorf("failed to mark PR as merged: %w", err)
	}

	// Auto-delete source branch if configured
	sourceBranch, err := uc.branchRepo.GetByID(pr.SourceBranchID)
	if err == nil && sourceBranch.AutoDeleteOnMerge {
		uc.logger.Info("Auto-deleting source branch", "branch", sourceBranch.Name)
		// Mark as merged, don't actually delete yet
		if err := uc.branchRepo.MarkMerged(sourceBranch.ID, req.MergedBy); err != nil {
			uc.logger.Warn("Failed to mark branch as merged", "error", err)
		}
	}

	uc.logger.Info("PR merged successfully", "pr", pr.Number)
	return nil
}

// ClosePullRequest closes a PR without merging
func (uc *PullRequestUseCase) ClosePullRequest(
	ctx context.Context,
	prID types.ID,
	reason string,
) error {
	uc.logger.Info("Closing PR", "pr", prID, "reason", reason)

	return uc.prRepo.Close(prID)
}

// inferPRType infers PR type from source branch type
func (uc *PullRequestUseCase) inferPRType(sourceBranch *domain.Branch) domain.PRType {
	switch sourceBranch.BranchType {
	case domain.BranchTypeContractor:
		return domain.PRTypeContractorWork
	case domain.BranchTypeVendor:
		return domain.PRTypeVendorService
	case domain.BranchTypeIssue:
		return domain.PRTypeIssueFix
	case domain.BranchTypeScan:
		return domain.PRTypeScanUpload
	default:
		return domain.PRTypeOther
	}
}

// autoAssignPR automatically assigns PR based on rules
func (uc *PullRequestUseCase) autoAssignPR(
	ctx context.Context,
	repositoryID types.ID,
	prType domain.PRType,
	priority domain.PRPriority,
) (*types.ID, bool) {
	// NOTE: Rule-based auto-assignment deferred to future enhancement
	// For MVP, manual assignment works
	// Future: Load assignment rules based on:
	// - File paths changed
	// - Equipment types affected
	// - Team specializations

	// For now, return nil (no auto-assignment)
	// Future: Load assignment rules and match based on:
	// - Equipment type
	// - Room type
	// - Floor number
	// - PR type
	// - Priority level

	return nil, false
}

// ListMyPRs lists PRs assigned to a user
func (uc *PullRequestUseCase) ListMyPRs(
	ctx context.Context,
	userID types.ID,
) ([]*domain.PullRequest, error) {
	return uc.prRepo.ListAssigned(userID)
}

// ListOpenPRs lists all open PRs for a repository
func (uc *PullRequestUseCase) ListOpenPRs(
	ctx context.Context,
	repositoryID types.ID,
) ([]*domain.PullRequest, error) {
	return uc.prRepo.ListOpen(repositoryID)
}

// GetPRStats returns PR statistics for a repository
func (uc *PullRequestUseCase) GetPRStats(
	ctx context.Context,
	repositoryID types.ID,
) (*PRStats, error) {
	// Get counts by status
	openStatus := domain.PRStatusOpen
	approvedStatus := domain.PRStatusApproved
	inReviewStatus := domain.PRStatusInReview

	openCount, _ := uc.prRepo.Count(domain.PRFilter{
		RepositoryID: &repositoryID,
		Status:       &openStatus,
	})

	approvedCount, _ := uc.prRepo.Count(domain.PRFilter{
		RepositoryID: &repositoryID,
		Status:       &approvedStatus,
	})

	inReviewCount, _ := uc.prRepo.Count(domain.PRFilter{
		RepositoryID: &repositoryID,
		Status:       &inReviewStatus,
	})

	overdueCount := len(uc.must(uc.prRepo.ListOverdue(repositoryID)))

	return &PRStats{
		OpenCount:     openCount,
		ApprovedCount: approvedCount,
		InReviewCount: inReviewCount,
		OverdueCount:  overdueCount,
	}, nil
}

// PRStats represents PR statistics
type PRStats struct {
	OpenCount     int
	ApprovedCount int
	InReviewCount int
	OverdueCount  int
}

// must is a helper that returns empty slice on error
func (uc *PullRequestUseCase) must(prs []*domain.PullRequest, err error) []*domain.PullRequest {
	if err != nil {
		return []*domain.PullRequest{}
	}
	return prs
}
