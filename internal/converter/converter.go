package converter

import (
	"fmt"
	"io"
	"os"
	"strings"
)

// Converter interface for all file format converters
type Converter interface {
	CanConvert(filename string) bool
	ConvertToBIM(input io.Reader, output io.Writer) error
	ConvertFromBIM(input io.Reader, output io.Writer) error
	GetFormat() string
	GetDescription() string
}

// ConverterRegistry manages all available converters
type ConverterRegistry struct {
	converters map[string]Converter
}

// NewRegistry creates a new converter registry
func NewRegistry() *ConverterRegistry {
	r := &ConverterRegistry{
		converters: make(map[string]Converter),
	}
	
	// Register working converters only
	r.Register(NewImprovedIFCConverter())
	r.Register(NewRealPDFConverter())
	
	return r
}

// Register adds a converter to the registry
func (r *ConverterRegistry) Register(c Converter) {
	r.converters[c.GetFormat()] = c
}

// GetConverter finds the appropriate converter for a file
func (r *ConverterRegistry) GetConverter(filename string) (Converter, error) {
	// Check each converter
	for _, conv := range r.converters {
		if conv.CanConvert(filename) {
			return conv, nil
		}
	}

	return nil, fmt.Errorf("no converter found for %s", filename)
}

// ConvertFile converts any supported format to BIM
func (r *ConverterRegistry) ConvertFile(inputPath, outputPath string) error {
	// Validate input file before processing
	if err := ValidateBeforeConversion(inputPath); err != nil {
		return fmt.Errorf("input validation failed: %w", err)
	}

	conv, err := r.GetConverter(inputPath)
	if err != nil {
		return err
	}

	// Open input file
	input, err := os.Open(inputPath)
	if err != nil {
		return fmt.Errorf("failed to open input: %w", err)
	}
	defer input.Close()

	// Create output file
	output, err := os.Create(outputPath)
	if err != nil {
		return fmt.Errorf("failed to create output: %w", err)
	}
	defer output.Close()

	// Convert
	return conv.ConvertToBIM(input, output)
}

// Building represents the universal building data model
type Building struct {
	ID          string      `json:"id"`
	Name        string      `json:"name"`
	Address     string      `json:"address"`
	Metadata    Metadata    `json:"metadata"`
	Floors      []Floor     `json:"floors"`
	Systems     []System    `json:"systems"`
	Documents   []Document  `json:"documents"`
}

type Metadata struct {
	Source      string            `json:"source"`
	Format      string            `json:"format"`
	Version     string            `json:"version"`
	Timestamp   string            `json:"timestamp"`
	Coordinates *GeoCoordinates   `json:"coordinates,omitempty"`
	Properties  map[string]string `json:"properties,omitempty"`
}

type Floor struct {
	ID        string     `json:"id"`
	Name      string     `json:"name"`
	Level     int        `json:"level"`
	Elevation float64    `json:"elevation"`
	Area      float64    `json:"area"`
	Height    float64    `json:"height"`
	Rooms     []Room     `json:"rooms"`
}

type Room struct {
	ID         string      `json:"id"`
	Name       string      `json:"name"`
	Number     string      `json:"number"`
	Type       string      `json:"type"`
	Area       float64     `json:"area"`
	Occupancy  int         `json:"occupancy"`
	Equipment  []Equipment `json:"equipment"`
	Geometry   *Geometry   `json:"geometry,omitempty"`
}

type Equipment struct {
	ID           string            `json:"id"`
	Tag          string            `json:"tag"`
	Name         string            `json:"name"`
	Type         string            `json:"type"`
	Category     string            `json:"category"`
	Manufacturer string            `json:"manufacturer"`
	Model        string            `json:"model"`
	Serial       string            `json:"serial"`
	Status       string            `json:"status"`
	Location     Location          `json:"location"`
	Properties   map[string]string `json:"properties"`
	Points       []Point           `json:"points,omitempty"`
}

type System struct {
	ID          string      `json:"id"`
	Name        string      `json:"name"`
	Type        string      `json:"type"`
	Description string      `json:"description"`
	Components  []string    `json:"components"` // Equipment IDs
}

type Document struct {
	ID          string   `json:"id"`
	Title       string   `json:"title"`
	Type        string   `json:"type"`
	Path        string   `json:"path"`
	Format      string   `json:"format"`
	Tags        []string `json:"tags"`
	RelatedTo   []string `json:"related_to"` // Equipment/Room IDs
}

type Location struct {
	Floor  string  `json:"floor"`
	Room   string  `json:"room"`
	X      float64 `json:"x,omitempty"`
	Y      float64 `json:"y,omitempty"`
	Z      float64 `json:"z,omitempty"`
}

type Geometry struct {
	Type        string      `json:"type"` // polygon, mesh, point-cloud
	Coordinates interface{} `json:"coordinates"`
	Bounds      *Bounds     `json:"bounds,omitempty"`
}

type Bounds struct {
	MinX float64 `json:"min_x"`
	MinY float64 `json:"min_y"`
	MinZ float64 `json:"min_z"`
	MaxX float64 `json:"max_x"`
	MaxY float64 `json:"max_y"`
	MaxZ float64 `json:"max_z"`
}

type GeoCoordinates struct {
	Latitude  float64 `json:"latitude"`
	Longitude float64 `json:"longitude"`
	Altitude  float64 `json:"altitude,omitempty"`
	CRS       string  `json:"crs,omitempty"` // Coordinate Reference System
}

type Point struct {
	ID       string            `json:"id"`
	Name     string            `json:"name"`
	Type     string            `json:"type"` // sensor, setpoint, command, status
	Unit     string            `json:"unit"`
	Value    interface{}       `json:"value,omitempty"`
	Tags     map[string]string `json:"tags,omitempty"` // Haystack tags
}

// ToBIM converts the universal model to BIM text format
func (b *Building) ToBIM() string {
	var sb strings.Builder
	
	// Header
	sb.WriteString("# ArxOS Building Information Model\n")
	if b.ID != "" {
		sb.WriteString(fmt.Sprintf("# Building: %s\n", b.ID))
	}
	if b.Name != "" {
		sb.WriteString(fmt.Sprintf("# Name: %s\n", b.Name))
	}
	if b.Address != "" {
		sb.WriteString(fmt.Sprintf("# Address: %s\n", b.Address))
	}
	if b.Metadata.Source != "" {
		sb.WriteString(fmt.Sprintf("# Source: %s (%s)\n", b.Metadata.Source, b.Metadata.Format))
	}
	sb.WriteString("\n")
	
	// Floors
	if len(b.Floors) > 0 {
		sb.WriteString("## FLOORS\n")
		for _, floor := range b.Floors {
			sb.WriteString(fmt.Sprintf("FLOOR %s \"%s\" %.1f\n", 
				floor.ID, floor.Name, floor.Elevation))
		}
		sb.WriteString("\n")
	}
	
	// Rooms
	if hasRooms(b) {
		sb.WriteString("## ROOMS\n")
		for _, floor := range b.Floors {
			for _, room := range floor.Rooms {
				sb.WriteString(fmt.Sprintf("ROOM %s/%s \"%s\" %s %.1f\n",
					floor.ID, room.Number, room.Name, room.Type, room.Area))
			}
		}
		sb.WriteString("\n")
	}
	
	// Equipment
	if hasEquipment(b) {
		sb.WriteString("## EQUIPMENT\n")
		for _, floor := range b.Floors {
			for _, room := range floor.Rooms {
				for _, eq := range room.Equipment {
					sb.WriteString(fmt.Sprintf("EQUIPMENT %s/%s/%s \"%s\" %s %s\n",
						floor.ID, room.Number, eq.Tag, eq.Name, eq.Type, eq.Status))
				}
			}
		}
		sb.WriteString("\n")
	}
	
	// Systems
	if len(b.Systems) > 0 {
		sb.WriteString("## SYSTEMS\n")
		for _, sys := range b.Systems {
			sb.WriteString(fmt.Sprintf("SYSTEM %s \"%s\" %s\n", sys.ID, sys.Name, sys.Type))
			for _, comp := range sys.Components {
				sb.WriteString(fmt.Sprintf("  COMPONENT %s\n", comp))
			}
		}
		sb.WriteString("\n")
	}
	
	// Documents
	if len(b.Documents) > 0 {
		sb.WriteString("## DOCUMENTS\n")
		for _, doc := range b.Documents {
			sb.WriteString(fmt.Sprintf("DOCUMENT \"%s\" %s %s\n", 
				doc.Title, doc.Type, doc.Path))
		}
	}
	
	return sb.String()
}

func hasRooms(b *Building) bool {
	for _, floor := range b.Floors {
		if len(floor.Rooms) > 0 {
			return true
		}
	}
	return false
}

func hasEquipment(b *Building) bool {
	for _, floor := range b.Floors {
		for _, room := range floor.Rooms {
			if len(room.Equipment) > 0 {
				return true
			}
		}
	}
	return false
}

// ValidateBuilding checks the building data for completeness and quality
func (b *Building) Validate() []string {
	var issues []string

	// Basic building info
	if b.Name == "" {
		issues = append(issues, "Building name is missing")
	}
	if len(b.Floors) == 0 {
		issues = append(issues, "No floors defined")
	}

	// Floor validation
	for i, floor := range b.Floors {
		if floor.ID == "" {
			issues = append(issues, fmt.Sprintf("Floor %d is missing ID", i+1))
		}
		if floor.Name == "" {
			issues = append(issues, fmt.Sprintf("Floor %d (%s) is missing name", i+1, floor.ID))
		}
		if len(floor.Rooms) == 0 {
			issues = append(issues, fmt.Sprintf("Floor %d (%s) has no rooms", i+1, floor.Name))
		}

		// Room validation
		for j, room := range floor.Rooms {
			if room.Number == "" && room.Name == "" {
				issues = append(issues, fmt.Sprintf("Room %d on floor %s has no number or name", j+1, floor.Name))
			}
			if room.Type == "" {
				issues = append(issues, fmt.Sprintf("Room %s on floor %s has no type", room.Number, floor.Name))
			}

			// Equipment validation
			for k, eq := range room.Equipment {
				if eq.Tag == "" && eq.Name == "" {
					issues = append(issues, fmt.Sprintf("Equipment %d in room %s has no tag or name", k+1, room.Number))
				}
				if eq.Type == "" {
					issues = append(issues, fmt.Sprintf("Equipment %s in room %s has no type", eq.Tag, room.Number))
				}
			}
		}
	}

	// Check for duplicate room numbers within floors
	for _, floor := range b.Floors {
		roomNumbers := make(map[string]bool)
		for _, room := range floor.Rooms {
			if room.Number != "" {
				if roomNumbers[room.Number] {
					issues = append(issues, fmt.Sprintf("Duplicate room number %s on floor %s", room.Number, floor.Name))
				}
				roomNumbers[room.Number] = true
			}
		}
	}

	return issues
}