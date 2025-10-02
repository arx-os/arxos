package ifc

import (
	"bufio"
	"fmt"
	"io"
	"regexp"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/domain/building"
)

// IFCParser parses IFC files and converts them to domain models
type IFCParser struct {
	// Simple regex patterns for IFC parsing
	entityPattern   *regexp.Regexp
	propertyPattern *regexp.Regexp
}

// NewIFCParser creates a new IFC parser
func NewIFCParser() *IFCParser {
	return &IFCParser{
		entityPattern:   regexp.MustCompile(`#(\d+)=IFC[A-Z]+\([^)]*\)`),
		propertyPattern: regexp.MustCompile(`'([^']*)'`),
	}
}

// ParseIFC parses an IFC file and returns domain models
func (p *IFCParser) ParseIFC(reader io.Reader) (*building.IFCBuilding, error) {
	scanner := bufio.NewScanner(reader)

	var entities []building.IFCEntity
	var properties []building.IFCProperty
	var materials []building.IFCMaterial
	var classifications []building.IFCClassification

	entityCount := 0
	propertyCount := 0
	materialCount := 0
	classificationCount := 0

	// Simple parsing - count entities and extract basic information
	for scanner.Scan() {
		line := scanner.Text()

		// Count entities
		if strings.Contains(line, "=IFC") {
			entityCount++

			// Extract entity type
			if strings.Contains(line, "IFCWALL") {
				// Parse wall entity
				entity := building.IFCEntity{
					ID:          fmt.Sprintf("wall_%d", entityCount),
					Type:        "IfcWall",
					Name:        fmt.Sprintf("Wall %d", entityCount),
					Description: "Building wall element",
					CreatedAt:   time.Now(),
				}
				entities = append(entities, entity)
			} else if strings.Contains(line, "IFCDOOR") {
				// Parse door entity
				entity := building.IFCEntity{
					ID:          fmt.Sprintf("door_%d", entityCount),
					Type:        "IfcDoor",
					Name:        fmt.Sprintf("Door %d", entityCount),
					Description: "Building door element",
					CreatedAt:   time.Now(),
				}
				entities = append(entities, entity)
			} else if strings.Contains(line, "IFCWINDOW") {
				// Parse window entity
				entity := building.IFCEntity{
					ID:          fmt.Sprintf("window_%d", entityCount),
					Type:        "IfcWindow",
					Name:        fmt.Sprintf("Window %d", entityCount),
					Description: "Building window element",
					CreatedAt:   time.Now(),
				}
				entities = append(entities, entity)
			}
		}

		// Count properties
		if strings.Contains(line, "IFCPROPERTY") {
			propertyCount++
			prop := building.IFCProperty{
				ID:          fmt.Sprintf("prop_%d", propertyCount),
				Name:        fmt.Sprintf("Property %d", propertyCount),
				Value:       "Sample Value",
				Type:        "String",
				Description: "Sample property",
				CreatedAt:   time.Now(),
			}
			properties = append(properties, prop)
		}

		// Count materials
		if strings.Contains(line, "IFCMATERIAL") {
			materialCount++
			material := building.IFCMaterial{
				ID:   fmt.Sprintf("mat_%d", materialCount),
				Name: fmt.Sprintf("Material %d", materialCount),
				Type: "Generic",
			}
			materials = append(materials, material)
		}

		// Count classifications
		if strings.Contains(line, "IFCCLASSIFICATION") {
			classificationCount++
			classification := building.IFCClassification{
				ID:          fmt.Sprintf("class_%d", classificationCount),
				System:      "Generic",
				Code:        fmt.Sprintf("CLS_%d", classificationCount),
				Description: fmt.Sprintf("Classification %d", classificationCount),
				CreatedAt:   time.Now(),
			}
			classifications = append(classifications, classification)
		}
	}

	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("failed to scan IFC file: %w", err)
	}

	// Create IFC building
	ifcBuilding := &building.IFCBuilding{
		ID:              fmt.Sprintf("ifc_%d", time.Now().UnixNano()),
		Name:            "Parsed IFC Building",
		Version:         "4.0",
		Discipline:      "architectural",
		Entities:        entities,
		Properties:      properties,
		Materials:       materials,
		Classifications: classifications,
		CreatedAt:       time.Now(),
		UpdatedAt:       time.Now(),
	}

	return ifcBuilding, nil
}

// CountEntities counts different types of entities in an IFC file
func (p *IFCParser) CountEntities(reader io.Reader) (map[string]int, error) {
	scanner := bufio.NewScanner(reader)
	counts := make(map[string]int)

	for scanner.Scan() {
		line := scanner.Text()

		if strings.Contains(line, "=IFCWALL") {
			counts["walls"]++
		} else if strings.Contains(line, "=IFCDOOR") {
			counts["doors"]++
		} else if strings.Contains(line, "=IFCWINDOW") {
			counts["windows"]++
		} else if strings.Contains(line, "=IFCSLAB") {
			counts["slabs"]++
		} else if strings.Contains(line, "=IFCBEAM") {
			counts["beams"]++
		} else if strings.Contains(line, "=IFCCOLUMN") {
			counts["columns"]++
		} else if strings.Contains(line, "=IFC") {
			counts["total"]++
		}
	}

	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("failed to scan IFC file: %w", err)
	}

	return counts, nil
}
