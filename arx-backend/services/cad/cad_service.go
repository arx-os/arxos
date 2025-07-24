package cad

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// CAD Service for Go Backend

// PrecisionLevel represents precision levels
type PrecisionLevel string

const (
	PrecisionLevelMillimeter    PrecisionLevel = "millimeter"
	PrecisionLevelSubMillimeter PrecisionLevel = "sub_millimeter"
	PrecisionLevelMicron        PrecisionLevel = "micron"
	PrecisionLevelNanometer     PrecisionLevel = "nanometer"
)

// ConstraintType represents constraint types
type ConstraintType string

const (
	ConstraintTypeDistance      ConstraintType = "distance"
	ConstraintTypeAngle         ConstraintType = "angle"
	ConstraintTypeParallel      ConstraintType = "parallel"
	ConstraintTypePerpendicular ConstraintType = "perpendicular"
	ConstraintTypeCoincident    ConstraintType = "coincident"
	ConstraintTypeTangent       ConstraintType = "tangent"
	ConstraintTypeSymmetric     ConstraintType = "symmetric"
)

// DimensionType represents dimension types
type DimensionType string

const (
	DimensionTypeLinearHorizontal DimensionType = "linear_horizontal"
	DimensionTypeLinearVertical   DimensionType = "linear_vertical"
	DimensionTypeLinearAligned    DimensionType = "linear_aligned"
	DimensionTypeRadial           DimensionType = "radial"
	DimensionTypeDiameter         DimensionType = "diameter"
	DimensionTypeAngular          DimensionType = "angular"
	DimensionTypeOrdinate         DimensionType = "ordinate"
)

// ParameterType represents parameter types
type ParameterType string

const (
	ParameterTypeLength   ParameterType = "length"
	ParameterTypeAngle    ParameterType = "angle"
	ParameterTypeRadius   ParameterType = "radius"
	ParameterTypeDiameter ParameterType = "diameter"
	ParameterTypeArea     ParameterType = "area"
	ParameterTypeVolume   ParameterType = "volume"
	ParameterTypeString   ParameterType = "string"
	ParameterTypeBoolean  ParameterType = "boolean"
	ParameterTypeInteger  ParameterType = "integer"
	ParameterTypeReal     ParameterType = "real"
)

// ViewType represents view types
type ViewType string

const (
	ViewTypeFront     ViewType = "front"
	ViewTypeTop       ViewType = "top"
	ViewTypeRight     ViewType = "right"
	ViewTypeLeft      ViewType = "left"
	ViewTypeBottom    ViewType = "bottom"
	ViewTypeBack      ViewType = "back"
	ViewTypeIsometric ViewType = "isometric"
	ViewTypeSection   ViewType = "section"
	ViewTypeDetail    ViewType = "detail"
	ViewTypeAuxiliary ViewType = "auxiliary"
)

// PrecisionPoint represents a high-precision point
type PrecisionPoint struct {
	X              float64        `json:"x"`
	Y              float64        `json:"y"`
	Z              *float64       `json:"z,omitempty"`
	PrecisionLevel PrecisionLevel `json:"precision_level"`
}

// GridConfig represents grid configuration
type GridConfig struct {
	GridType    string  `json:"grid_type"`
	SpacingX    float64 `json:"spacing_x"`
	SpacingY    float64 `json:"spacing_y"`
	OriginX     float64 `json:"origin_x"`
	OriginY     float64 `json:"origin_y"`
	Angle       float64 `json:"angle"`
	Visible     bool    `json:"visible"`
	SnapEnabled bool    `json:"snap_enabled"`
	MajorLines  int     `json:"major_lines"`
	Color       string  `json:"color"`
	MajorColor  string  `json:"major_color"`
}

// SnapConfig represents snap configuration
type SnapConfig struct {
	EnabledTypes   []string `json:"enabled_types"`
	Tolerance      float64  `json:"tolerance"`
	AngleSnap      float64  `json:"angle_snap"`
	VisualFeedback bool     `json:"visual_feedback"`
	MagneticSnap   bool     `json:"magnetic_snap"`
}

// DimensionStyleConfig represents dimension style configuration
type DimensionStyleConfig struct {
	StyleName       string   `json:"style_name"`
	TextHeight      float64  `json:"text_height"`
	TextColor       string   `json:"text_color"`
	LineColor       string   `json:"line_color"`
	LineWidth       float64  `json:"line_width"`
	ArrowSize       float64  `json:"arrow_size"`
	ExtensionOffset float64  `json:"extension_offset"`
	TextOffset      float64  `json:"text_offset"`
	Precision       int      `json:"precision"`
	Units           string   `json:"units"`
	ShowUnits       bool     `json:"show_units"`
	TolerancePlus   *float64 `json:"tolerance_plus,omitempty"`
	ToleranceMinus  *float64 `json:"tolerance_minus,omitempty"`
}

// Parameter represents a parameter
type Parameter struct {
	ParameterID    string                 `json:"parameter_id"`
	Name           string                 `json:"name"`
	ParameterType  ParameterType          `json:"parameter_type"`
	Value          interface{}            `json:"value"`
	Unit           string                 `json:"unit"`
	Description    string                 `json:"description"`
	Status         string                 `json:"status"`
	Constraints    map[string]interface{} `json:"constraints"`
	Dependencies   []string               `json:"dependencies"`
	Expressions    []string               `json:"expressions"`
	PrecisionLevel PrecisionLevel         `json:"precision_level"`
}

// Component represents an assembly component
type Component struct {
	ComponentID    string                 `json:"component_id"`
	Name           string                 `json:"name"`
	Geometry       map[string]interface{} `json:"geometry"`
	Position       PrecisionPoint         `json:"position"`
	Rotation       float64                `json:"rotation"`
	Scale          float64                `json:"scale"`
	Status         string                 `json:"status"`
	Constraints    []string               `json:"constraints"`
	ParentAssembly *string                `json:"parent_assembly,omitempty"`
	Children       []string               `json:"children"`
	Properties     map[string]interface{} `json:"properties"`
}

// AssemblyConstraint represents an assembly constraint
type AssemblyConstraint struct {
	ConstraintID   string                 `json:"constraint_id"`
	ConstraintType ConstraintType         `json:"constraint_type"`
	Component1     string                 `json:"component1"`
	Component2     string                 `json:"component2"`
	Parameters     map[string]interface{} `json:"parameters"`
	Status         string                 `json:"status"`
}

// Assembly represents an assembly
type Assembly struct {
	AssemblyID  string                 `json:"assembly_id"`
	Name        string                 `json:"name"`
	Components  map[string]Component   `json:"components"`
	Constraints []AssemblyConstraint   `json:"constraints"`
	Status      string                 `json:"status"`
	Properties  map[string]interface{} `json:"properties"`
}

// ViewConfig represents view configuration
type ViewConfig struct {
	ViewType        ViewType        `json:"view_type"`
	Projection      string          `json:"projection"`
	Scale           float64         `json:"scale"`
	Rotation        float64         `json:"rotation"`
	CenterPoint     *PrecisionPoint `json:"center_point,omitempty"`
	ViewportSize    []float64       `json:"viewport_size"`
	Margin          float64         `json:"margin"`
	ShowHiddenLines bool            `json:"show_hidden_lines"`
	ShowCenterLines bool            `json:"show_center_lines"`
	ShowDimensions  bool            `json:"show_dimensions"`
	ShowAnnotations bool            `json:"show_annotations"`
}

// DrawingView represents a drawing view
type DrawingView struct {
	ViewID      string                   `json:"view_id"`
	Name        string                   `json:"name"`
	ViewType    ViewType                 `json:"view_type"`
	Config      ViewConfig               `json:"config"`
	Geometry    map[string]interface{}   `json:"geometry"`
	Annotations []map[string]interface{} `json:"annotations"`
	Dimensions  []map[string]interface{} `json:"dimensions"`
	HiddenLines []map[string]interface{} `json:"hidden_lines"`
	CenterLines []map[string]interface{} `json:"center_lines"`
	Viewport    map[string]interface{}   `json:"viewport"`
}

// CADDrawing represents a CAD drawing
type CADDrawing struct {
	DrawingID      string                   `json:"drawing_id"`
	Name           string                   `json:"name"`
	PrecisionLevel PrecisionLevel           `json:"precision_level"`
	Components     []map[string]interface{} `json:"components"`
	Constraints    []map[string]interface{} `json:"constraints"`
	Dimensions     []map[string]interface{} `json:"dimensions"`
	Views          []string                 `json:"views"`
	Parameters     map[string]interface{}   `json:"parameters"`
	Assemblies     []map[string]interface{} `json:"assemblies"`
}

// CADSystem represents the main CAD system
type CADSystem struct {
	client  *http.Client
	baseURL string
}

// NewCADSystem creates a new CAD system
func NewCADSystem(baseURL string) *CADSystem {
	return &CADSystem{
		client:  &http.Client{Timeout: 30 * time.Second},
		baseURL: baseURL,
	}
}

// CreateNewDrawing creates a new CAD drawing
func (c *CADSystem) CreateNewDrawing(ctx context.Context, name string, precisionLevel PrecisionLevel) (*CADDrawing, error) {
	request := map[string]interface{}{
		"name":            name,
		"precision_level": precisionLevel,
	}

	resp, err := c.makeRequest(ctx, "POST", "/cad/drawing", request)
	if err != nil {
		return nil, fmt.Errorf("failed to create drawing: %w", err)
	}

	var drawing CADDrawing
	if err := json.Unmarshal(resp, &drawing); err != nil {
		return nil, fmt.Errorf("failed to unmarshal drawing: %w", err)
	}

	return &drawing, nil
}

// AddPrecisionPoint adds a precision point to the drawing
func (c *CADSystem) AddPrecisionPoint(ctx context.Context, drawingID string, x, y float64, z *float64) (*PrecisionPoint, error) {
	request := map[string]interface{}{
		"drawing_id": drawingID,
		"x":          x,
		"y":          y,
	}
	if z != nil {
		request["z"] = *z
	}

	resp, err := c.makeRequest(ctx, "POST", "/cad/point", request)
	if err != nil {
		return nil, fmt.Errorf("failed to add precision point: %w", err)
	}

	var point PrecisionPoint
	if err := json.Unmarshal(resp, &point); err != nil {
		return nil, fmt.Errorf("failed to unmarshal point: %w", err)
	}

	return &point, nil
}

// AddConstraint adds a constraint to the drawing
func (c *CADSystem) AddConstraint(ctx context.Context, drawingID string, constraintType ConstraintType, entities []string, parameters map[string]interface{}) error {
	request := map[string]interface{}{
		"drawing_id":      drawingID,
		"constraint_type": constraintType,
		"entities":        entities,
		"parameters":      parameters,
	}

	_, err := c.makeRequest(ctx, "POST", "/cad/constraint", request)
	if err != nil {
		return fmt.Errorf("failed to add constraint: %w", err)
	}

	return nil
}

// AddDimension adds a dimension to the drawing
func (c *CADSystem) AddDimension(ctx context.Context, drawingID string, dimensionType DimensionType, startPoint, endPoint PrecisionPoint, styleName string) error {
	request := map[string]interface{}{
		"drawing_id":     drawingID,
		"dimension_type": dimensionType,
		"start_point":    startPoint,
		"end_point":      endPoint,
		"style_name":     styleName,
	}

	_, err := c.makeRequest(ctx, "POST", "/cad/dimension", request)
	if err != nil {
		return fmt.Errorf("failed to add dimension: %w", err)
	}

	return nil
}

// AddParameter adds a parameter to the drawing
func (c *CADSystem) AddParameter(ctx context.Context, drawingID string, name string, parameterType ParameterType, value interface{}, unit, description string) (*Parameter, error) {
	request := map[string]interface{}{
		"drawing_id":     drawingID,
		"name":           name,
		"parameter_type": parameterType,
		"value":          value,
		"unit":           unit,
		"description":    description,
	}

	resp, err := c.makeRequest(ctx, "POST", "/cad/parameter", request)
	if err != nil {
		return nil, fmt.Errorf("failed to add parameter: %w", err)
	}

	var parameter Parameter
	if err := json.Unmarshal(resp, &parameter); err != nil {
		return nil, fmt.Errorf("failed to unmarshal parameter: %w", err)
	}

	return &parameter, nil
}

// CreateAssembly creates an assembly in the drawing
func (c *CADSystem) CreateAssembly(ctx context.Context, drawingID, name string) (*Assembly, error) {
	request := map[string]interface{}{
		"drawing_id": drawingID,
		"name":       name,
	}

	resp, err := c.makeRequest(ctx, "POST", "/cad/assembly", request)
	if err != nil {
		return nil, fmt.Errorf("failed to create assembly: %w", err)
	}

	var assembly Assembly
	if err := json.Unmarshal(resp, &assembly); err != nil {
		return nil, fmt.Errorf("failed to unmarshal assembly: %w", err)
	}

	return &assembly, nil
}

// AddComponentToAssembly adds a component to an assembly
func (c *CADSystem) AddComponentToAssembly(ctx context.Context, assemblyID string, component Component) error {
	request := map[string]interface{}{
		"assembly_id": assemblyID,
		"component":   component,
	}

	_, err := c.makeRequest(ctx, "POST", "/cad/assembly/component", request)
	if err != nil {
		return fmt.Errorf("failed to add component to assembly: %w", err)
	}

	return nil
}

// GenerateViews generates views for the drawing
func (c *CADSystem) GenerateViews(ctx context.Context, drawingID string, modelGeometry map[string]interface{}) (map[string]interface{}, error) {
	request := map[string]interface{}{
		"drawing_id":     drawingID,
		"model_geometry": modelGeometry,
	}

	resp, err := c.makeRequest(ctx, "POST", "/cad/views", request)
	if err != nil {
		return nil, fmt.Errorf("failed to generate views: %w", err)
	}

	var views map[string]interface{}
	if err := json.Unmarshal(resp, &views); err != nil {
		return nil, fmt.Errorf("failed to unmarshal views: %w", err)
	}

	return views, nil
}

// SolveConstraints solves all constraints in the drawing
func (c *CADSystem) SolveConstraints(ctx context.Context, drawingID string) error {
	request := map[string]interface{}{
		"drawing_id": drawingID,
	}

	_, err := c.makeRequest(ctx, "POST", "/cad/constraints/solve", request)
	if err != nil {
		return fmt.Errorf("failed to solve constraints: %w", err)
	}

	return nil
}

// ValidateDrawing validates the entire drawing
func (c *CADSystem) ValidateDrawing(ctx context.Context, drawingID string) error {
	request := map[string]interface{}{
		"drawing_id": drawingID,
	}

	_, err := c.makeRequest(ctx, "POST", "/cad/validate", request)
	if err != nil {
		return fmt.Errorf("failed to validate drawing: %w", err)
	}

	return nil
}

// GetDrawingInfo gets comprehensive drawing information
func (c *CADSystem) GetDrawingInfo(ctx context.Context, drawingID string) (map[string]interface{}, error) {
	resp, err := c.makeRequest(ctx, "GET", fmt.Sprintf("/cad/drawing/%s", drawingID), nil)
	if err != nil {
		return nil, fmt.Errorf("failed to get drawing info: %w", err)
	}

	var info map[string]interface{}
	if err := json.Unmarshal(resp, &info); err != nil {
		return nil, fmt.Errorf("failed to unmarshal drawing info: %w", err)
	}

	return info, nil
}

// ExportDrawing exports the drawing in specified format
func (c *CADSystem) ExportDrawing(ctx context.Context, drawingID, formatType string) (map[string]interface{}, error) {
	request := map[string]interface{}{
		"drawing_id": drawingID,
		"format":     formatType,
	}

	resp, err := c.makeRequest(ctx, "POST", "/cad/export", request)
	if err != nil {
		return nil, fmt.Errorf("failed to export drawing: %w", err)
	}

	var exportData map[string]interface{}
	if err := json.Unmarshal(resp, &exportData); err != nil {
		return nil, fmt.Errorf("failed to unmarshal export data: %w", err)
	}

	return exportData, nil
}

// makeRequest makes an HTTP request to the Python CAD service
func (c *CADSystem) makeRequest(ctx context.Context, method, path string, body interface{}) ([]byte, error) {
	var req *http.Request
	var err error

	if body != nil {
		jsonBody, err := json.Marshal(body)
		if err != nil {
			return nil, fmt.Errorf("failed to marshal request body: %w", err)
		}

		req, err = http.NewRequestWithContext(ctx, method, c.baseURL+path, bytes.NewBuffer(jsonBody))
		if err != nil {
			return nil, fmt.Errorf("failed to create request: %w", err)
		}
		req.Header.Set("Content-Type", "application/json")
	} else {
		req, err = http.NewRequestWithContext(ctx, method, c.baseURL+path, nil)
		if err != nil {
			return nil, fmt.Errorf("failed to create request: %w", err)
		}
	}

	resp, err := c.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to make request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("request failed with status: %d", resp.StatusCode)
	}

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}

	return respBody, nil
}
