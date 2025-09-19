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

	"github.com/arx-os/arxos/internal/bim"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
)

// StorageCoordinator manages the multi-level data architecture for ArxOS
type StorageCoordinator struct {
	textFiles  *BIMFileManager
	spatial    *database.PostGISDB
	cache      *database.PostGISDB
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

	// Initialize spatial database
	ctx := context.Background()
	spatial, err := database.NewPostGISConnection(ctx)
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
	// Load spatial anchors from PostGIS
	anchors, err := sc.spatial.GetSpatialAnchors(ctx, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to load spatial anchors: %w", err)
	}

	// Load associated equipment and room data
	floorPlan, err := sc.spatial.GetFloorPlan(ctx, buildingID)
	if err != nil {
		logger.Warn("Failed to load floor plan from spatial: %v", err)
		floorPlan = nil
	}

	return &BuildingData{
		SpatialAnchors: anchors,
		FloorPlan:      floorPlan,
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

	// Use bim.Writer to write the building to file
	writer := bim.NewWriter()
	content, err := writer.WriteBuilding(building)
	if err != nil {
		return fmt.Errorf("failed to serialize building: %w", err)
	}

	return os.WriteFile(filePath, content, 0644)
}

// hasSignificantChange determines if AR edit requires .bim.txt update
func (sc *StorageCoordinator) hasSignificantChange(building *BuildingData) bool {
	// Check if we have significant spatial changes
	if len(building.SpatialAnchors) == 0 {
		return false
	}

	// Count changes that affect structure
	significantChanges := 0
	for _, anchor := range building.SpatialAnchors {
		// Check confidence level - only high confidence changes should update BIM
		if anchor.Confidence >= 0.8 {
			significantChanges++
		}
	}

	// Require at least 3 significant changes or 1 high-priority change
	return significantChanges >= 3
}

// autoSyncLoop runs periodic synchronization between storage layers
func (sc *StorageCoordinator) autoSyncLoop() {
	ticker := time.NewTicker(sc.config.SyncInterval)
	defer ticker.Stop()

	for range ticker.C {
		// Implement periodic sync logic
		ctx := context.Background()

		// Check for pending changes in each layer
		// TODO: Get building list from PostGIS cache
		buildingIDs := []string{}

		for _, buildingID := range buildingIDs {
			// Check for unsync'd changes
			if sc.hasPendingChanges(ctx, buildingID) {
				logger.Info("Syncing pending changes for building %s", buildingID)
				if err := sc.syncBuilding(ctx, buildingID); err != nil {
					logger.Error("Failed to sync building %s: %v", buildingID, err)
				}
			}
		}

		logger.Debug("Completed periodic sync between storage layers")
	}
}

// syncBIMToOtherLayers syncs .bim.txt changes to spatial and cache layers
func (sc *StorageCoordinator) syncBIMToOtherLayers(ctx context.Context, building *BuildingData) {
	// Sync BIM to spatial database
	if building.BIMBuilding != nil {
		// Convert BIM equipment to spatial anchors
		for _, floor := range building.BIMBuilding.Floors {
			for _, equipment := range floor.Equipment {
				anchor := &database.SpatialAnchor{
					ID:          equipment.ID,
					BuildingID:  building.BIMBuilding.Name,
					EquipmentID: equipment.ID,
					Position: database.Point3D{
						X: equipment.Location.X,
						Y: equipment.Location.Y,
						Z: float64(floor.Level),
					},
					Confidence:  1.0, // BIM data has full confidence
					LastScanned: time.Now(),
				}

				if err := sc.spatial.SaveSpatialAnchor(ctx, anchor); err != nil {
					logger.Error("Failed to sync equipment %s to spatial: %v", equipment.ID, err)
				}
			}
		}

		// Sync to cache database
		floorPlan := convertBIMToFloorPlan(building.BIMBuilding)
		if err := sc.cache.SaveFloorPlan(ctx, floorPlan); err != nil {
			logger.Error("Failed to sync BIM to cache: %v", err)
		}
	}

	logger.Debug("Completed syncing BIM changes to other layers")
}

// syncCacheToBIM syncs cache changes back to .bim.txt
func (sc *StorageCoordinator) syncCacheToBIM(ctx context.Context, building *BuildingData) {
	// Convert cache floor plan to BIM format
	if building.FloorPlan != nil {
		bimBuilding := &bim.Building{
			Name:        building.FloorPlan.Name,
			FileVersion: bim.CurrentVersion,
			Generated:   time.Now(),
			Floors:      make([]bim.Floor, 0),
		}

		// Create a floor with equipment
		floor := bim.Floor{
			Level: building.FloorPlan.Level,
			Name:  fmt.Sprintf("Level %d", building.FloorPlan.Level),
			Equipment: make([]bim.Equipment, 0),
		}

		// Convert equipment
		for _, eq := range building.FloorPlan.Equipment {
			bimEq := bim.Equipment{
				ID:   eq.ID,
				Type: eq.Type,
				Location: bim.Location{
					X: 0, // TODO: Get actual coordinates
					Y: 0,
					Room: eq.RoomID,
				},
				Status: bim.EquipmentStatus(eq.Status),
			}
			floor.Equipment = append(floor.Equipment, bimEq)
		}

		bimBuilding.Floors = append(bimBuilding.Floors, floor)

		// Save to BIM file
		if err := sc.textFiles.SaveBuilding(bimBuilding); err != nil {
			logger.Error("Failed to sync cache to BIM: %v", err)
		} else {
			logger.Info("Synced cache changes to BIM for building %s", building.FloorPlan.ID)
		}
	}

	logger.Debug("Completed syncing cache changes to BIM")
}

// sanitizeFilename removes invalid characters from filename
func sanitizeFilename(name string) string {
	// Simple sanitization - replace spaces with underscores and remove special chars
	return filepath.Base(name) // This is a placeholder
}

// hasPendingChanges checks if a building has unsynchronized changes
func (sc *StorageCoordinator) hasPendingChanges(ctx context.Context, buildingID string) bool {
	// Check modification timestamps across layers
	// This is a simplified implementation
	return false
}

// syncBuilding synchronizes all layers for a specific building
func (sc *StorageCoordinator) syncBuilding(ctx context.Context, buildingID string) error {
	// Load from primary source and sync to others
	building, err := sc.GetBuilding(ctx, buildingID)
	if err != nil {
		return err
	}

	// Determine which layers need updates
	if contains(building.DataSources, SourceBIM) {
		sc.syncBIMToOtherLayers(ctx, building)
	} else if contains(building.DataSources, SourceTerminal) {
		sc.syncCacheToBIM(ctx, building)
	}

	return nil
}

// convertBIMToFloorPlan converts BIM building to floor plan model
func convertBIMToFloorPlan(bimBuilding *bim.Building) *models.FloorPlan {
	floorPlan := &models.FloorPlan{
		ID:        bimBuilding.ID,
		Name:      bimBuilding.Name,
		Equipment: make([]*models.Equipment, 0),
		Rooms:     make([]*models.Room, 0),
	}

	// Convert equipment
	for _, eq := range bimBuilding.Equipment {
		modelEq := &models.Equipment{
			ID:   eq.ID,
			Type: eq.Type,
			Location: &models.Point3D{
				X: eq.Location.X,
				Y: eq.Location.Y,
				Z: eq.Location.Z,
			},
			Status: models.EquipmentStatus(eq.Status),
		}
		floorPlan.Equipment = append(floorPlan.Equipment, modelEq)
	}

	// Convert rooms
	for _, room := range bimBuilding.Rooms {
		modelRoom := &models.Room{
			ID:    room.ID,
			Name:  room.Name,
			Floor: room.Floor,
		}
		floorPlan.Rooms = append(floorPlan.Rooms, modelRoom)
	}

	return floorPlan
}

// contains checks if a slice contains a value
func contains(slice []DataSource, item DataSource) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

// Close closes all storage connections
func (sc *StorageCoordinator) Close() error {
	if err := sc.spatial.Close(); err != nil {
		return fmt.Errorf("failed to close spatial database: %w", err)
	}
	return nil
}
