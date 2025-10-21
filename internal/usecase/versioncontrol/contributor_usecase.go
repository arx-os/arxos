package versioncontrol

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/versioncontrol"
	"github.com/arx-os/arxos/internal/domain/types"
)

// ContributorUseCase handles contributor management and access control
type ContributorUseCase struct {
	contributorRepo versioncontrol.ContributorRepository
	teamRepo        versioncontrol.TeamRepository
	teamMemberRepo  versioncontrol.TeamMemberRepository
	auditRepo       versioncontrol.AccessAuditRepository
	logger          domain.Logger
}

// NewContributorUseCase creates a new contributor use case
func NewContributorUseCase(
	contributorRepo versioncontrol.ContributorRepository,
	teamRepo versioncontrol.TeamRepository,
	teamMemberRepo versioncontrol.TeamMemberRepository,
	auditRepo versioncontrol.AccessAuditRepository,
	logger domain.Logger,
) *ContributorUseCase {
	return &ContributorUseCase{
		contributorRepo: contributorRepo,
		teamRepo:        teamRepo,
		teamMemberRepo:  teamMemberRepo,
		auditRepo:       auditRepo,
		logger:          logger,
	}
}

// AddContributor adds a user to a repository
func (uc *ContributorUseCase) AddContributor(
	ctx context.Context,
	req versioncontrol.AddContributorRequest,
) (*versioncontrol.Contributor, error) {
	uc.logger.Info("Adding contributor",
		"repository", req.RepositoryID,
		"user", req.UserID,
		"role", req.Role)

	// Check if user already exists
	existing, _ := uc.contributorRepo.GetByUser(req.RepositoryID, req.UserID)
	if existing != nil {
		return nil, fmt.Errorf("user is already a contributor")
	}

	// Create contributor with role-based permissions
	now := time.Now()
	contributor := &versioncontrol.Contributor{
		ID:           types.NewID(),
		RepositoryID: req.RepositoryID,
		UserID:       req.UserID,
		Role:         req.Role,
		Status:       versioncontrol.ContributorStatusActive,
		InvitedBy:    &req.InvitedBy,
		InvitedAt:    &now,
		CreatedAt:    now,
		CreatedBy:    &req.InvitedBy,
		UpdatedAt:    now,
	}

	// Set permissions based on role
	uc.setRolePermissions(contributor)

	// Save contributor
	if err := uc.contributorRepo.Add(contributor); err != nil {
		return nil, fmt.Errorf("failed to add contributor: %w", err)
	}

	// Log audit
	_ = uc.auditRepo.Log(&versioncontrol.AccessAuditLog{
		ID:            types.NewID(),
		RepositoryID:  &req.RepositoryID,
		Action:        versioncontrol.AccessAuditContributorAdded,
		SubjectUserID: &req.UserID,
		Details:       fmt.Sprintf("Added as %s", req.Role),
		ActorID:       req.InvitedBy,
		OccurredAt:    now,
	})

	uc.logger.Info("Contributor added", "id", contributor.ID)
	return contributor, nil
}

// RemoveContributor removes a user from a repository
func (uc *ContributorUseCase) RemoveContributor(
	ctx context.Context,
	contributorID, actorID types.ID,
) error {
	uc.logger.Info("Removing contributor", "contributor", contributorID, "actor", actorID)

	contributor, err := uc.contributorRepo.GetByID(contributorID)
	if err != nil {
		return err
	}

	// Remove contributor
	if err := uc.contributorRepo.Remove(contributorID); err != nil {
		return fmt.Errorf("failed to remove contributor: %w", err)
	}

	// Log audit
	_ = uc.auditRepo.Log(&versioncontrol.AccessAuditLog{
		ID:            types.NewID(),
		RepositoryID:  &contributor.RepositoryID,
		Action:        versioncontrol.AccessAuditContributorRemoved,
		SubjectUserID: &contributor.UserID,
		Details:       fmt.Sprintf("Removed (was %s)", contributor.Role),
		ActorID:       actorID,
		OccurredAt:    time.Now(),
	})

	return nil
}

// UpdateContributor updates contributor permissions
func (uc *ContributorUseCase) UpdateContributor(
	ctx context.Context,
	req versioncontrol.UpdateContributorRequest,
	actorID types.ID,
) error {
	uc.logger.Info("Updating contributor", "contributor", req.ContributorID, "actor", actorID)

	contributor, err := uc.contributorRepo.GetByID(req.ContributorID)
	if err != nil {
		return err
	}

	oldRole := contributor.Role

	// Update role if specified
	if req.Role != nil {
		contributor.Role = *req.Role
		uc.setRolePermissions(contributor)
	}

	// Update status if specified
	if req.Status != nil {
		contributor.Status = *req.Status
	}

	contributor.UpdatedAt = time.Now()

	if err := uc.contributorRepo.Update(contributor); err != nil {
		return fmt.Errorf("failed to update contributor: %w", err)
	}

	// Log audit if role changed
	if req.Role != nil && oldRole != *req.Role {
		_ = uc.auditRepo.Log(&versioncontrol.AccessAuditLog{
			ID:            types.NewID(),
			RepositoryID:  &contributor.RepositoryID,
			Action:        versioncontrol.AccessAuditRoleChanged,
			SubjectUserID: &contributor.UserID,
			Details:       fmt.Sprintf("Role changed from %s to %s", oldRole, *req.Role),
			ActorID:       actorID,
			OccurredAt:    time.Now(),
		})
	}

	return nil
}

// ListContributors lists all contributors for a repository
func (uc *ContributorUseCase) ListContributors(
	ctx context.Context,
	repositoryID types.ID,
) ([]*versioncontrol.Contributor, error) {
	return uc.contributorRepo.ListByRepository(repositoryID)
}

// CreateTeam creates a new team
func (uc *ContributorUseCase) CreateTeam(
	ctx context.Context,
	req versioncontrol.CreateTeamRequest,
) (*versioncontrol.Team, error) {
	uc.logger.Info("Creating team", "slug", req.Slug, "name", req.Name)

	now := time.Now()
	team := &versioncontrol.Team{
		ID:              types.NewID(),
		RepositoryID:    req.RepositoryID,
		OrganizationID:  req.OrganizationID,
		Slug:            req.Slug,
		Name:            req.Name,
		Description:     req.Description,
		TeamType:        req.TeamType,
		Specializations: req.Specializations,
		DefaultRole:     versioncontrol.ContributorRoleContributor,
		CreatedAt:       now,
		CreatedBy:       &req.CreatedBy,
		UpdatedAt:       now,
	}

	if err := uc.teamRepo.Create(team); err != nil {
		return nil, fmt.Errorf("failed to create team: %w", err)
	}

	uc.logger.Info("Team created", "id", team.ID)
	return team, nil
}

// AddTeamMember adds a user to a team
func (uc *ContributorUseCase) AddTeamMember(
	ctx context.Context,
	req versioncontrol.AddTeamMemberRequest,
) error {
	uc.logger.Info("Adding team member", "team", req.TeamID, "user", req.UserID)

	// Check if already member
	isMember, _ := uc.teamMemberRepo.IsMember(req.TeamID, req.UserID)
	if isMember {
		return fmt.Errorf("user is already a team member")
	}

	member := &versioncontrol.TeamMember{
		ID:       types.NewID(),
		TeamID:   req.TeamID,
		UserID:   req.UserID,
		TeamRole: req.TeamRole,
		Status:   versioncontrol.TeamMemberStatusActive,
		AddedAt:  time.Now(),
		AddedBy:  &req.AddedBy,
	}

	if err := uc.teamMemberRepo.Add(member); err != nil {
		return fmt.Errorf("failed to add team member: %w", err)
	}

	return nil
}

// RemoveTeamMember removes a user from a team
func (uc *ContributorUseCase) RemoveTeamMember(
	ctx context.Context,
	teamID, userID types.ID,
) error {
	uc.logger.Info("Removing team member", "team", teamID, "user", userID)
	return uc.teamMemberRepo.Remove(teamID, userID)
}

// CheckPermission checks if a user has a specific permission
func (uc *ContributorUseCase) CheckPermission(
	ctx context.Context,
	repositoryID, userID types.ID,
	permission string,
) (bool, error) {
	contributor, err := uc.contributorRepo.GetByUser(repositoryID, userID)
	if err != nil {
		return false, nil // User not a contributor
	}

	if contributor.Status != versioncontrol.ContributorStatusActive {
		return false, nil
	}

	// Check specific permission
	switch permission {
	case "read":
		return contributor.CanRead, nil
	case "write":
		return contributor.CanWrite, nil
	case "create_branch":
		return contributor.CanCreateBranch, nil
	case "create_pr":
		return contributor.CanCreatePR, nil
	case "merge_pr":
		return contributor.CanMergePR, nil
	case "approve_pr":
		return contributor.CanApprovePR, nil
	case "delete_branch":
		return contributor.CanDeleteBranch, nil
	case "manage_issues":
		return contributor.CanManageIssues, nil
	case "assign_issues":
		return contributor.CanAssignIssues, nil
	case "manage_contributors":
		return contributor.CanManageContributors, nil
	case "manage_settings":
		return contributor.CanManageSettings, nil
	default:
		return false, fmt.Errorf("unknown permission: %s", permission)
	}
}

// setRolePermissions sets permissions based on role
func (uc *ContributorUseCase) setRolePermissions(contributor *versioncontrol.Contributor) {
	// Reset all permissions
	contributor.CanRead = false
	contributor.CanWrite = false
	contributor.CanCreateBranch = false
	contributor.CanCreatePR = false
	contributor.CanMergePR = false
	contributor.CanApprovePR = false
	contributor.CanDeleteBranch = false
	contributor.CanManageIssues = false
	contributor.CanAssignIssues = false
	contributor.CanManageContributors = false
	contributor.CanManageSettings = false
	contributor.ScopeAllBuildings = true

	// Set permissions based on role
	switch contributor.Role {
	case versioncontrol.ContributorRoleOwner:
		// Owner has all permissions
		contributor.CanRead = true
		contributor.CanWrite = true
		contributor.CanCreateBranch = true
		contributor.CanCreatePR = true
		contributor.CanMergePR = true
		contributor.CanApprovePR = true
		contributor.CanDeleteBranch = true
		contributor.CanManageIssues = true
		contributor.CanAssignIssues = true
		contributor.CanManageContributors = true
		contributor.CanManageSettings = true

	case versioncontrol.ContributorRoleAdmin:
		// Admin can do everything except delete repository
		contributor.CanRead = true
		contributor.CanWrite = true
		contributor.CanCreateBranch = true
		contributor.CanCreatePR = true
		contributor.CanMergePR = true
		contributor.CanApprovePR = true
		contributor.CanDeleteBranch = true
		contributor.CanManageIssues = true
		contributor.CanAssignIssues = true
		contributor.CanManageContributors = true
		contributor.CanManageSettings = false

	case versioncontrol.ContributorRoleMaintainer:
		// Maintainer can merge PRs and manage issues
		contributor.CanRead = true
		contributor.CanWrite = true
		contributor.CanCreateBranch = true
		contributor.CanCreatePR = true
		contributor.CanMergePR = true
		contributor.CanApprovePR = true
		contributor.CanDeleteBranch = false
		contributor.CanManageIssues = true
		contributor.CanAssignIssues = true

	case versioncontrol.ContributorRoleContributor:
		// Contributor can create branches and PRs
		contributor.CanRead = true
		contributor.CanWrite = true
		contributor.CanCreateBranch = true
		contributor.CanCreatePR = true
		contributor.CanManageIssues = true

	case versioncontrol.ContributorRoleReporter:
		// Reporter can only create issues
		contributor.CanRead = true
		contributor.CanManageIssues = true

	case versioncontrol.ContributorRoleReader:
		// Reader has read-only access
		contributor.CanRead = true
	}
}

