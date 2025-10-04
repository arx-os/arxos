package component

import (
	"fmt"
	"time"
)

// Component represents a universal building component
// This is the core domain model for any physical element in a building
type Component struct {
	ID         string                 `json:"id"`
	Name       string                 `json:"name"`
	Type       ComponentType          `json:"type"`
	Path       string                 `json:"path"`       // Universal path like /B1/3/CONF-301/HVAC/UNIT-01
	Location   Location               `json:"location"`   // Spatial coordinates
	Properties map[string]interface{} `json:"properties"` // Type-specific properties
	Relations  []Relation             `json:"relations"`  // Connections to other components
	Status     ComponentStatus        `json:"status"`
	Version    string                 `json:"version"`
	CreatedAt  time.Time              `json:"created_at"`
	UpdatedAt  time.Time              `json:"updated_at"`
	CreatedBy  string                 `json:"created_by"`
	UpdatedBy  string                 `json:"updated_by"`
}

// ComponentType represents the type of component
type ComponentType string

const (
	// HVAC Components
	ComponentTypeHVACUnit   ComponentType = "hvac_unit"
	ComponentTypeDamper     ComponentType = "damper"
	ComponentTypeThermostat ComponentType = "thermostat"
	ComponentTypeVent       ComponentType = "vent"

	// Electrical Components
	ComponentTypePanel  ComponentType = "electrical_panel"
	ComponentTypeOutlet ComponentType = "outlet"
	ComponentTypeSwitch ComponentType = "switch"
	ComponentTypeLight  ComponentType = "light"

	// Plumbing Components
	ComponentTypeFaucet ComponentType = "faucet"
	ComponentTypeToilet ComponentType = "toilet"
	ComponentTypePipe   ComponentType = "pipe"
	ComponentTypeValve  ComponentType = "valve"

	// Fire Safety Components
	ComponentTypeDetector  ComponentType = "fire_detector"
	ComponentTypeSprinkler ComponentType = "sprinkler"
	ComponentTypeAlarm     ComponentType = "fire_alarm"

	// Access Control Components
	ComponentTypeDoor       ComponentType = "door"
	ComponentTypeLock       ComponentType = "lock"
	ComponentTypeCardReader ComponentType = "card_reader"

	// Generic Components
	ComponentTypeGeneric   ComponentType = "generic"
	ComponentTypeFood      ComponentType = "food_item"
	ComponentTypeFurniture ComponentType = "furniture"
	ComponentTypeEquipment ComponentType = "equipment"
)

// ComponentStatus represents the operational status of a component
type ComponentStatus string

const (
	ComponentStatusActive      ComponentStatus = "active"
	ComponentStatusInactive    ComponentStatus = "inactive"
	ComponentStatusMaintenance ComponentStatus = "maintenance"
	ComponentStatusFailed      ComponentStatus = "failed"
	ComponentStatusUnknown     ComponentStatus = "unknown"
)

// Location represents spatial coordinates
type Location struct {
	X           float64 `json:"x"`
	Y           float64 `json:"y"`
	Z           float64 `json:"z"`
	Floor       string  `json:"floor"`
	Room        string  `json:"room"`
	Building    string  `json:"building"`
	Description string  `json:"description"`
}

// Relation represents a connection between components
type Relation struct {
	ID         string                 `json:"id"`
	Type       RelationType           `json:"type"`
	TargetID   string                 `json:"target_id"`
	TargetPath string                 `json:"target_path"`
	Properties map[string]interface{} `json:"properties"`
	CreatedAt  time.Time              `json:"created_at"`
}

// RelationType represents the type of relation between components
type RelationType string

const (
	RelationTypeConnected  RelationType = "connected"
	RelationTypeControlled RelationType = "controlled"
	RelationTypeSupplies   RelationType = "supplies"
	RelationTypeDependsOn  RelationType = "depends_on"
	RelationTypeContains   RelationType = "contains"
	RelationTypeAdjacent   RelationType = "adjacent"
)

// NewComponent creates a new Component instance
func NewComponent(name string, compType ComponentType, path string, location Location, createdBy string) (*Component, error) {
	if name == "" || path == "" || createdBy == "" {
		return nil, fmt.Errorf("component name, path, and creator cannot be empty")
	}

	now := time.Now()
	return &Component{
		ID:         fmt.Sprintf("comp-%d", now.UnixNano()),
		Name:       name,
		Type:       compType,
		Path:       path,
		Location:   location,
		Properties: make(map[string]interface{}),
		Relations:  []Relation{},
		Status:     ComponentStatusActive,
		Version:    "1.0.0",
		CreatedAt:  now,
		UpdatedAt:  now,
		CreatedBy:  createdBy,
		UpdatedBy:  createdBy,
	}, nil
}

// AddProperty adds a property to the component
func (c *Component) AddProperty(key string, value interface{}) {
	if c.Properties == nil {
		c.Properties = make(map[string]interface{})
	}
	c.Properties[key] = value
	c.UpdatedAt = time.Now()
}

// AddRelation adds a relation to another component
func (c *Component) AddRelation(relType RelationType, targetID, targetPath string, properties map[string]interface{}) {
	relation := Relation{
		ID:         fmt.Sprintf("rel-%d", time.Now().UnixNano()),
		Type:       relType,
		TargetID:   targetID,
		TargetPath: targetPath,
		Properties: properties,
		CreatedAt:  time.Now(),
	}
	c.Relations = append(c.Relations, relation)
	c.UpdatedAt = time.Now()
}

// UpdateStatus updates the component status
func (c *Component) UpdateStatus(status ComponentStatus, updatedBy string) {
	c.Status = status
	c.UpdatedBy = updatedBy
	c.UpdatedAt = time.Now()
}

// GetProperty retrieves a property value
func (c *Component) GetProperty(key string) (interface{}, bool) {
	if c.Properties == nil {
		return nil, false
	}
	value, exists := c.Properties[key]
	return value, exists
}

// GetStringProperty retrieves a property as a string
func (c *Component) GetStringProperty(key string) (string, bool) {
	value, exists := c.GetProperty(key)
	if !exists {
		return "", false
	}
	if str, ok := value.(string); ok {
		return str, true
	}
	return fmt.Sprintf("%v", value), true
}

// GetFloatProperty retrieves a property as a float64
func (c *Component) GetFloatProperty(key string) (float64, bool) {
	value, exists := c.GetProperty(key)
	if !exists {
		return 0, false
	}
	switch v := value.(type) {
	case float64:
		return v, true
	case int:
		return float64(v), true
	case int64:
		return float64(v), true
	default:
		return 0, false
	}
}

// GetBoolProperty retrieves a property as a boolean
func (c *Component) GetBoolProperty(key string) (bool, bool) {
	value, exists := c.GetProperty(key)
	if !exists {
		return false, false
	}
	if b, ok := value.(bool); ok {
		return b, true
	}
	return false, false
}
