// Package types defines core data structures for PDF architectural parsing
package types

import "io"

// Document represents a parsed PDF document
type Document struct {
	Version   string
	Objects   map[int]*PDFObject
	Images    []*EmbeddedImage
	Text      string
	Metadata  DocumentMetadata
}

type DocumentMetadata struct {
	Creator     string
	CreatedAt   string
	Title       string
	PageCount   int
	FileSize    int64
}

// PDFObject represents a single PDF object
type PDFObject struct {
	ID         int
	Generation int
	Data       []byte
	Type       string
	Filters    []string
}

// EmbeddedImage represents an image embedded in the PDF
type EmbeddedImage struct {
	ObjectID         int
	Width            int
	Height           int
	BitsPerComponent int
	ColorSpace       string
	Filter           string
	RawData          []byte
	DecodedData      []byte
}

// Edge represents a detected edge in image processing
type Edge struct {
	X, Y      int
	Strength  float64
	Direction float64
}

// Line represents a line segment extracted from edges
type Line struct {
	X1, Y1, X2, Y2 int
	Length         float64
	Angle          float64
	Weight         float64
}

// Point represents a 2D coordinate
type Point struct {
	X, Y int
}

// Rect represents a rectangle
type Rect struct {
	X, Y, Width, Height int
}

// Size represents dimensions
type Size struct {
	Width, Height int
}

// Campus represents a complete building campus
type Campus struct {
	Name      string
	Buildings []Building
	IDFRooms  []IDFLocation
	Bounds    Rect
	Scale     float64
	Method    string // "vector", "image", "text", "hybrid"
}

// Building represents a single building structure
type Building struct {
	Name      string
	Bounds    Rect
	Rooms     []Room
	Hallways  []Hallway
	Entrances []Point
}

// Room represents a single room
type Room struct {
	Number      string
	Bounds      Rect
	Type        RoomType
	Doors       []Point
	Area        float64
	Equipment   []string
}

// Hallway represents a corridor or hallway
type Hallway struct {
	Path   []Point
	Width  int
	Length float64
}

// IDFLocation represents an IDF (Intermediate Distribution Frame) location
type IDFLocation struct {
	ID          string
	Position    Point
	Size        Size
	Equipment   []string
	RoomNumber  string
	Highlighted bool
}

// RoomType represents the type of room
type RoomType int

const (
	Unknown RoomType = iota
	Classroom
	Office
	IDF
	Utility
	Storage
	Restroom
	HallwayType
	Entrance
	MDF // Main Distribution Frame
)

func (rt RoomType) String() string {
	switch rt {
	case Classroom:
		return "classroom"
	case Office:
		return "office"
	case IDF:
		return "idf"
	case Utility:
		return "utility"
	case Storage:
		return "storage"
	case Restroom:
		return "restroom"
	case HallwayType:
		return "hallway"
	case Entrance:
		return "entrance"
	case MDF:
		return "mdf"
	default:
		return "unknown"
	}
}

// Interfaces for modular architecture

// PDFParser handles PDF document parsing
type PDFParser interface {
	ParseFile(path string) (*Document, error)
	ParseStream(reader io.Reader) (*Document, error)
}

// ImageProcessor handles image analysis and processing
type ImageProcessor interface {
	ProcessImage(img *EmbeddedImage) (*ProcessedImage, error)
	DetectEdges(img *EmbeddedImage) ([]Edge, error)
	ExtractLines(edges []Edge) ([]Line, error)
}

// ProcessedImage represents an analyzed image
type ProcessedImage struct {
	Image    *EmbeddedImage
	Edges    []Edge
	Lines    []Line
	Features []ImageFeature
}

// ImageFeature represents a detected feature in an image
type ImageFeature struct {
	Type     string // "room", "wall", "door", "text"
	Bounds   Rect
	Metadata map[string]interface{}
}

// CampusBuilder constructs building layouts from parsed data
type CampusBuilder interface {
	ExtractCampus(doc *Document, processedImages []*ProcessedImage) (*Campus, error)
	DetectRooms(lines []Line, text string) ([]Room, error)
	DetectIDFLocations(text string, rooms []Room) ([]IDFLocation, error)
}

// Renderer handles visualization and output
type Renderer interface {
	RenderASCII(campus *Campus) (string, error)
	RenderJSON(campus *Campus) ([]byte, error)
}

// TextExtractor handles text extraction from PDFs
type TextExtractor interface {
	ExtractText(doc *Document) (string, error)
	ExtractRoomNumbers(text string) ([]string, error)
	ExtractIDFReferences(text string) ([]string, error)
}

// ParseConfig holds configuration for parsing operations
type ParseConfig struct {
	EdgeDetectionThreshold float64
	MinRoomSize           int
	MaxRoomSize           int
	TextExtractionMode    string // "comprehensive", "basic", "hybrid"
	RenderScale           float64
	Debug                 bool
}

// DefaultParseConfig returns sensible defaults
func DefaultParseConfig() *ParseConfig {
	return &ParseConfig{
		EdgeDetectionThreshold: 25.0,
		MinRoomSize:           50,
		MaxRoomSize:           1000,
		TextExtractionMode:    "comprehensive",
		RenderScale:           25.0,
		Debug:                 false,
	}
}

// ParseResult represents the complete parsing result
type ParseResult struct {
	Campus    *Campus
	Document  *Document
	Images    []*ProcessedImage
	Config    *ParseConfig
	Stats     ParseStats
	Errors    []error
	Warnings  []string
}

// ParseStats provides parsing statistics
type ParseStats struct {
	ObjectsProcessed  int
	ImagesProcessed   int
	EdgesDetected     int
	LinesExtracted    int
	RoomsDetected     int
	IDFsDetected      int
	TextCharacters    int
	ProcessingTimeMS  int64
}