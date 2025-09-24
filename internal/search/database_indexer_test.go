package search

import (
	"context"
	"database/sql"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// MockDB implements database.DB for testing
type MockDB struct {
	floorPlans []*models.FloorPlan
	equipment  []*models.Equipment
	rooms      []*models.Room
}

func (m *MockDB) Connect(ctx context.Context, dbPath string) error { return nil }
func (m *MockDB) Close() error { return nil }
func (m *MockDB) BeginTx(ctx context.Context) (*sql.Tx, error) { return nil, nil }
func (m *MockDB) HasSpatialSupport() bool { return false }
func (m *MockDB) GetSpatialDB() (database.SpatialDB, error) { return nil, nil }
func (m *MockDB) GetFloorPlan(ctx context.Context, id string) (*models.FloorPlan, error) { return nil, nil }
func (m *MockDB) GetAllFloorPlans(ctx context.Context) ([]*models.FloorPlan, error) { return m.floorPlans, nil }
func (m *MockDB) SaveFloorPlan(ctx context.Context, plan *models.FloorPlan) error { return nil }
func (m *MockDB) UpdateFloorPlan(ctx context.Context, plan *models.FloorPlan) error { return nil }
func (m *MockDB) DeleteFloorPlan(ctx context.Context, id string) error { return nil }
func (m *MockDB) GetEquipment(ctx context.Context, id string) (*models.Equipment, error) { return nil, nil }
func (m *MockDB) GetEquipmentByFloorPlan(ctx context.Context, floorPlanID string) ([]*models.Equipment, error) { return m.equipment, nil }
func (m *MockDB) SaveEquipment(ctx context.Context, equipment *models.Equipment) error { return nil }
func (m *MockDB) UpdateEquipment(ctx context.Context, equipment *models.Equipment) error { return nil }
func (m *MockDB) DeleteEquipment(ctx context.Context, id string) error { return nil }
func (m *MockDB) GetRoom(ctx context.Context, id string) (*models.Room, error) { return nil, nil }
func (m *MockDB) GetRoomsByFloorPlan(ctx context.Context, floorPlanID string) ([]*models.Room, error) { return m.rooms, nil }
func (m *MockDB) SaveRoom(ctx context.Context, room *models.Room) error { return nil }
func (m *MockDB) UpdateRoom(ctx context.Context, room *models.Room) error { return nil }
func (m *MockDB) DeleteRoom(ctx context.Context, id string) error { return nil }
func (m *MockDB) GetUser(ctx context.Context, id string) (*models.User, error) { return nil, nil }
func (m *MockDB) GetUserByEmail(ctx context.Context, email string) (*models.User, error) { return nil, nil }
func (m *MockDB) SaveUser(ctx context.Context, user *models.User) error { return nil }
func (m *MockDB) UpdateUser(ctx context.Context, user *models.User) error { return nil }
func (m *MockDB) DeleteUser(ctx context.Context, id string) error { return nil }
func (m *MockDB) GetOrganization(ctx context.Context, id string) (*models.Organization, error) { return nil, nil }
func (m *MockDB) SaveOrganization(ctx context.Context, org *models.Organization) error { return nil }
func (m *MockDB) UpdateOrganization(ctx context.Context, org *models.Organization) error { return nil }
func (m *MockDB) DeleteOrganization(ctx context.Context, id string) error { return nil }
func (m *MockDB) AcceptOrganizationInvitation(ctx context.Context, userID, orgID string) error { return nil }
func (m *MockDB) AddOrganizationMember(ctx context.Context, orgID, userID, role string) error { return nil }
func (m *MockDB) RemoveOrganizationMember(ctx context.Context, orgID, userID string) error { return nil }
func (m *MockDB) UpdateOrganizationMemberRole(ctx context.Context, orgID, userID, role string) error { return nil }
func (m *MockDB) GetOrganizationMembers(ctx context.Context, orgID string) ([]*models.OrganizationMember, error) { return nil, nil }
func (m *MockDB) GetOrganizationMember(ctx context.Context, orgID, userID string) (*models.OrganizationMember, error) { return nil, nil }
func (m *MockDB) CreateOrganizationInvitation(ctx context.Context, invitation *models.OrganizationInvitation) error { return nil }
func (m *MockDB) GetOrganizationInvitationByToken(ctx context.Context, token string) (*models.OrganizationInvitation, error) { return nil, nil }
func (m *MockDB) GetOrganizationInvitation(ctx context.Context, id string) (*models.OrganizationInvitation, error) { return nil, nil }
func (m *MockDB) ListOrganizationInvitations(ctx context.Context, orgID string) ([]*models.OrganizationInvitation, error) { return nil, nil }
func (m *MockDB) RevokeOrganizationInvitation(ctx context.Context, id string) error { return nil }
func (m *MockDB) Query(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error) { return nil, nil }
func (m *MockDB) QueryRow(ctx context.Context, query string, args ...interface{}) *sql.Row { return nil }
func (m *MockDB) Exec(ctx context.Context, query string, args ...interface{}) (sql.Result, error) { return nil, nil }
func (m *MockDB) Migrate(ctx context.Context) error { return nil }
func (m *MockDB) CreateUser(ctx context.Context, user *models.User) error { return nil }
func (m *MockDB) CreateSession(ctx context.Context, session *models.UserSession) error { return nil }
func (m *MockDB) GetSession(ctx context.Context, token string) (*models.UserSession, error) { return nil, nil }
func (m *MockDB) GetSessionByRefreshToken(ctx context.Context, refreshToken string) (*models.UserSession, error) { return nil, nil }
func (m *MockDB) UpdateSession(ctx context.Context, session *models.UserSession) error { return nil }
func (m *MockDB) DeleteSession(ctx context.Context, id string) error { return nil }
func (m *MockDB) DeleteExpiredSessions(ctx context.Context) error { return nil }
func (m *MockDB) DeleteUserSessions(ctx context.Context, userID string) error { return nil }
func (m *MockDB) CreatePasswordResetToken(ctx context.Context, token *models.PasswordResetToken) error { return nil }
func (m *MockDB) GetPasswordResetToken(ctx context.Context, token string) (*models.PasswordResetToken, error) { return nil, nil }
func (m *MockDB) MarkPasswordResetTokenUsed(ctx context.Context, token string) error { return nil }
func (m *MockDB) DeleteExpiredPasswordResetTokens(ctx context.Context) error { return nil }
func (m *MockDB) GetOrganizationsByUser(ctx context.Context, userID string) ([]*models.Organization, error) { return nil, nil }
func (m *MockDB) CreateOrganization(ctx context.Context, org *models.Organization) error { return nil }
func (m *MockDB) GetVersion(ctx context.Context) (int, error) { return 1, nil }

func TestNewDatabaseIndexer(t *testing.T) {
	mockDB := &MockDB{}
	refreshInterval := 5 * time.Minute
	
	indexer := NewDatabaseIndexer(mockDB, refreshInterval)
	require.NotNil(t, indexer)
	assert.Equal(t, mockDB, indexer.db)
	assert.Equal(t, refreshInterval, indexer.refreshInterval)
	assert.NotNil(t, indexer.engine)
}

func TestDatabaseIndexer_StartIndexing(t *testing.T) {
	mockDB := &MockDB{}
	indexer := NewDatabaseIndexer(mockDB, 1*time.Second)
	
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	
	err := indexer.Start(ctx)
	require.NoError(t, err)
	
	// Wait a bit for the indexer to run
	time.Sleep(100 * time.Millisecond)
	
	// Stop the indexer
	indexer.Stop()
}

func TestDatabaseIndexer_StopIndexing(t *testing.T) {
	mockDB := &MockDB{}
	indexer := NewDatabaseIndexer(mockDB, 1*time.Second)
	
	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
	defer cancel()
	
	err := indexer.Start(ctx)
	require.NoError(t, err)
	
	indexer.Stop()
	
	// Should be able to stop again without error
	indexer.Stop()
}

func TestDatabaseIndexer_ProcessChanges(t *testing.T) {
	mockDB := &MockDB{
		floorPlans: []*models.FloorPlan{
			{
				ID:          "floor_1",
				Name:        "Office Floor 1",
				Description: "First floor office space",
				Building:    "building_1",
				Level:       1,
			},
		},
		equipment: []*models.Equipment{
			{
				ID:       "equipment_1",
				Name:     "HVAC Unit",
				Type:     "hvac",
				Status:   "operational",
				RoomID:   "room_1",
			},
		},
		rooms: []*models.Room{
			{
				ID:          "room_1",
				Name:        "Conference Room",
				FloorPlanID: "floor_1",
			},
		},
	}
	
	indexer := NewDatabaseIndexer(mockDB, 1*time.Second)
	
	// Start the indexer to process changes
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	
	err := indexer.Start(ctx)
	require.NoError(t, err)
	
	// Wait a bit for indexing to complete
	time.Sleep(100 * time.Millisecond)
	
	// Stop the indexer
	indexer.Stop()
	
	// Verify the search engine has the data
	results, err := indexer.engine.Search(context.Background(), SearchOptions{
		Query: "office",
		Limit: 10,
	})
	require.NoError(t, err)
	assert.Len(t, results, 1)
	assert.Equal(t, "floor_1", results[0].ID)
}