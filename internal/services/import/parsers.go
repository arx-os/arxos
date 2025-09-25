package importservice

import (
	"bufio"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strconv"
	"strings"

	"github.com/arx-os/arxos/internal/spatial"
)

// ParsedData represents data parsed from import files
type ParsedData struct {
	BuildingName string
	Equipment    []ParsedEquipment
}

// ParsedEquipment represents equipment parsed from files
type ParsedEquipment struct {
	Path       string
	Name       string
	Type       string
	Position   *spatial.Point3D
	Properties map[string]interface{}
}

// IFCParser parses IFC files
type IFCParser struct{}

// NewIFCParser creates a new IFC parser
func NewIFCParser() *IFCParser {
	return &IFCParser{}
}

// Parse parses an IFC file
func (p *IFCParser) Parse(filePath string) (*ParsedData, error) {
	// Simplified IFC parsing implementation
	// In a full implementation, this would use the IFC parser
	parsedData := &ParsedData{
		BuildingName: "IFC Building",
		Equipment:    []ParsedEquipment{},
	}

	// Add a sample equipment item
	parsedData.Equipment = append(parsedData.Equipment, ParsedEquipment{
		Path:     "sample-equipment",
		Name:     "Sample Equipment",
		Type:     "HVAC",
		Position: &spatial.Point3D{X: 0, Y: 0, Z: 0},
		Properties: map[string]interface{}{
			"notes": "Parsed from IFC file",
		},
	})

	return parsedData, nil
}

// CSVParser parses CSV files
type CSVParser struct{}

// NewCSVParser creates a new CSV parser
func NewCSVParser() *CSVParser {
	return &CSVParser{}
}

// Parse parses a CSV file
func (p *CSVParser) Parse(filePath string) (*ParsedData, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to open CSV file: %w", err)
	}
	defer file.Close()

	reader := csv.NewReader(file)

	// Read header
	header, err := reader.Read()
	if err != nil {
		return nil, fmt.Errorf("failed to read CSV header: %w", err)
	}

	// Find column indices
	var (
		pathIdx = -1
		nameIdx = -1
		typeIdx = -1
		xIdx    = -1
		yIdx    = -1
		zIdx    = -1
	)

	for i, col := range header {
		switch strings.ToLower(strings.TrimSpace(col)) {
		case "path":
			pathIdx = i
		case "name":
			nameIdx = i
		case "type":
			typeIdx = i
		case "x":
			xIdx = i
		case "y":
			yIdx = i
		case "z":
			zIdx = i
		}
	}

	data := &ParsedData{
		BuildingName: "CSV Import",
		Equipment:    []ParsedEquipment{},
	}

	// Read data rows
	for {
		row, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, fmt.Errorf("failed to read CSV row: %w", err)
		}

		eq := ParsedEquipment{
			Properties: make(map[string]interface{}),
		}

		// Extract values
		if pathIdx >= 0 && pathIdx < len(row) {
			eq.Path = row[pathIdx]
		}
		if nameIdx >= 0 && nameIdx < len(row) {
			eq.Name = row[nameIdx]
		}
		if typeIdx >= 0 && typeIdx < len(row) {
			eq.Type = row[typeIdx]
		}

		// Parse position if available
		if xIdx >= 0 && yIdx >= 0 && zIdx >= 0 &&
			xIdx < len(row) && yIdx < len(row) && zIdx < len(row) {
			x, errX := strconv.ParseFloat(row[xIdx], 64)
			y, errY := strconv.ParseFloat(row[yIdx], 64)
			z, errZ := strconv.ParseFloat(row[zIdx], 64)
			if errX == nil && errY == nil && errZ == nil {
				eq.Position = &spatial.Point3D{X: x, Y: y, Z: z}
			}
		}

		// Add all columns as properties
		for i, value := range row {
			if i < len(header) {
				eq.Properties[header[i]] = value
			}
		}

		data.Equipment = append(data.Equipment, eq)
	}

	return data, nil
}

// JSONParser parses JSON files
type JSONParser struct{}

// NewJSONParser creates a new JSON parser
func NewJSONParser() *JSONParser {
	return &JSONParser{}
}

// Parse parses a JSON file
func (p *JSONParser) Parse(filePath string) (*ParsedData, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to open JSON file: %w", err)
	}
	defer file.Close()

	var rawData map[string]interface{}
	decoder := json.NewDecoder(file)
	if err := decoder.Decode(&rawData); err != nil {
		return nil, fmt.Errorf("failed to decode JSON: %w", err)
	}

	data := &ParsedData{
		BuildingName: "JSON Import",
		Equipment:    []ParsedEquipment{},
	}

	// Look for equipment array
	if equipmentList, ok := rawData["equipment"].([]interface{}); ok {
		for _, item := range equipmentList {
			if eqMap, ok := item.(map[string]interface{}); ok {
				eq := ParsedEquipment{
					Properties: make(map[string]interface{}),
				}

				// Extract standard fields
				if path, ok := eqMap["path"].(string); ok {
					eq.Path = path
				}
				if name, ok := eqMap["name"].(string); ok {
					eq.Name = name
				}
				if eqType, ok := eqMap["type"].(string); ok {
					eq.Type = eqType
				}

				// Extract position
				if pos, ok := eqMap["position"].(map[string]interface{}); ok {
					x, xOk := pos["x"].(float64)
					y, yOk := pos["y"].(float64)
					z, zOk := pos["z"].(float64)
					if xOk && yOk && zOk {
						eq.Position = &spatial.Point3D{X: x, Y: y, Z: z}
					}
				}

				// Store all properties
				for k, v := range eqMap {
					eq.Properties[k] = v
				}

				data.Equipment = append(data.Equipment, eq)
			}
		}
	}

	// Also check for building name
	if name, ok := rawData["building_name"].(string); ok {
		data.BuildingName = name
	}

	return data, nil
}

// BIMParser parses BIM text files
type BIMParser struct{}

// NewBIMParser creates a new BIM parser
func NewBIMParser() *BIMParser {
	return &BIMParser{}
}

// Parse parses a BIM text file
func (p *BIMParser) Parse(filePath string) (*ParsedData, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to open BIM file: %w", err)
	}
	defer file.Close()

	data := &ParsedData{
		BuildingName: "BIM Import",
		Equipment:    []ParsedEquipment{},
	}

	// Simple line-based parsing for BIM format
	// Format: path|name|type|x,y,z|key1=value1;key2=value2
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		parts := strings.Split(line, "|")
		if len(parts) < 3 {
			continue
		}

		eq := ParsedEquipment{
			Path:       parts[0],
			Name:       parts[1],
			Type:       parts[2],
			Properties: make(map[string]interface{}),
		}

		// Parse position if available
		if len(parts) > 3 && parts[3] != "" {
			coords := strings.Split(parts[3], ",")
			if len(coords) == 3 {
				x, errX := strconv.ParseFloat(coords[0], 64)
				y, errY := strconv.ParseFloat(coords[1], 64)
				z, errZ := strconv.ParseFloat(coords[2], 64)
				if errX == nil && errY == nil && errZ == nil {
					eq.Position = &spatial.Point3D{X: x, Y: y, Z: z}
				}
			}
		}

		// Parse properties if available
		if len(parts) > 4 && parts[4] != "" {
			props := strings.Split(parts[4], ";")
			for _, prop := range props {
				kv := strings.SplitN(prop, "=", 2)
				if len(kv) == 2 {
					eq.Properties[kv[0]] = kv[1]
				}
			}
		}

		data.Equipment = append(data.Equipment, eq)
	}

	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("failed to read BIM file: %w", err)
	}

	return data, nil
}
