package commands

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// ArxObjectManager provides advanced ArxObject management capabilities
type ArxObjectManager struct {
	BuildingID string
	ObjectsDir string
	IndexPath  string
}

// NewArxObjectManager creates a new ArxObject manager for a building
func NewArxObjectManager(buildingID string) *ArxObjectManager {
	basePath := getBuildingPath(buildingID)
	return &ArxObjectManager{
		BuildingID: buildingID,
		ObjectsDir: filepath.Join(basePath, ".arxos", "objects"),
		IndexPath:  filepath.Join(basePath, ".arxos", "objects", "index.json"),
	}
}

// ArxObjectMetadata represents enhanced metadata for ArxObjects
type ArxObjectMetadata struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	Description string                 `json:"description,omitempty"`
	Properties  map[string]interface{} `json:"properties,omitempty"`
	Location    *Location              `json:"location,omitempty"`
	Parent      string                 `json:"parent,omitempty"`
	Children    []string               `json:"children,omitempty"`
	Status      string                 `json:"status"`
	Created     time.Time              `json:"created"`
	Updated     time.Time              `json:"updated"`

	// Advanced metadata
	ValidationStatus string                 `json:"validation_status,omitempty"`
	Confidence       float64                `json:"confidence,omitempty"`
	Tags             []string               `json:"tags,omitempty"`
	Flags            uint32                 `json:"flags,omitempty"`
	Hash             string                 `json:"hash,omitempty"`
	Version          int                    `json:"version,omitempty"`
	SourceType       string                 `json:"source_type,omitempty"`
	SourceFile       string                 `json:"source_file,omitempty"`
	SourcePage       int                    `json:"source_page,omitempty"`
	ValidatedAt      *time.Time             `json:"validated_at,omitempty"`
	Relationships    []RelationshipMetadata `json:"relationships,omitempty"`
	Validations      []ValidationMetadata   `json:"validations,omitempty"`
}

// RelationshipMetadata represents relationships between ArxObjects
type RelationshipMetadata struct {
	ID         string                 `json:"id"`
	Type       string                 `json:"type"`
	TargetID   string                 `json:"target_id"`
	SourceID   string                 `json:"source_id"`
	Properties map[string]interface{} `json:"properties,omitempty"`
	Confidence float64                `json:"confidence"`
	CreatedAt  time.Time              `json:"created_at"`
	Direction  string                 `json:"direction,omitempty"` // "incoming", "outgoing", "bidirectional"
}

// ValidationMetadata represents validation records for ArxObjects
type ValidationMetadata struct {
	ID          string                 `json:"id"`
	Timestamp   time.Time              `json:"timestamp"`
	ValidatedBy string                 `json:"validated_by"`
	Method      string                 `json:"method"`
	Evidence    map[string]interface{} `json:"evidence,omitempty"`
	Confidence  float64                `json:"confidence"`
	Notes       string                 `json:"notes,omitempty"`
	Status      string                 `json:"status"` // "pending", "approved", "rejected"
}

// ArxObjectLifecycle represents the lifecycle state of an ArxObject
type ArxObjectLifecycle struct {
	ID          string     `json:"id"`
	Status      string     `json:"status"`
	Phase       string     `json:"phase"`
	Created     time.Time  `json:"created"`
	Updated     time.Time  `json:"updated"`
	Activated   *time.Time `json:"activated,omitempty"`
	Deactivated *time.Time `json:"deactivated,omitempty"`
	Retired     *time.Time `json:"retired,omitempty"`
	Notes       string     `json:"notes,omitempty"`
}

// LoadArxObject loads an ArxObject from the filesystem
func (m *ArxObjectManager) LoadArxObject(objectID string) (*ArxObjectMetadata, error) {
	// Try to load from individual object file first
	objectPath := filepath.Join(m.ObjectsDir, fmt.Sprintf("%s.json", objectID))
	if data, err := os.ReadFile(objectPath); err == nil {
		var obj ArxObjectMetadata
		if err := json.Unmarshal(data, &obj); err != nil {
			return nil, fmt.Errorf("failed to unmarshal ArxObject %s: %w", objectID, err)
		}
		return &obj, nil
	}

	// Fall back to index lookup
	index, err := m.LoadIndex()
	if err != nil {
		return nil, fmt.Errorf("failed to load index: %w", err)
	}

	// Search by ID in the index
	for _, objList := range index.ByType {
		for _, id := range objList {
			if id == objectID {
				// Found in index, try to load from type-specific file
				return m.loadArxObjectByType(id, index)
			}
		}
	}

	return nil, fmt.Errorf("ArxObject %s not found", objectID)
}

// loadArxObjectByType loads an ArxObject based on its type
func (m *ArxObjectManager) loadArxObjectByType(objectID string, index *ArxObjectIndex) (*ArxObjectMetadata, error) {
	// Determine object type from ID
	var objType string
	if strings.Contains(objectID, ":floor:") {
		objType = "floor"
	} else if strings.Contains(objectID, ":system:") {
		objType = "system"
	} else if strings.HasPrefix(objectID, "building:") {
		objType = "building"
	} else {
		objType = "unknown"
	}

	// Try to load from type-specific file
	var filePath string
	switch objType {
	case "building":
		filePath = filepath.Join(m.ObjectsDir, "building.json")
	case "floor":
		floorNum := strings.Split(objectID, ":")[2]
		filePath = filepath.Join(m.ObjectsDir, fmt.Sprintf("floor_%s.json", floorNum))
	case "system":
		systemType := strings.Split(objectID, ":")[2]
		filePath = filepath.Join(m.ObjectsDir, fmt.Sprintf("system_%s.json", systemType))
	default:
		return nil, fmt.Errorf("unknown object type for %s", objectID)
	}

	if data, err := os.ReadFile(filePath); err != nil {
		return nil, fmt.Errorf("failed to read ArxObject file %s: %w", filePath, err)
	} else {
		var obj ArxObjectMetadata
		if err := json.Unmarshal(data, &obj); err != nil {
			return nil, fmt.Errorf("failed to unmarshal ArxObject from %s: %w", filePath, err)
		}
		return &obj, nil
	}
}

// SaveArxObject saves an ArxObject to the filesystem
func (m *ArxObjectManager) SaveArxObject(obj *ArxObjectMetadata) error {
	// Ensure objects directory exists
	if err := os.MkdirAll(m.ObjectsDir, 0755); err != nil {
		return fmt.Errorf("failed to create objects directory: %w", err)
	}

	// Update timestamp
	obj.Updated = time.Now().UTC()

	// Save individual object file
	objectPath := filepath.Join(m.ObjectsDir, fmt.Sprintf("%s.json", obj.ID))
	if err := writeJSON(objectPath, obj); err != nil {
		return fmt.Errorf("failed to save ArxObject %s: %w", obj.ID, err)
	}

	// Update index
	if err := m.updateIndex(obj); err != nil {
		return fmt.Errorf("failed to update index: %w", err)
	}

	return nil
}

// updateIndex updates the ArxObject index with a new/modified object
func (m *ArxObjectManager) updateIndex(obj *ArxObjectMetadata) error {
	index, err := m.LoadIndex()
	if err != nil {
		// Create new index if it doesn't exist
		index = &ArxObjectIndex{
			BuildingID: m.BuildingID,
			TotalCount: 0,
			ByType:     make(map[string][]string),
			ByLocation: make(map[string][]string),
			Hierarchy:  make(map[string][]string),
			Created:    time.Now().UTC(),
			Updated:    time.Now().UTC(),
		}
	}

	// Update type index
	if index.ByType[obj.Type] == nil {
		index.ByType[obj.Type] = []string{}
	}

	// Check if object already exists in type index
	found := false
	for _, id := range index.ByType[obj.Type] {
		if id == obj.ID {
			found = true
			break
		}
	}

	if !found {
		index.ByType[obj.Type] = append(index.ByType[obj.Type], obj.ID)
	}

	// Update location index
	if obj.Location != nil {
		locationKey := fmt.Sprintf("floor_%d", obj.Location.Floor)
		if index.ByLocation[locationKey] == nil {
			index.ByLocation[locationKey] = []string{}
		}

		// Check if object already exists in location index
		found = false
		for _, id := range index.ByLocation[locationKey] {
			if id == obj.ID {
				found = true
				break
			}
		}

		if !found {
			index.ByLocation[locationKey] = append(index.ByLocation[locationKey], obj.ID)
		}
	}

	// Update hierarchy index
	if obj.Parent != "" {
		if index.Hierarchy[obj.Parent] == nil {
			index.Hierarchy[obj.Parent] = []string{}
		}

		// Check if object already exists in hierarchy
		found = false
		for _, id := range index.Hierarchy[obj.Parent] {
			if id == obj.ID {
				found = true
				break
			}
		}

		if !found {
			index.Hierarchy[obj.Parent] = append(index.Hierarchy[obj.Parent], obj.ID)
		}
	}

	// Update total count
	index.TotalCount = len(index.ByType)
	index.Updated = time.Now().UTC()

	// Save updated index
	return writeJSON(m.IndexPath, index)
}

// LoadIndex loads the ArxObject index from the filesystem
func (m *ArxObjectManager) LoadIndex() (*ArxObjectIndex, error) {
	if data, err := os.ReadFile(m.IndexPath); err != nil {
		return nil, fmt.Errorf("failed to read index file: %w", err)
	} else {
		var index ArxObjectIndex
		if err := json.Unmarshal(data, &index); err != nil {
			return nil, fmt.Errorf("failed to unmarshal index: %w", err)
		}
		return &index, nil
	}
}

// GetAllArxObjects returns all ArxObjects in the building
func (m *ArxObjectManager) GetAllArxObjects() ([]*ArxObjectMetadata, error) {
	index, err := m.LoadIndex()
	if err != nil {
		return nil, fmt.Errorf("failed to load index: %w", err)
	}

	var objects []*ArxObjectMetadata
	for _, objList := range index.ByType {
		for _, objID := range objList {
			if obj, err := m.LoadArxObject(objID); err == nil {
				objects = append(objects, obj)
			}
		}
	}

	return objects, nil
}

// GetArxObjectsByType returns ArxObjects of a specific type
func (m *ArxObjectManager) GetArxObjectsByType(objType string) ([]*ArxObjectMetadata, error) {
	index, err := m.LoadIndex()
	if err != nil {
		return nil, fmt.Errorf("failed to load index: %w", err)
	}

	var objects []*ArxObjectMetadata
	if objList, exists := index.ByType[objType]; exists {
		for _, objID := range objList {
			if obj, err := m.LoadArxObject(objID); err == nil {
				objects = append(objects, obj)
			}
		}
	}

	return objects, nil
}

// GetArxObjectsByLocation returns ArxObjects at a specific location
func (m *ArxObjectManager) GetArxObjectsByLocation(floor int) ([]*ArxObjectMetadata, error) {
	index, err := m.LoadIndex()
	if err != nil {
		return nil, fmt.Errorf("failed to load index: %w", err)
	}

	locationKey := fmt.Sprintf("floor_%d", floor)
	var objects []*ArxObjectMetadata
	if objList, exists := index.ByLocation[locationKey]; exists {
		for _, objID := range objList {
			if obj, err := m.LoadArxObject(objID); err == nil {
				objects = append(objects, obj)
			}
		}
	}

	return objects, nil
}

// GetArxObjectChildren returns all children of an ArxObject
func (m *ArxObjectManager) GetArxObjectChildren(parentID string) ([]*ArxObjectMetadata, error) {
	index, err := m.LoadIndex()
	if err != nil {
		return nil, fmt.Errorf("failed to load index: %w", err)
	}

	var children []*ArxObjectMetadata
	if childList, exists := index.Hierarchy[parentID]; exists {
		for _, childID := range childList {
			if child, err := m.LoadArxObject(childID); err == nil {
				children = append(children, child)
			}
		}
	}

	return children, nil
}

// AddRelationship adds a relationship between two ArxObjects
func (m *ArxObjectManager) AddRelationship(sourceID, targetID, relType string, confidence float64, properties map[string]interface{}) error {
	// Load source object
	sourceObj, err := m.LoadArxObject(sourceID)
	if err != nil {
		return fmt.Errorf("failed to load source ArxObject %s: %w", sourceID, err)
	}

	// Load target object
	targetObj, err := m.LoadArxObject(targetID)
	if err != nil {
		return fmt.Errorf("failed to load target ArxObject %s: %w", targetID, err)
	}

	// Create relationship
	relationship := RelationshipMetadata{
		ID:         fmt.Sprintf("rel_%s_%s_%s", sourceID, relType, targetID),
		Type:       relType,
		TargetID:   targetID,
		SourceID:   sourceID,
		Properties: properties,
		Confidence: confidence,
		CreatedAt:  time.Now().UTC(),
		Direction:  "outgoing",
	}

	// Add to source object
	if sourceObj.Relationships == nil {
		sourceObj.Relationships = []RelationshipMetadata{}
	}
	sourceObj.Relationships = append(sourceObj.Relationships, relationship)

	// Create reverse relationship for target object
	reverseRel := RelationshipMetadata{
		ID:         fmt.Sprintf("rel_%s_%s_%s", targetID, relType, sourceID),
		Type:       relType,
		TargetID:   sourceID,
		SourceID:   targetID,
		Properties: properties,
		Confidence: confidence,
		CreatedAt:  time.Now().UTC(),
		Direction:  "incoming",
	}

	if targetObj.Relationships == nil {
		targetObj.Relationships = []RelationshipMetadata{}
	}
	targetObj.Relationships = append(targetObj.Relationships, reverseRel)

	// Save both objects
	if err := m.SaveArxObject(sourceObj); err != nil {
		return fmt.Errorf("failed to save source ArxObject: %w", err)
	}

	if err := m.SaveArxObject(targetObj); err != nil {
		return fmt.Errorf("failed to save target ArxObject: %w", err)
	}

	return nil
}

// RemoveRelationship removes a relationship between two ArxObjects
func (m *ArxObjectManager) RemoveRelationship(sourceID, targetID, relType string) error {
	// Load source object
	sourceObj, err := m.LoadArxObject(sourceID)
	if err != nil {
		return fmt.Errorf("failed to load source ArxObject %s: %w", sourceID, err)
	}

	// Load target object
	targetObj, err := m.LoadArxObject(targetID)
	if err != nil {
		return fmt.Errorf("failed to load target ArxObject %s: %w", targetID, err)
	}

	// Remove relationship from source object
	if sourceObj.Relationships != nil {
		var newRels []RelationshipMetadata
		for _, rel := range sourceObj.Relationships {
			if !(rel.TargetID == targetID && rel.Type == relType) {
				newRels = append(newRels, rel)
			}
		}
		sourceObj.Relationships = newRels
	}

	// Remove relationship from target object
	if targetObj.Relationships != nil {
		var newRels []RelationshipMetadata
		for _, rel := range targetObj.Relationships {
			if !(rel.TargetID == sourceID && rel.Type == relType) {
				newRels = append(newRels, rel)
			}
		}
		targetObj.Relationships = newRels
	}

	// Save both objects
	if err := m.SaveArxObject(sourceObj); err != nil {
		return fmt.Errorf("failed to save source ArxObject: %w", err)
	}

	if err := m.SaveArxObject(targetObj); err != nil {
		return fmt.Errorf("failed to save target ArxObject: %w", err)
	}

	return nil
}

// ValidateArxObject adds a validation record to an ArxObject
func (m *ArxObjectManager) ValidateArxObject(objectID, validatedBy, method string, confidence float64, notes string, evidence map[string]interface{}) error {
	obj, err := m.LoadArxObject(objectID)
	if err != nil {
		return fmt.Errorf("failed to load ArxObject %s: %w", objectID, err)
	}

	// Create validation record
	validation := ValidationMetadata{
		ID:          fmt.Sprintf("val_%s_%s_%d", objectID, method, time.Now().Unix()),
		Timestamp:   time.Now().UTC(),
		ValidatedBy: validatedBy,
		Method:      method,
		Evidence:    evidence,
		Confidence:  confidence,
		Notes:       notes,
		Status:      "approved",
	}

	// Add validation record
	if obj.Validations == nil {
		obj.Validations = []ValidationMetadata{}
	}
	obj.Validations = append(obj.Validations, validation)

	// Update validation status and confidence
	obj.ValidationStatus = "validated"
	obj.Confidence = confidence
	now := time.Now().UTC()
	obj.ValidatedAt = &now

	// Save updated object
	return m.SaveArxObject(obj)
}

// GetArxObjectRelationships returns all relationships for an ArxObject
func (m *ArxObjectManager) GetArxObjectRelationships(objectID string) ([]RelationshipMetadata, error) {
	obj, err := m.LoadArxObject(objectID)
	if err != nil {
		return nil, fmt.Errorf("failed to load ArxObject %s: %w", objectID, err)
	}

	return obj.Relationships, nil
}

// GetArxObjectValidations returns all validation records for an ArxObject
func (m *ArxObjectManager) GetArxObjectValidations(objectID string) ([]ValidationMetadata, error) {
	obj, err := m.LoadArxObject(objectID)
	if err != nil {
		return nil, fmt.Errorf("failed to load ArxObject %s: %w", objectID, err)
	}

	return obj.Validations, nil
}

// UpdateArxObjectLifecycle updates the lifecycle status of an ArxObject
func (m *ArxObjectManager) UpdateArxObjectLifecycle(objectID, status, phase, notes string) error {
	obj, err := m.LoadArxObject(objectID)
	if err != nil {
		return fmt.Errorf("failed to load ArxObject %s: %w", objectID, err)
	}

	// Update status
	obj.Status = status

	// Update lifecycle information
	now := time.Now().UTC()
	switch status {
	case "active":
		if obj.Properties == nil {
			obj.Properties = make(map[string]interface{})
		}
		obj.Properties["activated_at"] = now
	case "inactive":
		if obj.Properties == nil {
			obj.Properties = make(map[string]interface{})
		}
		obj.Properties["deactivated_at"] = now
	case "retired":
		if obj.Properties == nil {
			obj.Properties = make(map[string]interface{})
		}
		obj.Properties["retired_at"] = now
	}

	if obj.Properties == nil {
		obj.Properties = make(map[string]interface{})
	}
	obj.Properties["lifecycle_phase"] = phase
	obj.Properties["lifecycle_notes"] = notes

	// Save updated object
	return m.SaveArxObject(obj)
}

// SearchArxObjects searches ArxObjects based on various criteria
func (m *ArxObjectManager) SearchArxObjects(query string, filters map[string]interface{}) ([]*ArxObjectMetadata, error) {
	objects, err := m.GetAllArxObjects()
	if err != nil {
		return nil, fmt.Errorf("failed to get all ArxObjects: %w", err)
	}

	var results []*ArxObjectMetadata
	for _, obj := range objects {
		if m.matchesSearchCriteria(obj, query, filters) {
			results = append(results, obj)
		}
	}

	return results, nil
}

// matchesSearchCriteria checks if an ArxObject matches search criteria
func (m *ArxObjectManager) matchesSearchCriteria(obj *ArxObjectMetadata, query string, filters map[string]interface{}) bool {
	// Text search
	if query != "" {
		queryLower := strings.ToLower(query)
		if !strings.Contains(strings.ToLower(obj.Name), queryLower) &&
			!strings.Contains(strings.ToLower(obj.Description), queryLower) &&
			!strings.Contains(strings.ToLower(obj.Type), queryLower) {
			return false
		}
	}

	// Apply filters
	for key, value := range filters {
		switch key {
		case "type":
			if obj.Type != value {
				return false
			}
		case "status":
			if obj.Status != value {
				return false
			}
		case "validation_status":
			if obj.ValidationStatus != value {
				return false
			}
		case "floor":
			if obj.Location == nil || obj.Location.Floor != value {
				return false
			}
		case "confidence_min":
			if obj.Confidence < value.(float64) {
				return false
			}
		case "tags":
			if valueTags, ok := value.([]string); ok {
				found := false
				for _, tag := range valueTags {
					for _, objTag := range obj.Tags {
						if objTag == tag {
							found = true
							break
						}
					}
					if found {
						break
					}
				}
				if !found {
					return false
				}
			}
		}
	}

	return true
}

// GetArxObjectStats returns statistics about ArxObjects in the building
func (m *ArxObjectManager) GetArxObjectStats() (map[string]interface{}, error) {
	objects, err := m.GetAllArxObjects()
	if err != nil {
		return nil, fmt.Errorf("failed to get all ArxObjects: %w", err)
	}

	stats := map[string]interface{}{
		"total_count":         len(objects),
		"by_type":             make(map[string]int),
		"by_status":           make(map[string]int),
		"by_validation":       make(map[string]int),
		"by_floor":            make(map[int]int),
		"avg_confidence":      0.0,
		"validation_coverage": 0.0,
	}

	var totalConfidence float64
	var validatedCount int

	for _, obj := range objects {
		// Count by type
		stats["by_type"].(map[string]int)[obj.Type]++

		// Count by status
		stats["by_status"].(map[string]int)[obj.Status]++

		// Count by validation status
		if obj.ValidationStatus != "" {
			stats["by_validation"].(map[string]int)[obj.ValidationStatus]++
		}

		// Count by floor
		if obj.Location != nil {
			stats["by_floor"].(map[int]int)[obj.Location.Floor]++
		}

		// Track confidence
		totalConfidence += obj.Confidence

		// Track validation
		if obj.ValidationStatus == "validated" {
			validatedCount++
		}
	}

	// Calculate averages
	if len(objects) > 0 {
		stats["avg_confidence"] = totalConfidence / float64(len(objects))
		stats["validation_coverage"] = float64(validatedCount) / float64(len(objects))
	}

	return stats, nil
}

// ExportArxObjects exports ArxObjects to various formats
func (m *ArxObjectManager) ExportArxObjects(format string, filters map[string]interface{}) ([]byte, error) {
	objects, err := m.SearchArxObjects("", filters)
	if err != nil {
		return nil, fmt.Errorf("failed to search ArxObjects: %w", err)
	}

	switch format {
	case "json":
		return json.MarshalIndent(objects, "", "  ")
	case "csv":
		return m.exportToCSV(objects)
	default:
		return nil, fmt.Errorf("unsupported export format: %s", format)
	}
}

// exportToCSV exports ArxObjects to CSV format
func (m *ArxObjectManager) exportToCSV(objects []*ArxObjectMetadata) ([]byte, error) {
	if len(objects) == 0 {
		return []byte(""), nil
	}

	// Build CSV header
	headers := []string{"ID", "Name", "Type", "Description", "Status", "Floor", "Validation Status", "Confidence", "Created", "Updated"}

	// Build CSV rows
	var rows [][]string
	for _, obj := range objects {
		floor := ""
		if obj.Location != nil {
			floor = fmt.Sprintf("%d", obj.Location.Floor)
		}

		row := []string{
			obj.ID,
			obj.Name,
			obj.Type,
			obj.Description,
			obj.Status,
			floor,
			obj.ValidationStatus,
			fmt.Sprintf("%.2f", obj.Confidence),
			obj.Created.Format("2006-01-02 15:04:05"),
			obj.Updated.Format("2006-01-02 15:04:05"),
		}
		rows = append(rows, row)
	}

	// Convert to CSV string
	var csv strings.Builder
	csv.WriteString(strings.Join(headers, ",") + "\n")
	for _, row := range rows {
		csv.WriteString(strings.Join(row, ",") + "\n")
	}

	return []byte(csv.String()), nil
}
