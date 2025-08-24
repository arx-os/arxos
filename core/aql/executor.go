package aql

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/arxos/arxos/core/internal/arxobject"
	"gorm.io/gorm"
)

// Executor executes parsed AQL queries
type Executor struct {
	db        *gorm.DB
	arxEngine *arxobject.Engine
}

// NewExecutor creates a new AQL executor
func NewExecutor(database *gorm.DB, engine *arxobject.Engine) *Executor {
	return &Executor{
		db:        database,
		arxEngine: engine,
	}
}

// Execute runs a parsed AQL query and returns results
func (e *Executor) Execute(ctx context.Context, query *Query) (*Result, error) {
	switch query.Type {
	case SELECT:
		return e.executeSelect(ctx, query)
	case UPDATE:
		return e.executeUpdate(ctx, query)
	case VALIDATE:
		return e.executeValidate(ctx, query)
	case HISTORY:
		return e.executeHistory(ctx, query)
	case DIFF:
		return e.executeDiff(ctx, query)
	default:
		return nil, fmt.Errorf("unsupported query type: %s", query.Type)
	}
}

// Result represents query execution results
type Result struct {
	Type       QueryType
	Objects    []arxobject.ArxObject
	Count      int
	Message    string
	Metadata   map[string]interface{}
	ExecutedAt time.Time
}

// executeSelect handles SELECT queries
func (e *Executor) executeSelect(ctx context.Context, query *Query) (*Result, error) {
	dbQuery := e.db.WithContext(ctx).Model(&arxobject.ArxObject{})
	
	// Parse target (e.g., "building:empire_state:floor:3")
	targetParts := strings.Split(query.Target, ":")
	if len(targetParts) >= 2 {
		// Add hierarchical filtering
		dbQuery = e.applyHierarchicalFilter(dbQuery, targetParts)
	}
	
	// Apply WHERE filters
	for _, filter := range query.Filters {
		dbQuery = e.applyFilter(dbQuery, filter)
	}
	
	// Apply selections (if not *)
	if len(query.Selections) > 0 && query.Selections[0] != "*" {
		dbQuery = dbQuery.Select(query.Selections)
	}
	
	// Apply ordering
	if query.OrderBy != "" {
		dbQuery = dbQuery.Order(query.OrderBy)
	}
	
	// Apply limit
	if query.Limit > 0 {
		dbQuery = dbQuery.Limit(query.Limit)
	}
	
	// Execute query
	var objects []arxobject.ArxObject
	result := dbQuery.Find(&objects)
	
	if result.Error != nil {
		return nil, fmt.Errorf("query execution failed: %w", result.Error)
	}
	
	return &Result{
		Type:       SELECT,
		Objects:    objects,
		Count:      len(objects),
		ExecutedAt: time.Now(),
		Metadata: map[string]interface{}{
			"rows_affected": result.RowsAffected,
		},
	}, nil
}

// applyHierarchicalFilter applies building hierarchy filters
func (e *Executor) applyHierarchicalFilter(query *gorm.DB, parts []string) *gorm.DB {
	// Example: building:empire_state:floor:3:room:*
	for i := 0; i < len(parts); i += 2 {
		if i+1 < len(parts) {
			level := parts[i]
			value := parts[i+1]
			
			if value != "*" {
				// Use JSONB queries for PostgreSQL
				jsonPath := fmt.Sprintf("data->>'%s'", level)
				query = query.Where(jsonPath+" = ?", value)
			}
		}
	}
	return query
}

// applyFilter applies a single filter condition
func (e *Executor) applyFilter(query *gorm.DB, filter Filter) *gorm.DB {
	field := filter.Field
	
	// Handle special fields
	switch {
	case strings.HasPrefix(field, "confidence."):
		// Query confidence scores
		confField := strings.TrimPrefix(field, "confidence.")
		jsonPath := fmt.Sprintf("confidence->>'%s'", confField)
		return e.applyOperator(query, jsonPath, filter.Operator, filter.Value)
		
	case strings.HasPrefix(field, "data."):
		// Query data properties
		dataField := strings.TrimPrefix(field, "data.")
		jsonPath := fmt.Sprintf("data->>'%s'", dataField)
		return e.applyOperator(query, jsonPath, filter.Operator, filter.Value)
		
	case field == "type":
		return query.Where("type = ?", filter.Value)
		
	case field == "validated":
		return query.Where("metadata->>'validated' = ?", filter.Value)
		
	default:
		// Direct field query
		return e.applyOperator(query, field, filter.Operator, filter.Value)
	}
}

// applyOperator applies the appropriate SQL operator
func (e *Executor) applyOperator(query *gorm.DB, field, operator string, value interface{}) *gorm.DB {
	switch operator {
	case "=":
		return query.Where(field+" = ?", value)
	case "!=":
		return query.Where(field+" != ?", value)
	case ">":
		return query.Where(field+" > ?", value)
	case "<":
		return query.Where(field+" < ?", value)
	case ">=":
		return query.Where(field+" >= ?", value)
	case "<=":
		return query.Where(field+" <= ?", value)
	case "LIKE":
		return query.Where(field+" LIKE ?", value)
	case "IN":
		return query.Where(field+" IN ?", value)
	case "NEAR":
		// Spatial query - find objects within distance
		return e.applySpatialNear(query, field, value)
	case "WITHIN":
		// Spatial query - find objects within boundary
		return e.applySpatialWithin(query, field, value)
	case "CONNECTED_TO":
		// Relationship query
		return e.applyRelationshipQuery(query, value)
	default:
		return query
	}
}

// applySpatialNear finds objects near a location
func (e *Executor) applySpatialNear(query *gorm.DB, field string, value interface{}) *gorm.DB {
	// Use PostGIS ST_DWithin for proximity search
	// Value should be in format: "x,y,distance"
	if v, ok := value.(string); ok {
		parts := strings.Split(v, ",")
		if len(parts) == 3 {
			return query.Where(
				"ST_DWithin(geometry, ST_MakePoint(?, ?), ?)",
				parts[0], parts[1], parts[2],
			)
		}
	}
	return query
}

// applySpatialWithin finds objects within a boundary
func (e *Executor) applySpatialWithin(query *gorm.DB, field string, value interface{}) *gorm.DB {
	// Use PostGIS ST_Within for boundary search
	if boundary, ok := value.(string); ok {
		return query.Where(
			"ST_Within(geometry, ST_GeomFromText(?))",
			boundary,
		)
	}
	return query
}

// applyRelationshipQuery finds objects connected to a target
func (e *Executor) applyRelationshipQuery(query *gorm.DB, value interface{}) *gorm.DB {
	if targetID, ok := value.(string); ok {
		return query.Where(
			"EXISTS (SELECT 1 FROM jsonb_array_elements(relationships) AS r WHERE r->>'targetId' = ?)",
			targetID,
		)
	}
	return query
}

// executeUpdate handles UPDATE queries
func (e *Executor) executeUpdate(ctx context.Context, query *Query) (*Result, error) {
	// Start transaction
	tx := e.db.WithContext(ctx).Begin()
	defer func() {
		if r := recover(); r != nil {
			tx.Rollback()
		}
	}()
	
	// Find objects to update
	var objects []arxobject.ArxObject
	dbQuery := tx.Model(&arxobject.ArxObject{})
	
	// Apply filters
	for _, filter := range query.Filters {
		dbQuery = e.applyFilter(dbQuery, filter)
	}
	
	if err := dbQuery.Find(&objects).Error; err != nil {
		tx.Rollback()
		return nil, err
	}
	
	// Create version history for each object before update
	for _, obj := range objects {
		// Store previous version
		if err := e.createVersion(tx, &obj); err != nil {
			tx.Rollback()
			return nil, err
		}
		
		// Apply updates (simplified - would parse from query)
		// In production, this would handle the SET clause properly
		
		// Update object
		if err := tx.Save(&obj).Error; err != nil {
			tx.Rollback()
			return nil, err
		}
	}
	
	// Commit transaction
	if err := tx.Commit().Error; err != nil {
		return nil, err
	}
	
	return &Result{
		Type:       UPDATE,
		Count:      len(objects),
		Message:    fmt.Sprintf("Updated %d objects", len(objects)),
		ExecutedAt: time.Now(),
	}, nil
}

// executeValidate handles VALIDATE queries
func (e *Executor) executeValidate(ctx context.Context, query *Query) (*Result, error) {
	// Parse target to find object
	var obj arxobject.ArxObject
	if err := e.db.WithContext(ctx).Where("id = ?", query.Target).First(&obj).Error; err != nil {
		return nil, fmt.Errorf("object not found: %s", query.Target)
	}
	
	// Update validation status
	// TODO: Implement metadata validation when ArxMetadata is available
	// obj.Metadata.Validated = true
	// obj.Metadata.ValidatedAt = time.Now()
	// ValidatedBy would come from context/auth
	
	// Improve confidence scores
	obj.Confidence.Classification = min(obj.Confidence.Classification*1.2, 1.0)
	obj.Confidence.Position = min(obj.Confidence.Position*1.2, 1.0)
	obj.Confidence.Properties = min(obj.Confidence.Position*1.2, 1.0)
	obj.Confidence.CalculateOverall()
	
	// Save updated object
	if err := e.db.WithContext(ctx).Save(&obj).Error; err != nil {
		return nil, err
	}
	
	// Propagate confidence to related objects
	e.propagateConfidence(ctx, &obj)
	
	return &Result{
		Type:       VALIDATE,
		Objects:    []arxobject.ArxObject{obj},
		Count:      1,
		Message:    fmt.Sprintf("Validated object %s", query.Target),
		ExecutedAt: time.Now(),
		Metadata: map[string]interface{}{
			"new_confidence": obj.Confidence.Overall,
			"propagated_to":  0, // TODO: Implement relationship counting when available
		},
	}, nil
}

// executeHistory handles HISTORY queries
func (e *Executor) executeHistory(ctx context.Context, query *Query) (*Result, error) {
	// Query version history table
	var versions []ArxObjectVersion
	
	dbQuery := e.db.WithContext(ctx).Model(&ArxObjectVersion{}).
		Where("object_id = ?", query.Target).
		Order("created_at DESC")
	
	if query.TimeTravel != nil {
		if query.TimeTravel.AsOf != "" {
			dbQuery = dbQuery.Where("created_at <= ?", query.TimeTravel.AsOf)
		}
		if len(query.TimeTravel.Between) == 2 {
			dbQuery = dbQuery.Where("created_at BETWEEN ? AND ?",
				query.TimeTravel.Between[0], query.TimeTravel.Between[1])
		}
	}
	
	if err := dbQuery.Find(&versions).Error; err != nil {
		return nil, err
	}
	
	// Convert versions to ArxObjects
	var objects []arxobject.ArxObject
	for _, v := range versions {
		objects = append(objects, v.Object)
	}
	
	return &Result{
		Type:       HISTORY,
		Objects:    objects,
		Count:      len(objects),
		Message:    fmt.Sprintf("Found %d versions", len(versions)),
		ExecutedAt: time.Now(),
	}, nil
}

// executeDiff handles DIFF queries
func (e *Executor) executeDiff(ctx context.Context, query *Query) (*Result, error) {
	if query.TimeTravel == nil || len(query.TimeTravel.Between) != 2 {
		return nil, fmt.Errorf("DIFF requires two versions to compare")
	}
	
	// Get two versions
	var version1, version2 ArxObjectVersion
	
	if err := e.db.WithContext(ctx).
		Where("object_id = ? AND created_at = ?", query.Target, query.TimeTravel.Between[0]).
		First(&version1).Error; err != nil {
		return nil, fmt.Errorf("version 1 not found")
	}
	
	if err := e.db.WithContext(ctx).
		Where("object_id = ? AND created_at = ?", query.Target, query.TimeTravel.Between[1]).
		First(&version2).Error; err != nil {
		return nil, fmt.Errorf("version 2 not found")
	}
	
	// Calculate diff (simplified - would use proper diff algorithm)
	diff := e.calculateDiff(&version1.Object, &version2.Object)
	
	return &Result{
		Type:    DIFF,
		Objects: []arxobject.ArxObject{version1.Object, version2.Object},
		Count:   2,
		Message: "Diff calculated",
		Metadata: map[string]interface{}{
			"changes": diff,
		},
		ExecutedAt: time.Now(),
	}, nil
}

// Helper functions

func (e *Executor) createVersion(tx *gorm.DB, obj *arxobject.ArxObject) error {
	version := ArxObjectVersion{
		ObjectID:  fmt.Sprintf("%d", obj.ID), // Convert uint64 to string
		Object:    *obj,
		CreatedAt: time.Now(),
		Version:   e.getNextVersion(tx, fmt.Sprintf("%d", obj.ID)),
	}
	return tx.Create(&version).Error
}

func (e *Executor) getNextVersion(tx *gorm.DB, objectID string) int {
	var count int64
	tx.Model(&ArxObjectVersion{}).Where("object_id = ?", objectID).Count(&count)
	return int(count) + 1
}

func (e *Executor) propagateConfidence(ctx context.Context, obj *arxobject.ArxObject) {
	// TODO: Implement relationship propagation when relationship system is available
	// For now, this is a placeholder that does nothing
	// When relationships are implemented, this would:
	// 1. Find related objects using obj.RelationshipStart and obj.RelationshipCount
	// 2. Update their confidence scores
	// 3. Save the changes
}

func (e *Executor) calculateDiff(obj1, obj2 *arxobject.ArxObject) map[string]interface{} {
	diff := make(map[string]interface{})
	
	// Compare confidence scores
	if obj1.Confidence.Overall != obj2.Confidence.Overall {
		diff["confidence_change"] = obj2.Confidence.Overall - obj1.Confidence.Overall
	}
	
	// TODO: Compare validation status when metadata system is available
	// For now, only compare basic fields that are available
	if obj1.ValidationState != obj2.ValidationState {
		diff["validation_state_changed"] = obj2.ValidationState
	}
	
	// Compare geometric properties
	if obj1.X != obj2.X || obj1.Y != obj2.Y || obj1.Z != obj2.Z {
		diff["position_changed"] = true
	}
	
	if obj1.Length != obj2.Length || obj1.Width != obj2.Width || obj1.Height != obj2.Height {
		diff["dimensions_changed"] = true
	}
	
	return diff
}

func min(a, b float32) float32 {
	if a < b {
		return a
	}
	return b
}

// ArxObjectVersion stores historical versions of ArxObjects
type ArxObjectVersion struct {
	ID        uint                  `gorm:"primaryKey"`
	ObjectID  string               `gorm:"index"`
	Object    arxobject.ArxObject  `gorm:"type:jsonb"`
	Version   int
	CreatedAt time.Time
	CreatedBy string
	ChangeLog string
}