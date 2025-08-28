package ingestion

import "time"

// PDFExtractionOptions configures PDF extraction
type PDFExtractionOptions struct {
	ExtractText      bool   `json:"extract_text"`
	ExtractImages    bool   `json:"extract_images"`
	ExtractTables    bool   `json:"extract_tables"`
	DetectFloorPlans bool   `json:"detect_floor_plans"`
	DPI              int    `json:"dpi"`
	OutputFormat     string `json:"output_format"`
}

// PDFExtractionResult contains PDF extraction results
type PDFExtractionResult struct {
	DocumentID string             `json:"document_id"`
	Metadata   DocumentMetadata   `json:"metadata"`
	Pages      []Page            `json:"pages"`
	FloorPlans []FloorPlan       `json:"floor_plans"`
	Confidence float32           `json:"confidence"`
	Warnings   []string          `json:"warnings"`
}

// DocumentMetadata contains document information
type DocumentMetadata struct {
	Title        string            `json:"title"`
	Author       string            `json:"author"`
	CreationDate string            `json:"creation_date"`
	PageCount    int               `json:"page_count"`
	DocumentType string            `json:"document_type"`
	Properties   map[string]string `json:"properties"`
}

// Page represents a document page
type Page struct {
	PageNumber  int              `json:"page_number"`
	TextContent string           `json:"text_content"`
	TextBlocks  []TextBlock      `json:"text_blocks"`
	Images      []ExtractedImage `json:"images"`
	Tables      []Table          `json:"tables"`
}

// TextBlock represents a text region
type TextBlock struct {
	Text      string  `json:"text"`
	Font      string  `json:"font"`
	FontSize  float32 `json:"font_size"`
	BlockType string  `json:"block_type"`
}

// ExtractedImage represents an extracted image
type ExtractedImage struct {
	Data      []byte `json:"data"`
	Format    string `json:"format"`
	Caption   string `json:"caption"`
	ImageType string `json:"image_type"`
}

// Table represents an extracted table
type Table struct {
	Rows    []TableRow `json:"rows"`
	Caption string     `json:"caption"`
}

// TableRow represents a table row
type TableRow struct {
	Cells []TableCell `json:"cells"`
}

// TableCell represents a table cell
type TableCell struct {
	Text    string `json:"text"`
	ColSpan int    `json:"col_span"`
	RowSpan int    `json:"row_span"`
}

// WallDetectionOptions configures wall detection
type WallDetectionOptions struct {
	ImageFormat      string  `json:"image_format"`
	MinWallThickness float32 `json:"min_wall_thickness"`
	MaxWallThickness float32 `json:"max_wall_thickness"`
	DetectDoors      bool    `json:"detect_doors"`
	DetectWindows    bool    `json:"detect_windows"`
	DetectColumns    bool    `json:"detect_columns"`
	Units            string  `json:"units"`
}

// WallDetectionResult contains wall detection results
type WallDetectionResult struct {
	Walls      []Wall     `json:"walls"`
	Doors      []Door     `json:"doors"`
	Windows    []Window   `json:"windows"`
	Columns    []Column   `json:"columns"`
	Rooms      []Room     `json:"rooms"`
	FloorPlan  *FloorPlan `json:"floor_plan"`
	Confidence float32    `json:"confidence"`
}

// Wall represents a detected wall
type Wall struct {
	ID        string  `json:"id"`
	StartX    float32 `json:"start_x"`
	StartY    float32 `json:"start_y"`
	EndX      float32 `json:"end_x"`
	EndY      float32 `json:"end_y"`
	Thickness float32 `json:"thickness"`
	Material  string  `json:"material"`
	WallType  string  `json:"wall_type"`
	Height    float32 `json:"height"`
}

// Door represents a detected door
type Door struct {
	ID              string  `json:"id"`
	X               float32 `json:"x"`
	Y               float32 `json:"y"`
	Width           float32 `json:"width"`
	Height          float32 `json:"height"`
	SwingAngle      float32 `json:"swing_angle"`
	DoorType        string  `json:"door_type"`
	ConnectedWallID string  `json:"connected_wall_id"`
}

// Window represents a detected window
type Window struct {
	ID              string  `json:"id"`
	X               float32 `json:"x"`
	Y               float32 `json:"y"`
	Width           float32 `json:"width"`
	Height          float32 `json:"height"`
	SillHeight      float32 `json:"sill_height"`
	WindowType      string  `json:"window_type"`
	ConnectedWallID string  `json:"connected_wall_id"`
}

// Column represents a detected column
type Column struct {
	ID       string  `json:"id"`
	X        float32 `json:"x"`
	Y        float32 `json:"y"`
	Radius   float32 `json:"radius"`
	Width    float32 `json:"width"`
	Height   float32 `json:"height"`
	Material string  `json:"material"`
}

// Room represents a detected room
type Room struct {
	ID               string    `json:"id"`
	Name             string    `json:"name"`
	RoomType         string    `json:"room_type"`
	Boundary         []Point2D `json:"boundary"`
	Area             float32   `json:"area"`
	Height           float32   `json:"height"`
	AdjacentRoomIDs  []string  `json:"adjacent_room_ids"`
	Properties       map[string]string `json:"properties"`
}

// Point2D represents a 2D point
type Point2D struct {
	X float32 `json:"x"`
	Y float32 `json:"y"`
}

// Point3D represents a 3D point
type Point3D struct {
	X float32 `json:"x"`
	Y float32 `json:"y"`
	Z float32 `json:"z"`
}

// FloorPlan represents a floor plan
type FloorPlan struct {
	ID            string  `json:"id"`
	FloorName     string  `json:"floor_name"`
	FloorNumber   int     `json:"floor_number"`
	Scale         float32 `json:"scale"`
	Rotation      float32 `json:"rotation"`
	NorthDirection Point2D `json:"north_direction"`
}

// BIMGenerationRequest configures BIM generation
type BIMGenerationRequest struct {
	FloorPlan *FloorPlan `json:"floor_plan"`
	Walls     []Wall     `json:"walls"`
	Doors     []Door     `json:"doors"`
	Windows   []Window   `json:"windows"`
	Rooms     []Room     `json:"rooms"`
	Options   BIMOptions `json:"options"`
}

// BIMOptions contains BIM generation options
type BIMOptions struct {
	DefaultFloorHeight float32 `json:"default_floor_height"`
	DefaultWallHeight  float32 `json:"default_wall_height"`
	GenerateCeiling    bool    `json:"generate_ceiling"`
	GenerateRoof       bool    `json:"generate_roof"`
	CoordinateSystem   string  `json:"coordinate_system"`
	LevelOfDetail      int     `json:"level_of_detail"`
}

// BIMGenerationResult contains BIM generation results
type BIMGenerationResult struct {
	ModelID    string       `json:"model_id"`
	ModelName  string       `json:"model_name"`
	IFCVersion string       `json:"ifc_version"`
	IFCData    []byte       `json:"ifc_data"`
	GLTFData   string       `json:"gltf_data"`
	Elements   []BIMElement `json:"elements"`
	Spaces     []BIMSpace   `json:"spaces"`
	Confidence float32      `json:"confidence"`
	Warnings   []string     `json:"warnings"`
}

// BIMElement represents a BIM element
type BIMElement struct {
	ID         string            `json:"id"`
	IFCClass   string            `json:"ifc_class"`
	Name       string            `json:"name"`
	Properties map[string]string `json:"properties"`
	Transform  Transform3D       `json:"transform"`
	MaterialID string            `json:"material_id"`
}

// Transform3D represents 3D transformation
type Transform3D struct {
	Position Point3D `json:"position"`
	Rotation Point3D `json:"rotation"`
	Scale    Point3D `json:"scale"`
}

// BIMSpace represents a BIM space
type BIMSpace struct {
	ID                  string   `json:"id"`
	Name                string   `json:"name"`
	SpaceType           string   `json:"space_type"`
	Area                float32  `json:"area"`
	Volume              float32  `json:"volume"`
	BoundaryElementIDs  []string `json:"boundary_element_ids"`
}

// ProcessingStatus represents processing status
type ProcessingStatus struct {
	SessionID        string        `json:"session_id"`
	Status           string        `json:"status"`
	Progress         float32       `json:"progress"`
	CurrentStage     string        `json:"current_stage"`
	Message          string        `json:"message"`
	StartedAt        time.Time     `json:"started_at"`
	UpdatedAt        time.Time     `json:"updated_at"`
	CompletedStages  []string      `json:"completed_stages"`
	PendingStages    []string      `json:"pending_stages"`
	Result           interface{}   `json:"result"`
}

// MeasurementRequest contains measurement extraction parameters
type MeasurementRequest struct {
	ImageData []byte                `json:"image_data"`
	Walls     []Wall                `json:"walls"`
	Options   MeasurementOptions    `json:"options"`
}

// MeasurementOptions configures measurement extraction
type MeasurementOptions struct {
	ExtractDimensions bool   `json:"extract_dimensions"`
	ExtractAnnotations bool   `json:"extract_annotations"`
	ExtractScale      bool   `json:"extract_scale"`
	DefaultUnits      string `json:"default_units"`
}

// MeasurementResult contains measurement extraction results
type MeasurementResult struct {
	Dimensions []Dimension `json:"dimensions"`
	Annotations []Annotation `json:"annotations"`
	Scale      *Scale      `json:"scale"`
	Confidence float32     `json:"confidence"`
}

// Dimension represents a measurement dimension
type Dimension struct {
	ID                   string  `json:"id"`
	StartPoint           Point2D `json:"start_point"`
	EndPoint             Point2D `json:"end_point"`
	Value                float32 `json:"value"`
	Units                string  `json:"units"`
	DimensionType        string  `json:"dimension_type"`
	AssociatedElementID  string  `json:"associated_element_id"`
}

// Annotation represents a drawing annotation
type Annotation struct {
	Text                string  `json:"text"`
	Position            Point2D `json:"position"`
	AnnotationType      string  `json:"annotation_type"`
	AssociatedElementID string  `json:"associated_element_id"`
}

// Scale represents drawing scale
type Scale struct {
	PixelsPerUnit float32 `json:"pixels_per_unit"`
	Units         string  `json:"units"`
	Confidence    float32 `json:"confidence"`
}