// Package database provides database storage for ArxObjects
package database

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"time"

	"arxos/core/arxobject"
	"github.com/lib/pq"
	_ "github.com/lib/pq"
	"github.com/jmoiron/sqlx"
	"go.uber.org/zap"
)

// ArxObjectStore manages ArxObject persistence
type ArxObjectStore struct {
	db       *sqlx.DB
	logger   *zap.Logger
	config   StoreConfig
	prepared map[string]*sqlx.Stmt
}

// StoreConfig configures the database store
type StoreConfig struct {
	DSN               string        `json:"dsn"`
	MaxConnections    int           `json:"max_connections"`
	MaxIdleConns      int           `json:"max_idle_conns"`
	ConnMaxLifetime   time.Duration `json:"conn_max_lifetime"`
	EnablePostGIS     bool          `json:"enable_postgis"`
	BatchSize         int           `json:"batch_size"`
	TransactionRetries int          `json:"transaction_retries"`
}

// BuildingInfo represents building metadata
type BuildingInfo struct {
	ID           string    `db:"id" json:"id"`
	Name         string    `db:"name" json:"name"`
	Address      string    `db:"address" json:"address"`
	TotalFloors  int       `db:"total_floors" json:"total_floors"`
	TotalObjects int       `db:"total_objects" json:"total_objects"`
	CreatedAt    time.Time `db:"created_at" json:"created_at"`
	UpdatedAt    time.Time `db:"updated_at" json:"updated_at"`
	Metadata     json.RawMessage `db:"metadata" json:"metadata"`
}

// NewArxObjectStore creates a new database store
func NewArxObjectStore(backend string) (*ArxObjectStore, error) {
	config := StoreConfig{
		DSN:             getEnvOrDefault("DATABASE_URL", "postgres://localhost/arxos"),
		MaxConnections:  20,
		MaxIdleConns:    5,
		ConnMaxLifetime: 5 * time.Minute,
		EnablePostGIS:   true,
		BatchSize:       1000,
		TransactionRetries: 3,
	}

	return NewArxObjectStoreWithConfig(config)
}

// NewArxObjectStoreWithConfig creates a store with specific configuration
func NewArxObjectStoreWithConfig(config StoreConfig) (*ArxObjectStore, error) {
	db, err := sqlx.Connect("postgres", config.DSN)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to database: %w", err)
	}

	// Configure connection pool
	db.SetMaxOpenConns(config.MaxConnections)
	db.SetMaxIdleConns(config.MaxIdleConns)
	db.SetConnMaxLifetime(config.ConnMaxLifetime)

	// Test connection
	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	store := &ArxObjectStore{
		db:       db,
		logger:   zap.NewNop(), // Default to no-op logger
		config:   config,
		prepared: make(map[string]*sqlx.Stmt),
	}

	// Initialize schema if needed
	if err := store.initializeSchema(); err != nil {
		return nil, fmt.Errorf("failed to initialize schema: %w", err)
	}

	// Prepare common statements
	if err := store.prepareStatements(); err != nil {
		return nil, fmt.Errorf("failed to prepare statements: %w", err)
	}

	return store, nil
}

// StoreBatch stores multiple ArxObjects in a transaction
func (s *ArxObjectStore) StoreBatch(ctx context.Context, buildingID string, objects []*arxobject.ArxObjectOptimized) error {
	if len(objects) == 0 {
		return nil
	}

	// Start transaction with retries
	var err error
	for retry := 0; retry < s.config.TransactionRetries; retry++ {
		err = s.storeBatchTx(ctx, buildingID, objects)
		if err == nil {
			return nil
		}
		
		// Check if error is retryable
		if !isRetryableError(err) {
			break
		}
		
		// Exponential backoff
		time.Sleep(time.Duration(1<<uint(retry)) * 100 * time.Millisecond)
	}
	
	return fmt.Errorf("failed to store batch after %d retries: %w", s.config.TransactionRetries, err)
}

// storeBatchTx performs the actual batch storage in a transaction
func (s *ArxObjectStore) storeBatchTx(ctx context.Context, buildingID string, objects []*arxobject.ArxObjectOptimized) error {
	tx, err := s.db.BeginTxx(ctx, nil)
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	// Ensure building exists
	if err := s.ensureBuilding(ctx, tx, buildingID); err != nil {
		return fmt.Errorf("failed to ensure building: %w", err)
	}

	// Process in batches for better performance
	batchSize := s.config.BatchSize
	for i := 0; i < len(objects); i += batchSize {
		end := min(i+batchSize, len(objects))
		batch := objects[i:end]
		
		if err := s.insertObjectBatch(ctx, tx, buildingID, batch); err != nil {
			return fmt.Errorf("failed to insert batch %d-%d: %w", i, end, err)
		}
	}

	// Update building statistics
	if err := s.updateBuildingStats(ctx, tx, buildingID); err != nil {
		return fmt.Errorf("failed to update building stats: %w", err)
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	s.logger.Info("Stored ArxObject batch",
		zap.String("building_id", buildingID),
		zap.Int("objects", len(objects)))

	return nil
}

// insertObjectBatch inserts a batch of objects using COPY or bulk insert
func (s *ArxObjectStore) insertObjectBatch(ctx context.Context, tx *sqlx.Tx, buildingID string, objects []*arxobject.ArxObjectOptimized) error {
	if s.config.EnablePostGIS {
		return s.insertWithPostGIS(ctx, tx, buildingID, objects)
	}
	return s.insertStandard(ctx, tx, buildingID, objects)
}

// insertWithPostGIS uses PostGIS for spatial data
func (s *ArxObjectStore) insertWithPostGIS(ctx context.Context, tx *sqlx.Tx, buildingID string, objects []*arxobject.ArxObjectOptimized) error {
	stmt, err := tx.PrepareContext(ctx, `
		INSERT INTO arx_objects (
			id, building_id, object_type, system_type, scale_level,
			x_nano, y_nano, z_nano, length_nano, width_nano, height_nano,
			type_flags, rotation_pack, metadata_id, parent_id,
			geom, properties, created_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
			ST_MakePoint($6::float8/1e9, $7::float8/1e9, $8::float8/1e9), $16, $17)
		ON CONFLICT (id, building_id) DO UPDATE SET
			x_nano = EXCLUDED.x_nano,
			y_nano = EXCLUDED.y_nano,
			z_nano = EXCLUDED.z_nano,
			length_nano = EXCLUDED.length_nano,
			width_nano = EXCLUDED.width_nano,
			height_nano = EXCLUDED.height_nano,
			geom = EXCLUDED.geom,
			properties = EXCLUDED.properties,
			updated_at = NOW()
	`)
	if err != nil {
		return fmt.Errorf("failed to prepare statement: %w", err)
	}
	defer stmt.Close()

	for _, obj := range objects {
		properties := s.extractProperties(obj)
		propsJSON, _ := json.Marshal(properties)
		
		_, err := stmt.ExecContext(ctx,
			obj.ID,
			buildingID,
			obj.GetType(),
			obj.GetSystem(),
			obj.GetScale(),
			obj.X,
			obj.Y,
			obj.Z,
			obj.Length,
			obj.Width,
			obj.Height,
			obj.TypeFlags,
			obj.RotationPack,
			obj.MetadataID,
			obj.ParentID,
			propsJSON,
			time.Now(),
		)
		if err != nil {
			return fmt.Errorf("failed to insert object %d: %w", obj.ID, err)
		}
	}

	return nil
}

// insertStandard uses standard SQL without PostGIS
func (s *ArxObjectStore) insertStandard(ctx context.Context, tx *sqlx.Tx, buildingID string, objects []*arxobject.ArxObjectOptimized) error {
	// Build bulk insert values
	valueStrings := make([]string, 0, len(objects))
	valueArgs := make([]interface{}, 0, len(objects)*16)
	
	for i, obj := range objects {
		properties := s.extractProperties(obj)
		propsJSON, _ := json.Marshal(properties)
		
		valueStrings = append(valueStrings, fmt.Sprintf(
			"($%d, $%d, $%d, $%d, $%d, $%d, $%d, $%d, $%d, $%d, $%d, $%d, $%d, $%d, $%d, $%d)",
			i*16+1, i*16+2, i*16+3, i*16+4, i*16+5, i*16+6, i*16+7, i*16+8,
			i*16+9, i*16+10, i*16+11, i*16+12, i*16+13, i*16+14, i*16+15, i*16+16,
		))
		
		valueArgs = append(valueArgs,
			obj.ID,
			buildingID,
			obj.GetType(),
			obj.GetSystem(),
			obj.GetScale(),
			obj.X,
			obj.Y,
			obj.Z,
			obj.Length,
			obj.Width,
			obj.Height,
			obj.TypeFlags,
			obj.RotationPack,
			obj.MetadataID,
			obj.ParentID,
			propsJSON,
		)
	}
	
	query := fmt.Sprintf(`
		INSERT INTO arx_objects (
			id, building_id, object_type, system_type, scale_level,
			x_nano, y_nano, z_nano, length_nano, width_nano, height_nano,
			type_flags, rotation_pack, metadata_id, parent_id, properties
		) VALUES %s
		ON CONFLICT (id, building_id) DO UPDATE SET
			x_nano = EXCLUDED.x_nano,
			y_nano = EXCLUDED.y_nano,
			z_nano = EXCLUDED.z_nano,
			updated_at = NOW()
	`, strings.Join(valueStrings, ","))
	
	_, err := tx.ExecContext(ctx, query, valueArgs...)
	return err
}

// GetBuilding retrieves building information
func (s *ArxObjectStore) GetBuilding(ctx context.Context, buildingID string) (*BuildingInfo, error) {
	var building BuildingInfo
	
	err := s.db.GetContext(ctx, &building, `
		SELECT id, name, address, total_floors, total_objects, created_at, updated_at, metadata
		FROM buildings
		WHERE id = $1
	`, buildingID)
	
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("building not found: %s", buildingID)
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get building: %w", err)
	}
	
	return &building, nil
}

// GetBuildingObjects retrieves objects for a building with optional filters
func (s *ArxObjectStore) GetBuildingObjects(ctx context.Context, buildingID, objType, floor string) ([]*arxobject.ArxObjectOptimized, error) {
	query := `
		SELECT id, object_type, system_type, scale_level,
			   x_nano, y_nano, z_nano, length_nano, width_nano, height_nano,
			   type_flags, rotation_pack, metadata_id, parent_id
		FROM arx_objects
		WHERE building_id = $1
	`
	args := []interface{}{buildingID}
	argCount := 1
	
	// Add optional filters
	if objType != "" {
		argCount++
		query += fmt.Sprintf(" AND object_type = $%d", argCount)
		args = append(args, objType)
	}
	
	if floor != "" {
		// Calculate Z range for floor (assuming 3m per floor)
		floorNum := 0
		fmt.Sscanf(floor, "%d", &floorNum)
		zMin := int64(floorNum-1) * 3 * arxobject.Meter
		zMax := int64(floorNum) * 3 * arxobject.Meter
		
		argCount += 2
		query += fmt.Sprintf(" AND z_nano >= $%d AND z_nano < $%d", argCount-1, argCount)
		args = append(args, zMin, zMax)
	}
	
	query += " ORDER BY id"
	
	rows, err := s.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to query objects: %w", err)
	}
	defer rows.Close()
	
	var objects []*arxobject.ArxObjectOptimized
	for rows.Next() {
		obj := &arxobject.ArxObjectOptimized{}
		err := rows.Scan(
			&obj.ID,
			&objType, // Temporary variable
			&obj.TypeFlags, // Will reconstruct from components
			&obj.X,
			&obj.Y,
			&obj.Z,
			&obj.Length,
			&obj.Width,
			&obj.Height,
			&obj.TypeFlags,
			&obj.RotationPack,
			&obj.MetadataID,
			&obj.ParentID,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan object: %w", err)
		}
		objects = append(objects, obj)
	}
	
	return objects, nil
}

// ensureBuilding creates building record if it doesn't exist
func (s *ArxObjectStore) ensureBuilding(ctx context.Context, tx *sqlx.Tx, buildingID string) error {
	_, err := tx.ExecContext(ctx, `
		INSERT INTO buildings (id, name, created_at, updated_at)
		VALUES ($1, $2, NOW(), NOW())
		ON CONFLICT (id) DO NOTHING
	`, buildingID, "Unnamed Building")
	
	return err
}

// updateBuildingStats updates building statistics
func (s *ArxObjectStore) updateBuildingStats(ctx context.Context, tx *sqlx.Tx, buildingID string) error {
	_, err := tx.ExecContext(ctx, `
		UPDATE buildings 
		SET total_objects = (
			SELECT COUNT(*) FROM arx_objects WHERE building_id = $1
		),
		total_floors = (
			SELECT COUNT(DISTINCT FLOOR(z_nano / $2)) 
			FROM arx_objects 
			WHERE building_id = $1
		),
		updated_at = NOW()
		WHERE id = $1
	`, buildingID, 3*arxobject.Meter)
	
	return err
}

// extractProperties extracts properties from ArxObject for JSON storage
func (s *ArxObjectStore) extractProperties(obj *arxobject.ArxObjectOptimized) map[string]interface{} {
	props := make(map[string]interface{})
	
	// Extract basic properties
	props["type"] = obj.GetType()
	props["system"] = obj.GetSystem()
	props["scale"] = obj.GetScale()
	props["active"] = obj.IsActive()
	
	// Extract rotation if present
	if obj.RotationPack != 0 {
		props["rotation"] = float64(obj.RotationPack>>32) / 1000.0 // Convert from milliradians
	}
	
	// Add dimension info
	props["dimensions"] = map[string]float64{
		"length_m": float64(obj.Length) / float64(arxobject.Meter),
		"width_m":  float64(obj.Width) / float64(arxobject.Meter),
		"height_m": float64(obj.Height) / float64(arxobject.Meter),
	}
	
	return props
}

// initializeSchema ensures database schema exists
func (s *ArxObjectStore) initializeSchema() error {
	schema := `
	CREATE TABLE IF NOT EXISTS buildings (
		id VARCHAR(36) PRIMARY KEY,
		name VARCHAR(255),
		address TEXT,
		total_floors INTEGER DEFAULT 0,
		total_objects INTEGER DEFAULT 0,
		created_at TIMESTAMP NOT NULL DEFAULT NOW(),
		updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
		metadata JSONB
	);

	CREATE TABLE IF NOT EXISTS arx_objects (
		id BIGINT NOT NULL,
		building_id VARCHAR(36) NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
		object_type SMALLINT NOT NULL,
		system_type SMALLINT NOT NULL,
		scale_level SMALLINT NOT NULL,
		x_nano BIGINT NOT NULL,
		y_nano BIGINT NOT NULL,
		z_nano BIGINT NOT NULL,
		length_nano BIGINT NOT NULL,
		width_nano BIGINT NOT NULL,
		height_nano BIGINT NOT NULL,
		type_flags BIGINT NOT NULL,
		rotation_pack BIGINT,
		metadata_id BIGINT,
		parent_id BIGINT,
		properties JSONB,
		created_at TIMESTAMP NOT NULL DEFAULT NOW(),
		updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
		PRIMARY KEY (id, building_id)
	);

	CREATE INDEX IF NOT EXISTS idx_arx_objects_building ON arx_objects(building_id);
	CREATE INDEX IF NOT EXISTS idx_arx_objects_type ON arx_objects(object_type);
	CREATE INDEX IF NOT EXISTS idx_arx_objects_system ON arx_objects(system_type);
	CREATE INDEX IF NOT EXISTS idx_arx_objects_parent ON arx_objects(parent_id);
	CREATE INDEX IF NOT EXISTS idx_arx_objects_z ON arx_objects(z_nano);
	`

	// Add PostGIS extensions if enabled
	if s.config.EnablePostGIS {
		schema = `CREATE EXTENSION IF NOT EXISTS postgis;` + schema + `
		ALTER TABLE arx_objects ADD COLUMN IF NOT EXISTS geom geometry(PointZ, 4326);
		CREATE INDEX IF NOT EXISTS idx_arx_objects_geom ON arx_objects USING GIST(geom);
		`
	}

	_, err := s.db.Exec(schema)
	return err
}

// prepareStatements prepares commonly used SQL statements
func (s *ArxObjectStore) prepareStatements() error {
	statements := map[string]string{
		"get_building": `
			SELECT id, name, address, total_floors, total_objects, created_at, updated_at, metadata
			FROM buildings WHERE id = $1
		`,
		"get_objects_by_type": `
			SELECT * FROM arx_objects 
			WHERE building_id = $1 AND object_type = $2
			ORDER BY id
		`,
		"get_objects_in_bbox": `
			SELECT * FROM arx_objects 
			WHERE building_id = $1 
			AND x_nano >= $2 AND x_nano <= $3
			AND y_nano >= $4 AND y_nano <= $5
			AND z_nano >= $6 AND z_nano <= $7
		`,
	}

	for name, query := range statements {
		stmt, err := s.db.Preparex(query)
		if err != nil {
			return fmt.Errorf("failed to prepare %s: %w", name, err)
		}
		s.prepared[name] = stmt
	}

	return nil
}

// Close closes the database connection
func (s *ArxObjectStore) Close() error {
	// Close prepared statements
	for _, stmt := range s.prepared {
		stmt.Close()
	}
	
	// Close database connection
	return s.db.Close()
}

// SetLogger sets the logger for the store
func (s *ArxObjectStore) SetLogger(logger *zap.Logger) {
	s.logger = logger
}

// Helper functions

func isRetryableError(err error) bool {
	if err == nil {
		return false
	}
	
	// Check for PostgreSQL specific errors
	if pqErr, ok := err.(*pq.Error); ok {
		switch pqErr.Code {
		case "40001", // serialization_failure
		     "40P01", // deadlock_detected
		     "55P03": // lock_not_available
			return true
		}
	}
	
	// Check for connection errors
	if err == sql.ErrConnDone {
		return true
	}
	
	return false
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func getEnvOrDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}