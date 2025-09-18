// Package bim provides parsing and writing capabilities for the Building Information Model text format.
// It implements the BIM Specification v1.0 for human-readable building infrastructure data.
package bim

import (
	"fmt"
	"time"
)

// FileVersion represents the BIM format version
const CurrentVersion = "1.0.0"

// CoordinateSystem defines the coordinate reference system
type CoordinateSystem string

const (
	TopLeftOrigin    CoordinateSystem = "TOP_LEFT_ORIGIN"
	BottomLeftOrigin CoordinateSystem = "BOTTOM_LEFT_ORIGIN"
	CenterOrigin     CoordinateSystem = "CENTER_ORIGIN"
)

// UnitSystem defines the measurement units
type UnitSystem string

const (
	Feet   UnitSystem = "FEET"
	Meters UnitSystem = "METERS"
	Inches UnitSystem = "INCHES"
)

// EquipmentStatus represents the operational state of equipment
type EquipmentStatus string

const (
	StatusOperational EquipmentStatus = "OPERATIONAL"
	StatusWarning     EquipmentStatus = "WARNING"
	StatusFailed      EquipmentStatus = "FAILED"
	StatusUnknown     EquipmentStatus = "UNKNOWN"
	StatusMaintenance EquipmentStatus = "MAINTENANCE"
)

// Priority represents issue priority levels
type Priority string

const (
	PriorityCritical Priority = "CRITICAL"
	PriorityHigh     Priority = "HIGH"
	PriorityMedium   Priority = "MEDIUM"
	PriorityLow      Priority = "LOW"
)

// ConnectionType represents types of connections between equipment
type ConnectionType string

const (
	ConnectionPower    ConnectionType = "POWER"
	ConnectionNetwork  ConnectionType = "NETWORK"
	ConnectionPlumbing ConnectionType = "PLUMBING"
	ConnectionHVAC     ConnectionType = "HVAC"
	ConnectionLogical  ConnectionType = "LOGICAL"
)

// Building represents the complete building model
type Building struct {
	// Header information
	Name             string           `json:"name"`
	FileVersion      string           `json:"file_version"`
	Generated        time.Time        `json:"generated"`
	CoordinateSystem CoordinateSystem `json:"coordinate_system"`
	Units            UnitSystem       `json:"units"`

	// Building data
	Floors []Floor `json:"floors"`

	// Metadata
	Metadata Metadata `json:"metadata"`

	// Validation
	Validation Validation `json:"validation"`
}

// Floor represents a single floor in the building
type Floor struct {
	Level       int                             `json:"level"`
	Name        string                          `json:"name"`
	Dimensions  Dimensions                      `json:"dimensions"`
	GridScale   GridScale                       `json:"grid_scale"`
	Legend      map[rune]string                 `json:"legend"`
	Layout      []string                        `json:"layout"` // ASCII art lines
	Equipment   []Equipment                     `json:"equipment"`
	Connections map[ConnectionType][]Connection `json:"connections"`
	Issues      []Issue                         `json:"issues"`
}

// Dimensions represents floor dimensions
type Dimensions struct {
	Width  float64 `json:"width"`
	Height float64 `json:"height"`
}

// GridScale represents the ASCII grid scaling
type GridScale struct {
	Ratio       string `json:"ratio"`       // e.g., "1:10"
	Description string `json:"description"` // e.g., "1 char = 10 feet"
}

// Equipment represents a piece of equipment
type Equipment struct {
	ID           string            `json:"id"`
	Type         string            `json:"type"` // Hierarchical type (dot notation)
	Location     Location          `json:"location"`
	Status       EquipmentStatus   `json:"status"`
	Serial       string            `json:"serial,omitempty"`
	Model        string            `json:"model,omitempty"`
	Manufacturer string            `json:"manufacturer,omitempty"`
	Installed    *time.Time        `json:"installed,omitempty"`
	LastMaint    *time.Time        `json:"last_maint,omitempty"`
	NextMaint    *time.Time        `json:"next_maint,omitempty"`
	Power        string            `json:"power,omitempty"`
	Network      string            `json:"network,omitempty"`
	Notes        string            `json:"notes,omitempty"`
	AssignedTo   string            `json:"assigned_to,omitempty"`
	Ticket       string            `json:"ticket,omitempty"`
	Priority     Priority          `json:"priority,omitempty"`
	CustomFields map[string]string `json:"custom_fields,omitempty"`
}

// Location represents equipment location
type Location struct {
	X    float64 `json:"x"`
	Y    float64 `json:"y"`
	Room string  `json:"room"`
}

// Connection represents a connection between equipment
type Connection struct {
	From          string `json:"from"`          // Equipment ID
	To            string `json:"to"`            // Equipment ID
	Specification string `json:"specification"` // e.g., "120V/1PH/20A"
}

// Issue represents an equipment issue
type Issue struct {
	EquipmentID string   `json:"equipment_id"`
	Description string   `json:"description"`
	Priority    Priority `json:"priority"`
	Ticket      string   `json:"ticket,omitempty"`
}

// Metadata contains building metadata
type Metadata struct {
	CreatedBy    string   `json:"created_by"`
	Organization string   `json:"organization"`
	Tags         []string `json:"tags"`
	Notes        string   `json:"notes"`
}

// Validation contains file validation information
type Validation struct {
	Checksum        string    `json:"checksum"`
	EquipmentCount  int       `json:"equipment_count"`
	ConnectionCount int       `json:"connection_count"`
	LastModified    time.Time `json:"last_modified"`
	ModifiedBy      string    `json:"modified_by"`
}

// ParseError represents a parsing error with context
type ParseError struct {
	Line    int    `json:"line"`
	Column  int    `json:"column"`
	Message string `json:"message"`
	Context string `json:"context"` // Surrounding lines for context
}

func (e ParseError) Error() string {
	return fmt.Sprintf("parse error at line %d, column %d: %s", e.Line, e.Column, e.Message)
}

// ValidationError represents a validation error
type ValidationError struct {
	Field   string `json:"field"`
	Value   string `json:"value"`
	Message string `json:"message"`
}

func (e ValidationError) Error() string {
	return fmt.Sprintf("validation error in %s: %s (value: %s)", e.Field, e.Message, e.Value)
}
