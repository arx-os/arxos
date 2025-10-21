package workflow

import (
	"context"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/versioncontrol"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/test/helpers"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestPRWorkflow_Complete tests the complete PR workflow end-to-end
func TestPRWorkflow_Complete(t *testing.T) {
	// Setup
	db, cleanup := helpers.SetupTestEnvironment(t)
	defer cleanup()

	logger := helpers.NewTestLogger()
	repos := helpers.SetupRepositories(db)

	// Clean up test data
	db.Exec("DELETE FROM pull_requests")
	db.Exec("DELETE FROM repository_branches")
	db.Exec("DELETE FROM building_repositories")
	db.Exec("DELETE FROM buildings")
	db.Exec("DELETE FROM users WHERE id = 'test-user-pr'")

	// Create user for PR workflow
	_, err := db.Exec(`
		INSERT INTO users (id, email, username, full_name, password_hash, role, is_active, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
	`, "test-user-pr", "pr-test@arxos.io", "prtest", "PR Test User", "hashed", "user", true, time.Now(), time.Now())
	require.NoError(t, err)

	// Create use cases
	branchUC := helpers.SetupBranchUseCase(repos, logger)
	prUC := helpers.SetupPullRequestUseCase(repos, db, logger)
	buildingUC := helpers.SetupBuildingUseCase(repos, logger)

	ctx := context.Background()

	// Step 1: Create a building/repository
	t.Log("Step 1: Creating building/repository")
	buildingReq := &domain.CreateBuildingRequest{
		Name:    "PR Workflow Test Building",
		Address: "PR Test Address",
		Coordinates: &domain.Location{
			X: -122.4194,
			Y: 37.7749,
			Z: 0,
		},
	}

	building, err := buildingUC.CreateBuilding(ctx, buildingReq)
	require.NoError(t, err)
	repoID := building.ID

	// Create building repository
	_, err = db.Exec(`
		INSERT INTO building_repositories (id, name, type, floors, structure_json)
		VALUES ($1, $2, $3, $4, $5)
	`, repoID.String(), building.Name, "office", 1, "{}")
	require.NoError(t, err)

	// Step 2: Create main branch
	t.Log("Step 2: Creating main branch")
	userID := types.FromString("test-user-pr")
	mainBranch, err := branchUC.CreateBranch(ctx, domain.CreateBranchRequest{
		RepositoryID: repoID,
		Name:         "main",
		DisplayName:  "Main Branch",
		BranchType:   versioncontrol.BranchTypeMain,
		CreatedBy:    &userID,
	})
	require.NoError(t, err)
	assert.Equal(t, "main", mainBranch.Name)
	assert.True(t, mainBranch.Protected)

	// Step 3: Create feature branch
	t.Log("Step 3: Creating feature branch")
	featureBranch, err := branchUC.CreateBranch(ctx, domain.CreateBranchRequest{
		RepositoryID: repoID,
		Name:         "feature/test-feature",
		DisplayName:  "Test Feature",
		BranchType:   versioncontrol.BranchTypeFeature,
		CreatedBy:    &userID,
	})
	require.NoError(t, err)
	assert.Equal(t, "feature/test-feature", featureBranch.Name)
	assert.False(t, featureBranch.Protected)

	// Step 3.5: Create dev branch (non-protected target)
	t.Log("Step 3.5: Creating dev branch")
	devBranch, err := branchUC.CreateBranch(ctx, domain.CreateBranchRequest{
		RepositoryID: repoID,
		Name:         "dev",
		DisplayName:  "Development Branch",
		BranchType:   versioncontrol.BranchTypeDevelopment,
		CreatedBy:    &userID,
	})
	require.NoError(t, err)
	assert.False(t, devBranch.Protected, "Dev branch should not be protected")

	// Step 4: Create Pull Request
	t.Log("Step 4: Creating Pull Request")
	prReq := versioncontrol.CreatePRRequest{
		RepositoryID:   repoID,
		Title:          "Test Feature PR",
		Description:    "This is a test PR for integration testing",
		SourceBranchID: featureBranch.ID,
		TargetBranchID: devBranch.ID, // Use dev instead of main
		PRType:         domain.PRTypeFeature,
		Priority:       versioncontrol.PRPriorityNormal,
		CreatedBy:      userID,
	}

	pr, err := prUC.CreatePullRequest(ctx, prReq)
	require.NoError(t, err)
	require.NotNil(t, pr)
	assert.Equal(t, "Test Feature PR", pr.Title)
	assert.Equal(t, versioncontrol.PRStatusOpen, pr.Status)
	assert.Equal(t, domain.PRTypeFeature, pr.PRType)
	assert.False(t, pr.RequiresReview, "Dev target should not require review")

	// Step 5: Get PR
	t.Log("Step 5: Retrieving PR")
	retrievedPR, err := prUC.GetPullRequest(ctx, repoID, pr.Number)
	require.NoError(t, err)
	assert.Equal(t, pr.ID, retrievedPR.ID)
	assert.Equal(t, pr.Title, retrievedPR.Title)

	// Step 6: List PRs
	t.Log("Step 6: Listing PRs")
	filter := versioncontrol.PRFilter{
		RepositoryID: &repoID,
	}
	prs, err := prUC.ListPullRequests(ctx, filter, 10, 0)
	require.NoError(t, err)
	assert.GreaterOrEqual(t, len(prs), 1, "Should have at least one PR")

	// Step 7: Approve PR
	t.Log("Step 7: Approving PR")
	reviewerID := types.FromString("test-user-pr")
	err = prUC.ApprovePullRequest(ctx, pr.ID, reviewerID, "LGTM - looks good!")
	require.NoError(t, err)

	// Step 8: Merge PR
	t.Log("Step 8: Merging PR")
	mergeReq := versioncontrol.MergePRRequest{
		PRID:     pr.ID,
		MergedBy: userID,
		Message:  "Merge feature branch",
		Strategy: "merge",
	}

	err = prUC.MergePullRequest(ctx, mergeReq)
	require.NoError(t, err)

	// Step 9: Verify PR is merged
	t.Log("Step 9: Verifying PR is merged")
	mergedPR, err := prUC.GetPullRequest(ctx, repoID, pr.Number)
	require.NoError(t, err)
	assert.Equal(t, versioncontrol.PRStatusMerged, mergedPR.Status)
	assert.NotNil(t, mergedPR.MergedAt, "MergedAt should be set")

	t.Log("✅ PR workflow test complete")
}

// TestIssueWorkflow_Complete tests the complete issue workflow end-to-end
func TestIssueWorkflow_Complete(t *testing.T) {
	// Setup
	db, cleanup := helpers.SetupTestEnvironment(t)
	defer cleanup()

	logger := helpers.NewTestLogger()
	repos := helpers.SetupRepositories(db)

	// Clean up test data
	db.Exec("DELETE FROM issues")
	db.Exec("DELETE FROM pull_requests")
	db.Exec("DELETE FROM repository_branches")
	db.Exec("DELETE FROM building_repositories")
	db.Exec("DELETE FROM buildings")
	db.Exec("DELETE FROM users WHERE id = 'test-user-issue'")

	// Create user
	_, err := db.Exec(`
		INSERT INTO users (id, email, username, full_name, password_hash, role, is_active, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
	`, "test-user-issue", "issue-test@arxos.io", "issuetest", "Issue Test User", "hashed", "user", true, time.Now(), time.Now())
	require.NoError(t, err)

	// Create use cases
	branchUC := helpers.SetupBranchUseCase(repos, logger)
	prUC := helpers.SetupPullRequestUseCase(repos, db, logger)
	issueUC := helpers.SetupIssueUseCase(repos, prUC, branchUC, logger)
	buildingUC := helpers.SetupBuildingUseCase(repos, logger)

	ctx := context.Background()

	// Step 1: Create building/repository
	t.Log("Step 1: Creating building/repository")
	buildingReq := &domain.CreateBuildingRequest{
		Name:    "Issue Workflow Test Building",
		Address: "Issue Test Address",
		Coordinates: &domain.Location{
			X: -122.4194,
			Y: 37.7749,
			Z: 0,
		},
	}

	building, err := buildingUC.CreateBuilding(ctx, buildingReq)
	require.NoError(t, err)
	repoID := building.ID

	// Create building repository
	_, err = db.Exec(`
		INSERT INTO building_repositories (id, name, type, floors, structure_json)
		VALUES ($1, $2, $3, $4, $5)
	`, repoID.String(), building.Name, "office", 1, "{}")
	require.NoError(t, err)

	// Step 2: Create Issue
	t.Log("Step 2: Creating Issue")
	userID := types.FromString("test-user-issue")
	issueReq := versioncontrol.CreateIssueRequest{
		RepositoryID: repoID,
		Title:        "Test outlet not working",
		Body:         "Outlet in room 105 is not providing power",
		IssueType:    versioncontrol.IssueTypeProblem,
		Priority:     versioncontrol.IssuePriorityHigh,
		ReportedBy:   userID,
	}

	issue, err := issueUC.CreateIssue(ctx, issueReq)
	require.NoError(t, err)
	require.NotNil(t, issue)
	assert.Equal(t, "Test outlet not working", issue.Title)
	assert.Equal(t, domain.IssueStatusOpen, issue.Status)

	// Step 3: Get Issue
	t.Log("Step 3: Retrieving Issue")
	retrievedIssue, err := issueUC.GetIssue(ctx, repoID, issue.Number)
	require.NoError(t, err)
	assert.Equal(t, issue.ID, retrievedIssue.ID)
	assert.Equal(t, issue.Title, retrievedIssue.Title)

	// Step 4: List Issues
	t.Log("Step 4: Listing Issues")
	filter := versioncontrol.IssueFilter{
		RepositoryID: &repoID,
	}
	issues, err := issueUC.ListIssues(ctx, filter, 10, 0)
	require.NoError(t, err)
	assert.GreaterOrEqual(t, len(issues), 1, "Should have at least one issue")

	// Step 5: Start work on issue (creates branch and PR)
	t.Log("Step 5: Starting work on issue")
	branch, pr, err := issueUC.StartWork(ctx, issue.ID, userID)
	require.NoError(t, err)
	require.NotNil(t, branch)
	require.NotNil(t, pr)
	assert.Contains(t, branch.Name, "issue/")
	assert.Equal(t, domain.PRTypeIssueFix, pr.PRType)

	// Step 6: Verify issue status updated
	t.Log("Step 6: Verifying issue status")
	updatedIssue, err := issueUC.GetIssue(ctx, repoID, issue.Number)
	require.NoError(t, err)
	assert.Equal(t, domain.IssueStatusInProgress, updatedIssue.Status)
	assert.NotNil(t, updatedIssue.BranchID)
	assert.NotNil(t, updatedIssue.PRID)

	// Step 7: Resolve issue
	t.Log("Step 7: Resolving issue")
	resolveReq := domain.ResolveIssueRequest{
		IssueID:         issue.ID,
		ResolvedBy:      userID,
		ResolutionNotes: "Reset breaker - outlet now working",
	}

	err = issueUC.ResolveIssue(ctx, resolveReq)
	require.NoError(t, err)

	// Step 8: Verify issue resolved
	t.Log("Step 8: Verifying issue resolved")
	resolvedIssue, err := issueUC.GetIssue(ctx, repoID, issue.Number)
	require.NoError(t, err)
	assert.Equal(t, domain.IssueStatusResolved, resolvedIssue.Status)
	assert.NotNil(t, resolvedIssue.ResolvedAt)

	// Step 9: Close issue
	t.Log("Step 9: Closing issue")
	err = issueUC.CloseIssue(ctx, issue.ID, "Work completed and verified")
	require.NoError(t, err)

	// Step 10: Verify issue closed
	t.Log("Step 10: Verifying issue closed")
	closedIssue, err := issueUC.GetIssue(ctx, repoID, issue.Number)
	require.NoError(t, err)
	assert.Equal(t, domain.IssueStatusClosed, closedIssue.Status)
	assert.NotNil(t, closedIssue.ClosedAt)

	t.Log("✅ Issue workflow test complete")
}

// TestPRIssueIntegration tests PR and Issue workflow together
func TestPRIssueIntegration(t *testing.T) {
	// Setup
	db, cleanup := helpers.SetupTestEnvironment(t)
	defer cleanup()

	logger := helpers.NewTestLogger()
	repos := helpers.SetupRepositories(db)

	// Clean up test data
	db.Exec("DELETE FROM issues")
	db.Exec("DELETE FROM pull_requests")
	db.Exec("DELETE FROM repository_branches")
	db.Exec("DELETE FROM building_repositories")
	db.Exec("DELETE FROM buildings")
	db.Exec("DELETE FROM users WHERE id IN ('test-user-integration', 'test-reviewer')")

	// Create users
	for _, userID := range []string{"test-user-integration", "test-reviewer"} {
		_, err := db.Exec(`
			INSERT INTO users (id, email, username, full_name, password_hash, role, is_active, created_at, updated_at)
			VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
		`, userID, userID+"@arxos.io", userID, userID, "hashed", "user", true, time.Now(), time.Now())
		require.NoError(t, err)
	}

	// Create use cases
	branchUC := helpers.SetupBranchUseCase(repos, logger)
	prUC := helpers.SetupPullRequestUseCase(repos, db, logger)
	issueUC := helpers.SetupIssueUseCase(repos, prUC, branchUC, logger)
	buildingUC := helpers.SetupBuildingUseCase(repos, logger)

	ctx := context.Background()

	// Create building/repository
	buildingReq := &domain.CreateBuildingRequest{
		Name:    "Integration Test Building",
		Address: "Integration Test Address",
		Coordinates: &domain.Location{
			X: -122.4194,
			Y: 37.7749,
			Z: 0,
		},
	}

	building, err := buildingUC.CreateBuilding(ctx, buildingReq)
	require.NoError(t, err)
	repoID := building.ID

	_, err = db.Exec(`
		INSERT INTO building_repositories (id, name, type, floors, structure_json)
		VALUES ($1, $2, $3, $4, $5)
	`, repoID.String(), building.Name, "office", 1, "{}")
	require.NoError(t, err)

	// Workflow: Create issue → Start work → Resolve → Merge PR → Close issue
	userID := types.FromString("test-user-integration")

	// 1. Create issue
	issueReq := versioncontrol.CreateIssueRequest{
		RepositoryID: repoID,
		Title:        "HVAC not cooling properly",
		Body:         "VAV damper stuck, needs adjustment",
		IssueType:    versioncontrol.IssueTypeProblem,
		Priority:     versioncontrol.IssuePriorityHigh,
		ReportedBy:   userID,
	}

	issue, err := issueUC.CreateIssue(ctx, issueReq)
	require.NoError(t, err)
	assert.Equal(t, domain.IssueStatusOpen, issue.Status)

	// 2. Start work (creates branch + PR)
	branch, pr, err := issueUC.StartWork(ctx, issue.ID, userID)
	require.NoError(t, err)
	assert.NotNil(t, branch)
	assert.NotNil(t, pr)
	assert.Equal(t, domain.PRTypeIssueFix, pr.PRType)

	// 3. Approve PR
	reviewerID := types.FromString("test-reviewer")
	err = prUC.ApprovePullRequest(ctx, pr.ID, reviewerID, "Looks good")
	require.NoError(t, err)

	// 4. Resolve issue
	resolveReq := domain.ResolveIssueRequest{
		IssueID:         issue.ID,
		ResolvedBy:      userID,
		ResolutionNotes: "Adjusted VAV damper, cooling restored",
	}
	err = issueUC.ResolveIssue(ctx, resolveReq)
	require.NoError(t, err)

	// 5. Merge PR
	mergeReq := versioncontrol.MergePRRequest{
		PRID:     pr.ID,
		MergedBy: userID,
		Message:  "Fix HVAC cooling issue",
		Strategy: "squash",
	}
	err = prUC.MergePullRequest(ctx, mergeReq)
	require.NoError(t, err)

	// 6. Close issue
	err = issueUC.CloseIssue(ctx, issue.ID, "Work completed and merged")
	require.NoError(t, err)

	// Verify final states
	finalIssue, err := issueUC.GetIssue(ctx, repoID, issue.Number)
	require.NoError(t, err)
	assert.Equal(t, domain.IssueStatusClosed, finalIssue.Status)

	finalPR, err := prUC.GetPullRequest(ctx, repoID, pr.Number)
	require.NoError(t, err)
	assert.Equal(t, versioncontrol.PRStatusMerged, finalPR.Status)

	t.Log("✅ PR/Issue integration workflow complete")
}
