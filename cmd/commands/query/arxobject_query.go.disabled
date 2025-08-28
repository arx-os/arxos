package query

import (
	"fmt"
	"strings"
	"time"
	
	"github.com/arxos/arxos/cmd/aql"
	"github.com/arxos/arxos/cmd/cgo"
)

// ArxObjectQueryEngine executes AQL queries against the CGO ArxObject system
type ArxObjectQueryEngine struct {
	initialized bool
}

// NewArxObjectQueryEngine creates a new query engine
func NewArxObjectQueryEngine() (*ArxObjectQueryEngine, error) {
	engine := &ArxObjectQueryEngine{}
	
	// Initialize CGO ArxObject system
	config := map[string]interface{}{
		"log_level": 2,
		"cache_size": 10000,
	}
	
	if err := cgo.Initialize(config); err != nil {
		return nil, fmt.Errorf("failed to initialize ArxObject system: %w", err)
	}
	
	engine.initialized = true
	return engine, nil
}

// ExecuteQuery executes an AQL query string
func (e *ArxObjectQueryEngine) ExecuteQuery(queryStr string) (*AQLResult, error) {
	if !e.initialized {
		return nil, fmt.Errorf("engine not initialized")
	}
	
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
func (e *ArxObjectQueryEngine) executeSelect(query *aql.Query) (*AQLResult, error) {
	startTime := time.Now()
	var objects []*cgo.ArxObject
	
	// Debug: Print query target
	// fmt.Printf("Debug: Query target = '%s'\n", query.Target)
	
	// Handle different query patterns
	if query.Target == "*" {
		// Query all objects
		for objType := cgo.TypeBuilding; objType <= cgo.TypeSystem; objType++ {
			results, err := cgo.QueryByType(objType)
			if err != nil {
				continue // Skip errors for now
			}
			objects = append(objects, results...)
		}
	} else {
		// Query specific type
		objType := parseObjectType(query.Target)
		if objType != cgo.TypeUnknown {
			results, err := cgo.QueryByType(objType)
			if err != nil {
				return nil, err
			}
			objects = results
		} else {
			// Try path-based query
			results, err := cgo.QueryByPath(query.Target)
			if err != nil {
				return nil, err
			}
			objects = results
		}
	}
	
	// Apply conditions
	if len(query.Conditions) > 0 {
		objects = e.filterByConditions(objects, query.Conditions)
	}
	
	// TODO: Apply sorting from query options
	// objects = e.sortObjects(objects)
	
	// TODO: Apply limit and offset from query string parsing
	
	// Convert to result format
	resultObjects := e.convertToResultFormat(objects, query.Fields)
	
	executionTime := time.Since(startTime)
	
	return &AQLResult{
		Type:    "SELECT",
		Objects: resultObjects,
		Count:   len(resultObjects),
		Message: fmt.Sprintf("Query executed successfully in %v", executionTime),
		Metadata: map[string]interface{}{
			"total_matched": len(objects),
			"returned":      len(resultObjects),
			"query_time":    executionTime.String(),
			"fields":        query.Fields,
		},
		ExecutedAt: time.Now(),
	}, nil
}

// executeValidate handles VALIDATE queries
func (e *ArxObjectQueryEngine) executeValidate(query *aql.Query) (*AQLResult, error) {
	// TODO: Implement validation logic
	return &AQLResult{
		Type:    "VALIDATE",
		Objects: []interface{}{},
		Count:   0,
		Message: "Validation not yet implemented",
		ExecutedAt: time.Now(),
	}, nil
}

// executeInsert handles INSERT queries
func (e *ArxObjectQueryEngine) executeInsert(query *aql.Query) (*AQLResult, error) {
	// Extract values from query
	name := ""
	path := ""
	objType := cgo.TypeUnknown
	x, y, z := int32(0), int32(0), int32(0)
	
	// Parse values from query (simplified)
	if query.Values != nil {
		for k, v := range query.Values {
			switch k {
			case "name":
				name = fmt.Sprintf("%v", v)
			case "path":
				path = fmt.Sprintf("%v", v)
			case "type":
				objType = parseObjectType(fmt.Sprintf("%v", v))
			case "x":
				fmt.Sscanf(fmt.Sprintf("%v", v), "%d", &x)
			case "y":
				fmt.Sscanf(fmt.Sprintf("%v", v), "%d", &y)
			case "z":
				fmt.Sscanf(fmt.Sprintf("%v", v), "%d", &z)
			}
		}
	}
	
	// Create the object
	obj, err := cgo.CreateObject(name, path, objType, x, y, z)
	if err != nil {
		return nil, err
	}
	
	return &AQLResult{
		Type:    "INSERT",
		Objects: []interface{}{convertArxObjectToMap(obj)},
		Count:   1,
		Message: fmt.Sprintf("Object created with ID: %d", obj.ID),
		Metadata: map[string]interface{}{
			"object_id": obj.ID,
			"type":      obj.Type,
		},
		ExecutedAt: time.Now(),
	}, nil
}

// executeUpdate handles UPDATE queries
func (e *ArxObjectQueryEngine) executeUpdate(query *aql.Query) (*AQLResult, error) {
	// First, find objects to update
	selectQuery := &aql.Query{
		Type:       aql.SELECT,
		Target:     query.Target,
		Conditions: query.Conditions,
	}
	
	selectResult, err := e.executeSelect(selectQuery)
	if err != nil {
		return nil, err
	}
	
	updatedCount := 0
	
	// Update each object
	for _, objInterface := range selectResult.Objects {
		if objMap, ok := objInterface.(map[string]interface{}); ok {
			if idFloat, ok := objMap["id"].(float64); ok {
				id := uint64(idFloat)
				
				// Get the object
				obj, err := cgo.GetObject(id)
				if err != nil {
					continue
				}
				
				// Apply updates
				if query.Values != nil {
					for field, value := range query.Values {
						switch field {
						case "confidence":
							var conf float32
							fmt.Sscanf(fmt.Sprintf("%v", value), "%f", &conf)
							obj.Confidence = conf
						case "validated":
							obj.IsValidated = (fmt.Sprintf("%v", value) == "true")
						case "name":
							obj.Name = fmt.Sprintf("%v", value)
						}
					}
				}
				
				// Update the object
				if err := cgo.UpdateObject(obj); err == nil {
					updatedCount++
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

// executeDelete handles DELETE queries
func (e *ArxObjectQueryEngine) executeDelete(query *aql.Query) (*AQLResult, error) {
	// First, find objects to delete
	selectQuery := &aql.Query{
		Type:       aql.SELECT,
		Target:     query.Target,
		Conditions: query.Conditions,
	}
	
	selectResult, err := e.executeSelect(selectQuery)
	if err != nil {
		return nil, err
	}
	
	deletedCount := 0
	
	// Delete each object
	for _, objInterface := range selectResult.Objects {
		if objMap, ok := objInterface.(map[string]interface{}); ok {
			if idFloat, ok := objMap["id"].(float64); ok {
				id := uint64(idFloat)
				
				// Delete the object
				if err := cgo.DeleteObject(id); err == nil {
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

// filterByConditions applies WHERE conditions to objects
func (e *ArxObjectQueryEngine) filterByConditions(objects []*cgo.ArxObject, conditions []aql.Condition) []*cgo.ArxObject {
	var filtered []*cgo.ArxObject
	
	for _, obj := range objects {
		match := true
		for _, cond := range conditions {
			if !e.matchCondition(obj, cond) {
				match = false
				break
			}
		}
		if match {
			filtered = append(filtered, obj)
		}
	}
	
	return filtered
}

// matchCondition checks if an object matches a condition
func (e *ArxObjectQueryEngine) matchCondition(obj *cgo.ArxObject, cond aql.Condition) bool {
	valueStr := fmt.Sprintf("%v", cond.Value)
	
	switch cond.Field {
	case "id":
		var id uint64
		fmt.Sscanf(valueStr, "%d", &id)
		return compareUint64(obj.ID, cond.Operator, id)
	case "name":
		return compareString(obj.Name, cond.Operator, valueStr)
	case "path":
		return compareString(obj.Path, cond.Operator, valueStr)
	case "type":
		typeStr := objectTypeToString(obj.Type)
		return compareString(typeStr, cond.Operator, valueStr)
	case "confidence":
		var conf float32
		fmt.Sscanf(valueStr, "%f", &conf)
		return compareFloat32(obj.Confidence, cond.Operator, conf)
	case "validated":
		validated := obj.IsValidated
		expectedVal := (valueStr == "true")
		return validated == expectedVal
	case "x", "world_x":
		var x int32
		fmt.Sscanf(valueStr, "%d", &x)
		return compareInt32(obj.WorldX, cond.Operator, x)
	case "y", "world_y":
		var y int32
		fmt.Sscanf(valueStr, "%d", &y)
		return compareInt32(obj.WorldY, cond.Operator, y)
	case "z", "world_z":
		var z int32
		fmt.Sscanf(valueStr, "%d", &z)
		return compareInt32(obj.WorldZ, cond.Operator, z)
	}
	return false
}

// sortObjects sorts objects by the specified fields
func (e *ArxObjectQueryEngine) sortObjects(objects []*cgo.ArxObject) []*cgo.ArxObject {
	// TODO: Implement sorting based on query options
	// This is a placeholder implementation
	return objects
}

// convertToResultFormat converts ArxObjects to result format
func (e *ArxObjectQueryEngine) convertToResultFormat(objects []*cgo.ArxObject, fields []string) []interface{} {
	results := make([]interface{}, 0, len(objects))
	
	for _, obj := range objects {
		if len(fields) == 1 && fields[0] == "*" {
			// Return all fields
			results = append(results, convertArxObjectToMap(obj))
		} else {
			// Return selected fields
			selected := make(map[string]interface{})
			for _, field := range fields {
				switch field {
				case "id":
					selected["id"] = obj.ID
				case "name":
					selected["name"] = obj.Name
				case "path":
					selected["path"] = obj.Path
				case "type":
					selected["type"] = objectTypeToString(obj.Type)
				case "confidence":
					selected["confidence"] = obj.Confidence
				case "validated":
					selected["validated"] = obj.IsValidated
				case "x", "world_x":
					selected["world_x"] = obj.WorldX
				case "y", "world_y":
					selected["world_y"] = obj.WorldY
				case "z", "world_z":
					selected["world_z"] = obj.WorldZ
				case "width":
					selected["width"] = obj.Width
				case "height":
					selected["height"] = obj.Height
				case "depth":
					selected["depth"] = obj.Depth
				}
			}
			results = append(results, selected)
		}
	}
	
	return results
}

// Helper functions

func parseObjectType(typeName string) cgo.ObjectType {
	typeMap := map[string]cgo.ObjectType{
		"building":  cgo.TypeBuilding,
		"floor":     cgo.TypeFloor,
		"room":      cgo.TypeRoom,
		"wall":      cgo.TypeWall,
		"door":      cgo.TypeDoor,
		"window":    cgo.TypeWindow,
		"column":    cgo.TypeColumn,
		"beam":      cgo.TypeBeam,
		"slab":      cgo.TypeSlab,
		"roof":      cgo.TypeRoof,
		"stair":     cgo.TypeStair,
		"elevator":  cgo.TypeElevator,
		"equipment": cgo.TypeEquipment,
		"furniture": cgo.TypeFurniture,
		"fixture":   cgo.TypeFixture,
		"pipe":      cgo.TypePipe,
		"duct":      cgo.TypeDuct,
		"cable":     cgo.TypeCable,
		"sensor":    cgo.TypeSensor,
		"system":    cgo.TypeSystem,
	}
	
	if t, ok := typeMap[strings.ToLower(typeName)]; ok {
		return t
	}
	return cgo.TypeUnknown
}

func objectTypeToString(objType cgo.ObjectType) string {
	typeNames := map[cgo.ObjectType]string{
		cgo.TypeBuilding:  "building",
		cgo.TypeFloor:     "floor",
		cgo.TypeRoom:      "room",
		cgo.TypeWall:      "wall",
		cgo.TypeDoor:      "door",
		cgo.TypeWindow:    "window",
		cgo.TypeColumn:    "column",
		cgo.TypeBeam:      "beam",
		cgo.TypeSlab:      "slab",
		cgo.TypeRoof:      "roof",
		cgo.TypeStair:     "stair",
		cgo.TypeElevator:  "elevator",
		cgo.TypeEquipment: "equipment",
		cgo.TypeFurniture: "furniture",
		cgo.TypeFixture:   "fixture",
		cgo.TypePipe:      "pipe",
		cgo.TypeDuct:      "duct",
		cgo.TypeCable:     "cable",
		cgo.TypeSensor:    "sensor",
		cgo.TypeSystem:    "system",
	}
	
	if name, ok := typeNames[objType]; ok {
		return name
	}
	return "unknown"
}

func convertArxObjectToMap(obj *cgo.ArxObject) map[string]interface{} {
	return map[string]interface{}{
		"id":          obj.ID,
		"name":        obj.Name,
		"path":        obj.Path,
		"type":        objectTypeToString(obj.Type),
		"world_x":     obj.WorldX,
		"world_y":     obj.WorldY,
		"world_z":     obj.WorldZ,
		"width":       obj.Width,
		"height":      obj.Height,
		"depth":       obj.Depth,
		"confidence":  obj.Confidence,
		"validated":   obj.IsValidated,
		"parent_id":   obj.ParentID,
		"child_ids":   obj.ChildIDs,
		"properties":  obj.Properties,
		"metadata":    obj.Metadata,
	}
}

// Comparison functions

func compareString(actual, operator, expected string) bool {
	switch operator {
	case "=", "==":
		return actual == expected
	case "!=", "<>":
		return actual != expected
	case "LIKE":
		// Simple pattern matching (could be enhanced)
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

func compareFloat32(actual float32, operator string, expected float32) bool {
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

func compareInt32(actual int32, operator string, expected int32) bool {
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

func compareUint64(actual uint64, operator string, expected uint64) bool {
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

// Cleanup releases resources
func (e *ArxObjectQueryEngine) Cleanup() {
	if e.initialized {
		cgo.Cleanup()
		e.initialized = false
	}
}