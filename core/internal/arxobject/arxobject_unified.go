// Package arxobject provides the updated ArxObject with unified confidence system
package arxobject

import (
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/arxos/arxos/core/internal/confidence"
	arxpath "github.com/arxos/arxos/core/internal/path"
)

// ArxObjectUnified is the updated ArxObject using unified systems
type ArxObjectUnified struct {
	// Core Identity
	ID           string        `json:"id"`
	Type         ArxObjectType `json:"type"`
	Name         string        `json:"name"`
	Description  string        `json:"description,omitempty"`
	
	// Unified Path System
	Path         arxpath.ArxPath `json:"path"`  // Unix-style path
	
	// Hierarchy (derived from path)
	BuildingID   string        `json:"building_id"`
	FloorID      string        `json:"floor_id,omitempty"`
	ZoneID       string        `json:"zone_id,omitempty"`
	ParentID     string        `json:"parent_id,omitempty"`
	
	// Spatial
	Geometry     Geometry      `json:"geometry"`
	
	// Properties
	Properties   Properties    `json:"properties"`
	Material     string        `json:"material,omitempty"`
	Color        string        `json:"color,omitempty"`
	
	// Relationships
	Relationships []Relationship `json:"relationships,omitempty"`
	
	// Unified Confidence System (Single Source of Truth)
	Confidence   *confidence.Confidence `json:"confidence"`
	
	// Validation
	ValidationStatus ValidationStatus    `json:"validation_status"`
	Validations      []ValidationRecord  `json:"validations,omitempty"`
	
	// Source & Versioning
	SourceType   string        `json:"source_type"`      // "pdf", "ifc", "lidar", etc.
	SourceFile   string        `json:"source_file,omitempty"`
	SourcePage   int           `json:"source_page,omitempty"`
	Version      int           `json:"version"`
	
	// Timestamps
	CreatedAt    time.Time     `json:"created_at"`
	UpdatedAt    time.Time     `json:"updated_at"`
	ValidatedAt  *time.Time    `json:"validated_at,omitempty"`
	
	// Metadata
	Tags         []string      `json:"tags,omitempty"`
	Flags        uint32        `json:"flags,omitempty"`
	Hash         string        `json:"hash,omitempty"`
	
	// Synchronization
	mu           sync.RWMutex  `json:"-"`
}

// NewArxObjectUnified creates a new unified ArxObject
func NewArxObjectUnified(objType ArxObjectType, name string, path string) *ArxObjectUnified {
	now := time.Now()
	
	// Normalize path
	normalizedPath := arxpath.Normalize(path)
	
	return &ArxObjectUnified{
		ID:               uuid.New().String(),
		Type:             objType,
		Name:             name,
		Path:             normalizedPath,
		Properties:       make(Properties),
		Relationships:    []Relationship{},
		Confidence:       confidence.NewConfidence(),
		Validations:      []ValidationRecord{},
		ValidationStatus: ValidationPending,
		Version:          1,
		CreatedAt:        now,
		UpdatedAt:        now,
	}
}

// GetPath returns the unified Unix-style path
func (obj *ArxObjectUnified) GetPath() string {
	obj.mu.RLock()
	defer obj.mu.RUnlock()
	return obj.Path.String()
}

// SetPath updates the path using the unified system
func (obj *ArxObjectUnified) SetPath(newPath string) {
	obj.mu.Lock()
	defer obj.mu.Unlock()
	
	obj.Path = arxpath.Normalize(newPath)
	obj.UpdatedAt = time.Now()
	
	// Update derived hierarchy fields
	obj.updateHierarchyFromPath()
}

// updateHierarchyFromPath updates hierarchy fields based on path
func (obj *ArxObjectUnified) updateHierarchyFromPath() {
	segments := obj.Path.Split()
	
	for i, segment := range segments {
		if i == 0 {
			// First segment is usually the system type
			continue
		}
		
		// Look for hierarchy markers
		if i > 0 && segments[i-1] == "building" {
			obj.BuildingID = segment
		} else if i > 0 && segments[i-1] == "floor" {
			obj.FloorID = segment
		} else if i > 0 && segments[i-1] == "zone" {
			obj.ZoneID = segment
		}
	}
	
	// Set parent as the path parent
	if !obj.Path.IsRoot() {
		obj.ParentID = obj.Path.Parent().String()
	}
}

// UpdateConfidence updates the confidence using the unified system
func (obj *ArxObjectUnified) UpdateConfidence(source confidence.Source, params confidence.UpdateParams) {
	obj.mu.Lock()
	defer obj.mu.Unlock()
	
	if obj.Confidence == nil {
		obj.Confidence = confidence.NewConfidence()
	}
	
	obj.Confidence.Update(params)
	obj.UpdatedAt = time.Now()
}

// GetConfidenceScore returns the overall confidence score
func (obj *ArxObjectUnified) GetConfidenceScore() float64 {
	obj.mu.RLock()
	defer obj.mu.RUnlock()
	
	if obj.Confidence == nil {
		return 0.5 // Default neutral confidence
	}
	
	return obj.Confidence.GetOverall()
}

// GetConfidenceLevel returns a human-readable confidence level
func (obj *ArxObjectUnified) GetConfidenceLevel() string {
	obj.mu.RLock()
	defer obj.mu.RUnlock()
	
	if obj.Confidence == nil {
		return "Unknown"
	}
	
	return obj.Confidence.ConfidenceLevel()
}

// NeedsValidation checks if the object needs validation
func (obj *ArxObjectUnified) NeedsValidation() bool {
	obj.mu.RLock()
	defer obj.mu.RUnlock()
	
	if obj.Confidence == nil {
		return true
	}
	
	return obj.Confidence.NeedsValidation()
}

// AddValidation adds a validation record and updates confidence
func (obj *ArxObjectUnified) AddValidation(record ValidationRecord) {
	obj.mu.Lock()
	defer obj.mu.Unlock()
	
	// Add to validation history
	obj.Validations = append(obj.Validations, record)
	
	// Update confidence based on validation
	source := confidence.Source{
		Type:        confidence.SourceValidation,
		Method:      record.Method,
		Confidence:  record.Confidence,
		Timestamp:   record.Timestamp,
		ValidatorID: record.ValidatedBy,
	}
	
	params := confidence.UpdateParams{
		Source: source,
		Reason: fmt.Sprintf("Validation by %s using %s", record.ValidatedBy, record.Method),
	}
	
	// Update confidence components based on validation method
	switch record.Method {
	case "lidar":
		pos := 0.95
		params.Position = &pos
		props := 0.90
		params.Properties = &props
	case "photo":
		class := 0.80
		params.Classification = &class
		props := 0.70
		params.Properties = &props
	case "manual":
		props := record.Confidence
		params.Properties = &props
	}
	
	if obj.Confidence == nil {
		obj.Confidence = confidence.NewConfidence()
	}
	obj.Confidence.Update(params)
	
	// Update validation status
	if obj.Confidence.GetOverall() > 0.7 {
		obj.ValidationStatus = ValidationValidated
		now := time.Now()
		obj.ValidatedAt = &now
	} else if obj.Confidence.GetOverall() > 0.5 {
		obj.ValidationStatus = ValidationPartial
	}
	
	obj.UpdatedAt = time.Now()
}

// Clone creates a deep copy of the ArxObject
func (obj *ArxObjectUnified) Clone() *ArxObjectUnified {
	obj.mu.RLock()
	defer obj.mu.RUnlock()
	
	clone := &ArxObjectUnified{
		ID:              obj.ID + "_clone",
		Type:            obj.Type,
		Name:            obj.Name,
		Description:     obj.Description,
		Path:            obj.Path,
		BuildingID:      obj.BuildingID,
		FloorID:         obj.FloorID,
		ZoneID:          obj.ZoneID,
		ParentID:        obj.ParentID,
		Geometry:        obj.Geometry,
		Material:        obj.Material,
		Color:           obj.Color,
		ValidationStatus: obj.ValidationStatus,
		SourceType:      obj.SourceType,
		SourceFile:      obj.SourceFile,
		SourcePage:      obj.SourcePage,
		Version:         obj.Version,
		CreatedAt:       obj.CreatedAt,
		UpdatedAt:       time.Now(),
	}
	
	// Clone properties
	clone.Properties = make(Properties)
	for k, v := range obj.Properties {
		clone.Properties[k] = v
	}
	
	// Clone relationships
	clone.Relationships = make([]Relationship, len(obj.Relationships))
	copy(clone.Relationships, obj.Relationships)
	
	// Clone confidence
	if obj.Confidence != nil {
		clone.Confidence = obj.Confidence.Clone()
	}
	
	// Clone validations
	clone.Validations = make([]ValidationRecord, len(obj.Validations))
	copy(clone.Validations, obj.Validations)
	
	// Clone tags
	clone.Tags = make([]string, len(obj.Tags))
	copy(clone.Tags, obj.Tags)
	
	return clone
}

// ToJSON serializes the ArxObject to JSON
func (obj *ArxObjectUnified) ToJSON() ([]byte, error) {
	obj.mu.RLock()
	defer obj.mu.RUnlock()
	return json.Marshal(obj)
}

// FromJSON deserializes an ArxObject from JSON
func FromJSON(data []byte) (*ArxObjectUnified, error) {
	obj := &ArxObjectUnified{
		Properties:    make(Properties),
		Relationships: []Relationship{},
		Validations:   []ValidationRecord{},
	}
	
	if err := json.Unmarshal(data, obj); err != nil {
		return nil, err
	}
	
	// Ensure confidence is initialized
	if obj.Confidence == nil {
		obj.Confidence = confidence.NewConfidence()
	}
	
	return obj, nil
}

// String returns a string representation of the ArxObject
func (obj *ArxObjectUnified) String() string {
	obj.mu.RLock()
	defer obj.mu.RUnlock()
	
	return fmt.Sprintf("ArxObject{ID:%s, Type:%s, Name:%s, Path:%s, Confidence:%s}",
		obj.ID, obj.Type, obj.Name, obj.Path, obj.Confidence.ConfidenceLevel())
}

// GetSystem returns the system type from the path
func (obj *ArxObjectUnified) GetSystem() string {
	obj.mu.RLock()
	defer obj.mu.RUnlock()
	return obj.Path.GetSystem()
}

// IsInSystem checks if the object belongs to a specific system
func (obj *ArxObjectUnified) IsInSystem(system string) bool {
	return obj.GetSystem() == system
}

// GetParentPath returns the parent path
func (obj *ArxObjectUnified) GetParentPath() string {
	obj.mu.RLock()
	defer obj.mu.RUnlock()
	return obj.Path.Parent().String()
}

// IsChildOf checks if this object is a child of another path
func (obj *ArxObjectUnified) IsChildOf(parentPath string) bool {
	obj.mu.RLock()
	defer obj.mu.RUnlock()
	
	parent := arxpath.Normalize(parentPath)
	return obj.Path.IsSubpathOf(parent)
}