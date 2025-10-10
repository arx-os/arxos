package postgis

import (
	"database/sql"
	"fmt"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
)

// IssueRepository implements issue repository for PostGIS
type IssueRepository struct {
	db *sql.DB
}

// NewIssueRepository creates a new PostGIS issue repository
func NewIssueRepository(db *sql.DB) *IssueRepository {
	return &IssueRepository{
		db: db,
	}
}

// Create creates a new issue
func (r *IssueRepository) Create(issue *domain.Issue) error {
	query := `
		INSERT INTO issues (
			id, repository_id, title, body,
			building_id, floor_id, room_id, equipment_id, bas_point_id,
			location_description,
			issue_type, status, priority,
			assigned_to, assigned_team, auto_assigned,
			branch_id, pr_id,
			reported_by, reported_via,
			metadata, created_at, updated_at
		) VALUES (
			$1, $2, $3, $4,
			$5, $6, $7, $8, $9,
			$10,
			$11, $12, $13,
			$14, $15, $16,
			$17, $18,
			$19, $20,
			$21, $22, $23
		)
		RETURNING number
	`

	err := r.db.QueryRow(query,
		issue.ID.String(), issue.RepositoryID.String(), issue.Title, issue.Body,
		nullableID(issue.BuildingID), nullableID(issue.FloorID), nullableID(issue.RoomID),
		nullableID(issue.EquipmentID), nullableID(issue.BASPointID),
		issue.LocationDescription,
		issue.IssueType, issue.Status, issue.Priority,
		nullableID(issue.AssignedTo), issue.AssignedTeam, issue.AutoAssigned,
		nullableID(issue.BranchID), nullableID(issue.PRID),
		issue.ReportedBy.String(), nullableReportedVia(issue.ReportedVia),
		issue.Metadata, issue.CreatedAt, issue.UpdatedAt,
	).Scan(&issue.Number)

	return err
}

// GetByID retrieves an issue by ID
func (r *IssueRepository) GetByID(id types.ID) (*domain.Issue, error) {
	query := `
		SELECT 
			id, repository_id, number, title, body,
			building_id, floor_id, room_id, equipment_id, bas_point_id,
			location_description,
			issue_type, status, priority,
			assigned_to, assigned_team, auto_assigned,
			branch_id, pr_id,
			reported_by, reported_via,
			resolved_by, resolved_at, resolution_notes,
			verified_by_reporter, verified_at,
			metadata, created_at, updated_at, closed_at
		FROM issues
		WHERE id = $1
	`

	return r.scanIssue(r.db.QueryRow(query, id.String()))
}

// GetByNumber retrieves an issue by number
func (r *IssueRepository) GetByNumber(repositoryID types.ID, number int) (*domain.Issue, error) {
	query := `
		SELECT 
			id, repository_id, number, title, body,
			building_id, floor_id, room_id, equipment_id, bas_point_id,
			location_description,
			issue_type, status, priority,
			assigned_to, assigned_team, auto_assigned,
			branch_id, pr_id,
			reported_by, reported_via,
			resolved_by, resolved_at, resolution_notes,
			verified_by_reporter, verified_at,
			metadata, created_at, updated_at, closed_at
		FROM issues
		WHERE repository_id = $1 AND number = $2
	`

	return r.scanIssue(r.db.QueryRow(query, repositoryID.String(), number))
}

// Update updates an existing issue
func (r *IssueRepository) Update(issue *domain.Issue) error {
	query := `
		UPDATE issues SET
			title = $1,
			body = $2,
			status = $3,
			priority = $4,
			assigned_to = $5,
			assigned_team = $6,
			resolution_notes = $7,
			verified_by_reporter = $8,
			metadata = $9,
			updated_at = NOW()
		WHERE id = $10
	`

	_, err := r.db.Exec(query,
		issue.Title, issue.Body,
		issue.Status, issue.Priority,
		nullableID(issue.AssignedTo), issue.AssignedTeam,
		issue.ResolutionNotes,
		issue.VerifiedByReporter,
		issue.Metadata,
		issue.ID.String(),
	)

	return err
}

// Delete deletes an issue
func (r *IssueRepository) Delete(id types.ID) error {
	query := `DELETE FROM issues WHERE id = $1`

	result, err := r.db.Exec(query, id.String())
	if err != nil {
		return err
	}

	rows, err := result.RowsAffected()
	if err != nil {
		return err
	}

	if rows == 0 {
		return fmt.Errorf("issue not found")
	}

	return nil
}

// List retrieves issues with filtering
func (r *IssueRepository) List(filter domain.IssueFilter, limit, offset int) ([]*domain.Issue, error) {
	query, args := r.buildListQuery(filter, limit, offset)

	rows, err := r.db.Query(query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	issues := make([]*domain.Issue, 0)
	for rows.Next() {
		issue, err := r.scanIssue(rows)
		if err != nil {
			return nil, err
		}
		issues = append(issues, issue)
	}

	return issues, nil
}

// Count counts issues matching filter
func (r *IssueRepository) Count(filter domain.IssueFilter) (int, error) {
	query, args := r.buildCountQuery(filter)

	var count int
	err := r.db.QueryRow(query, args...).Scan(&count)
	return count, err
}

// ListOpen retrieves all open issues for a repository
func (r *IssueRepository) ListOpen(repositoryID types.ID) ([]*domain.Issue, error) {
	status := domain.IssueStatusOpen
	return r.List(domain.IssueFilter{
		RepositoryID: &repositoryID,
		Status:       &status,
	}, 100, 0)
}

// ListAssigned retrieves all issues assigned to a user
func (r *IssueRepository) ListAssigned(userID types.ID) ([]*domain.Issue, error) {
	return r.List(domain.IssueFilter{
		AssignedTo: &userID,
	}, 100, 0)
}

// ListByRoom retrieves all issues for a room
func (r *IssueRepository) ListByRoom(roomID types.ID) ([]*domain.Issue, error) {
	return r.List(domain.IssueFilter{
		RoomID: &roomID,
	}, 100, 0)
}

// ListByEquipment retrieves all issues for equipment
func (r *IssueRepository) ListByEquipment(equipmentID types.ID) ([]*domain.Issue, error) {
	return r.List(domain.IssueFilter{
		EquipmentID: &equipmentID,
	}, 100, 0)
}

// ListUnverified retrieves resolved but unverified issues
func (r *IssueRepository) ListUnverified(repositoryID types.ID) ([]*domain.Issue, error) {
	return r.List(domain.IssueFilter{
		RepositoryID: &repositoryID,
		Unverified:   true,
	}, 100, 0)
}

// UpdateStatus updates the status of an issue
func (r *IssueRepository) UpdateStatus(id types.ID, status domain.IssueStatus) error {
	query := `UPDATE issues SET status = $1, updated_at = NOW() WHERE id = $2`
	_, err := r.db.Exec(query, status, id.String())
	return err
}

// Resolve marks an issue as resolved
func (r *IssueRepository) Resolve(id types.ID, resolvedBy types.ID, notes string) error {
	query := `
		UPDATE issues SET
			status = 'resolved',
			resolved_by = $1,
			resolved_at = NOW(),
			resolution_notes = $2,
			updated_at = NOW()
		WHERE id = $3
	`

	_, err := r.db.Exec(query, resolvedBy.String(), notes, id.String())
	return err
}

// Verify marks an issue as verified by reporter
func (r *IssueRepository) Verify(id types.ID, verifiedBy types.ID) error {
	query := `
		UPDATE issues SET
			verified_by_reporter = true,
			verified_at = NOW(),
			updated_at = NOW()
		WHERE id = $1 AND reported_by = $2
	`

	_, err := r.db.Exec(query, id.String(), verifiedBy.String())
	return err
}

// Close closes an issue
func (r *IssueRepository) Close(id types.ID) error {
	query := `
		UPDATE issues SET
			status = 'closed',
			closed_at = NOW(),
			updated_at = NOW()
		WHERE id = $1
	`

	_, err := r.db.Exec(query, id.String())
	return err
}

// Reopen reopens a closed issue
func (r *IssueRepository) Reopen(id types.ID) error {
	query := `
		UPDATE issues SET
			status = 'open',
			closed_at = NULL,
			updated_at = NOW()
		WHERE id = $1
	`

	_, err := r.db.Exec(query, id.String())
	return err
}

// buildListQuery builds a dynamic issue list query
func (r *IssueRepository) buildListQuery(filter domain.IssueFilter, limit, offset int) (string, []interface{}) {
	query := `
		SELECT 
			id, repository_id, number, title, body,
			building_id, floor_id, room_id, equipment_id, bas_point_id,
			location_description,
			issue_type, status, priority,
			assigned_to, assigned_team, auto_assigned,
			branch_id, pr_id,
			reported_by, reported_via,
			resolved_by, resolved_at, resolution_notes,
			verified_by_reporter, verified_at,
			metadata, created_at, updated_at, closed_at
		FROM issues
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

	if filter.IssueType != nil {
		query += fmt.Sprintf(" AND issue_type = $%d", argCount)
		args = append(args, *filter.IssueType)
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

	if filter.ReportedBy != nil {
		query += fmt.Sprintf(" AND reported_by = $%d", argCount)
		args = append(args, filter.ReportedBy.String())
		argCount++
	}

	if filter.BuildingID != nil {
		query += fmt.Sprintf(" AND building_id = $%d", argCount)
		args = append(args, filter.BuildingID.String())
		argCount++
	}

	if filter.RoomID != nil {
		query += fmt.Sprintf(" AND room_id = $%d", argCount)
		args = append(args, filter.RoomID.String())
		argCount++
	}

	if filter.EquipmentID != nil {
		query += fmt.Sprintf(" AND equipment_id = $%d", argCount)
		args = append(args, filter.EquipmentID.String())
		argCount++
	}

	if filter.ReportedVia != nil {
		query += fmt.Sprintf(" AND reported_via = $%d", argCount)
		args = append(args, *filter.ReportedVia)
		argCount++
	}

	if filter.Unverified {
		query += " AND status = 'resolved' AND verified_by_reporter = false"
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
func (r *IssueRepository) buildCountQuery(filter domain.IssueFilter) (string, []interface{}) {
	query := `SELECT COUNT(*) FROM issues WHERE 1=1`

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

	if filter.Priority != nil {
		query += fmt.Sprintf(" AND priority = $%d", argCount)
		args = append(args, *filter.Priority)
		argCount++
	}

	if filter.Unverified {
		query += " AND status = 'resolved' AND verified_by_reporter = false"
	}

	return query, args
}

// scanIssue scans a row into an Issue entity
func (r *IssueRepository) scanIssue(scanner interface {
	Scan(dest ...interface{}) error
}) (*domain.Issue, error) {
	issue := &domain.Issue{}
	var body, locationDesc sql.NullString
	var buildingID, floorID, roomID, equipmentID, basPointID sql.NullString
	var assignedTo, assignedTeam, branchID, prID sql.NullString
	var reportedVia sql.NullString
	var resolvedBy sql.NullString
	var resolvedAt, verifiedAt, closedAt sql.NullTime
	var resolutionNotes sql.NullString

	err := scanner.Scan(
		&issue.ID, &issue.RepositoryID, &issue.Number, &issue.Title, &body,
		&buildingID, &floorID, &roomID, &equipmentID, &basPointID,
		&locationDesc,
		&issue.IssueType, &issue.Status, &issue.Priority,
		&assignedTo, &assignedTeam, &issue.AutoAssigned,
		&branchID, &prID,
		&issue.ReportedBy, &reportedVia,
		&resolvedBy, &resolvedAt, &resolutionNotes,
		&issue.VerifiedByReporter, &verifiedAt,
		&issue.Metadata, &issue.CreatedAt, &issue.UpdatedAt, &closedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("issue not found")
		}
		return nil, err
	}

	// Handle nullable fields
	if body.Valid {
		issue.Body = body.String
	}
	if locationDesc.Valid {
		issue.LocationDescription = locationDesc.String
	}
	if buildingID.Valid {
		id := types.FromString(buildingID.String)
		issue.BuildingID = &id
	}
	if floorID.Valid {
		id := types.FromString(floorID.String)
		issue.FloorID = &id
	}
	if roomID.Valid {
		id := types.FromString(roomID.String)
		issue.RoomID = &id
	}
	if equipmentID.Valid {
		id := types.FromString(equipmentID.String)
		issue.EquipmentID = &id
	}
	if basPointID.Valid {
		id := types.FromString(basPointID.String)
		issue.BASPointID = &id
	}
	if assignedTo.Valid {
		id := types.FromString(assignedTo.String)
		issue.AssignedTo = &id
	}
	if assignedTeam.Valid {
		issue.AssignedTeam = assignedTeam.String
	}
	if branchID.Valid {
		id := types.FromString(branchID.String)
		issue.BranchID = &id
	}
	if prID.Valid {
		id := types.FromString(prID.String)
		issue.PRID = &id
	}
	if reportedVia.Valid {
		via := domain.ReportedVia(reportedVia.String)
		issue.ReportedVia = &via
	}
	if resolvedBy.Valid {
		id := types.FromString(resolvedBy.String)
		issue.ResolvedBy = &id
	}
	if resolvedAt.Valid {
		issue.ResolvedAt = &resolvedAt.Time
	}
	if resolutionNotes.Valid {
		issue.ResolutionNotes = resolutionNotes.String
	}
	if verifiedAt.Valid {
		issue.VerifiedAt = &verifiedAt.Time
	}
	if closedAt.Valid {
		issue.ClosedAt = &closedAt.Time
	}

	return issue, nil
}

// nullableReportedVia converts a pointer to ReportedVia to sql.NullString
func nullableReportedVia(via *domain.ReportedVia) sql.NullString {
	if via == nil {
		return sql.NullString{Valid: false}
	}
	return sql.NullString{String: string(*via), Valid: true}
}

