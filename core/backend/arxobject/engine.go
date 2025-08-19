package arxobject

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"math"
	"sync"
	"time"

	"github.com/google/uuid"
)

// Engine manages ArxObjects and their relationships
type Engine struct {
	db              *sql.DB
	cache           *ObjectCache
	spatialIndex    *SpatialIndex
	relationshipMap map[string][]string // object ID -> related IDs
	mu              sync.RWMutex
}

// NewEngine creates a new ArxObject engine
func NewEngine(db *sql.DB) *Engine {
	return &Engine{
		db:              db,
		cache:           NewObjectCache(10000), // Cache up to 10k objects
		spatialIndex:    NewSpatialIndex(),
		relationshipMap: make(map[string][]string),
	}
}

// CreateObject creates a new ArxObject in the database
func (e *Engine) CreateObject(obj *ArxObject) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	if obj.ID == "" {
		obj.ID = fmt.Sprintf("arx_%s", uuid.New().String())
	}
	if obj.UUID == "" {
		obj.UUID = uuid.New().String()
	}

	// Calculate overall confidence if not set
	if obj.Confidence.Overall == 0 {
		obj.Confidence.CalculateOverall()
	}

	query := `
		INSERT INTO arx_objects (
			id, uuid, type, system, x, y, z, 
			width, height, depth, scale_min, scale_max,
			building_id, floor_id, room_id, parent_id,
			properties, confidence, extraction_method, source,
			created_at, updated_at
		) VALUES (
			$1, $2, $3, $4, $5, $6, $7,
			$8, $9, $10, $11, $12,
			$13, $14, $15, $16,
			$17, $18, $19, $20,
			$21, $22
		)
	`

	confidenceJSON, _ := json.Marshal(obj.Confidence)
	
	_, err := e.db.Exec(query,
		obj.ID, obj.UUID, obj.Type, obj.System, obj.X, obj.Y, obj.Z,
		obj.Width, obj.Height, obj.Depth, obj.ScaleMin, obj.ScaleMax,
		obj.BuildingID, obj.FloorID, obj.RoomID, obj.ParentID,
		obj.Properties, confidenceJSON, obj.ExtractionMethod, obj.Source,
		obj.CreatedAt, obj.UpdatedAt,
	)

	if err != nil {
		return fmt.Errorf("failed to create ArxObject: %w", err)
	}

	// Add to cache and spatial index
	e.cache.Set(obj.ID, obj)
	e.spatialIndex.Insert(obj)

	// Process relationships
	for _, rel := range obj.Relationships {
		e.addRelationship(obj.ID, rel.TargetID)
	}

	return nil
}

// GetObject retrieves an ArxObject by ID
func (e *Engine) GetObject(id string) (*ArxObject, error) {
	e.mu.RLock()
	defer e.mu.RUnlock()

	// Check cache first
	if obj, found := e.cache.Get(id); found {
		return obj, nil
	}

	// Query database
	query := `
		SELECT id, uuid, type, system, x, y, z,
			   width, height, depth, scale_min, scale_max,
			   building_id, floor_id, room_id, parent_id,
			   properties, confidence, extraction_method, source,
			   created_at, updated_at, validated_at, validated_by
		FROM arx_objects WHERE id = $1
	`

	var obj ArxObject
	var confidenceJSON []byte
	
	err := e.db.QueryRow(query, id).Scan(
		&obj.ID, &obj.UUID, &obj.Type, &obj.System, &obj.X, &obj.Y, &obj.Z,
		&obj.Width, &obj.Height, &obj.Depth, &obj.ScaleMin, &obj.ScaleMax,
		&obj.BuildingID, &obj.FloorID, &obj.RoomID, &obj.ParentID,
		&obj.Properties, &confidenceJSON, &obj.ExtractionMethod, &obj.Source,
		&obj.CreatedAt, &obj.UpdatedAt, &obj.ValidatedAt, &obj.ValidatedBy,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to get ArxObject: %w", err)
	}

	json.Unmarshal(confidenceJSON, &obj.Confidence)

	// Load relationships
	obj.Relationships = e.getRelationships(id)

	// Cache the object
	e.cache.Set(id, &obj)

	return &obj, nil
}

// GetObjectsInTile retrieves objects visible in a tile at given zoom level
func (e *Engine) GetObjectsInTile(zoom, tileX, tileY int) ([]*ArxObject, error) {
	// Calculate tile bounds in nanometers
	tileSize := e.getTileSizeNM(zoom)
	minX := int64(tileX) * tileSize
	maxX := minX + tileSize
	minY := int64(tileY) * tileSize
	maxY := minY + tileSize

	// Use spatial index for fast lookup
	candidates := e.spatialIndex.Query(minX, minY, maxX, maxY)
	
	var objects []*ArxObject
	for _, obj := range candidates {
		if obj.IsVisibleAtScale(zoom) {
			objects = append(objects, obj)
		}
	}

	// If no cached results, query database
	if len(objects) == 0 {
		query := `
			SELECT id, uuid, type, system, x, y, z,
				   width, height, depth, scale_min, scale_max,
				   building_id, floor_id, room_id,
				   properties, confidence
			FROM arx_objects
			WHERE x >= $1 AND x <= $2
			  AND y >= $3 AND y <= $4
			  AND scale_min <= $5 AND scale_max >= $5
			ORDER BY z, id
			LIMIT 1000
		`

		rows, err := e.db.Query(query, minX, maxX, minY, maxY, zoom)
		if err != nil {
			return nil, err
		}
		defer rows.Close()

		for rows.Next() {
			var obj ArxObject
			var confidenceJSON []byte
			
			err := rows.Scan(
				&obj.ID, &obj.UUID, &obj.Type, &obj.System, &obj.X, &obj.Y, &obj.Z,
				&obj.Width, &obj.Height, &obj.Depth, &obj.ScaleMin, &obj.ScaleMax,
				&obj.BuildingID, &obj.FloorID, &obj.RoomID,
				&obj.Properties, &confidenceJSON,
			)
			if err != nil {
				continue
			}

			json.Unmarshal(confidenceJSON, &obj.Confidence)
			objects = append(objects, &obj)
			
			// Add to spatial index
			e.spatialIndex.Insert(&obj)
		}
	}

	return objects, nil
}

// UpdateObject updates an existing ArxObject
func (e *Engine) UpdateObject(obj *ArxObject) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	obj.UpdatedAt = time.Now()
	obj.Confidence.CalculateOverall()

	query := `
		UPDATE arx_objects SET
			type = $2, system = $3, x = $4, y = $5, z = $6,
			width = $7, height = $8, depth = $9, 
			scale_min = $10, scale_max = $11,
			properties = $12, confidence = $13,
			updated_at = $14
		WHERE id = $1
	`

	confidenceJSON, _ := json.Marshal(obj.Confidence)

	_, err := e.db.Exec(query,
		obj.ID, obj.Type, obj.System, obj.X, obj.Y, obj.Z,
		obj.Width, obj.Height, obj.Depth,
		obj.ScaleMin, obj.ScaleMax,
		obj.Properties, confidenceJSON,
		obj.UpdatedAt,
	)

	if err != nil {
		return fmt.Errorf("failed to update ArxObject: %w", err)
	}

	// Update cache and spatial index
	e.cache.Set(obj.ID, obj)
	e.spatialIndex.Update(obj)

	return nil
}

// ValidateObject marks an object as validated
func (e *Engine) ValidateObject(objectID, validatorID string) error {
	obj, err := e.GetObject(objectID)
	if err != nil {
		return err
	}

	obj.Validate(validatorID)
	return e.UpdateObject(obj)
}

// FindSimilarObjects finds objects similar to the given one for pattern propagation
func (e *Engine) FindSimilarObjects(obj *ArxObject, maxDistance float64) ([]*ArxObject, error) {
	query := `
		SELECT id, uuid, type, system, x, y, z,
			   width, height, depth, scale_min, scale_max,
			   properties, confidence
		FROM arx_objects
		WHERE type = $1 AND system = $2
		  AND ABS(width - $3) < $4
		  AND ABS(height - $5) < $6
		  AND id != $7
		  AND validated_at IS NULL
		LIMIT 100
	`

	tolerance := int64(maxDistance * 1000000) // Convert to nanometers

	rows, err := e.db.Query(query,
		obj.Type, obj.System,
		obj.Width, tolerance,
		obj.Height, tolerance,
		obj.ID,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var similar []*ArxObject
	for rows.Next() {
		var simObj ArxObject
		var confidenceJSON []byte
		
		err := rows.Scan(
			&simObj.ID, &simObj.UUID, &simObj.Type, &simObj.System,
			&simObj.X, &simObj.Y, &simObj.Z,
			&simObj.Width, &simObj.Height, &simObj.Depth,
			&simObj.ScaleMin, &simObj.ScaleMax,
			&simObj.Properties, &confidenceJSON,
		)
		if err != nil {
			continue
		}

		json.Unmarshal(confidenceJSON, &simObj.Confidence)
		similar = append(similar, &simObj)
	}

	return similar, nil
}

// PropagateValidation applies validation from one object to similar objects
func (e *Engine) PropagateValidation(sourceID, validatorID string) (int, error) {
	source, err := e.GetObject(sourceID)
	if err != nil {
		return 0, err
	}

	// Find similar objects within 10% size tolerance
	similar, err := e.FindSimilarObjects(source, 0.1)
	if err != nil {
		return 0, err
	}

	count := 0
	for _, obj := range similar {
		// Only propagate to objects with lower confidence
		if obj.Confidence.Overall < source.Confidence.Overall {
			// Boost confidence but not as much as direct validation
			obj.Confidence.Classification = min(obj.Confidence.Classification*1.1, 0.9)
			obj.Confidence.Position = min(obj.Confidence.Position*1.1, 0.9)
			obj.Confidence.Properties = min(obj.Confidence.Properties*1.1, 0.9)
			obj.Confidence.CalculateOverall()
			
			if err := e.UpdateObject(obj); err == nil {
				count++
			}
		}
	}

	return count, nil
}

// GetObjectsByConfidence retrieves objects filtered by confidence level
func (e *Engine) GetObjectsByConfidence(minConfidence, maxConfidence float32) ([]*ArxObject, error) {
	query := `
		SELECT id, uuid, type, system, x, y, z,
			   width, height, depth, scale_min, scale_max,
			   properties, confidence
		FROM arx_objects
		WHERE (confidence->>'overall')::float >= $1
		  AND (confidence->>'overall')::float <= $2
		ORDER BY (confidence->>'overall')::float ASC
		LIMIT 1000
	`

	rows, err := e.db.Query(query, minConfidence, maxConfidence)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var objects []*ArxObject
	for rows.Next() {
		var obj ArxObject
		var confidenceJSON []byte
		
		err := rows.Scan(
			&obj.ID, &obj.UUID, &obj.Type, &obj.System,
			&obj.X, &obj.Y, &obj.Z,
			&obj.Width, &obj.Height, &obj.Depth,
			&obj.ScaleMin, &obj.ScaleMax,
			&obj.Properties, &confidenceJSON,
		)
		if err != nil {
			continue
		}

		json.Unmarshal(confidenceJSON, &obj.Confidence)
		objects = append(objects, &obj)
	}

	return objects, nil
}

// Helper methods

func (e *Engine) getTileSizeNM(zoom int) int64 {
	// Base tile size at zoom 0 is 10km = 10,000,000,000 nm
	baseTileSize := int64(10000000000000) // 10km in nanometers
	
	// Each zoom level divides by 2
	divisor := int64(math.Pow(2, float64(zoom)))
	return baseTileSize / divisor
}

func (e *Engine) addRelationship(objectID, targetID string) {
	e.relationshipMap[objectID] = append(e.relationshipMap[objectID], targetID)
	// Also add reverse relationship for bidirectional lookup
	e.relationshipMap[targetID] = append(e.relationshipMap[targetID], objectID)
}

func (e *Engine) getRelationships(objectID string) []Relationship {
	// This would query a relationships table in production
	// For now, return empty slice
	return []Relationship{}
}

// ObjectCache provides fast access to frequently used objects
type ObjectCache struct {
	objects map[string]*ArxObject
	mu      sync.RWMutex
	maxSize int
}

func NewObjectCache(maxSize int) *ObjectCache {
	return &ObjectCache{
		objects: make(map[string]*ArxObject),
		maxSize: maxSize,
	}
}

func (c *ObjectCache) Get(id string) (*ArxObject, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	obj, found := c.objects[id]
	return obj, found
}

func (c *ObjectCache) Set(id string, obj *ArxObject) {
	c.mu.Lock()
	defer c.mu.Unlock()
	
	// Simple eviction if cache is full
	if len(c.objects) >= c.maxSize {
		// Remove first item (simple FIFO)
		for k := range c.objects {
			delete(c.objects, k)
			break
		}
	}
	
	c.objects[id] = obj
}

// SpatialIndex provides fast spatial queries
type SpatialIndex struct {
	objects map[string]*ArxObject
	mu      sync.RWMutex
	// In production, would use R-tree or similar
}

func NewSpatialIndex() *SpatialIndex {
	return &SpatialIndex{
		objects: make(map[string]*ArxObject),
	}
}

func (si *SpatialIndex) Insert(obj *ArxObject) {
	si.mu.Lock()
	defer si.mu.Unlock()
	si.objects[obj.ID] = obj
}

func (si *SpatialIndex) Update(obj *ArxObject) {
	si.Insert(obj) // Simple replacement for now
}

func (si *SpatialIndex) Query(minX, minY, maxX, maxY int64) []*ArxObject {
	si.mu.RLock()
	defer si.mu.RUnlock()
	
	var results []*ArxObject
	for _, obj := range si.objects {
		if obj.X >= minX && obj.X <= maxX &&
		   obj.Y >= minY && obj.Y <= maxY {
			results = append(results, obj)
		}
	}
	return results
}

// min function is already defined in arxobject.go