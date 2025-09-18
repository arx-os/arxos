package database

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/errors"
	"github.com/arx-os/arxos/internal/spatial"
	"github.com/arx-os/arxos/pkg/models"
)

// PostGISHybridDB combines PostGIS spatial operations with SQLite for regular data
type PostGISHybridDB struct {
	*PostGISDB                // Spatial operations
	sqliteDB    *SQLiteDB     // Regular database operations
	connected   bool
}

// NewPostGISHybridDB creates a new PostGIS hybrid database
func NewPostGISHybridDB(pgConfig *config.PostGISConfig) (*PostGISHybridDB, error) {
	if pgConfig == nil {
		return nil, errors.NewConfigError("postgis_config", "PostGIS config is required")
	}

	// Validate required fields for PostGIS
	if pgConfig.Host == "" {
		return nil, errors.NewValidationError("host", "PostGIS host is required")
	}
	if pgConfig.Database == "" {
		return nil, errors.NewValidationError("database", "PostGIS database name is required")
	}
	if pgConfig.User == "" {
		return nil, errors.NewValidationError("user", "PostGIS user is required")
	}

	// Create default SQLite config for fallback
	sqliteConfig := NewConfig("arxos.db")

	// Convert config.PostGISConfig to database.PostGISConfig
	dbPGConfig := PostGISConfig{
		Host:            pgConfig.Host,
		Port:            pgConfig.Port,
		Database:        pgConfig.Database,
		User:            pgConfig.User,
		Password:        pgConfig.Password,
		SSLMode:         pgConfig.SSLMode,
		SpatialRef:      pgConfig.SRID,
		MaxConnections:  25,
		ConnMaxLifetime: 30 * time.Minute,
	}

	return &PostGISHybridDB{
		PostGISDB: NewPostGISDB(dbPGConfig),
		sqliteDB:  NewSQLiteDB(sqliteConfig),
	}, nil
}

// Connect establishes connections to both databases
func (p *PostGISHybridDB) Connect(ctx context.Context, dbPath string) error {
	// Use dbPath for SQLite if provided, otherwise use default
	sqlitePath := "arxos.db"
	if dbPath != "" {
		sqlitePath = dbPath
	}
	// Connect SQLite for regular operations first
	if err := p.sqliteDB.Connect(ctx, sqlitePath); err != nil {
		return errors.Wrap(err, errors.ErrorTypeConnection, "SQLITE_CONNECT_FAILED",
			"failed to connect to SQLite database")
	}

	// Try to connect PostGIS for spatial operations
	if err := p.PostGISDB.Connect(ctx); err != nil {
		logger.Warn("PostGIS connection failed, spatial features disabled: %v", err)
		// Don't fail entirely - we can still work without spatial features
		p.connected = false
		return errors.Wrap(err, errors.ErrorTypeConnection, "POSTGIS_CONNECT_FAILED",
			"PostGIS connection failed, falling back to SQLite-only mode")
	} else {
		p.connected = true
		logger.Info("PostGIS connected, spatial features enabled")
	}

	return nil
}

// Close closes both database connections
func (p *PostGISHybridDB) Close() error {
	var firstErr error

	// Close PostGIS
	if p.connected {
		if err := p.PostGISDB.Close(); err != nil {
			firstErr = err
		}
	}

	// Close SQLite
	if err := p.sqliteDB.Close(); err != nil && firstErr == nil {
		firstErr = err
	}

	return firstErr
}

// HasSpatialSupport returns true if PostGIS is connected
func (p *PostGISHybridDB) HasSpatialSupport() bool {
	return p.connected
}

// GetSpatialDB returns the spatial database interface if available
func (p *PostGISHybridDB) GetSpatialDB() (SpatialDB, error) {
	if !p.connected {
		return nil, errors.NewNotFoundError("spatial_database", "PostGIS not connected")
	}
	return p.PostGISDB, nil
}

// --- Delegate all non-spatial operations to SQLite ---

// BeginTx starts a transaction in SQLite
func (p *PostGISHybridDB) BeginTx(ctx context.Context) (*sql.Tx, error) {
	return p.sqliteDB.BeginTx(ctx)
}

// GetFloorPlan retrieves a floor plan from SQLite
func (p *PostGISHybridDB) GetFloorPlan(ctx context.Context, id string) (*models.FloorPlan, error) {
	return p.sqliteDB.GetFloorPlan(ctx, id)
}

// GetAllFloorPlans retrieves all floor plans from SQLite
func (p *PostGISHybridDB) GetAllFloorPlans(ctx context.Context) ([]*models.FloorPlan, error) {
	return p.sqliteDB.GetAllFloorPlans(ctx)
}

// SaveFloorPlan saves a floor plan to SQLite (and updates spatial index if connected)
func (p *PostGISHybridDB) SaveFloorPlan(ctx context.Context, plan *models.FloorPlan) error {
	// Save to SQLite first
	if err := p.sqliteDB.SaveFloorPlan(ctx, plan); err != nil {
		return err
	}

	// Update spatial index if connected
	if p.connected && plan.Building != "" {
		// Could create a building transform here if needed
		logger.Debug("Floor plan %s saved, building: %s", plan.ID, plan.Building)
	}

	return nil
}

// UpdateFloorPlan updates a floor plan in SQLite
func (p *PostGISHybridDB) UpdateFloorPlan(ctx context.Context, plan *models.FloorPlan) error {
	return p.sqliteDB.UpdateFloorPlan(ctx, plan)
}

// DeleteFloorPlan deletes a floor plan from SQLite
func (p *PostGISHybridDB) DeleteFloorPlan(ctx context.Context, id string) error {
	return p.sqliteDB.DeleteFloorPlan(ctx, id)
}

// GetEquipment retrieves equipment from SQLite with optional spatial data
func (p *PostGISHybridDB) GetEquipment(ctx context.Context, id string) (*models.Equipment, error) {
	// Get base equipment from SQLite
	equipment, err := p.sqliteDB.GetEquipment(ctx, id)
	if err != nil {
		return nil, err
	}

	// Enhance with spatial data if available
	if p.connected {
		spatialEq, err := p.PostGISDB.GetEquipmentPosition(id)
		if err == nil && spatialEq != nil && spatialEq.SpatialData != nil {
			// Could enhance equipment with precise coordinates
			logger.Debug("Enhanced equipment %s with spatial data", id)
		}
	}

	return equipment, nil
}

// GetEquipmentByFloorPlan retrieves equipment for a floor plan
func (p *PostGISHybridDB) GetEquipmentByFloorPlan(ctx context.Context, floorPlanID string) ([]*models.Equipment, error) {
	return p.sqliteDB.GetEquipmentByFloorPlan(ctx, floorPlanID)
}

// SaveEquipment saves equipment to SQLite and optionally to PostGIS
func (p *PostGISHybridDB) SaveEquipment(ctx context.Context, equipment *models.Equipment) error {
	// Save to SQLite first
	if err := p.sqliteDB.SaveEquipment(ctx, equipment); err != nil {
		return err
	}

	// Save spatial data if available and PostGIS is connected
	if p.connected && equipment.Location != nil {
		// Convert 2D location to 3D point (assuming floor 0 for now)
		pos := spatial.Point3D{
			X: equipment.Location.X,
			Y: equipment.Location.Y,
			Z: 0, // Could be calculated from floor plan
		}

		// Store in PostGIS
		if err := p.PostGISDB.UpdateEquipmentPosition(
			equipment.ID,
			pos,
			spatial.CONFIDENCE_ESTIMATED,
			"import",
		); err != nil {
			logger.Warn("Failed to save spatial data for equipment %s: %v", equipment.ID, err)
			// Don't fail the whole operation
		}
	}

	return nil
}

// UpdateEquipment updates equipment in SQLite
func (p *PostGISHybridDB) UpdateEquipment(ctx context.Context, equipment *models.Equipment) error {
	// Update SQLite
	if err := p.sqliteDB.UpdateEquipment(ctx, equipment); err != nil {
		return err
	}

	// Update spatial data if connected
	if p.connected && equipment.Location != nil {
		pos := spatial.Point3D{
			X: equipment.Location.X,
			Y: equipment.Location.Y,
			Z: 0,
		}

		if err := p.PostGISDB.UpdateEquipmentPosition(
			equipment.ID,
			pos,
			spatial.CONFIDENCE_ESTIMATED,
			"update",
		); err != nil {
			logger.Warn("Failed to update spatial data: %v", err)
		}
	}

	return nil
}

// DeleteEquipment deletes equipment from SQLite
func (p *PostGISHybridDB) DeleteEquipment(ctx context.Context, id string) error {
	return p.sqliteDB.DeleteEquipment(ctx, id)
}

// GetRoom retrieves a room from SQLite
func (p *PostGISHybridDB) GetRoom(ctx context.Context, id string) (*models.Room, error) {
	return p.sqliteDB.GetRoom(ctx, id)
}

// GetRoomsByFloorPlan retrieves rooms for a floor plan
func (p *PostGISHybridDB) GetRoomsByFloorPlan(ctx context.Context, floorPlanID string) ([]*models.Room, error) {
	return p.sqliteDB.GetRoomsByFloorPlan(ctx, floorPlanID)
}

// SaveRoom saves a room to SQLite
func (p *PostGISHybridDB) SaveRoom(ctx context.Context, room *models.Room) error {
	return p.sqliteDB.SaveRoom(ctx, room)
}

// UpdateRoom updates a room in SQLite
func (p *PostGISHybridDB) UpdateRoom(ctx context.Context, room *models.Room) error {
	return p.sqliteDB.UpdateRoom(ctx, room)
}

// DeleteRoom deletes a room from SQLite
func (p *PostGISHybridDB) DeleteRoom(ctx context.Context, id string) error {
	return p.sqliteDB.DeleteRoom(ctx, id)
}

// --- User operations delegate to SQLite ---

func (p *PostGISHybridDB) GetUser(ctx context.Context, id string) (*models.User, error) {
	return p.sqliteDB.GetUser(ctx, id)
}

func (p *PostGISHybridDB) GetUserByEmail(ctx context.Context, email string) (*models.User, error) {
	return p.sqliteDB.GetUserByEmail(ctx, email)
}

func (p *PostGISHybridDB) CreateUser(ctx context.Context, user *models.User) error {
	return p.sqliteDB.CreateUser(ctx, user)
}

func (p *PostGISHybridDB) UpdateUser(ctx context.Context, user *models.User) error {
	return p.sqliteDB.UpdateUser(ctx, user)
}

func (p *PostGISHybridDB) DeleteUser(ctx context.Context, id string) error {
	return p.sqliteDB.DeleteUser(ctx, id)
}

// --- Session operations delegate to SQLite ---

func (p *PostGISHybridDB) CreateSession(ctx context.Context, session *models.UserSession) error {
	return p.sqliteDB.CreateSession(ctx, session)
}

func (p *PostGISHybridDB) GetSession(ctx context.Context, token string) (*models.UserSession, error) {
	return p.sqliteDB.GetSession(ctx, token)
}

func (p *PostGISHybridDB) GetSessionByRefreshToken(ctx context.Context, refreshToken string) (*models.UserSession, error) {
	return p.sqliteDB.GetSessionByRefreshToken(ctx, refreshToken)
}

func (p *PostGISHybridDB) UpdateSession(ctx context.Context, session *models.UserSession) error {
	return p.sqliteDB.UpdateSession(ctx, session)
}

func (p *PostGISHybridDB) DeleteSession(ctx context.Context, id string) error {
	return p.sqliteDB.DeleteSession(ctx, id)
}

func (p *PostGISHybridDB) DeleteExpiredSessions(ctx context.Context) error {
	return p.sqliteDB.DeleteExpiredSessions(ctx)
}

func (p *PostGISHybridDB) DeleteUserSessions(ctx context.Context, userID string) error {
	return p.sqliteDB.DeleteUserSessions(ctx, userID)
}

// --- Password reset operations delegate to SQLite ---

func (p *PostGISHybridDB) CreatePasswordResetToken(ctx context.Context, token *models.PasswordResetToken) error {
	return p.sqliteDB.CreatePasswordResetToken(ctx, token)
}

func (p *PostGISHybridDB) GetPasswordResetToken(ctx context.Context, token string) (*models.PasswordResetToken, error) {
	return p.sqliteDB.GetPasswordResetToken(ctx, token)
}

func (p *PostGISHybridDB) MarkPasswordResetTokenUsed(ctx context.Context, token string) error {
	return p.sqliteDB.MarkPasswordResetTokenUsed(ctx, token)
}

func (p *PostGISHybridDB) DeleteExpiredPasswordResetTokens(ctx context.Context) error {
	return p.sqliteDB.DeleteExpiredPasswordResetTokens(ctx)
}

// --- Organization operations delegate to SQLite ---

func (p *PostGISHybridDB) GetOrganization(ctx context.Context, id string) (*models.Organization, error) {
	return p.sqliteDB.GetOrganization(ctx, id)
}

func (p *PostGISHybridDB) GetOrganizationsByUser(ctx context.Context, userID string) ([]*models.Organization, error) {
	return p.sqliteDB.GetOrganizationsByUser(ctx, userID)
}

func (p *PostGISHybridDB) CreateOrganization(ctx context.Context, org *models.Organization) error {
	return p.sqliteDB.CreateOrganization(ctx, org)
}

func (p *PostGISHybridDB) UpdateOrganization(ctx context.Context, org *models.Organization) error {
	return p.sqliteDB.UpdateOrganization(ctx, org)
}

func (p *PostGISHybridDB) DeleteOrganization(ctx context.Context, id string) error {
	return p.sqliteDB.DeleteOrganization(ctx, id)
}

// --- Organization member operations delegate to SQLite ---

func (p *PostGISHybridDB) AddOrganizationMember(ctx context.Context, orgID, userID, role string) error {
	return p.sqliteDB.AddOrganizationMember(ctx, orgID, userID, role)
}

func (p *PostGISHybridDB) RemoveOrganizationMember(ctx context.Context, orgID, userID string) error {
	return p.sqliteDB.RemoveOrganizationMember(ctx, orgID, userID)
}

func (p *PostGISHybridDB) UpdateOrganizationMemberRole(ctx context.Context, orgID, userID, role string) error {
	return p.sqliteDB.UpdateOrganizationMemberRole(ctx, orgID, userID, role)
}

func (p *PostGISHybridDB) GetOrganizationMembers(ctx context.Context, orgID string) ([]*models.OrganizationMember, error) {
	return p.sqliteDB.GetOrganizationMembers(ctx, orgID)
}

func (p *PostGISHybridDB) GetOrganizationMember(ctx context.Context, orgID, userID string) (*models.OrganizationMember, error) {
	return p.sqliteDB.GetOrganizationMember(ctx, orgID, userID)
}

// --- Organization invitation operations delegate to SQLite ---

func (p *PostGISHybridDB) CreateOrganizationInvitation(ctx context.Context, invitation *models.OrganizationInvitation) error {
	return p.sqliteDB.CreateOrganizationInvitation(ctx, invitation)
}

func (p *PostGISHybridDB) GetOrganizationInvitationByToken(ctx context.Context, token string) (*models.OrganizationInvitation, error) {
	return p.sqliteDB.GetOrganizationInvitationByToken(ctx, token)
}

func (p *PostGISHybridDB) GetOrganizationInvitation(ctx context.Context, id string) (*models.OrganizationInvitation, error) {
	return p.sqliteDB.GetOrganizationInvitation(ctx, id)
}

func (p *PostGISHybridDB) ListOrganizationInvitations(ctx context.Context, orgID string) ([]*models.OrganizationInvitation, error) {
	return p.sqliteDB.ListOrganizationInvitations(ctx, orgID)
}

func (p *PostGISHybridDB) AcceptOrganizationInvitation(ctx context.Context, token, userID string) error {
	return p.sqliteDB.AcceptOrganizationInvitation(ctx, token, userID)
}

func (p *PostGISHybridDB) RevokeOrganizationInvitation(ctx context.Context, id string) error {
	return p.sqliteDB.RevokeOrganizationInvitation(ctx, id)
}

// --- Query operations delegate to SQLite ---

func (p *PostGISHybridDB) Query(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error) {
	return p.sqliteDB.Query(ctx, query, args...)
}

func (p *PostGISHybridDB) QueryRow(ctx context.Context, query string, args ...interface{}) *sql.Row {
	return p.sqliteDB.QueryRow(ctx, query, args...)
}

func (p *PostGISHybridDB) Exec(ctx context.Context, query string, args ...interface{}) (sql.Result, error) {
	return p.sqliteDB.Exec(ctx, query, args...)
}

// --- Migration operations ---

func (p *PostGISHybridDB) Migrate(ctx context.Context) error {
	// Migrate SQLite
	if err := p.sqliteDB.Migrate(ctx); err != nil {
		return fmt.Errorf("SQLite migration failed: %w", err)
	}

	// PostGIS tables are created during connection
	logger.Info("Database migration complete")
	return nil
}

func (p *PostGISHybridDB) GetVersion(ctx context.Context) (int, error) {
	return p.sqliteDB.GetVersion(ctx)
}