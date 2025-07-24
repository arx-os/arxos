package handlers

import (
	"net/http"

	"arx/services/cad"
	"arx/utils"

	"github.com/go-chi/chi/v5"
)

// CAD handlers for REST API endpoints

// CreateDrawingRequest represents request to create a new drawing
type CreateDrawingRequest struct {
	Name           string             `json:"name" binding:"required"`
	PrecisionLevel cad.PrecisionLevel `json:"precision_level"`
}

// AddPointRequest represents request to add a precision point
type AddPointRequest struct {
	DrawingID string   `json:"drawing_id" binding:"required"`
	X         float64  `json:"x" binding:"required"`
	Y         float64  `json:"y" binding:"required"`
	Z         *float64 `json:"z,omitempty"`
}

// AddConstraintRequest represents request to add a constraint
type AddConstraintRequest struct {
	DrawingID      string                 `json:"drawing_id" binding:"required"`
	ConstraintType cad.ConstraintType     `json:"constraint_type" binding:"required"`
	Entities       []string               `json:"entities" binding:"required"`
	Parameters     map[string]interface{} `json:"parameters"`
}

// AddDimensionRequest represents request to add a dimension
type AddDimensionRequest struct {
	DrawingID     string             `json:"drawing_id" binding:"required"`
	DimensionType cad.DimensionType  `json:"dimension_type" binding:"required"`
	StartPoint    cad.PrecisionPoint `json:"start_point" binding:"required"`
	EndPoint      cad.PrecisionPoint `json:"end_point" binding:"required"`
	StyleName     string             `json:"style_name"`
}

// AddParameterRequest represents request to add a parameter
type AddParameterRequest struct {
	DrawingID     string            `json:"drawing_id" binding:"required"`
	Name          string            `json:"name" binding:"required"`
	ParameterType cad.ParameterType `json:"parameter_type" binding:"required"`
	Value         interface{}       `json:"value" binding:"required"`
	Unit          string            `json:"unit"`
	Description   string            `json:"description"`
}

// CreateAssemblyRequest represents request to create an assembly
type CreateAssemblyRequest struct {
	DrawingID string `json:"drawing_id" binding:"required"`
	Name      string `json:"name" binding:"required"`
}

// AddComponentRequest represents request to add a component to assembly
type AddComponentRequest struct {
	AssemblyID string        `json:"assembly_id" binding:"required"`
	Component  cad.Component `json:"component" binding:"required"`
}

// GenerateViewsRequest represents request to generate views
type GenerateViewsRequest struct {
	DrawingID     string                 `json:"drawing_id" binding:"required"`
	ModelGeometry map[string]interface{} `json:"model_geometry" binding:"required"`
}

// ExportDrawingRequest represents request to export drawing
type ExportDrawingRequest struct {
	DrawingID string `json:"drawing_id" binding:"required"`
	Format    string `json:"format" binding:"required"`
}

// CADHandler handles CAD-related HTTP requests
type CADHandler struct {
	cadService *cad.CADSystem
}

// NewCADHandler creates a new CAD handler
func NewCADHandler(cadService *cad.CADSystem) *CADHandler {
	return &CADHandler{
		cadService: cadService,
	}
}

// CreateDrawing creates a new CAD drawing
func (h *CADHandler) CreateDrawing(c *utils.ChiContext) {
	var req CreateDrawingRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	precisionLevel := req.PrecisionLevel
	if precisionLevel == "" {
		precisionLevel = cad.PrecisionLevelSubMillimeter
	}

	drawing, err := h.cadService.CreateNewDrawing(c.Request.Context(), req.Name, precisionLevel)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to create drawing", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    drawing,
		"message": "Drawing created successfully",
	})
}

// AddPrecisionPoint adds a precision point to a drawing
func (h *CADHandler) AddPrecisionPoint(c *utils.ChiContext) {
	var req AddPointRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	point, err := h.cadService.AddPrecisionPoint(c.Request.Context(), req.DrawingID, req.X, req.Y, req.Z)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to add precision point", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    point,
		"message": "Precision point added successfully",
	})
}

// AddConstraint adds a constraint to a drawing
func (h *CADHandler) AddConstraint(c *utils.ChiContext) {
	var req AddConstraintRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	err := h.cadService.AddConstraint(c.Request.Context(), req.DrawingID, req.ConstraintType, req.Entities, req.Parameters)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to add constraint", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "Constraint added successfully",
	})
}

// AddDimension adds a dimension to a drawing
func (h *CADHandler) AddDimension(c *utils.ChiContext) {
	var req AddDimensionRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	err := h.cadService.AddDimension(c.Request.Context(), req.DrawingID, req.DimensionType, req.StartPoint, req.EndPoint, req.StyleName)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to add dimension", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "Dimension added successfully",
	})
}

// AddParameter adds a parameter to a drawing
func (h *CADHandler) AddParameter(c *utils.ChiContext) {
	var req AddParameterRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	parameter, err := h.cadService.AddParameter(c.Request.Context(), req.DrawingID, req.Name, req.ParameterType, req.Value, req.Unit, req.Description)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to add parameter", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    parameter,
		"message": "Parameter added successfully",
	})
}

// CreateAssembly creates a new assembly
func (h *CADHandler) CreateAssembly(c *utils.ChiContext) {
	var req CreateAssemblyRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	assembly, err := h.cadService.CreateAssembly(c.Request.Context(), req.DrawingID, req.Name)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to create assembly", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    assembly,
		"message": "Assembly created successfully",
	})
}

// AddComponentToAssembly adds a component to an assembly
func (h *CADHandler) AddComponentToAssembly(c *utils.ChiContext) {
	var req AddComponentRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	err := h.cadService.AddComponentToAssembly(c.Request.Context(), req.AssemblyID, req.Component)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to add component to assembly", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "Component added to assembly successfully",
	})
}

// GenerateViews generates views for a drawing
func (h *CADHandler) GenerateViews(c *utils.ChiContext) {
	var req GenerateViewsRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	views, err := h.cadService.GenerateViews(c.Request.Context(), req.DrawingID, req.ModelGeometry)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to generate views", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    views,
		"message": "Views generated successfully",
	})
}

// SolveConstraints solves constraints in a drawing
func (h *CADHandler) SolveConstraints(c *utils.ChiContext) {
	drawingID := c.Reader.Param("drawingID")
	if drawingID == "" {
		c.Writer.Error(http.StatusBadRequest, "Drawing ID is required", "")
		return
	}

	err := h.cadService.SolveConstraints(c.Request.Context(), drawingID)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to solve constraints", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "Constraints solved successfully",
	})
}

// ValidateDrawing validates a drawing
func (h *CADHandler) ValidateDrawing(c *utils.ChiContext) {
	drawingID := c.Reader.Param("drawingID")
	if drawingID == "" {
		c.Writer.Error(http.StatusBadRequest, "Drawing ID is required", "")
		return
	}

	err := h.cadService.ValidateDrawing(c.Request.Context(), drawingID)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to validate drawing", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "Drawing validation completed",
	})
}

// GetDrawingInfo gets information about a drawing
func (h *CADHandler) GetDrawingInfo(c *utils.ChiContext) {
	drawingID := c.Reader.Param("drawingID")
	if drawingID == "" {
		c.Writer.Error(http.StatusBadRequest, "Drawing ID is required", "")
		return
	}

	info, err := h.cadService.GetDrawingInfo(c.Request.Context(), drawingID)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get drawing info", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    info,
		"message": "Drawing info retrieved successfully",
	})
}

// ExportDrawing exports a drawing
func (h *CADHandler) ExportDrawing(c *utils.ChiContext) {
	var req ExportDrawingRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	exportData, err := h.cadService.ExportDrawing(c.Request.Context(), req.DrawingID, req.Format)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to export drawing", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    exportData,
		"message": "Drawing exported successfully",
	})
}

// GetDrawingHistory gets the history of a drawing
func (h *CADHandler) GetDrawingHistory(c *utils.ChiContext) {
	drawingID := c.Reader.Param("drawingID")
	if drawingID == "" {
		c.Writer.Error(http.StatusBadRequest, "Drawing ID is required", "")
		return
	}

	// Placeholder implementation since GetDrawingHistory doesn't exist in the service
	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    []map[string]interface{}{},
		"message": "Drawing history retrieved successfully",
	})
}

// GetCADSystemInfo gets information about the CAD system
func (h *CADHandler) GetCADSystemInfo(c *utils.ChiContext) {
	// Placeholder implementation since GetSystemInfo doesn't exist in the service
	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"data": map[string]interface{}{
			"precision_levels": []string{"millimeter", "sub_millimeter", "micron", "nanometer"},
			"constraint_types": []string{"distance", "angle", "parallel", "perpendicular", "coincident", "tangent", "symmetric"},
			"dimension_types":  []string{"linear_horizontal", "linear_vertical", "linear_aligned", "radial", "diameter", "angular", "ordinate"},
			"parameter_types":  []string{"length", "angle", "radius", "diameter", "area", "volume", "string", "boolean", "integer", "real"},
			"view_types":       []string{"front", "top", "right", "left", "bottom", "back", "isometric", "section", "detail", "auxiliary"},
		},
		"message": "CAD system info retrieved successfully",
	})
}

// SetupCADRoutes sets up CAD-related routes
func SetupCADRoutes(router chi.Router, cadHandler *CADHandler) {
	router.Route("/api/cad", func(r chi.Router) {
		// Drawing management
		r.Post("/drawing", utils.ToChiHandler(cadHandler.CreateDrawing))
		r.Get("/drawing/{drawing_id}", utils.ToChiHandler(cadHandler.GetDrawingInfo))
		r.Get("/drawings", utils.ToChiHandler(cadHandler.GetDrawingHistory))

		// Precision and geometry
		r.Post("/point", utils.ToChiHandler(cadHandler.AddPrecisionPoint))

		// Constraints
		r.Post("/constraint", utils.ToChiHandler(cadHandler.AddConstraint))
		r.Post("/constraints/solve", utils.ToChiHandler(cadHandler.SolveConstraints))

		// Dimensions
		r.Post("/dimension", utils.ToChiHandler(cadHandler.AddDimension))

		// Parameters
		r.Post("/parameter", utils.ToChiHandler(cadHandler.AddParameter))

		// Assemblies
		r.Post("/assembly", utils.ToChiHandler(cadHandler.CreateAssembly))
		r.Post("/assembly/component", utils.ToChiHandler(cadHandler.AddComponentToAssembly))

		// Views
		r.Post("/views", utils.ToChiHandler(cadHandler.GenerateViews))

		// Validation and export
		r.Post("/validate", utils.ToChiHandler(cadHandler.ValidateDrawing))
		r.Post("/export", utils.ToChiHandler(cadHandler.ExportDrawing))

		// System info
		r.Get("/system/info", utils.ToChiHandler(cadHandler.GetCADSystemInfo))
	})
}
