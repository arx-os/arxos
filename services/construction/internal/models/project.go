package models

import (
	"time"
)

// Project represents a construction project
type Project struct {
	ID          string    `json:"id" gorm:"primaryKey"`
	Name        string    `json:"name" gorm:"not null"`
	Description string    `json:"description"`
	Location    string    `json:"location" gorm:"not null"`
	Type        string    `json:"type" gorm:"not null"` // Education, Healthcare, Commercial, etc.
	Client      string    `json:"client" gorm:"not null"`
	Status      string    `json:"status" gorm:"default:'active'"` // active, completed, on-hold, cancelled
	StartDate   time.Time `json:"start_date"`
	EndDate     time.Time `json:"end_date"`
	Budget      float64   `json:"budget"`
	CreatedAt   time.Time `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt   time.Time `json:"updated_at" gorm:"autoUpdateTime"`

	// Relationships
	Schedules       []Schedule       `json:"schedules,omitempty" gorm:"foreignKey:ProjectID"`
	Documents       []Document       `json:"documents,omitempty" gorm:"foreignKey:ProjectID"`
	Inspections     []Inspection     `json:"inspections,omitempty" gorm:"foreignKey:ProjectID"`
	SafetyIncidents []SafetyIncident `json:"safety_incidents,omitempty" gorm:"foreignKey:ProjectID"`
	Users           []ProjectUser    `json:"users,omitempty" gorm:"foreignKey:ProjectID"`
}

// ProjectUser represents user assignments to projects
type ProjectUser struct {
	ID        string    `json:"id" gorm:"primaryKey"`
	ProjectID string    `json:"project_id" gorm:"not null"`
	UserID    string    `json:"user_id" gorm:"not null"`
	Role      string    `json:"role" gorm:"not null"` // superintendent, foreman, contractor, etc.
	CreatedAt time.Time `json:"created_at" gorm:"autoCreateTime"`
}

// ProjectCreateRequest represents the request to create a new project
type ProjectCreateRequest struct {
	Name        string    `json:"name" validate:"required"`
	Description string    `json:"description"`
	Location    string    `json:"location" validate:"required"`
	Type        string    `json:"type" validate:"required"`
	Client      string    `json:"client" validate:"required"`
	StartDate   time.Time `json:"start_date"`
	EndDate     time.Time `json:"end_date"`
	Budget      float64   `json:"budget"`
}

// ProjectUpdateRequest represents the request to update a project
type ProjectUpdateRequest struct {
	Name        *string    `json:"name"`
	Description *string    `json:"description"`
	Location    *string    `json:"location"`
	Type        *string    `json:"type"`
	Client      *string    `json:"client"`
	Status      *string    `json:"status"`
	StartDate   *time.Time `json:"start_date"`
	EndDate     *time.Time `json:"end_date"`
	Budget      *float64   `json:"budget"`
}

// ProjectListResponse represents the response for listing projects
type ProjectListResponse struct {
	Projects []Project `json:"projects"`
	Total    int64     `json:"total"`
	Page     int       `json:"page"`
	Limit    int       `json:"limit"`
}
