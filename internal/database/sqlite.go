package database

import (
	"context"
	"database/sql"
	"fmt"
	"path/filepath"
	"strings"
	"time"

	_ "modernc.org/sqlite"
	
	"github.com/joelpate/arxos/internal/logger"
	"github.com/joelpate/arxos/pkg/models"
)

// SQLiteDB implements the DB interface using SQLite
type SQLiteDB struct {
	db     *sql.DB
	config *Config
}

// NewSQLiteDB creates a new SQLite database instance
func NewSQLiteDB(config *Config) *SQLiteDB {
	return &SQLiteDB{
		config: config,
	}
}

// NewSQLiteDBFromPath creates a new SQLite database instance from a path
func NewSQLiteDBFromPath(dbPath string) (*SQLiteDB, error) {
	config := NewConfig(dbPath)
	db := NewSQLiteDB(config)
	
	// Connect immediately
	ctx := context.Background()
	if err := db.Connect(ctx, dbPath); err != nil {
		return nil, err
	}
	
	return db, nil
}

// Connect establishes a connection to the SQLite database
func (s *SQLiteDB) Connect(ctx context.Context, dbPath string) error {
	if dbPath == "" {
		dbPath = s.config.DatabasePath
	}
	
	// Ensure absolute path
	absPath, err := filepath.Abs(dbPath)
	if err != nil {
		return fmt.Errorf("failed to get absolute path: %w", err)
	}
	
	// Open database connection
	db, err := sql.Open("sqlite", absPath+"?_pragma=foreign_keys(1)&_pragma=journal_mode(WAL)")
	if err != nil {
		return fmt.Errorf("failed to open database: %w", err)
	}
	
	// Configure connection pool
	db.SetMaxOpenConns(s.config.MaxOpenConns)
	db.SetMaxIdleConns(s.config.MaxIdleConns)
	db.SetConnMaxLifetime(s.config.MaxLifetime)
	
	// Test connection
	if err := db.PingContext(ctx); err != nil {
		return fmt.Errorf("failed to ping database: %w", err)
	}
	
	s.db = db
	
	// Run migrations
	if err := s.Migrate(ctx); err != nil {
		return fmt.Errorf("failed to run migrations: %w", err)
	}
	
	logger.Info("Connected to SQLite database: %s", absPath)
	return nil
}

// Close closes the database connection
func (s *SQLiteDB) Close() error {
	if s.db != nil {
		return s.db.Close()
	}
	return nil
}

// BeginTx starts a new transaction
func (s *SQLiteDB) BeginTx(ctx context.Context) (*sql.Tx, error) {
	return s.db.BeginTx(ctx, nil)
}

// GetFloorPlan retrieves a floor plan by ID
func (s *SQLiteDB) GetFloorPlan(ctx context.Context, id string) (*models.FloorPlan, error) {
	query := `
		SELECT id, name, building, level, created_at, updated_at
		FROM floor_plans
		WHERE id = ?
	`
	
	var plan models.FloorPlan
	err := s.db.QueryRowContext(ctx, query, id).Scan(
		&plan.Name,
		&plan.Name,
		&plan.Building,
		&plan.Level,
		&plan.CreatedAt,
		&plan.UpdatedAt,
	)
	
	if err == sql.ErrNoRows {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get floor plan: %w", err)
	}
	
	// Load rooms
	rooms, err := s.GetRoomsByFloorPlan(ctx, id)
	if err != nil {
		return nil, err
	}
	// Convert []*Room to []Room
	plan.Rooms = make([]models.Room, len(rooms))
	for i, r := range rooms {
		plan.Rooms[i] = *r
	}
	
	// Load equipment
	equipment, err := s.GetEquipmentByFloorPlan(ctx, id)
	if err != nil {
		return nil, err
	}
	// Convert []*Equipment to []Equipment
	plan.Equipment = make([]models.Equipment, len(equipment))
	for i, e := range equipment {
		plan.Equipment[i] = *e
	}
	if err != nil {
		return nil, err
	}
	
	return &plan, nil
}

// GetAllFloorPlans retrieves all floor plans
func (s *SQLiteDB) GetAllFloorPlans(ctx context.Context) ([]*models.FloorPlan, error) {
	query := `
		SELECT id, name, building, level, created_at, updated_at
		FROM floor_plans
		ORDER BY building, level
	`
	
	rows, err := s.db.QueryContext(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("failed to query floor plans: %w", err)
	}
	defer rows.Close()
	
	var plans []*models.FloorPlan
	for rows.Next() {
		var plan models.FloorPlan
		var id string
		err := rows.Scan(
			&id,
			&plan.Name,
			&plan.Building,
			&plan.Level,
			&plan.CreatedAt,
			&plan.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan floor plan: %w", err)
		}
		
		// Load rooms and equipment for each plan
		rooms, _ := s.GetRoomsByFloorPlan(ctx, id)
		plan.Rooms = make([]models.Room, len(rooms))
		for i, r := range rooms {
			plan.Rooms[i] = *r
		}
		equipment, _ := s.GetEquipmentByFloorPlan(ctx, id)
		plan.Equipment = make([]models.Equipment, len(equipment))
		for i, e := range equipment {
			plan.Equipment[i] = *e
		}
		
		plans = append(plans, &plan)
	}
	
	return plans, nil
}

// SaveFloorPlan saves a new floor plan
func (s *SQLiteDB) SaveFloorPlan(ctx context.Context, plan *models.FloorPlan) error {
	// Validate floor plan before saving
	if err := ValidateFloorPlan(plan); err != nil {
		return fmt.Errorf("invalid floor plan: %w", err)
	}
	// Use the fixed version with proper foreign key handling
	return s.SaveFloorPlanFixed(ctx, plan)
}

// SaveFloorPlanOld is the original implementation (kept for reference)
func (s *SQLiteDB) SaveFloorPlanOld(ctx context.Context, plan *models.FloorPlan) error {
	tx, err := s.BeginTx(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	
	// Generate ID if not set
	if plan.Name == "" {
		plan.Name = fmt.Sprintf("floor_%d", time.Now().Unix())
	}
	
	// Insert floor plan
	query := `
		INSERT INTO floor_plans (id, name, building, level, created_at, updated_at)
		VALUES (?, ?, ?, ?, ?, ?)
	`
	
	now := time.Now()
	plan.CreatedAt = now
	plan.UpdatedAt = now
	
	_, err = tx.ExecContext(ctx, query,
		plan.Name, // Using name as ID for now
		plan.Name,
		plan.Building,
		plan.Level,
		plan.CreatedAt,
		plan.UpdatedAt,
	)
	if err != nil {
		return fmt.Errorf("failed to insert floor plan: %w", err)
	}
	
	// Save rooms
	for i := range plan.Rooms {
		if err := s.saveRoomTx(ctx, tx, plan.Name, &plan.Rooms[i]); err != nil {
			return err
		}
	}
	
	// Save equipment
	for i := range plan.Equipment {
		if err := s.saveEquipmentTx(ctx, tx, plan.Name, &plan.Equipment[i]); err != nil {
			return err
		}
	}
	
	return tx.Commit()
}

// UpdateFloorPlan updates an existing floor plan
func (s *SQLiteDB) UpdateFloorPlan(ctx context.Context, plan *models.FloorPlan) error {
	// Validate floor plan before updating
	if err := ValidateFloorPlan(plan); err != nil {
		return fmt.Errorf("invalid floor plan: %w", err)
	}
	// Use the fixed version with proper foreign key handling
	return s.UpdateFloorPlanFixed(ctx, plan)
}

// UpdateFloorPlanOld is the original implementation (kept for reference)
func (s *SQLiteDB) UpdateFloorPlanOld(ctx context.Context, plan *models.FloorPlan) error {
	tx, err := s.BeginTx(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	
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
		plan.Name, // Using name as ID
	)
	if err != nil {
		return fmt.Errorf("failed to update floor plan: %w", err)
	}
	
	// Delete existing rooms and equipment
	if _, err = tx.ExecContext(ctx, "DELETE FROM rooms WHERE floor_plan_id = ?", plan.Name); err != nil {
		return err
	}
	if _, err = tx.ExecContext(ctx, "DELETE FROM equipment WHERE floor_plan_id = ?", plan.Name); err != nil {
		return err
	}
	
	// Re-save rooms and equipment
	for i := range plan.Rooms {
		if err := s.saveRoomTx(ctx, tx, plan.Name, &plan.Rooms[i]); err != nil {
			return err
		}
	}
	
	for i := range plan.Equipment {
		if err := s.saveEquipmentTx(ctx, tx, plan.Name, &plan.Equipment[i]); err != nil {
			return err
		}
	}
	
	return tx.Commit()
}

// DeleteFloorPlan deletes a floor plan
func (s *SQLiteDB) DeleteFloorPlan(ctx context.Context, id string) error {
	query := `DELETE FROM floor_plans WHERE id = ?`
	_, err := s.db.ExecContext(ctx, query, id)
	return err
}

// GetEquipment retrieves equipment by ID
func (s *SQLiteDB) GetEquipment(ctx context.Context, id string) (*models.Equipment, error) {
	query := `
		SELECT id, name, type, room_id, location_x, location_y, 
		       status, notes, marked_by, marked_at, floor_plan_id
		FROM equipment
		WHERE LOWER(id) = LOWER(?)
	`
	
	var equipment models.Equipment
	var locationX, locationY sql.NullFloat64
	var markedAt sql.NullTime
	var roomID sql.NullString
	var floorPlanID string
	
	err := s.db.QueryRowContext(ctx, query, id).Scan(
		&equipment.ID,
		&equipment.Name,
		&equipment.Type,
		&roomID,
		&locationX,
		&locationY,
		&equipment.Status,
		&equipment.Notes,
		&equipment.MarkedBy,
		&markedAt,
		&floorPlanID,
	)
	
	if err == sql.ErrNoRows {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get equipment: %w", err)
	}
	
	if roomID.Valid {
		equipment.RoomID = roomID.String
	}
	equipment.Location.X = locationX.Float64
	equipment.Location.Y = locationY.Float64
	if markedAt.Valid {
		equipment.MarkedAt = markedAt.Time
	}
	
	return &equipment, nil
}

// GetEquipmentByFloorPlan retrieves all equipment for a floor plan
func (s *SQLiteDB) GetEquipmentByFloorPlan(ctx context.Context, floorPlanID string) ([]*models.Equipment, error) {
	query := `
		SELECT id, name, type, room_id, location_x, location_y, 
		       status, notes, marked_by, marked_at
		FROM equipment
		WHERE floor_plan_id = ?
		ORDER BY room_id, name
	`
	
	rows, err := s.db.QueryContext(ctx, query, floorPlanID)
	if err != nil {
		return nil, fmt.Errorf("failed to query equipment: %w", err)
	}
	defer rows.Close()
	
	var equipmentList []*models.Equipment
	for rows.Next() {
		var equipment models.Equipment
		var locationX, locationY sql.NullFloat64
		var markedAt sql.NullTime
		var roomID sql.NullString
		
		err := rows.Scan(
			&equipment.ID,
			&equipment.Name,
			&equipment.Type,
			&roomID,
			&locationX,
			&locationY,
			&equipment.Status,
			&equipment.Notes,
			&equipment.MarkedBy,
			&markedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan equipment: %w", err)
		}
		
		if roomID.Valid {
			equipment.RoomID = roomID.String
		}
		equipment.Location.X = locationX.Float64
		equipment.Location.Y = locationY.Float64
		if markedAt.Valid {
			equipment.MarkedAt = markedAt.Time
		}
		
		equipmentList = append(equipmentList, &equipment)
	}
	
	return equipmentList, nil
}

// SaveEquipment saves new equipment
func (s *SQLiteDB) SaveEquipment(ctx context.Context, equipment *models.Equipment) error {
	query := `
		INSERT INTO equipment (id, name, type, room_id, location_x, location_y, 
		                      status, notes, marked_by, marked_at, floor_plan_id)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	`
	
	_, err := s.db.ExecContext(ctx, query,
		equipment.ID,
		equipment.Name,
		equipment.Type,
		equipment.RoomID,
		equipment.Location.X,
		equipment.Location.Y,
		equipment.Status,
		equipment.Notes,
		equipment.MarkedBy,
		equipment.MarkedAt,
		"", // floor_plan_id to be set separately
	)
	
	return err
}

// saveEquipmentTx saves equipment within a transaction
func (s *SQLiteDB) saveEquipmentTx(ctx context.Context, tx *sql.Tx, floorPlanID string, equipment *models.Equipment) error {
	query := `
		INSERT INTO equipment (id, name, type, room_id, location_x, location_y, 
		                      status, notes, marked_by, marked_at, floor_plan_id)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	`
	
	_, err := tx.ExecContext(ctx, query,
		equipment.ID,
		equipment.Name,
		equipment.Type,
		equipment.RoomID,
		equipment.Location.X,
		equipment.Location.Y,
		equipment.Status,
		equipment.Notes,
		equipment.MarkedBy,
		equipment.MarkedAt,
		floorPlanID,
	)
	
	return err
}

// UpdateEquipment updates existing equipment
func (s *SQLiteDB) UpdateEquipment(ctx context.Context, equipment *models.Equipment) error {
	query := `
		UPDATE equipment 
		SET name = ?, type = ?, room_id = ?, location_x = ?, location_y = ?,
		    status = ?, notes = ?, marked_by = ?, marked_at = ?
		WHERE LOWER(id) = LOWER(?)
	`
	
	_, err := s.db.ExecContext(ctx, query,
		equipment.Name,
		equipment.Type,
		equipment.RoomID,
		equipment.Location.X,
		equipment.Location.Y,
		equipment.Status,
		equipment.Notes,
		equipment.MarkedBy,
		equipment.MarkedAt,
		equipment.ID,
	)
	
	return err
}

// DeleteEquipment deletes equipment
func (s *SQLiteDB) DeleteEquipment(ctx context.Context, id string) error {
	query := `DELETE FROM equipment WHERE LOWER(id) = LOWER(?)`
	_, err := s.db.ExecContext(ctx, query, id)
	return err
}

// GetRoom retrieves a room by ID
func (s *SQLiteDB) GetRoom(ctx context.Context, id string) (*models.Room, error) {
	query := `
		SELECT id, name, min_x, min_y, max_x, max_y, floor_plan_id
		FROM rooms
		WHERE LOWER(id) = LOWER(?)
	`
	
	var room models.Room
	var floorPlanID string
	
	err := s.db.QueryRowContext(ctx, query, id).Scan(
		&room.ID,
		&room.Name,
		&room.Bounds.MinX,
		&room.Bounds.MinY,
		&room.Bounds.MaxX,
		&room.Bounds.MaxY,
		&floorPlanID,
	)
	
	if err == sql.ErrNoRows {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get room: %w", err)
	}
	
	// Get equipment IDs for this room
	equipQuery := `SELECT id FROM equipment WHERE room_id = ?`
	rows, err := s.db.QueryContext(ctx, equipQuery, room.ID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	
	for rows.Next() {
		var equipID string
		if err := rows.Scan(&equipID); err != nil {
			continue
		}
		room.Equipment = append(room.Equipment, equipID)
	}
	
	return &room, nil
}

// GetRoomsByFloorPlan retrieves all rooms for a floor plan
func (s *SQLiteDB) GetRoomsByFloorPlan(ctx context.Context, floorPlanID string) ([]*models.Room, error) {
	query := `
		SELECT id, name, min_x, min_y, max_x, max_y
		FROM rooms
		WHERE floor_plan_id = ?
		ORDER BY name
	`
	
	rows, err := s.db.QueryContext(ctx, query, floorPlanID)
	if err != nil {
		return nil, fmt.Errorf("failed to query rooms: %w", err)
	}
	defer rows.Close()
	
	var rooms []*models.Room
	for rows.Next() {
		var room models.Room
		err := rows.Scan(
			&room.ID,
			&room.Name,
			&room.Bounds.MinX,
			&room.Bounds.MinY,
			&room.Bounds.MaxX,
			&room.Bounds.MaxY,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan room: %w", err)
		}
		
		// Get equipment IDs for this room
		equipQuery := `SELECT id FROM equipment WHERE room_id = ?`
		equipRows, err := s.db.QueryContext(ctx, equipQuery, room.ID)
		if err == nil {
			defer equipRows.Close()
			for equipRows.Next() {
				var equipID string
				if err := equipRows.Scan(&equipID); err == nil {
					room.Equipment = append(room.Equipment, equipID)
				}
			}
		}
		
		rooms = append(rooms, &room)
	}
	
	return rooms, nil
}

// SaveRoom saves a new room
func (s *SQLiteDB) SaveRoom(ctx context.Context, room *models.Room) error {
	query := `
		INSERT INTO rooms (id, name, min_x, min_y, max_x, max_y, floor_plan_id)
		VALUES (?, ?, ?, ?, ?, ?, ?)
	`
	
	_, err := s.db.ExecContext(ctx, query,
		room.ID,
		room.Name,
		room.Bounds.MinX,
		room.Bounds.MinY,
		room.Bounds.MaxX,
		room.Bounds.MaxY,
		"", // floor_plan_id to be set separately
	)
	
	return err
}

// saveRoomTx saves a room within a transaction
func (s *SQLiteDB) saveRoomTx(ctx context.Context, tx *sql.Tx, floorPlanID string, room *models.Room) error {
	query := `
		INSERT INTO rooms (id, name, min_x, min_y, max_x, max_y, floor_plan_id)
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
	
	return err
}

// UpdateRoom updates an existing room
func (s *SQLiteDB) UpdateRoom(ctx context.Context, room *models.Room) error {
	query := `
		UPDATE rooms 
		SET name = ?, min_x = ?, min_y = ?, max_x = ?, max_y = ?
		WHERE LOWER(id) = LOWER(?)
	`
	
	_, err := s.db.ExecContext(ctx, query,
		room.Name,
		room.Bounds.MinX,
		room.Bounds.MinY,
		room.Bounds.MaxX,
		room.Bounds.MaxY,
		room.ID,
	)
	
	return err
}

// DeleteRoom deletes a room
func (s *SQLiteDB) DeleteRoom(ctx context.Context, id string) error {
	query := `DELETE FROM rooms WHERE LOWER(id) = LOWER(?)`
	_, err := s.db.ExecContext(ctx, query, id)
	return err
}

// Query executes a raw SQL query
func (s *SQLiteDB) Query(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error) {
	// Basic SQL injection prevention - only allow SELECT queries
	if !strings.HasPrefix(strings.TrimSpace(strings.ToUpper(query)), "SELECT") {
		return nil, ErrInvalidQuery
	}
	
	return s.db.QueryContext(ctx, query, args...)
}

// QueryRow executes a query that returns a single row
func (s *SQLiteDB) QueryRow(ctx context.Context, query string, args ...interface{}) *sql.Row {
	return s.db.QueryRowContext(ctx, query, args...)
}

// Exec executes a query that doesn't return rows
func (s *SQLiteDB) Exec(ctx context.Context, query string, args ...interface{}) (sql.Result, error) {
	return s.db.ExecContext(ctx, query, args...)
}

// GetVersion returns the current database schema version
func (s *SQLiteDB) GetVersion(ctx context.Context) (int, error) {
	var version int
	query := `SELECT version FROM schema_version ORDER BY version DESC LIMIT 1`
	err := s.db.QueryRowContext(ctx, query).Scan(&version)
	if err == sql.ErrNoRows {
		return 0, nil
	}
	return version, err
}