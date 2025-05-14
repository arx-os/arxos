// models/models.go
package models

import (
	"time"

	"gorm.io/gorm"
)

// User represents a system user (Owner, Builder, or Guest).
type User struct {
	ID        uint           `gorm:"primaryKey" json:"id"`
	CreatedAt time.Time      `json:"created_at"`
	UpdatedAt time.Time      `json:"updated_at"`
	DeletedAt gorm.DeletedAt `gorm:"index" json:"-"`
	Email     string         `gorm:"uniqueIndex;not null" json:"email"`
	Password  string         `json:"-"` // never expose in API responses
	Projects  []Project      `gorm:"constraint:OnDelete:CASCADE;" json:"projects"`
}

// Project represents a building or site under a user's account.
type Project struct {
	ID        uint           `gorm:"primaryKey" json:"id"`
	CreatedAt time.Time      `json:"created_at"`
	UpdatedAt time.Time      `json:"updated_at"`
	DeletedAt gorm.DeletedAt `gorm:"index" json:"-"`
	Name      string         `gorm:"not null" json:"name"`
	UserID    uint           `gorm:"index;not null" json:"user_id"`
	Drawings  []Drawing      `gorm:"constraint:OnDelete:CASCADE;" json:"drawings"`
}

// Drawing represents one SVG file associated with a specific project.
type Drawing struct {
	ID        uint           `gorm:"primaryKey" json:"id"`
	CreatedAt time.Time      `json:"created_at"`
	UpdatedAt time.Time      `json:"updated_at"`
	DeletedAt gorm.DeletedAt `gorm:"index" json:"-"`
	ProjectID uint           `gorm:"index;not null" json:"project_id"`
	Name      string         `gorm:"not null" json:"name"`
	SVG       string         `gorm:"type:text;not null" json:"svg"`
}

// Building represents a physical building managed in the system.
type Building struct {
	ID        uint           `gorm:"primaryKey" json:"id"`
	CreatedAt time.Time      `json:"created_at"`
	UpdatedAt time.Time      `json:"updated_at"`
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
	UpdatedAt  time.Time      `json:"updated_at"`
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
