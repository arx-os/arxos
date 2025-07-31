package models

import (
	"time"
)

// SafetyIncident represents a safety incident
type SafetyIncident struct {
	ID           string     `json:"id" gorm:"primaryKey"`
	ProjectID    string     `json:"project_id" gorm:"not null"`
	Title        string     `json:"title" gorm:"not null"`
	Description  string     `json:"description"`
	Type         string     `json:"type" gorm:"not null"`         // injury, near-miss, property-damage, environmental, etc.
	Severity     string     `json:"severity" gorm:"not null"`     // low, medium, high, critical
	Status       string     `json:"status" gorm:"default:'open'"` // open, investigating, resolved, closed
	Location     string     `json:"location"`                     // Building area or zone
	ReportedBy   string     `json:"reported_by" gorm:"not null"`
	ReportedAt   time.Time  `json:"reported_at" gorm:"not null"`
	IncidentDate time.Time  `json:"incident_date" gorm:"not null"`
	ResolvedAt   *time.Time `json:"resolved_at"`
	CreatedAt    time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt    time.Time  `json:"updated_at" gorm:"autoUpdateTime"`

	// Relationships
	Photos   []SafetyIncidentPhoto   `json:"photos,omitempty" gorm:"foreignKey:IncidentID"`
	Comments []SafetyIncidentComment `json:"comments,omitempty" gorm:"foreignKey:IncidentID"`
	Actions  []SafetyAction          `json:"actions,omitempty" gorm:"foreignKey:IncidentID"`
}

// SafetyIncidentPhoto represents a photo of a safety incident
type SafetyIncidentPhoto struct {
	ID         string    `json:"id" gorm:"primaryKey"`
	IncidentID string    `json:"incident_id" gorm:"not null"`
	Caption    string    `json:"caption"`
	FilePath   string    `json:"file_path" gorm:"not null"`
	FileSize   int64     `json:"file_size"`
	TakenBy    string    `json:"taken_by" gorm:"not null"`
	TakenAt    time.Time `json:"taken_at" gorm:"autoCreateTime"`
}

// SafetyIncidentComment represents a comment on a safety incident
type SafetyIncidentComment struct {
	ID         string    `json:"id" gorm:"primaryKey"`
	IncidentID string    `json:"incident_id" gorm:"not null"`
	Comment    string    `json:"comment" gorm:"not null"`
	AuthorID   string    `json:"author_id" gorm:"not null"`
	CreatedAt  time.Time `json:"created_at" gorm:"autoCreateTime"`
}

// SafetyAction represents an action taken in response to a safety incident
type SafetyAction struct {
	ID          string     `json:"id" gorm:"primaryKey"`
	IncidentID  string     `json:"incident_id" gorm:"not null"`
	Title       string     `json:"title" gorm:"not null"`
	Description string     `json:"description"`
	Type        string     `json:"type" gorm:"not null"`            // corrective, preventive, training, etc.
	Status      string     `json:"status" gorm:"default:'pending'"` // pending, in-progress, completed
	AssignedTo  string     `json:"assigned_to" gorm:"not null"`
	DueDate     time.Time  `json:"due_date"`
	CompletedAt *time.Time `json:"completed_at"`
	CreatedAt   time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt   time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

// SafetyChecklist represents a safety checklist
type SafetyChecklist struct {
	ID            string     `json:"id" gorm:"primaryKey"`
	ProjectID     string     `json:"project_id" gorm:"not null"`
	Name          string     `json:"name" gorm:"not null"`
	Description   string     `json:"description"`
	Type          string     `json:"type" gorm:"not null"`            // daily, weekly, monthly, pre-task, etc.
	Status        string     `json:"status" gorm:"default:'pending'"` // pending, in-progress, completed
	AssignedTo    string     `json:"assigned_to" gorm:"not null"`
	ScheduledDate time.Time  `json:"scheduled_date"`
	CompletedAt   *time.Time `json:"completed_at"`
	CreatedAt     time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt     time.Time  `json:"updated_at" gorm:"autoUpdateTime"`

	// Relationships
	Items []SafetyChecklistItem `json:"items,omitempty" gorm:"foreignKey:ChecklistID"`
}

// SafetyChecklistItem represents an item in a safety checklist
type SafetyChecklistItem struct {
	ID          string    `json:"id" gorm:"primaryKey"`
	ChecklistID string    `json:"checklist_id" gorm:"not null"`
	Name        string    `json:"name" gorm:"not null"`
	Description string    `json:"description"`
	Requirement string    `json:"requirement"`                     // What needs to be checked
	Status      string    `json:"status" gorm:"default:'pending'"` // pending, pass, fail, n/a
	Notes       string    `json:"notes"`                           // Inspector notes
	Order       int       `json:"order" gorm:"not null"`
	CreatedAt   time.Time `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt   time.Time `json:"updated_at" gorm:"autoUpdateTime"`
}

// SafetyIncidentCreateRequest represents the request to create a new safety incident
type SafetyIncidentCreateRequest struct {
	ProjectID    string    `json:"project_id" validate:"required"`
	Title        string    `json:"title" validate:"required"`
	Description  string    `json:"description"`
	Type         string    `json:"type" validate:"required"`
	Severity     string    `json:"severity" validate:"required"`
	Location     string    `json:"location"`
	ReportedBy   string    `json:"reported_by" validate:"required"`
	IncidentDate time.Time `json:"incident_date" validate:"required"`
}

// SafetyIncidentUpdateRequest represents the request to update a safety incident
type SafetyIncidentUpdateRequest struct {
	Title       *string    `json:"title"`
	Description *string    `json:"description"`
	Type        *string    `json:"type"`
	Severity    *string    `json:"severity"`
	Status      *string    `json:"status"`
	Location    *string    `json:"location"`
	ResolvedAt  *time.Time `json:"resolved_at"`
}

// SafetyChecklistCreateRequest represents the request to create a new safety checklist
type SafetyChecklistCreateRequest struct {
	ProjectID     string    `json:"project_id" validate:"required"`
	Name          string    `json:"name" validate:"required"`
	Description   string    `json:"description"`
	Type          string    `json:"type" validate:"required"`
	AssignedTo    string    `json:"assigned_to" validate:"required"`
	ScheduledDate time.Time `json:"scheduled_date"`
}

// SafetyIncidentListResponse represents the response for listing safety incidents
type SafetyIncidentListResponse struct {
	Incidents []SafetyIncident `json:"incidents"`
	Total     int64            `json:"total"`
	Page      int              `json:"page"`
	Limit     int              `json:"limit"`
}
