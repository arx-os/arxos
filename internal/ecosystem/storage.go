package ecosystem

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/database"
)

// TierStorage manages storage operations across the three-tier ecosystem
type TierStorage struct {
	postgis *database.PostGISDB
	tier    Tier
}

// NewTierStorage creates a new tier-specific storage instance
func NewTierStorage(postgis *database.PostGISDB, tier Tier) *TierStorage {
	return &TierStorage{
		postgis: postgis,
		tier:    tier,
	}
}

// Core Storage Operations (Layer 1 - FREE)
func (ts *TierStorage) CreateBuilding(ctx context.Context, req CreateBuildingRequest) (*Building, error) {
	if ts.tier != TierCore {
		return nil, fmt.Errorf("building creation requires core tier access")
	}

	// Simple PostGIS-only storage for core tier
	query := `
		INSERT INTO buildings (id, name, path, tier, metadata, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
		RETURNING id, name, path, tier, metadata, created_at, updated_at
	`

	var storageBuilding StorageBuilding
	err := ts.postgis.QueryRow(ctx, query,
		generateID(),
		req.Name,
		req.Path,
		string(ts.tier),
		req.Metadata,
	).Scan(
		&storageBuilding.ID,
		&storageBuilding.Name,
		&storageBuilding.Path,
		&storageBuilding.Tier,
		&storageBuilding.Metadata,
		&storageBuilding.CreatedAt,
		&storageBuilding.UpdatedAt,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to create building: %w", err)
	}

	// Convert to interface type
	building := &Building{
		ID:       storageBuilding.ID,
		Name:     storageBuilding.Name,
		Path:     storageBuilding.Path,
		Tier:     storageBuilding.Tier,
		Metadata: storageBuilding.Metadata,
	}

	return building, nil
}

func (ts *TierStorage) GetBuilding(ctx context.Context, id string) (*Building, error) {
	// Core tier always has read access
	query := `
		SELECT id, name, path, tier, metadata, created_at, updated_at
		FROM buildings
		WHERE id = $1
	`

	var storageBuilding StorageBuilding
	err := ts.postgis.QueryRow(ctx, query, id).Scan(
		&storageBuilding.ID,
		&storageBuilding.Name,
		&storageBuilding.Path,
		&storageBuilding.Tier,
		&storageBuilding.Metadata,
		&storageBuilding.CreatedAt,
		&storageBuilding.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("building not found")
		}
		return nil, fmt.Errorf("failed to get building: %w", err)
	}

	// Convert to interface type
	building := &Building{
		ID:       storageBuilding.ID,
		Name:     storageBuilding.Name,
		Path:     storageBuilding.Path,
		Tier:     storageBuilding.Tier,
		Metadata: storageBuilding.Metadata,
	}

	return building, nil
}

func (ts *TierStorage) CreateEquipment(ctx context.Context, req CreateEquipmentRequest) (*Equipment, error) {
	if ts.tier != TierCore {
		return nil, fmt.Errorf("equipment creation requires core tier access")
	}

	// Store equipment with spatial data in PostGIS
	query := `
		INSERT INTO equipment (id, name, path, type, position, tier, metadata, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
		RETURNING id, name, path, type, position, tier, metadata, created_at, updated_at
	`

	var storageEquipment StorageEquipment
	err := ts.postgis.QueryRow(ctx, query,
		generateID(),
		req.Name,
		req.Path,
		req.Type,
		req.Position,
		string(ts.tier),
		req.Metadata,
	).Scan(
		&storageEquipment.ID,
		&storageEquipment.Name,
		&storageEquipment.Path,
		&storageEquipment.Type,
		&storageEquipment.Position,
		&storageEquipment.Tier,
		&storageEquipment.Metadata,
		&storageEquipment.CreatedAt,
		&storageEquipment.UpdatedAt,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to create equipment: %w", err)
	}

	// Convert to interface type
	equipment := &Equipment{
		ID:       storageEquipment.ID,
		Name:     storageEquipment.Name,
		Path:     storageEquipment.Path,
		Type:     storageEquipment.Type,
		Position: storageEquipment.Position,
		Metadata: storageEquipment.Metadata,
	}

	return equipment, nil
}

func (ts *TierStorage) QueryEquipment(ctx context.Context, query EquipmentQuery) ([]*Equipment, error) {
	// Core tier always has read access
	sqlQuery := `
		SELECT id, name, path, type, position, tier, metadata, created_at, updated_at
		FROM equipment
		WHERE 1=1
	`

	args := []interface{}{}
	argIndex := 1

	if query.BuildingID != "" {
		sqlQuery += fmt.Sprintf(" AND building_id = $%d", argIndex)
		args = append(args, query.BuildingID)
		argIndex++
	}

	if query.Type != "" {
		sqlQuery += fmt.Sprintf(" AND type = $%d", argIndex)
		args = append(args, query.Type)
		argIndex++
	}

	if query.Limit > 0 {
		sqlQuery += fmt.Sprintf(" LIMIT $%d", argIndex)
		args = append(args, query.Limit)
		argIndex++
	}

	if query.Offset > 0 {
		sqlQuery += fmt.Sprintf(" OFFSET $%d", argIndex)
		args = append(args, query.Offset)
	}

	rows, err := ts.postgis.Query(ctx, sqlQuery, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to query equipment: %w", err)
	}
	defer rows.Close()

	var equipment []*Equipment
	for rows.Next() {
		var storageItem StorageEquipment
		err := rows.Scan(
			&storageItem.ID,
			&storageItem.Name,
			&storageItem.Path,
			&storageItem.Type,
			&storageItem.Position,
			&storageItem.Tier,
			&storageItem.Metadata,
			&storageItem.CreatedAt,
			&storageItem.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan equipment: %w", err)
		}

		// Convert to interface type
		item := &Equipment{
			ID:       storageItem.ID,
			Name:     storageItem.Name,
			Path:     storageItem.Path,
			Type:     storageItem.Type,
			Position: storageItem.Position,
			Metadata: storageItem.Metadata,
		}
		equipment = append(equipment, item)
	}

	return equipment, nil
}

// Hardware Storage Operations (Layer 2 - FREEMIUM)
func (ts *TierStorage) CreateDevice(ctx context.Context, req RegisterDeviceRequest) (*Device, error) {
	if ts.tier != TierHardware && ts.tier != TierWorkflow {
		return nil, fmt.Errorf("device creation requires hardware tier access")
	}

	query := `
		INSERT INTO devices (id, name, type, template_id, status, config, tier, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
		RETURNING id, name, type, template_id, status, config, tier, created_at, updated_at
	`

	var storageDevice StorageDevice
	err := ts.postgis.QueryRow(ctx, query,
		generateID(),
		req.Name,
		req.Type,
		req.TemplateID,
		"active",
		req.Config,
		string(ts.tier),
	).Scan(
		&storageDevice.ID,
		&storageDevice.Name,
		&storageDevice.Type,
		&storageDevice.TemplateID,
		&storageDevice.Status,
		&storageDevice.Config,
		&storageDevice.Tier,
		&storageDevice.CreatedAt,
		&storageDevice.UpdatedAt,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to create device: %w", err)
	}

	// Convert to interface type
	device := &Device{
		ID:         storageDevice.ID,
		Name:       storageDevice.Name,
		Type:       storageDevice.Type,
		TemplateID: storageDevice.TemplateID,
		Status:     storageDevice.Status,
		Config:     storageDevice.Config,
	}

	return device, nil
}

func (ts *TierStorage) ListDevices(ctx context.Context, userID string) ([]*Device, error) {
	if ts.tier != TierHardware && ts.tier != TierWorkflow {
		return nil, fmt.Errorf("device listing requires hardware tier access")
	}

	query := `
		SELECT id, name, type, template_id, status, config, tier, created_at, updated_at
		FROM devices
		WHERE user_id = $1
		ORDER BY created_at DESC
	`

	rows, err := ts.postgis.Query(ctx, query, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to list devices: %w", err)
	}
	defer rows.Close()

	var devices []*Device
	for rows.Next() {
		var storageDevice StorageDevice
		err := rows.Scan(
			&storageDevice.ID,
			&storageDevice.Name,
			&storageDevice.Type,
			&storageDevice.TemplateID,
			&storageDevice.Status,
			&storageDevice.Config,
			&storageDevice.Tier,
			&storageDevice.CreatedAt,
			&storageDevice.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan device: %w", err)
		}

		// Convert to interface type
		device := &Device{
			ID:         storageDevice.ID,
			Name:       storageDevice.Name,
			Type:       storageDevice.Type,
			TemplateID: storageDevice.TemplateID,
			Status:     storageDevice.Status,
			Config:     storageDevice.Config,
		}
		devices = append(devices, device)
	}

	return devices, nil
}

// Workflow Storage Operations (Layer 3 - PAID)
func (ts *TierStorage) CreateWorkflow(ctx context.Context, req CreateWorkflowRequest) (*Workflow, error) {
	if ts.tier != TierWorkflow {
		return nil, fmt.Errorf("workflow creation requires workflow tier access")
	}

	query := `
		INSERT INTO workflows (id, name, description, definition, status, tier, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
		RETURNING id, name, description, definition, status, tier, created_at, updated_at
	`

	var storageWorkflow StorageWorkflow
	err := ts.postgis.QueryRow(ctx, query,
		generateID(),
		req.Name,
		req.Description,
		req.Definition,
		"active",
		string(ts.tier),
	).Scan(
		&storageWorkflow.ID,
		&storageWorkflow.Name,
		&storageWorkflow.Description,
		&storageWorkflow.Definition,
		&storageWorkflow.Status,
		&storageWorkflow.Tier,
		&storageWorkflow.CreatedAt,
		&storageWorkflow.UpdatedAt,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to create workflow: %w", err)
	}

	// Convert to interface type
	workflow := &Workflow{
		ID:          storageWorkflow.ID,
		Name:        storageWorkflow.Name,
		Description: storageWorkflow.Description,
		Definition:  storageWorkflow.Definition,
		Status:      storageWorkflow.Status,
	}

	return workflow, nil
}

func (ts *TierStorage) CreateWorkOrder(ctx context.Context, req CreateWorkOrderRequest) (*WorkOrder, error) {
	if ts.tier != TierWorkflow {
		return nil, fmt.Errorf("work order creation requires workflow tier access")
	}

	query := `
		INSERT INTO work_orders (id, title, description, priority, status, equipment_id, metadata, tier, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
		RETURNING id, title, description, priority, status, equipment_id, metadata, tier, created_at, updated_at
	`

	var storageWorkOrder StorageWorkOrder
	err := ts.postgis.QueryRow(ctx, query,
		generateID(),
		req.Title,
		req.Description,
		req.Priority,
		"open",
		req.EquipmentID,
		req.Metadata,
		string(ts.tier),
	).Scan(
		&storageWorkOrder.ID,
		&storageWorkOrder.Title,
		&storageWorkOrder.Description,
		&storageWorkOrder.Priority,
		&storageWorkOrder.Status,
		&storageWorkOrder.EquipmentID,
		&storageWorkOrder.Metadata,
		&storageWorkOrder.Tier,
		&storageWorkOrder.CreatedAt,
		&storageWorkOrder.UpdatedAt,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to create work order: %w", err)
	}

	// Convert to interface type
	workOrder := &WorkOrder{
		ID:          storageWorkOrder.ID,
		Title:       storageWorkOrder.Title,
		Description: storageWorkOrder.Description,
		Priority:    storageWorkOrder.Priority,
		Status:      storageWorkOrder.Status,
		EquipmentID: storageWorkOrder.EquipmentID,
		Metadata:    storageWorkOrder.Metadata,
	}

	return workOrder, nil
}

// Helper function to generate unique IDs
func generateID() string {
	// Simple ID generation - in production, use proper UUID generation
	return fmt.Sprintf("id_%d", time.Now().UnixNano())
}

// Storage-specific data structures with additional fields
type StorageBuilding struct {
	ID        string                 `json:"id"`
	Name      string                 `json:"name"`
	Path      string                 `json:"path"`
	Tier      Tier                   `json:"tier"`
	Metadata  map[string]interface{} `json:"metadata"`
	CreatedAt time.Time              `json:"created_at"`
	UpdatedAt time.Time              `json:"updated_at"`
}

type StorageEquipment struct {
	ID        string                 `json:"id"`
	Name      string                 `json:"name"`
	Path      string                 `json:"path"`
	Type      string                 `json:"type"`
	Position  map[string]interface{} `json:"position"`
	Tier      Tier                   `json:"tier"`
	Metadata  map[string]interface{} `json:"metadata"`
	CreatedAt time.Time              `json:"created_at"`
	UpdatedAt time.Time              `json:"updated_at"`
}

type StorageDevice struct {
	ID         string                 `json:"id"`
	Name       string                 `json:"name"`
	Type       string                 `json:"type"`
	TemplateID string                 `json:"template_id"`
	Status     string                 `json:"status"`
	Config     map[string]interface{} `json:"config"`
	Tier       Tier                   `json:"tier"`
	CreatedAt  time.Time              `json:"created_at"`
	UpdatedAt  time.Time              `json:"updated_at"`
}

type StorageWorkflow struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Definition  map[string]interface{} `json:"definition"`
	Status      string                 `json:"status"`
	Tier        Tier                   `json:"tier"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
}

type StorageWorkOrder struct {
	ID          string                 `json:"id"`
	Title       string                 `json:"title"`
	Description string                 `json:"description"`
	Priority    string                 `json:"priority"`
	Status      string                 `json:"status"`
	EquipmentID string                 `json:"equipment_id"`
	Metadata    map[string]interface{} `json:"metadata"`
	Tier        Tier                   `json:"tier"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
}
