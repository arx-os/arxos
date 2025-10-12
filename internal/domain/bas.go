package domain

import (
	"time"

	"github.com/arx-os/arxos/internal/domain/types"
)

// BAS (Building Automation System) domain entities
// These represent control points and systems from BAS platforms like
// Johnson Controls Metasys, Siemens Desigo, Honeywell, etc.

// BASSystemType represents the type of BAS system
type BASSystemType string

const (
	BASSystemTypeMetasys           BASSystemType = "johnson_controls_metasys"
	BASSystemTypeDesigo            BASSystemType = "siemens_desigo"
	BASSystemTypeHoneywell         BASSystemType = "honeywell_ebi"
	BASSystemTypeNiagara           BASSystemType = "tridium_niagara"
	BASSystemTypeSchneiderElectric BASSystemType = "schneider_electric"
	BASSystemTypeOther             BASSystemType = "other"
)

// BASProtocol represents communication protocols
type BASProtocol string

const (
	BASProtocolBACnet   BASProtocol = "bacnet"
	BASProtocolModbus   BASProtocol = "modbus"
	BASProtocolLonWorks BASProtocol = "lonworks"
	BASProtocolHTTP     BASProtocol = "http"
	BASProtocolHTTPS    BASProtocol = "https"
)

// BASSystem represents a Building Automation System configuration
type BASSystem struct {
	ID           types.ID      `json:"id"`
	BuildingID   types.ID      `json:"building_id"`
	RepositoryID *types.ID     `json:"repository_id,omitempty"`
	Name         string        `json:"name"`
	SystemType   BASSystemType `json:"system_type"`
	Vendor       string        `json:"vendor,omitempty"`
	Version      string        `json:"version,omitempty"`

	// Connection details (optional, for live integration)
	Host     string       `json:"host,omitempty"`
	Port     int          `json:"port,omitempty"`
	Protocol *BASProtocol `json:"protocol,omitempty"`

	// Configuration
	Enabled      bool       `json:"enabled"`
	ReadOnly     bool       `json:"read_only"`
	SyncInterval *int       `json:"sync_interval,omitempty"` // Seconds
	LastSync     *time.Time `json:"last_sync,omitempty"`

	// Metadata
	Metadata map[string]interface{} `json:"metadata,omitempty"`
	Notes    string                 `json:"notes,omitempty"`

	// Audit
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
	CreatedBy *types.ID `json:"created_by,omitempty"`
}

// BASPoint represents a single BAS control point (sensor, actuator, setpoint)
type BASPoint struct {
	ID          types.ID `json:"id"`
	BuildingID  types.ID `json:"building_id"`
	BASSystemID types.ID `json:"bas_system_id"`

	// Spatial links
	RoomID      *types.ID `json:"room_id,omitempty"`
	FloorID     *types.ID `json:"floor_id,omitempty"`
	EquipmentID *types.ID `json:"equipment_id,omitempty"`

	// BAS identifiers
	PointName      string `json:"point_name"`
	Path           string `json:"path,omitempty"` // Universal naming convention path (e.g. /B1/3/301/BAS/AI-1-1)
	DeviceID       string `json:"device_id"`
	ObjectType     string `json:"object_type"`
	ObjectInstance *int   `json:"object_instance,omitempty"`

	// Point metadata
	Description string `json:"description,omitempty"`
	Units       string `json:"units,omitempty"`
	PointType   string `json:"point_type,omitempty"`

	// Location
	LocationText string    `json:"location_text,omitempty"` // From CSV import
	Location     *Location `json:"location,omitempty"`      // Spatial coordinates

	// Point configuration
	Writeable bool     `json:"writeable"`
	MinValue  *float64 `json:"min_value,omitempty"`
	MaxValue  *float64 `json:"max_value,omitempty"`

	// Current value (if live connection)
	CurrentValue        *string    `json:"current_value,omitempty"`
	CurrentValueNumeric *float64   `json:"current_value_numeric,omitempty"`
	CurrentValueBoolean *bool      `json:"current_value_boolean,omitempty"`
	LastUpdated         *time.Time `json:"last_updated,omitempty"`

	// Mapping status
	Mapped            bool `json:"mapped"`
	MappingConfidence int  `json:"mapping_confidence"` // 0-3

	// Import tracking
	ImportedAt   time.Time `json:"imported_at"`
	ImportSource string    `json:"import_source,omitempty"`

	// Version control
	AddedInVersion   *types.ID `json:"added_in_version,omitempty"`
	RemovedInVersion *types.ID `json:"removed_in_version,omitempty"`

	// Metadata
	Metadata map[string]interface{} `json:"metadata,omitempty"`

	// Audit
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

// BASImportResult represents the result of a BAS import operation
type BASImportResult struct {
	// Import details
	ImportID types.ID `json:"import_id"`
	Filename string   `json:"filename"`
	FileSize int64    `json:"file_size"`
	FileHash string   `json:"file_hash"`

	// Results
	PointsAdded    int `json:"points_added"`
	PointsModified int `json:"points_modified"`
	PointsDeleted  int `json:"points_deleted"`
	PointsMapped   int `json:"points_mapped"`
	PointsUnmapped int `json:"points_unmapped"`

	// Status
	Status       string   `json:"status"` // success, partial, failed
	ErrorMessage string   `json:"error_message,omitempty"`
	Errors       []string `json:"errors,omitempty"`

	// Timing
	StartedAt   time.Time `json:"started_at"`
	CompletedAt time.Time `json:"completed_at"`
	DurationMS  int       `json:"duration_ms"`

	// Version control
	VersionID *types.ID `json:"version_id,omitempty"`
}

// Request/Response DTOs

// CreateBASSystemRequest represents a request to create a BAS system
type CreateBASSystemRequest struct {
	BuildingID   types.ID      `json:"building_id" validate:"required"`
	RepositoryID *types.ID     `json:"repository_id,omitempty"`
	Name         string        `json:"name" validate:"required"`
	SystemType   BASSystemType `json:"system_type" validate:"required"`
	Vendor       string        `json:"vendor,omitempty"`
	Version      string        `json:"version,omitempty"`
	Host         string        `json:"host,omitempty"`
	Port         int           `json:"port,omitempty"`
	Protocol     *BASProtocol  `json:"protocol,omitempty"`
	Enabled      bool          `json:"enabled"`
	ReadOnly     bool          `json:"read_only"`
	Notes        string        `json:"notes,omitempty"`
}

// UpdateBASSystemRequest represents a request to update a BAS system
type UpdateBASSystemRequest struct {
	ID       types.ID     `json:"id" validate:"required"`
	Name     *string      `json:"name,omitempty"`
	Vendor   *string      `json:"vendor,omitempty"`
	Version  *string      `json:"version,omitempty"`
	Host     *string      `json:"host,omitempty"`
	Port     *int         `json:"port,omitempty"`
	Protocol *BASProtocol `json:"protocol,omitempty"`
	Enabled  *bool        `json:"enabled,omitempty"`
	ReadOnly *bool        `json:"read_only,omitempty"`
	Notes    *string      `json:"notes,omitempty"`
}

// ImportBASPointsRequest represents a request to import BAS points
type ImportBASPointsRequest struct {
	BuildingID    types.ID      `json:"building_id" validate:"required"`
	BASSystemID   types.ID      `json:"bas_system_id" validate:"required"`
	RepositoryID  *types.ID     `json:"repository_id,omitempty"`
	FilePath      string        `json:"file_path" validate:"required"`
	SystemType    BASSystemType `json:"system_type" validate:"required"`
	AutoMap       bool          `json:"auto_map"`    // Attempt to map points to rooms/equipment
	AutoCommit    bool          `json:"auto_commit"` // Create version commit after import
	CommitMessage string        `json:"commit_message,omitempty"`
}

// BASPointFilter represents filters for querying BAS points
type BASPointFilter struct {
	BuildingID  *types.ID `json:"building_id,omitempty"`
	BASSystemID *types.ID `json:"bas_system_id,omitempty"`
	RoomID      *types.ID `json:"room_id,omitempty"`
	FloorID     *types.ID `json:"floor_id,omitempty"`
	EquipmentID *types.ID `json:"equipment_id,omitempty"`
	PointType   string    `json:"point_type,omitempty"`
	ObjectType  string    `json:"object_type,omitempty"`
	Mapped      *bool     `json:"mapped,omitempty"`
	DeviceID    string    `json:"device_id,omitempty"`
}

// MapBASPointRequest represents a request to map a BAS point to a location
type MapBASPointRequest struct {
	PointID     types.ID  `json:"point_id" validate:"required"`
	RoomID      *types.ID `json:"room_id,omitempty"`
	EquipmentID *types.ID `json:"equipment_id,omitempty"`
	Location    *Location `json:"location,omitempty"`
	Confidence  int       `json:"confidence" validate:"min=0,max=3"`
}

// BASPointRepository defines the interface for BAS point data access
type BASPointRepository interface {
	// CRUD operations
	Create(point *BASPoint) error
	GetByID(id types.ID) (*BASPoint, error)
	Update(point *BASPoint) error
	Delete(id types.ID) error

	// Query operations
	List(filter BASPointFilter, limit, offset int) ([]*BASPoint, error)
	Count(filter BASPointFilter) (int, error)
	ListByBuilding(buildingID types.ID) ([]*BASPoint, error)
	ListByBASSystem(systemID types.ID) ([]*BASPoint, error)
	ListByRoom(roomID types.ID) ([]*BASPoint, error)
	ListByEquipment(equipmentID types.ID) ([]*BASPoint, error)
	ListUnmapped(buildingID types.ID) ([]*BASPoint, error)

	// Bulk operations
	BulkCreate(points []*BASPoint) error
	BulkUpdate(points []*BASPoint) error

	// Mapping operations
	MapToRoom(pointID, roomID types.ID, confidence int) error
	MapToEquipment(pointID, equipmentID types.ID, confidence int) error
}

// BASSystemRepository defines the interface for BAS system data access
type BASSystemRepository interface {
	// CRUD operations
	Create(system *BASSystem) error
	GetByID(id types.ID) (*BASSystem, error)
	Update(system *BASSystem) error
	Delete(id types.ID) error

	// Query operations
	List(buildingID types.ID) ([]*BASSystem, error)
	GetByName(buildingID types.ID, name string) (*BASSystem, error)
}

// BASImportHistoryRepository defines the interface for import history data access
type BASImportHistoryRepository interface {
	Create(result *BASImportResult) error
	GetByID(id types.ID) (*BASImportResult, error)
	List(buildingID types.ID, limit, offset int) ([]*BASImportResult, error)
	GetByFileHash(hash string) (*BASImportResult, error)
}
