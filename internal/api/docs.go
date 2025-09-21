package api

// This file contains OpenAPI/Swagger documentation for API endpoints

// HealthCheck godoc
// @Summary Health check endpoint
// @Description Check if the API is running
// @Tags health
// @Accept json
// @Produce json
// @Success 200 {object} map[string]interface{}
// @Router /health [get]
func (s *Server) HealthCheck() {}

// Login godoc
// @Summary User login
// @Description Authenticate user and receive JWT token
// @Tags auth
// @Accept json
// @Produce json
// @Param credentials body AuthRequest true "Login credentials"
// @Success 200 {object} AuthResponse
// @Failure 400 {object} ErrorResponse
// @Failure 401 {object} ErrorResponse
// @Router /auth/login [post]
func (s *Server) Login() {}

// GetBuildings godoc
// @Summary Get all buildings
// @Description Retrieve a list of all buildings
// @Tags buildings
// @Accept json
// @Produce json
// @Security ApiKeyAuth
// @Param page query int false "Page number" default(1)
// @Param per_page query int false "Items per page" default(20)
// @Param search query string false "Search term"
// @Success 200 {object} PaginatedResponse
// @Failure 401 {object} ErrorResponse
// @Failure 500 {object} ErrorResponse
// @Router /buildings [get]
func (s *Server) GetBuildings() {}

// GetBuilding godoc
// @Summary Get building by ID
// @Description Retrieve detailed information about a specific building
// @Tags buildings
// @Accept json
// @Produce json
// @Security ApiKeyAuth
// @Param id path string true "Building ID"
// @Success 200 {object} SuccessResponse
// @Failure 401 {object} ErrorResponse
// @Failure 404 {object} ErrorResponse
// @Failure 500 {object} ErrorResponse
// @Router /buildings/{id} [get]
func (s *Server) GetBuilding() {}

// CreateBuilding godoc
// @Summary Create a new building
// @Description Create a new building entry
// @Tags buildings
// @Accept json
// @Produce json
// @Security ApiKeyAuth
// @Param building body models.Building true "Building data"
// @Success 201 {object} SuccessResponse
// @Failure 400 {object} ErrorResponse
// @Failure 401 {object} ErrorResponse
// @Failure 500 {object} ErrorResponse
// @Router /buildings [post]
func (s *Server) CreateBuilding() {}

// UpdateBuilding godoc
// @Summary Update building
// @Description Update an existing building
// @Tags buildings
// @Accept json
// @Produce json
// @Security ApiKeyAuth
// @Param id path string true "Building ID"
// @Param building body models.Building true "Building data"
// @Success 200 {object} SuccessResponse
// @Failure 400 {object} ErrorResponse
// @Failure 401 {object} ErrorResponse
// @Failure 404 {object} ErrorResponse
// @Failure 500 {object} ErrorResponse
// @Router /buildings/{id} [put]
func (s *Server) UpdateBuilding() {}

// DeleteBuilding godoc
// @Summary Delete building
// @Description Delete a building
// @Tags buildings
// @Accept json
// @Produce json
// @Security ApiKeyAuth
// @Param id path string true "Building ID"
// @Success 204 "No Content"
// @Failure 401 {object} ErrorResponse
// @Failure 404 {object} ErrorResponse
// @Failure 500 {object} ErrorResponse
// @Router /buildings/{id} [delete]
func (s *Server) DeleteBuilding() {}

// GetEquipment godoc
// @Summary Get all equipment
// @Description Retrieve a list of all equipment
// @Tags equipment
// @Accept json
// @Produce json
// @Security ApiKeyAuth
// @Param building_id query string false "Filter by building ID"
// @Param floor query int false "Filter by floor number"
// @Param type query string false "Filter by equipment type"
// @Param status query string false "Filter by status"
// @Param page query int false "Page number" default(1)
// @Param per_page query int false "Items per page" default(20)
// @Success 200 {object} PaginatedResponse
// @Failure 401 {object} ErrorResponse
// @Failure 500 {object} ErrorResponse
// @Router /equipment [get]
func (s *Server) GetEquipment() {}

// GetEquipmentByID godoc
// @Summary Get equipment by ID
// @Description Retrieve detailed information about specific equipment
// @Tags equipment
// @Accept json
// @Produce json
// @Security ApiKeyAuth
// @Param id path string true "Equipment ID"
// @Success 200 {object} SuccessResponse
// @Failure 401 {object} ErrorResponse
// @Failure 404 {object} ErrorResponse
// @Failure 500 {object} ErrorResponse
// @Router /equipment/{id} [get]
func (s *Server) GetEquipmentByID() {}

// CreateEquipment godoc
// @Summary Create new equipment
// @Description Create a new equipment entry
// @Tags equipment
// @Accept json
// @Produce json
// @Security ApiKeyAuth
// @Param equipment body models.Equipment true "Equipment data"
// @Success 201 {object} SuccessResponse
// @Failure 400 {object} ErrorResponse
// @Failure 401 {object} ErrorResponse
// @Failure 500 {object} ErrorResponse
// @Router /equipment [post]
func (s *Server) CreateEquipment() {}

// UpdateEquipment godoc
// @Summary Update equipment
// @Description Update existing equipment
// @Tags equipment
// @Accept json
// @Produce json
// @Security ApiKeyAuth
// @Param id path string true "Equipment ID"
// @Param equipment body models.Equipment true "Equipment data"
// @Success 200 {object} SuccessResponse
// @Failure 400 {object} ErrorResponse
// @Failure 401 {object} ErrorResponse
// @Failure 404 {object} ErrorResponse
// @Failure 500 {object} ErrorResponse
// @Router /equipment/{id} [put]
func (s *Server) UpdateEquipment() {}

// QuerySpatial godoc
// @Summary Spatial query
// @Description Perform spatial queries on equipment
// @Tags spatial
// @Accept json
// @Produce json
// @Security ApiKeyAuth
// @Param query body SpatialQuery true "Spatial query parameters"
// @Success 200 {object} SuccessResponse
// @Failure 400 {object} ErrorResponse
// @Failure 401 {object} ErrorResponse
// @Failure 500 {object} ErrorResponse
// @Router /spatial/query [post]
func (s *Server) QuerySpatial() {}

// SpatialQuery represents spatial query parameters
// @Description Spatial query parameters
type SpatialQuery struct {
	Type      string   `json:"type" example:"proximity"`
	Center    *Point3D `json:"center,omitempty"`
	Radius    float64  `json:"radius,omitempty" example:"10.5"`
	BBox      *BBox    `json:"bbox,omitempty"`
	Floor     *int     `json:"floor,omitempty" example:"3"`
	Equipment []string `json:"equipment_types,omitempty" example:"[\"outlet\",\"switch\"]"`
}

// Point3D represents a 3D point
// @Description 3D coordinate point
type Point3D struct {
	X float64 `json:"x" example:"10.5"`
	Y float64 `json:"y" example:"20.3"`
	Z float64 `json:"z" example:"3.0"`
}

// BBox represents a bounding box
// @Description Spatial bounding box
type BBox struct {
	MinX float64 `json:"min_x" example:"0.0"`
	MinY float64 `json:"min_y" example:"0.0"`
	MinZ float64 `json:"min_z" example:"0.0"`
	MaxX float64 `json:"max_x" example:"100.0"`
	MaxY float64 `json:"max_y" example:"100.0"`
	MaxZ float64 `json:"max_z" example:"10.0"`
}

// ImportIFC godoc
// @Summary Import IFC file
// @Description Import building data from IFC file
// @Tags import
// @Accept multipart/form-data
// @Produce json
// @Security ApiKeyAuth
// @Param file formData file true "IFC file"
// @Param building_id formData string false "Building ID to update"
// @Success 200 {object} SuccessResponse
// @Failure 400 {object} ErrorResponse
// @Failure 401 {object} ErrorResponse
// @Failure 413 {object} ErrorResponse "File too large"
// @Failure 500 {object} ErrorResponse
// @Router /import/ifc [post]
func (s *Server) ImportIFC() {}

// ExportBIM godoc
// @Summary Export to BIM format
// @Description Export building data in BIM text format
// @Tags export
// @Accept json
// @Produce text/plain
// @Security ApiKeyAuth
// @Param building_id query string true "Building ID"
// @Param format query string false "Export format" default("bim") Enums(bim, json, csv)
// @Success 200 {string} string "BIM data"
// @Failure 401 {object} ErrorResponse
// @Failure 404 {object} ErrorResponse
// @Failure 500 {object} ErrorResponse
// @Router /export/bim [get]
func (s *Server) ExportBIM() {}

// GetConnectionGraph godoc
// @Summary Get equipment connection graph
// @Description Retrieve equipment connection relationships
// @Tags connections
// @Accept json
// @Produce json
// @Security ApiKeyAuth
// @Param equipment_id query string false "Starting equipment ID"
// @Param type query string false "Connection type filter"
// @Param depth query int false "Maximum traversal depth" default(3)
// @Success 200 {object} SuccessResponse
// @Failure 401 {object} ErrorResponse
// @Failure 500 {object} ErrorResponse
// @Router /connections/graph [get]
func (s *Server) GetConnectionGraph() {}

// CreateConnection godoc
// @Summary Create equipment connection
// @Description Create a connection between two pieces of equipment
// @Tags connections
// @Accept json
// @Produce json
// @Security ApiKeyAuth
// @Param connection body ConnectionRequest true "Connection data"
// @Success 201 {object} SuccessResponse
// @Failure 400 {object} ErrorResponse
// @Failure 401 {object} ErrorResponse
// @Failure 409 {object} ErrorResponse "Would create cycle"
// @Failure 500 {object} ErrorResponse
// @Router /connections [post]
func (s *Server) CreateConnection() {}

// ConnectionRequest represents a connection creation request
// @Description Equipment connection request
type ConnectionRequest struct {
	FromEquipmentID string                 `json:"from_equipment_id" binding:"required" example:"EQ001"`
	ToEquipmentID   string                 `json:"to_equipment_id" binding:"required" example:"EQ002"`
	Type            string                 `json:"type" binding:"required" example:"electrical"`
	Metadata        map[string]interface{} `json:"metadata,omitempty"`
}