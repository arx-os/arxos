package arxoscore

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/lib/pq"
)

// Repository provides database operations for ArxObjects
type Repository interface {
	// Basic CRUD operations
	Create(obj *ArxObject) error
	Get(id string) (*ArxObject, error)
	Update(obj *ArxObject) error
	Delete(id string) error
	
	// Batch operations
	BatchCreate(objects []*ArxObject) error
	BatchUpdate(objects []*ArxObject) error
	
	// Hierarchy queries
	GetChildren(parentID string) ([]*ArxObject, error)
	GetParent(childID string) (*ArxObject, error)
	GetAncestors(id string) ([]*ArxObject, error)
	GetDescendants(id string) ([]*ArxObject, error)
	
	// Spatial queries
	GetInBounds(minX, minY, maxX, maxY float64) ([]*ArxObject, error)
	GetAtPosition(x, y float64, tolerance float64) ([]*ArxObject, error)
	GetOverlapping(id string) ([]*ArxObject, error)
	
	// Scale-based queries
	GetAtScale(scale float64, viewport Viewport) ([]*ArxObject, error)
	GetTile(z, x, y int) ([]*ArxObject, error)
	
	// System queries
	GetBySystem(system string) ([]*ArxObject, error)
	GetByType(objType string) ([]*ArxObject, error)
	GetByTags(tags []string) ([]*ArxObject, error)
	
	// Search
	Search(query string) ([]*ArxObject, error)
	
	// Statistics
	Count() (int64, error)
	CountBySystem() (map[string]int64, error)
	CountByType() (map[string]int64, error)
}

// Viewport represents a viewing area for scale-based queries
type Viewport struct {
	MinX, MinY float64
	MaxX, MaxY float64
	Scale      float64
}

// PostgresRepository implements Repository using PostgreSQL
type PostgresRepository struct {
	db *sql.DB
}

// NewPostgresRepository creates a new PostgreSQL repository
func NewPostgresRepository(db *sql.DB) *PostgresRepository {
	return &PostgresRepository{db: db}
}

// Create inserts a new ArxObject
func (r *PostgresRepository) Create(obj *ArxObject) error {
	if err := obj.Validate(); err != nil {
		return fmt.Errorf("validation failed: %w", err)
	}
	
	query := `
		INSERT INTO arxobjects (
			id, type, name, system, parent_id, child_ids,
			position_x, position_y, position_z,
			width, height, depth,
			rotation_x, rotation_y, rotation_z,
			system_plane_layer, system_plane_z_order, system_plane_elevation,
			scale_min, scale_max, optimal_scale,
			svg_path, style, icon,
			symbol_id, source, confidence,
			properties, created_by, created_at, updated_at,
			bilt_reward, version, active, verified, tags
		) VALUES (
			$1, $2, $3, $4, $5, $6,
			$7, $8, $9,
			$10, $11, $12,
			$13, $14, $15,
			$16, $17, $18,
			$19, $20, $21,
			$22, $23, $24,
			$25, $26, $27,
			$28, $29, $30, $31,
			$32, $33, $34, $35, $36
		)`
	
	propertiesJSON, _ := json.Marshal(obj.Properties)
	
	_, err := r.db.Exec(query,
		obj.ID, obj.Type, obj.Name, obj.System, obj.ParentID, pq.Array(obj.ChildIDs),
		obj.Position.X, obj.Position.Y, obj.Position.Z,
		obj.Dimensions.Width, obj.Dimensions.Height, obj.Dimensions.Depth,
		obj.Rotation.X, obj.Rotation.Y, obj.Rotation.Z,
		obj.SystemPlane.Layer, obj.SystemPlane.ZOrder, obj.SystemPlane.Elevation,
		obj.ScaleMin, obj.ScaleMax, obj.OptimalScale,
		obj.Geometry.SVGPath, obj.Geometry.Style, obj.Geometry.Icon,
		obj.SymbolID, obj.Source, obj.Confidence,
		propertiesJSON, obj.CreatedBy, obj.CreatedAt, obj.UpdatedAt,
		obj.BILTReward, obj.Version, obj.Active, obj.Verified, pq.Array(obj.Tags),
	)
	
	return err
}

// Get retrieves an ArxObject by ID
func (r *PostgresRepository) Get(id string) (*ArxObject, error) {
	query := `
		SELECT 
			id, type, name, system, parent_id, child_ids,
			position_x, position_y, position_z,
			width, height, depth,
			rotation_x, rotation_y, rotation_z,
			system_plane_layer, system_plane_z_order, system_plane_elevation,
			scale_min, scale_max, optimal_scale,
			svg_path, style, icon,
			symbol_id, source, confidence,
			properties, created_by, created_at, updated_by, updated_at,
			bilt_reward, version, active, verified, tags
		FROM arxobjects
		WHERE id = $1`
	
	obj := &ArxObject{}
	var propertiesJSON []byte
	var updatedBy sql.NullString
	
	err := r.db.QueryRow(query, id).Scan(
		&obj.ID, &obj.Type, &obj.Name, &obj.System, &obj.ParentID, pq.Array(&obj.ChildIDs),
		&obj.Position.X, &obj.Position.Y, &obj.Position.Z,
		&obj.Dimensions.Width, &obj.Dimensions.Height, &obj.Dimensions.Depth,
		&obj.Rotation.X, &obj.Rotation.Y, &obj.Rotation.Z,
		&obj.SystemPlane.Layer, &obj.SystemPlane.ZOrder, &obj.SystemPlane.Elevation,
		&obj.ScaleMin, &obj.ScaleMax, &obj.OptimalScale,
		&obj.Geometry.SVGPath, &obj.Geometry.Style, &obj.Geometry.Icon,
		&obj.SymbolID, &obj.Source, &obj.Confidence,
		&propertiesJSON, &obj.CreatedBy, &obj.CreatedAt, &updatedBy, &obj.UpdatedAt,
		&obj.BILTReward, &obj.Version, &obj.Active, &obj.Verified, pq.Array(&obj.Tags),
	)
	
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("ArxObject not found: %s", id)
		}
		return nil, err
	}
	
	if updatedBy.Valid {
		obj.UpdatedBy = updatedBy.String
	}
	
	if propertiesJSON != nil {
		json.Unmarshal(propertiesJSON, &obj.Properties)
	}
	
	// Load connections and overlaps separately
	obj.Connections, _ = r.getConnections(id)
	obj.Overlaps, _ = r.getOverlaps(id)
	obj.History, _ = r.getHistory(id)
	
	return obj, nil
}

// Update modifies an existing ArxObject
func (r *PostgresRepository) Update(obj *ArxObject) error {
	if err := obj.Validate(); err != nil {
		return fmt.Errorf("validation failed: %w", err)
	}
	
	obj.UpdatedAt = time.Now()
	obj.Version++
	
	query := `
		UPDATE arxobjects SET
			type = $2, name = $3, system = $4, parent_id = $5, child_ids = $6,
			position_x = $7, position_y = $8, position_z = $9,
			width = $10, height = $11, depth = $12,
			rotation_x = $13, rotation_y = $14, rotation_z = $15,
			system_plane_layer = $16, system_plane_z_order = $17, system_plane_elevation = $18,
			scale_min = $19, scale_max = $20, optimal_scale = $21,
			svg_path = $22, style = $23, icon = $24,
			symbol_id = $25, source = $26, confidence = $27,
			properties = $28, updated_by = $29, updated_at = $30,
			bilt_reward = $31, version = $32, active = $33, verified = $34, tags = $35
		WHERE id = $1 AND version = $36`
	
	propertiesJSON, _ := json.Marshal(obj.Properties)
	
	result, err := r.db.Exec(query,
		obj.ID, obj.Type, obj.Name, obj.System, obj.ParentID, pq.Array(obj.ChildIDs),
		obj.Position.X, obj.Position.Y, obj.Position.Z,
		obj.Dimensions.Width, obj.Dimensions.Height, obj.Dimensions.Depth,
		obj.Rotation.X, obj.Rotation.Y, obj.Rotation.Z,
		obj.SystemPlane.Layer, obj.SystemPlane.ZOrder, obj.SystemPlane.Elevation,
		obj.ScaleMin, obj.ScaleMax, obj.OptimalScale,
		obj.Geometry.SVGPath, obj.Geometry.Style, obj.Geometry.Icon,
		obj.SymbolID, obj.Source, obj.Confidence,
		propertiesJSON, obj.UpdatedBy, obj.UpdatedAt,
		obj.BILTReward, obj.Version, obj.Active, obj.Verified, pq.Array(obj.Tags),
		obj.Version-1, // Optimistic locking
	)
	
	if err != nil {
		return err
	}
	
	rows, err := result.RowsAffected()
	if err != nil {
		return err
	}
	
	if rows == 0 {
		return fmt.Errorf("update failed: version conflict or object not found")
	}
	
	return nil
}

// Delete removes an ArxObject
func (r *PostgresRepository) Delete(id string) error {
	_, err := r.db.Exec("DELETE FROM arxobjects WHERE id = $1", id)
	return err
}

// GetChildren retrieves all child objects
func (r *PostgresRepository) GetChildren(parentID string) ([]*ArxObject, error) {
	query := `
		SELECT id FROM arxobjects 
		WHERE parent_id = $1 
		ORDER BY type, name`
	
	rows, err := r.db.Query(query, parentID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	
	var objects []*ArxObject
	for rows.Next() {
		var id string
		if err := rows.Scan(&id); err != nil {
			continue
		}
		if obj, err := r.Get(id); err == nil {
			objects = append(objects, obj)
		}
	}
	
	return objects, nil
}

// GetAtScale retrieves objects visible at a given zoom level
func (r *PostgresRepository) GetAtScale(scale float64, viewport Viewport) ([]*ArxObject, error) {
	query := `
		SELECT id FROM arxobjects
		WHERE position_x BETWEEN $1 AND $2
			AND position_y BETWEEN $3 AND $4
			AND scale_min >= $5
			AND scale_max <= $5
			AND active = true
		ORDER BY system_plane_z_order, optimal_scale DESC
		LIMIT 10000`
	
	rows, err := r.db.Query(query,
		viewport.MinX, viewport.MaxX,
		viewport.MinY, viewport.MaxY,
		scale,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	
	var objects []*ArxObject
	for rows.Next() {
		var id string
		if err := rows.Scan(&id); err != nil {
			continue
		}
		if obj, err := r.Get(id); err == nil {
			objects = append(objects, obj)
		}
	}
	
	return objects, nil
}

// GetBySystem retrieves all objects in a building system
func (r *PostgresRepository) GetBySystem(system string) ([]*ArxObject, error) {
	query := `
		SELECT id FROM arxobjects
		WHERE system = $1 AND active = true
		ORDER BY type, name`
	
	rows, err := r.db.Query(query, system)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	
	var objects []*ArxObject
	for rows.Next() {
		var id string
		if err := rows.Scan(&id); err != nil {
			continue
		}
		if obj, err := r.Get(id); err == nil {
			objects = append(objects, obj)
		}
	}
	
	return objects, nil
}

// Search performs a text search across ArxObjects
func (r *PostgresRepository) Search(searchQuery string) ([]*ArxObject, error) {
	// Simple search implementation - can be enhanced with full-text search
	query := `
		SELECT id FROM arxobjects
		WHERE (
			LOWER(name) LIKE LOWER($1) OR
			LOWER(type) LIKE LOWER($1) OR
			LOWER(system) LIKE LOWER($1) OR
			$2 = ANY(tags)
		) AND active = true
		ORDER BY name
		LIMIT 100`
	
	searchTerm := "%" + searchQuery + "%"
	
	rows, err := r.db.Query(query, searchTerm, strings.ToLower(searchQuery))
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	
	var objects []*ArxObject
	for rows.Next() {
		var id string
		if err := rows.Scan(&id); err != nil {
			continue
		}
		if obj, err := r.Get(id); err == nil {
			objects = append(objects, obj)
		}
	}
	
	return objects, nil
}

// Helper methods

func (r *PostgresRepository) getConnections(id string) ([]Connection, error) {
	query := `
		SELECT to_id, connection_type, properties
		FROM arxobject_connections
		WHERE from_id = $1`
	
	rows, err := r.db.Query(query, id)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	
	var connections []Connection
	for rows.Next() {
		var conn Connection
		var propertiesJSON []byte
		
		if err := rows.Scan(&conn.ToID, &conn.Type, &propertiesJSON); err != nil {
			continue
		}
		
		if propertiesJSON != nil {
			json.Unmarshal(propertiesJSON, &conn.Properties)
		}
		
		connections = append(connections, conn)
	}
	
	return connections, nil
}

func (r *PostgresRepository) getOverlaps(id string) ([]Overlap, error) {
	query := `
		SELECT object_id, relationship
		FROM arxobject_overlaps
		WHERE source_id = $1`
	
	rows, err := r.db.Query(query, id)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	
	var overlaps []Overlap
	for rows.Next() {
		var overlap Overlap
		if err := rows.Scan(&overlap.ObjectID, &overlap.Relationship); err != nil {
			continue
		}
		overlaps = append(overlaps, overlap)
	}
	
	return overlaps, nil
}

func (r *PostgresRepository) getHistory(id string) ([]Change, error) {
	query := `
		SELECT timestamp, user_id, action, description, 
			   old_values, new_values, bilt_reward
		FROM arxobject_history
		WHERE object_id = $1
		ORDER BY timestamp DESC`
	
	rows, err := r.db.Query(query, id)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	
	var history []Change
	for rows.Next() {
		var change Change
		var oldJSON, newJSON []byte
		
		if err := rows.Scan(
			&change.Timestamp, &change.UserID, &change.Action, &change.Description,
			&oldJSON, &newJSON, &change.BILTReward,
		); err != nil {
			continue
		}
		
		if oldJSON != nil {
			json.Unmarshal(oldJSON, &change.OldValues)
		}
		if newJSON != nil {
			json.Unmarshal(newJSON, &change.NewValues)
		}
		
		history = append(history, change)
	}
	
	return history, nil
}

// Implement remaining interface methods...
// GetParent, GetAncestors, GetDescendants, GetInBounds, GetAtPosition, 
// GetOverlapping, GetTile, GetByType, GetByTags, BatchCreate, BatchUpdate,
// Count, CountBySystem, CountByType