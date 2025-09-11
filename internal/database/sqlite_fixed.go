package database

import (
	"context"
	"database/sql"
	"fmt"
	"time"
	
	"github.com/joelpate/arxos/internal/logger"
	"github.com/joelpate/arxos/pkg/models"
)

// SaveFloorPlanFixed saves a floor plan with proper foreign key handling
func (s *SQLiteDB) SaveFloorPlanFixed(ctx context.Context, plan *models.FloorPlan) error {
	tx, err := s.BeginTx(ctx)
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()
	
	// Generate ID if not set
	if plan.Name == "" {
		plan.Name = fmt.Sprintf("floor_%d", time.Now().Unix())
	}
	
	// Use INSERT OR REPLACE to handle existing floor plans
	query := `
		INSERT OR REPLACE INTO floor_plans (id, name, building, level, created_at, updated_at)
		VALUES (?, ?, ?, ?, ?, ?)
	`
	
	now := time.Now()
	if plan.CreatedAt.IsZero() {
		plan.CreatedAt = now
	}
	plan.UpdatedAt = now
	
	_, err = tx.ExecContext(ctx, query,
		plan.Name, // Using name as ID
		plan.Name,
		plan.Building,
		plan.Level,
		plan.CreatedAt,
		plan.UpdatedAt,
	)
	if err != nil {
		return fmt.Errorf("failed to insert floor plan: %w", err)
	}
	
	// First, save all rooms (they must exist before equipment can reference them)
	for i := range plan.Rooms {
		if err := s.saveRoomFixedTx(ctx, tx, plan.Name, &plan.Rooms[i]); err != nil {
			return fmt.Errorf("failed to save room %s: %w", plan.Rooms[i].ID, err)
		}
	}
	
	// Then save equipment (which may reference rooms)
	for i := range plan.Equipment {
		if err := s.saveEquipmentFixedTx(ctx, tx, plan.Name, &plan.Equipment[i]); err != nil {
			return fmt.Errorf("failed to save equipment %s: %w", plan.Equipment[i].ID, err)
		}
	}
	
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}
	
	logger.Debug("Successfully saved floor plan: %s with %d rooms and %d equipment", 
		plan.Name, len(plan.Rooms), len(plan.Equipment))
	
	return nil
}

// saveRoomFixedTx saves a room with proper error handling
func (s *SQLiteDB) saveRoomFixedTx(ctx context.Context, tx *sql.Tx, floorPlanID string, room *models.Room) error {
	// Use INSERT OR REPLACE to handle duplicate room IDs
	query := `
		INSERT OR REPLACE INTO rooms (id, name, min_x, min_y, max_x, max_y, floor_plan_id)
		VALUES (?, ?, ?, ?, ?, ?, ?)
	`
	
	_, err := tx.ExecContext(ctx, query,
		room.ID,
		room.Name,
		room.Bounds.MinX,
		room.Bounds.MinY,
		room.Bounds.MaxX,
		room.Bounds.MaxY,
		floorPlanID,
	)
	
	if err != nil {
		return fmt.Errorf("failed to insert room: %w", err)
	}
	
	return nil
}

// saveEquipmentFixedTx saves equipment with proper foreign key handling
func (s *SQLiteDB) saveEquipmentFixedTx(ctx context.Context, tx *sql.Tx, floorPlanID string, equipment *models.Equipment) error {
	// Validate room_id exists if provided
	if equipment.RoomID != "" {
		var exists bool
		checkQuery := `SELECT EXISTS(SELECT 1 FROM rooms WHERE id = ? AND floor_plan_id = ?)`
		err := tx.QueryRowContext(ctx, checkQuery, equipment.RoomID, floorPlanID).Scan(&exists)
		if err != nil {
			return fmt.Errorf("failed to check room existence: %w", err)
		}
		if !exists {
			logger.Warn("Room %s does not exist for equipment %s, setting to NULL", 
				equipment.RoomID, equipment.ID)
			equipment.RoomID = ""
		}
	}
	
	// Use INSERT OR REPLACE to handle duplicate equipment IDs
	query := `
		INSERT OR REPLACE INTO equipment (
			id, name, type, room_id, location_x, location_y, 
			status, notes, marked_by, marked_at, floor_plan_id
		)
		VALUES (?, ?, ?, NULLIF(?, ''), ?, ?, ?, ?, ?, ?, ?)
	`
	
	// Handle null marked_at
	var markedAt *time.Time
	if !equipment.MarkedAt.IsZero() {
		markedAt = &equipment.MarkedAt
	}
	
	_, err := tx.ExecContext(ctx, query,
		equipment.ID,
		equipment.Name,
		equipment.Type,
		equipment.RoomID, // NULLIF will convert empty string to NULL
		equipment.Location.X,
		equipment.Location.Y,
		equipment.Status,
		equipment.Notes,
		equipment.MarkedBy,
		markedAt,
		floorPlanID,
	)
	
	if err != nil {
		return fmt.Errorf("failed to insert equipment: %w", err)
	}
	
	return nil
}

// MigrateJSONToDatabase migrates a JSON floor plan to the database with proper handling
func (s *SQLiteDB) MigrateJSONToDatabase(ctx context.Context, plan *models.FloorPlan) error {
	logger.Info("Migrating floor plan '%s' to database", plan.Name)
	
	// Check if floor plan already exists
	var exists bool
	checkQuery := `SELECT EXISTS(SELECT 1 FROM floor_plans WHERE id = ?)`
	err := s.db.QueryRowContext(ctx, checkQuery, plan.Name).Scan(&exists)
	if err != nil {
		return fmt.Errorf("failed to check floor plan existence: %w", err)
	}
	
	if exists {
		logger.Info("Floor plan '%s' already exists, updating...", plan.Name)
		return s.UpdateFloorPlanFixed(ctx, plan)
	}
	
	// Use the fixed save method
	return s.SaveFloorPlanFixed(ctx, plan)
}

// UpdateFloorPlanFixed updates a floor plan with proper foreign key handling
func (s *SQLiteDB) UpdateFloorPlanFixed(ctx context.Context, plan *models.FloorPlan) error {
	tx, err := s.BeginTx(ctx)
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()
	
	// Update floor plan
	query := `
		UPDATE floor_plans 
		SET name = ?, building = ?, level = ?, updated_at = ?
		WHERE id = ?
	`
	
	plan.UpdatedAt = time.Now()
	
	_, err = tx.ExecContext(ctx, query,
		plan.Name,
		plan.Building,
		plan.Level,
		plan.UpdatedAt,
		plan.Name, // ID
	)
	if err != nil {
		return fmt.Errorf("failed to update floor plan: %w", err)
	}
	
	// Delete existing rooms and equipment (cascade will handle equipment)
	// This ensures clean state before re-inserting
	deleteRoomsQuery := `DELETE FROM rooms WHERE floor_plan_id = ?`
	if _, err := tx.ExecContext(ctx, deleteRoomsQuery, plan.Name); err != nil {
		return fmt.Errorf("failed to delete existing rooms: %w", err)
	}
	
	// Re-insert rooms
	for i := range plan.Rooms {
		if err := s.saveRoomFixedTx(ctx, tx, plan.Name, &plan.Rooms[i]); err != nil {
			return fmt.Errorf("failed to save room %s: %w", plan.Rooms[i].ID, err)
		}
	}
	
	// Re-insert equipment
	for i := range plan.Equipment {
		if err := s.saveEquipmentFixedTx(ctx, tx, plan.Name, &plan.Equipment[i]); err != nil {
			return fmt.Errorf("failed to save equipment %s: %w", plan.Equipment[i].ID, err)
		}
	}
	
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}
	
	logger.Debug("Successfully updated floor plan: %s", plan.Name)
	
	return nil
}

// ValidateFloorPlan checks if a floor plan data is valid before saving
func ValidateFloorPlan(plan *models.FloorPlan) error {
	if plan == nil {
		return fmt.Errorf("floor plan is nil")
	}
	
	if plan.Name == "" {
		return fmt.Errorf("floor plan name is required")
	}
	
	if plan.Building == "" {
		return fmt.Errorf("building name is required")
	}
	
	// Check for duplicate room IDs
	roomIDs := make(map[string]bool)
	for _, room := range plan.Rooms {
		if room.ID == "" {
			return fmt.Errorf("room ID is required")
		}
		if roomIDs[room.ID] {
			return fmt.Errorf("duplicate room ID: %s", room.ID)
		}
		roomIDs[room.ID] = true
	}
	
	// Check for duplicate equipment IDs and validate room references
	equipIDs := make(map[string]bool)
	for _, equip := range plan.Equipment {
		if equip.ID == "" {
			return fmt.Errorf("equipment ID is required")
		}
		if equipIDs[equip.ID] {
			return fmt.Errorf("duplicate equipment ID: %s", equip.ID)
		}
		equipIDs[equip.ID] = true
		
		// If equipment references a room, ensure it exists
		if equip.RoomID != "" && !roomIDs[equip.RoomID] {
			return fmt.Errorf("equipment %s references non-existent room %s", equip.ID, equip.RoomID)
		}
	}
	
	return nil
}