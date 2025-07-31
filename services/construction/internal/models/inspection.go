package models

import (
	"time"
)

// Inspection represents a construction inspection
type Inspection struct {
	ID            string     `json:"id" gorm:"primaryKey"`
	ProjectID     string     `json:"project_id" gorm:"not null"`
	Name          string     `json:"name" gorm:"not null"`
	Description   string     `json:"description"`
	Type          string     `json:"type" gorm:"not null"`             // quality, safety, permit, final, etc.
	Status        string     `json:"status" gorm:"default:'pending'"`  // pending, in-progress, passed, failed, cancelled
	Priority      string     `json:"priority" gorm:"default:'medium'"` // low, medium, high, critical
	Location      string     `json:"location"`                         // Building area or zone
	InspectorID   string     `json:"inspector_id" gorm:"not null"`
	ScheduledDate time.Time  `json:"scheduled_date"`
	CompletedDate *time.Time `json:"completed_date"`
	CreatedAt     time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt     time.Time  `json:"updated_at" gorm:"autoUpdateTime"`

	// Relationships
	Items    []InspectionItem    `json:"items,omitempty" gorm:"foreignKey:InspectionID"`
	Photos   []InspectionPhoto   `json:"photos,omitempty" gorm:"foreignKey:InspectionID"`
	Comments []InspectionComment `json:"comments,omitempty" gorm:"foreignKey:InspectionID"`
}

// InspectionItem represents an item to be inspected
type InspectionItem struct {
	ID           string    `json:"id" gorm:"primaryKey"`
	InspectionID string    `json:"inspection_id" gorm:"not null"`
	Name         string    `json:"name" gorm:"not null"`
	Description  string    `json:"description"`
	Requirement  string    `json:"requirement"`                     // What needs to be checked
	Status       string    `json:"status" gorm:"default:'pending'"` // pending, pass, fail, n/a
	Notes        string    `json:"notes"`                           // Inspector notes
	CreatedAt    time.Time `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt    time.Time `json:"updated_at" gorm:"autoUpdateTime"`
}

// InspectionPhoto represents a photo taken during inspection
type InspectionPhoto struct {
	ID           string    `json:"id" gorm:"primaryKey"`
	InspectionID string    `json:"inspection_id" gorm:"not null"`
	ItemID       *string   `json:"item_id"` // Optional link to specific item
	Caption      string    `json:"caption"`
	FilePath     string    `json:"file_path" gorm:"not null"`
	FileSize     int64     `json:"file_size"`
	TakenBy      string    `json:"taken_by" gorm:"not null"`
	TakenAt      time.Time `json:"taken_at" gorm:"autoCreateTime"`
}

// InspectionComment represents a comment on an inspection
type InspectionComment struct {
	ID           string    `json:"id" gorm:"primaryKey"`
	InspectionID string    `json:"inspection_id" gorm:"not null"`
	ItemID       *string   `json:"item_id"` // Optional link to specific item
	Comment      string    `json:"comment" gorm:"not null"`
	AuthorID     string    `json:"author_id" gorm:"not null"`
	CreatedAt    time.Time `json:"created_at" gorm:"autoCreateTime"`
}

// InspectionTemplate represents a template for inspections
type InspectionTemplate struct {
	ID          string                   `json:"id" gorm:"primaryKey"`
	Name        string                   `json:"name" gorm:"not null"`
	Description string                   `json:"description"`
	Type        string                   `json:"type" gorm:"not null"`
	Category    string                   `json:"category" gorm:"not null"` // electrical, mechanical, structural, etc.
	Items       []InspectionTemplateItem `json:"items,omitempty" gorm:"foreignKey:TemplateID"`
	CreatedAt   time.Time                `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt   time.Time                `json:"updated_at" gorm:"autoUpdateTime"`
}

// InspectionTemplateItem represents an item in an inspection template
type InspectionTemplateItem struct {
	ID          string `json:"id" gorm:"primaryKey"`
	TemplateID  string `json:"template_id" gorm:"not null"`
	Name        string `json:"name" gorm:"not null"`
	Description string `json:"description"`
	Requirement string `json:"requirement"`
	Order       int    `json:"order" gorm:"not null"`
}

// InspectionCreateRequest represents the request to create a new inspection
type InspectionCreateRequest struct {
	ProjectID     string    `json:"project_id" validate:"required"`
	Name          string    `json:"name" validate:"required"`
	Description   string    `json:"description"`
	Type          string    `json:"type" validate:"required"`
	Priority      string    `json:"priority"`
	Location      string    `json:"location"`
	InspectorID   string    `json:"inspector_id" validate:"required"`
	ScheduledDate time.Time `json:"scheduled_date"`
	TemplateID    *string   `json:"template_id"` // Optional template to use
}

// InspectionUpdateRequest represents the request to update an inspection
type InspectionUpdateRequest struct {
	Name          *string    `json:"name"`
	Description   *string    `json:"description"`
	Type          *string    `json:"type"`
	Status        *string    `json:"status"`
	Priority      *string    `json:"priority"`
	Location      *string    `json:"location"`
	InspectorID   *string    `json:"inspector_id"`
	ScheduledDate *time.Time `json:"scheduled_date"`
	CompletedDate *time.Time `json:"completed_date"`
}

// InspectionListResponse represents the response for listing inspections
type InspectionListResponse struct {
	Inspections []Inspection `json:"inspections"`
	Total       int64        `json:"total"`
	Page        int          `json:"page"`
	Limit       int          `json:"limit"`
}
