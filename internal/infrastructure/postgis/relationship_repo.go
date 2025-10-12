package postgis

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"

	"github.com/google/uuid"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
)

// RelationshipRepository implements relationship persistence using PostgreSQL
type RelationshipRepository struct {
	db *sql.DB
}

// NewRelationshipRepository creates a new relationship repository
func NewRelationshipRepository(db *sql.DB) *RelationshipRepository {
	return &RelationshipRepository{db: db}
}

// Create creates a new item relationship
func (r *RelationshipRepository) Create(ctx context.Context, req *domain.CreateRelationshipRequest) (*domain.ItemRelationship, error) {
	query := `
		INSERT INTO item_relationships (
			id, from_item_id, to_item_id, relationship_type,
			properties, strength, bidirectional, created_by
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
		RETURNING id, from_item_id, to_item_id, relationship_type,
			properties, strength, bidirectional,
			created_at, updated_at, created_by
	`

	relationshipID := uuid.New().String()
	strength := req.Strength
	if strength == 0 {
		strength = 1.0 // Default strength
	}

	propertiesJSON, err := json.Marshal(req.Properties)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal properties: %w", err)
	}

	var rel domain.ItemRelationship
	var propertiesStr string

	err = r.db.QueryRowContext(ctx, query,
		relationshipID,
		req.FromItemID.String(),
		req.ToItemID.String(),
		req.RelationshipType,
		propertiesJSON,
		strength,
		req.Bidirectional,
		req.CreatedBy,
	).Scan(
		&rel.ID,
		&rel.FromItemID,
		&rel.ToItemID,
		&rel.RelationshipType,
		&propertiesStr,
		&rel.Strength,
		&rel.Bidirectional,
		&rel.CreatedAt,
		&rel.UpdatedAt,
		&rel.CreatedBy,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to create relationship: %w", err)
	}

	// Parse properties JSON
	if propertiesStr != "" {
		if err := json.Unmarshal([]byte(propertiesStr), &rel.Properties); err != nil {
			rel.Properties = make(map[string]any)
		}
	}

	return &rel, nil
}

// GetByID retrieves a relationship by ID
func (r *RelationshipRepository) GetByID(ctx context.Context, id string) (*domain.ItemRelationship, error) {
	query := `
		SELECT id, from_item_id, to_item_id, relationship_type,
			properties, strength, bidirectional,
			created_at, updated_at, created_by
		FROM item_relationships
		WHERE id = $1
	`

	var rel domain.ItemRelationship
	var propertiesStr string

	err := r.db.QueryRowContext(ctx, query, id).Scan(
		&rel.ID,
		&rel.FromItemID,
		&rel.ToItemID,
		&rel.RelationshipType,
		&propertiesStr,
		&rel.Strength,
		&rel.Bidirectional,
		&rel.CreatedAt,
		&rel.UpdatedAt,
		&rel.CreatedBy,
	)

	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("relationship not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get relationship: %w", err)
	}

	// Parse properties JSON
	if propertiesStr != "" {
		if err := json.Unmarshal([]byte(propertiesStr), &rel.Properties); err != nil {
			rel.Properties = make(map[string]any)
		}
	}

	return &rel, nil
}

// List retrieves relationships based on filter
func (r *RelationshipRepository) List(ctx context.Context, filter *domain.RelationshipFilter) ([]*domain.ItemRelationship, error) {
	query := `
		SELECT id, from_item_id, to_item_id, relationship_type,
			properties, strength, bidirectional,
			created_at, updated_at, created_by
		FROM item_relationships
		WHERE 1=1
	`
	args := []any{}
	argPos := 1

	if filter.FromItemID != nil {
		query += fmt.Sprintf(" AND from_item_id = $%d", argPos)
		args = append(args, filter.FromItemID.String())
		argPos++
	}

	if filter.ToItemID != nil {
		query += fmt.Sprintf(" AND to_item_id = $%d", argPos)
		args = append(args, filter.ToItemID.String())
		argPos++
	}

	if filter.RelationshipType != nil {
		query += fmt.Sprintf(" AND relationship_type = $%d", argPos)
		args = append(args, *filter.RelationshipType)
		argPos++
	}

	if filter.Bidirectional != nil {
		query += fmt.Sprintf(" AND bidirectional = $%d", argPos)
		args = append(args, *filter.Bidirectional)
		argPos++
	}

	query += " ORDER BY created_at DESC"

	if filter.Limit > 0 {
		query += fmt.Sprintf(" LIMIT $%d", argPos)
		args = append(args, filter.Limit)
		argPos++
	}

	if filter.Offset > 0 {
		query += fmt.Sprintf(" OFFSET $%d", argPos)
		args = append(args, filter.Offset)
	}

	rows, err := r.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to list relationships: %w", err)
	}
	defer rows.Close()

	var relationships []*domain.ItemRelationship
	for rows.Next() {
		var rel domain.ItemRelationship
		var propertiesStr string

		err := rows.Scan(
			&rel.ID,
			&rel.FromItemID,
			&rel.ToItemID,
			&rel.RelationshipType,
			&propertiesStr,
			&rel.Strength,
			&rel.Bidirectional,
			&rel.CreatedAt,
			&rel.UpdatedAt,
			&rel.CreatedBy,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan relationship: %w", err)
		}

		// Parse properties
		if propertiesStr != "" {
			if err := json.Unmarshal([]byte(propertiesStr), &rel.Properties); err != nil {
				rel.Properties = make(map[string]any)
			}
		}

		relationships = append(relationships, &rel)
	}

	return relationships, nil
}

// Delete removes a relationship
func (r *RelationshipRepository) Delete(ctx context.Context, id string) error {
	query := `DELETE FROM item_relationships WHERE id = $1`
	result, err := r.db.ExecContext(ctx, query, id)
	if err != nil {
		return fmt.Errorf("failed to delete relationship: %w", err)
	}

	rows, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to get rows affected: %w", err)
	}

	if rows == 0 {
		return fmt.Errorf("relationship not found")
	}

	return nil
}

// GetUpstream traverses relationships upstream (find sources/parents)
func (r *RelationshipRepository) GetUpstream(ctx context.Context, itemID types.ID, relType string, depth int) ([]*domain.ItemRelationship, error) {
	// Use recursive CTE to traverse graph upstream
	query := `
		WITH RECURSIVE upstream AS (
			-- Base case: direct upstream relationships
			SELECT id, from_item_id, to_item_id, relationship_type,
				properties, strength, bidirectional,
				created_at, updated_at, created_by,
				1 as level
			FROM item_relationships
			WHERE to_item_id = $1
				AND ($2 = '' OR relationship_type = $2)

			UNION ALL

			-- Recursive case: traverse upstream
			SELECT r.id, r.from_item_id, r.to_item_id, r.relationship_type,
				r.properties, r.strength, r.bidirectional,
				r.created_at, r.updated_at, r.created_by,
				u.level + 1
			FROM item_relationships r
			INNER JOIN upstream u ON r.to_item_id = u.from_item_id
			WHERE u.level < $3
				AND ($2 = '' OR r.relationship_type = $2)
		)
		SELECT id, from_item_id, to_item_id, relationship_type,
			properties, strength, bidirectional,
			created_at, updated_at, created_by
		FROM upstream
		ORDER BY level
	`

	if depth <= 0 {
		depth = 100 // Default max depth
	}

	rows, err := r.db.QueryContext(ctx, query, itemID.String(), relType, depth)
	if err != nil {
		return nil, fmt.Errorf("failed to get upstream relationships: %w", err)
	}
	defer rows.Close()

	return r.scanRelationships(rows)
}

// GetDownstream traverses relationships downstream (find children/destinations)
func (r *RelationshipRepository) GetDownstream(ctx context.Context, itemID types.ID, relType string, depth int) ([]*domain.ItemRelationship, error) {
	// Use recursive CTE to traverse graph downstream
	query := `
		WITH RECURSIVE downstream AS (
			-- Base case: direct downstream relationships
			SELECT id, from_item_id, to_item_id, relationship_type,
				properties, strength, bidirectional,
				created_at, updated_at, created_by,
				1 as level
			FROM item_relationships
			WHERE from_item_id = $1
				AND ($2 = '' OR relationship_type = $2)

			UNION ALL

			-- Recursive case: traverse downstream
			SELECT r.id, r.from_item_id, r.to_item_id, r.relationship_type,
				r.properties, r.strength, r.bidirectional,
				r.created_at, r.updated_at, r.created_by,
				d.level + 1
			FROM item_relationships r
			INNER JOIN downstream d ON r.from_item_id = d.to_item_id
			WHERE d.level < $3
				AND ($2 = '' OR r.relationship_type = $2)
		)
		SELECT id, from_item_id, to_item_id, relationship_type,
			properties, strength, bidirectional,
			created_at, updated_at, created_by
		FROM downstream
		ORDER BY level
	`

	if depth <= 0 {
		depth = 100 // Default max depth
	}

	rows, err := r.db.QueryContext(ctx, query, itemID.String(), relType, depth)
	if err != nil {
		return nil, fmt.Errorf("failed to get downstream relationships: %w", err)
	}
	defer rows.Close()

	return r.scanRelationships(rows)
}

// GetPath finds the shortest path between two items
func (r *RelationshipRepository) GetPath(ctx context.Context, fromID, toID types.ID) ([]*domain.ItemRelationship, error) {
	// Use bidirectional BFS to find shortest path
	query := `
		WITH RECURSIVE path AS (
			-- Base case: direct relationship
			SELECT id, from_item_id, to_item_id, relationship_type,
				properties, strength, bidirectional,
				created_at, updated_at, created_by,
				ARRAY[id] as path_ids,
				1 as depth
			FROM item_relationships
			WHERE from_item_id = $1

			UNION ALL

			-- Recursive case: extend path
			SELECT r.id, r.from_item_id, r.to_item_id, r.relationship_type,
				r.properties, r.strength, r.bidirectional,
				r.created_at, r.updated_at, r.created_by,
				p.path_ids || r.id,
				p.depth + 1
			FROM item_relationships r
			INNER JOIN path p ON r.from_item_id = p.to_item_id
			WHERE r.to_item_id = $2
				AND p.depth < 10
				AND NOT (r.id = ANY(p.path_ids)) -- Prevent cycles
		)
		SELECT id, from_item_id, to_item_id, relationship_type,
			properties, strength, bidirectional,
			created_at, updated_at, created_by
		FROM path
		WHERE to_item_id = $2
		ORDER BY depth ASC
		LIMIT 1
	`

	rows, err := r.db.QueryContext(ctx, query, fromID.String(), toID.String())
	if err != nil {
		return nil, fmt.Errorf("failed to find path: %w", err)
	}
	defer rows.Close()

	return r.scanRelationships(rows)
}

// CreateBulk creates multiple relationships in a single transaction
func (r *RelationshipRepository) CreateBulk(ctx context.Context, requests []*domain.CreateRelationshipRequest) ([]*domain.ItemRelationship, error) {
	tx, err := r.db.BeginTx(ctx, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	query := `
		INSERT INTO item_relationships (
			id, from_item_id, to_item_id, relationship_type,
			properties, strength, bidirectional, created_by
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
		RETURNING id, from_item_id, to_item_id, relationship_type,
			properties, strength, bidirectional,
			created_at, updated_at, created_by
	`

	var relationships []*domain.ItemRelationship

	for _, req := range requests {
		relationshipID := uuid.New().String()
		strength := req.Strength
		if strength == 0 {
			strength = 1.0
		}

		propertiesJSON, err := json.Marshal(req.Properties)
		if err != nil {
			return nil, fmt.Errorf("failed to marshal properties: %w", err)
		}

		var rel domain.ItemRelationship
		var propertiesStr string

		err = tx.QueryRowContext(ctx, query,
			relationshipID,
			req.FromItemID.String(),
			req.ToItemID.String(),
			req.RelationshipType,
			propertiesJSON,
			strength,
			req.Bidirectional,
			req.CreatedBy,
		).Scan(
			&rel.ID,
			&rel.FromItemID,
			&rel.ToItemID,
			&rel.RelationshipType,
			&propertiesStr,
			&rel.Strength,
			&rel.Bidirectional,
			&rel.CreatedAt,
			&rel.UpdatedAt,
			&rel.CreatedBy,
		)

		if err != nil {
			return nil, fmt.Errorf("failed to create relationship: %w", err)
		}

		// Parse properties
		if propertiesStr != "" {
			if err := json.Unmarshal([]byte(propertiesStr), &rel.Properties); err != nil {
				rel.Properties = make(map[string]any)
			}
		}

		relationships = append(relationships, &rel)
	}

	if err := tx.Commit(); err != nil {
		return nil, fmt.Errorf("failed to commit transaction: %w", err)
	}

	return relationships, nil
}

// DeleteByItem deletes all relationships for an item
func (r *RelationshipRepository) DeleteByItem(ctx context.Context, itemID types.ID) error {
	query := `
		DELETE FROM item_relationships
		WHERE from_item_id = $1 OR to_item_id = $1
	`

	_, err := r.db.ExecContext(ctx, query, itemID.String())
	if err != nil {
		return fmt.Errorf("failed to delete relationships for item: %w", err)
	}

	return nil
}

// scanRelationships is a helper to scan relationship rows
func (r *RelationshipRepository) scanRelationships(rows *sql.Rows) ([]*domain.ItemRelationship, error) {
	var relationships []*domain.ItemRelationship

	for rows.Next() {
		var rel domain.ItemRelationship
		var propertiesStr string

		err := rows.Scan(
			&rel.ID,
			&rel.FromItemID,
			&rel.ToItemID,
			&rel.RelationshipType,
			&propertiesStr,
			&rel.Strength,
			&rel.Bidirectional,
			&rel.CreatedAt,
			&rel.UpdatedAt,
			&rel.CreatedBy,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan relationship: %w", err)
		}

		// Parse properties
		if propertiesStr != "" {
			if err := json.Unmarshal([]byte(propertiesStr), &rel.Properties); err != nil {
				rel.Properties = make(map[string]any)
			}
		}

		relationships = append(relationships, &rel)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating relationships: %w", err)
	}

	return relationships, nil
}
