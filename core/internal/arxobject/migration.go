// Package arxobject provides migration utilities for the unified systems
package arxobject

import (
	"fmt"
	"strings"
	"time"
	
	"github.com/arxos/arxos/core/internal/confidence"
	arxpath "github.com/arxos/arxos/core/internal/path"
)

// MigrateToUnified migrates an old ArxObject to the unified system
func MigrateToUnified(old *ArxObject) *ArxObjectUnified {
	// Create path from hierarchy
	path := buildPathFromHierarchy(old)
	
	// Create new unified object
	unified := &ArxObjectUnified{
		ID:           old.ID,
		Type:         old.Type,
		Name:         old.Name,
		Description:  old.Description,
		Path:         arxpath.Normalize(path),
		BuildingID:   old.BuildingID,
		FloorID:      old.FloorID,
		ZoneID:       old.ZoneID,
		ParentID:     old.ParentID,
		Geometry:     old.Geometry,
		Properties:   old.Properties,
		Material:     old.Material,
		Color:        old.Color,
		Relationships: old.Relationships,
		ValidationStatus: old.ValidationStatus,
		Validations:  old.Validations,
		SourceType:   old.SourceType,
		SourceFile:   old.SourceFile,
		SourcePage:   old.SourcePage,
		Version:      old.Version,
		CreatedAt:    old.CreatedAt,
		UpdatedAt:    old.UpdatedAt,
		ValidatedAt:  old.ValidatedAt,
		Tags:         old.Tags,
		Flags:        old.Flags,
		Hash:         old.Hash,
	}
	
	// Migrate confidence
	unified.Confidence = migrateConfidence(old.Confidence, old.ConfidenceFactors)
	
	// Update confidence from validations
	for _, validation := range old.Validations {
		source := confidence.Source{
			Type:        confidence.SourceValidation,
			Method:      validation.Method,
			Confidence:  validation.Confidence,
			Timestamp:   validation.Timestamp,
			ValidatorID: validation.ValidatedBy,
		}
		
		params := confidence.UpdateParams{
			Source: source,
			Reason: fmt.Sprintf("Migrated validation from %s", validation.Method),
		}
		
		unified.Confidence.Update(params)
	}
	
	return unified
}

// buildPathFromHierarchy constructs a path from hierarchy fields
func buildPathFromHierarchy(obj *ArxObject) string {
	var pathParts []string
	
	// Determine system from type
	system := getSystemFromType(obj.Type)
	if system != "" {
		pathParts = append(pathParts, system)
	}
	
	// Add building if present
	if obj.BuildingID != "" {
		pathParts = append(pathParts, "building", cleanID(obj.BuildingID))
	}
	
	// Add floor if present
	if obj.FloorID != "" {
		pathParts = append(pathParts, "floor", cleanID(obj.FloorID))
	}
	
	// Add zone if present
	if obj.ZoneID != "" {
		pathParts = append(pathParts, "zone", cleanID(obj.ZoneID))
	}
	
	// Add object type and name/ID
	objType := strings.ToLower(string(obj.Type))
	objType = strings.ReplaceAll(objType, "_", "-")
	
	if obj.Name != "" {
		pathParts = append(pathParts, objType, cleanName(obj.Name))
	} else {
		pathParts = append(pathParts, objType, cleanID(obj.ID))
	}
	
	return "/" + strings.Join(pathParts, "/")
}

// getSystemFromType determines the system based on object type
func getSystemFromType(objType ArxObjectType) string {
	switch objType {
	case TypeElectricalPanel, TypeElectricalOutlet, TypeElectricalSwitch, 
	     TypeElectricalConduit, TypeLightFixture:
		return "electrical"
		
	case TypeHVACUnit, TypeHVACDuct, TypeHVACVent, TypeThermostat:
		return "hvac"
		
	case TypePlumbingPipe, TypePlumbingFixture, TypePlumbingValve, TypeDrain:
		return "plumbing"
		
	case TypeWall, TypeColumn, TypeBeam, TypeSlab, TypeFoundation, 
	     TypeRoof, TypeStair:
		return "structural"
		
	case TypeFireSprinkler, TypeFireAlarm, TypeSmokeDetector, 
	     TypeEmergencyExit, TypeFireExtinguisher:
		return "fire"
		
	case TypeSensor, TypeActuator, TypeController, TypeNetworkDevice:
		return "network"
		
	case TypeDoor, TypeWindow, TypeOpening:
		return "openings"
		
	case TypeRoom, TypeFloor, TypeZone, TypeBuilding:
		return "spaces"
		
	default:
		return "general"
	}
}

// cleanID cleans an ID for use in a path
func cleanID(id string) string {
	// Remove UUID formatting if present
	id = strings.ReplaceAll(id, "-", "")
	
	// Take first 8 chars if it's a UUID
	if len(id) > 8 {
		id = id[:8]
	}
	
	return strings.ToLower(id)
}

// cleanName cleans a name for use in a path
func cleanName(name string) string {
	// Convert to lowercase
	name = strings.ToLower(name)
	
	// Replace spaces with hyphens
	name = strings.ReplaceAll(name, " ", "-")
	
	// Remove special characters
	name = strings.ReplaceAll(name, "(", "")
	name = strings.ReplaceAll(name, ")", "")
	name = strings.ReplaceAll(name, "[", "")
	name = strings.ReplaceAll(name, "]", "")
	name = strings.ReplaceAll(name, ",", "")
	name = strings.ReplaceAll(name, ".", "")
	
	return name
}

// migrateConfidence migrates old confidence values to the new system
func migrateConfidence(overallConfidence float64, factors map[string]float64) *confidence.Confidence {
	conf := confidence.NewConfidence()
	
	// Set overall if available
	if overallConfidence > 0 {
		// Use the overall as a base for all components
		classification := overallConfidence
		position := overallConfidence
		properties := overallConfidence
		relationships := overallConfidence
		
		// Override with specific factors if available
		if factors != nil {
			if val, exists := factors["classification"]; exists {
				classification = val
			}
			if val, exists := factors["position"]; exists {
				position = val
			}
			if val, exists := factors["properties"]; exists {
				properties = val
			}
			if val, exists := factors["relationships"]; exists {
				relationships = val
			}
		}
		
		params := confidence.UpdateParams{
			Source: confidence.Source{
				Type:       confidence.SourceComputed,
				Method:     "migration",
				Confidence: overallConfidence,
				Timestamp:  time.Now(),
			},
			Classification: &classification,
			Position:       &position,
			Properties:     &properties,
			Relationships:  &relationships,
			Reason:         "Migrated from legacy confidence system",
		}
		
		conf.Update(params)
	}
	
	return conf
}

// BatchMigrate migrates multiple ArxObjects
func BatchMigrate(objects []*ArxObject) []*ArxObjectUnified {
	unified := make([]*ArxObjectUnified, len(objects))
	
	for i, obj := range objects {
		unified[i] = MigrateToUnified(obj)
	}
	
	return unified
}

// MigrationReport provides statistics about a migration
type MigrationReport struct {
	TotalObjects       int
	MigratedObjects    int
	PathsNormalized    int
	ConfidenceUpdated  int
	Errors             []string
}

// MigrateWithReport migrates objects and provides a report
func MigrateWithReport(objects []*ArxObject) ([]*ArxObjectUnified, *MigrationReport) {
	report := &MigrationReport{
		TotalObjects: len(objects),
		Errors:       []string{},
	}
	
	unified := make([]*ArxObjectUnified, 0, len(objects))
	
	for _, obj := range objects {
		// Track original state
		hadConfidence := obj.Confidence > 0 || len(obj.ConfidenceFactors) > 0
		
		// Migrate
		newObj := MigrateToUnified(obj)
		
		if newObj != nil {
			unified = append(unified, newObj)
			report.MigratedObjects++
			
			// Track what was updated
			report.PathsNormalized++
			if hadConfidence {
				report.ConfidenceUpdated++
			}
		} else {
			report.Errors = append(report.Errors, 
				fmt.Sprintf("Failed to migrate object %s", obj.ID))
		}
	}
	
	return unified, report
}