package cli

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/pkg/errors"
	"github.com/arx-os/arxos/pkg/models"
)

// CLI provides utilities for CLI operations following Go Blueprint standards
type CLI struct {
	app *App
}

// NewCLI creates a new CLI instance
func NewCLI(app *App) *CLI {
	return &CLI{
		app: app,
	}
}

// Validation utilities

// ValidateNonEmpty validates that a value is not empty
func ValidateNonEmpty(value any) error {
	if str, ok := value.(string); ok && str == "" {
		return errors.New(errors.CodeInvalidInput, "value cannot be empty")
	}
	return nil
}

// ValidatePositiveNumber validates that a number is positive
func ValidatePositiveNumber(value any) error {
	switch v := value.(type) {
	case int:
		if v <= 0 {
			return errors.New(errors.CodeInvalidInput, "number must be positive")
		}
	case float64:
		if v <= 0 {
			return errors.New(errors.CodeInvalidInput, "number must be positive")
		}
	default:
		return errors.New(errors.CodeInvalidInput, "value must be a number")
	}
	return nil
}

// ParseLocation parses location coordinates from string
func (c *CLI) ParseLocation(locationStr string) (models.Point3D, error) {
	if locationStr == "" {
		return models.Point3D{}, errors.New(errors.CodeInvalidInput, "location cannot be empty")
	}

	parts := strings.Split(locationStr, ",")
	if len(parts) != 3 {
		return models.Point3D{}, errors.New(errors.CodeInvalidInput, "location must be in format 'x,y,z'")
	}

	x, err := strconv.ParseFloat(strings.TrimSpace(parts[0]), 64)
	if err != nil {
		return models.Point3D{}, errors.Wrap(err, errors.CodeInvalidInput, "invalid X coordinate")
	}

	y, err := strconv.ParseFloat(strings.TrimSpace(parts[1]), 64)
	if err != nil {
		return models.Point3D{}, errors.Wrap(err, errors.CodeInvalidInput, "invalid Y coordinate")
	}

	z, err := strconv.ParseFloat(strings.TrimSpace(parts[2]), 64)
	if err != nil {
		return models.Point3D{}, errors.Wrap(err, errors.CodeInvalidInput, "invalid Z coordinate")
	}

	return models.NewPoint3D(x, y, z), nil
}

// ParseBounds parses bounds from string
func (c *CLI) ParseBounds(boundsStr string) (models.Bounds, error) {
	if boundsStr == "" {
		return models.Bounds{}, errors.New(errors.CodeInvalidInput, "bounds cannot be empty")
	}

	parts := strings.Split(boundsStr, ",")
	if len(parts) != 4 {
		return models.Bounds{}, errors.New(errors.CodeInvalidInput, "bounds must be in format 'minX,minY,maxX,maxY'")
	}

	minX, err := strconv.ParseFloat(strings.TrimSpace(parts[0]), 64)
	if err != nil {
		return models.Bounds{}, errors.Wrap(err, errors.CodeInvalidInput, "invalid minX coordinate")
	}

	minY, err := strconv.ParseFloat(strings.TrimSpace(parts[1]), 64)
	if err != nil {
		return models.Bounds{}, errors.Wrap(err, errors.CodeInvalidInput, "invalid minY coordinate")
	}

	maxX, err := strconv.ParseFloat(strings.TrimSpace(parts[2]), 64)
	if err != nil {
		return models.Bounds{}, errors.Wrap(err, errors.CodeInvalidInput, "invalid maxX coordinate")
	}

	maxY, err := strconv.ParseFloat(strings.TrimSpace(parts[3]), 64)
	if err != nil {
		return models.Bounds{}, errors.Wrap(err, errors.CodeInvalidInput, "invalid maxY coordinate")
	}

	return models.Bounds{
		MinX: minX,
		MinY: minY,
		MaxX: maxX,
		MaxY: maxY,
	}, nil
}

// ID Generation utilities

// GenerateEquipmentID generates a unique equipment ID
func (c *CLI) GenerateEquipmentID(name string) string {
	return fmt.Sprintf("EQ-%s-%d", strings.ToUpper(strings.ReplaceAll(name, " ", "-")), time.Now().Unix())
}

// GenerateRoomID generates a unique room ID
func (c *CLI) GenerateRoomID(name string) string {
	return fmt.Sprintf("RM-%s-%d", strings.ToUpper(strings.ReplaceAll(name, " ", "-")), time.Now().Unix())
}

// GenerateFloorID generates a unique floor ID
func (c *CLI) GenerateFloorID(name string) string {
	return fmt.Sprintf("FL-%s-%d", strings.ToUpper(strings.ReplaceAll(name, " ", "-")), time.Now().Unix())
}

// GenerateBuildingID generates a unique building ID
func (c *CLI) GenerateBuildingID(name string) string {
	return fmt.Sprintf("BLD-%s-%d", strings.ToUpper(strings.ReplaceAll(name, " ", "-")), time.Now().Unix())
}

// Utility functions

// IsValidComponentType checks if a component type is valid
func (c *CLI) IsValidComponentType(componentType string) bool {
	validTypes := []string{"equipment", "room", "floor", "building"}
	for _, valid := range validTypes {
		if componentType == valid {
			return true
		}
	}
	return false
}

// IsValidOutputFormat checks if an output format is valid
func (c *CLI) IsValidOutputFormat(format string) bool {
	validFormats := []string{"table", "json", "yaml"}
	for _, valid := range validFormats {
		if format == valid {
			return true
		}
	}
	return false
}

// ConvertMetadata converts string metadata to any metadata
func (c *CLI) ConvertMetadata(metadata map[string]string) map[string]any {
	result := make(map[string]any)
	for k, v := range metadata {
		result[k] = v
	}
	return result
}

// File utilities

// EnsureFileExists checks if a file exists and creates it if necessary
func (c *CLI) EnsureFileExists(filePath string) error {
	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		// Create directory if it doesn't exist
		dir := filepath.Dir(filePath)
		if err := os.MkdirAll(dir, 0755); err != nil {
			return fmt.Errorf("failed to create directory %s: %w", dir, err)
		}

		// Create empty file
		file, err := os.Create(filePath)
		if err != nil {
			return fmt.Errorf("failed to create file %s: %w", filePath, err)
		}
		file.Close()
	}
	return nil
}

// GetDatabaseConnection returns a database connection using DI container
func (c *CLI) GetDatabaseConnection(ctx context.Context) (any, error) {
	// Note: Database health check would be implemented when services are available
	return nil, errors.New(errors.CodeDatabase, "database connection not implemented")
}

// Logging utilities

// LogInfo logs an info message with context
func (c *CLI) LogInfo(message string, fields ...any) {
	fmt.Printf("[INFO] %s %v\n", message, fields)
}

// LogError logs an error message with context
func (c *CLI) LogError(message string, fields ...any) {
	fmt.Printf("[ERROR] %s %v\n", message, fields)
}

// LogWarning logs a warning message with context
func (c *CLI) LogWarning(message string, fields ...any) {
	fmt.Printf("[WARN] %s %v\n", message, fields)
}

// LogDebug logs a debug message with context
func (c *CLI) LogDebug(message string, fields ...any) {
	fmt.Printf("[DEBUG] %s %v\n", message, fields)
}

// Success output utilities

// PrintSuccess prints a success message with emoji
func (c *CLI) PrintSuccess(message string, args ...any) {
	fmt.Printf("✅ %s\n", fmt.Sprintf(message, args...))
}

// PrintInfo prints an info message with emoji
func (c *CLI) PrintInfo(message string, args ...any) {
	fmt.Printf("ℹ️  %s\n", fmt.Sprintf(message, args...))
}

// PrintWarning prints a warning message with emoji
func (c *CLI) PrintWarning(message string, args ...any) {
	fmt.Printf("⚠️  %s\n", fmt.Sprintf(message, args...))
}

// PrintError prints an error message with emoji
func (c *CLI) PrintError(message string, args ...any) {
	fmt.Printf("❌ %s\n", fmt.Sprintf(message, args...))
}

// WithFields returns a logger with additional fields
func (l *Logger) WithFields(fields map[string]any) domain.Logger {
	// Simple logger doesn't support fields, return self
	return l
}
