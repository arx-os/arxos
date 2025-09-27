package it

import (
	"encoding/json"
	"net/http"
	"strings"
)

// ITAPI provides HTTP API for IT management
type ITAPI struct {
	itManager *ITManager
}

// NewITAPI creates a new IT API
func NewITAPI(itManager *ITManager) *ITAPI {
	return &ITAPI{
		itManager: itManager,
	}
}

// RegisterRoutes registers IT API routes
func (api *ITAPI) RegisterRoutes(mux *http.ServeMux) {
	// Asset routes
	mux.HandleFunc("/api/it/assets", api.handleAssets)
	mux.HandleFunc("/api/it/assets/", api.handleAssetByID)
	mux.HandleFunc("/api/it/assets/room/", api.handleAssetsByRoom)

	// Configuration routes
	mux.HandleFunc("/api/it/configurations", api.handleConfigurations)
	mux.HandleFunc("/api/it/configurations/", api.handleConfigurationByID)
	mux.HandleFunc("/api/it/configurations/templates", api.handleConfigTemplates)

	// Room setup routes
	mux.HandleFunc("/api/it/rooms", api.handleRoomSetups)
	mux.HandleFunc("/api/it/rooms/", api.handleRoomSetupByPath)
	mux.HandleFunc("/api/it/rooms/summary/", api.handleRoomSummary)

	// Work order routes
	mux.HandleFunc("/api/it/workorders", api.handleWorkOrders)
	mux.HandleFunc("/api/it/workorders/", api.handleWorkOrderByID)
	mux.HandleFunc("/api/it/workorders/room/", api.handleWorkOrdersByRoom)

	// Inventory routes
	mux.HandleFunc("/api/it/inventory/parts", api.handleParts)
	mux.HandleFunc("/api/it/inventory/parts/", api.handlePartByID)
	mux.HandleFunc("/api/it/inventory/low-stock", api.handleLowStockParts)
	mux.HandleFunc("/api/it/inventory/reorder", api.handleReorderReport)

	// Summary routes
	mux.HandleFunc("/api/it/summary/building/", api.handleBuildingSummary)
	mux.HandleFunc("/api/it/summary/overview", api.handleITOverview)

	// Metrics routes
	mux.HandleFunc("/api/it/metrics", api.handleMetrics)
}

// handleAssets handles asset requests
func (api *ITAPI) handleAssets(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getAssets(w, r)
	case http.MethodPost:
		api.createAsset(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// getAssets gets all assets with optional filtering
func (api *ITAPI) getAssets(w http.ResponseWriter, r *http.Request) {
	// Parse query parameters
	assetType := r.URL.Query().Get("type")
	status := r.URL.Query().Get("status")
	building := r.URL.Query().Get("building")
	room := r.URL.Query().Get("room")

	// Create filter
	filter := AssetFilter{}
	if assetType != "" {
		filter.Type = AssetType(assetType)
	}
	if status != "" {
		filter.Status = AssetStatus(status)
	}
	if building != "" {
		filter.Location.Building = building
	}
	if room != "" {
		filter.Location.Room = room
	}

	assets := api.itManager.assetManager.GetAssets(filter)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(assets)
}

// createAsset creates a new asset
func (api *ITAPI) createAsset(w http.ResponseWriter, r *http.Request) {
	var asset ITAsset
	if err := json.NewDecoder(r.Body).Decode(&asset); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	err := api.itManager.assetManager.CreateAsset(&asset)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(asset)
}

// handleAssetByID handles asset by ID requests
func (api *ITAPI) handleAssetByID(w http.ResponseWriter, r *http.Request) {
	// Extract ID from URL path
	path := strings.TrimPrefix(r.URL.Path, "/api/it/assets/")
	assetID := strings.Split(path, "/")[0]

	switch r.Method {
	case http.MethodGet:
		api.getAssetByID(w, r, assetID)
	case http.MethodPut:
		api.updateAssetByID(w, r, assetID)
	case http.MethodDelete:
		api.deleteAssetByID(w, r, assetID)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// getAssetByID gets a specific asset
func (api *ITAPI) getAssetByID(w http.ResponseWriter, r *http.Request, assetID string) {
	asset, err := api.itManager.assetManager.GetAsset(assetID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(asset)
}

// updateAssetByID updates a specific asset
func (api *ITAPI) updateAssetByID(w http.ResponseWriter, r *http.Request, assetID string) {
	var asset ITAsset
	if err := json.NewDecoder(r.Body).Decode(&asset); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	err := api.itManager.assetManager.UpdateAsset(assetID, &asset)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(asset)
}

// deleteAssetByID deletes a specific asset
func (api *ITAPI) deleteAssetByID(w http.ResponseWriter, r *http.Request, assetID string) {
	err := api.itManager.assetManager.DeleteAsset(assetID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusNoContent)
}

// handleAssetsByRoom handles assets by room requests
func (api *ITAPI) handleAssetsByRoom(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Extract room path from URL
	path := strings.TrimPrefix(r.URL.Path, "/api/it/assets/room/")
	roomPath := "/" + path

	assets, err := api.itManager.GetAssetsByRoomPath(roomPath)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(assets)
}

// handleConfigurations handles configuration requests
func (api *ITAPI) handleConfigurations(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getConfigurations(w, r)
	case http.MethodPost:
		api.createConfiguration(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// getConfigurations gets all configurations
func (api *ITAPI) getConfigurations(w http.ResponseWriter, r *http.Request) {
	// Parse query parameters
	assetType := r.URL.Query().Get("asset_type")
	includeTemplates := r.URL.Query().Get("include_templates") == "true"
	createdBy := r.URL.Query().Get("created_by")

	// Create filter
	filter := ConfigFilter{
		IncludeTemplates: includeTemplates,
	}
	if assetType != "" {
		filter.AssetType = AssetType(assetType)
	}
	if createdBy != "" {
		filter.CreatedBy = createdBy
	}

	configs := api.itManager.configManager.GetConfigurations(filter)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(configs)
}

// createConfiguration creates a new configuration
func (api *ITAPI) createConfiguration(w http.ResponseWriter, r *http.Request) {
	var config Configuration
	if err := json.NewDecoder(r.Body).Decode(&config); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	err := api.itManager.configManager.CreateConfiguration(&config)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(config)
}

// handleConfigurationByID handles configuration by ID requests
func (api *ITAPI) handleConfigurationByID(w http.ResponseWriter, r *http.Request) {
	// Extract ID from URL path
	path := strings.TrimPrefix(r.URL.Path, "/api/it/configurations/")
	configID := strings.Split(path, "/")[0]

	switch r.Method {
	case http.MethodGet:
		api.getConfigurationByID(w, r, configID)
	case http.MethodPut:
		api.updateConfigurationByID(w, r, configID)
	case http.MethodDelete:
		api.deleteConfigurationByID(w, r, configID)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// getConfigurationByID gets a specific configuration
func (api *ITAPI) getConfigurationByID(w http.ResponseWriter, r *http.Request, configID string) {
	config, err := api.itManager.configManager.GetConfiguration(configID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(config)
}

// updateConfigurationByID updates a specific configuration
func (api *ITAPI) updateConfigurationByID(w http.ResponseWriter, r *http.Request, configID string) {
	var config Configuration
	if err := json.NewDecoder(r.Body).Decode(&config); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	err := api.itManager.configManager.UpdateConfiguration(configID, &config)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(config)
}

// deleteConfigurationByID deletes a specific configuration
func (api *ITAPI) deleteConfigurationByID(w http.ResponseWriter, r *http.Request, configID string) {
	err := api.itManager.configManager.DeleteConfiguration(configID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusNoContent)
}

// handleConfigTemplates handles configuration templates
func (api *ITAPI) handleConfigTemplates(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	templates := api.itManager.configManager.GetConfigurationTemplates()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(templates)
}

// handleRoomSetups handles room setup requests
func (api *ITAPI) handleRoomSetups(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getRoomSetups(w, r)
	case http.MethodPost:
		api.createRoomSetup(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// getRoomSetups gets all room setups
func (api *ITAPI) getRoomSetups(w http.ResponseWriter, r *http.Request) {
	// Parse query parameters
	setupType := r.URL.Query().Get("setup_type")
	building := r.URL.Query().Get("building")
	room := r.URL.Query().Get("room")
	includeTemplates := r.URL.Query().Get("include_templates") == "true"

	// Create filter
	filter := SetupFilter{
		IncludeTemplates: includeTemplates,
	}
	if setupType != "" {
		filter.SetupType = SetupType(setupType)
	}
	if building != "" {
		filter.Building = building
	}
	if room != "" {
		filter.Room = room
	}

	setups := api.itManager.configManager.GetRoomSetups(filter)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(setups)
}

// createRoomSetup creates a new room setup
func (api *ITAPI) createRoomSetup(w http.ResponseWriter, r *http.Request) {
	var request struct {
		RoomPath  string `json:"room_path"`
		SetupType string `json:"setup_type"`
		CreatedBy string `json:"created_by"`
	}

	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	setup, err := api.itManager.CreateRoomSetupFromPath(request.RoomPath, SetupType(request.SetupType), request.CreatedBy)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(setup)
}

// handleRoomSetupByPath handles room setup by path requests
func (api *ITAPI) handleRoomSetupByPath(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Extract room path from URL
	path := strings.TrimPrefix(r.URL.Path, "/api/it/rooms/")
	roomPath := "/" + path

	setup, err := api.itManager.GetRoomSetupByPath(roomPath)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(setup)
}

// handleRoomSummary handles room summary requests
func (api *ITAPI) handleRoomSummary(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Extract room path from URL
	path := strings.TrimPrefix(r.URL.Path, "/api/it/rooms/summary/")
	roomPath := "/" + path

	summary, err := api.itManager.GetRoomSetupSummary(roomPath)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(summary)
}

// handleWorkOrders handles work order requests
func (api *ITAPI) handleWorkOrders(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getWorkOrders(w, r)
	case http.MethodPost:
		api.createWorkOrder(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// getWorkOrders gets all work orders
func (api *ITAPI) getWorkOrders(w http.ResponseWriter, r *http.Request) {
	// Parse query parameters
	status := r.URL.Query().Get("status")
	workOrderType := r.URL.Query().Get("type")
	priority := r.URL.Query().Get("priority")
	assignedTo := r.URL.Query().Get("assigned_to")
	requestedBy := r.URL.Query().Get("requested_by")
	building := r.URL.Query().Get("building")
	room := r.URL.Query().Get("room")

	// Create filter
	filter := WorkOrderFilter{}
	if status != "" {
		filter.Status = WorkOrderStatus(status)
	}
	if workOrderType != "" {
		filter.Type = WorkOrderType(workOrderType)
	}
	if priority != "" {
		filter.Priority = Priority(priority)
	}
	if assignedTo != "" {
		filter.AssignedTo = assignedTo
	}
	if requestedBy != "" {
		filter.RequestedBy = requestedBy
	}
	if building != "" {
		filter.Building = building
	}
	if room != "" {
		filter.Room = room
	}

	workOrders := api.itManager.workOrderManager.GetWorkOrders(filter)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(workOrders)
}

// createWorkOrder creates a new work order
func (api *ITAPI) createWorkOrder(w http.ResponseWriter, r *http.Request) {
	var request struct {
		RoomPath    string `json:"room_path"`
		Title       string `json:"title"`
		Description string `json:"description"`
		Type        string `json:"type"`
		Priority    string `json:"priority"`
		RequestedBy string `json:"requested_by"`
	}

	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	workOrder, err := api.itManager.CreateWorkOrderForRoom(
		request.RoomPath,
		request.Title,
		request.Description,
		WorkOrderType(request.Type),
		Priority(request.Priority),
		request.RequestedBy,
	)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(workOrder)
}

// handleWorkOrderByID handles work order by ID requests
func (api *ITAPI) handleWorkOrderByID(w http.ResponseWriter, r *http.Request) {
	// Extract ID from URL path
	path := strings.TrimPrefix(r.URL.Path, "/api/it/workorders/")
	workOrderID := strings.Split(path, "/")[0]

	switch r.Method {
	case http.MethodGet:
		api.getWorkOrderByID(w, r, workOrderID)
	case http.MethodPut:
		api.updateWorkOrderByID(w, r, workOrderID)
	case http.MethodDelete:
		api.deleteWorkOrderByID(w, r, workOrderID)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// getWorkOrderByID gets a specific work order
func (api *ITAPI) getWorkOrderByID(w http.ResponseWriter, r *http.Request, workOrderID string) {
	workOrder, err := api.itManager.workOrderManager.GetWorkOrder(workOrderID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(workOrder)
}

// updateWorkOrderByID updates a specific work order
func (api *ITAPI) updateWorkOrderByID(w http.ResponseWriter, r *http.Request, workOrderID string) {
	var workOrder ITWorkOrder
	if err := json.NewDecoder(r.Body).Decode(&workOrder); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	err := api.itManager.workOrderManager.UpdateWorkOrder(workOrderID, &workOrder)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(workOrder)
}

// deleteWorkOrderByID deletes a specific work order
func (api *ITAPI) deleteWorkOrderByID(w http.ResponseWriter, r *http.Request, workOrderID string) {
	err := api.itManager.workOrderManager.DeleteWorkOrder(workOrderID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusNoContent)
}

// handleWorkOrdersByRoom handles work orders by room requests
func (api *ITAPI) handleWorkOrdersByRoom(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Extract room path from URL
	path := strings.TrimPrefix(r.URL.Path, "/api/it/workorders/room/")
	roomPath := "/" + path

	workOrders, err := api.itManager.GetWorkOrdersByRoomPath(roomPath)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(workOrders)
}

// handleParts handles parts requests
func (api *ITAPI) handleParts(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getParts(w, r)
	case http.MethodPost:
		api.createPart(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// getParts gets all parts
func (api *ITAPI) getParts(w http.ResponseWriter, r *http.Request) {
	// Parse query parameters
	category := r.URL.Query().Get("category")
	brand := r.URL.Query().Get("brand")
	status := r.URL.Query().Get("status")
	supplier := r.URL.Query().Get("supplier")
	lowStock := r.URL.Query().Get("low_stock") == "true"
	outOfStock := r.URL.Query().Get("out_of_stock") == "true"

	// Create filter
	filter := PartFilter{
		LowStock:   lowStock,
		OutOfStock: outOfStock,
	}
	if category != "" {
		filter.Category = category
	}
	if brand != "" {
		filter.Brand = brand
	}
	if status != "" {
		filter.Status = PartStatus(status)
	}
	if supplier != "" {
		filter.Supplier = supplier
	}

	parts := api.itManager.inventoryManager.GetParts(filter)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(parts)
}

// createPart creates a new part
func (api *ITAPI) createPart(w http.ResponseWriter, r *http.Request) {
	var part Part
	if err := json.NewDecoder(r.Body).Decode(&part); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	err := api.itManager.inventoryManager.CreatePart(&part)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(part)
}

// handlePartByID handles part by ID requests
func (api *ITAPI) handlePartByID(w http.ResponseWriter, r *http.Request) {
	// Extract ID from URL path
	path := strings.TrimPrefix(r.URL.Path, "/api/it/inventory/parts/")
	partID := strings.Split(path, "/")[0]

	switch r.Method {
	case http.MethodGet:
		api.getPartByID(w, r, partID)
	case http.MethodPut:
		api.updatePartByID(w, r, partID)
	case http.MethodDelete:
		api.deletePartByID(w, r, partID)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// getPartByID gets a specific part
func (api *ITAPI) getPartByID(w http.ResponseWriter, r *http.Request, partID string) {
	part, err := api.itManager.inventoryManager.GetPart(partID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(part)
}

// updatePartByID updates a specific part
func (api *ITAPI) updatePartByID(w http.ResponseWriter, r *http.Request, partID string) {
	var part Part
	if err := json.NewDecoder(r.Body).Decode(&part); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	err := api.itManager.inventoryManager.UpdatePart(partID, &part)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(part)
}

// deletePartByID deletes a specific part
func (api *ITAPI) deletePartByID(w http.ResponseWriter, r *http.Request, partID string) {
	err := api.itManager.inventoryManager.DeletePart(partID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusNoContent)
}

// handleLowStockParts handles low stock parts requests
func (api *ITAPI) handleLowStockParts(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	parts := api.itManager.inventoryManager.GetLowStockParts()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(parts)
}

// handleReorderReport handles reorder report requests
func (api *ITAPI) handleReorderReport(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	reorderItems := api.itManager.inventoryManager.GenerateReorderReport()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(reorderItems)
}

// handleBuildingSummary handles building summary requests
func (api *ITAPI) handleBuildingSummary(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Extract building path from URL
	path := strings.TrimPrefix(r.URL.Path, "/api/it/summary/building/")
	buildingPath := "/" + path

	summary, err := api.itManager.GetBuildingITSummary(buildingPath)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(summary)
}

// handleITOverview handles IT overview requests
func (api *ITAPI) handleITOverview(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	api.itManager.UpdateMetrics()
	metrics := api.itManager.GetMetrics()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(metrics)
}

// handleMetrics handles metrics requests
func (api *ITAPI) handleMetrics(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	api.itManager.UpdateMetrics()
	metrics := api.itManager.GetMetrics()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(metrics)
}
