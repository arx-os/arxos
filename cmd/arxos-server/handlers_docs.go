package main

// handleHealth godoc
//
//	@Summary		Health check
//	@Description	Check if the service is healthy and responding
//	@Tags			Health
//	@Accept			json
//	@Produce		json
//	@Success		200	{object}	docs.HealthResponse
//	@Router			/health [get]
func (h *handlers) handleHealthDoc() {}

// handleReady godoc
//
//	@Summary		Readiness check
//	@Description	Check if the service is ready to accept requests
//	@Tags			Health
//	@Accept			json
//	@Produce		json
//	@Success		200	{object}	docs.ReadyResponse
//	@Failure		503	{object}	docs.ReadyResponse
//	@Router			/ready [get]
func (h *handlers) handleReadyDoc() {}

// handleAPIRoot godoc
//
//	@Summary		API information
//	@Description	Get information about the API and available endpoints
//	@Tags			Health
//	@Accept			json
//	@Produce		json
//	@Success		200	{object}	docs.APIRootResponse
//	@Router			/api/v1 [get]
func (h *handlers) handleAPIRootDoc() {}

// handleLogin godoc
//
//	@Summary		User login
//	@Description	Authenticate a user and return access tokens
//	@Tags			Authentication
//	@Accept			json
//	@Produce		json
//	@Param			request	body		docs.LoginRequest	true	"Login credentials"
//	@Success		200		{object}	docs.AuthResponse
//	@Failure		400		{object}	docs.ErrorResponse
//	@Failure		401		{object}	docs.ErrorResponse
//	@Router			/api/v1/auth/login [post]
func (h *handlers) handleLoginDoc() {}

// handleRegister godoc
//
//	@Summary		User registration
//	@Description	Register a new user account
//	@Tags			Authentication
//	@Accept			json
//	@Produce		json
//	@Param			request	body		docs.RegisterRequest	true	"Registration details"
//	@Success		201		{object}	docs.AuthResponse
//	@Failure		400		{object}	docs.ErrorResponse
//	@Router			/api/v1/auth/register [post]
func (h *handlers) handleRegisterDoc() {}

// handleLogout godoc
//
//	@Summary		User logout
//	@Description	Logout the current user and invalidate tokens
//	@Tags			Authentication
//	@Accept			json
//	@Produce		json
//	@Security		BearerAuth
//	@Success		200	{object}	docs.SuccessResponse
//	@Router			/api/v1/auth/logout [post]
func (h *handlers) handleLogoutDoc() {}

// handleRefresh godoc
//
//	@Summary		Refresh access token
//	@Description	Refresh an expired access token using refresh token
//	@Tags			Authentication
//	@Accept			json
//	@Produce		json
//	@Success		200	{object}	docs.AuthResponse
//	@Failure		400	{object}	docs.ErrorResponse
//	@Failure		401	{object}	docs.ErrorResponse
//	@Router			/api/v1/auth/refresh [post]
func (h *handlers) handleRefreshDoc() {}

// handleListBuildings godoc
//
//	@Summary		List buildings
//	@Description	Get a list of all buildings accessible to the user
//	@Tags			Buildings
//	@Accept			json
//	@Produce		json
//	@Security		BearerAuth
//	@Param			limit	query		int	false	"Maximum number of buildings to return"	default(100)
//	@Param			offset	query		int	false	"Number of buildings to skip"			default(0)
//	@Success		200		{array}		docs.FloorPlan
//	@Failure		401		{object}	docs.ErrorResponse
//	@Failure		500		{object}	docs.ErrorResponse
//	@Router			/api/v1/buildings [get]
func (h *handlers) handleListBuildingsDoc() {}

// handleCreateBuilding godoc
//
//	@Summary		Create building
//	@Description	Create a new building/floor plan
//	@Tags			Buildings
//	@Accept			json
//	@Produce		json
//	@Security		BearerAuth
//	@Param			building	body		docs.FloorPlan	true	"Building details"
//	@Success		201			{object}	docs.FloorPlan
//	@Failure		400			{object}	docs.ErrorResponse
//	@Failure		401			{object}	docs.ErrorResponse
//	@Failure		500			{object}	docs.ErrorResponse
//	@Router			/api/v1/buildings [post]
func (h *handlers) handleCreateBuildingDoc() {}

// handleGetBuilding godoc
//
//	@Summary		Get building
//	@Description	Get details of a specific building by ID
//	@Tags			Buildings
//	@Accept			json
//	@Produce		json
//	@Security		BearerAuth
//	@Param			buildingID	path		string	true	"Building ID"
//	@Success		200			{object}	docs.FloorPlan
//	@Failure		401			{object}	docs.ErrorResponse
//	@Failure		404			{object}	docs.ErrorResponse
//	@Failure		500			{object}	docs.ErrorResponse
//	@Router			/api/v1/buildings/{buildingID} [get]
func (h *handlers) handleGetBuildingDoc() {}

// handleUpdateBuilding godoc
//
//	@Summary		Update building
//	@Description	Update an existing building
//	@Tags			Buildings
//	@Accept			json
//	@Produce		json
//	@Security		BearerAuth
//	@Param			buildingID	path		string			true	"Building ID"
//	@Param			building	body		docs.FloorPlan	true	"Updated building details"
//	@Success		200			{object}	docs.FloorPlan
//	@Failure		400			{object}	docs.ErrorResponse
//	@Failure		401			{object}	docs.ErrorResponse
//	@Failure		404			{object}	docs.ErrorResponse
//	@Failure		500			{object}	docs.ErrorResponse
//	@Router			/api/v1/buildings/{buildingID} [put]
func (h *handlers) handleUpdateBuildingDoc() {}

// handleDeleteBuilding godoc
//
//	@Summary		Delete building
//	@Description	Delete a building by ID
//	@Tags			Buildings
//	@Accept			json
//	@Produce		json
//	@Security		BearerAuth
//	@Param			buildingID	path	string	true	"Building ID"
//	@Success		204
//	@Failure		401	{object}	docs.ErrorResponse
//	@Failure		404	{object}	docs.ErrorResponse
//	@Failure		500	{object}	docs.ErrorResponse
//	@Router			/api/v1/buildings/{buildingID} [delete]
func (h *handlers) handleDeleteBuildingDoc() {}

// handleListEquipment godoc
//
//	@Summary		List equipment
//	@Description	Get a list of equipment, optionally filtered by building, type, or status
//	@Tags			Equipment
//	@Accept			json
//	@Produce		json
//	@Security		BearerAuth
//	@Param			building_id	query		string	false	"Filter by building ID"
//	@Param			type		query		string	false	"Filter by equipment type"
//	@Param			status		query		string	false	"Filter by equipment status"	Enums(normal, needs-repair, failed, unknown)
//	@Success		200			{array}		docs.Equipment
//	@Failure		401			{object}	docs.ErrorResponse
//	@Failure		500			{object}	docs.ErrorResponse
//	@Router			/api/v1/equipment [get]
func (h *handlers) handleListEquipmentDoc() {}

// handleCreateEquipment godoc
//
//	@Summary		Create equipment
//	@Description	Create new equipment entry
//	@Tags			Equipment
//	@Accept			json
//	@Produce		json
//	@Security		BearerAuth
//	@Param			equipment	body		docs.Equipment	true	"Equipment details"
//	@Success		201			{object}	docs.Equipment
//	@Failure		400			{object}	docs.ErrorResponse
//	@Failure		401			{object}	docs.ErrorResponse
//	@Failure		500			{object}	docs.ErrorResponse
//	@Router			/api/v1/equipment [post]
func (h *handlers) handleCreateEquipmentDoc() {}

// handleGetEquipment godoc
//
//	@Summary		Get equipment
//	@Description	Get details of specific equipment by ID
//	@Tags			Equipment
//	@Accept			json
//	@Produce		json
//	@Security		BearerAuth
//	@Param			equipmentID	path		string	true	"Equipment ID"
//	@Success		200			{object}	docs.Equipment
//	@Failure		401			{object}	docs.ErrorResponse
//	@Failure		404			{object}	docs.ErrorResponse
//	@Failure		500			{object}	docs.ErrorResponse
//	@Router			/api/v1/equipment/{equipmentID} [get]
func (h *handlers) handleGetEquipmentDoc() {}

// handleUpdateEquipment godoc
//
//	@Summary		Update equipment
//	@Description	Update existing equipment
//	@Tags			Equipment
//	@Accept			json
//	@Produce		json
//	@Security		BearerAuth
//	@Param			equipmentID	path		string			true	"Equipment ID"
//	@Param			equipment	body		docs.Equipment	true	"Updated equipment details"
//	@Success		200			{object}	docs.Equipment
//	@Failure		400			{object}	docs.ErrorResponse
//	@Failure		401			{object}	docs.ErrorResponse
//	@Failure		404			{object}	docs.ErrorResponse
//	@Failure		500			{object}	docs.ErrorResponse
//	@Router			/api/v1/equipment/{equipmentID} [put]
func (h *handlers) handleUpdateEquipmentDoc() {}

// handleDeleteEquipment godoc
//
//	@Summary		Delete equipment
//	@Description	Delete equipment by ID
//	@Tags			Equipment
//	@Accept			json
//	@Produce		json
//	@Security		BearerAuth
//	@Param			equipmentID	path	string	true	"Equipment ID"
//	@Success		204
//	@Failure		401	{object}	docs.ErrorResponse
//	@Failure		404	{object}	docs.ErrorResponse
//	@Failure		500	{object}	docs.ErrorResponse
//	@Router			/api/v1/equipment/{equipmentID} [delete]
func (h *handlers) handleDeleteEquipmentDoc() {}

// handleListOrganizations godoc
//
//	@Summary		List organizations
//	@Description	Get a list of organizations accessible to the user
//	@Tags			Organizations
//	@Accept			json
//	@Produce		json
//	@Security		BearerAuth
//	@Success		200	{array}		docs.Organization
//	@Failure		401	{object}	docs.ErrorResponse
//	@Failure		500	{object}	docs.ErrorResponse
//	@Router			/api/v1/organizations [get]
func (h *handlers) handleListOrganizationsDoc() {}

// handleCreateOrganization godoc
//
//	@Summary		Create organization
//	@Description	Create a new organization (admin only)
//	@Tags			Organizations
//	@Accept			json
//	@Produce		json
//	@Security		BearerAuth
//	@Param			organization	body		docs.CreateOrganizationRequest	true	"Organization details"
//	@Success		201				{object}	docs.Organization
//	@Failure		400				{object}	docs.ErrorResponse
//	@Failure		401				{object}	docs.ErrorResponse
//	@Failure		403				{object}	docs.ErrorResponse
//	@Failure		500				{object}	docs.ErrorResponse
//	@Router			/api/v1/organizations [post]
func (h *handlers) handleCreateOrganizationDoc() {}

// handleGetOrganization godoc
//
//	@Summary		Get organization
//	@Description	Get details of a specific organization
//	@Tags			Organizations
//	@Accept			json
//	@Produce		json
//	@Security		BearerAuth
//	@Param			orgID	path		string	true	"Organization ID"
//	@Success		200		{object}	docs.Organization
//	@Failure		401		{object}	docs.ErrorResponse
//	@Failure		404		{object}	docs.ErrorResponse
//	@Failure		500		{object}	docs.ErrorResponse
//	@Router			/api/v1/organizations/{orgID} [get]
func (h *handlers) handleGetOrganizationDoc() {}

// handlePDFUpload godoc
//
//	@Summary		Upload PDF
//	@Description	Upload and process a PDF file to extract building floor plans
//	@Tags			Upload
//	@Accept			multipart/form-data
//	@Produce		json
//	@Security		BearerAuth
//	@Param			file			formData	file	true	"PDF file to upload"
//	@Param			building_name	formData	string	false	"Name for the building"
//	@Param			building_id		formData	string	false	"Existing building ID to update"
//	@Param			overwrite		formData	bool	false	"Whether to overwrite existing data"
//	@Success		200				{object}	docs.UploadResponse
//	@Failure		400				{object}	docs.ErrorResponse
//	@Failure		401				{object}	docs.ErrorResponse
//	@Failure		500				{object}	docs.ErrorResponse
//	@Router			/api/v1/upload/pdf [post]
func (h *handlers) handlePDFUploadDoc() {}