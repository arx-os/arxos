package postgis

import (
	"github.com/arx-os/arxos/internal/domain/versioncontrol"
	"database/sql"
	"encoding/json"
	"fmt"

	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/lib/pq"
)

// BranchRepository implements branch repository for PostGIS
type BranchRepository struct {
	db *sql.DB
}

// NewBranchRepository creates a new PostGIS branch repository
func NewBranchRepository(db *sql.DB) *BranchRepository {
	return &BranchRepository{
		db: db,
	}
}

// Create creates a new branch
func (r *BranchRepository) Create(branch *versioncontrol.Branch) error {
	query := `
		INSERT INTO repository_branches (
			id, repository_id, name, display_name, description,
			base_commit, head_commit,
			branch_type, protected, requires_review, auto_delete_on_merge,
			status, is_default,
			created_by, owned_by,
			created_at, updated_at
		) VALUES (
			$1, $2, $3, $4, $5,
			$6, $7,
			$8, $9, $10, $11,
			$12, $13,
			$14, $15,
			$16, $17
		)
	`

	_, err := r.db.Exec(query,
		branch.ID.String(), branch.RepositoryID.String(), branch.Name, branch.DisplayName, branch.Description,
		nullableID(branch.BaseCommit), nullableID(branch.HeadCommit),
		branch.BranchType, branch.Protected, branch.RequiresReview, branch.AutoDeleteOnMerge,
		branch.Status, branch.IsDefault,
		nullableID(branch.CreatedBy), nullableID(branch.OwnedBy),
		branch.CreatedAt, branch.UpdatedAt,
	)

	return err
}

// GetByID retrieves a branch by ID
func (r *BranchRepository) GetByID(id types.ID) (*versioncontrol.Branch, error) {
	query := `
		SELECT
			id, repository_id, name, display_name, description,
			base_commit, head_commit,
			branch_type, protected, requires_review, auto_delete_on_merge,
			status, is_default,
			created_by, owned_by,
			created_at, updated_at, merged_at, merged_by
		FROM repository_branches
		WHERE id = $1
	`

	branch := &versioncontrol.Branch{}
	var baseCommit, headCommit, createdBy, ownedBy, mergedBy sql.NullString
	var description sql.NullString
	var mergedAt sql.NullTime

	err := r.db.QueryRow(query, id.String()).Scan(
		&branch.ID, &branch.RepositoryID, &branch.Name, &branch.DisplayName, &description,
		&baseCommit, &headCommit,
		&branch.BranchType, &branch.Protected, &branch.RequiresReview, &branch.AutoDeleteOnMerge,
		&branch.Status, &branch.IsDefault,
		&createdBy, &ownedBy,
		&branch.CreatedAt, &branch.UpdatedAt, &mergedAt, &mergedBy,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("branch not found")
		}
		return nil, err
	}

	// Handle nullable fields
	if description.Valid {
		branch.Description = description.String
	}
	if baseCommit.Valid {
		id := types.FromString(baseCommit.String)
		branch.BaseCommit = &id
	}
	if headCommit.Valid {
		id := types.FromString(headCommit.String)
		branch.HeadCommit = &id
	}
	if createdBy.Valid {
		id := types.FromString(createdBy.String)
		branch.CreatedBy = &id
	}
	if ownedBy.Valid {
		id := types.FromString(ownedBy.String)
		branch.OwnedBy = &id
	}
	if mergedAt.Valid {
		branch.MergedAt = &mergedAt.Time
	}
	if mergedBy.Valid {
		id := types.FromString(mergedBy.String)
		branch.MergedBy = &id
	}

	return branch, nil
}

// Update updates an existing branch
func (r *BranchRepository) Update(branch *versioncontrol.Branch) error {
	query := `
		UPDATE repository_branches SET
			display_name = $1,
			description = $2,
			head_commit = $3,
			protected = $4,
			requires_review = $5,
			status = $6,
			owned_by = $7,
			updated_at = NOW()
		WHERE id = $8
	`

	_, err := r.db.Exec(query,
		branch.DisplayName, branch.Description,
		nullableID(branch.HeadCommit),
		branch.Protected, branch.RequiresReview,
		branch.Status,
		nullableID(branch.OwnedBy),
		branch.ID.String(),
	)

	return err
}

// Delete deletes a branch
func (r *BranchRepository) Delete(id types.ID) error {
	query := `DELETE FROM repository_branches WHERE id = $1 AND protected = false`

	result, err := r.db.Exec(query, id.String())
	if err != nil {
		return err
	}

	rows, err := result.RowsAffected()
	if err != nil {
		return err
	}

	if rows == 0 {
		return fmt.Errorf("branch not found or is protected")
	}

	return nil
}

// List retrieves branches with filtering
func (r *BranchRepository) List(filter versioncontrol.BranchFilter) ([]*versioncontrol.Branch, error) {
	query, args := r.buildListQuery(filter)

	rows, err := r.db.Query(query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	branches := make([]*versioncontrol.Branch, 0)
	for rows.Next() {
		branch, err := r.scanBranch(rows)
		if err != nil {
			return nil, err
		}
		branches = append(branches, branch)
	}

	return branches, nil
}

// GetByName retrieves a branch by name within a repository
func (r *BranchRepository) GetByName(repositoryID types.ID, name string) (*versioncontrol.Branch, error) {
	query := `
		SELECT
			id, repository_id, name, display_name, description,
			base_commit, head_commit,
			branch_type, protected, requires_review, auto_delete_on_merge,
			status, is_default,
			created_by, owned_by,
			created_at, updated_at, merged_at, merged_by
		FROM repository_branches
		WHERE repository_id = $1 AND name = $2
	`

	branch := &versioncontrol.Branch{}
	var baseCommit, headCommit, createdBy, ownedBy, mergedBy sql.NullString
	var description sql.NullString
	var mergedAt sql.NullTime

	err := r.db.QueryRow(query, repositoryID.String(), name).Scan(
		&branch.ID, &branch.RepositoryID, &branch.Name, &branch.DisplayName, &description,
		&baseCommit, &headCommit,
		&branch.BranchType, &branch.Protected, &branch.RequiresReview, &branch.AutoDeleteOnMerge,
		&branch.Status, &branch.IsDefault,
		&createdBy, &ownedBy,
		&branch.CreatedAt, &branch.UpdatedAt, &mergedAt, &mergedBy,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("branch '%s' not found", name)
		}
		return nil, err
	}

	// Handle nullable fields (same as GetByID)
	if description.Valid {
		branch.Description = description.String
	}
	if baseCommit.Valid {
		id := types.FromString(baseCommit.String)
		branch.BaseCommit = &id
	}
	if headCommit.Valid {
		id := types.FromString(headCommit.String)
		branch.HeadCommit = &id
	}
	if createdBy.Valid {
		id := types.FromString(createdBy.String)
		branch.CreatedBy = &id
	}
	if ownedBy.Valid {
		id := types.FromString(ownedBy.String)
		branch.OwnedBy = &id
	}
	if mergedAt.Valid {
		branch.MergedAt = &mergedAt.Time
	}
	if mergedBy.Valid {
		id := types.FromString(mergedBy.String)
		branch.MergedBy = &id
	}

	return branch, nil
}

// GetDefaultBranch retrieves the default branch for a repository
func (r *BranchRepository) GetDefaultBranch(repositoryID types.ID) (*versioncontrol.Branch, error) {
	query := `
		SELECT
			id, repository_id, name, display_name, description,
			base_commit, head_commit,
			branch_type, protected, requires_review, auto_delete_on_merge,
			status, is_default,
			created_by, owned_by,
			created_at, updated_at, merged_at, merged_by
		FROM repository_branches
		WHERE repository_id = $1 AND is_default = true
		LIMIT 1
	`

	branch := &versioncontrol.Branch{}
	var baseCommit, headCommit, createdBy, ownedBy, mergedBy sql.NullString
	var description sql.NullString
	var mergedAt sql.NullTime

	err := r.db.QueryRow(query, repositoryID.String()).Scan(
		&branch.ID, &branch.RepositoryID, &branch.Name, &branch.DisplayName, &description,
		&baseCommit, &headCommit,
		&branch.BranchType, &branch.Protected, &branch.RequiresReview, &branch.AutoDeleteOnMerge,
		&branch.Status, &branch.IsDefault,
		&createdBy, &ownedBy,
		&branch.CreatedAt, &branch.UpdatedAt, &mergedAt, &mergedBy,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("no default branch found")
		}
		return nil, err
	}

	// Handle nullable fields
	if description.Valid {
		branch.Description = description.String
	}
	if baseCommit.Valid {
		id := types.FromString(baseCommit.String)
		branch.BaseCommit = &id
	}
	if headCommit.Valid {
		id := types.FromString(headCommit.String)
		branch.HeadCommit = &id
	}
	if createdBy.Valid {
		id := types.FromString(createdBy.String)
		branch.CreatedBy = &id
	}
	if ownedBy.Valid {
		id := types.FromString(ownedBy.String)
		branch.OwnedBy = &id
	}
	if mergedAt.Valid {
		branch.MergedAt = &mergedAt.Time
	}
	if mergedBy.Valid {
		id := types.FromString(mergedBy.String)
		branch.MergedBy = &id
	}

	return branch, nil
}

// ListActive retrieves all active branches for a repository
func (r *BranchRepository) ListActive(repositoryID types.ID) ([]*versioncontrol.Branch, error) {
	status := versioncontrol.BranchStatusActive
	return r.List(versioncontrol.BranchFilter{
		RepositoryID: &repositoryID,
		Status:       &status,
	})
}

// SetHead updates the head commit of a branch
func (r *BranchRepository) SetHead(branchID, commitID types.ID) error {
	query := `
		UPDATE repository_branches SET
			head_commit = $1,
			updated_at = NOW()
		WHERE id = $2
	`

	_, err := r.db.Exec(query, commitID.String(), branchID.String())
	return err
}

// MarkMerged marks a branch as merged
func (r *BranchRepository) MarkMerged(branchID, mergedBy types.ID) error {
	query := `
		UPDATE repository_branches SET
			status = 'merged',
			merged_at = NOW(),
			merged_by = $1,
			updated_at = NOW()
		WHERE id = $2
	`

	_, err := r.db.Exec(query, mergedBy.String(), branchID.String())
	return err
}

// buildListQuery builds a dynamic list query based on filter
func (r *BranchRepository) buildListQuery(filter versioncontrol.BranchFilter) (string, []any) {
	query := `
		SELECT
			id, repository_id, name, display_name, description,
			base_commit, head_commit,
			branch_type, protected, requires_review, auto_delete_on_merge,
			status, is_default,
			created_by, owned_by,
			created_at, updated_at, merged_at, merged_by
		FROM repository_branches
		WHERE 1=1
	`

	args := make([]any, 0)
	argCount := 1

	if filter.RepositoryID != nil {
		query += fmt.Sprintf(" AND repository_id = $%d", argCount)
		args = append(args, filter.RepositoryID.String())
		argCount++
	}

	if filter.Status != nil {
		query += fmt.Sprintf(" AND status = $%d", argCount)
		args = append(args, *filter.Status)
		argCount++
	}

	if filter.BranchType != nil {
		query += fmt.Sprintf(" AND branch_type = $%d", argCount)
		args = append(args, *filter.BranchType)
		argCount++
	}

	if filter.OwnedBy != nil {
		query += fmt.Sprintf(" AND owned_by = $%d", argCount)
		args = append(args, filter.OwnedBy.String())
		argCount++
	}

	if filter.CreatedBy != nil {
		query += fmt.Sprintf(" AND created_by = $%d", argCount)
		args = append(args, filter.CreatedBy.String())
		argCount++
	}

	if filter.Protected != nil {
		query += fmt.Sprintf(" AND protected = $%d", argCount)
		args = append(args, *filter.Protected)
		argCount++
	}

	query += " ORDER BY is_default DESC, created_at DESC"

	return query, args
}

// scanBranch scans a row into a Branch entity
func (r *BranchRepository) scanBranch(scanner interface {
	Scan(dest ...any) error
}) (*versioncontrol.Branch, error) {
	branch := &versioncontrol.Branch{}
	var baseCommit, headCommit, createdBy, ownedBy, mergedBy sql.NullString
	var description sql.NullString
	var mergedAt sql.NullTime

	err := scanner.Scan(
		&branch.ID, &branch.RepositoryID, &branch.Name, &branch.DisplayName, &description,
		&baseCommit, &headCommit,
		&branch.BranchType, &branch.Protected, &branch.RequiresReview, &branch.AutoDeleteOnMerge,
		&branch.Status, &branch.IsDefault,
		&createdBy, &ownedBy,
		&branch.CreatedAt, &branch.UpdatedAt, &mergedAt, &mergedBy,
	)

	if err != nil {
		return nil, err
	}

	// Handle nullable fields
	if description.Valid {
		branch.Description = description.String
	}
	if baseCommit.Valid {
		id := types.FromString(baseCommit.String)
		branch.BaseCommit = &id
	}
	if headCommit.Valid {
		id := types.FromString(headCommit.String)
		branch.HeadCommit = &id
	}
	if createdBy.Valid {
		id := types.FromString(createdBy.String)
		branch.CreatedBy = &id
	}
	if ownedBy.Valid {
		id := types.FromString(ownedBy.String)
		branch.OwnedBy = &id
	}
	if mergedAt.Valid {
		branch.MergedAt = &mergedAt.Time
	}
	if mergedBy.Valid {
		id := types.FromString(mergedBy.String)
		branch.MergedBy = &id
	}

	return branch, nil
}

// CommitRepository implements enhanced commit repository
type CommitRepository struct {
	db *sql.DB
}

// NewCommitRepository creates a new PostGIS commit repository
func NewCommitRepository(db *sql.DB) *CommitRepository {
	return &CommitRepository{
		db: db,
	}
}

// Create creates a new commit
func (r *CommitRepository) Create(commit *versioncontrol.Commit) error {
	query := `
		INSERT INTO repository_commits (
			id, repository_id, branch_id, version_id,
			commit_hash, short_hash,
			message, description,
			author_name, author_email, author_id,
			parent_commits, merge_commit,
			changes_summary, files_changed, lines_added, lines_deleted,
			tags, metadata, committed_at
		) VALUES (
			$1, $2, $3, $4,
			$5, $6,
			$7, $8,
			$9, $10, $11,
			$12, $13,
			$14, $15, $16, $17,
			$18, $19, $20
		)
	`

	// Convert parent commits to string array
	parentStrs := make([]string, len(commit.ParentCommits))
	for i, parent := range commit.ParentCommits {
		parentStrs[i] = parent.String()
	}

	// Marshal changes summary to JSON
	changesSummaryJSON, err := json.Marshal(commit.ChangesSummary)
	if err != nil {
		return fmt.Errorf("failed to marshal changes summary: %w", err)
	}

	// Marshal metadata to JSON
	metadataJSON, err := json.Marshal(commit.Metadata)
	if err != nil {
		return fmt.Errorf("failed to marshal metadata: %w", err)
	}

	_, err = r.db.Exec(query,
		commit.ID.String(), commit.RepositoryID.String(), commit.BranchID.String(), commit.VersionID.String(),
		commit.CommitHash, commit.ShortHash,
		commit.Message, commit.Description,
		commit.AuthorName, commit.AuthorEmail, nullableID(commit.AuthorID),
		pq.Array(parentStrs), commit.MergeCommit,
		changesSummaryJSON, commit.FilesChanged, commit.LinesAdded, commit.LinesDeleted,
		pq.Array(commit.Tags), metadataJSON, commit.CommittedAt,
	)

	return err
}

// GetByID retrieves a commit by ID
func (r *CommitRepository) GetByID(id types.ID) (*versioncontrol.Commit, error) {
	query := `
		SELECT
			id, repository_id, branch_id, version_id,
			commit_hash, short_hash,
			message, description,
			author_name, author_email, author_id,
			parent_commits, merge_commit,
			changes_summary, files_changed, lines_added, lines_deleted,
			tags, metadata, committed_at
		FROM repository_commits
		WHERE id = $1
	`

	return r.scanCommit(r.db.QueryRow(query, id.String()))
}

// GetByHash retrieves a commit by hash
func (r *CommitRepository) GetByHash(hash string) (*versioncontrol.Commit, error) {
	query := `
		SELECT
			id, repository_id, branch_id, version_id,
			commit_hash, short_hash,
			message, description,
			author_name, author_email, author_id,
			parent_commits, merge_commit,
			changes_summary, files_changed, lines_added, lines_deleted,
			tags, metadata, committed_at
		FROM repository_commits
		WHERE commit_hash = $1 OR short_hash = $2
		LIMIT 1
	`

	return r.scanCommit(r.db.QueryRow(query, hash, hash))
}

// List retrieves commits with filtering
func (r *CommitRepository) List(filter versioncontrol.CommitFilter, limit, offset int) ([]*versioncontrol.Commit, error) {
	query, args := r.buildCommitListQuery(filter, limit, offset)

	rows, err := r.db.Query(query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	commits := make([]*versioncontrol.Commit, 0)
	for rows.Next() {
		commit, err := r.scanCommit(rows)
		if err != nil {
			return nil, err
		}
		commits = append(commits, commit)
	}

	return commits, nil
}

// ListByBranch retrieves commits for a branch
func (r *CommitRepository) ListByBranch(branchID types.ID, limit, offset int) ([]*versioncontrol.Commit, error) {
	return r.List(versioncontrol.CommitFilter{
		BranchID: &branchID,
	}, limit, offset)
}

// GetHistory retrieves full commit history for a branch
func (r *CommitRepository) GetHistory(branchID types.ID) ([]*versioncontrol.Commit, error) {
	return r.ListByBranch(branchID, 10000, 0)
}

// GetParents retrieves parent commits
func (r *CommitRepository) GetParents(commitID types.ID) ([]*versioncontrol.Commit, error) {
	// Get the commit first to get parent IDs
	commit, err := r.GetByID(commitID)
	if err != nil {
		return nil, err
	}

	if len(commit.ParentCommits) == 0 {
		return []*versioncontrol.Commit{}, nil
	}

	// Query parent commits
	parents := make([]*versioncontrol.Commit, 0, len(commit.ParentCommits))
	for _, parentID := range commit.ParentCommits {
		parent, err := r.GetByID(parentID)
		if err != nil {
			// Skip missing parents
			continue
		}
		parents = append(parents, parent)
	}

	return parents, nil
}

// GetChildren retrieves child commits
func (r *CommitRepository) GetChildren(commitID types.ID) ([]*versioncontrol.Commit, error) {
	query := `
		SELECT
			id, repository_id, branch_id, version_id,
			commit_hash, short_hash,
			message, description,
			author_name, author_email, author_id,
			parent_commits, merge_commit,
			changes_summary, files_changed, lines_added, lines_deleted,
			tags, metadata, committed_at
		FROM repository_commits
		WHERE $1 = ANY(parent_commits)
		ORDER BY committed_at
	`

	rows, err := r.db.Query(query, commitID.String())
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	children := make([]*versioncontrol.Commit, 0)
	for rows.Next() {
		commit, err := r.scanCommit(rows)
		if err != nil {
			return nil, err
		}
		children = append(children, commit)
	}

	return children, nil
}

// IsAncestor checks if one commit is an ancestor of another
func (r *CommitRepository) IsAncestor(ancestor, descendant types.ID) (bool, error) {
	// Use recursive CTE (Common Table Expression) for efficient graph traversal
	query := `
		WITH RECURSIVE commit_ancestry AS (
			-- Base case: start with the descendant commit
			SELECT id, parent_commits
			FROM repository_commits
			WHERE id = $1

			UNION ALL

			-- Recursive case: get all parent commits
			SELECT c.id, c.parent_commits
			FROM repository_commits c
			INNER JOIN commit_ancestry ca
				ON c.id = ANY(ca.parent_commits)
		)
		SELECT EXISTS (
			SELECT 1
			FROM commit_ancestry
			WHERE id = $2
		) as is_ancestor
	`

	var isAncestor bool
	err := r.db.QueryRow(query, descendant.String(), ancestor.String()).Scan(&isAncestor)
	if err != nil {
		return false, fmt.Errorf("failed to check ancestry: %w", err)
	}

	return isAncestor, nil
}

// buildCommitListQuery builds a dynamic commit query
func (r *CommitRepository) buildCommitListQuery(filter versioncontrol.CommitFilter, limit, offset int) (string, []any) {
	query := `
		SELECT
			id, repository_id, branch_id, version_id,
			commit_hash, short_hash,
			message, description,
			author_name, author_email, author_id,
			parent_commits, merge_commit,
			changes_summary, files_changed, lines_added, lines_deleted,
			tags, metadata, committed_at
		FROM repository_commits
		WHERE 1=1
	`

	args := make([]any, 0)
	argCount := 1

	if filter.RepositoryID != nil {
		query += fmt.Sprintf(" AND repository_id = $%d", argCount)
		args = append(args, filter.RepositoryID.String())
		argCount++
	}

	if filter.BranchID != nil {
		query += fmt.Sprintf(" AND branch_id = $%d", argCount)
		args = append(args, filter.BranchID.String())
		argCount++
	}

	if filter.AuthorID != nil {
		query += fmt.Sprintf(" AND author_id = $%d", argCount)
		args = append(args, filter.AuthorID.String())
		argCount++
	}

	if filter.Since != nil {
		query += fmt.Sprintf(" AND committed_at >= $%d", argCount)
		args = append(args, *filter.Since)
		argCount++
	}

	if filter.Until != nil {
		query += fmt.Sprintf(" AND committed_at <= $%d", argCount)
		args = append(args, *filter.Until)
		argCount++
	}

	if filter.MergeCommit != nil {
		query += fmt.Sprintf(" AND merge_commit = $%d", argCount)
		args = append(args, *filter.MergeCommit)
		argCount++
	}

	query += " ORDER BY committed_at DESC"

	if limit > 0 {
		query += fmt.Sprintf(" LIMIT $%d", argCount)
		args = append(args, limit)
		argCount++
	}

	if offset > 0 {
		query += fmt.Sprintf(" OFFSET $%d", argCount)
		args = append(args, offset)
	}

	return query, args
}

// scanCommit scans a row into a Commit entity
func (r *CommitRepository) scanCommit(scanner interface {
	Scan(dest ...any) error
}) (*versioncontrol.Commit, error) {
	commit := &versioncontrol.Commit{}
	var authorID sql.NullString
	var description sql.NullString
	var parentCommitsArray pq.StringArray
	var tagsArray pq.StringArray

	err := scanner.Scan(
		&commit.ID, &commit.RepositoryID, &commit.BranchID, &commit.VersionID,
		&commit.CommitHash, &commit.ShortHash,
		&commit.Message, &description,
		&commit.AuthorName, &commit.AuthorEmail, &authorID,
		&parentCommitsArray, &commit.MergeCommit,
		&commit.ChangesSummary, &commit.FilesChanged, &commit.LinesAdded, &commit.LinesDeleted,
		&tagsArray, &commit.Metadata, &commit.CommittedAt,
	)

	if err != nil {
		return nil, err
	}

	// Handle nullable fields
	if description.Valid {
		commit.Description = description.String
	}
	if authorID.Valid {
		id := types.FromString(authorID.String)
		commit.AuthorID = &id
	}

	// Convert parent commits array
	commit.ParentCommits = make([]types.ID, len(parentCommitsArray))
	for i, parentStr := range parentCommitsArray {
		commit.ParentCommits[i] = types.FromString(parentStr)
	}

	// Convert tags array
	commit.Tags = make([]string, len(tagsArray))
	copy(commit.Tags, tagsArray)

	return commit, nil
}
