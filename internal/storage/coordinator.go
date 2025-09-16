// Package storage provides a simplified storage coordinator for ArxOS multi-level data architecture.
// This replaces the complex multi-backend storage system with a clean coordinator that bridges:
// - .bim.txt files (schematic representation, source of truth)
// - PostGIS database (millimeter-precision spatial data for AR)
// - SQLite cache (query performance for terminal operations)
package storage

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/joelpate/arxos/internal/bim"
	"github.com/joelpate/arxos/internal/common/logger"
	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/pkg/models"
)

// StorageCoordinator manages the multi-level data architecture for ArxOS
type StorageCoordinator struct {
	textFiles  *BIMFileManager
	spatial    *database.SQLiteDB // Will be PostGIS in future
	cache      *database.SQLiteDB
	translator *CoordinateTranslator
	config     *CoordinatorConfig
	mu         sync.RWMutex
}

// CoordinatorConfig contains configuration for the storage coordinator
type CoordinatorConfig struct {
	BIMFilesPath   string        // Path to .bim.txt files
	DatabasePath   string        // Path to SQLite/PostGIS database
	AutoSync       bool          // Automatically sync between layers
	SyncInterval   time.Duration // How often to sync
	ValidateOnSave bool          // Validate .bim.txt files on save
}

// BIMFileManager handles .bim.txt file operations
type BIMFileManager struct {
	rootPath string
	parser   *bim.Parser
	mu       sync.RWMutex
}

// CoordinateTranslator bridges between grid and world coordinates
type CoordinateTranslator struct {
	// Building coordinate system configuration
	BuildingOrigin Point3D // Real-world building origin
	GridScale      float64 // Meters per grid unit
	GridOrigin     Point2D // Grid coordinate (0,0) position
	FloorHeight    float64 // Meters between floors
	Orientation    float64 // Building rotation (degrees from north)
}

// Point3D represents a 3D coordinate
type Point3D struct {
	X, Y, Z float64
}

// Point2D represents a 2D coordinate
type Point2D struct {
	X, Y float64
}

// NewStorageCoordinator creates a new storage coordinator
func NewStorageCoordinator(config *CoordinatorConfig) (*StorageCoordinator, error) {
	if config == nil {
		return nil, fmt.Errorf("coordinator config is required")
	}

	// Initialize BIM file manager
	textFiles, err := NewBIMFileManager(config.BIMFilesPath)
	if err != nil {
		return nil, fmt.Errorf("failed to create BIM file manager: %w", err)
	}

	// Initialize spatial database (SQLite for now, PostGIS later)
	spatial, err := database.NewSQLiteDBFromPath(config.DatabasePath)
	if err != nil {
		return nil, fmt.Errorf("failed to create spatial database: %w", err)
	}

	// Initialize coordinate translator with defaults
	translator := &CoordinateTranslator{
		BuildingOrigin: Point3D{X: 0, Y: 0, Z: 0},
		GridScale:      0.5, // 0.5 meters per grid unit
		GridOrigin:     Point2D{X: 0, Y: 0},
		FloorHeight:    3.0, // 3 meters per floor
		Orientation:    0.0, // North up
	}

	coordinator := &StorageCoordinator{
		textFiles:  textFiles,
		spatial:    spatial,
		cache:      spatial, // Same database for now
		translator: translator,
		config:     config,
	}

	// Start auto-sync if enabled
	if config.AutoSync {
		go coordinator.autoSyncLoop()
	}

	return coordinator, nil
}

// NewBIMFileManager creates a new BIM file manager
func NewBIMFileManager(rootPath string) (*BIMFileManager, error) {
	if err := os.MkdirAll(rootPath, 0755); err != nil {
		return nil, fmt.Errorf("failed to create BIM files directory: %w", err)
	}

	return &BIMFileManager{
		rootPath: rootPath,
		parser:   bim.NewParser(),
	}, nil
}

// GetBuilding retrieves a building from the appropriate data source based on query type
func (sc *StorageCoordinator) GetBuilding(ctx context.Context, buildingID string, queryType QueryType) (*BuildingData, error) {
	sc.mu.RLock()
	defer sc.mu.RUnlock()

	switch queryType {
	case QueryOverview:
		// Load from .bim.txt for schematic overview
		return sc.getBuildingFromBIM(ctx, buildingID)
	case QuerySpatial:
		// Load from PostGIS for precise coordinates
		return sc.getBuildingFromSpatial(ctx, buildingID)
	case QueryDetail:
		// Load from cache/database for system tracing
		return sc.getBuildingFromCache(ctx, buildingID)
	default:
		return nil, fmt.Errorf("unknown query type: %v", queryType)
	}
}

// SaveBuilding saves building data to the appropriate storage layers
func (sc *StorageCoordinator) SaveBuilding(ctx context.Context, building *BuildingData, source DataSource) error {
	sc.mu.Lock()
	defer sc.mu.Unlock()

	switch source {
	case SourceBIM:
		// Save to .bim.txt and sync to other layers
		return sc.saveBuildingFromBIM(ctx, building)
	case SourceAR:
		// Save to PostGIS and conditionally update .bim.txt
		return sc.saveBuildingFromAR(ctx, building)
	case SourceTerminal:
		// Save to cache and sync to .bim.txt
		return sc.saveBuildingFromTerminal(ctx, building)
	default:
		return fmt.Errorf("unknown data source: %v", source)
	}
}

// QueryType represents different types of building queries
type QueryType int

const (
	QueryOverview QueryType = iota // Building manager - schematic view
	QueryDetail                    // Systems engineer - detailed tracing
	QuerySpatial                   // Field technician - precise coordinates
)

// DataSource represents where the data is coming from
type DataSource int

const (
	SourceBIM      DataSource = iota // .bim.txt file edit
	SourceAR                         // AR mobile app edit
	SourceTerminal                   // Terminal command edit
)

// BuildingData represents building data with multi-level information
type BuildingData struct {
	// Schematic data (from .bim.txt)
	BIMBuilding *bim.Building

	// Spatial data (from PostGIS)
	SpatialAnchors []*database.SpatialAnchor

	// Cache data (from SQLite)
	FloorPlan *models.FloorPlan

	// Metadata
	LastModified time.Time
	DataSources  []DataSource // Which sources have been loaded
}

// getBuildingFromBIM loads building data from .bim.txt file
func (sc *StorageCoordinator) getBuildingFromBIM(ctx context.Context, buildingID string) (*BuildingData, error) {
	building, err := sc.textFiles.LoadBuilding(buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to load BIM file: %w", err)
	}

	return &BuildingData{
		BIMBuilding:  building,
		DataSources:  []DataSource{SourceBIM},
		LastModified: time.Now(),
	}, nil
}

// getBuildingFromSpatial loads building data from PostGIS
func (sc *StorageCoordinator) getBuildingFromSpatial(ctx context.Context, buildingID string) (*BuildingData, error) {
	// TODO: Load spatial anchors from PostGIS
	// For now, return empty spatial data
	return &BuildingData{
		SpatialAnchors: make([]*database.SpatialAnchor, 0),
		DataSources:    []DataSource{SourceAR},
		LastModified:   time.Now(),
	}, nil
}

// getBuildingFromCache loads building data from SQLite cache
func (sc *StorageCoordinator) getBuildingFromCache(ctx context.Context, buildingID string) (*BuildingData, error) {
	floorPlan, err := sc.cache.GetFloorPlan(ctx, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to load from cache: %w", err)
	}

	return &BuildingData{
		FloorPlan:    floorPlan,
		DataSources:  []DataSource{SourceTerminal},
		LastModified: time.Now(),
	}, nil
}

// saveBuildingFromBIM saves building data originating from .bim.txt edit
func (sc *StorageCoordinator) saveBuildingFromBIM(ctx context.Context, building *BuildingData) error {
	if building.BIMBuilding == nil {
		return fmt.Errorf("no BIM data to save")
	}

	// Save to .bim.txt file
	if err := sc.textFiles.SaveBuilding(building.BIMBuilding); err != nil {
		return fmt.Errorf("failed to save BIM file: %w", err)
	}

	// Sync to other layers if auto-sync is enabled
	if sc.config.AutoSync {
		go sc.syncBIMToOtherLayers(ctx, building)
	}

	logger.Info("Saved building %s from BIM source", building.BIMBuilding.Name)
	return nil
}

// saveBuildingFromAR saves building data originating from AR edit
func (sc *StorageCoordinator) saveBuildingFromAR(ctx context.Context, building *BuildingData) error {
	// Save to PostGIS (spatial database)
	for _, anchor := range building.SpatialAnchors {
		if err := sc.spatial.SaveSpatialAnchor(ctx, anchor); err != nil {
			return fmt.Errorf("failed to save spatial anchor: %w", err)
		}
	}

	// Check if we need to update .bim.txt (significant change detection)
	if sc.hasSignificantChange(building) {
		// Convert spatial coordinates back to grid coordinates
		// Update .bim.txt file
		// This is where the coordinate translation happens
		logger.Info("Significant change detected - updating .bim.txt from AR edit")
	}

	return nil
}

// saveBuildingFromTerminal saves building data originating from terminal edit
func (sc *StorageCoordinator) saveBuildingFromTerminal(ctx context.Context, building *BuildingData) error {
	if building.FloorPlan == nil {
		return fmt.Errorf("no floor plan data to save")
	}

	// Save to cache
	if err := sc.cache.SaveFloorPlan(ctx, building.FloorPlan); err != nil {
		return fmt.Errorf("failed to save to cache: %w", err)
	}

	// Sync to .bim.txt if auto-sync is enabled
	if sc.config.AutoSync {
		go sc.syncCacheToBIM(ctx, building)
	}

	return nil
}

// LoadBuilding loads a building from .bim.txt file
func (bfm *BIMFileManager) LoadBuilding(buildingID string) (*bim.Building, error) {
	bfm.mu.RLock()
	defer bfm.mu.RUnlock()

	filePath := filepath.Join(bfm.rootPath, buildingID+".bim.txt")
	return bfm.parser.ParseFile(filePath)
}

// SaveBuilding saves a building to .bim.txt file
func (bfm *BIMFileManager) SaveBuilding(building *bim.Building) error {
	bfm.mu.Lock()
	defer bfm.mu.Unlock()

	// Generate filename from building name/ID
	filename := fmt.Sprintf("%s.bim.txt", sanitizeFilename(building.Name))
	filePath := filepath.Join(bfm.rootPath, filename)

	// TODO: Use bim.Writer to write the building to file
	// For now, just create a placeholder
	content := fmt.Sprintf("BUILDING: %s\nVERSION: %s\nCREATED: %s\n",
		building.Name, building.FileVersion, time.Now().Format(time.RFC3339))

	return os.WriteFile(filePath, []byte(content), 0644)
}

// hasSignificantChange determines if AR edit requires .bim.txt update
func (sc *StorageCoordinator) hasSignificantChange(building *BuildingData) bool {
	// TODO: Implement coordinate translation and change detection
	// For now, assume no significant change
	return false
}

// autoSyncLoop runs periodic synchronization between storage layers
func (sc *StorageCoordinator) autoSyncLoop() {
	ticker := time.NewTicker(sc.config.SyncInterval)
	defer ticker.Stop()

	for range ticker.C {
		// TODO: Implement periodic sync logic
		logger.Debug("Running periodic sync between storage layers")
	}
}

// syncBIMToOtherLayers syncs .bim.txt changes to spatial and cache layers
func (sc *StorageCoordinator) syncBIMToOtherLayers(ctx context.Context, building *BuildingData) {
	// TODO: Implement BIM to spatial/cache sync
	logger.Debug("Syncing BIM changes to other layers")
}

// syncCacheToBIM syncs cache changes back to .bim.txt
func (sc *StorageCoordinator) syncCacheToBIM(ctx context.Context, building *BuildingData) {
	// TODO: Implement cache to BIM sync
	logger.Debug("Syncing cache changes to BIM")
}

// sanitizeFilename removes invalid characters from filename
func sanitizeFilename(name string) string {
	// Simple sanitization - replace spaces with underscores and remove special chars
	return filepath.Base(name) // This is a placeholder
}

// Close closes all storage connections
func (sc *StorageCoordinator) Close() error {
	if err := sc.spatial.Close(); err != nil {
		return fmt.Errorf("failed to close spatial database: %w", err)
	}
	return nil
}
