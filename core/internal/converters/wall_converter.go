// Package converters provides data conversion utilities
package converters

import (
	"fmt"
	"github.com/arxos/arxos/core/internal/arxobject"
)

// WallConverter converts wall data between formats
type WallConverter struct{}

// NewWallConverter creates a new wall converter
func NewWallConverter() *WallConverter {
	return &WallConverter{}
}

// ConvertToArxObject converts wall data to ArxObject
func (c *WallConverter) ConvertToArxObject(data map[string]interface{}) (*arxobject.ArxObject, error) {
	// Extract wall properties
	name, ok := data["name"].(string)
	if !ok {
		name = "Wall"
	}
	
	obj := arxobject.NewArxObject(arxobject.TypeWall, name)
	
	// Set properties from data
	for k, v := range data {
		obj.SetProperty(k, v)
	}
	
	return obj, nil
}

// ConvertFromArxObject converts ArxObject to wall data
func (c *WallConverter) ConvertFromArxObject(obj *arxobject.ArxObject) (map[string]interface{}, error) {
	if obj.Type != arxobject.TypeWall {
		return nil, fmt.Errorf("object is not a wall: %s", obj.Type)
	}
	
	data := make(map[string]interface{})
	data["id"] = obj.ID
	data["name"] = obj.Name
	data["type"] = string(obj.Type)
	
	// Copy properties
	for k, v := range obj.Properties {
		data[k] = v
	}
	
	return data, nil
}

// ConvertBatch converts multiple walls
func (c *WallConverter) ConvertBatch(items []map[string]interface{}) ([]*arxobject.ArxObject, error) {
	results := make([]*arxobject.ArxObject, 0, len(items))
	
	for _, item := range items {
		obj, err := c.ConvertToArxObject(item)
		if err != nil {
			return nil, fmt.Errorf("failed to convert item: %w", err)
		}
		results = append(results, obj)
	}
	
	return results, nil
}