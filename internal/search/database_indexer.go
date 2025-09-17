package search

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/pkg/models"
)

// DatabaseIndexer manages search index synchronization with the database
type DatabaseIndexer struct {
	engine *SearchEngine
	db     database.DB
	mu     sync.RWMutex
	
	// Index refresh settings
	refreshInterval time.Duration
	stopChan       chan struct{}
	running        bool
}

// NewDatabaseIndexer creates a new database-backed search indexer
func NewDatabaseIndexer(db database.DB, refreshInterval time.Duration) *DatabaseIndexer {
	if refreshInterval == 0 {
		refreshInterval = 5 * time.Minute
	}
	
	return &DatabaseIndexer{
		engine:          NewSearchEngine(),
		db:              db,
		refreshInterval: refreshInterval,
		stopChan:       make(chan struct{}),
	}
}

// Start begins the indexing process
func (idx *DatabaseIndexer) Start(ctx context.Context) error {
	idx.mu.Lock()
	defer idx.mu.Unlock()
	
	if idx.running {
		return fmt.Errorf("indexer already running")
	}
	
	// Initial index build
	if err := idx.rebuildIndex(ctx); err != nil {
		return fmt.Errorf("failed to build initial index: %w", err)
	}
	
	// Start background refresh
	go idx.backgroundRefresh()
	
	idx.running = true
	logger.Info("Search indexer started with %v refresh interval", idx.refreshInterval)
	
	return nil
}

// Stop stops the indexing process
func (idx *DatabaseIndexer) Stop() {
	idx.mu.Lock()
	defer idx.mu.Unlock()
	
	if !idx.running {
		return
	}
	
	close(idx.stopChan)
	idx.running = false
	logger.Info("Search indexer stopped")
}

// backgroundRefresh periodically refreshes the search index
func (idx *DatabaseIndexer) backgroundRefresh() {
	ticker := time.NewTicker(idx.refreshInterval)
	defer ticker.Stop()
	
	for {
		select {
		case <-ticker.C:
			ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
			if err := idx.rebuildIndex(ctx); err != nil {
				logger.Error("Failed to refresh search index: %v", err)
			}
			cancel()
			
		case <-idx.stopChan:
			return
		}
	}
}

// rebuildIndex rebuilds the entire search index from the database
func (idx *DatabaseIndexer) rebuildIndex(ctx context.Context) error {
	logger.Debug("Rebuilding search index...")
	startTime := time.Now()
	
	// Clear existing index
	idx.engine.Clear()
	
	// Index all floor plans
	floorPlans, err := idx.db.GetAllFloorPlans(ctx)
	if err != nil {
		return fmt.Errorf("failed to get floor plans: %w", err)
	}
	
	for _, fp := range floorPlans {
		if err := idx.engine.Index(ctx, "building", fp.ID, fp); err != nil {
			logger.Error("Failed to index floor plan %s: %v", fp.ID, err)
		}
		
		// Index rooms
		for _, room := range fp.Rooms {
			if err := idx.engine.Index(ctx, "room", room.ID, room); err != nil {
				logger.Error("Failed to index room %s: %v", room.ID, err)
			}
		}

		// Index equipment
		for _, equip := range fp.Equipment {
			if err := idx.engine.Index(ctx, "equipment", equip.ID, equip); err != nil {
				logger.Error("Failed to index equipment %s: %v", equip.ID, err)
			}
		}
	}
	
	stats := idx.engine.Stats()
	logger.Info("Search index rebuilt in %v: %d buildings, %d rooms, %d equipment, %d tokens",
		time.Since(startTime), stats["buildings"], stats["rooms"], 
		stats["equipment"], stats["text_tokens"])
	
	return nil
}

// Search performs a search query
func (idx *DatabaseIndexer) Search(ctx context.Context, opts SearchOptions) ([]SearchResult, error) {
	return idx.engine.Search(ctx, opts)
}

// Suggest provides search suggestions
func (idx *DatabaseIndexer) Suggest(ctx context.Context, prefix string, limit int) []string {
	return idx.engine.Suggest(ctx, prefix, limit)
}

// IndexFloorPlan indexes a single floor plan (for real-time updates)
func (idx *DatabaseIndexer) IndexFloorPlan(ctx context.Context, fp *models.FloorPlan) error {
	if err := idx.engine.Index(ctx, "building", fp.ID, fp); err != nil {
		return err
	}
	
	// Index associated rooms
	for _, room := range fp.Rooms {
		if err := idx.engine.Index(ctx, "room", room.ID, room); err != nil {
			return err
		}
	}

	// Index associated equipment
	for _, equip := range fp.Equipment {
		if err := idx.engine.Index(ctx, "equipment", equip.ID, equip); err != nil {
			return err
		}
	}
	
	return nil
}

// IndexEquipment indexes a single piece of equipment
func (idx *DatabaseIndexer) IndexEquipment(ctx context.Context, equip *models.Equipment) error {
	return idx.engine.Index(ctx, "equipment", equip.ID, equip)
}

// IndexRoom indexes a single room
func (idx *DatabaseIndexer) IndexRoom(ctx context.Context, room *models.Room) error {
	return idx.engine.Index(ctx, "room", room.ID, room)
}

// Stats returns indexer statistics
func (idx *DatabaseIndexer) Stats() map[string]interface{} {
	engineStats := idx.engine.Stats()
	
	return map[string]interface{}{
		"engine_stats":     engineStats,
		"refresh_interval": idx.refreshInterval,
		"running":         idx.running,
	}
}