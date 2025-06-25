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
	ID        uint           `gorm:"primaryKey" json:"id"`
	CreatedAt time.Time      `json:"created_at"`
	UpdatedAt time.Time      `json:"last_modified"`
	DeletedAt gorm.DeletedAt `gorm:"index" json:"-"`
	Email     string         `gorm:"uniqueIndex;not null" json:"email"`
	Username  string         `gorm:"uniqueIndex;not null" json:"username"`
	Password  string         `json:"-"` // never expose in API responses
	Role      string         `gorm:"not null;default:'user'" json:"role"`
	Projects  []Project      `gorm:"constraint:OnDelete:CASCADE;" json:"projects"`
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
	ID        uint           `gorm:"primaryKey" json:"id"`
	CreatedAt time.Time      `json:"created_at"`
	UpdatedAt time.Time      `json:"last_modified"`
	DeletedAt gorm.DeletedAt `gorm:"index" json:"-"`
	Name      string         `gorm:"not null" json:"name"`
	Address   string         `json:"address"`
	OwnerID   uint           `gorm:"index;not null" json:"owner_id"`
	Floors    []Floor        `gorm:"constraint:OnDelete:CASCADE;" json:"floors"`
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
