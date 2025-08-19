package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"math"
	"math/rand"
	"sync"
	"time"
)

// TileService handles tile generation and caching
type TileService struct {
	db         *sql.DB
	cache      map[string]*TileCache
	mu         sync.RWMutex
	demoMode   bool
	demoObjects []ArxObject
}

// TileCache stores cached tile data
type TileCache struct {
	Data      []ArxObject
	Generated time.Time
	TTL       time.Duration
}

// ArxObject represents a building component
type ArxObject struct {
	ID       int64   `json:"id"`
	UUID     string  `json:"uuid"`
	Type     string  `json:"type"`
	System   string  `json:"system"`
	X        float64 `json:"x"`
	Y        float64 `json:"y"`
	Z        float64 `json:"z"`
	Width    int     `json:"width,omitempty"`
	Height   int     `json:"height,omitempty"`
	ScaleMin int     `json:"scaleMin"`
	ScaleMax int     `json:"scaleMax"`
	Properties json.RawMessage `json:"properties,omitempty"`
}

// NewTileService creates a new tile service
func NewTileService(db *sql.DB) *TileService {
	ts := &TileService{
		db:    db,
		cache: make(map[string]*TileCache),
		demoMode: db == nil,
	}
	
	if ts.demoMode {
		ts.initDemoData()
	} else {
		// Try to create tables if they don't exist
		ts.initDatabase()
	}
	
	return ts
}

// Initialize database tables
func (t *TileService) initDatabase() {
	if t.db == nil {
		return
	}

	// Create ArxObjects table if it doesn't exist
	query := `
	CREATE TABLE IF NOT EXISTS arx_objects (
		id SERIAL PRIMARY KEY,
		uuid VARCHAR(36) DEFAULT gen_random_uuid(),
		type VARCHAR(50),
		system VARCHAR(50),
		x FLOAT,
		y FLOAT,
		z FLOAT,
		width INTEGER DEFAULT 10,
		height INTEGER DEFAULT 10,
		scale_min INTEGER DEFAULT 0,
		scale_max INTEGER DEFAULT 10,
		properties JSONB,
		created_at TIMESTAMP DEFAULT NOW()
	);
	
	CREATE INDEX IF NOT EXISTS idx_arx_objects_position ON arx_objects(x, y);
	CREATE INDEX IF NOT EXISTS idx_arx_objects_scale ON arx_objects(scale_min, scale_max);
	`
	
	if _, err := t.db.Exec(query); err != nil {
		log.Printf("Warning: Could not create tables: %v", err)
	} else {
		log.Println("✅ Database tables initialized")
		
		// Check if we have any data
		var count int
		t.db.QueryRow("SELECT COUNT(*) FROM arx_objects").Scan(&count)
		
		if count == 0 {
			log.Println("📝 Inserting demo data into database...")
			t.insertDemoData()
		} else {
			log.Printf("📊 Found %d existing ArxObjects in database", count)
		}
	}
}

// Insert demo data into database
func (t *TileService) insertDemoData() {
	if t.db == nil {
		return
	}

	// Create a demo floor plan
	objects := t.generateDemoFloorPlan()
	
	for _, obj := range objects {
		query := `
		INSERT INTO arx_objects (type, system, x, y, z, width, height, scale_min, scale_max)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
		`
		_, err := t.db.Exec(query, obj.Type, obj.System, obj.X, obj.Y, obj.Z, 
			obj.Width, obj.Height, obj.ScaleMin, obj.ScaleMax)
		if err != nil {
			log.Printf("Failed to insert demo object: %v", err)
		}
	}
	
	log.Printf("✅ Inserted %d demo objects", len(objects))
}

// Initialize demo data for when database is not available
func (t *TileService) initDemoData() {
	t.demoObjects = t.generateDemoFloorPlan()
	log.Printf("🎮 Demo mode: Generated %d demo objects", len(t.demoObjects))
}

// Generate demo floor plan
func (t *TileService) generateDemoFloorPlan() []ArxObject {
	var objects []ArxObject
	id := int64(1)
	
	// Create 5 floors
	for floor := 0; floor < 5; floor++ {
		baseY := float64(floor * 500)
		
		// Outer walls
		walls := []struct{ x, y, w, h float64 }{
			{0, baseY, 1000, 10},      // Top
			{0, baseY + 490, 1000, 10}, // Bottom
			{0, baseY, 10, 500},        // Left
			{990, baseY, 10, 500},      // Right
		}
		
		for _, wall := range walls {
			objects = append(objects, ArxObject{
				ID:       id,
				UUID:     fmt.Sprintf("wall-%d", id),
				Type:     "wall",
				System:   "structural",
				X:        wall.x,
				Y:        wall.y,
				Width:    int(wall.w),
				Height:   int(wall.h),
				ScaleMin: 4,
				ScaleMax: 10,
			})
			id++
		}
		
		// Rooms (4 per floor)
		for i := 0; i < 2; i++ {
			for j := 0; j < 2; j++ {
				roomX := float64(i*500 + 50)
				roomY := baseY + float64(j*250+50)
				
				// Room walls
				objects = append(objects, ArxObject{
					ID:       id,
					UUID:     fmt.Sprintf("room-%d", id),
					Type:     "room",
					System:   "structural",
					X:        roomX,
					Y:        roomY,
					Width:    400,
					Height:   200,
					ScaleMin: 5,
					ScaleMax: 10,
				})
				id++
				
				// Electrical outlets
				objects = append(objects, ArxObject{
					ID:       id,
					UUID:     fmt.Sprintf("outlet-%d", id),
					Type:     "outlet",
					System:   "electrical",
					X:        roomX + 20,
					Y:        roomY + 20,
					Width:    15,
					Height:   15,
					ScaleMin: 6,
					ScaleMax: 10,
				})
				id++
				
				// HVAC vent
				objects = append(objects, ArxObject{
					ID:       id,
					UUID:     fmt.Sprintf("vent-%d", id),
					Type:     "vent",
					System:   "hvac",
					X:        roomX + 200,
					Y:        roomY + 100,
					Width:    40,
					Height:   20,
					ScaleMin: 6,
					ScaleMax: 10,
				})
				id++
			}
		}
		
		// Plumbing (bathrooms)
		objects = append(objects, ArxObject{
			ID:       id,
			UUID:     fmt.Sprintf("plumbing-%d", id),
			Type:     "pipe",
			System:   "plumbing",
			X:        450,
			Y:        baseY + 200,
			Width:    5,
			Height:   100,
			ScaleMin: 7,
			ScaleMax: 10,
		})
		id++
	}
	
	return objects
}

// GetTile retrieves objects for a specific tile
func (t *TileService) GetTile(zoom, x, y int) ([]ArxObject, error) {
	// Check cache first
	cacheKey := fmt.Sprintf("%d/%d/%d", zoom, x, y)
	
	t.mu.RLock()
	if cached, exists := t.cache[cacheKey]; exists {
		if time.Since(cached.Generated) < cached.TTL {
			t.mu.RUnlock()
			return cached.Data, nil
		}
	}
	t.mu.RUnlock()

	// Get objects for this tile
	var objects []ArxObject
	
	if t.demoMode {
		// Return demo objects filtered by tile bounds
		bounds := t.tileToBounds(zoom, x, y)
		for _, obj := range t.demoObjects {
			if obj.X >= bounds.MinX && obj.X <= bounds.MaxX &&
			   obj.Y >= bounds.MinY && obj.Y <= bounds.MaxY &&
			   zoom >= obj.ScaleMin && zoom <= obj.ScaleMax {
				objects = append(objects, obj)
			}
		}
	} else if t.db != nil {
		// Query database
		bounds := t.tileToBounds(zoom, x, y)
		query := `
		SELECT id, uuid, type, system, x, y, z, width, height, scale_min, scale_max
		FROM arx_objects
		WHERE x >= $1 AND x <= $2 AND y >= $3 AND y <= $4
		AND scale_min <= $5 AND scale_max >= $5
		LIMIT 1000
		`
		
		rows, err := t.db.Query(query, bounds.MinX, bounds.MaxX, bounds.MinY, bounds.MaxY, zoom)
		if err != nil {
			log.Printf("Database query failed: %v", err)
			return t.getFallbackObjects(zoom, x, y), nil
		}
		defer rows.Close()
		
		for rows.Next() {
			var obj ArxObject
			err := rows.Scan(&obj.ID, &obj.UUID, &obj.Type, &obj.System,
				&obj.X, &obj.Y, &obj.Z, &obj.Width, &obj.Height,
				&obj.ScaleMin, &obj.ScaleMax)
			if err != nil {
				continue
			}
			objects = append(objects, obj)
		}
	}

	// Cache the result
	t.mu.Lock()
	t.cache[cacheKey] = &TileCache{
		Data:      objects,
		Generated: time.Now(),
		TTL:       5 * time.Minute,
	}
	t.mu.Unlock()

	return objects, nil
}

// TileBounds for simplified tile calculation
type TileBounds struct {
	MinX, MaxX float64
	MinY, MaxY float64
}

// tileToBounds converts tile coordinates to bounds
func (t *TileService) tileToBounds(zoom, x, y int) TileBounds {
	// Simplified tile bounds (not geographic projection)
	tileSize := 256.0 * math.Pow(2, float64(10-zoom))
	
	return TileBounds{
		MinX: float64(x) * tileSize,
		MaxX: float64(x+1) * tileSize,
		MinY: float64(y) * tileSize,
		MaxY: float64(y+1) * tileSize,
	}
}

// getFallbackObjects returns demo objects when database fails
func (t *TileService) getFallbackObjects(zoom, x, y int) []ArxObject {
	var objects []ArxObject
	
	// Generate some random objects for this tile
	rand.Seed(int64(zoom + x*100 + y*10000))
	
	for i := 0; i < 10; i++ {
		objects = append(objects, ArxObject{
			ID:     int64(i),
			UUID:   fmt.Sprintf("demo-%d-%d-%d-%d", zoom, x, y, i),
			Type:   []string{"wall", "door", "window", "outlet"}[rand.Intn(4)],
			System: []string{"structural", "electrical", "hvac", "plumbing"}[rand.Intn(4)],
			X:      float64(x*256 + rand.Intn(256)),
			Y:      float64(y*256 + rand.Intn(256)),
			Width:  10 + rand.Intn(50),
			Height: 10 + rand.Intn(50),
			ScaleMin: 0,
			ScaleMax: 10,
		})
	}
	
	return objects
}

// GetAllObjects returns all objects (for testing)
func (t *TileService) GetAllObjects() []ArxObject {
	if t.demoMode {
		return t.demoObjects
	}
	
	if t.db == nil {
		return []ArxObject{}
	}
	
	var objects []ArxObject
	query := `SELECT id, uuid, type, system, x, y, z, width, height, scale_min, scale_max FROM arx_objects LIMIT 1000`
	
	rows, err := t.db.Query(query)
	if err != nil {
		log.Printf("Failed to get all objects: %v", err)
		return []ArxObject{}
	}
	defer rows.Close()
	
	for rows.Next() {
		var obj ArxObject
		rows.Scan(&obj.ID, &obj.UUID, &obj.Type, &obj.System,
			&obj.X, &obj.Y, &obj.Z, &obj.Width, &obj.Height, &obj.ScaleMin, &obj.ScaleMax)
		objects = append(objects, obj)
	}
	
	return objects
}

// CreateObject creates a new ArxObject
func (t *TileService) CreateObject(obj *ArxObject) error {
	if t.demoMode {
		obj.ID = int64(len(t.demoObjects) + 1)
		obj.UUID = fmt.Sprintf("demo-%d", obj.ID)
		t.demoObjects = append(t.demoObjects, *obj)
		return nil
	}
	
	if t.db == nil {
		return fmt.Errorf("database not available")
	}
	
	query := `
	INSERT INTO arx_objects (type, system, x, y, z, width, height, scale_min, scale_max)
	VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
	RETURNING id, uuid
	`
	
	err := t.db.QueryRow(query, obj.Type, obj.System, obj.X, obj.Y, obj.Z,
		obj.Width, obj.Height, obj.ScaleMin, obj.ScaleMax).Scan(&obj.ID, &obj.UUID)
	
	if err != nil {
		return fmt.Errorf("failed to create object: %w", err)
	}
	
	// Clear cache for affected area
	t.clearCache()
	
	return nil
}

// clearCache clears the tile cache
func (t *TileService) clearCache() {
	t.mu.Lock()
	t.cache = make(map[string]*TileCache)
	t.mu.Unlock()
}