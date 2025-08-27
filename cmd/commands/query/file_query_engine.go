package query

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
	
	"github.com/arxos/arxos/cmd/aql"
	"github.com/arxos/arxos/cmd/models"
)

// FileBasedQueryEngine executes AQL queries against file-based ArxObject storage
type FileBasedQueryEngine struct {
	buildingRoot string
	objectsDir   string
	indexPath    string
	objects      map[string]*models.ArxObjectMetadata // Cache of loaded objects
}

// NewFileBasedQueryEngine creates a new query engine for file-based storage
func NewFileBasedQueryEngine() (*FileBasedQueryEngine, error) {
	// Find the building root
	cwd, err := os.Getwd()
	if err != nil {
		return nil, fmt.Errorf("failed to get current directory: %w", err)
	}
	
	// Look for .arxos directory to find building root
	buildingRoot := findBuildingRootFrom(cwd)
	if buildingRoot == "" {
		return nil, fmt.Errorf("not in a building workspace")
	}
	
	engine := &FileBasedQueryEngine{
		buildingRoot: buildingRoot,
		objectsDir:   filepath.Join(buildingRoot, ".arxos", "objects"),
		indexPath:    filepath.Join(buildingRoot, ".arxos", "objects", "index.json"),
		objects:      make(map[string]*models.ArxObjectMetadata),
	}
	
	// Load all objects into memory for querying
	if err := engine.loadAllObjects(); err != nil {
		return nil, fmt.Errorf("failed to load objects: %w", err)
	}
	
	return engine, nil
}

// findBuildingRootFrom searches for .arxos directory
func findBuildingRootFrom(startPath string) string {
	current := startPath
	for {
		arxosPath := filepath.Join(current, ".arxos")
		if info, err := os.Stat(arxosPath); err == nil && info.IsDir() {
			return current
		}
		
		parent := filepath.Dir(current)
		if parent == current {
			break
		}
		current = parent
	}
	return ""
}

// loadAllObjects loads all ArxObject JSON files into memory
func (e *FileBasedQueryEngine) loadAllObjects() error {
	// Check if objects directory exists
	if _, err := os.Stat(e.objectsDir); os.IsNotExist(err) {
		return nil // No objects yet
	}
	
	// Walk through all JSON files in objects directory
	err := filepath.Walk(e.objectsDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		
		// Skip directories and non-JSON files
		if info.IsDir() || !strings.HasSuffix(path, ".json") {
			return nil
		}
		
		// Skip index.json and consolidated files (building.json, floor_*.json, system_*.json)
		baseName := filepath.Base(path)
		if baseName == "index.json" || baseName == "building.json" || 
		   strings.HasPrefix(baseName, "floor_") || strings.HasPrefix(baseName, "system_") {
			return nil
		}
		
		// Load the object
		data, err := os.ReadFile(path)
		if err != nil {
			return fmt.Errorf("failed to read %s: %w", path, err)
		}
		
		var obj models.ArxObjectMetadata
		if err := json.Unmarshal(data, &obj); err != nil {
			return fmt.Errorf("failed to parse %s: %w", path, err)
		}
		
		e.objects[obj.ID] = &obj
		return nil
	})
	
	return err
}

// ExecuteQuery executes an AQL query string
func (e *FileBasedQueryEngine) ExecuteQuery(queryStr string) (*AQLResult, error) {
	// Parse the AQL query
	parser := aql.NewParser()
	query, err := parser.Parse(queryStr)
	if err != nil {
		return nil, fmt.Errorf("query parse error: %w", err)
	}
	
	// Execute based on query type
	switch query.Type {
	case aql.SELECT:
		return e.executeSelect(query)
	case aql.UPDATE:
		return e.executeUpdate(query)
	case aql.DELETE:
		return e.executeDelete(query)
	case aql.VALIDATE:
		return e.executeValidate(query)
	default:
		return nil, fmt.Errorf("unsupported query type: %v", query.Type)
	}
}

// executeSelect handles SELECT queries
func (e *FileBasedQueryEngine) executeSelect(query *aql.Query) (*AQLResult, error) {
	startTime := time.Now()
	var results []interface{}
	
	// Filter objects based on query
	for _, obj := range e.objects {
		// Check if object matches target type/pattern
		if !e.matchesTarget(obj, query.Target) {
			continue
		}
		
		// Check if object matches conditions
		if !e.matchesConditions(obj, query.Conditions) {
			continue
		}
		
		// Add to results
		results = append(results, e.formatObject(obj, query.Fields))
	}
	
	executionTime := time.Since(startTime)
	
	return &AQLResult{
		Type:    "SELECT",
		Objects: results,
		Count:   len(results),
		Message: fmt.Sprintf("Query executed successfully in %v", executionTime),
		Metadata: map[string]interface{}{
			"total_scanned": len(e.objects),
			"matched":       len(results),
			"query_time":    executionTime.String(),
		},
		ExecutedAt: time.Now(),
	}, nil
}

// matchesTarget checks if an object matches the query target
func (e *FileBasedQueryEngine) matchesTarget(obj *models.ArxObjectMetadata, target string) bool {
	if target == "*" {
		return true
	}
	
	// Check if target is a type
	targetLower := strings.ToLower(target)
	if obj.Type == targetLower {
		return true
	}
	
	// Check if target is a path pattern
	if strings.Contains(target, ":") || strings.Contains(target, "/") {
		// Handle wildcard patterns like "building:*"
		if strings.HasSuffix(target, "*") {
			prefix := strings.TrimSuffix(target, "*")
			return strings.HasPrefix(obj.ID, prefix)
		}
		return strings.Contains(obj.ID, target)
	}
	
	// Check various type synonyms
	typeMap := map[string][]string{
		"floor":     {"floor", "floors", "level"},
		"room":      {"room", "rooms", "space"},
		"wall":      {"wall", "walls"},
		"door":      {"door", "doors", "entrance"},
		"window":    {"window", "windows"},
		"equipment": {"equipment", "device", "unit"},
		"sensor":    {"sensor", "sensors", "detector"},
		"system":    {"system", "systems"},
		"building":  {"building", "buildings"},
	}
	
	for objType, synonyms := range typeMap {
		for _, synonym := range synonyms {
			if targetLower == synonym && obj.Type == objType {
				return true
			}
		}
	}
	
	return false
}

// matchesConditions checks if an object matches WHERE conditions
func (e *FileBasedQueryEngine) matchesConditions(obj *models.ArxObjectMetadata, conditions []aql.Condition) bool {
	for _, cond := range conditions {
		if !e.matchCondition(obj, cond) {
			return false
		}
	}
	return true
}

// matchCondition checks if an object matches a single condition
func (e *FileBasedQueryEngine) matchCondition(obj *models.ArxObjectMetadata, cond aql.Condition) bool {
	valueStr := fmt.Sprintf("%v", cond.Value)
	
	switch cond.Field {
	case "id":
		return fileCompareString(obj.ID, cond.Operator, valueStr)
		
	case "name":
		return fileCompareString(obj.Name, cond.Operator, valueStr)
		
	case "type":
		return fileCompareString(obj.Type, cond.Operator, valueStr)
		
	case "status":
		return fileCompareString(obj.Status, cond.Operator, valueStr)
		
	case "parent":
		return fileCompareString(obj.Parent, cond.Operator, valueStr)
		
	case "confidence":
		var conf float64
		fmt.Sscanf(valueStr, "%f", &conf)
		return fileCompareFloat(obj.Confidence, cond.Operator, conf)
		
	case "validated":
		isValidated := obj.ValidationStatus == "validated"
		expectedVal := (valueStr == "true")
		return isValidated == expectedVal
		
	case "validation_status":
		return fileCompareString(obj.ValidationStatus, cond.Operator, valueStr)
		
	case "floor":
		if obj.Location != nil {
			return fileCompareInt(obj.Location.Floor, cond.Operator, fileParseInt(valueStr))
		}
		return false
		
	case "room":
		if obj.Location != nil {
			return fileCompareString(obj.Location.Room, cond.Operator, valueStr)
		}
		return false
		
	default:
		// Check in properties
		if obj.Properties != nil {
			if propVal, exists := obj.Properties[cond.Field]; exists {
				propStr := fmt.Sprintf("%v", propVal)
				return fileCompareString(propStr, cond.Operator, valueStr)
			}
		}
		return false
	}
}

// formatObject formats an object for output based on selected fields
func (e *FileBasedQueryEngine) formatObject(obj *models.ArxObjectMetadata, fields []string) map[string]interface{} {
	// If * or no fields specified, return all fields
	if len(fields) == 0 || (len(fields) == 1 && fields[0] == "*") {
		return map[string]interface{}{
			"id":                obj.ID,
			"name":              obj.Name,
			"type":              obj.Type,
			"description":       obj.Description,
			"status":            obj.Status,
			"parent":            obj.Parent,
			"confidence":        obj.Confidence,
			"validation_status": obj.ValidationStatus,
			"created":           obj.Created,
			"updated":           obj.Updated,
			"location":          obj.Location,
			"properties":        obj.Properties,
		}
	}
	
	// Return only selected fields
	result := make(map[string]interface{})
	for _, field := range fields {
		switch field {
		case "id":
			result["id"] = obj.ID
		case "name":
			result["name"] = obj.Name
		case "type":
			result["type"] = obj.Type
		case "description":
			result["description"] = obj.Description
		case "status":
			result["status"] = obj.Status
		case "parent":
			result["parent"] = obj.Parent
		case "confidence":
			result["confidence"] = obj.Confidence
		case "validation_status":
			result["validation_status"] = obj.ValidationStatus
		case "created":
			result["created"] = obj.Created
		case "updated":
			result["updated"] = obj.Updated
		case "location":
			result["location"] = obj.Location
		case "properties":
			result["properties"] = obj.Properties
		}
	}
	
	return result
}

// executeUpdate handles UPDATE queries
func (e *FileBasedQueryEngine) executeUpdate(query *aql.Query) (*AQLResult, error) {
	// First, find objects to update
	selectQuery := &aql.Query{
		Type:       aql.SELECT,
		Target:     query.Target,
		Conditions: query.Conditions,
		Fields:     []string{"*"},
	}
	
	selectResult, err := e.executeSelect(selectQuery)
	if err != nil {
		return nil, err
	}
	
	updatedCount := 0
	
	// Update each object
	for _, objInterface := range selectResult.Objects {
		if objMap, ok := objInterface.(map[string]interface{}); ok {
			if id, ok := objMap["id"].(string); ok {
				if obj, exists := e.objects[id]; exists {
					// Apply updates
					if query.Values != nil {
						for field, value := range query.Values {
							e.updateObjectField(obj, field, value)
						}
					}
					
					// Save the updated object
					if err := e.saveObject(obj); err == nil {
						updatedCount++
					}
				}
			}
		}
	}
	
	return &AQLResult{
		Type:    "UPDATE",
		Objects: []interface{}{},
		Count:   updatedCount,
		Message: fmt.Sprintf("Updated %d objects", updatedCount),
		Metadata: map[string]interface{}{
			"rows_affected": updatedCount,
		},
		ExecutedAt: time.Now(),
	}, nil
}

// updateObjectField updates a specific field on an object
func (e *FileBasedQueryEngine) updateObjectField(obj *models.ArxObjectMetadata, field string, value interface{}) {
	switch field {
	case "name":
		obj.Name = fmt.Sprintf("%v", value)
	case "status":
		obj.Status = fmt.Sprintf("%v", value)
	case "confidence":
		fmt.Sscanf(fmt.Sprintf("%v", value), "%f", &obj.Confidence)
	case "validation_status":
		obj.ValidationStatus = fmt.Sprintf("%v", value)
	case "description":
		obj.Description = fmt.Sprintf("%v", value)
	default:
		// Update in properties
		if obj.Properties == nil {
			obj.Properties = make(map[string]interface{})
		}
		obj.Properties[field] = value
	}
	obj.Updated = time.Now()
}

// saveObject saves an object back to disk
func (e *FileBasedQueryEngine) saveObject(obj *models.ArxObjectMetadata) error {
	filename := filepath.Join(e.objectsDir, obj.ID+".json")
	
	data, err := json.MarshalIndent(obj, "", "  ")
	if err != nil {
		return err
	}
	
	return os.WriteFile(filename, data, 0644)
}

// executeDelete handles DELETE queries
func (e *FileBasedQueryEngine) executeDelete(query *aql.Query) (*AQLResult, error) {
	// First, find objects to delete
	selectQuery := &aql.Query{
		Type:       aql.SELECT,
		Target:     query.Target,
		Conditions: query.Conditions,
		Fields:     []string{"id"},
	}
	
	selectResult, err := e.executeSelect(selectQuery)
	if err != nil {
		return nil, err
	}
	
	deletedCount := 0
	
	// Delete each object
	for _, objInterface := range selectResult.Objects {
		if objMap, ok := objInterface.(map[string]interface{}); ok {
			if id, ok := objMap["id"].(string); ok {
				// Delete the file
				filename := filepath.Join(e.objectsDir, id+".json")
				if err := os.Remove(filename); err == nil {
					delete(e.objects, id)
					deletedCount++
				}
			}
		}
	}
	
	return &AQLResult{
		Type:    "DELETE",
		Objects: []interface{}{},
		Count:   deletedCount,
		Message: fmt.Sprintf("Deleted %d objects", deletedCount),
		Metadata: map[string]interface{}{
			"rows_affected": deletedCount,
		},
		ExecutedAt: time.Now(),
	}, nil
}

// executeValidate handles VALIDATE queries
func (e *FileBasedQueryEngine) executeValidate(query *aql.Query) (*AQLResult, error) {
	// Similar to UPDATE but specifically for validation
	selectQuery := &aql.Query{
		Type:       aql.SELECT,
		Target:     query.Target,
		Conditions: query.Conditions,
		Fields:     []string{"*"},
	}
	
	selectResult, err := e.executeSelect(selectQuery)
	if err != nil {
		return nil, err
	}
	
	validatedCount := 0
	
	for _, objInterface := range selectResult.Objects {
		if objMap, ok := objInterface.(map[string]interface{}); ok {
			if id, ok := objMap["id"].(string); ok {
				if obj, exists := e.objects[id]; exists {
					obj.ValidationStatus = "validated"
					obj.Confidence = 1.0
					validatedTime := time.Now()
					obj.ValidatedAt = &validatedTime
					obj.Updated = time.Now()
					
					if err := e.saveObject(obj); err == nil {
						validatedCount++
					}
				}
			}
		}
	}
	
	return &AQLResult{
		Type:    "VALIDATE",
		Objects: []interface{}{},
		Count:   validatedCount,
		Message: fmt.Sprintf("Validated %d objects", validatedCount),
		Metadata: map[string]interface{}{
			"rows_affected": validatedCount,
		},
		ExecutedAt: time.Now(),
	}, nil
}

// GetObjectCount returns the total number of loaded objects
func (e *FileBasedQueryEngine) GetObjectCount() int {
	return len(e.objects)
}

// Cleanup releases resources (no-op for file-based engine)
func (e *FileBasedQueryEngine) Cleanup() {
	// No cleanup needed for file-based engine
}

// Helper comparison functions

func fileCompareString(actual, operator, expected string) bool {
	switch operator {
	case "=", "==":
		return actual == expected
	case "!=", "<>":
		return actual != expected
	case "LIKE":
		return strings.Contains(strings.ToLower(actual), strings.ToLower(expected))
	case ">":
		return actual > expected
	case ">=":
		return actual >= expected
	case "<":
		return actual < expected
	case "<=":
		return actual <= expected
	}
	return false
}

func fileCompareFloat(actual float64, operator string, expected float64) bool {
	switch operator {
	case "=", "==":
		return actual == expected
	case "!=", "<>":
		return actual != expected
	case ">":
		return actual > expected
	case ">=":
		return actual >= expected
	case "<":
		return actual < expected
	case "<=":
		return actual <= expected
	}
	return false
}

func fileCompareInt(actual int, operator string, expected int) bool {
	switch operator {
	case "=", "==":
		return actual == expected
	case "!=", "<>":
		return actual != expected
	case ">":
		return actual > expected
	case ">=":
		return actual >= expected
	case "<":
		return actual < expected
	case "<=":
		return actual <= expected
	}
	return false
}

func fileParseInt(s string) int {
	var i int
	fmt.Sscanf(s, "%d", &i)
	return i
}