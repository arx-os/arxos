package postgis

import (
	"database/sql"
	"encoding/json"
	"fmt"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/lib/pq"
)

// PullRequestRepository implements pull request repository for PostGIS
type PullRequestRepository struct {
	db *sql.DB
}

// NewPullRequestRepository creates a new PostGIS pull request repository
func NewPullRequestRepository(db *sql.DB) *PullRequestRepository {
	return &PullRequestRepository{
		db: db,
	}
}

// Create creates a new pull request
func (r *PullRequestRepository) Create(pr *domain.PullRequest) error {
	query := `
		INSERT INTO pull_requests (
			id, repository_id, title, description,
			source_branch_id, target_branch_id,
			pr_type, status, priority,
			requires_review, required_reviewers, approved_count,
			assigned_to, assigned_team, auto_assigned,
			estimated_hours, actual_hours, budget_amount, actual_cost,
			due_date, labels, metadata,
			created_by, created_at, updated_at
		) VALUES (
			$1, $2, $3, $4,
			$5, $6,
			$7, $8, $9,
			$10, $11, $12,
			$13, $14, $15,
			$16, $17, $18, $19,
			$20, $21, $22,
			$23, $24, $25
		)
		RETURNING number
	`

	// Marshal metadata to JSON
	metadataJSON, err := json.Marshal(pr.Metadata)
	if err != nil {
		return fmt.Errorf("failed to marshal metadata: %w", err)
	}

	err = r.db.QueryRow(query,
		pr.ID.String(), pr.RepositoryID.String(), pr.Title, pr.Description,
		pr.SourceBranchID.String(), pr.TargetBranchID.String(),
		pr.PRType, pr.Status, pr.Priority,
		pr.RequiresReview, pr.RequiredReviewers, pr.ApprovedCount,
		nullableID(pr.AssignedTo), pr.AssignedTeam, pr.AutoAssigned,
		pr.EstimatedHours, pr.ActualHours, pr.BudgetAmount, pr.ActualCost,
		pr.DueDate, pq.Array(pr.Labels), metadataJSON,
		pr.CreatedBy.String(), pr.CreatedAt, pr.UpdatedAt,
	).Scan(&pr.Number)

	return err
}

// GetByID retrieves a pull request by ID
func (r *PullRequestRepository) GetByID(id types.ID) (*domain.PullRequest, error) {
	query := `
		SELECT
			id, repository_id, number, title, description,
			source_branch_id, target_branch_id,
			pr_type, status, priority,
			requires_review, required_reviewers, approved_count,
			assigned_to, assigned_team, auto_assigned,
			estimated_hours, actual_hours, budget_amount, actual_cost,
			due_date, labels, metadata,
			created_by, created_at, updated_at, closed_at, merged_at, merged_by
		FROM pull_requests
		WHERE id = $1
	`

	return r.scanPR(r.db.QueryRow(query, id.String()))
}

// GetByNumber retrieves a pull request by number
func (r *PullRequestRepository) GetByNumber(repositoryID types.ID, number int) (*domain.PullRequest, error) {
	query := `
		SELECT
			id, repository_id, number, title, description,
			source_branch_id, target_branch_id,
			pr_type, status, priority,
			requires_review, required_reviewers, approved_count,
			assigned_to, assigned_team, auto_assigned,
			estimated_hours, actual_hours, budget_amount, actual_cost,
			due_date, labels, metadata,
			created_by, created_at, updated_at, closed_at, merged_at, merged_by
		FROM pull_requests
		WHERE repository_id = $1 AND number = $2
	`

	return r.scanPR(r.db.QueryRow(query, repositoryID.String(), number))
}

// Update updates an existing pull request
func (r *PullRequestRepository) Update(pr *domain.PullRequest) error {
	query := `
		UPDATE pull_requests SET
			title = $1,
			description = $2,
			status = $3,
			priority = $4,
			assigned_to = $5,
			assigned_team = $6,
			approved_count = $7,
			actual_hours = $8,
			actual_cost = $9,
			due_date = $10,
			labels = $11,
			metadata = $12,
			updated_at = NOW()
		WHERE id = $13
	`

	// Marshal metadata to JSON
	metadataJSON, err := json.Marshal(pr.Metadata)
	if err != nil {
		return fmt.Errorf("failed to marshal metadata: %w", err)
	}

	_, err = r.db.Exec(query,
		pr.Title, pr.Description,
		pr.Status, pr.Priority,
		nullableID(pr.AssignedTo), pr.AssignedTeam,
		pr.ApprovedCount,
		pr.ActualHours, pr.ActualCost,
		pr.DueDate, pq.Array(pr.Labels), metadataJSON,
		pr.ID.String(),
	)

	return err
}

// Delete deletes a pull request
func (r *PullRequestRepository) Delete(id types.ID) error {
	query := `DELETE FROM pull_requests WHERE id = $1`

	result, err := r.db.Exec(query, id.String())
	if err != nil {
		return err
	}

	rows, err := result.RowsAffected()
	if err != nil {
		return err
	}

	if rows == 0 {
		return fmt.Errorf("pull request not found")
	}

	return nil
}

// List retrieves pull requests with filtering
func (r *PullRequestRepository) List(filter domain.PRFilter, limit, offset int) ([]*domain.PullRequest, error) {
	query, args := r.buildListQuery(filter, limit, offset)

	rows, err := r.db.Query(query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	prs := make([]*domain.PullRequest, 0)
	for rows.Next() {
		pr, err := r.scanPR(rows)
		if err != nil {
			return nil, err
		}
		prs = append(prs, pr)
	}

	return prs, nil
}

// Count counts pull requests matching filter
func (r *PullRequestRepository) Count(filter domain.PRFilter) (int, error) {
	query, args := r.buildCountQuery(filter)

	var count int
	err := r.db.QueryRow(query, args...).Scan(&count)
	return count, err
}

// ListOpen retrieves all open PRs for a repository
func (r *PullRequestRepository) ListOpen(repositoryID types.ID) ([]*domain.PullRequest, error) {
	status := domain.PRStatusOpen
	return r.List(domain.PRFilter{
		RepositoryID: &repositoryID,
		Status:       &status,
	}, 100, 0)
}

// ListAssigned retrieves all PRs assigned to a user
func (r *PullRequestRepository) ListAssigned(userID types.ID) ([]*domain.PullRequest, error) {
	return r.List(domain.PRFilter{
		AssignedTo: &userID,
	}, 100, 0)
}

// ListOverdue retrieves overdue PRs
func (r *PullRequestRepository) ListOverdue(repositoryID types.ID) ([]*domain.PullRequest, error) {
	return r.List(domain.PRFilter{
		RepositoryID: &repositoryID,
		Overdue:      true,
	}, 100, 0)
}

// UpdateStatus updates the status of a PR
func (r *PullRequestRepository) UpdateStatus(id types.ID, status domain.PRStatus) error {
	query := `
		UPDATE pull_requests SET
			status = $1,
			updated_at = NOW()
		WHERE id = $2
	`

	_, err := r.db.Exec(query, status, id.String())
	return err
}

// Merge marks a PR as merged
func (r *PullRequestRepository) Merge(id types.ID, mergedBy types.ID) error {
	query := `
		UPDATE pull_requests SET
			status = 'merged',
			merged_at = NOW(),
			merged_by = $1,
			updated_at = NOW()
		WHERE id = $2
	`

	_, err := r.db.Exec(query, mergedBy.String(), id.String())
	return err
}

// Close closes a PR without merging
func (r *PullRequestRepository) Close(id types.ID) error {
	query := `
		UPDATE pull_requests SET
			status = 'closed',
			closed_at = NOW(),
			updated_at = NOW()
		WHERE id = $1
	`

	_, err := r.db.Exec(query, id.String())
	return err
}

// buildListQuery builds a dynamic PR list query
func (r *PullRequestRepository) buildListQuery(filter domain.PRFilter, limit, offset int) (string, []interface{}) {
	query := `
		SELECT
			id, repository_id, number, title, description,
			source_branch_id, target_branch_id,
			pr_type, status, priority,
			requires_review, required_reviewers, approved_count,
			assigned_to, assigned_team, auto_assigned,
			estimated_hours, actual_hours, budget_amount, actual_cost,
			due_date, labels, metadata,
			created_by, created_at, updated_at, closed_at, merged_at, merged_by
		FROM pull_requests
		WHERE 1=1
	`

	args := make([]interface{}, 0)
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

	if filter.PRType != nil {
		query += fmt.Sprintf(" AND pr_type = $%d", argCount)
		args = append(args, *filter.PRType)
		argCount++
	}

	if filter.Priority != nil {
		query += fmt.Sprintf(" AND priority = $%d", argCount)
		args = append(args, *filter.Priority)
		argCount++
	}

	if filter.AssignedTo != nil {
		query += fmt.Sprintf(" AND assigned_to = $%d", argCount)
		args = append(args, filter.AssignedTo.String())
		argCount++
	}

	if filter.CreatedBy != nil {
		query += fmt.Sprintf(" AND created_by = $%d", argCount)
		args = append(args, filter.CreatedBy.String())
		argCount++
	}

	if filter.Label != "" {
		query += fmt.Sprintf(" AND $%d = ANY(labels)", argCount)
		args = append(args, filter.Label)
		argCount++
	}

	if filter.Overdue {
		query += " AND due_date < NOW() AND status NOT IN ('merged', 'closed')"
	}

	query += " ORDER BY created_at DESC"

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

// buildCountQuery builds a count query
func (r *PullRequestRepository) buildCountQuery(filter domain.PRFilter) (string, []interface{}) {
	query := `SELECT COUNT(*) FROM pull_requests WHERE 1=1`

	args := make([]interface{}, 0)
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

	if filter.Overdue {
		query += " AND due_date < NOW() AND status NOT IN ('merged', 'closed')"
	}

	return query, args
}

// scanPR scans a row into a PullRequest entity
func (r *PullRequestRepository) scanPR(scanner interface {
	Scan(dest ...interface{}) error
}) (*domain.PullRequest, error) {
	pr := &domain.PullRequest{}
	var description, assignedTo, assignedTeam sql.NullString
	var mergedBy sql.NullString
	var estimatedHours, actualHours, budgetAmount, actualCost sql.NullFloat64
	var dueDate, closedAt, mergedAt sql.NullTime
	var labelsArray pq.StringArray
	var metadataJSON []byte

	err := scanner.Scan(
		&pr.ID, &pr.RepositoryID, &pr.Number, &pr.Title, &description,
		&pr.SourceBranchID, &pr.TargetBranchID,
		&pr.PRType, &pr.Status, &pr.Priority,
		&pr.RequiresReview, &pr.RequiredReviewers, &pr.ApprovedCount,
		&assignedTo, &assignedTeam, &pr.AutoAssigned,
		&estimatedHours, &actualHours, &budgetAmount, &actualCost,
		&dueDate, &labelsArray, &metadataJSON,
		&pr.CreatedBy, &pr.CreatedAt, &pr.UpdatedAt, &closedAt, &mergedAt, &mergedBy,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("pull request not found")
		}
		return nil, err
	}

	// Unmarshal metadata JSON
	if len(metadataJSON) > 0 {
		if err := json.Unmarshal(metadataJSON, &pr.Metadata); err != nil {
			return nil, fmt.Errorf("failed to unmarshal metadata: %w", err)
		}
	} else {
		pr.Metadata = make(map[string]interface{})
	}

	// Handle nullable fields
	if description.Valid {
		pr.Description = description.String
	}
	if assignedTo.Valid {
		id := types.FromString(assignedTo.String)
		pr.AssignedTo = &id
	}
	if assignedTeam.Valid {
		pr.AssignedTeam = assignedTeam.String
	}
	if estimatedHours.Valid {
		pr.EstimatedHours = &estimatedHours.Float64
	}
	if actualHours.Valid {
		pr.ActualHours = &actualHours.Float64
	}
	if budgetAmount.Valid {
		pr.BudgetAmount = &budgetAmount.Float64
	}
	if actualCost.Valid {
		pr.ActualCost = &actualCost.Float64
	}
	if dueDate.Valid {
		pr.DueDate = &dueDate.Time
	}
	if closedAt.Valid {
		pr.ClosedAt = &closedAt.Time
	}
	if mergedAt.Valid {
		pr.MergedAt = &mergedAt.Time
	}
	if mergedBy.Valid {
		id := types.FromString(mergedBy.String)
		pr.MergedBy = &id
	}

	// Convert labels array
	pr.Labels = make([]string, len(labelsArray))
	copy(pr.Labels, labelsArray)

	return pr, nil
}
