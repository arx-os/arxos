// models/models.go
package models

import (
	"encoding/json"
	"fmt"
	"regexp"
	"time"

	"gorm.io/datatypes"
	"gorm.io/gorm"
)

var DB *gorm.DB

var idPattern = regexp.MustCompile(`^[A-Z0-9]{3,10}_L[0-9]{1,2}_(E|LV|FA|N|M|P)_[A-Z][a-zA-Z]+_[0-9]{3}$`)

func IsValidObjectId(id string) bool {
	return idPattern.MatchString(id)
}

// User represents a system user (Owner, Builder, or Guest).
type User struct {
	ID                   uint                   `gorm:"primaryKey" json:"id"`
	CreatedAt            time.Time              `json:"created_at"`
	UpdatedAt            time.Time              `json:"last_modified"`
	DeletedAt            gorm.DeletedAt         `gorm:"index" json:"-"`
	TenantID             string                 `gorm:"type:uuid" json:"tenant_id"`
	Email                string                 `gorm:"unique;not null" json:"email"`
	Username             string                 `gorm:"unique;not null" json:"username"`
	Password             string                 `json:"-"` // never expose in API responses
	Role                 string                 `gorm:"not null;default:'user'" json:"role"`
	FirstName            string                 `json:"first_name"`
	LastName             string                 `json:"last_name"`
	Phone                string                 `json:"phone"`
	AvatarURL            string                 `json:"avatar_url"`
	Status               string                 `gorm:"default:'active'" json:"status"`
	EmailVerified        bool                   `gorm:"default:false" json:"email_verified"`
	EmailVerifiedAt      *time.Time            `json:"email_verified_at"`
	LastLoginAt          *time.Time            `json:"last_login_at"`
	LoginCount           int                   `gorm:"default:0" json:"login_count"`
	FailedLoginAttempts  int                   `gorm:"default:0" json:"failed_login_attempts"`
	LockedUntil          *time.Time            `json:"locked_until"`
	Metadata             map[string]interface{} `gorm:"type:jsonb" json:"metadata"`
	Preferences          map[string]interface{} `gorm:"type:jsonb" json:"preferences"`
	Projects             []Project              `gorm:"constraint:OnDelete:CASCADE;" json:"projects"`
}

// Project represents a building or site under a user's account.
type Project struct {
	ID        uint           `gorm:"primaryKey" json:"id"`
	CreatedAt time.Time      `json:"created_at"`
	UpdatedAt time.Time      `json:"last_modified"`
	DeletedAt gorm.DeletedAt `gorm:"index" json:"-"`
	Name      string         `gorm:"not null" json:"name"`
	UserID    uint           `gorm:"index;not null" json:"user_id"`
	Drawings  []Drawing      `gorm:"constraint:OnDelete:CASCADE;" json:"drawings"`
}

// Drawing represents one SVG file associated with a specific project.
type Drawing struct {
	ID        uint           `gorm:"primaryKey" json:"id"`
	CreatedAt time.Time      `json:"created_at"`
	UpdatedAt time.Time      `json:"last_modified"`
	DeletedAt gorm.DeletedAt `gorm:"index" json:"-"`
	ProjectID uint           `gorm:"index;not null" json:"project_id"`
	Name      string         `gorm:"not null" json:"name"`
	SVG       string         `gorm:"type:text;not null" json:"svg"`
}

// Building represents a physical building managed in the system.
type Building struct {
	ID           uint           `gorm:"primaryKey" json:"id"`
	CreatedAt    time.Time      `json:"created_at"`
	UpdatedAt    time.Time      `json:"last_modified"`
	DeletedAt    gorm.DeletedAt `gorm:"index" json:"-"`
	Name         string         `gorm:"not null" json:"name"`
	Address      string         `json:"address"`
	City         string         `json:"city"`
	State        string         `json:"state"`
	ZipCode      string         `json:"zip_code"`
	BuildingType string         `json:"building_type"`
	Status       string         `gorm:"default:'active'" json:"status"`
	AccessLevel  string         `gorm:"default:'public'" json:"access_level"`
	OwnerID      uint           `gorm:"index;not null" json:"owner_id"`
	Floors       []Floor        `gorm:"constraint:OnDelete:CASCADE;" json:"floors"`
}

// Floor represents a floor (SVG) within a building.
type Floor struct {
	ID         uint           `gorm:"primaryKey" json:"id"`
	CreatedAt  time.Time      `json:"created_at"`
	UpdatedAt  time.Time      `json:"last_modified"`
	DeletedAt  gorm.DeletedAt `gorm:"index" json:"-"`
	BuildingID uint           `gorm:"index;not null" json:"building_id"`
	Name       string         `gorm:"not null" json:"name"`
	SVGPath    string         `json:"svg_path"`
}

// Markup represents a markup submission for a building/floor.
type Markup struct {
	ID         uint      `gorm:"primaryKey" json:"id"`
	BuildingID uint      `gorm:"index;not null" json:"building_id"`
	FloorID    uint      `gorm:"index;not null" json:"floor_id"`
	UserID     uint      `gorm:"index;not null" json:"user_id"`
	System     string    `json:"system"`
	Elements   string    `gorm:"type:text" json:"elements"` // JSON string for now
	CreatedAt  time.Time `json:"created_at"`
}

// Log represents a log entry for a building.
type Log struct {
	ID         uint      `gorm:"primaryKey" json:"id"`
	BuildingID uint      `gorm:"index;not null" json:"building_id"`
	UserID     uint      `gorm:"index;not null" json:"user_id"`
	Message    string    `gorm:"type:text" json:"message"`
	CreatedAt  time.Time `json:"created_at"`
}

// SVGObject represents an object parsed from an SVG (e.g., device, room, system).
type SVGObject struct {
	ID        uint           `gorm:"primaryKey" json:"id"`
	CreatedAt time.Time      `json:"created_at"`
	UpdatedAt time.Time      `json:"last_modified"`
	DeletedAt gorm.DeletedAt `gorm:"index" json:"-"`
	FloorID   uint           `gorm:"index;not null" json:"floor_id"`
	ObjectID  string         `gorm:"not null" json:"object_id"` // SVG element ID
	Type      string         `json:"type"`
	Label     string         `json:"label"`
	X         float64        `json:"x"`
	Y         float64        `json:"y"`
	Metadata  string         `gorm:"type:text" json:"metadata"`
}

// Comment represents a user comment linked to an SVGObject.
type Comment struct {
	ID          uint           `gorm:"primaryKey" json:"id"`
	CreatedAt   time.Time      `json:"created_at"`
	UpdatedAt   time.Time      `json:"last_modified"`
	DeletedAt   gorm.DeletedAt `gorm:"index" json:"-"`
	SVGObjectID uint           `gorm:"index;not null" json:"svg_object_id"`
	UserID      uint           `gorm:"index;not null" json:"user_id"`
	Content     string         `gorm:"type:text" json:"content"`
}

// --- BIM Core Types ---

type Point struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
}

type Geometry struct {
	Type     string  `json:"type"` // e.g., "LineString", "Polygon", "Point"
	Points   []Point `json:"points"`
	Rotation float64 `json:"rotation,omitempty"`
	Scale    float64 `json:"scale,omitempty"`
}

type Room struct {
	ID         string   `gorm:"primaryKey" json:"id"`
	Name       string   `json:"name"`
	Geometry   Geometry `gorm:"embedded;embeddedPrefix:geometry_" json:"geometry"`
	Devices    []Device `gorm:"foreignKey:RoomID" json:"devices"`
	Layer      string   `json:"layer,omitempty"`
	CreatedBy  uint     `json:"created_by"`
	Status     string   `json:"status,omitempty"`
	SourceSVG  string   `json:"source_svg,omitempty"`
	SVGID      string   `json:"svg_id,omitempty"`
	LockedBy   uint     `json:"locked_by,omitempty"`
	AssignedTo uint     `json:"assigned_to,omitempty"`
	Category   string   `json:"category"`
	ProjectID  uint     `json:"project_id"`
}

type Wall struct {
	ID         string   `gorm:"primaryKey" json:"id"`
	Name       string   `json:"name"`
	Geometry   Geometry `gorm:"embedded;embeddedPrefix:geometry_" json:"geometry"`
	Type       string   `json:"type,omitempty"`     // e.g., "exterior", "interior", "fire", "load-bearing"
	Material   string   `json:"material,omitempty"` // e.g., "concrete", "drywall", "brick"
	Thickness  float64  `json:"thickness,omitempty"`
	Height     float64  `json:"height,omitempty"`
	Layer      string   `json:"layer,omitempty"`
	CreatedBy  uint     `json:"created_by"`
	Status     string   `json:"status,omitempty"`
	SourceSVG  string   `json:"source_svg,omitempty"`
	SVGID      string   `json:"svg_id,omitempty"`
	LockedBy   uint     `json:"locked_by,omitempty"`
	AssignedTo uint     `json:"assigned_to,omitempty"`
	Category   string   `json:"category"`
	ProjectID  uint     `json:"project_id"`
	// Wall-specific metadata
	RoomID1    string `json:"room_id_1,omitempty"`   // First room this wall borders
	RoomID2    string `json:"room_id_2,omitempty"`   // Second room this wall borders
	FireRating string `json:"fire_rating,omitempty"` // e.g., "1-hour", "2-hour"
	Insulation string `json:"insulation,omitempty"`  // e.g., "R-13", "R-19"
}

type Device struct {
	ID         string   `gorm:"primaryKey" json:"id"`
	Type       string   `json:"type"`
	Geometry   Geometry `gorm:"embedded;embeddedPrefix:geometry_" json:"geometry"`
	System     string   `json:"system,omitempty"`
	Subtype    string   `json:"subtype,omitempty"`
	Layer      string   `json:"layer,omitempty"`
	RoomID     string   `gorm:"index" json:"room_id,omitempty"`
	CreatedBy  uint     `json:"created_by"`
	Status     string   `json:"status,omitempty"`
	SourceSVG  string   `json:"source_svg,omitempty"`
	SVGID      string   `json:"svg_id,omitempty"`
	LockedBy   uint     `json:"locked_by,omitempty"`
	AssignedTo uint     `json:"assigned_to,omitempty"`
	Category   string   `json:"category"`
	ProjectID  uint     `json:"project_id"`
	// Metadata links
	PanelID      string `json:"panel_id,omitempty"`
	CircuitID    string `json:"circuit_id,omitempty"`
	UpstreamID   string `json:"upstream_id,omitempty"`
	DownstreamID string `json:"downstream_id,omitempty"`
	PipeID       string `json:"pipe_id,omitempty"`
}

type Label struct {
	ID           string   `gorm:"primaryKey" json:"id"`
	Text         string   `json:"text"`
	Geometry     Geometry `gorm:"embedded;embeddedPrefix:geometry_" json:"geometry"`
	Layer        string   `json:"layer,omitempty"`
	CreatedBy    uint     `json:"created_by"`
	Status       string   `json:"status,omitempty"`
	SourceSVG    string   `json:"source_svg,omitempty"`
	SVGID        string   `json:"svg_id,omitempty"`
	LockedBy     uint     `json:"locked_by,omitempty"`
	AssignedTo   uint     `json:"assigned_to,omitempty"`
	RoomID       string   `gorm:"index" json:"room_id,omitempty"` // Optional: label-to-room relationship
	Category     string   `json:"category"`
	ProjectID    uint     `json:"project_id"`
	UpstreamID   string   `json:"upstream_id,omitempty"`
	DownstreamID string   `json:"downstream_id,omitempty"`
}

type Zone struct {
	ID           string   `gorm:"primaryKey" json:"id"`
	Name         string   `json:"name"`
	Geometry     Geometry `gorm:"embedded;embeddedPrefix:geometry_" json:"geometry"`
	Layer        string   `json:"layer,omitempty"`
	CreatedBy    uint     `json:"created_by"`
	Status       string   `json:"status,omitempty"`
	SourceSVG    string   `json:"source_svg,omitempty"`
	SVGID        string   `json:"svg_id,omitempty"`
	LockedBy     uint     `json:"locked_by,omitempty"`
	AssignedTo   uint     `json:"assigned_to,omitempty"`
	Category     string   `json:"category"`
	ProjectID    uint     `json:"project_id"`
	UpstreamID   string   `json:"upstream_id,omitempty"`
	DownstreamID string   `json:"downstream_id,omitempty"`
}

type BIMModel struct {
	Rooms   []Room   `json:"rooms"`
	Walls   []Wall   `json:"walls"`
	Devices []Device `json:"devices"`
	Labels  []Label  `json:"labels"`
	Zones   []Zone   `json:"zones"`
	Routes  []Route  `json:"routes"`
	Pins    []Pin    `json:"pins"`
	// Add more as needed
}

type Category struct {
	gorm.Model
	Name       string
	BuildingID uint // optional, if categories are building-specific
}

type UserCategoryPermission struct {
	gorm.Model
	UserID     uint
	CategoryID uint
	ProjectID  uint
	CanEdit    bool
}

func CanUserAccessCategory(db *gorm.DB, userID, categoryID uint, requireEdit bool) bool {
	var perm UserCategoryPermission
	err := db.Where("user_id = ? AND category_id = ?", userID, categoryID).First(&perm).Error
	if err != nil {
		return false
	}
	if requireEdit && !perm.CanEdit {
		return false
	}
	return true
}

type AuditLog struct {
	ID         uint `gorm:"primaryKey"`
	UserID     uint
	ObjectType string
	ObjectID   string
	Action     string
	Payload    datatypes.JSON
	CreatedAt  time.Time

	// Enhanced fields for detailed tracking
	IPAddress  string  `json:"ip_address,omitempty"`
	UserAgent  string  `json:"user_agent,omitempty"`
	SessionID  string  `json:"session_id,omitempty"`
	BuildingID *uint   `json:"building_id,omitempty"`
	FloorID    *uint   `json:"floor_id,omitempty"`
	AssetID    *string `json:"asset_id,omitempty"`
	ExportID   *uint   `json:"export_id,omitempty"`

	// Field-level change tracking
	FieldChanges datatypes.JSON `json:"field_changes,omitempty"` // {"field_name": {"before": "value", "after": "value"}}

	// Additional context
	Context datatypes.JSON `json:"context,omitempty"` // Additional metadata
}

func LogChange(db *gorm.DB, userID uint, objectType, objectID, action string, payload any) error {
	jsonPayload, _ := json.Marshal(payload)
	return db.Create(&AuditLog{
		UserID:     userID,
		ObjectType: objectType,
		ObjectID:   objectID,
		Action:     action,
		Payload:    datatypes.JSON(jsonPayload),
	}).Error
}

// LogAssetChange logs asset changes without HTTP request context
func LogAssetChange(db *gorm.DB, userID uint, assetID string, action string, before, after *BuildingAsset, r interface{}) error {
	payload := map[string]interface{}{
		"action":   action,
		"asset_id": assetID,
	}

	if before != nil {
		payload["before"] = before
	}
	if after != nil {
		payload["after"] = after
	}

	// Track field-level changes
	fieldChanges := make(map[string]map[string]interface{})
	if before != nil && after != nil {
		// Compare key fields for changes
		fieldsToTrack := []string{"AssetType", "System", "Subsystem", "Status", "EstimatedValue", "ReplacementCost"}
		for _, field := range fieldsToTrack {
			beforeVal := getFieldValue(before, field)
			afterVal := getFieldValue(after, field)
			if beforeVal != afterVal {
				fieldChanges[field] = map[string]interface{}{
					"before": beforeVal,
					"after":  afterVal,
				}
			}
		}
	}

	jsonPayload, _ := json.Marshal(payload)
	jsonFieldChanges, _ := json.Marshal(fieldChanges)

	var buildingID, floorID *uint
	if after != nil {
		buildingID = &after.BuildingID
		floorID = &after.FloorID
	}

	return db.Create(&AuditLog{
		UserID:       userID,
		ObjectType:   "asset",
		ObjectID:     assetID,
		Action:       action,
		Payload:      datatypes.JSON(jsonPayload),
		AssetID:      &assetID,
		BuildingID:   buildingID,
		FloorID:      floorID,
		FieldChanges: datatypes.JSON(jsonFieldChanges),
	}).Error
}

// LogExportChange logs export activities without HTTP request context
func LogExportChange(db *gorm.DB, userID uint, exportID uint, action string, payload map[string]interface{}, r interface{}) error {
	jsonPayload, _ := json.Marshal(payload)

	return db.Create(&AuditLog{
		UserID:     userID,
		ObjectType: "export",
		ObjectID:   fmt.Sprintf("%d", exportID),
		Action:     action,
		Payload:    datatypes.JSON(jsonPayload),
		ExportID:   &exportID,
	}).Error
}

// Helper function to get field value
func getFieldValue(asset *BuildingAsset, fieldName string) interface{} {
	switch fieldName {
	case "AssetType":
		return asset.AssetType
	case "System":
		return asset.System
	case "Subsystem":
		return asset.Subsystem
	case "Status":
		return asset.Status
	case "EstimatedValue":
		return asset.EstimatedValue
	case "ReplacementCost":
		return asset.ReplacementCost
	default:
		return nil
	}
}

type ChatMessage struct {
	ID         uint           `gorm:"primaryKey"`
	BuildingID uint           `gorm:"index"`
	UserID     uint           `gorm:"index"`
	Message    string         `gorm:"type:text"`
	AuditLogID *uint          `gorm:"index"` // nullable, references AuditLog
	References datatypes.JSON `json:"references,omitempty"`
	CreatedAt  time.Time
}

type CatalogItem struct {
	ID           uint   `gorm:"primaryKey"`
	Make         string `gorm:"index"`
	Model        string `gorm:"index"`
	SerialNumber string `gorm:"index"`
	CategoryID   uint   `gorm:"index"`
	Type         string `gorm:"index"`
	Specs        datatypes.JSON
	DatasheetURL string
	Approved     bool
	CreatedBy    uint `gorm:"index"`
	CreatedAt    time.Time
	UpdatedAt    time.Time
}

type Route struct {
	ID           string   `gorm:"primaryKey" json:"id"`
	ProjectID    uint     `json:"project_id"`
	FloorID      uint     `json:"floor_id"`
	System       string   `json:"system"`
	Label        string   `json:"label"`
	Circuit      string   `json:"circuit"`
	Geometry     Geometry `gorm:"embedded;embeddedPrefix:geometry_" json:"geometry"`
	CreatedBy    uint     `json:"created_by"`
	Status       string   `json:"status"`
	UpstreamID   string   `json:"upstream_id,omitempty"`
	DownstreamID string   `json:"downstream_id,omitempty"`
}

type Pin struct {
	ID        uint      `gorm:"primaryKey" json:"id"`
	ProjectID uint      `gorm:"index" json:"project_id"`
	FloorID   uint      `gorm:"index" json:"floor_id"`
	MessageID uint      `gorm:"index" json:"message_id"` // Associated chat message
	X         float64   `json:"x"`
	Y         float64   `json:"y"`
	CreatedBy uint      `json:"created_by"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"last_modified"`
}

// DrawingVersion stores a version of the SVG for a floor, for undo/redo/versioning
type DrawingVersion struct {
	ID            uint      `gorm:"primaryKey" json:"id"`
	FloorID       uint      `gorm:"index;not null" json:"floor_id"`
	SVG           string    `gorm:"type:text;not null" json:"svg"`
	VersionNumber int       `gorm:"not null" json:"version_number"`
	UserID        uint      `gorm:"index;not null" json:"user_id"`
	ActionType    string    `gorm:"type:varchar(32);not null" json:"action_type"`
	CreatedAt     time.Time `json:"created_at"`
}

// GenerateObjectId creates an object ID from building, floor, system, type, and instance number.
// TODO: In the future, auto-increment instance if not provided.
func GenerateObjectId(building, floor, system, objType string, instance int) string {
	// Example: TCHS_L2_E_Receptacle_015
	return fmt.Sprintf("%s_%s_%s_%s_%03d", building, floor, system, objType, instance)
}

// GetNextInstanceNumber returns the next available instance number for the given object context.
// TODO: Implement DB query to find the highest instance for building, floor, system, and type.
func GetNextInstanceNumber(building, floor, system, objType string) int {
	// Example stub: always return 1 for now
	return 1
}

// Validation helper for metadata links
func ValidateMetadataLinks(links map[string]string) (bool, []string) {
	var invalidFields []string
	for field, id := range links {
		if id != "" && !IsValidObjectId(id) {
			invalidFields = append(invalidFields, field)
		}
	}
	return len(invalidFields) == 0, invalidFields
}

// SymbolLibraryCache is used for caching symbol library responses
type SymbolLibraryCache struct {
	ID        uint      `json:"id" gorm:"primaryKey"`
	Query     string    `json:"query"`
	Category  string    `json:"category"`
	Response  string    `json:"response" gorm:"type:text"`
	CreatedAt time.Time `json:"created_at"`
	ExpiresAt time.Time `json:"expires_at"`
}

// SymbolPlacement represents a placed symbol in a markup
// Example JSON:
//
//	{
//	  "symbol_id": "ahu",
//	  "x": 100.0,
//	  "y": 200.0,
//	  "rotation": 0,
//	  "scale": 1.0,
//	  "metadata": { "label": "AHU-1" }
//	}
type SymbolPlacement struct {
	SymbolID string                 `json:"symbol_id"`
	X        float64                `json:"x"`
	Y        float64                `json:"y"`
	Rotation float64                `json:"rotation,omitempty"`
	Scale    float64                `json:"scale,omitempty"`
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// MarkupElements is the expected structure for the Elements field in Markup
// Example JSON:
//
//	{
//	  "symbols": [ SymbolPlacement, ... ]
//	}
type MarkupElements struct {
	Symbols []SymbolPlacement `json:"symbols"`
}

// BuildingAsset represents a detailed asset inventory item
type BuildingAsset struct {
	ID         string `gorm:"primaryKey" json:"id"`
	BuildingID uint   `gorm:"index;not null" json:"building_id"`
	FloorID    uint   `gorm:"index" json:"floor_id"`
	RoomID     string `gorm:"index" json:"room_id,omitempty"`
	SymbolID   string `gorm:"index;not null" json:"symbol_id"`
	AssetType  string `gorm:"index;not null" json:"asset_type"`
	System     string `gorm:"index;not null" json:"system"`
	Subsystem  string `json:"subsystem,omitempty"`

	// Location details
	Location AssetLocation `gorm:"embedded;embeddedPrefix:location_" json:"location"`

	// Specifications from YAML properties
	Specifications datatypes.JSON `json:"specifications"`

	// Metadata and notes
	Metadata datatypes.JSON `json:"metadata"`

	// Calculated fields
	Age              int    `json:"age,omitempty"` // years since installation
	EfficiencyRating string `json:"efficiency_rating,omitempty"`
	LifecycleStage   string `json:"lifecycle_stage,omitempty"`

	// Valuation
	EstimatedValue  float64 `json:"estimated_value,omitempty"`
	ReplacementCost float64 `json:"replacement_cost,omitempty"`

	// Status and tracking
	Status    string         `gorm:"default:'active'" json:"status"`
	CreatedBy uint           `gorm:"index;not null" json:"created_by"`
	CreatedAt time.Time      `json:"created_at"`
	UpdatedAt time.Time      `json:"updated_at"`
	DeletedAt gorm.DeletedAt `gorm:"index" json:"-"`

	// Relationships
	Building    Building           `json:"building,omitempty"`
	Floor       Floor              `json:"floor,omitempty"`
	History     []AssetHistory     `gorm:"foreignKey:AssetID" json:"history,omitempty"`
	Maintenance []AssetMaintenance `gorm:"foreignKey:AssetID" json:"maintenance,omitempty"`
	Valuations  []AssetValuation   `gorm:"foreignKey:AssetID" json:"valuations,omitempty"`
}

// AssetLocation represents the physical location of an asset
type AssetLocation struct {
	Floor       string  `json:"floor,omitempty"`
	Room        string  `json:"room,omitempty"`
	Area        string  `json:"area,omitempty"`
	X           float64 `json:"x,omitempty"`
	Y           float64 `json:"y,omitempty"`
	Coordinates string  `json:"coordinates,omitempty"` // "x,y" format
}

// AssetHistory tracks changes and events for an asset
type AssetHistory struct {
	ID          uint           `gorm:"primaryKey" json:"id"`
	AssetID     string         `gorm:"index;not null" json:"asset_id"`
	EventType   string         `gorm:"index;not null" json:"event_type"` // installation, replacement, repair, upgrade, etc.
	EventDate   time.Time      `json:"event_date"`
	Description string         `gorm:"type:text" json:"description"`
	Cost        float64        `json:"cost,omitempty"`
	Contractor  string         `json:"contractor,omitempty"`
	Warranty    string         `json:"warranty,omitempty"`
	Documents   datatypes.JSON `json:"documents,omitempty"` // URLs to related documents
	CreatedBy   uint           `gorm:"index;not null" json:"created_by"`
	CreatedAt   time.Time      `json:"created_at"`
}

// AssetMaintenance represents maintenance records and schedules
type AssetMaintenance struct {
	ID              uint           `gorm:"primaryKey" json:"id"`
	AssetID         string         `gorm:"index;not null" json:"asset_id"`
	MaintenanceType string         `gorm:"index;not null" json:"maintenance_type"` // preventive, corrective, emergency
	Status          string         `gorm:"index;not null" json:"status"`           // scheduled, in_progress, completed, overdue
	ScheduledDate   time.Time      `json:"scheduled_date"`
	CompletedDate   time.Time      `json:"completed_date,omitempty"`
	Description     string         `gorm:"type:text" json:"description"`
	Cost            float64        `json:"cost,omitempty"`
	Technician      string         `json:"technician,omitempty"`
	Parts           datatypes.JSON `json:"parts,omitempty"`
	Notes           string         `gorm:"type:text" json:"notes,omitempty"`
	CreatedBy       uint           `gorm:"index;not null" json:"created_by"`
	CreatedAt       time.Time      `json:"created_at"`
	UpdatedAt       time.Time      `json:"updated_at"`
}

// AssetValuation represents asset value tracking over time
type AssetValuation struct {
	ID              uint      `gorm:"primaryKey" json:"id"`
	AssetID         string    `gorm:"index;not null" json:"asset_id"`
	ValuationDate   time.Time `json:"valuation_date"`
	ValuationType   string    `gorm:"index;not null" json:"valuation_type"` // market, replacement, depreciated
	Value           float64   `json:"value"`
	Currency        string    `gorm:"default:'USD'" json:"currency"`
	ValuationMethod string    `json:"valuation_method,omitempty"`
	Notes           string    `gorm:"type:text" json:"notes,omitempty"`
	CreatedBy       uint      `gorm:"index;not null" json:"created_by"`
	CreatedAt       time.Time `json:"created_at"`
}

// BuildingAssetInventory represents a compiled inventory for a building
type BuildingAssetInventory struct {
	ID            uint           `gorm:"primaryKey" json:"id"`
	BuildingID    uint           `gorm:"index;not null" json:"building_id"`
	InventoryDate time.Time      `json:"inventory_date"`
	TotalAssets   int            `json:"total_assets"`
	Systems       datatypes.JSON `json:"systems"`       // Summary by system
	ExportFormat  string         `json:"export_format"` // csv, json, xml
	ExportData    datatypes.JSON `json:"export_data"`   // Compiled data
	CreatedBy     uint           `gorm:"index;not null" json:"created_by"`
	CreatedAt     time.Time      `json:"created_at"`
}

// IndustryBenchmark represents industry standards for equipment
type IndustryBenchmark struct {
	ID            uint      `gorm:"primaryKey" json:"id"`
	EquipmentType string    `gorm:"index;not null" json:"equipment_type"`
	System        string    `gorm:"index;not null" json:"system"`
	Metric        string    `gorm:"index;not null" json:"metric"` // efficiency, lifespan, cost_per_unit, etc.
	Value         float64   `json:"value"`
	Unit          string    `json:"unit"`
	Source        string    `json:"source"` // ASHRAE, IEEE, etc.
	Year          int       `json:"year"`
	Description   string    `gorm:"type:text" json:"description"`
	CreatedAt     time.Time `json:"created_at"`
}

// DataVendorAPIKey represents an API key for data vendor access
type DataVendorAPIKey struct {
	ID          uint      `gorm:"primaryKey" json:"id"`
	Key         string    `gorm:"uniqueIndex;not null" json:"key"`
	VendorName  string    `gorm:"not null" json:"vendor_name"`
	Email       string    `gorm:"not null" json:"email"`
	AccessLevel string    `gorm:"default:'basic'" json:"access_level"` // basic, premium, enterprise
	RateLimit   int       `gorm:"default:1000" json:"rate_limit"`      // requests per hour
	IsActive    bool      `gorm:"default:true" json:"is_active"`
	ExpiresAt   time.Time `json:"expires_at"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

// DataVendorRequest represents a data request from a vendor
type DataVendorRequest struct {
	ID          uint      `gorm:"primaryKey" json:"id"`
	APIKeyID    uint      `gorm:"index;not null" json:"api_key_id"`
	RequestType string    `gorm:"not null" json:"request_type"` // building_inventory, asset_details, etc.
	BuildingID  uint      `gorm:"index" json:"building_id"`
	Format      string    `gorm:"default:'json'" json:"format"`
	Filters     string    `gorm:"type:text" json:"filters"`
	IPAddress   string    `json:"ip_address"`
	UserAgent   string    `json:"user_agent"`
	Status      string    `gorm:"default:'completed'" json:"status"`
	CreatedAt   time.Time `json:"created_at"`
}

// Maintenance Workflow Models
type MaintenanceTask struct {
	ID             int        `json:"id" db:"id"`
	AssetID        int        `json:"asset_id" db:"asset_id"`
	ScheduleID     *int       `json:"schedule_id" db:"schedule_id"` // Optional link to maintenance schedule
	TaskType       string     `json:"task_type" db:"task_type"`     // preventive, corrective, emergency, inspection
	Status         string     `json:"status" db:"status"`           // pending, in_progress, completed, cancelled, overdue
	Priority       string     `json:"priority" db:"priority"`       // low, medium, high, critical
	Title          string     `json:"title" db:"title"`
	Description    string     `json:"description" db:"description"`
	Instructions   string     `json:"instructions" db:"instructions"`
	AssignedTo     string     `json:"assigned_to" db:"assigned_to"`
	EstimatedHours float64    `json:"estimated_hours" db:"estimated_hours"`
	ActualHours    float64    `json:"actual_hours" db:"actual_hours"`
	EstimatedCost  float64    `json:"estimated_cost" db:"estimated_cost"`
	ActualCost     float64    `json:"actual_cost" db:"actual_cost"`
	PartsUsed      string     `json:"parts_used" db:"parts_used"` // JSON array
	Notes          string     `json:"notes" db:"notes"`
	ScheduledDate  time.Time  `json:"scheduled_date" db:"scheduled_date"`
	StartedDate    *time.Time `json:"started_date" db:"started_date"`
	CompletedDate  *time.Time `json:"completed_date" db:"completed_date"`
	DueDate        time.Time  `json:"due_date" db:"due_date"`
	CreatedAt      time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt      time.Time  `json:"updated_at" db:"updated_at"`
}

type AssetLifecycle struct {
	ID              int        `json:"id" db:"id"`
	AssetID         int        `json:"asset_id" db:"asset_id"`
	InstallDate     time.Time  `json:"install_date" db:"install_date"`
	ExpectedLife    int        `json:"expected_life" db:"expected_life"` // in months
	EndOfLifeDate   time.Time  `json:"end_of_life_date" db:"end_of_life_date"`
	ReplacementDate *time.Time `json:"replacement_date" db:"replacement_date"`
	Status          string     `json:"status" db:"status"`         // active, maintenance, replacement_planned, end_of_life, retired
	Condition       string     `json:"condition" db:"condition"`   // excellent, good, fair, poor, critical
	RiskLevel       string     `json:"risk_level" db:"risk_level"` // low, medium, high, critical
	Notes           string     `json:"notes" db:"notes"`
	CreatedAt       time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt       time.Time  `json:"updated_at" db:"updated_at"`
}

type Warranty struct {
	ID             int       `json:"id" db:"id"`
	AssetID        int       `json:"asset_id" db:"asset_id"`
	WarrantyType   string    `json:"warranty_type" db:"warranty_type"` // manufacturer, extended, service
	Provider       string    `json:"provider" db:"provider"`
	ContractNumber string    `json:"contract_number" db:"contract_number"`
	StartDate      time.Time `json:"start_date" db:"start_date"`
	EndDate        time.Time `json:"end_date" db:"end_date"`
	Coverage       string    `json:"coverage" db:"coverage"`         // parts, labor, both
	Terms          string    `json:"terms" db:"terms"`               // JSON terms and conditions
	ContactInfo    string    `json:"contact_info" db:"contact_info"` // JSON contact details
	IsActive       bool      `json:"is_active" db:"is_active"`
	CreatedAt      time.Time `json:"created_at" db:"created_at"`
	UpdatedAt      time.Time `json:"updated_at" db:"updated_at"`
}

type ReplacementPlan struct {
	ID                 int        `json:"id" db:"id"`
	AssetID            int        `json:"asset_id" db:"asset_id"`
	PlanType           string     `json:"plan_type" db:"plan_type"` // scheduled, emergency, upgrade
	Reason             string     `json:"reason" db:"reason"`
	Priority           string     `json:"priority" db:"priority"` // low, medium, high, critical
	EstimatedCost      float64    `json:"estimated_cost" db:"estimated_cost"`
	BudgetedAmount     float64    `json:"budgeted_amount" db:"budgeted_amount"`
	PlannedDate        time.Time  `json:"planned_date" db:"planned_date"`
	ActualDate         *time.Time `json:"actual_date" db:"actual_date"`
	Status             string     `json:"status" db:"status"` // planned, approved, in_progress, completed, cancelled
	ReplacementAssetID *int       `json:"replacement_asset_id" db:"replacement_asset_id"`
	Notes              string     `json:"notes" db:"notes"`
	CreatedAt          time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt          time.Time  `json:"updated_at" db:"updated_at"`
}

type MaintenanceCost struct {
	ID            int       `json:"id" db:"id"`
	AssetID       int       `json:"asset_id" db:"asset_id"`
	TaskID        *int      `json:"task_id" db:"task_id"`
	CostType      string    `json:"cost_type" db:"cost_type"` // labor, parts, materials, external
	Description   string    `json:"description" db:"description"`
	Amount        float64   `json:"amount" db:"amount"`
	Currency      string    `json:"currency" db:"currency"` // USD, EUR, etc.
	Date          time.Time `json:"date" db:"date"`
	InvoiceNumber string    `json:"invoice_number" db:"invoice_number"`
	Vendor        string    `json:"vendor" db:"vendor"`
	ApprovedBy    string    `json:"approved_by" db:"approved_by"`
	CreatedAt     time.Time `json:"created_at" db:"created_at"`
	UpdatedAt     time.Time `json:"updated_at" db:"updated_at"`
}

type MaintenanceNotification struct {
	ID               int        `json:"id" db:"id"`
	AssetID          int        `json:"asset_id" db:"asset_id"`
	TaskID           *int       `json:"task_id" db:"task_id"`
	NotificationType string     `json:"notification_type" db:"notification_type"` // due_date, overdue, completion, warranty_expiry, eol
	Title            string     `json:"title" db:"title"`
	Message          string     `json:"message" db:"message"`
	Priority         string     `json:"priority" db:"priority"` // low, medium, high, critical
	IsRead           bool       `json:"is_read" db:"is_read"`
	ReadBy           string     `json:"read_by" db:"read_by"`
	ReadAt           *time.Time `json:"read_at" db:"read_at"`
	CreatedAt        time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt        time.Time  `json:"updated_at" db:"updated_at"`
}

// ExportActivity tracks all export requests and their completion status
type ExportActivity struct {
	ID             uint       `gorm:"primaryKey" json:"id"`
	UserID         uint       `gorm:"index;not null" json:"user_id"`
	BuildingID     uint       `gorm:"index" json:"building_id"`
	ExportType     string     `gorm:"index;not null" json:"export_type"` // asset_inventory, building_data, etc.
	Format         string     `gorm:"not null" json:"format"`            // csv, json, xml, pdf
	Filters        string     `gorm:"type:text" json:"filters"`          // JSON filters applied
	Status         string     `gorm:"index;not null" json:"status"`      // requested, processing, completed, failed
	FileSize       int64      `json:"file_size,omitempty"`               // in bytes
	DownloadCount  int        `gorm:"default:0" json:"download_count"`
	ProcessingTime int        `json:"processing_time,omitempty"` // in milliseconds
	ErrorMessage   string     `gorm:"type:text" json:"error_message,omitempty"`
	IPAddress      string     `json:"ip_address"`
	UserAgent      string     `json:"user_agent"`
	RequestedAt    time.Time  `json:"requested_at"`
	CompletedAt    *time.Time `json:"completed_at,omitempty"`
	ExpiresAt      *time.Time `json:"expires_at,omitempty"`
	CreatedAt      time.Time  `json:"created_at"`
	UpdatedAt      time.Time  `json:"updated_at"`

	// Relationships
	User     User     `json:"user,omitempty"`
	Building Building `json:"building,omitempty"`
}

// ExportAnalytics stores aggregated export statistics
type ExportAnalytics struct {
	ID                uint      `gorm:"primaryKey" json:"id"`
	Date              time.Time `gorm:"index;not null" json:"date"`
	Period            string    `gorm:"not null" json:"period"` // daily, weekly, monthly
	TotalExports      int       `json:"total_exports"`
	TotalDownloads    int       `json:"total_downloads"`
	TotalFileSize     int64     `json:"total_file_size"`
	AvgProcessingTime int       `json:"avg_processing_time"`

	// Format breakdown
	CSVCount  int `json:"csv_count"`
	JSONCount int `json:"json_count"`
	XMLCount  int `json:"xml_count"`
	PDFCount  int `json:"pdf_count"`

	// Export type breakdown
	AssetInventoryCount int `json:"asset_inventory_count"`
	BuildingDataCount   int `json:"building_data_count"`
	MaintenanceCount    int `json:"maintenance_count"`
	OtherCount          int `json:"other_count"`

	// User activity
	ActiveUsers    int  `json:"active_users"`
	TopUserID      uint `json:"top_user_id"`
	TopUserExports int  `json:"top_user_exports"`

	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

// DataVendorUsage tracks API usage by data vendors
type DataVendorUsage struct {
	ID             uint      `gorm:"primaryKey" json:"id"`
	APIKeyID       uint      `gorm:"index;not null" json:"api_key_id"`
	VendorName     string    `gorm:"index;not null" json:"vendor_name"`
	RequestType    string    `gorm:"index;not null" json:"request_type"`
	BuildingID     uint      `gorm:"index" json:"building_id"`
	Format         string    `gorm:"not null" json:"format"`
	FileSize       int64     `json:"file_size,omitempty"`
	ProcessingTime int       `json:"processing_time,omitempty"`
	Status         string    `gorm:"index;not null" json:"status"`
	ErrorCode      string    `json:"error_code,omitempty"`
	ErrorMessage   string    `gorm:"type:text" json:"error_message,omitempty"`
	IPAddress      string    `json:"ip_address"`
	UserAgent      string    `json:"user_agent"`
	RateLimitHit   bool      `gorm:"default:false" json:"rate_limit_hit"`
	CreatedAt      time.Time `json:"created_at"`

	// Relationships
	APIKey   DataVendorAPIKey `json:"api_key,omitempty"`
	Building Building         `json:"building,omitempty"`
}

// ExportDashboard provides real-time export statistics
type ExportDashboard struct {
	TodayExports      int               `json:"today_exports"`
	TodayDownloads    int               `json:"today_downloads"`
	TodayFileSize     int64             `json:"today_file_size"`
	WeekExports       int               `json:"week_exports"`
	WeekDownloads     int               `json:"week_downloads"`
	MonthExports      int               `json:"month_exports"`
	MonthDownloads    int               `json:"month_downloads"`
	ActiveExports     int               `json:"active_exports"`
	FailedExports     int               `json:"failed_exports"`
	AvgProcessingTime int               `json:"avg_processing_time"`
	TopFormats        map[string]int    `json:"top_formats"`
	TopExportTypes    map[string]int    `json:"top_export_types"`
	TopUsers          []UserExportStats `json:"top_users"`
	RecentExports     []ExportActivity  `json:"recent_exports"`
}

// UserExportStats for dashboard display
type UserExportStats struct {
	UserID        uint   `json:"user_id"`
	Username      string `json:"username"`
	ExportCount   int    `json:"export_count"`
	DownloadCount int    `json:"download_count"`
	TotalFileSize int64  `json:"total_file_size"`
}

// ========================
// COMPLIANCE MODELS
// ========================

// DataRetentionPolicy defines retention policies for different object types
type DataRetentionPolicy struct {
	ID              uint      `gorm:"primaryKey" json:"id"`
	ObjectType      string    `gorm:"index;not null" json:"object_type"`
	RetentionPeriod int       `gorm:"not null" json:"retention_period"` // in days
	ArchiveAfter    int       `gorm:"not null" json:"archive_after"`    // in days
	DeleteAfter     int       `gorm:"not null" json:"delete_after"`     // in days
	IsActive        bool      `gorm:"default:true" json:"is_active"`
	Description     string    `gorm:"type:text" json:"description"`
	CreatedAt       time.Time `json:"created_at"`
	UpdatedAt       time.Time `json:"updated_at"`
}

// ArchivedAuditLog stores archived audit logs for long-term retention
type ArchivedAuditLog struct {
	ID           uint           `gorm:"primaryKey" json:"id"`
	OriginalID   uint           `gorm:"not null" json:"original_id"`
	UserID       uint           `gorm:"index;not null" json:"user_id"`
	ObjectType   string         `gorm:"index;not null" json:"object_type"`
	ObjectID     string         `gorm:"index;not null" json:"object_id"`
	Action       string         `gorm:"not null" json:"action"`
	Payload      datatypes.JSON `json:"payload"`
	IPAddress    string         `json:"ip_address"`
	UserAgent    string         `gorm:"type:text" json:"user_agent"`
	SessionID    string         `json:"session_id"`
	BuildingID   *uint          `json:"building_id"`
	FloorID      *uint          `json:"floor_id"`
	AssetID      *string        `json:"asset_id"`
	ExportID     *uint          `json:"export_id"`
	FieldChanges datatypes.JSON `json:"field_changes"`
	Context      datatypes.JSON `json:"context"`
	CreatedAt    time.Time      `json:"created_at"`
	ArchivedAt   time.Time      `json:"archived_at"`
}

// ComplianceReport stores generated compliance reports
type ComplianceReport struct {
	ID           uint           `gorm:"primaryKey" json:"id"`
	ReportType   string         `gorm:"index;not null" json:"report_type"` // data_access, change_history, export_summary, retention_audit
	ReportName   string         `gorm:"not null" json:"report_name"`
	GeneratedBy  uint           `gorm:"index;not null" json:"generated_by"`
	Parameters   datatypes.JSON `json:"parameters"` // Report parameters and filters
	FilePath     string         `json:"file_path"`  // Path to generated report file
	FileSize     int64          `json:"file_size"`
	Format       string         `json:"format"`                             // csv, json, pdf, xlsx
	Status       string         `gorm:"default:'generating'" json:"status"` // generating, completed, failed
	ErrorMessage string         `gorm:"type:text" json:"error_message"`
	ExpiresAt    *time.Time     `json:"expires_at"`
	CreatedAt    time.Time      `json:"created_at"`
	CompletedAt  *time.Time     `json:"completed_at"`

	// Relationships
	User User `gorm:"foreignKey:GeneratedBy;references:ID" json:"user,omitempty"`
}

// DataAccessLog tracks detailed data access for auditors
type DataAccessLog struct {
	ID          uint      `gorm:"primaryKey" json:"id"`
	UserID      uint      `gorm:"index;not null" json:"user_id"`
	Action      string    `gorm:"index;not null" json:"action"` // view, export, modify, delete
	ObjectType  string    `gorm:"index;not null" json:"object_type"`
	ObjectID    string    `gorm:"index;not null" json:"object_id"`
	IPAddress   string    `json:"ip_address"`
	UserAgent   string    `gorm:"type:text" json:"user_agent"`
	SessionID   string    `json:"session_id"`
	BuildingID  *uint     `json:"building_id"`
	FloorID     *uint     `json:"floor_id"`
	AssetID     *string   `json:"asset_id"`
	ExportID    *uint     `json:"export_id"`
	AccessLevel string    `json:"access_level"` // basic, premium, enterprise, admin
	CreatedAt   time.Time `json:"created_at"`

	// Relationships
	User User `json:"user,omitempty"`
}

// SecurityAlert represents security-related alerts and incidents
type SecurityAlert struct {
	ID         uint           `gorm:"primaryKey" json:"id"`
	AlertType  string         `gorm:"index;not null" json:"alert_type"` // authentication_failure, rate_limit_exceeded, suspicious_activity, etc.
	Severity   string         `gorm:"index;not null" json:"severity"`   // low, medium, high, critical
	IPAddress  string         `gorm:"index" json:"ip_address"`
	UserAgent  string         `gorm:"type:text" json:"user_agent"`
	Path       string         `json:"path"`
	Method     string         `json:"method"`
	UserID     *uint          `gorm:"index" json:"user_id"`
	SessionID  string         `json:"session_id"`
	Details    datatypes.JSON `json:"details"` // Additional alert details
	IsResolved bool           `gorm:"default:false" json:"is_resolved"`
	ResolvedBy *uint          `gorm:"index" json:"resolved_by"`
	ResolvedAt *time.Time     `json:"resolved_at"`
	Notes      string         `gorm:"type:text" json:"notes"`
	CreatedAt  time.Time      `json:"created_at"`
	UpdatedAt  time.Time      `json:"updated_at"`

	// Relationships
	User           User `json:"user,omitempty"`
	ResolvedByUser User `gorm:"foreignKey:ResolvedBy" json:"resolved_by_user,omitempty"`
}

// APIKeyUsage represents detailed API key usage tracking
type APIKeyUsage struct {
	ID           uint      `gorm:"primaryKey" json:"id"`
	APIKeyID     uint      `gorm:"index;not null" json:"api_key_id"`
	Endpoint     string    `gorm:"index;not null" json:"endpoint"`
	Method       string    `gorm:"not null" json:"method"`
	Status       int       `gorm:"not null" json:"status"`
	ResponseTime int       `json:"response_time"` // in milliseconds
	RequestSize  int64     `json:"request_size"`  // in bytes
	ResponseSize int64     `json:"response_size"` // in bytes
	IPAddress    string    `gorm:"index" json:"ip_address"`
	UserAgent    string    `gorm:"type:text" json:"user_agent"`
	ErrorCode    string    `json:"error_code"`
	ErrorMessage string    `gorm:"type:text" json:"error_message"`
	RateLimitHit bool      `gorm:"default:false" json:"rate_limit_hit"`
	CreatedAt    time.Time `json:"created_at"`

	// Relationships
	APIKey DataVendorAPIKey `json:"api_key,omitempty"`
}

// Add archived field to existing AuditLog struct
func (al *AuditLog) AfterFind(tx *gorm.DB) error {
	// This ensures the archived field is always available
	return nil
}
