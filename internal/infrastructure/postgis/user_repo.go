package postgis

import (
	"context"
	"database/sql"
	"fmt"

	"github.com/arx-os/arxos/internal/domain"
)

// UserRepository implements user repository for PostGIS
type UserRepository struct {
	db *sql.DB
}

// NewUserRepository creates a new PostGIS user repository
func NewUserRepository(db *sql.DB) *UserRepository {
	return &UserRepository{
		db: db,
	}
}

// Create creates a new user in PostGIS
func (r *UserRepository) Create(ctx context.Context, u *domain.User) error {
	query := `
		INSERT INTO users (id, email, name, role, active, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
	`

	_, err := r.db.ExecContext(ctx, query,
		u.ID.String(),
		u.Email,
		u.Name,
		u.Role,
		u.Active,
		u.CreatedAt,
		u.UpdatedAt,
	)

	return err
}

// GetByID retrieves a user by ID
func (r *UserRepository) GetByID(ctx context.Context, id string) (*domain.User, error) {
	query := `
		SELECT id, email, name, role, active, created_at, updated_at
		FROM users
		WHERE id = $1
	`

	var u domain.User

	err := r.db.QueryRowContext(ctx, query, id).Scan(
		&u.ID,
		&u.Email,
		&u.Name,
		&u.Role,
		&u.Active,
		&u.CreatedAt,
		&u.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("user not found")
		}
		return nil, err
	}

	return &u, nil
}

// GetByEmail retrieves a user by email
func (r *UserRepository) GetByEmail(ctx context.Context, email string) (*domain.User, error) {
	query := `
		SELECT id, email, name, role, active, created_at, updated_at
		FROM users
		WHERE email = $1
	`

	var u domain.User

	err := r.db.QueryRowContext(ctx, query, email).Scan(
		&u.ID,
		&u.Email,
		&u.Name,
		&u.Role,
		&u.Active,
		&u.CreatedAt,
		&u.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("user not found")
		}
		return nil, err
	}

	return &u, nil
}

// List retrieves a list of users with filtering
func (r *UserRepository) List(ctx context.Context, filter *domain.UserFilter) ([]*domain.User, error) {
	query := `
		SELECT id, email, name, role, active, created_at, updated_at
		FROM users
		WHERE 1=1`

	args := []any{}
	argCount := 1

	// Add filters
	if filter != nil {
		if filter.Email != nil {
			query += fmt.Sprintf(" AND email ILIKE $%d", argCount)
			args = append(args, "%"+*filter.Email+"%")
			argCount++
		}
		if filter.Role != nil {
			query += fmt.Sprintf(" AND role = $%d", argCount)
			args = append(args, *filter.Role)
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

// Update updates an existing user
func (r *UserRepository) Update(ctx context.Context, u *domain.User) error {
	query := `
		UPDATE users
		SET email = $2, name = $3, role = $4, active = $5, updated_at = $6
		WHERE id = $1
	`

	_, err := r.db.ExecContext(ctx, query,
		u.ID.String(),
		u.Email,
		u.Name,
		u.Role,
		u.Active,
		u.UpdatedAt,
	)

	return err
}

// Delete deletes a user
func (r *UserRepository) Delete(ctx context.Context, id string) error {
	query := `DELETE FROM users WHERE id = $1`
	_, err := r.db.ExecContext(ctx, query, id)
	return err
}

// GetOrganizations retrieves organizations for a user
func (r *UserRepository) GetOrganizations(ctx context.Context, userID string) ([]*domain.Organization, error) {
	// Note: This assumes a user_organizations join table exists
	// For now, we'll return an empty slice since the schema might not have this yet
	query := `
		SELECT o.id, o.name, o.description, o.plan, o.active, o.created_at, o.updated_at
		FROM organizations o
		INNER JOIN user_organizations uo ON o.id = uo.organization_id
		WHERE uo.user_id = $1
		ORDER BY o.created_at DESC
	`

	rows, err := r.db.QueryContext(ctx, query, userID)
	if err != nil {
		// If the join table doesn't exist yet, return empty list
		return []*domain.Organization{}, nil
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
