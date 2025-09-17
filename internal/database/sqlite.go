package database

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"path/filepath"
	"strings"
	"time"

	_ "modernc.org/sqlite"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/pkg/models"
)

// SQLiteDB implements the DB interface using SQLite
type SQLiteDB struct {
	db     *sql.DB
	config *Config
}

// NewSQLiteDB creates a new SQLite database instance with the provided configuration.
// The database is not connected until Connect() is called explicitly.
func NewSQLiteDB(config *Config) *SQLiteDB {
	return &SQLiteDB{
		config: config,
	}
}

// NewSQLiteDBFromPath creates a new SQLite database instance from a file path.
// It automatically connects to the database and runs migrations, making it ready for use.
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
	
	// Run migrations using embedded files
	if err := RunMigrations(db, ""); err != nil {
		logger.Warn("Failed to run migrations: %v", err)
		// Continue anyway for backward compatibility
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

// Migrate runs database migrations
func (s *SQLiteDB) Migrate(ctx context.Context) error {
	// Run migrations using the migration runner
	if s.db == nil {
		return fmt.Errorf("database not connected")
	}

	return RunMigrations(s.db, "") // Use embedded migrations
}

// GetVersion returns the current database schema version
func (s *SQLiteDB) GetVersion(ctx context.Context) (int, error) {
	var version int
	query := `SELECT COALESCE(MAX(version), 0) FROM schema_migrations`

	err := s.db.QueryRowContext(ctx, query).Scan(&version)
	if err != nil {
		// Table might not exist yet
		return 0, nil
	}

	return version, nil
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
		&plan.ID,
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
	// Rooms are now []*Room
	plan.Rooms = rooms
	
	// Load equipment
	equipment, err := s.GetEquipmentByFloorPlan(ctx, id)
	if err != nil {
		return nil, err
	}
	plan.Equipment = equipment
	
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
		err := rows.Scan(
			&plan.ID,
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
		rooms, _ := s.GetRoomsByFloorPlan(ctx, plan.ID)
		plan.Rooms = rooms
		equipment, _ := s.GetEquipmentByFloorPlan(ctx, plan.ID)
		plan.Equipment = equipment
		
		plans = append(plans, &plan)
	}
	
	return plans, nil
}

// SaveFloorPlan saves a new floor plan
func (s *SQLiteDB) SaveFloorPlan(ctx context.Context, plan *models.FloorPlan) error {
	// Generate ID if not set
	if plan.ID == "" {
		if plan.Name != "" {
			plan.ID = plan.Name
		} else {
			plan.ID = fmt.Sprintf("floor_%d", time.Now().Unix())
			plan.Name = plan.ID
		}
	}
	
	// Validate floor plan before saving
	if err := ValidateFloorPlan(plan); err != nil {
		return fmt.Errorf("invalid floor plan: %w", err)
	}
	// Use the original implementation
	return s.SaveFloorPlanOld(ctx, plan)
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
	plan.CreatedAt = &now
	plan.UpdatedAt = &now
	
	// Use plan.ID if available, otherwise use name
	planID := plan.ID
	if planID == "" {
		planID = plan.Name
	}

	_, err = tx.ExecContext(ctx, query,
		planID,
		plan.Name,
		plan.Building,
		plan.Level,
		*plan.CreatedAt,
		*plan.UpdatedAt,
	)
	if err != nil {
		return fmt.Errorf("failed to insert floor plan: %w", err)
	}
	
	// Save rooms
	for _, room := range plan.Rooms {
		if err := s.saveRoomTx(ctx, tx, planID, room); err != nil {
			return err
		}
	}

	// Save equipment
	for _, eq := range plan.Equipment {
		if err := s.saveEquipmentTx(ctx, tx, planID, eq); err != nil {
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
	// Use the original implementation
	return s.UpdateFloorPlanOld(ctx, plan)
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
	
	now := time.Now()
	plan.UpdatedAt = &now
	
	_, err = tx.ExecContext(ctx, query,
		plan.Name,
		plan.Building,
		plan.Level,
		*plan.UpdatedAt,
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
	for _, room := range plan.Rooms {
		if err := s.saveRoomTx(ctx, tx, plan.Name, room); err != nil {
			return err
		}
	}

	for _, eq := range plan.Equipment {
		if err := s.saveEquipmentTx(ctx, tx, plan.Name, eq); err != nil {
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
		SELECT id, name, equipment_type, room_id, location_x, location_y, location_z,
		       status, model, serial_number, metadata, installation_date, building_id
		FROM equipment
		WHERE LOWER(id) = LOWER(?)
	`

	var equipment models.Equipment
	var locationX, locationY, locationZ sql.NullFloat64
	var roomID, model, serial, buildingID sql.NullString
	var metadataJSON sql.NullString
	var installDate sql.NullTime

	err := s.db.QueryRowContext(ctx, query, id).Scan(
		&equipment.ID,
		&equipment.Name,
		&equipment.Type,
		&roomID,
		&locationX,
		&locationY,
		&locationZ,
		&equipment.Status,
		&model,
		&serial,
		&metadataJSON,
		&installDate,
		&buildingID,
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
	if locationX.Valid || locationY.Valid {
		equipment.Location = &models.Point{
			X: locationX.Float64,
			Y: locationY.Float64,
		}
	}
	if installDate.Valid {
		t := installDate.Time
		equipment.Installed = &t
	}
	if model.Valid {
		equipment.Model = model.String
	}
	if serial.Valid {
		equipment.Serial = serial.String
	}

	// Parse metadata JSON
	if metadataJSON.Valid && metadataJSON.String != "" {
		var metadata map[string]interface{}
		if err := json.Unmarshal([]byte(metadataJSON.String), &metadata); err == nil {
			equipment.Metadata = metadata
		}
	}

	// Store building_id in metadata if needed
	if equipment.Metadata == nil {
		equipment.Metadata = make(map[string]interface{})
	}
	if buildingID.Valid {
		equipment.Metadata["building_id"] = buildingID.String
	}

	return &equipment, nil
}

// GetEquipmentByFloorPlan retrieves all equipment for a floor plan
func (s *SQLiteDB) GetEquipmentByFloorPlan(ctx context.Context, floorPlanID string) ([]*models.Equipment, error) {
	query := `
		SELECT id, name, equipment_type, room_id, location_x, location_y,
		       status, model, serial_number
		FROM equipment
		WHERE floor_id = ?
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
		var roomID, model, serial sql.NullString

		err := rows.Scan(
			&equipment.ID,
			&equipment.Name,
			&equipment.Type,
			&roomID,
			&locationX,
			&locationY,
			&equipment.Status,
			&model,
			&serial,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan equipment: %w", err)
		}
		
		if roomID.Valid {
			equipment.RoomID = roomID.String
		}
		if locationX.Valid || locationY.Valid {
			equipment.Location = &models.Point{}
			if locationX.Valid {
				equipment.Location.X = locationX.Float64
			}
			if locationY.Valid {
				equipment.Location.Y = locationY.Float64
			}
		}
		if model.Valid {
			equipment.Model = model.String
		}
		if serial.Valid {
			equipment.Serial = serial.String
		}
		
		equipmentList = append(equipmentList, &equipment)
	}
	
	return equipmentList, nil
}

// SaveEquipment saves new equipment
func (s *SQLiteDB) SaveEquipment(ctx context.Context, equipment *models.Equipment) error {
	// Generate equipment tag if not provided
	equipmentTag := equipment.Path
	if equipmentTag == "" {
		equipmentTag = equipment.ID
	}

	// Extract building_id from metadata or use default
	buildingID := "DEFAULT_BUILDING"
	if equipment.Metadata != nil {
		if bid, exists := equipment.Metadata["building"]; exists {
			buildingID = fmt.Sprintf("%v", bid)
		}
	}

	// Handle optional location coordinates
	var locationX, locationY, locationZ interface{}
	if equipment.Location != nil {
		locationX = equipment.Location.X
		locationY = equipment.Location.Y
	}
	if equipment.Metadata != nil {
		if z, exists := equipment.Metadata["location_z"]; exists {
			locationZ = z
		}
	}

	// Convert metadata to JSON
	var metadataJSON []byte
	if equipment.Metadata != nil {
		metadataJSON, _ = json.Marshal(equipment.Metadata)
	}

	query := `
		INSERT INTO equipment (
			id, building_id, equipment_tag, name, equipment_type,
			manufacturer, model, serial_number, status,
			location_x, location_y, location_z, metadata
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	`

	_, err := s.db.ExecContext(ctx, query,
		equipment.ID,
		buildingID,
		equipmentTag,
		equipment.Name,
		equipment.Type,
		"", // manufacturer
		equipment.Model,
		equipment.Serial,
		equipment.Status,
		locationX,
		locationY,
		locationZ,
		metadataJSON,
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
	
	// Handle nil Location
	var locX, locY float64
	if equipment.Location != nil {
		locX = equipment.Location.X
		locY = equipment.Location.Y
	}

	// Handle empty RoomID as NULL for foreign key
	var roomID interface{}
	if equipment.RoomID != "" {
		roomID = equipment.RoomID
	} else {
		roomID = nil
	}

	_, err := tx.ExecContext(ctx, query,
		equipment.ID,
		equipment.Name,
		equipment.Type,
		roomID, // NULL if empty
		locX,
		locY,
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
	// Handle optional location coordinates
	var locationX, locationY, locationZ interface{}
	if equipment.Location != nil {
		locationX = equipment.Location.X
		locationY = equipment.Location.Y
	}
	if equipment.Metadata != nil {
		if z, exists := equipment.Metadata["location_z"]; exists {
			locationZ = z
		}
	}

	// Convert metadata to JSON
	var metadataJSON []byte
	if equipment.Metadata != nil {
		metadataJSON, _ = json.Marshal(equipment.Metadata)
	}

	query := `
		UPDATE equipment
		SET name = ?, equipment_type = ?,
		    location_x = ?, location_y = ?, location_z = ?,
		    status = ?, model = ?, serial_number = ?, metadata = ?,
		    updated_at = CURRENT_TIMESTAMP
		WHERE id = ?
	`

	_, err := s.db.ExecContext(ctx, query,
		equipment.Name,
		equipment.Type,
		locationX,
		locationY,
		locationZ,
		equipment.Status,
		equipment.Model,
		equipment.Serial,
		metadataJSON,
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

// User operations

// GetUser retrieves a user by ID
func (s *SQLiteDB) GetUser(ctx context.Context, id string) (*models.User, error) {
	query := `
		SELECT id, email, name, password_hash, avatar, phone, status, 
		       email_verified, phone_verified, mfa_enabled, mfa_secret,
		       created_at, updated_at, last_login_at
		FROM users WHERE id = ?
	`
	
	var user models.User
	var lastLoginAt sql.NullTime
	
	err := s.db.QueryRowContext(ctx, query, id).Scan(
		&user.ID, &user.Email, &user.FullName, &user.PasswordHash,
		&user.Avatar, &user.Phone, &user.Status,
		&user.EmailVerified, &user.PhoneVerified, &user.MFAEnabled, &user.MFASecret,
		&user.CreatedAt, &user.UpdatedAt, &lastLoginAt,
	)
	
	if err == sql.ErrNoRows {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	
	if lastLoginAt.Valid {
		user.LastLogin = &lastLoginAt.Time
	}
	
	return &user, nil
}

// GetUserByEmail retrieves a user by email
func (s *SQLiteDB) GetUserByEmail(ctx context.Context, email string) (*models.User, error) {
	query := `
		SELECT id, email, name, password_hash, avatar, phone, status, 
		       email_verified, phone_verified, mfa_enabled, mfa_secret,
		       created_at, updated_at, last_login_at
		FROM users WHERE email = ?
	`
	
	var user models.User
	var lastLoginAt sql.NullTime
	
	err := s.db.QueryRowContext(ctx, query, email).Scan(
		&user.ID, &user.Email, &user.FullName, &user.PasswordHash,
		&user.Avatar, &user.Phone, &user.Status,
		&user.EmailVerified, &user.PhoneVerified, &user.MFAEnabled, &user.MFASecret,
		&user.CreatedAt, &user.UpdatedAt, &lastLoginAt,
	)
	
	if err == sql.ErrNoRows {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	
	if lastLoginAt.Valid {
		user.LastLogin = &lastLoginAt.Time
	}
	
	return &user, nil
}

// CreateUser creates a new user
func (s *SQLiteDB) CreateUser(ctx context.Context, user *models.User) error {
	query := `
		INSERT INTO users (id, email, name, password_hash, avatar, phone, status,
		                  email_verified, phone_verified, mfa_enabled, mfa_secret,
		                  created_at, updated_at, last_login_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	`
	
	var lastLoginAt interface{}
	if user.LastLogin != nil {
		lastLoginAt = *user.LastLogin
	}
	
	_, err := s.db.ExecContext(ctx, query,
		user.ID, user.Email, user.FullName, user.PasswordHash,
		user.Avatar, user.Phone, user.Status,
		user.EmailVerified, user.PhoneVerified, user.MFAEnabled, user.MFASecret,
		user.CreatedAt, user.UpdatedAt, lastLoginAt,
	)
	
	return err
}

// UpdateUser updates an existing user
func (s *SQLiteDB) UpdateUser(ctx context.Context, user *models.User) error {
	query := `
		UPDATE users SET 
			name = ?, password_hash = ?, avatar = ?, phone = ?, status = ?,
			email_verified = ?, phone_verified = ?, mfa_enabled = ?, mfa_secret = ?,
			updated_at = ?, last_login_at = ?
		WHERE id = ?
	`
	
	var lastLoginAt interface{}
	if user.LastLogin != nil {
		lastLoginAt = *user.LastLogin
	}
	
	_, err := s.db.ExecContext(ctx, query,
		user.FullName, user.PasswordHash, user.Avatar, user.Phone, user.Status,
		user.EmailVerified, user.PhoneVerified, user.MFAEnabled, user.MFASecret,
		user.UpdatedAt, lastLoginAt, user.ID,
	)
	
	return err
}

// DeleteUser deletes a user
func (s *SQLiteDB) DeleteUser(ctx context.Context, id string) error {
	query := `DELETE FROM users WHERE id = ?`
	_, err := s.db.ExecContext(ctx, query, id)
	return err
}

// Session operations

// CreateSession creates a new user session
func (s *SQLiteDB) CreateSession(ctx context.Context, session *models.UserSession) error {
	query := `
		INSERT INTO user_sessions (id, user_id, organization_id, token, refresh_token, 
		                          ip_address, user_agent, expires_at, created_at, last_access_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	`
	
	_, err := s.db.ExecContext(ctx, query,
		session.ID, session.UserID, session.OrganizationID, session.Token, session.RefreshToken,
		session.IPAddress, session.UserAgent, session.ExpiresAt, session.CreatedAt, session.LastAccessAt,
	)
	return err
}

// GetSession retrieves a session by access token
func (s *SQLiteDB) GetSession(ctx context.Context, token string) (*models.UserSession, error) {
	query := `
		SELECT id, user_id, organization_id, token, refresh_token,
		       ip_address, user_agent, expires_at, created_at, last_access_at
		FROM user_sessions WHERE token = ?
	`
	
	var session models.UserSession
	var orgID sql.NullString
	
	err := s.db.QueryRowContext(ctx, query, token).Scan(
		&session.ID, &session.UserID, &orgID, &session.Token, &session.RefreshToken,
		&session.IPAddress, &session.UserAgent, &session.ExpiresAt, &session.CreatedAt, &session.LastAccessAt,
	)
	
	if err == sql.ErrNoRows {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	
	if orgID.Valid {
		session.OrganizationID = orgID.String
	}
	
	return &session, nil
}

// GetSessionByRefreshToken retrieves a session by refresh token
func (s *SQLiteDB) GetSessionByRefreshToken(ctx context.Context, refreshToken string) (*models.UserSession, error) {
	query := `
		SELECT id, user_id, organization_id, token, refresh_token,
		       ip_address, user_agent, expires_at, created_at, last_access_at
		FROM user_sessions WHERE refresh_token = ?
	`
	
	var session models.UserSession
	var orgID sql.NullString
	
	err := s.db.QueryRowContext(ctx, query, refreshToken).Scan(
		&session.ID, &session.UserID, &orgID, &session.Token, &session.RefreshToken,
		&session.IPAddress, &session.UserAgent, &session.ExpiresAt, &session.CreatedAt, &session.LastAccessAt,
	)
	
	if err == sql.ErrNoRows {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	
	if orgID.Valid {
		session.OrganizationID = orgID.String
	}
	
	return &session, nil
}

// UpdateSession updates an existing session
func (s *SQLiteDB) UpdateSession(ctx context.Context, session *models.UserSession) error {
	query := `
		UPDATE user_sessions 
		SET organization_id = ?, token = ?, refresh_token = ?, 
		    expires_at = ?, last_access_at = ?
		WHERE id = ?
	`
	
	_, err := s.db.ExecContext(ctx, query,
		session.OrganizationID, session.Token, session.RefreshToken,
		session.ExpiresAt, session.LastAccessAt, session.ID,
	)
	return err
}

// DeleteSession deletes a session by ID
func (s *SQLiteDB) DeleteSession(ctx context.Context, id string) error {
	query := `DELETE FROM user_sessions WHERE id = ?`
	_, err := s.db.ExecContext(ctx, query, id)
	return err
}

// DeleteExpiredSessions removes all expired sessions
func (s *SQLiteDB) DeleteExpiredSessions(ctx context.Context) error {
	query := `DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP`
	_, err := s.db.ExecContext(ctx, query)
	return err
}

// DeleteUserSessions removes all sessions for a specific user
func (s *SQLiteDB) DeleteUserSessions(ctx context.Context, userID string) error {
	query := `DELETE FROM user_sessions WHERE user_id = ?`
	_, err := s.db.ExecContext(ctx, query, userID)
	return err
}

// Organization operations

// GetOrganization retrieves an organization by ID
func (s *SQLiteDB) GetOrganization(ctx context.Context, id string) (*models.Organization, error) {
	query := `
		SELECT id, name, slug, plan, max_users, max_buildings,
		       status, created_at, updated_at
		FROM organizations WHERE id = ?
	`
	
	var org models.Organization
	err := s.db.QueryRowContext(ctx, query, id).Scan(
		&org.ID, &org.Name, &org.Slug, 
		&org.Plan, &org.MaxUsers, &org.MaxBuildings,
		&org.Status, &org.CreatedAt, &org.UpdatedAt,
	)
	
	if err == sql.ErrNoRows {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	
	return &org, nil
}

// GetOrganizationsByUser retrieves organizations for a user
func (s *SQLiteDB) GetOrganizationsByUser(ctx context.Context, userID string) ([]*models.Organization, error) {
	query := `
		SELECT o.id, o.name, o.slug, o.plan, 
		       o.max_users, o.max_buildings, o.status, 
		       o.created_at, o.updated_at
		FROM organizations o
		JOIN organization_members om ON o.id = om.organization_id
		WHERE om.user_id = ?
	`
	
	rows, err := s.db.QueryContext(ctx, query, userID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	
	var orgs []*models.Organization
	for rows.Next() {
		var org models.Organization
		err := rows.Scan(
			&org.ID, &org.Name, &org.Slug, 
			&org.Plan, &org.MaxUsers, &org.MaxBuildings,
			&org.Status, &org.CreatedAt, &org.UpdatedAt,
		)
		if err != nil {
			return nil, err
		}
		orgs = append(orgs, &org)
	}
	
	return orgs, nil
}

// CreateOrganization creates a new organization
func (s *SQLiteDB) CreateOrganization(ctx context.Context, org *models.Organization) error {
	query := `
		INSERT INTO organizations (id, name, slug, plan, 
		                          max_users, max_buildings, status, 
		                          created_at, updated_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
	`
	
	_, err := s.db.ExecContext(ctx, query,
		org.ID, org.Name, org.Slug, org.Plan,
		org.MaxUsers, org.MaxBuildings, org.Status,
		org.CreatedAt, org.UpdatedAt,
	)
	
	return err
}

// UpdateOrganization updates an existing organization
func (s *SQLiteDB) UpdateOrganization(ctx context.Context, org *models.Organization) error {
	query := `
		UPDATE organizations SET 
			name = ?, slug = ?, plan = ?,
			max_users = ?, max_buildings = ?, status = ?, updated_at = ?
		WHERE id = ?
	`
	
	_, err := s.db.ExecContext(ctx, query,
		org.Name, org.Slug, org.Plan,
		org.MaxUsers, org.MaxBuildings, org.Status, org.UpdatedAt,
		org.ID,
	)
	
	return err
}

// DeleteOrganization deletes an organization
func (s *SQLiteDB) DeleteOrganization(ctx context.Context, id string) error {
	query := `DELETE FROM organizations WHERE id = ?`
	_, err := s.db.ExecContext(ctx, query, id)
	return err
}

// Organization member operations

// AddOrganizationMember adds a member to an organization
func (s *SQLiteDB) AddOrganizationMember(ctx context.Context, orgID, userID, role string) error {
	query := `
		INSERT INTO organization_members (organization_id, user_id, role, joined_at)
		VALUES (?, ?, ?, ?)
	`
	
	_, err := s.db.ExecContext(ctx, query, orgID, userID, role, time.Now())
	return err
}

// RemoveOrganizationMember removes a member from an organization
func (s *SQLiteDB) RemoveOrganizationMember(ctx context.Context, orgID, userID string) error {
	query := `DELETE FROM organization_members WHERE organization_id = ? AND user_id = ?`
	_, err := s.db.ExecContext(ctx, query, orgID, userID)
	return err
}

// UpdateOrganizationMemberRole updates a member's role in an organization
func (s *SQLiteDB) UpdateOrganizationMemberRole(ctx context.Context, orgID, userID, role string) error {
	query := `
		UPDATE organization_members SET role = ? 
		WHERE organization_id = ? AND user_id = ?
	`
	
	_, err := s.db.ExecContext(ctx, query, role, orgID, userID)
	return err
}

// GetOrganizationMembers retrieves members of an organization
func (s *SQLiteDB) GetOrganizationMembers(ctx context.Context, orgID string) ([]*models.OrganizationMember, error) {
	query := `
		SELECT om.user_id, om.organization_id, om.role, om.joined_at,
		       u.email, u.name, u.avatar
		FROM organization_members om
		JOIN users u ON om.user_id = u.id
		WHERE om.organization_id = ?
	`
	
	rows, err := s.db.QueryContext(ctx, query, orgID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	
	var members []*models.OrganizationMember
	for rows.Next() {
		var member models.OrganizationMember
		var joinedAt sql.NullTime
		
		// Initialize user if nil
		if member.User == nil {
			member.User = &models.User{}
		}
		
		err := rows.Scan(
			&member.UserID, &member.OrganizationID, &member.Role, 
			&joinedAt,
			&member.User.Email, &member.User.FullName, &member.User.Avatar,
		)
		if err != nil {
			return nil, err
		}
		
		if joinedAt.Valid {
			member.JoinedAt = &joinedAt.Time
		}
		
		member.User.ID = member.UserID
		members = append(members, &member)
	}
	
	return members, nil
}

// GetOrganizationMember retrieves a specific member of an organization
func (s *SQLiteDB) GetOrganizationMember(ctx context.Context, orgID, userID string) (*models.OrganizationMember, error) {
	query := `
		SELECT om.user_id, om.organization_id, om.role, om.joined_at,
		       u.email, u.name, u.avatar
		FROM organization_members om
		JOIN users u ON om.user_id = u.id
		WHERE om.organization_id = ? AND om.user_id = ?
	`
	
	var member models.OrganizationMember
	var joinedAt sql.NullTime
	
	// Initialize user
	member.User = &models.User{}
	
	err := s.db.QueryRowContext(ctx, query, orgID, userID).Scan(
		&member.UserID, &member.OrganizationID, &member.Role, 
		&joinedAt,
		&member.User.Email, &member.User.FullName, &member.User.Avatar,
	)
	
	if err == sql.ErrNoRows {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	
	if joinedAt.Valid {
		member.JoinedAt = &joinedAt.Time
	}
	
	member.User.ID = member.UserID
	return &member, nil
}

// Organization invitation operations

// CreateOrganizationInvitation creates a new organization invitation
func (s *SQLiteDB) CreateOrganizationInvitation(ctx context.Context, invitation *models.OrganizationInvitation) error {
	query := `
		INSERT INTO organization_invitations 
		(id, organization_id, email, role, token, invited_by, expires_at, created_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?)
	`
	
	_, err := s.db.ExecContext(ctx, query,
		invitation.ID, invitation.OrganizationID, invitation.Email, invitation.Role,
		invitation.Token, invitation.InvitedBy, invitation.ExpiresAt, invitation.CreatedAt,
	)
	
	return err
}

// GetOrganizationInvitationByToken retrieves an invitation by token
func (s *SQLiteDB) GetOrganizationInvitationByToken(ctx context.Context, token string) (*models.OrganizationInvitation, error) {
	query := `
		SELECT id, organization_id, email, role, token, invited_by, expires_at, accepted_at, created_at
		FROM organization_invitations WHERE token = ?
	`
	
	var invitation models.OrganizationInvitation
	var acceptedAt sql.NullTime
	
	err := s.db.QueryRowContext(ctx, query, token).Scan(
		&invitation.ID, &invitation.OrganizationID, &invitation.Email, &invitation.Role,
		&invitation.Token, &invitation.InvitedBy, &invitation.ExpiresAt, &acceptedAt, &invitation.CreatedAt,
	)
	
	if err == sql.ErrNoRows {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	
	if acceptedAt.Valid {
		invitation.AcceptedAt = &acceptedAt.Time
	}
	
	return &invitation, nil
}

// GetOrganizationInvitation retrieves an invitation by ID
func (s *SQLiteDB) GetOrganizationInvitation(ctx context.Context, id string) (*models.OrganizationInvitation, error) {
	query := `
		SELECT id, organization_id, email, role, token, invited_by, expires_at, accepted_at, created_at
		FROM organization_invitations WHERE id = ?
	`
	
	var invitation models.OrganizationInvitation
	var acceptedAt sql.NullTime
	
	err := s.db.QueryRowContext(ctx, query, id).Scan(
		&invitation.ID, &invitation.OrganizationID, &invitation.Email, &invitation.Role,
		&invitation.Token, &invitation.InvitedBy, &invitation.ExpiresAt, &acceptedAt, &invitation.CreatedAt,
	)
	
	if err == sql.ErrNoRows {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	
	if acceptedAt.Valid {
		invitation.AcceptedAt = &acceptedAt.Time
	}
	
	return &invitation, nil
}

// ListOrganizationInvitations retrieves pending invitations for an organization
func (s *SQLiteDB) ListOrganizationInvitations(ctx context.Context, orgID string) ([]*models.OrganizationInvitation, error) {
	query := `
		SELECT id, organization_id, email, role, token, invited_by, expires_at, accepted_at, created_at
		FROM organization_invitations 
		WHERE organization_id = ? AND accepted_at IS NULL
		ORDER BY created_at DESC
	`
	
	rows, err := s.db.QueryContext(ctx, query, orgID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	
	var invitations []*models.OrganizationInvitation
	for rows.Next() {
		var invitation models.OrganizationInvitation
		var acceptedAt sql.NullTime
		
		err := rows.Scan(
			&invitation.ID, &invitation.OrganizationID, &invitation.Email, &invitation.Role,
			&invitation.Token, &invitation.InvitedBy, &invitation.ExpiresAt, &acceptedAt, &invitation.CreatedAt,
		)
		if err != nil {
			return nil, err
		}
		
		if acceptedAt.Valid {
			invitation.AcceptedAt = &acceptedAt.Time
		}
		
		invitations = append(invitations, &invitation)
	}
	
	return invitations, nil
}

// AcceptOrganizationInvitation marks an invitation as accepted and creates membership
func (s *SQLiteDB) AcceptOrganizationInvitation(ctx context.Context, token, userID string) error {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	
	// Get invitation details
	var invitation models.OrganizationInvitation
	query := `
		SELECT id, organization_id, email, role, invited_by, expires_at, accepted_at
		FROM organization_invitations WHERE token = ?
	`
	
	var acceptedAt sql.NullTime
	err = tx.QueryRowContext(ctx, query, token).Scan(
		&invitation.ID, &invitation.OrganizationID, &invitation.Email, 
		&invitation.Role, &invitation.InvitedBy, &invitation.ExpiresAt, &acceptedAt,
	)
	
	if err == sql.ErrNoRows {
		return ErrNotFound
	}
	if err != nil {
		return err
	}
	
	// Check if already accepted
	if acceptedAt.Valid {
		return fmt.Errorf("invitation already accepted")
	}
	
	// Check if expired
	if time.Now().After(invitation.ExpiresAt) {
		return fmt.Errorf("invitation expired")
	}
	
	// Mark invitation as accepted
	now := time.Now()
	updateQuery := `UPDATE organization_invitations SET accepted_at = ? WHERE token = ?`
	_, err = tx.ExecContext(ctx, updateQuery, now, token)
	if err != nil {
		return err
	}
	
	// Add user to organization
	memberQuery := `
		INSERT INTO organization_members (organization_id, user_id, role, joined_at)
		VALUES (?, ?, ?, ?)
	`
	_, err = tx.ExecContext(ctx, memberQuery, invitation.OrganizationID, userID, invitation.Role, now)
	if err != nil {
		return err
	}
	
	return tx.Commit()
}

// RevokeOrganizationInvitation deletes an invitation
func (s *SQLiteDB) RevokeOrganizationInvitation(ctx context.Context, id string) error {
	query := `DELETE FROM organization_invitations WHERE id = ?`
	_, err := s.db.ExecContext(ctx, query, id)
	return err
}

// Password Reset Token operations

// CreatePasswordResetToken creates a new password reset token
func (s *SQLiteDB) CreatePasswordResetToken(ctx context.Context, token *models.PasswordResetToken) error {
	query := `
		INSERT INTO password_reset_tokens (id, user_id, token, expires_at, used, created_at)
		VALUES (?, ?, ?, ?, ?, ?)
	`
	_, err := s.db.ExecContext(ctx, query,
		token.ID, token.UserID, token.Token, token.ExpiresAt, token.Used, token.CreatedAt,
	)
	return err
}

// GetPasswordResetToken retrieves a password reset token
func (s *SQLiteDB) GetPasswordResetToken(ctx context.Context, token string) (*models.PasswordResetToken, error) {
	query := `
		SELECT id, user_id, token, expires_at, used, created_at, used_at
		FROM password_reset_tokens
		WHERE token = ?
	`
	
	var resetToken models.PasswordResetToken
	err := s.db.QueryRowContext(ctx, query, token).Scan(
		&resetToken.ID,
		&resetToken.UserID,
		&resetToken.Token,
		&resetToken.ExpiresAt,
		&resetToken.Used,
		&resetToken.CreatedAt,
		&resetToken.UsedAt,
	)
	
	if err == sql.ErrNoRows {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	
	return &resetToken, nil
}

// MarkPasswordResetTokenUsed marks a password reset token as used
func (s *SQLiteDB) MarkPasswordResetTokenUsed(ctx context.Context, token string) error {
	query := `
		UPDATE password_reset_tokens
		SET used = true, used_at = ?
		WHERE token = ?
	`
	_, err := s.db.ExecContext(ctx, query, time.Now(), token)
	return err
}

// DeleteExpiredPasswordResetTokens deletes expired password reset tokens
func (s *SQLiteDB) DeleteExpiredPasswordResetTokens(ctx context.Context) error {
	query := `
		DELETE FROM password_reset_tokens
		WHERE expires_at < ? OR used = true
	`
	_, err := s.db.ExecContext(ctx, query, time.Now())
	return err
}

// HasSpatialSupport returns false as SQLite doesn't have PostGIS
func (s *SQLiteDB) HasSpatialSupport() bool {
	return false
}

// GetSpatialDB returns an error as SQLite doesn't support spatial operations
func (s *SQLiteDB) GetSpatialDB() (SpatialDB, error) {
	return nil, fmt.Errorf("spatial operations not supported in SQLite mode")
}