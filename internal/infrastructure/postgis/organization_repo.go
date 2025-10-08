package postgis

import (
	"context"
	"database/sql"
	"fmt"

	"github.com/arx-os/arxos/internal/domain"
)

// OrganizationRepository implements organization repository for PostGIS
type OrganizationRepository struct {
	db *sql.DB
}

// NewOrganizationRepository creates a new PostGIS organization repository
func NewOrganizationRepository(db *sql.DB) *OrganizationRepository {
	return &OrganizationRepository{
		db: db,
	}
}

// Create creates a new organization in PostGIS
func (r *OrganizationRepository) Create(ctx context.Context, org *domain.Organization) error {
	query := `
		INSERT INTO organizations (id, name, description, plan, active, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
	`

	_, err := r.db.ExecContext(ctx, query,
		org.ID.String(),
		org.Name,
		org.Description,
		org.Plan,
		org.Active,
		org.CreatedAt,
		org.UpdatedAt,
	)

	return err
}

// GetByID retrieves an organization by ID
func (r *OrganizationRepository) GetByID(ctx context.Context, id string) (*domain.Organization, error) {
	query := `
		SELECT id, name, description, plan, active, created_at, updated_at
		FROM organizations
		WHERE id = $1
	`

	var org domain.Organization

	err := r.db.QueryRowContext(ctx, query, id).Scan(
		&org.ID,
		&org.Name,
		&org.Description,
		&org.Plan,
		&org.Active,
		&org.CreatedAt,
		&org.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("organization not found")
		}
		return nil, err
	}

	return &org, nil
}

// GetByName retrieves an organization by name
func (r *OrganizationRepository) GetByName(ctx context.Context, name string) (*domain.Organization, error) {
	query := `
		SELECT id, name, description, plan, active, created_at, updated_at
		FROM organizations
		WHERE name = $1
		LIMIT 1
	`

	var org domain.Organization

	err := r.db.QueryRowContext(ctx, query, name).Scan(
		&org.ID,
		&org.Name,
		&org.Description,
		&org.Plan,
		&org.Active,
		&org.CreatedAt,
		&org.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("organization not found")
		}
		return nil, err
	}

	return &org, nil
}

// List retrieves a list of organizations with filtering
func (r *OrganizationRepository) List(ctx context.Context, filter *domain.OrganizationFilter) ([]*domain.Organization, error) {
	query := `
		SELECT id, name, description, plan, active, created_at, updated_at
		FROM organizations
		WHERE 1=1`

	args := []any{}
	argCount := 1

	// Add filters
	if filter != nil {
		if filter.Name != nil {
			query += fmt.Sprintf(" AND name ILIKE $%d", argCount)
			args = append(args, "%"+*filter.Name+"%")
			argCount++
		}
		if filter.Plan != nil {
			query += fmt.Sprintf(" AND plan = $%d", argCount)
			args = append(args, *filter.Plan)
			argCount++
		}
		if filter.Active != nil {
			query += fmt.Sprintf(" AND active = $%d", argCount)
			args = append(args, *filter.Active)
			argCount++
		}
	}

	query += " ORDER BY created_at DESC"

	// Add pagination
	limit := 100
	offset := 0
	if filter != nil {
		if filter.Limit > 0 {
			limit = filter.Limit
		}
		if filter.Offset > 0 {
			offset = filter.Offset
		}
	}

	query += fmt.Sprintf(" LIMIT $%d OFFSET $%d", argCount, argCount+1)
	args = append(args, limit, offset)

	rows, err := r.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var organizations []*domain.Organization

	for rows.Next() {
		var org domain.Organization

		err := rows.Scan(
			&org.ID,
			&org.Name,
			&org.Description,
			&org.Plan,
			&org.Active,
			&org.CreatedAt,
			&org.UpdatedAt,
		)

		if err != nil {
			return nil, err
		}

		organizations = append(organizations, &org)
	}

	return organizations, nil
}

// Update updates an existing organization
func (r *OrganizationRepository) Update(ctx context.Context, org *domain.Organization) error {
	query := `
		UPDATE organizations
		SET name = $2, description = $3, plan = $4, active = $5, updated_at = $6
		WHERE id = $1
	`

	_, err := r.db.ExecContext(ctx, query,
		org.ID.String(),
		org.Name,
		org.Description,
		org.Plan,
		org.Active,
		org.UpdatedAt,
	)

	return err
}

// Delete deletes an organization
func (r *OrganizationRepository) Delete(ctx context.Context, id string) error {
	query := `DELETE FROM organizations WHERE id = $1`
	_, err := r.db.ExecContext(ctx, query, id)
	return err
}

// GetUsers retrieves users for an organization
func (r *OrganizationRepository) GetUsers(ctx context.Context, orgID string) ([]*domain.User, error) {
	// Note: This assumes a user_organizations join table exists
	// For now, we'll return an empty slice since the schema might not have this yet
	query := `
		SELECT u.id, u.email, u.name, u.role, u.active, u.created_at, u.updated_at
		FROM users u
		INNER JOIN user_organizations uo ON u.id = uo.user_id
		WHERE uo.organization_id = $1
		ORDER BY u.created_at DESC
	`

	rows, err := r.db.QueryContext(ctx, query, orgID)
	if err != nil {
		// If the join table doesn't exist yet, return empty list
		return []*domain.User{}, nil
	}
	defer rows.Close()

	var users []*domain.User

	for rows.Next() {
		var u domain.User

		err := rows.Scan(
			&u.ID,
			&u.Email,
			&u.Name,
			&u.Role,
			&u.Active,
			&u.CreatedAt,
			&u.UpdatedAt,
		)

		if err != nil {
			return nil, err
		}

		users = append(users, &u)
	}

	return users, nil
}

// AddUser adds a user to an organization
func (r *OrganizationRepository) AddUser(ctx context.Context, orgID, userID string) error {
	query := `
		INSERT INTO user_organizations (organization_id, user_id, created_at)
		VALUES ($1, $2, NOW())
		ON CONFLICT (organization_id, user_id) DO NOTHING
	`

	_, err := r.db.ExecContext(ctx, query, orgID, userID)
	return err
}

// RemoveUser removes a user from an organization
func (r *OrganizationRepository) RemoveUser(ctx context.Context, orgID, userID string) error {
	query := `
		DELETE FROM user_organizations
		WHERE organization_id = $1 AND user_id = $2
	`

	_, err := r.db.ExecContext(ctx, query, orgID, userID)
	return err
}
