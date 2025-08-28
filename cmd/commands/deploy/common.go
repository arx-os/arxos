package deploy

import (
	"fmt"
	"github.com/jmoiron/sqlx"
	"github.com/arxos/arxos/cmd/config"
	_ "github.com/lib/pq" // PostgreSQL driver
)

// getStatusIcon returns an icon/emoji for deployment status
func getStatusIcon(status string) string {
	icons := map[string]string{
		"draft":       "📝",
		"pending":     "⏳",
		"in_progress": "🔄",
		"completed":   "✅",
		"failed":      "❌",
		"rolled_back": "↩️",
		"scheduled":   "📅",
		"cancelled":   "🚫",
	}
	
	if icon, ok := icons[status]; ok {
		return icon
	}
	return "•"
}

// getDB returns a database connection using the configured connection string
func getDB() (*sqlx.DB, error) {
	cfg := config.GetConfig()
	if cfg == nil {
		// Fallback to environment variable or default
		connStr := "postgres://arxos:arxos_secure_password@localhost:5432/arxos?sslmode=disable"
		return sqlx.Connect("postgres", connStr)
	}
	return sqlx.Connect("postgres", cfg.DatabaseURL)
}

// DeploymentStatus constants
const (
	StatusDraft      = "draft"
	StatusPending    = "pending"
	StatusInProgress = "in_progress"
	StatusCompleted  = "completed"
	StatusFailed     = "failed"
	StatusRolledBack = "rolled_back"
	StatusScheduled  = "scheduled"
	StatusCancelled  = "cancelled"
)

// DeploymentStrategy constants
const (
	StrategyImmediate = "immediate"
	StrategyCanary    = "canary"
	StrategyRolling   = "rolling"
	StrategyBlueGreen = "blue_green"
)

// formatDuration formats a duration in milliseconds to human-readable format
func formatDuration(ms int) string {
	if ms < 1000 {
		return fmt.Sprintf("%dms", ms)
	}
	seconds := ms / 1000
	if seconds < 60 {
		return fmt.Sprintf("%ds", seconds)
	}
	minutes := seconds / 60
	seconds = seconds % 60
	if minutes < 60 {
		return fmt.Sprintf("%dm%ds", minutes, seconds)
	}
	hours := minutes / 60
	minutes = minutes % 60
	return fmt.Sprintf("%dh%dm", hours, minutes)
}

// validateDeploymentID checks if a deployment ID is valid
func validateDeploymentID(id string) error {
	if id == "" {
		return fmt.Errorf("deployment ID cannot be empty")
	}
	if len(id) < 3 {
		return fmt.Errorf("invalid deployment ID format")
	}
	return nil
}