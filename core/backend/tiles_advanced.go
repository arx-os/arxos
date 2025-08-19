package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"math"
	"sync"
	"time"

	"arxos/arxobject"
)

// AdvancedTileService provides fractal tile-based data loading
type AdvancedTileService struct {
	db        *sql.DB
	arxEngine *arxobject.Engine
	cache     *TileCache
	mu        sync.RWMutex
}

// NewAdvancedTileService creates a new advanced tile service
func NewAdvancedTileService(db *sql.DB) *AdvancedTileService {
	return &AdvancedTileService{
		db:        db,
		arxEngine: arxobject.NewEngine(db),
		cache:     NewTileCache(1000, 5*time.Minute),
	}
}

// GetTile returns ArxObjects for a specific tile at given zoom level
func (s *AdvancedTileService) GetTile(zoom, x, y int) (*TileData, error) {
	// Validate zoom level (0-9 for fractal scales)
	if zoom < 0 || zoom > 9 {
		return nil, fmt.Errorf("invalid zoom level: %d (must be 0-9)", zoom)
	}
	
	// Check cache first
	cacheKey := fmt.Sprintf("%d/%d/%d", zoom, x, y)
	if cached, found := s.cache.Get(cacheKey); found {
		log.Printf("Tile cache hit: %s", cacheKey)
		return cached, nil
	}
	
	// Calculate tile bounds in real-world coordinates
	bounds := s.calculateTileBounds(zoom, x, y)
	
	// Query ArxObjects within bounds
	objects, err := s.queryObjectsInBounds(bounds, zoom)
	if err != nil {
		return nil, fmt.Errorf("failed to query objects: %w", err)
	}
	
	// Apply level-of-detail optimization
	objects = s.applyLOD(objects, zoom)
	
	// Group objects by system for efficient rendering
	systemGroups := s.groupBySystem(objects)
	
	// Calculate tile statistics
	stats := s.calculateTileStats(objects)
	
	tileData := &TileData{
		Zoom:         zoom,
		X:            x,
		Y:            y,
		Bounds:       bounds,
		Objects:      objects,
		SystemGroups: systemGroups,
		Statistics:   stats,
		Generated:    time.Now(),
	}
	
	// Cache the tile
	s.cache.Set(cacheKey, tileData)
	
	return tileData, nil
}

// calculateTileBounds calculates real-world bounds for a tile
func (s *AdvancedTileService) calculateTileBounds(zoom, x, y int) TileBounds {
	// Fractal scaling: each zoom level represents a 10x change in scale
	// Zoom 0: Continental (10,000 km)
	// Zoom 1: Regional (1,000 km)
	// Zoom 2: Municipal (100 km)
	// Zoom 3: Campus (10 km)
	// Zoom 4: Building (1 km)
	// Zoom 5: Floor (100 m)
	// Zoom 6: Room (10 m)
	// Zoom 7: Component (1 m)
	// Zoom 8: Circuit (10 cm)
	// Zoom 9: Trace (1 cm)
	
	// Base size at zoom 0 in millimeters
	baseSize := float64(10000000000) // 10,000 km in mm
	
	// Calculate size for current zoom level
	tileSize := baseSize / math.Pow(10, float64(zoom))
	
	// Calculate bounds
	minX := float64(x) * tileSize
	minY := float64(y) * tileSize
	maxX := minX + tileSize
	maxY := minY + tileSize
	
	// Determine appropriate unit for this scale
	unit := s.getAppropriateUnit(zoom)
	
	return TileBounds{
		MinX:     minX,
		MinY:     minY,
		MaxX:     maxX,
		MaxY:     maxY,
		Width:    tileSize,
		Height:   tileSize,
		Unit:     unit,
		RealSize: s.formatRealSize(tileSize),
	}
}

// queryObjectsInBounds queries ArxObjects within spatial bounds
func (s *AdvancedTileService) queryObjectsInBounds(bounds TileBounds, zoom int) ([]*TileObject, error) {
	// Convert bounds to nanometers for database query
	minXNM := int64(bounds.MinX * 1000000)
	maxXNM := int64(bounds.MaxX * 1000000)
	minYNM := int64(bounds.MinY * 1000000)
	maxYNM := int64(bounds.MaxY * 1000000)
	
	query := `
		SELECT 
			id, uuid, type, system, x, y, z,
			width, height, depth, scale_min, scale_max,
			building_id, floor_id, room_id,
			properties, confidence,
			extraction_method, validated_at
		FROM arx_objects
		WHERE x >= $1 AND x <= $2
		  AND y >= $3 AND y <= $4
		  AND scale_min <= $5 AND scale_max >= $5
		ORDER BY z DESC, system, type
		LIMIT $6
	`
	
	// Adjust limit based on zoom level (fewer objects at lower zoom)
	limit := s.getQueryLimit(zoom)
	
	rows, err := s.db.Query(query, minXNM, maxXNM, minYNM, maxYNM, zoom, limit)
	if err != nil {
		// If table doesn't exist, return empty result
		if err.Error() == `pq: relation "arx_objects" does not exist` {
			return []*TileObject{}, nil
		}
		return nil, err
	}
	defer rows.Close()
	
	var objects []*TileObject
	
	for rows.Next() {
		var obj TileObject
		var props json.RawMessage
		var confJSON []byte
		var validatedAt sql.NullTime
		
		err := rows.Scan(
			&obj.ID, &obj.UUID, &obj.Type, &obj.System,
			&obj.X, &obj.Y, &obj.Z,
			&obj.Width, &obj.Height, &obj.Depth,
			&obj.ScaleMin, &obj.ScaleMax,
			&obj.BuildingID, &obj.FloorID, &obj.RoomID,
			&props, &confJSON,
			&obj.ExtractionMethod, &validatedAt,
		)
		if err != nil {
			log.Printf("Error scanning object: %v", err)
			continue
		}
		
		// Convert nanometers to millimeters for client
		obj.X = obj.X / 1000000
		obj.Y = obj.Y / 1000000
		obj.Z = obj.Z / 1000000
		obj.Width = obj.Width / 1000000
		obj.Height = obj.Height / 1000000
		obj.Depth = obj.Depth / 1000000
		
		// Parse confidence
		var conf arxobject.ConfidenceScore
		if err := json.Unmarshal(confJSON, &conf); err == nil {
			obj.Confidence = conf.Overall
			obj.ConfidenceLevel = s.getConfidenceLevel(conf.Overall)
		}
		
		// Parse properties for display
		if err := json.Unmarshal(props, &obj.Properties); err == nil {
			// Successfully parsed
		}
		
		obj.Validated = validatedAt.Valid
		
		// Calculate render priority
		obj.RenderPriority = s.calculateRenderPriority(&obj, zoom)
		
		objects = append(objects, &obj)
	}
	
	return objects, nil
}

// applyLOD applies level-of-detail optimization
func (s *AdvancedTileService) applyLOD(objects []*TileObject, zoom int) []*TileObject {
	// At lower zoom levels, simplify or aggregate objects
	if zoom <= 3 { // Campus level and above
		return s.aggregateObjects(objects)
	}
	
	if zoom <= 5 { // Floor level and above
		return s.simplifyObjects(objects)
	}
	
	// At detailed zoom levels, return all objects
	return objects
}

// aggregateObjects combines multiple objects into summary objects
func (s *AdvancedTileService) aggregateObjects(objects []*TileObject) []*TileObject {
	// Group by building and create building summary objects
	buildingGroups := make(map[int64][]*TileObject)
	
	for _, obj := range objects {
		if obj.BuildingID != nil {
			buildingGroups[*obj.BuildingID] = append(buildingGroups[*obj.BuildingID], obj)
		}
	}
	
	var aggregated []*TileObject
	
	for buildingID, group := range buildingGroups {
		// Calculate building bounds
		minX, minY := math.MaxFloat64, math.MaxFloat64
		maxX, maxY := -math.MaxFloat64, -math.MaxFloat64
		
		systemCounts := make(map[string]int)
		totalConfidence := float32(0)
		
		for _, obj := range group {
			minX = math.Min(minX, obj.X)
			minY = math.Min(minY, obj.Y)
			maxX = math.Max(maxX, obj.X+obj.Width)
			maxY = math.Max(maxY, obj.Y+obj.Height)
			systemCounts[obj.System]++
			totalConfidence += obj.Confidence
		}
		
		// Create aggregated building object
		buildingObj := &TileObject{
			ID:     fmt.Sprintf("building_%d", buildingID),
			Type:   "building_aggregate",
			System: "structural",
			X:      minX,
			Y:      minY,
			Width:  maxX - minX,
			Height: maxY - minY,
			Properties: map[string]interface{}{
				"object_count":   len(group),
				"system_counts":  systemCounts,
				"building_id":    buildingID,
			},
			Confidence:      totalConfidence / float32(len(group)),
			RenderPriority:  100, // High priority for building outlines
		}
		
		aggregated = append(aggregated, buildingObj)
	}
	
	return aggregated
}

// simplifyObjects reduces detail for mid-level zoom
func (s *AdvancedTileService) simplifyObjects(objects []*TileObject) []*TileObject {
	var simplified []*TileObject
	
	// Keep only major structural elements and systems
	majorTypes := map[string]bool{
		"building": true,
		"floor":    true,
		"room":     true,
		"wall":     true,
		"column":   true,
		"corridor": true,
	}
	
	for _, obj := range objects {
		if majorTypes[obj.Type] || obj.RenderPriority > 50 {
			simplified = append(simplified, obj)
		}
	}
	
	return simplified
}

// groupBySystem groups objects by their system
func (s *AdvancedTileService) groupBySystem(objects []*TileObject) map[string][]*TileObject {
	groups := make(map[string][]*TileObject)
	
	for _, obj := range objects {
		groups[obj.System] = append(groups[obj.System], obj)
	}
	
	return groups
}

// calculateTileStats calculates statistics for the tile
func (s *AdvancedTileService) calculateTileStats(objects []*TileObject) TileStatistics {
	stats := TileStatistics{
		ObjectCount:   len(objects),
		SystemCounts:  make(map[string]int),
		TypeCounts:    make(map[string]int),
	}
	
	var totalConfidence float32
	highConf, medConf, lowConf := 0, 0, 0
	validated := 0
	
	for _, obj := range objects {
		stats.SystemCounts[obj.System]++
		stats.TypeCounts[obj.Type]++
		totalConfidence += obj.Confidence
		
		switch obj.ConfidenceLevel {
		case "high":
			highConf++
		case "medium":
			medConf++
		case "low":
			lowConf++
		}
		
		if obj.Validated {
			validated++
		}
	}
	
	if len(objects) > 0 {
		stats.AverageConfidence = totalConfidence / float32(len(objects))
	}
	
	stats.HighConfidence = highConf
	stats.MediumConfidence = medConf
	stats.LowConfidence = lowConf
	stats.ValidatedCount = validated
	
	return stats
}

// Helper methods

func (s *AdvancedTileService) getAppropriateUnit(zoom int) string {
	units := []string{
		"km",  // 0: Continental
		"km",  // 1: Regional
		"km",  // 2: Municipal
		"km",  // 3: Campus
		"m",   // 4: Building
		"m",   // 5: Floor
		"m",   // 6: Room
		"cm",  // 7: Component
		"mm",  // 8: Circuit
		"mm",  // 9: Trace
	}
	
	if zoom >= 0 && zoom < len(units) {
		return units[zoom]
	}
	return "m"
}

func (s *AdvancedTileService) formatRealSize(sizeInMM float64) string {
	if sizeInMM >= 1000000 { // >= 1km
		return fmt.Sprintf("%.1f km", sizeInMM/1000000)
	} else if sizeInMM >= 1000 { // >= 1m
		return fmt.Sprintf("%.1f m", sizeInMM/1000)
	} else if sizeInMM >= 10 { // >= 1cm
		return fmt.Sprintf("%.1f cm", sizeInMM/10)
	}
	return fmt.Sprintf("%.1f mm", sizeInMM)
}

func (s *AdvancedTileService) getQueryLimit(zoom int) int {
	// Fewer objects at lower zoom levels
	limits := []int{
		100,   // 0: Continental
		200,   // 1: Regional
		500,   // 2: Municipal
		1000,  // 3: Campus
		2000,  // 4: Building
		5000,  // 5: Floor
		10000, // 6: Room
		10000, // 7: Component
		10000, // 8: Circuit
		10000, // 9: Trace
	}
	
	if zoom >= 0 && zoom < len(limits) {
		return limits[zoom]
	}
	return 1000
}

func (s *AdvancedTileService) getConfidenceLevel(confidence float32) string {
	if confidence > 0.85 {
		return "high"
	} else if confidence >= 0.60 {
		return "medium"
	}
	return "low"
}

func (s *AdvancedTileService) calculateRenderPriority(obj *TileObject, zoom int) int {
	priority := 50 // Base priority
	
	// Structural elements have higher priority
	if obj.System == "structural" {
		priority += 20
	}
	
	// Larger objects have higher priority at lower zoom
	if zoom <= 5 {
		area := obj.Width * obj.Height
		if area > 10000 { // > 10 sqm
			priority += 30
		} else if area > 1000 { // > 1 sqm
			priority += 20
		}
	}
	
	// Validated objects have higher priority
	if obj.Validated {
		priority += 10
	}
	
	// High confidence objects have higher priority
	if obj.Confidence > 0.85 {
		priority += 10
	}
	
	return priority
}

// GetScaleInfo returns information about the current scale level
func (s *AdvancedTileService) GetScaleInfo(zoom int) ScaleInfo {
	scales := []ScaleInfo{
		{Level: 0, Name: "CONTINENTAL", Description: "Continental infrastructure", TileSize: "10,000 km", MinFeature: "Power grids"},
		{Level: 1, Name: "REGIONAL", Description: "State/province level", TileSize: "1,000 km", MinFeature: "Cities"},
		{Level: 2, Name: "MUNICIPAL", Description: "City level", TileSize: "100 km", MinFeature: "Districts"},
		{Level: 3, Name: "CAMPUS", Description: "Multi-building sites", TileSize: "10 km", MinFeature: "Buildings"},
		{Level: 4, Name: "BUILDING", Description: "Individual structures", TileSize: "1 km", MinFeature: "Floors"},
		{Level: 5, Name: "FLOOR", Description: "Floor plates", TileSize: "100 m", MinFeature: "Rooms"},
		{Level: 6, Name: "ROOM", Description: "Individual spaces", TileSize: "10 m", MinFeature: "Walls"},
		{Level: 7, Name: "COMPONENT", Description: "Equipment level", TileSize: "1 m", MinFeature: "Fixtures"},
		{Level: 8, Name: "CIRCUIT", Description: "Circuit board level", TileSize: "10 cm", MinFeature: "Components"},
		{Level: 9, Name: "TRACE", Description: "Nanometer precision", TileSize: "1 cm", MinFeature: "Traces"},
	}
	
	if zoom >= 0 && zoom < len(scales) {
		return scales[zoom]
	}
	
	return ScaleInfo{Level: zoom, Name: "UNKNOWN"}
}

// ClearCache clears the tile cache
func (s *AdvancedTileService) ClearCache() {
	s.cache.Clear()
	log.Println("Tile cache cleared")
}

// Types

type TileData struct {
	Zoom         int                        `json:"zoom"`
	X            int                        `json:"x"`
	Y            int                        `json:"y"`
	Bounds       TileBounds                 `json:"bounds"`
	Objects      []*TileObject              `json:"objects"`
	SystemGroups map[string][]*TileObject   `json:"system_groups"`
	Statistics   TileStatistics             `json:"statistics"`
	Generated    time.Time                  `json:"generated"`
}

type TileBounds struct {
	MinX     float64 `json:"min_x"`
	MinY     float64 `json:"min_y"`
	MaxX     float64 `json:"max_x"`
	MaxY     float64 `json:"max_y"`
	Width    float64 `json:"width"`
	Height   float64 `json:"height"`
	Unit     string  `json:"unit"`
	RealSize string  `json:"real_size"`
}

type TileObject struct {
	ID               string                 `json:"id"`
	UUID             string                 `json:"uuid,omitempty"`
	Type             string                 `json:"type"`
	System           string                 `json:"system"`
	X                float64                `json:"x"`
	Y                float64                `json:"y"`
	Z                float64                `json:"z"`
	Width            float64                `json:"width"`
	Height           float64                `json:"height"`
	Depth            float64                `json:"depth"`
	ScaleMin         int                    `json:"scale_min"`
	ScaleMax         int                    `json:"scale_max"`
	BuildingID       *int64                 `json:"building_id,omitempty"`
	FloorID          *int64                 `json:"floor_id,omitempty"`
	RoomID           *int64                 `json:"room_id,omitempty"`
	Properties       map[string]interface{} `json:"properties"`
	Confidence       float32                `json:"confidence"`
	ConfidenceLevel  string                 `json:"confidence_level"`
	ExtractionMethod string                 `json:"extraction_method"`
	Validated        bool                   `json:"validated"`
	RenderPriority   int                    `json:"render_priority"`
}

type TileStatistics struct {
	ObjectCount       int            `json:"object_count"`
	SystemCounts      map[string]int `json:"system_counts"`
	TypeCounts        map[string]int `json:"type_counts"`
	AverageConfidence float32        `json:"average_confidence"`
	HighConfidence    int            `json:"high_confidence"`
	MediumConfidence  int            `json:"medium_confidence"`
	LowConfidence     int            `json:"low_confidence"`
	ValidatedCount    int            `json:"validated_count"`
}

type ScaleInfo struct {
	Level       int    `json:"level"`
	Name        string `json:"name"`
	Description string `json:"description"`
	TileSize    string `json:"tile_size"`
	MinFeature  string `json:"min_feature"`
}

// TileCache provides caching for tile data
type TileCache struct {
	cache map[string]*TileCacheEntry
	mu    sync.RWMutex
	maxSize int
	ttl     time.Duration
}

type TileCacheEntry struct {
	Data      *TileData
	ExpiresAt time.Time
}

func NewTileCache(maxSize int, ttl time.Duration) *TileCache {
	cache := &TileCache{
		cache:   make(map[string]*TileCacheEntry),
		maxSize: maxSize,
		ttl:     ttl,
	}
	
	// Start cleanup goroutine
	go cache.cleanup()
	
	return cache
}

func (c *TileCache) Get(key string) (*TileData, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	
	entry, found := c.cache[key]
	if !found {
		return nil, false
	}
	
	// Check expiration
	if time.Now().After(entry.ExpiresAt) {
		return nil, false
	}
	
	return entry.Data, true
}

func (c *TileCache) Set(key string, data *TileData) {
	c.mu.Lock()
	defer c.mu.Unlock()
	
	// Simple eviction if cache is full
	if len(c.cache) >= c.maxSize {
		// Remove oldest entry
		var oldestKey string
		oldestTime := time.Now()
		
		for k, v := range c.cache {
			if v.ExpiresAt.Before(oldestTime) {
				oldestKey = k
				oldestTime = v.ExpiresAt
			}
		}
		
		if oldestKey != "" {
			delete(c.cache, oldestKey)
		}
	}
	
	c.cache[key] = &TileCacheEntry{
		Data:      data,
		ExpiresAt: time.Now().Add(c.ttl),
	}
}

func (c *TileCache) Clear() {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.cache = make(map[string]*TileCacheEntry)
}

func (c *TileCache) cleanup() {
	ticker := time.NewTicker(1 * time.Minute)
	defer ticker.Stop()
	
	for range ticker.C {
		c.mu.Lock()
		now := time.Now()
		
		for key, entry := range c.cache {
			if now.After(entry.ExpiresAt) {
				delete(c.cache, key)
			}
		}
		
		c.mu.Unlock()
	}
}