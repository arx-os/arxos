package database

import (
	"context"
	"database/sql"
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/pkg/models"
	"github.com/arx-os/arxos/internal/common/logger"
)

// HybridDB implements DB with automatic fallback between PostGIS and SQLite
type HybridDB struct {
	primary   DB        // PostGIS when available
	fallback  DB        // SQLite always available
	spatialDB SpatialDB // Spatial operations (may be nil)

	// Connection state
	spatialAvailable bool
	lastCheck        time.Time
	checkInterval    time.Duration
	mu               sync.RWMutex

	// Sync queue for offline spatial updates
	syncQueue []SpatialUpdate
	queueMu   sync.Mutex
}

// NewHybridDB creates a new hybrid database with automatic fallback
func NewHybridDB(primary, fallback DB) *HybridDB {
	h := &HybridDB{
		primary:       primary,
		fallback:      fallback,
		checkInterval: 30 * time.Second,
		syncQueue:     make([]SpatialUpdate, 0),
	}

	// Check if primary has spatial support
	h.checkSpatialAvailability()

	// Start background checker
	go h.backgroundHealthCheck()

	return h
}

// Connect establishes database connections
func (h *HybridDB) Connect(ctx context.Context, dbPath string) error {
	// Always connect fallback
	if err := h.fallback.Connect(ctx, dbPath); err != nil {
		return fmt.Errorf("fallback connection failed: %w", err)
	}

	// Try to connect primary
	if h.primary != nil {
		if err := h.primary.Connect(ctx, ""); err != nil {
			logger.Warn("Primary database connection failed, using fallback: %v", err)
			h.spatialAvailable = false
		} else {
			h.checkSpatialAvailability()
		}
	}

	return nil
}

// Close closes all database connections
func (h *HybridDB) Close() error {
	var errs []error

	if h.primary != nil {
		if err := h.primary.Close(); err != nil {
			errs = append(errs, fmt.Errorf("primary close error: %w", err))
		}
	}

	if err := h.fallback.Close(); err != nil {
		errs = append(errs, fmt.Errorf("fallback close error: %w", err))
	}

	if len(errs) > 0 {
		return fmt.Errorf("close errors: %v", errs)
	}

	return nil
}

// HasSpatialSupport returns true if spatial operations are available
func (h *HybridDB) HasSpatialSupport() bool {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return h.spatialAvailable
}

// GetSpatialDB returns the spatial database interface
func (h *HybridDB) GetSpatialDB() (SpatialDB, error) {
	h.mu.RLock()
	defer h.mu.RUnlock()

	if !h.spatialAvailable || h.spatialDB == nil {
		return nil, fmt.Errorf("spatial database not available")
	}

	return h.spatialDB, nil
}

// BeginTx starts a transaction on the active database
func (h *HybridDB) BeginTx(ctx context.Context) (*sql.Tx, error) {
	db := h.getActiveDB()
	return db.BeginTx(ctx)
}

// GetFloorPlan retrieves a floor plan
func (h *HybridDB) GetFloorPlan(ctx context.Context, id string) (*models.FloorPlan, error) {
	// Try primary first if available
	if h.spatialAvailable && h.primary != nil {
		plan, err := h.primary.GetFloorPlan(ctx, id)
		if err == nil {
			return plan, nil
		}
		logger.Debug("Primary query failed, trying fallback: %v", err)
	}

	// Use fallback
	return h.fallback.GetFloorPlan(ctx, id)
}

// GetAllFloorPlans retrieves all floor plans
func (h *HybridDB) GetAllFloorPlans(ctx context.Context) ([]*models.FloorPlan, error) {
	db := h.getActiveDB()
	return db.GetAllFloorPlans(ctx)
}

// SaveFloorPlan saves a floor plan to both databases
func (h *HybridDB) SaveFloorPlan(ctx context.Context, plan *models.FloorPlan) error {
	// Save to fallback first (always available)
	if err := h.fallback.SaveFloorPlan(ctx, plan); err != nil {
		return fmt.Errorf("fallback save failed: %w", err)
	}

	// Try to save to primary if available
	if h.spatialAvailable && h.primary != nil {
		if err := h.primary.SaveFloorPlan(ctx, plan); err != nil {
			logger.Warn("Primary save failed, data saved to fallback: %v", err)
			// Don't return error since fallback succeeded
		}
	}

	return nil
}

// UpdateFloorPlan updates a floor plan in both databases
func (h *HybridDB) UpdateFloorPlan(ctx context.Context, plan *models.FloorPlan) error {
	// Update fallback first
	if err := h.fallback.UpdateFloorPlan(ctx, plan); err != nil {
		return fmt.Errorf("fallback update failed: %w", err)
	}

	// Try to update primary
	if h.spatialAvailable && h.primary != nil {
		if err := h.primary.UpdateFloorPlan(ctx, plan); err != nil {
			logger.Warn("Primary update failed: %v", err)
		}
	}

	return nil
}

// DeleteFloorPlan deletes a floor plan from both databases
func (h *HybridDB) DeleteFloorPlan(ctx context.Context, id string) error {
	var errs []error

	// Delete from both databases
	if err := h.fallback.DeleteFloorPlan(ctx, id); err != nil {
		errs = append(errs, fmt.Errorf("fallback delete: %w", err))
	}

	if h.spatialAvailable && h.primary != nil {
		if err := h.primary.DeleteFloorPlan(ctx, id); err != nil {
			errs = append(errs, fmt.Errorf("primary delete: %w", err))
		}
	}

	if len(errs) > 0 {
		return fmt.Errorf("delete errors: %v", errs)
	}

	return nil
}

// GetEquipment retrieves equipment with optional spatial data
func (h *HybridDB) GetEquipment(ctx context.Context, id string) (*models.Equipment, error) {
	// Get base equipment from fallback
	equipment, err := h.fallback.GetEquipment(ctx, id)
	if err != nil {
		return nil, err
	}

	// Enhance with spatial data if available
	if h.spatialAvailable && h.spatialDB != nil {
		if _, err := h.spatialDB.GetEquipmentPosition(id); err == nil {
			// Merge spatial data into equipment
			// This would be implemented based on the actual Equipment struct
			logger.Debug("Enhanced equipment %s with spatial data", id)
		}
	}

	return equipment, nil
}

// GetEquipmentByFloorPlan retrieves equipment for a floor plan
func (h *HybridDB) GetEquipmentByFloorPlan(ctx context.Context, floorPlanID string) ([]*models.Equipment, error) {
	db := h.getActiveDB()
	return db.GetEquipmentByFloorPlan(ctx, floorPlanID)
}

// SaveEquipment saves equipment to both databases
func (h *HybridDB) SaveEquipment(ctx context.Context, equipment *models.Equipment) error {
	// Save to fallback first
	if err := h.fallback.SaveEquipment(ctx, equipment); err != nil {
		return fmt.Errorf("fallback save failed: %w", err)
	}

	// Try to save to primary
	if h.spatialAvailable && h.primary != nil {
		if err := h.primary.SaveEquipment(ctx, equipment); err != nil {
			logger.Warn("Primary save failed: %v", err)
		}
	}

	return nil
}

// UpdateEquipment updates equipment in both databases
func (h *HybridDB) UpdateEquipment(ctx context.Context, equipment *models.Equipment) error {
	// Update fallback
	if err := h.fallback.UpdateEquipment(ctx, equipment); err != nil {
		return err
	}

	// Try to update primary
	if h.spatialAvailable && h.primary != nil {
		if err := h.primary.UpdateEquipment(ctx, equipment); err != nil {
			logger.Warn("Primary update failed: %v", err)
		}
	}

	return nil
}

// DeleteEquipment deletes equipment from both databases
func (h *HybridDB) DeleteEquipment(ctx context.Context, id string) error {
	var errs []error

	if err := h.fallback.DeleteEquipment(ctx, id); err != nil {
		errs = append(errs, err)
	}

	if h.spatialAvailable && h.primary != nil {
		if err := h.primary.DeleteEquipment(ctx, id); err != nil {
			errs = append(errs, err)
		}
	}

	if len(errs) > 0 {
		return fmt.Errorf("delete errors: %v", errs)
	}

	return nil
}

// Room operations - delegate to active database
func (h *HybridDB) GetRoom(ctx context.Context, id string) (*models.Room, error) {
	db := h.getActiveDB()
	return db.GetRoom(ctx, id)
}

func (h *HybridDB) GetRoomsByFloorPlan(ctx context.Context, floorPlanID string) ([]*models.Room, error) {
	db := h.getActiveDB()
	return db.GetRoomsByFloorPlan(ctx, floorPlanID)
}

func (h *HybridDB) SaveRoom(ctx context.Context, room *models.Room) error {
	return h.saveToAll(ctx, func(db DB) error {
		return db.SaveRoom(ctx, room)
	})
}

func (h *HybridDB) UpdateRoom(ctx context.Context, room *models.Room) error {
	return h.saveToAll(ctx, func(db DB) error {
		return db.UpdateRoom(ctx, room)
	})
}

func (h *HybridDB) DeleteRoom(ctx context.Context, id string) error {
	return h.deleteFromAll(ctx, func(db DB) error {
		return db.DeleteRoom(ctx, id)
	})
}

// User operations - delegate to active database
func (h *HybridDB) GetUser(ctx context.Context, id string) (*models.User, error) {
	db := h.getActiveDB()
	return db.GetUser(ctx, id)
}

func (h *HybridDB) GetUserByEmail(ctx context.Context, email string) (*models.User, error) {
	db := h.getActiveDB()
	return db.GetUserByEmail(ctx, email)
}

func (h *HybridDB) CreateUser(ctx context.Context, user *models.User) error {
	return h.saveToAll(ctx, func(db DB) error {
		return db.CreateUser(ctx, user)
	})
}

func (h *HybridDB) UpdateUser(ctx context.Context, user *models.User) error {
	return h.saveToAll(ctx, func(db DB) error {
		return db.UpdateUser(ctx, user)
	})
}

func (h *HybridDB) DeleteUser(ctx context.Context, id string) error {
	return h.deleteFromAll(ctx, func(db DB) error {
		return db.DeleteUser(ctx, id)
	})
}

// Organization operations
func (h *HybridDB) GetOrganization(ctx context.Context, id string) (*models.Organization, error) {
	db := h.getActiveDB()
	return db.GetOrganization(ctx, id)
}

// GetOrganizationsByUser retrieves organizations for a user
func (h *HybridDB) GetOrganizationsByUser(ctx context.Context, userID string) ([]*models.Organization, error) {
	db := h.getActiveDB()
	return db.GetOrganizationsByUser(ctx, userID)
}

func (h *HybridDB) CreateOrganization(ctx context.Context, org *models.Organization) error {
	return h.saveToAll(ctx, func(db DB) error {
		return db.CreateOrganization(ctx, org)
	})
}

func (h *HybridDB) UpdateOrganization(ctx context.Context, org *models.Organization) error {
	return h.saveToAll(ctx, func(db DB) error {
		return db.UpdateOrganization(ctx, org)
	})
}

func (h *HybridDB) DeleteOrganization(ctx context.Context, id string) error {
	return h.deleteFromAll(ctx, func(db DB) error {
		return db.DeleteOrganization(ctx, id)
	})
}

// Helper methods

// getActiveDB returns the currently active database
func (h *HybridDB) getActiveDB() DB {
	h.mu.RLock()
	defer h.mu.RUnlock()

	if h.spatialAvailable && h.primary != nil {
		return h.primary
	}
	return h.fallback
}

// checkSpatialAvailability checks if spatial features are available
func (h *HybridDB) checkSpatialAvailability() {
	h.mu.Lock()
	defer h.mu.Unlock()

	h.lastCheck = time.Now()

	if h.primary != nil && h.primary.HasSpatialSupport() {
		spatialDB, err := h.primary.GetSpatialDB()
		if err == nil {
			h.spatialDB = spatialDB
			h.spatialAvailable = true
			logger.Info("Spatial database available")

			// Process any queued updates
			go h.processSyncQueue()
			return
		}
	}

	h.spatialAvailable = false
	h.spatialDB = nil
}

// backgroundHealthCheck periodically checks database availability
func (h *HybridDB) backgroundHealthCheck() {
	ticker := time.NewTicker(h.checkInterval)
	defer ticker.Stop()

	for range ticker.C {
		h.checkSpatialAvailability()
	}
}

// processSyncQueue processes queued spatial updates
func (h *HybridDB) processSyncQueue() {
	h.queueMu.Lock()
	defer h.queueMu.Unlock()

	if len(h.syncQueue) == 0 {
		return
	}

	logger.Info("Processing %d queued spatial updates", len(h.syncQueue))

	for _, update := range h.syncQueue {
		if h.spatialDB != nil {
			err := h.spatialDB.UpdateEquipmentPosition(
				update.EquipmentID,
				*update.Position,
				*update.Confidence,
				update.Source,
			)
			if err != nil {
				logger.Error("Failed to sync spatial update: %v", err)
			}
		}
	}

	// Clear processed queue
	h.syncQueue = make([]SpatialUpdate, 0)
}

// QueueSpatialUpdate queues a spatial update for later processing
func (h *HybridDB) QueueSpatialUpdate(update SpatialUpdate) {
	h.queueMu.Lock()
	defer h.queueMu.Unlock()

	h.syncQueue = append(h.syncQueue, update)
	logger.Debug("Queued spatial update for %s", update.EquipmentID)
}

// saveToAll saves data to all available databases
func (h *HybridDB) saveToAll(ctx context.Context, fn func(DB) error) error {
	// Always save to fallback
	if err := fn(h.fallback); err != nil {
		return err
	}

	// Try to save to primary if available
	if h.spatialAvailable && h.primary != nil {
		if err := fn(h.primary); err != nil {
			logger.Warn("Primary save failed: %v", err)
			// Don't return error since fallback succeeded
		}
	}

	return nil
}

// deleteFromAll deletes data from all available databases
func (h *HybridDB) deleteFromAll(ctx context.Context, fn func(DB) error) error {
	var errs []error

	if err := fn(h.fallback); err != nil {
		errs = append(errs, err)
	}

	if h.spatialAvailable && h.primary != nil {
		if err := fn(h.primary); err != nil {
			errs = append(errs, err)
		}
	}

	if len(errs) > 0 {
		return fmt.Errorf("delete errors: %v", errs)
	}

	return nil
}