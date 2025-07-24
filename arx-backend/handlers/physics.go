package handlers

import (
	"fmt"
	"net/http"

	"arx/services/physics"
	"arx/utils"

	"github.com/go-chi/chi/v5"
)

// PhysicsHandler handles physics-related HTTP requests
type PhysicsHandler struct {
	structuralService *physics.StructuralService
	fluidService      *physics.FluidService
	thermalService    *physics.ThermalService
	electricalService *physics.ElectricalService
}

// NewPhysicsHandler creates a new physics handler
func NewPhysicsHandler(
	structuralService *physics.StructuralService,
	fluidService *physics.FluidService,
	thermalService *physics.ThermalService,
	electricalService *physics.ElectricalService,
) *PhysicsHandler {
	return &PhysicsHandler{
		structuralService: structuralService,
		fluidService:      fluidService,
		thermalService:    thermalService,
		electricalService: electricalService,
	}
}

// AnalyzeStructure handles POST /api/physics/structural/analyze
func (ph *PhysicsHandler) AnalyzeStructure(c *utils.ChiContext) {
	var request physics.StructuralAnalysisRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	// Validate request
	if err := ph.validateStructuralRequest(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Validation failed", err.Error())
		return
	}

	// Perform analysis
	result, err := ph.structuralService.AnalyzeStructure(&request)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Analysis failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// AnalyzeBeam handles POST /api/physics/structural/beam
func (ph *PhysicsHandler) AnalyzeBeam(c *utils.ChiContext) {
	var request struct {
		BeamID   string         `json:"beam_id" binding:"required"`
		Length   float64        `json:"length" binding:"required"`
		Width    float64        `json:"width" binding:"required"`
		Height   float64        `json:"height" binding:"required"`
		Material string         `json:"material" binding:"required"`
		Loads    []physics.Load `json:"loads"`
	}

	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	// Perform beam analysis
	result, err := ph.structuralService.AnalyzeBeam(
		request.BeamID,
		request.Length,
		request.Width,
		request.Height,
		request.Material,
		request.Loads,
	)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Beam analysis failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// AnalyzeColumn handles POST /api/physics/structural/column
func (ph *PhysicsHandler) AnalyzeColumn(c *utils.ChiContext) {
	var request struct {
		ColumnID  string  `json:"column_id" binding:"required"`
		Length    float64 `json:"length" binding:"required"`
		Width     float64 `json:"width" binding:"required"`
		Height    float64 `json:"height" binding:"required"`
		Material  string  `json:"material" binding:"required"`
		AxialLoad float64 `json:"axial_load" binding:"required"`
	}

	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	// Perform column analysis
	result, err := ph.structuralService.AnalyzeColumn(
		request.ColumnID,
		request.Length,
		request.Width,
		request.Height,
		request.Material,
		request.AxialLoad,
	)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Column analysis failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// AnalyzePlate handles POST /api/physics/structural/plate
func (ph *PhysicsHandler) AnalyzePlate(c *utils.ChiContext) {
	var request struct {
		PlateID   string         `json:"plate_id" binding:"required"`
		Length    float64        `json:"length" binding:"required"`
		Width     float64        `json:"width" binding:"required"`
		Thickness float64        `json:"thickness" binding:"required"`
		Material  string         `json:"material" binding:"required"`
		Loads     []physics.Load `json:"loads"`
	}

	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	// Perform plate analysis
	result, err := ph.structuralService.AnalyzePlate(
		request.PlateID,
		request.Length,
		request.Width,
		request.Thickness,
		request.Material,
		request.Loads,
	)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Plate analysis failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// AnalyzeFatigue handles POST /api/physics/structural/fatigue
func (ph *PhysicsHandler) AnalyzeFatigue(c *utils.ChiContext) {
	var request struct {
		ElementID   string                    `json:"element_id" binding:"required"`
		Element     physics.StructuralElement `json:"element" binding:"required"`
		LoadHistory []physics.Load            `json:"load_history" binding:"required"`
	}

	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	// Perform fatigue analysis
	result, err := ph.structuralService.AnalyzeFatigue(
		request.ElementID,
		request.Element,
		request.LoadHistory,
	)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Fatigue analysis failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// AnalyzeDynamic handles POST /api/physics/structural/dynamic
func (ph *PhysicsHandler) AnalyzeDynamic(c *utils.ChiContext) {
	var request struct {
		ElementID string                    `json:"element_id" binding:"required"`
		Element   physics.StructuralElement `json:"element" binding:"required"`
		Loads     []physics.Load            `json:"loads" binding:"required"`
		TimeStep  float64                   `json:"time_step" binding:"required"`
		MaxTime   float64                   `json:"max_time" binding:"required"`
	}

	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	// Perform dynamic analysis
	result, err := ph.structuralService.AnalyzeDynamic(
		request.ElementID,
		request.Element,
		request.Loads,
		request.TimeStep,
		request.MaxTime,
	)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Dynamic analysis failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// GetAnalysisHistory handles GET /api/physics/structural/history/:element_id
func (ph *PhysicsHandler) GetAnalysisHistory(c *utils.ChiContext) {
	elementID := c.Reader.Param("element_id")
	if elementID == "" {
		c.Writer.Error(http.StatusBadRequest, "Element ID is required")
		return
	}

	// Get analysis history
	history, err := ph.structuralService.GetAnalysisHistory(elementID)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get analysis history", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"element_id": elementID,
		"history":    history,
		"count":      len(history),
	})
}

// GetMaterialProperties handles GET /api/physics/materials/:material_name
func (ph *PhysicsHandler) GetMaterialProperties(c *utils.ChiContext) {
	materialName := c.Reader.Param("material_name")
	if materialName == "" {
		c.Writer.Error(http.StatusBadRequest, "Material name is required")
		return
	}

	// Get material properties
	material, err := ph.structuralService.GetMaterialProperties(materialName)
	if err != nil {
		c.Writer.Error(http.StatusNotFound, "Material not found", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, material)
}

// GetCacheStats handles GET /api/physics/cache/stats
func (ph *PhysicsHandler) GetCacheStats(c *utils.ChiContext) {
	stats := ph.structuralService.GetCacheStats()
	c.Writer.JSON(http.StatusOK, stats)
}

// ClearCache handles POST /api/physics/cache/clear
func (ph *PhysicsHandler) ClearCache(c *utils.ChiContext) {
	ph.structuralService.ClearCache()
	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"message": "Cache cleared successfully",
	})
}

// AnalyzeFluid handles POST /api/physics/fluid/analyze
func (ph *PhysicsHandler) AnalyzeFluid(c *utils.ChiContext) {
	var request physics.FluidAnalysisRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	// Validate request
	if err := ph.fluidService.ValidateFluidAnalysisRequest(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Validation failed", err.Error())
		return
	}

	// Perform fluid analysis
	result, err := ph.fluidService.AnalyzeFluidFlow(&request)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Fluid analysis failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// AnalyzeLaminarFlow handles POST /api/physics/fluid/laminar
func (ph *PhysicsHandler) AnalyzeLaminarFlow(c *utils.ChiContext) {
	var request physics.FluidAnalysisRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	// Perform laminar flow analysis
	result, err := ph.fluidService.AnalyzeLaminarFlow(&request)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Laminar flow analysis failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// AnalyzeTurbulentFlow handles POST /api/physics/fluid/turbulent
func (ph *PhysicsHandler) AnalyzeTurbulentFlow(c *utils.ChiContext) {
	var request physics.FluidAnalysisRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	// Perform turbulent flow analysis
	result, err := ph.fluidService.AnalyzeTurbulentFlow(&request)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Turbulent flow analysis failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// GetFluidProperties handles GET /api/physics/fluid/properties/:name
func (ph *PhysicsHandler) GetFluidProperties(c *utils.ChiContext) {
	fluidName := c.Reader.Param("name")
	if fluidName == "" {
		c.Writer.Error(http.StatusBadRequest, "Fluid name is required")
		return
	}

	properties, err := ph.fluidService.GetFluidProperties(fluidName)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get fluid properties", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, properties)
}

// AnalyzeThermal handles POST /api/physics/thermal/analyze
func (ph *PhysicsHandler) AnalyzeThermal(c *utils.ChiContext) {
	var request physics.ThermalAnalysisRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	// Validate request
	if err := ph.thermalService.ValidateThermalAnalysisRequest(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Validation failed", err.Error())
		return
	}

	// Perform thermal analysis
	result, err := ph.thermalService.AnalyzeThermalBehavior(&request)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Thermal analysis failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// AnalyzeConduction handles POST /api/physics/thermal/conduction
func (ph *PhysicsHandler) AnalyzeConduction(c *utils.ChiContext) {
	var request physics.ThermalAnalysisRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	// Perform conduction analysis
	result, err := ph.thermalService.AnalyzeConduction(&request)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Conduction analysis failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// AnalyzeConvection handles POST /api/physics/thermal/convection
func (ph *PhysicsHandler) AnalyzeConvection(c *utils.ChiContext) {
	var request physics.ThermalAnalysisRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	// Perform convection analysis
	result, err := ph.thermalService.AnalyzeConvection(&request)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Convection analysis failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// AnalyzeRadiation handles POST /api/physics/thermal/radiation
func (ph *PhysicsHandler) AnalyzeRadiation(c *utils.ChiContext) {
	var request physics.ThermalAnalysisRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	// Perform radiation analysis
	result, err := ph.thermalService.AnalyzeRadiation(&request)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Radiation analysis failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// GetThermalMaterialProperties handles GET /api/physics/thermal/materials/:name
func (ph *PhysicsHandler) GetThermalMaterialProperties(c *utils.ChiContext) {
	materialName := c.Reader.Param("name")
	if materialName == "" {
		c.Writer.Error(http.StatusBadRequest, "Material name is required")
		return
	}

	properties, err := ph.thermalService.GetMaterialProperties(materialName)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get material properties", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, properties)
}

// AnalyzeElectrical handles POST /api/physics/electrical/analyze
func (ph *PhysicsHandler) AnalyzeElectrical(c *utils.ChiContext) {
	var request physics.ElectricalAnalysisRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	// Validate request
	if err := ph.electricalService.ValidateElectricalAnalysisRequest(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Validation failed", err.Error())
		return
	}

	// Perform electrical analysis
	result, err := ph.electricalService.AnalyzeElectricalCircuit(&request)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Electrical analysis failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// AnalyzeSteadyState handles POST /api/physics/electrical/steady-state
func (ph *PhysicsHandler) AnalyzeSteadyState(c *utils.ChiContext) {
	var request physics.ElectricalAnalysisRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	// Perform steady-state analysis
	result, err := ph.electricalService.AnalyzeSteadyState(&request)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Steady-state analysis failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// AnalyzeTransient handles POST /api/physics/electrical/transient
func (ph *PhysicsHandler) AnalyzeTransient(c *utils.ChiContext) {
	var request physics.ElectricalAnalysisRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	// Perform transient analysis
	result, err := ph.electricalService.AnalyzeTransient(&request)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Transient analysis failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// AnalyzeFault handles POST /api/physics/electrical/fault
func (ph *PhysicsHandler) AnalyzeFault(c *utils.ChiContext) {
	var request physics.ElectricalAnalysisRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	// Perform fault analysis
	result, err := ph.electricalService.AnalyzeFault(&request)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Fault analysis failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// GetElectricalMaterialProperties handles GET /api/physics/electrical/materials/:name
func (ph *PhysicsHandler) GetElectricalMaterialProperties(c *utils.ChiContext) {
	materialName := c.Reader.Param("name")
	if materialName == "" {
		c.Writer.Error(http.StatusBadRequest, "Material name is required")
		return
	}

	properties, err := ph.electricalService.GetMaterialProperties(materialName)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get material properties", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, properties)
}

// GetPhysicsStatistics handles GET /api/physics/statistics
func (ph *PhysicsHandler) GetPhysicsStatistics(c *utils.ChiContext) {
	// Parse query parameters
	period := c.Reader.Query("period")
	if period == "" {
		period = "daily"
	}
	startDate := c.Reader.Query("start_date")
	endDate := c.Reader.Query("end_date")

	// This would typically query the database
	// For now, return mock statistics
	stats := map[string]interface{}{
		"structural": map[string]interface{}{
			"total_analyses": 150,
			"successful":     145,
			"failed":         5,
			"average_time":   2.1,
			"success_rate":   96.7,
		},
		"fluid": map[string]interface{}{
			"total_analyses": 75,
			"successful":     72,
			"failed":         3,
			"average_time":   1.8,
			"success_rate":   96.0,
		},
		"thermal": map[string]interface{}{
			"total_analyses": 60,
			"successful":     58,
			"failed":         2,
			"average_time":   2.3,
			"success_rate":   96.7,
		},
		"electrical": map[string]interface{}{
			"total_analyses": 45,
			"successful":     43,
			"failed":         2,
			"average_time":   1.5,
			"success_rate":   95.6,
		},
		"period":     period,
		"start_date": startDate,
		"end_date":   endDate,
	}

	c.Writer.JSON(http.StatusOK, stats)
}

// Helper methods

func (ph *PhysicsHandler) validateStructuralRequest(request *physics.StructuralAnalysisRequest) error {
	if request.ElementID == "" {
		return fmt.Errorf("element ID is required")
	}

	if len(request.Elements) == 0 {
		return fmt.Errorf("at least one element is required")
	}

	if request.AnalysisType == "" {
		return fmt.Errorf("analysis type is required")
	}

	// Validate analysis type
	validTypes := []string{"static", "dynamic", "buckling", "fatigue", "deflection"}
	valid := false
	for _, t := range validTypes {
		if request.AnalysisType == t {
			valid = true
			break
		}
	}
	if !valid {
		return fmt.Errorf("invalid analysis type: %s", request.AnalysisType)
	}

	// Validate elements
	for i, element := range request.Elements {
		if element.ID == "" {
			return fmt.Errorf("element %d: ID is required", i)
		}

		if element.Type == "" {
			return fmt.Errorf("element %d: type is required", i)
		}

		if len(element.Nodes) < 2 {
			return fmt.Errorf("element %d: at least 2 nodes are required", i)
		}

		if element.Material == "" {
			return fmt.Errorf("element %d: material is required", i)
		}
	}

	return nil
}

// RegisterRoutes registers physics routes
func (ph *PhysicsHandler) RegisterRoutes(router chi.Router) {
	// Structural analysis routes
	router.Route("/physics/structural", func(r chi.Router) {
		r.Post("/analyze", utils.ToChiHandler(ph.AnalyzeStructure))
		r.Post("/beam", utils.ToChiHandler(ph.AnalyzeBeam))
		r.Post("/column", utils.ToChiHandler(ph.AnalyzeColumn))
		r.Post("/plate", utils.ToChiHandler(ph.AnalyzePlate))
		r.Post("/fatigue", utils.ToChiHandler(ph.AnalyzeFatigue))
		r.Post("/dynamic", utils.ToChiHandler(ph.AnalyzeDynamic))
		r.Get("/history/{element_id}", utils.ToChiHandler(ph.GetAnalysisHistory))
	})

	// Material routes
	router.Get("/physics/materials/{material_name}", utils.ToChiHandler(ph.GetMaterialProperties))

	// Fluid analysis routes
	router.Post("/physics/fluid/analyze", utils.ToChiHandler(ph.AnalyzeFluid))
	router.Post("/physics/fluid/laminar", utils.ToChiHandler(ph.AnalyzeLaminarFlow))
	router.Post("/physics/fluid/turbulent", utils.ToChiHandler(ph.AnalyzeTurbulentFlow))
	router.Get("/physics/fluid/properties/{name}", utils.ToChiHandler(ph.GetFluidProperties))

	// Thermal analysis routes
	router.Post("/physics/thermal/analyze", utils.ToChiHandler(ph.AnalyzeThermal))
	router.Post("/physics/thermal/conduction", utils.ToChiHandler(ph.AnalyzeConduction))
	router.Post("/physics/thermal/convection", utils.ToChiHandler(ph.AnalyzeConvection))
	router.Post("/physics/thermal/radiation", utils.ToChiHandler(ph.AnalyzeRadiation))
	router.Get("/physics/thermal/materials/{name}", utils.ToChiHandler(ph.GetThermalMaterialProperties))

	// Electrical analysis routes
	router.Post("/physics/electrical/analyze", utils.ToChiHandler(ph.AnalyzeElectrical))
	router.Post("/physics/electrical/steady-state", utils.ToChiHandler(ph.AnalyzeSteadyState))
	router.Post("/physics/electrical/transient", utils.ToChiHandler(ph.AnalyzeTransient))
	router.Post("/physics/electrical/fault", utils.ToChiHandler(ph.AnalyzeFault))
	router.Get("/physics/electrical/materials/{name}", utils.ToChiHandler(ph.GetElectricalMaterialProperties))

	// Statistics routes
	router.Get("/physics/statistics", utils.ToChiHandler(ph.GetPhysicsStatistics))

	// Cache management routes
	router.Route("/physics/cache", func(r chi.Router) {
		r.Get("/stats", utils.ToChiHandler(ph.GetCacheStats))
		r.Post("/clear", utils.ToChiHandler(ph.ClearCache))
	})
}
