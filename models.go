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

// Project represents a building or site under a user’s account.
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
