package models

import (
	"time"
)

// Schedule represents a construction project schedule
type Schedule struct {
	ID          string    `json:"id" gorm:"primaryKey"`
	ProjectID   string    `json:"project_id" gorm:"not null"`
	Name        string    `json:"name" gorm:"not null"`
	Description string    `json:"description"`
	StartDate   time.Time `json:"start_date" gorm:"not null"`
	EndDate     time.Time `json:"end_date" gorm:"not null"`
	Status      string    `json:"status" gorm:"default:'draft'"` // draft, active, completed, on-hold
	CreatedAt   time.Time `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt   time.Time `json:"updated_at" gorm:"autoUpdateTime"`

	// Relationships
	Tasks []Task `json:"tasks,omitempty" gorm:"foreignKey:ScheduleID"`
}

// Task represents a task in the construction schedule
type Task struct {
	ID          string    `json:"id" gorm:"primaryKey"`
	ScheduleID  string    `json:"schedule_id" gorm:"not null"`
	Name        string    `json:"name" gorm:"not null"`
	Description string    `json:"description"`
	StartDate   time.Time `json:"start_date" gorm:"not null"`
	EndDate     time.Time `json:"end_date" gorm:"not null"`
	Duration    int       `json:"duration" gorm:"not null"`            // Duration in days
	Progress    float64   `json:"progress" gorm:"default:0"`           // Progress percentage (0-100)
	Status      string    `json:"status" gorm:"default:'not-started'"` // not-started, in-progress, completed, delayed
	Priority    string    `json:"priority" gorm:"default:'medium'"`    // low, medium, high, critical
	AssignedTo  string    `json:"assigned_to"`                         // User ID
	CreatedAt   time.Time `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt   time.Time `json:"updated_at" gorm:"autoUpdateTime"`

	// Dependencies
	Dependencies []TaskDependency `json:"dependencies,omitempty" gorm:"foreignKey:TaskID"`
}

// TaskDependency represents dependencies between tasks
type TaskDependency struct {
	ID          string `json:"id" gorm:"primaryKey"`
	TaskID      string `json:"task_id" gorm:"not null"`
	DependentID string `json:"dependent_id" gorm:"not null"`          // ID of the task this depends on
	Type        string `json:"type" gorm:"default:'finish-to-start'"` // finish-to-start, start-to-start, etc.
	Lag         int    `json:"lag" gorm:"default:0"`                  // Lag in days
}

// GanttChart represents a Gantt chart for a schedule
type GanttChart struct {
	ScheduleID    string      `json:"schedule_id"`
	Tasks         []GanttTask `json:"tasks"`
	CriticalPath  []string    `json:"critical_path"`
	TotalDuration int         `json:"total_duration"`
	StartDate     time.Time   `json:"start_date"`
	EndDate       time.Time   `json:"end_date"`
}

// GanttTask represents a task in the Gantt chart
type GanttTask struct {
	ID           string    `json:"id"`
	Name         string    `json:"name"`
	StartDate    time.Time `json:"start_date"`
	EndDate      time.Time `json:"end_date"`
	Duration     int       `json:"duration"`
	Progress     float64   `json:"progress"`
	Status       string    `json:"status"`
	Priority     string    `json:"priority"`
	AssignedTo   string    `json:"assigned_to"`
	Dependencies []string  `json:"dependencies"`
	IsCritical   bool      `json:"is_critical"`
}

// ScheduleCreateRequest represents the request to create a new schedule
type ScheduleCreateRequest struct {
	ProjectID   string    `json:"project_id" validate:"required"`
	Name        string    `json:"name" validate:"required"`
	Description string    `json:"description"`
	StartDate   time.Time `json:"start_date" validate:"required"`
	EndDate     time.Time `json:"end_date" validate:"required"`
}

// TaskCreateRequest represents the request to create a new task
type TaskCreateRequest struct {
	ScheduleID   string    `json:"schedule_id" validate:"required"`
	Name         string    `json:"name" validate:"required"`
	Description  string    `json:"description"`
	StartDate    time.Time `json:"start_date" validate:"required"`
	EndDate      time.Time `json:"end_date" validate:"required"`
	Duration     int       `json:"duration" validate:"required,min=1"`
	Priority     string    `json:"priority"`
	AssignedTo   string    `json:"assigned_to"`
	Dependencies []string  `json:"dependencies"`
}
