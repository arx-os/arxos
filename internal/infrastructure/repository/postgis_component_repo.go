package repository

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"strings"

	"github.com/arx-os/arxos/internal/domain/component"
)

// PostGISComponentRepository implements component.ComponentRepository for PostGIS
type PostGISComponentRepository struct {
	db *sql.DB
}

// NewPostGISComponentRepository creates a new PostGIS component repository
func NewPostGISComponentRepository(db *sql.DB) component.ComponentRepository {
	return &PostGISComponentRepository{
		db: db,
	}
}

// Create creates a new component
func (r *PostGISComponentRepository) Create(ctx context.Context, comp *component.Component) error {
	query := `
		INSERT INTO components (
			id, name, type, path, location_json, properties_json, 
			relations_json, status, version, created_at, updated_at, 
			created_by, updated_by
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
	`

	// Serialize location to JSON
	locationJSON, err := json.Marshal(comp.Location)
	if err != nil {
		return fmt.Errorf("failed to marshal location: %w", err)
	}

	// Serialize properties to JSON
	propertiesJSON, err := json.Marshal(comp.Properties)
	if err != nil {
		return fmt.Errorf("failed to marshal properties: %w", err)
	}

	// Serialize relations to JSON
	relationsJSON, err := json.Marshal(comp.Relations)
	if err != nil {
		return fmt.Errorf("failed to marshal relations: %w", err)
	}

	_, err = r.db.ExecContext(ctx, query,
		comp.ID,
		comp.Name,
		string(comp.Type),
		comp.Path,
		locationJSON,
		propertiesJSON,
		relationsJSON,
		string(comp.Status),
		comp.Version,
		comp.CreatedAt,
		comp.UpdatedAt,
		comp.CreatedBy,
		comp.UpdatedBy,
	)

	return err
}

// GetByID retrieves a component by ID
func (r *PostGISComponentRepository) GetByID(ctx context.Context, id string) (*component.Component, error) {
	query := `
		SELECT id, name, type, path, location_json, properties_json, 
		       relations_json, status, version, created_at, updated_at, 
		       created_by, updated_by
		FROM components 
		WHERE id = $1
	`

	row := r.db.QueryRowContext(ctx, query, id)
	return r.scanComponent(row)
}

// GetByPath retrieves a component by path
func (r *PostGISComponentRepository) GetByPath(ctx context.Context, path string) (*component.Component, error) {
	query := `
		SELECT id, name, type, path, location_json, properties_json, 
		       relations_json, status, version, created_at, updated_at, 
		       created_by, updated_by
		FROM components 
		WHERE path = $1
	`

	row := r.db.QueryRowContext(ctx, query, path)
	return r.scanComponent(row)
}

// GetByType retrieves components by type
func (r *PostGISComponentRepository) GetByType(ctx context.Context, compType component.ComponentType) ([]*component.Component, error) {
	query := `
		SELECT id, name, type, path, location_json, properties_json, 
		       relations_json, status, version, created_at, updated_at, 
		       created_by, updated_by
		FROM components 
		WHERE type = $1
		ORDER BY created_at DESC
	`

	rows, err := r.db.QueryContext(ctx, query, string(compType))
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	return r.scanComponents(rows)
}

// GetByLocation retrieves components within a location range
func (r *PostGISComponentRepository) GetByLocation(ctx context.Context, location component.Location, radius float64) ([]*component.Component, error) {
	query := `
		SELECT id, name, type, path, location_json, properties_json, 
		       relations_json, status, version, created_at, updated_at, 
		       created_by, updated_by
		FROM components 
		WHERE ST_DWithin(
			ST_SetSRID(ST_MakePoint((location_json->>'x')::float, (location_json->>'y')::float, (location_json->>'z')::float), 4326),
			ST_SetSRID(ST_MakePoint($1, $2, $3), 4326),
			$4
		)
		ORDER BY ST_Distance(
			ST_SetSRID(ST_MakePoint((location_json->>'x')::float, (location_json->>'y')::float, (location_json->>'z')::float), 4326),
			ST_SetSRID(ST_MakePoint($1, $2, $3), 4326)
		)
	`

	rows, err := r.db.QueryContext(ctx, query, location.X, location.Y, location.Z, radius)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	return r.scanComponents(rows)
}

// Update updates an existing component
func (r *PostGISComponentRepository) Update(ctx context.Context, comp *component.Component) error {
	query := `
		UPDATE components SET
			name = $2,
			type = $3,
			path = $4,
			location_json = $5,
			properties_json = $6,
			relations_json = $7,
			status = $8,
			version = $9,
			updated_at = $10,
			updated_by = $11
		WHERE id = $1
	`

	// Serialize location to JSON
	locationJSON, err := json.Marshal(comp.Location)
	if err != nil {
		return fmt.Errorf("failed to marshal location: %w", err)
	}

	// Serialize properties to JSON
	propertiesJSON, err := json.Marshal(comp.Properties)
	if err != nil {
		return fmt.Errorf("failed to marshal properties: %w", err)
	}

	// Serialize relations to JSON
	relationsJSON, err := json.Marshal(comp.Relations)
	if err != nil {
		return fmt.Errorf("failed to marshal relations: %w", err)
	}

	_, err = r.db.ExecContext(ctx, query,
		comp.ID,
		comp.Name,
		string(comp.Type),
		comp.Path,
		locationJSON,
		propertiesJSON,
		relationsJSON,
		string(comp.Status),
		comp.Version,
		comp.UpdatedAt,
		comp.UpdatedBy,
	)

	return err
}

// Delete deletes a component by ID
func (r *PostGISComponentRepository) Delete(ctx context.Context, id string) error {
	query := `DELETE FROM components WHERE id = $1`
	_, err := r.db.ExecContext(ctx, query, id)
	return err
}

// List retrieves components with pagination and filtering
func (r *PostGISComponentRepository) List(ctx context.Context, filter component.ComponentFilter) ([]*component.Component, error) {
	query := `SELECT id, name, type, path, location_json, properties_json, 
		       relations_json, status, version, created_at, updated_at, 
		       created_by, updated_by FROM components`

	args := []interface{}{}
	argIndex := 1
	conditions := []string{}

	// Add filters
	if filter.Type != nil {
		conditions = append(conditions, fmt.Sprintf("type = $%d", argIndex))
		args = append(args, string(*filter.Type))
		argIndex++
	}

	if filter.Status != nil {
		conditions = append(conditions, fmt.Sprintf("status = $%d", argIndex))
		args = append(args, string(*filter.Status))
		argIndex++
	}

	if filter.Building != "" {
		conditions = append(conditions, fmt.Sprintf("location_json->>'building' = $%d", argIndex))
		args = append(args, filter.Building)
		argIndex++
	}

	if filter.Floor != "" {
		conditions = append(conditions, fmt.Sprintf("location_json->>'floor' = $%d", argIndex))
		args = append(args, filter.Floor)
		argIndex++
	}

	if filter.Room != "" {
		conditions = append(conditions, fmt.Sprintf("location_json->>'room' = $%d", argIndex))
		args = append(args, filter.Room)
		argIndex++
	}

	if filter.PathPrefix != "" {
		conditions = append(conditions, fmt.Sprintf("path LIKE $%d", argIndex))
		args = append(args, filter.PathPrefix+"%")
		argIndex++
	}

	if filter.CreatedBy != "" {
		conditions = append(conditions, fmt.Sprintf("created_by = $%d", argIndex))
		args = append(args, filter.CreatedBy)
		argIndex++
	}

	// Add WHERE clause if conditions exist
	if len(conditions) > 0 {
		query += " WHERE " + strings.Join(conditions, " AND ")
	}

	// Add ORDER BY
	query += " ORDER BY created_at DESC"

	// Add LIMIT and OFFSET
	if filter.Limit > 0 {
		query += fmt.Sprintf(" LIMIT $%d", argIndex)
		args = append(args, filter.Limit)
		argIndex++
	}

	if filter.Offset > 0 {
		query += fmt.Sprintf(" OFFSET $%d", argIndex)
		args = append(args, filter.Offset)
		argIndex++
	}

	rows, err := r.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	return r.scanComponents(rows)
}

// Count returns the total count of components matching the filter
func (r *PostGISComponentRepository) Count(ctx context.Context, filter component.ComponentFilter) (int64, error) {
	query := `SELECT COUNT(*) FROM components`

	args := []interface{}{}
	argIndex := 1
	conditions := []string{}

	// Add filters (same logic as List)
	if filter.Type != nil {
		conditions = append(conditions, fmt.Sprintf("type = $%d", argIndex))
		args = append(args, string(*filter.Type))
		argIndex++
	}

	if filter.Status != nil {
		conditions = append(conditions, fmt.Sprintf("status = $%d", argIndex))
		args = append(args, string(*filter.Status))
		argIndex++
	}

	if filter.Building != "" {
		conditions = append(conditions, fmt.Sprintf("location_json->>'building' = $%d", argIndex))
		args = append(args, filter.Building)
		argIndex++
	}

	if filter.Floor != "" {
		conditions = append(conditions, fmt.Sprintf("location_json->>'floor' = $%d", argIndex))
		args = append(args, filter.Floor)
		argIndex++
	}

	if filter.Room != "" {
		conditions = append(conditions, fmt.Sprintf("location_json->>'room' = $%d", argIndex))
		args = append(args, filter.Room)
		argIndex++
	}

	if filter.PathPrefix != "" {
		conditions = append(conditions, fmt.Sprintf("path LIKE $%d", argIndex))
		args = append(args, filter.PathPrefix+"%")
		argIndex++
	}

	if filter.CreatedBy != "" {
		conditions = append(conditions, fmt.Sprintf("created_by = $%d", argIndex))
		args = append(args, filter.CreatedBy)
		argIndex++
	}

	// Add WHERE clause if conditions exist
	if len(conditions) > 0 {
		query += " WHERE " + strings.Join(conditions, " AND ")
	}

	var count int64
	err := r.db.QueryRowContext(ctx, query, args...).Scan(&count)
	return count, err
}

// Helper methods

func (r *PostGISComponentRepository) scanComponent(row *sql.Row) (*component.Component, error) {
	var comp component.Component
	var typeStr, statusStr string
	var locationJSON, propertiesJSON, relationsJSON []byte

	err := row.Scan(
		&comp.ID,
		&comp.Name,
		&typeStr,
		&comp.Path,
		&locationJSON,
		&propertiesJSON,
		&relationsJSON,
		&statusStr,
		&comp.Version,
		&comp.CreatedAt,
		&comp.UpdatedAt,
		&comp.CreatedBy,
		&comp.UpdatedBy,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("component not found")
		}
		return nil, err
	}

	// Parse type and status
	comp.Type = component.ComponentType(typeStr)
	comp.Status = component.ComponentStatus(statusStr)

	// Parse location JSON
	if err := json.Unmarshal(locationJSON, &comp.Location); err != nil {
		return nil, fmt.Errorf("failed to unmarshal location: %w", err)
	}

	// Parse properties JSON
	if err := json.Unmarshal(propertiesJSON, &comp.Properties); err != nil {
		return nil, fmt.Errorf("failed to unmarshal properties: %w", err)
	}

	// Parse relations JSON
	if err := json.Unmarshal(relationsJSON, &comp.Relations); err != nil {
		return nil, fmt.Errorf("failed to unmarshal relations: %w", err)
	}

	return &comp, nil
}

func (r *PostGISComponentRepository) scanComponents(rows *sql.Rows) ([]*component.Component, error) {
	var components []*component.Component

	for rows.Next() {
		var comp component.Component
		var typeStr, statusStr string
		var locationJSON, propertiesJSON, relationsJSON []byte

		err := rows.Scan(
			&comp.ID,
			&comp.Name,
			&typeStr,
			&comp.Path,
			&locationJSON,
			&propertiesJSON,
			&relationsJSON,
			&statusStr,
			&comp.Version,
			&comp.CreatedAt,
			&comp.UpdatedAt,
			&comp.CreatedBy,
			&comp.UpdatedBy,
		)

		if err != nil {
			return nil, err
		}

		// Parse type and status
		comp.Type = component.ComponentType(typeStr)
		comp.Status = component.ComponentStatus(statusStr)

		// Parse location JSON
		if err := json.Unmarshal(locationJSON, &comp.Location); err != nil {
			return nil, fmt.Errorf("failed to unmarshal location: %w", err)
		}

		// Parse properties JSON
		if err := json.Unmarshal(propertiesJSON, &comp.Properties); err != nil {
			return nil, fmt.Errorf("failed to unmarshal properties: %w", err)
		}

		// Parse relations JSON
		if err := json.Unmarshal(relationsJSON, &comp.Relations); err != nil {
			return nil, fmt.Errorf("failed to unmarshal relations: %w", err)
		}

		components = append(components, &comp)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	return components, nil
}
