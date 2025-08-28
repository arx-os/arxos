package state

import (
	"fmt"
	"github.com/jmoiron/sqlx"
	"github.com/arxos/arxos/cmd/config"
	_ "github.com/lib/pq" // PostgreSQL driver
)

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

// StateStatus constants
const (
	StatusActive    = "active"
	StatusArchived  = "archived"
	StatusDeleted   = "deleted"
	StatusDraft     = "draft"
	StatusPublished = "published"
)

// getStateIcon returns an icon for state status
func getStateIcon(status string) string {
	icons := map[string]string{
		"active":    "🟢",
		"archived":  "📦",
		"deleted":   "🗑️",
		"draft":     "📝",
		"published": "📚",
		"snapshot":  "📸",
		"branch":    "🌿",
		"tag":       "🏷️",
	}
	
	if icon, ok := icons[status]; ok {
		return icon
	}
	return "•"
}

// formatBytes formats bytes to human-readable format
func formatBytes(bytes int64) string {
	const unit = 1024
	if bytes < unit {
		return fmt.Sprintf("%d B", bytes)
	}
	div, exp := int64(unit), 0
	for n := bytes / unit; n >= unit; n /= unit {
		div *= unit
		exp++
	}
	return fmt.Sprintf("%.1f %cB", float64(bytes)/float64(div), "KMGTPE"[exp])
}

// validateBuildingID checks if a building ID is valid
func validateBuildingID(id string) error {
	if id == "" {
		return fmt.Errorf("building ID cannot be empty")
	}
	if len(id) < 3 {
		return fmt.Errorf("invalid building ID format")
	}
	return nil
}