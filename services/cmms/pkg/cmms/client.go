package cmms

import (
	"arx-cmms/internal/connector"
	"arx-cmms/internal/sync"
	"arx-cmms/pkg/models"
	"context"
	"time"

	"gorm.io/gorm"
)

// Client provides a public API for CMMS operations
type Client struct {
	db          *gorm.DB
	connector   *connector.CMMSConnector
	syncManager *sync.SyncManager
}

// NewClient creates a new CMMS client
func NewClient(db *gorm.DB) *Client {
	return &Client{
		db:          db,
		syncManager: sync.NewSyncManager(db),
	}
}

// GetConnection retrieves a CMMS connection by ID
func (c *Client) GetConnection(id int) (*models.CMMSConnection, error) {
	var conn models.CMMSConnection
	err := c.db.First(&conn, id).Error
	if err != nil {
		return nil, err
	}
	return &conn, nil
}

// ListConnections retrieves all CMMS connections
func (c *Client) ListConnections() ([]models.CMMSConnection, error) {
	var conns []models.CMMSConnection
	err := c.db.Find(&conns).Error
	return conns, err
}

// CreateConnection creates a new CMMS connection
func (c *Client) CreateConnection(conn *models.CMMSConnection) error {
	conn.CreatedAt = time.Now()
	conn.UpdatedAt = time.Now()
	return c.db.Create(conn).Error
}

// UpdateConnection updates an existing CMMS connection
func (c *Client) UpdateConnection(conn *models.CMMSConnection) error {
	conn.UpdatedAt = time.Now()
	return c.db.Save(conn).Error
}

// DeleteConnection deletes a CMMS connection
func (c *Client) DeleteConnection(id int) error {
	return c.db.Delete(&models.CMMSConnection{}, id).Error
}

// TestConnection tests a CMMS connection
func (c *Client) TestConnection(id int) error {
	conn, err := c.GetConnection(id)
	if err != nil {
		return err
	}

	cmmsConnector := connector.NewCMMSConnector(conn, c.db)
	return cmmsConnector.TestConnection()
}

// SyncConnection performs a manual sync for a CMMS connection
func (c *Client) SyncConnection(ctx context.Context, id int, syncType string) error {
	conn, err := c.GetConnection(id)
	if err != nil {
		return err
	}

	cmmsConnector := connector.NewCMMSConnector(conn, c.db)

	switch syncType {
	case "schedules":
		_, err = c.syncManager.SyncSchedules(ctx, conn, cmmsConnector.GetClient())
	case "work_orders":
		_, err = c.syncManager.SyncWorkOrders(ctx, conn, cmmsConnector.GetClient())
	case "specs":
		_, err = c.syncManager.SyncEquipmentSpecs(ctx, conn, cmmsConnector.GetClient())
	default:
		return cmmsConnector.SyncAll(ctx)
	}

	return err
}

// GetMappings retrieves field mappings for a CMMS connection
func (c *Client) GetMappings(connectionID int) ([]models.CMMSMapping, error) {
	return c.syncManager.GetMappings(connectionID)
}

// CreateMapping creates a new field mapping
func (c *Client) CreateMapping(mapping *models.CMMSMapping) error {
	return c.db.Create(mapping).Error
}

// GetSyncLogs retrieves sync logs for a CMMS connection
func (c *Client) GetSyncLogs(connectionID int, limit int) ([]models.CMMSSyncLog, error) {
	var logs []models.CMMSSyncLog
	err := c.db.Where("cmms_connection_id = ?", connectionID).
		Order("started_at DESC").
		Limit(limit).
		Find(&logs).Error
	return logs, err
}

// StartSyncScheduler starts the background CMMS sync scheduler
func (c *Client) StartSyncScheduler() {
	connector.StartCMMSSyncScheduler(c.db)
}
