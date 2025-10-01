package import

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
	ConvertToDB(input io.Reader, db interface{}) error // Direct to PostGIS import
	GetFormat() string
	GetDescription() string
}

// ConverterRegistry manages all available converters
type ConverterRegistry struct {
	converters map[string]Converter
}

// NewConverterRegistry creates a new converter registry
func NewConverterRegistry() *ConverterRegistry {
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

// UniversalBuilding represents the universal building data model
type UniversalBuilding struct {
	ID          string     `json:"id"`
	GUID        string     `json:"guid"` // Global Unique ID from IFC
	Name        string     `json:"name"`
	Description string     `json:"description"`
	Address     string     `json:"address"`
	Project     string     `json:"project"` // Project name for IFC
	Metadata    Metadata   `json:"metadata"`
	Floors      []Floor    `json:"floors"`
	Systems     []System   `json:"systems"`
	Documents   []Document `json:"documents"`
}

type Metadata struct {
	Source      string            `json:"source"`
	Version     string            `json:"version"`
	CreatedAt   string            `json:"created_at"`
	UpdatedAt   string            `json:"updated_at"`
	Author      string            `json:"author"`
	Description string            `json:"description"`
	Custom      map[string]string `json:"custom"`
}

type Floor struct {
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	Level       int       `json:"level"`
	Elevation   float64   `json:"elevation"`
	Height      float64   `json:"height"`
	Area        float64   `json:"area"`
	Spaces      []Space   `json:"spaces"`
	Equipment   []Equipment `json:"equipment"`
}

type Space struct {
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	Type        string    `json:"type"`
	Area        float64   `json:"area"`
	Volume      float64   `json:"volume"`
	Height      float64   `json:"height"`
	Perimeter   float64   `json:"perimeter"`
	Equipment   []Equipment `json:"equipment"`
}

type Equipment struct {
	ID              string                 `json:"id"`
	Name            string                 `json:"name"`
	Type            string                 `json:"type"`
	Category        string                 `json:"category"`
	Manufacturer    string                 `json:"manufacturer"`
	Model           string                 `json:"model"`
	SerialNumber    string                 `json:"serial_number"`
	Location        Location               `json:"location"`
	Specifications  map[string]interface{} `json:"specifications"`
	Connections     []Connection           `json:"connections"`
	Status          string                 `json:"status"`
	InstallationDate string                `json:"installation_date"`
	WarrantyExpiry  string                 `json:"warranty_expiry"`
}

type Location struct {
	FloorID   string  `json:"floor_id"`
	SpaceID   string  `json:"space_id"`
	X         float64 `json:"x"`
	Y         float64 `json:"y"`
	Z         float64 `json:"z"`
	Rotation  float64 `json:"rotation"`
}

type Connection struct {
	ID             string `json:"id"`
	SourceID       string `json:"source_id"`
	TargetID       string `json:"target_id"`
	ConnectionType string `json:"connection_type"`
	Media          string `json:"media"`
}

type System struct {
	ID          string      `json:"id"`
	Name        string      `json:"name"`
	Type        string      `json:"type"`
	Description string      `json:"description"`
	Equipment   []Equipment `json:"equipment"`
}

type Document struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	Type        string `json:"type"`
	Path        string `json:"path"`
	Size        int64  `json:"size"`
	CreatedAt   string `json:"created_at"`
	UpdatedAt   string `json:"updated_at"`
}

// ValidateBeforeConversion validates input file before conversion
func ValidateBeforeConversion(inputPath string) error {
	// Check if file exists
	if _, err := os.Stat(inputPath); os.IsNotExist(err) {
		return fmt.Errorf("input file does not exist: %s", inputPath)
	}

	// Check file extension
	ext := strings.ToLower(inputPath[strings.LastIndex(inputPath, "."):])
	supportedExtensions := []string{".ifc", ".pdf", ".csv", ".json", ".bim"}

	for _, supported := range supportedExtensions {
		if ext == supported {
			return nil
		}
	}

	return fmt.Errorf("unsupported file extension: %s", ext)
}

// Placeholder converter implementations
func NewImprovedIFCConverter() Converter {
	return &IFCConverter{}
}

func NewRealPDFConverter() Converter {
	return &PDFConverter{}
}

// IFCConverter implements Converter for IFC files
type IFCConverter struct{}

func (c *IFCConverter) CanConvert(filename string) bool {
	return strings.HasSuffix(strings.ToLower(filename), ".ifc")
}

func (c *IFCConverter) GetFormat() string {
	return "IFC"
}

func (c *IFCConverter) GetDescription() string {
	return "Industry Foundation Classes (IFC) converter"
}

func (c *IFCConverter) ConvertToBIM(input io.Reader, output io.Writer) error {
	// Placeholder implementation
	return fmt.Errorf("IFC conversion not implemented")
}

func (c *IFCConverter) ConvertFromBIM(input io.Reader, output io.Writer) error {
	// Placeholder implementation
	return fmt.Errorf("IFC reverse conversion not implemented")
}

func (c *IFCConverter) ConvertToDB(input io.Reader, db interface{}) error {
	// Placeholder implementation
	return fmt.Errorf("IFC to database conversion not implemented")
}

// PDFConverter implements Converter for PDF files
type PDFConverter struct{}

func (c *PDFConverter) CanConvert(filename string) bool {
	return strings.HasSuffix(strings.ToLower(filename), ".pdf")
}

func (c *PDFConverter) GetFormat() string {
	return "PDF"
}

func (c *PDFConverter) GetDescription() string {
	return "PDF document converter"
}

func (c *PDFConverter) ConvertToBIM(input io.Reader, output io.Writer) error {
	// Placeholder implementation
	return fmt.Errorf("PDF conversion not implemented")
}

func (c *PDFConverter) ConvertFromBIM(input io.Reader, output io.Writer) error {
	// Placeholder implementation
	return fmt.Errorf("PDF reverse conversion not implemented")
}

func (c *PDFConverter) ConvertToDB(input io.Reader, db interface{}) error {
	// Placeholder implementation
	return fmt.Errorf("PDF to database conversion not implemented")
}
