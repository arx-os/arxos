package usecase

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
)

// IssueUseCase handles issue tracking with auto-branch/PR creation
type IssueUseCase struct {
	issueRepo domain.IssueRepository
	branchUC  *BranchUseCase
	prUC      *PullRequestUseCase
	logger    domain.Logger
}

// NewIssueUseCase creates a new issue use case
func NewIssueUseCase(
	issueRepo domain.IssueRepository,
	branchUC *BranchUseCase,
	prUC *PullRequestUseCase,
	logger domain.Logger,
) *IssueUseCase {
	return &IssueUseCase{
		issueRepo: issueRepo,
		branchUC:  branchUC,
		prUC:      prUC,
		logger:    logger,
	}
}

// CreateIssue creates a new issue and optionally auto-creates branch/PR
func (uc *IssueUseCase) CreateIssue(
	ctx context.Context,
	req domain.CreateIssueRequest,
) (*domain.Issue, error) {
	uc.logger.Info("Creating issue",
		"repository", req.RepositoryID,
		"title", req.Title,
		"reported_by", req.ReportedBy)

	// Auto-escalate priority for safety/emergency types
	priority := req.Priority
	if req.IssueType == domain.IssueTypeSafety || req.IssueType == domain.IssueTypeEmergency {
		if priority == domain.IssuePriorityNormal || priority == domain.IssuePriorityLow {
			priority = domain.IssuePriorityUrgent
			uc.logger.Info("Auto-escalating priority for safety/emergency issue", "new_priority", priority)
		}
	}

	// Create issue
	now := time.Now()
	issue := &domain.Issue{
		ID:           types.NewID(),
		RepositoryID: req.RepositoryID,
		Title:        req.Title,
		Body:         req.Body,

		BuildingID:  req.BuildingID,
		FloorID:     req.FloorID,
		RoomID:      req.RoomID,
		EquipmentID: req.EquipmentID,
		BASPointID:  req.BASPointID,

		Location:            req.Location,
		LocationDescription: req.LocationDescription,

		IssueType: req.IssueType,
		Status:    domain.IssueStatusOpen,
		Priority:  priority,

		ReportedBy:  req.ReportedBy,
		ReportedVia: req.ReportedVia,

		CreatedAt: now,
		UpdatedAt: now,
	}

	// Auto-assign based on equipment type or issue type
	assignedTo, autoAssigned := uc.autoAssignIssue(ctx, issue)
	issue.AssignedTo = assignedTo
	issue.AutoAssigned = autoAssigned

	// Save issue
	if err := uc.issueRepo.Create(issue); err != nil {
		return nil, fmt.Errorf("failed to create issue: %w", err)
	}

	uc.logger.Info("Issue created",
		"id", issue.ID,
		"number", issue.Number,
		"assigned_to", assignedTo,
		"auto_assigned", autoAssigned)

	// NOTE: Auto-labeling and activity logging are future enhancements:
	// - Auto-labels: Based on keywords in title/description
	// - Activity logging: Via audit middleware when implemented

	return issue, nil
}

// StartWork begins work on an issue (creates branch and PR)
func (uc *IssueUseCase) StartWork(
	ctx context.Context,
	issueID types.ID,
	workerID types.ID,
) (*domain.Branch, *domain.PullRequest, error) {
	uc.logger.Info("Starting work on issue", "issue", issueID, "worker", workerID)

	// Get issue
	issue, err := uc.issueRepo.GetByID(issueID)
	if err != nil {
		return nil, nil, err
	}

	// Check if work already started
	if issue.BranchID != nil {
		return nil, nil, fmt.Errorf("work already started on this issue (branch exists)")
	}

	// Create branch for issue
	branchName := fmt.Sprintf("issue/%d-%s", issue.Number, uc.slugify(issue.Title))
	branch, err := uc.branchUC.CreateBranch(ctx, domain.CreateBranchRequest{
		RepositoryID: issue.RepositoryID,
		Name:         branchName,
		DisplayName:  fmt.Sprintf("Issue #%d: %s", issue.Number, issue.Title),
		Description:  issue.Body,
		BranchType:   domain.BranchTypeIssue,
		CreatedBy:    &workerID,
	})
	if err != nil {
		return nil, nil, fmt.Errorf("failed to create branch: %w", err)
	}

	// Create PR for issue
	pr, err := uc.prUC.CreatePullRequest(ctx, domain.CreatePRRequest{
		RepositoryID:   issue.RepositoryID,
		Title:          fmt.Sprintf("Fix issue #%d: %s", issue.Number, issue.Title),
		Description:    fmt.Sprintf("Resolves #%d\n\n%s", issue.Number, issue.Body),
		SourceBranchID: branch.ID,
		TargetBranchID: branch.ID, // Uses current branch as target
		PRType:         domain.PRTypeIssueFix,
		Priority:       domain.PRPriority(issue.Priority),
		CreatedBy:      workerID,
	})
	if err != nil {
		return nil, nil, fmt.Errorf("failed to create PR: %w", err)
	}

	// Link issue to branch and PR
	issue.BranchID = &branch.ID
	issue.PRID = &pr.ID
	issue.Status = domain.IssueStatusInProgress

	if err := uc.issueRepo.Update(issue); err != nil {
		return nil, nil, fmt.Errorf("failed to update issue: %w", err)
	}

	uc.logger.Info("Work started on issue",
		"issue", issue.Number,
		"branch", branch.Name,
		"pr", pr.Number)

	return branch, pr, nil
}

// ResolveIssue resolves an issue
func (uc *IssueUseCase) ResolveIssue(
	ctx context.Context,
	req domain.ResolveIssueRequest,
) error {
	uc.logger.Info("Resolving issue", "issue", req.IssueID, "resolved_by", req.ResolvedBy)

	return uc.issueRepo.Resolve(req.IssueID, req.ResolvedBy, req.ResolutionNotes)
}

// VerifyIssue allows reporter to verify the fix
func (uc *IssueUseCase) VerifyIssue(
	ctx context.Context,
	req domain.VerifyIssueRequest,
) error {
	uc.logger.Info("Verifying issue fix",
		"issue", req.IssueID,
		"verified_by", req.VerifiedBy,
		"confirmed", req.Confirmed)

	if !req.Confirmed {
		// Reporter says still broken - reopen issue
		return uc.issueRepo.Reopen(req.IssueID)
	}

	return uc.issueRepo.Verify(req.IssueID, req.VerifiedBy)
}

// ListIssues lists issues with filtering
func (uc *IssueUseCase) ListIssues(
	ctx context.Context,
	filter domain.IssueFilter,
	limit, offset int,
) ([]*domain.Issue, error) {
	return uc.issueRepo.List(filter, limit, offset)
}

// GetIssue retrieves an issue by number
func (uc *IssueUseCase) GetIssue(
	ctx context.Context,
	repositoryID types.ID,
	number int,
) (*domain.Issue, error) {
	return uc.issueRepo.GetByNumber(repositoryID, number)
}

// ListMyIssues lists issues assigned to a user
func (uc *IssueUseCase) ListMyIssues(
	ctx context.Context,
	userID types.ID,
) ([]*domain.Issue, error) {
	return uc.issueRepo.ListAssigned(userID)
}

// ListOpenIssues lists all open issues for a repository
func (uc *IssueUseCase) ListOpenIssues(
	ctx context.Context,
	repositoryID types.ID,
) ([]*domain.Issue, error) {
	return uc.issueRepo.ListOpen(repositoryID)
}

// CloseIssue closes an issue
func (uc *IssueUseCase) CloseIssue(
	ctx context.Context,
	issueID types.ID,
	reason string,
) error {
	uc.logger.Info("Closing issue", "issue", issueID, "reason", reason)
	return uc.issueRepo.Close(issueID)
}

// ReopenIssue reopens a closed issue
func (uc *IssueUseCase) ReopenIssue(
	ctx context.Context,
	issueID types.ID,
) error {
	uc.logger.Info("Reopening issue", "issue", issueID)
	return uc.issueRepo.Reopen(issueID)
}

// autoAssignIssue automatically assigns an issue based on equipment type or rules
func (uc *IssueUseCase) autoAssignIssue(
	ctx context.Context,
	issue *domain.Issue,
) (*types.ID, bool) {
	// NOTE: Rule-based auto-assignment is future enhancement
	// For MVP, manual assignment or simple defaults:

	// If equipment specified, assign based on equipment type
	// if issue.EquipmentID != nil {
	//     equipment, err := equipmentRepo.GetByID(issue.EquipmentID)
	//     if err == nil {
	//         return assignByEquipmentType(equipment.Type)
	//     }
	// }

	// If room specified, assign to building staff
	// If BAS point specified, assign to BAS team
	// etc.

	return nil, false
}

// slugify converts a title to URL-safe slug
func (uc *IssueUseCase) slugify(title string) string {
	// Convert to lowercase
	slug := strings.ToLower(title)

	// Replace spaces with hyphens
	slug = strings.ReplaceAll(slug, " ", "-")

	// Remove special characters
	slug = strings.Map(func(r rune) rune {
		if (r >= 'a' && r <= 'z') || (r >= '0' && r <= '9') || r == '-' {
			return r
		}
		return -1
	}, slug)

	// Limit length
	if len(slug) > 50 {
		slug = slug[:50]
	}

	// Remove trailing hyphens
	slug = strings.TrimRight(slug, "-")

	return slug
}
