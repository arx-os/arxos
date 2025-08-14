package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"math"
	"sync"
	"time"
)

// TileService handles tile generation and caching for Google Maps-like loading
type TileService struct {
	db    *sql.DB
	cache map[string]*TileCache
	mu    sync.RWMutex
}

// TileCache stores cached tile data
type TileCache struct {
	Data      []ArxObject
	Generated time.Time
	TTL       time.Duration
}

// ArxObject represents a building component
type ArxObject struct {
	ID           int64           `json:"id"`
	UUID         string          `json:"uuid"`
	Type         string          `json:"type"`
	System       string          `json:"system"`
	X            float64         `json:"x"`
	Y            float64         `json:"y"`
	Z            float64         `json:"z"`
	Width        int             `json:"width,omitempty"`
	Height       int             `json:"height,omitempty"`
	ScaleMin     int             `json:"scaleMin"`
	ScaleMax     int             `json:"scaleMax"`
	Properties   json.RawMessage `json:"properties,omitempty"`
	Manufacturer string          `json:"manufacturer,omitempty"`
	Model        string          `json:"model,omitempty"`
}

// TileBounds represents the geographic bounds of a tile
type TileBounds struct {
	MinLon float64
	MinLat float64
	MaxLon float64
	MaxLat float64
}

// NewTileService creates a new tile service
func NewTileService(db *sql.DB) *TileService {
	return &TileService{
		db:    db,
		cache: make(map[string]*TileCache),
	}
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

	// Calculate tile bounds
	bounds := t.tileToBounds(zoom, x, y)
	scale := t.zoomToScale(zoom)

	// Query database for objects in tile
	objects, err := t.queryObjects(bounds, scale)
	if err != nil {
		return nil, err
	}

	// Cache the result
	t.mu.Lock()
	t.cache[cacheKey] = &TileCache{
		Data:      objects,
		Generated: time.Now(),
		TTL:       5 * time.Minute,
	}
	t.mu.Unlock()

	// Also store in database cache
	go t.storeTileCache(zoom, x, y, objects)

	return objects, nil
}

// tileToBounds converts tile coordinates to geographic bounds
func (t *TileService) tileToBounds(zoom, x, y int) TileBounds {
	n := math.Pow(2, float64(zoom))
	
	minLon := float64(x)/n*360.0 - 180.0
	maxLon := float64(x+1)/n*360.0 - 180.0
	
	minLat := math.Atan(math.Sinh(math.Pi*(1-2*float64(y+1)/n))) * 180.0 / math.Pi
	maxLat := math.Atan(math.Sinh(math.Pi*(1-2*float64(y)/n))) * 180.0 / math.Pi
	
	return TileBounds{
		MinLon: minLon,
		MinLat: minLat,
		MaxLon: maxLon,
		MaxLat: maxLat,
	}
}

// zoomToScale maps zoom level to our fractal scale system
func (t *TileService) zoomToScale(zoom int) int {
	// Map zoom levels to our 10-level fractal scale
	scales := []int{
		10000000, // 0 - Continental
		1000000,  // 1 - Regional
		100000,   // 2 - Municipal  
		10000,    // 3 - Campus
		1000,     // 4 - Building
		100,      // 5 - Floor
		10,       // 6 - Room
		1,        // 7 - Component
		1,        // 8 - Circuit
		1,        // 9 - Trace
	}
	
	if zoom < 0 {
		zoom = 0
	}
	if zoom >= len(scales) {
		zoom = len(scales) - 1
	}
	
	return scales[zoom]
}

// queryObjects fetches objects from database within bounds at scale
func (t *TileService) queryObjects(bounds TileBounds, scale int) ([]ArxObject, error) {
	query := `
		SELECT 
			id, uuid, type, system,
			ST_X(geom) as x, ST_Y(geom) as y, ST_Z(geom) as z,
			width, height, scale_min, scale_max,
			properties, manufacturer, model
		FROM arx_objects
		WHERE 
			geom && ST_MakeEnvelope($1, $2, $3, $4, 4326)
			AND scale_min <= $5 
			AND scale_max >= $5
		ORDER BY z_order, id
		LIMIT 1000
	`
	
	rows, err := t.db.Query(query,
		bounds.MinLon, bounds.MinLat, bounds.MaxLon, bounds.MaxLat, scale)
	if err != nil {
		return nil, fmt.Errorf("query failed: %w", err)
	}
	defer rows.Close()
	
	var objects []ArxObject
	for rows.Next() {
		var obj ArxObject
		var manufacturer, model sql.NullString
		var properties sql.NullString
		
		err := rows.Scan(
			&obj.ID, &obj.UUID, &obj.Type, &obj.System,
			&obj.X, &obj.Y, &obj.Z,
			&obj.Width, &obj.Height,
			&obj.ScaleMin, &obj.ScaleMax,
			&properties, &manufacturer, &model,
		)
		if err != nil {
			continue
		}
		
		if manufacturer.Valid {
			obj.Manufacturer = manufacturer.String
		}
		if model.Valid {
			obj.Model = model.String
		}
		if properties.Valid {
			obj.Properties = json.RawMessage(properties.String)
		}
		
		objects = append(objects, obj)
	}
	
	return objects, nil
}

// storeTileCache saves tile data to database cache
func (t *TileService) storeTileCache(zoom, x, y int, objects []ArxObject) {
	data, err := json.Marshal(objects)
	if err != nil {
		return
	}
	
	query := `
		INSERT INTO arx_tiles (zoom, x, y, data, object_count, generated_at, expires_at)
		VALUES ($1, $2, $3, $4, $5, NOW(), NOW() + INTERVAL '1 hour')
		ON CONFLICT (zoom, x, y) 
		DO UPDATE SET 
			data = $4,
			object_count = $5,
			generated_at = NOW(),
			expires_at = NOW() + INTERVAL '1 hour'
	`
	
	t.db.Exec(query, zoom, x, y, data, len(objects))
}

// CleanCache removes expired tiles from memory and database
func (t *TileService) CleanCache() {
	// Clean memory cache
	t.mu.Lock()
	for key, cached := range t.cache {
		if time.Since(cached.Generated) > cached.TTL {
			delete(t.cache, key)
		}
	}
	t.mu.Unlock()
	
	// Clean database cache
	t.db.Exec("DELETE FROM arx_tiles WHERE expires_at < NOW()")
}

// PreloadArea preloads tiles for an area (predictive caching)
func (t *TileService) PreloadArea(centerLat, centerLon float64, zoom int, radius int) {
	centerX, centerY := t.latLonToTile(centerLat, centerLon, zoom)
	
	for dx := -radius; dx <= radius; dx++ {
		for dy := -radius; dy <= radius; dy++ {
			go t.GetTile(zoom, centerX+dx, centerY+dy)
		}
	}
}

// latLonToTile converts lat/lon to tile coordinates
func (t *TileService) latLonToTile(lat, lon float64, zoom int) (int, int) {
	n := math.Pow(2, float64(zoom))
	x := int((lon + 180.0) / 360.0 * n)
	y := int((1.0 - math.Log(math.Tan(lat*math.Pi/180.0)+1.0/math.Cos(lat*math.Pi/180.0))/math.Pi) / 2.0 * n)
	return x, y
}