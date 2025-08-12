// Tile Server for Fractal ArxObject System
// Provides map-style tile loading for efficient viewport rendering

package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/gorilla/mux"
	_ "github.com/lib/pq"
	"github.com/minio/minio-go/v7"
	"github.com/minio/minio-go/v7/pkg/credentials"
	"github.com/redis/go-redis/v9"
	"github.com/rs/cors"
	"github.com/sirupsen/logrus"
)

type Server struct {
	db          *sql.DB
	redis       *redis.Client
	minio       *minio.Client
	logger      *logrus.Logger
	cacheTTL    time.Duration
}

type TileRequest struct {
	Z     int     `json:"z"`
	X     int     `json:"x"`
	Y     int     `json:"y"`
	Scale float64 `json:"scale"`
}

type TileResponse struct {
	Tile    TileCoordinate  `json:"tile"`
	Bounds  BoundingBox     `json:"bounds"`
	Objects []FractalObject `json:"objects"`
	Count   int             `json:"count"`
	Cached  bool            `json:"cached"`
}

type TileCoordinate struct {
	Z int `json:"z"`
	X int `json:"x"`
	Y int `json:"y"`
}

type BoundingBox struct {
	MinX float64 `json:"min_x"`
	MinY float64 `json:"min_y"`
	MaxX float64 `json:"max_x"`
	MaxY float64 `json:"max_y"`
}

type FractalObject struct {
	ID         string                 `json:"id"`
	Type       string                 `json:"type"`
	Name       string                 `json:"name,omitempty"`
	X          float64                `json:"x"`
	Y          float64                `json:"y"`
	Z          float64                `json:"z"`
	Importance int                    `json:"importance"`
	Properties map[string]interface{} `json:"properties,omitempty"`
}

func NewServer() (*Server, error) {
	// Initialize logger
	logger := logrus.New()
	logger.SetFormatter(&logrus.JSONFormatter{})
	
	// Connect to PostgreSQL
	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		dbURL = "postgresql://arxos:arxos_dev_2025@localhost:5433/arxos_fractal?sslmode=disable"
	}
	
	db, err := sql.Open("postgres", dbURL)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to database: %w", err)
	}
	
	// Test database connection
	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}
	
	// Connect to Redis
	redisURL := os.Getenv("REDIS_URL")
	if redisURL == "" {
		redisURL = "redis://localhost:6380/1"
	}
	
	opt, err := redis.ParseURL(redisURL)
	if err != nil {
		return nil, fmt.Errorf("failed to parse Redis URL: %w", err)
	}
	
	redisClient := redis.NewClient(opt)
	
	// Test Redis connection
	ctx := context.Background()
	if err := redisClient.Ping(ctx).Err(); err != nil {
		return nil, fmt.Errorf("failed to connect to Redis: %w", err)
	}
	
	// Connect to MinIO
	minioEndpoint := os.Getenv("MINIO_ENDPOINT")
	if minioEndpoint == "" {
		minioEndpoint = "localhost:9000"
	}
	
	minioAccessKey := os.Getenv("MINIO_ACCESS_KEY")
	if minioAccessKey == "" {
		minioAccessKey = "arxos"
	}
	
	minioSecretKey := os.Getenv("MINIO_SECRET_KEY")
	if minioSecretKey == "" {
		minioSecretKey = "arxos_minio_2025"
	}
	
	minioClient, err := minio.New(minioEndpoint, &minio.Options{
		Creds:  credentials.NewStaticV4(minioAccessKey, minioSecretKey, ""),
		Secure: false,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to connect to MinIO: %w", err)
	}
	
	// Create bucket if it doesn't exist
	bucketName := "arxos-tiles"
	exists, err := minioClient.BucketExists(ctx, bucketName)
	if err != nil {
		return nil, fmt.Errorf("failed to check bucket existence: %w", err)
	}
	
	if !exists {
		err = minioClient.MakeBucket(ctx, bucketName, minio.MakeBucketOptions{})
		if err != nil {
			return nil, fmt.Errorf("failed to create bucket: %w", err)
		}
		logger.Info("Created MinIO bucket: " + bucketName)
	}
	
	return &Server{
		db:       db,
		redis:    redisClient,
		minio:    minioClient,
		logger:   logger,
		cacheTTL: 5 * time.Minute,
	}, nil
}

func (s *Server) getTileHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	
	z, err := strconv.Atoi(vars["z"])
	if err != nil {
		http.Error(w, "Invalid z parameter", http.StatusBadRequest)
		return
	}
	
	x, err := strconv.Atoi(vars["x"])
	if err != nil {
		http.Error(w, "Invalid x parameter", http.StatusBadRequest)
		return
	}
	
	y, err := strconv.Atoi(vars["y"])
	if err != nil {
		http.Error(w, "Invalid y parameter", http.StatusBadRequest)
		return
	}
	
	// Get scale from query parameter
	scaleStr := r.URL.Query().Get("scale")
	scale := 1.0 // Default scale
	if scaleStr != "" {
		scale, err = strconv.ParseFloat(scaleStr, 64)
		if err != nil {
			http.Error(w, "Invalid scale parameter", http.StatusBadRequest)
			return
		}
	}
	
	// Try to get from cache first
	ctx := r.Context()
	cacheKey := fmt.Sprintf("tile:%d:%d:%d:%.8f", z, x, y, scale)
	
	cached, err := s.redis.Get(ctx, cacheKey).Result()
	if err == nil && cached != "" {
		// Cache hit
		w.Header().Set("Content-Type", "application/json")
		w.Header().Set("X-Cache", "HIT")
		w.Write([]byte(cached))
		
		s.logger.WithFields(logrus.Fields{
			"z": z, "x": x, "y": y, "scale": scale, "cache": "hit",
		}).Debug("Tile served from cache")
		return
	}
	
	// Cache miss - load from database
	tile, err := s.loadTile(ctx, z, x, y, scale)
	if err != nil {
		s.logger.WithError(err).Error("Failed to load tile")
		http.Error(w, "Failed to load tile", http.StatusInternalServerError)
		return
	}
	
	// Serialize response
	response, err := json.Marshal(tile)
	if err != nil {
		s.logger.WithError(err).Error("Failed to serialize tile")
		http.Error(w, "Failed to serialize tile", http.StatusInternalServerError)
		return
	}
	
	// Store in cache
	if err := s.redis.Set(ctx, cacheKey, response, s.cacheTTL).Err(); err != nil {
		s.logger.WithError(err).Warn("Failed to cache tile")
	}
	
	// Send response
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Cache", "MISS")
	w.Write(response)
	
	s.logger.WithFields(logrus.Fields{
		"z": z, "x": x, "y": y, "scale": scale, "cache": "miss", "objects": tile.Count,
	}).Debug("Tile loaded from database")
}

func (s *Server) loadTile(ctx context.Context, z, x, y int, scale float64) (*TileResponse, error) {
	// Calculate tile bounds
	tileSize := 360.0 / float64(1<<uint(z))
	minX := float64(x)*tileSize - 180
	maxX := float64(x+1)*tileSize - 180
	minY := float64(y)*tileSize - 90
	maxY := float64(y+1)*tileSize - 90
	
	// Query database for objects in tile
	query := `
		SELECT * FROM fractal.get_tile_data($1, $2, $3, $4)
	`
	
	var tileDataJSON string
	err := s.db.QueryRowContext(ctx, query, z, x, y, scale).Scan(&tileDataJSON)
	if err != nil {
		return nil, fmt.Errorf("failed to query tile data: %w", err)
	}
	
	// Parse the JSON response from the database
	var dbResponse map[string]interface{}
	if err := json.Unmarshal([]byte(tileDataJSON), &dbResponse); err != nil {
		return nil, fmt.Errorf("failed to parse database response: %w", err)
	}
	
	// Build response
	response := &TileResponse{
		Tile: TileCoordinate{Z: z, X: x, Y: y},
		Bounds: BoundingBox{
			MinX: minX,
			MinY: minY,
			MaxX: maxX,
			MaxY: maxY,
		},
		Objects: []FractalObject{},
		Count:   0,
		Cached:  false,
	}
	
	// Parse objects from database response
	if objects, ok := dbResponse["objects"].([]interface{}); ok {
		for _, obj := range objects {
			if objMap, ok := obj.(map[string]interface{}); ok {
				fractalObj := FractalObject{
					ID:   getString(objMap, "id"),
					Type: getString(objMap, "type"),
					Name: getString(objMap, "name"),
					X:    getFloat(objMap, "x"),
					Y:    getFloat(objMap, "y"),
					Z:    getFloat(objMap, "z"),
					Importance: getInt(objMap, "importance"),
				}
				
				if props, ok := objMap["properties"].(map[string]interface{}); ok {
					fractalObj.Properties = props
				}
				
				response.Objects = append(response.Objects, fractalObj)
			}
		}
	}
	
	response.Count = len(response.Objects)
	
	return response, nil
}

func (s *Server) preloadHandler(w http.ResponseWriter, r *http.Request) {
	var req struct {
		CenterZ int     `json:"z"`
		CenterX int     `json:"x"`
		CenterY int     `json:"y"`
		Radius  int     `json:"radius"`
		Scale   float64 `json:"scale"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}
	
	// Query for adjacent tiles
	query := `
		SELECT * FROM fractal.preload_adjacent_tiles($1, $2, $3, $4)
	`
	
	rows, err := s.db.Query(query, req.CenterZ, req.CenterX, req.CenterY, req.Radius)
	if err != nil {
		s.logger.WithError(err).Error("Failed to query adjacent tiles")
		http.Error(w, "Failed to query adjacent tiles", http.StatusInternalServerError)
		return
	}
	defer rows.Close()
	
	var tiles []map[string]interface{}
	for rows.Next() {
		var z, x, y, priority int
		if err := rows.Scan(&z, &x, &y, &priority); err != nil {
			continue
		}
		
		tiles = append(tiles, map[string]interface{}{
			"z":        z,
			"x":        x,
			"y":        y,
			"priority": priority,
		})
		
		// Trigger async preload for high priority tiles
		if priority == 1 {
			go func(z, x, y int, scale float64) {
				ctx := context.Background()
				cacheKey := fmt.Sprintf("tile:%d:%d:%d:%.8f", z, x, y, scale)
				
				// Check if already cached
				if exists := s.redis.Exists(ctx, cacheKey).Val(); exists > 0 {
					return
				}
				
				// Load and cache the tile
				tile, err := s.loadTile(ctx, z, x, y, scale)
				if err == nil {
					if data, err := json.Marshal(tile); err == nil {
						s.redis.Set(ctx, cacheKey, data, s.cacheTTL)
					}
				}
			}(z, x, y, req.Scale)
		}
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"tiles":    tiles,
		"preloaded": len(tiles),
	})
}

func (s *Server) statsHandler(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	
	// Get cache statistics
	cacheInfo := s.redis.Info(ctx, "stats").Val()
	
	// Get database statistics
	var dbStats struct {
		TotalObjects       int `json:"total_objects"`
		TotalContributions int `json:"total_contributions"`
		CachedTiles        int `json:"cached_tiles"`
	}
	
	err := s.db.QueryRow(`
		SELECT 
			(SELECT COUNT(*) FROM fractal.fractal_arxobjects) as total_objects,
			(SELECT COUNT(*) FROM fractal.scale_contributions) as total_contributions,
			(SELECT COUNT(*) FROM fractal.tile_cache WHERE expires_at > NOW()) as cached_tiles
	`).Scan(&dbStats.TotalObjects, &dbStats.TotalContributions, &dbStats.CachedTiles)
	
	if err != nil {
		s.logger.WithError(err).Error("Failed to get database stats")
	}
	
	// Get scale statistics
	scaleStats := []map[string]interface{}{}
	rows, err := s.db.Query(`SELECT * FROM fractal.get_scale_statistics(NULL)`)
	if err == nil {
		defer rows.Close()
		for rows.Next() {
			var scaleRange string
			var objectCount int64
			var avgImportance float64
			var totalContributions int64
			var totalBiltEarned float64
			
			if err := rows.Scan(&scaleRange, &objectCount, &avgImportance, &totalContributions, &totalBiltEarned); err == nil {
				scaleStats = append(scaleStats, map[string]interface{}{
					"scale_range":         scaleRange,
					"object_count":        objectCount,
					"avg_importance":      avgImportance,
					"total_contributions": totalContributions,
					"total_bilt_earned":   totalBiltEarned,
				})
			}
		}
	}
	
	response := map[string]interface{}{
		"database": dbStats,
		"cache":    cacheInfo,
		"scales":   scaleStats,
		"server": map[string]interface{}{
			"uptime":   time.Since(startTime).Seconds(),
			"version":  "1.0.0",
			"cache_ttl": s.cacheTTL.Seconds(),
		},
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func (s *Server) healthHandler(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	
	// Check database
	dbHealthy := s.db.PingContext(ctx) == nil
	
	// Check Redis
	redisHealthy := s.redis.Ping(ctx).Err() == nil
	
	// Check MinIO
	minioHealthy := true
	_, err := s.minio.ListBuckets(ctx)
	if err != nil {
		minioHealthy = false
	}
	
	healthy := dbHealthy && redisHealthy && minioHealthy
	
	response := map[string]interface{}{
		"healthy":  healthy,
		"database": dbHealthy,
		"redis":    redisHealthy,
		"minio":    minioHealthy,
	}
	
	if !healthy {
		w.WriteHeader(http.StatusServiceUnavailable)
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// Helper functions
func getString(m map[string]interface{}, key string) string {
	if v, ok := m[key].(string); ok {
		return v
	}
	return ""
}

func getFloat(m map[string]interface{}, key string) float64 {
	if v, ok := m[key].(float64); ok {
		return v
	}
	return 0
}

func getInt(m map[string]interface{}, key string) int {
	if v, ok := m[key].(float64); ok {
		return int(v)
	}
	return 0
}

var startTime = time.Now()

func main() {
	// Create server
	server, err := NewServer()
	if err != nil {
		log.Fatalf("Failed to create server: %v", err)
	}
	defer server.db.Close()
	
	// Set up routes
	router := mux.NewRouter()
	
	// Tile endpoints
	router.HandleFunc("/tiles/{z}/{x}/{y}", server.getTileHandler).Methods("GET")
	router.HandleFunc("/preload", server.preloadHandler).Methods("POST")
	
	// Management endpoints
	router.HandleFunc("/stats", server.statsHandler).Methods("GET")
	router.HandleFunc("/health", server.healthHandler).Methods("GET")
	
	// Set up CORS
	c := cors.New(cors.Options{
		AllowedOrigins:   []string{"*"},
		AllowedMethods:   []string{"GET", "POST", "OPTIONS"},
		AllowedHeaders:   []string{"*"},
		AllowCredentials: true,
	})
	
	handler := c.Handler(router)
	
	// Start server
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	
	server.logger.WithField("port", port).Info("Starting tile server")
	
	if err := http.ListenAndServe(":"+port, handler); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}