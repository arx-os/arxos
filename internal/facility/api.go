package facility

import (
	"encoding/json"
	"net/http"
)

// FacilityAPI provides HTTP API for facility management
type FacilityAPI struct {
	facilityManager    *FacilityManager
	workOrderManager   *WorkOrderManager
	maintenanceManager *MaintenanceManager
	inspectionManager  *InspectionManager
	vendorManager      *VendorManager
}

// NewFacilityAPI creates a new facility API
func NewFacilityAPI() *FacilityAPI {
	facilityManager := NewFacilityManager()
	workOrderManager := NewWorkOrderManager(facilityManager)
	maintenanceManager := NewMaintenanceManager(facilityManager, workOrderManager)
	inspectionManager := NewInspectionManager(facilityManager, workOrderManager)
	vendorManager := NewVendorManager(facilityManager)

	return &FacilityAPI{
		facilityManager:    facilityManager,
		workOrderManager:   workOrderManager,
		maintenanceManager: maintenanceManager,
		inspectionManager:  inspectionManager,
		vendorManager:      vendorManager,
	}
}

// RegisterRoutes registers HTTP routes for the facility API
func (api *FacilityAPI) RegisterRoutes(mux *http.ServeMux) {
	// Building management routes
	mux.HandleFunc("/api/v1/facility/buildings", api.handleBuildings)
	mux.HandleFunc("/api/v1/facility/buildings/", api.handleBuildingByID)

	// Space management routes
	mux.HandleFunc("/api/v1/facility/spaces", api.handleSpaces)
	mux.HandleFunc("/api/v1/facility/spaces/", api.handleSpaceByID)
	mux.HandleFunc("/api/v1/facility/buildings/", api.handleSpacesByBuilding)

	// Asset management routes
	mux.HandleFunc("/api/v1/facility/assets", api.handleAssets)
	mux.HandleFunc("/api/v1/facility/assets/", api.handleAssetByID)
	mux.HandleFunc("/api/v1/facility/buildings/", api.handleAssetsByBuilding)
	mux.HandleFunc("/api/v1/facility/spaces/", api.handleAssetsBySpace)

	// Work order management routes
	mux.HandleFunc("/api/v1/facility/workorders", api.handleWorkOrders)
	mux.HandleFunc("/api/v1/facility/workorders/", api.handleWorkOrderByID)
	mux.HandleFunc("/api/v1/facility/workorders/assign", api.handleAssignWorkOrder)
	mux.HandleFunc("/api/v1/facility/workorders/start", api.handleStartWorkOrder)
	mux.HandleFunc("/api/v1/facility/workorders/complete", api.handleCompleteWorkOrder)
	mux.HandleFunc("/api/v1/facility/workorders/cancel", api.handleCancelWorkOrder)

	// Maintenance management routes
	mux.HandleFunc("/api/v1/facility/maintenance", api.handleMaintenanceSchedules)
	mux.HandleFunc("/api/v1/facility/maintenance/", api.handleMaintenanceScheduleByID)
	mux.HandleFunc("/api/v1/facility/maintenance/execute", api.handleExecuteMaintenance)
	mux.HandleFunc("/api/v1/facility/maintenance/execute-all", api.handleExecuteAllMaintenance)

	// Inspection management routes
	mux.HandleFunc("/api/v1/facility/inspections", api.handleInspections)
	mux.HandleFunc("/api/v1/facility/inspections/", api.handleInspectionByID)
	mux.HandleFunc("/api/v1/facility/inspections/start", api.handleStartInspection)
	mux.HandleFunc("/api/v1/facility/inspections/complete", api.handleCompleteInspection)
	mux.HandleFunc("/api/v1/facility/inspections/findings", api.handleFindings)

	// Vendor management routes
	mux.HandleFunc("/api/v1/facility/vendors", api.handleVendors)
	mux.HandleFunc("/api/v1/facility/vendors/", api.handleVendorByID)
	mux.HandleFunc("/api/v1/facility/contracts", api.handleContracts)
	mux.HandleFunc("/api/v1/facility/contracts/", api.handleContractByID)

	// Metrics and statistics routes
	mux.HandleFunc("/api/v1/facility/metrics", api.handleFacilityMetrics)
	mux.HandleFunc("/api/v1/facility/workorders/metrics", api.handleWorkOrderMetrics)
	mux.HandleFunc("/api/v1/facility/maintenance/metrics", api.handleMaintenanceMetrics)
	mux.HandleFunc("/api/v1/facility/inspections/metrics", api.handleInspectionMetrics)
	mux.HandleFunc("/api/v1/facility/vendors/metrics", api.handleVendorMetrics)
}

// Building Management Handlers

func (api *FacilityAPI) handleBuildings(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getBuildings(w, r)
	case http.MethodPost:
		api.createBuilding(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

func (api *FacilityAPI) handleBuildingByID(w http.ResponseWriter, r *http.Request) {
	buildingID := r.URL.Path[len("/api/v1/facility/buildings/"):]
	if buildingID == "" {
		http.Error(w, "Building ID required", http.StatusBadRequest)
		return
	}

	switch r.Method {
	case http.MethodGet:
		api.getBuilding(w, r, buildingID)
	case http.MethodPut:
		api.updateBuilding(w, r, buildingID)
	case http.MethodDelete:
		api.deleteBuilding(w, r, buildingID)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

func (api *FacilityAPI) getBuildings(w http.ResponseWriter, r *http.Request) {
	buildings := api.facilityManager.ListBuildings()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(buildings)
}

func (api *FacilityAPI) createBuilding(w http.ResponseWriter, r *http.Request) {
	var building Building
	if err := json.NewDecoder(r.Body).Decode(&building); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.facilityManager.CreateBuilding(&building); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(building)
}

func (api *FacilityAPI) getBuilding(w http.ResponseWriter, r *http.Request, buildingID string) {
	building, err := api.facilityManager.GetBuilding(buildingID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(building)
}

func (api *FacilityAPI) updateBuilding(w http.ResponseWriter, r *http.Request, buildingID string) {
	var updates map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&updates); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.facilityManager.UpdateBuilding(buildingID, updates); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "updated"})
}

func (api *FacilityAPI) deleteBuilding(w http.ResponseWriter, r *http.Request, buildingID string) {
	if err := api.facilityManager.DeleteBuilding(buildingID); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "deleted"})
}

// Space Management Handlers

func (api *FacilityAPI) handleSpaces(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getSpaces(w, r)
	case http.MethodPost:
		api.createSpace(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

func (api *FacilityAPI) handleSpaceByID(w http.ResponseWriter, r *http.Request) {
	spaceID := r.URL.Path[len("/api/v1/facility/spaces/"):]
	if spaceID == "" {
		http.Error(w, "Space ID required", http.StatusBadRequest)
		return
	}

	switch r.Method {
	case http.MethodGet:
		api.getSpace(w, r, spaceID)
	case http.MethodPut:
		api.updateSpace(w, r, spaceID)
	case http.MethodDelete:
		api.deleteSpace(w, r, spaceID)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

func (api *FacilityAPI) handleSpacesByBuilding(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	buildingID := r.URL.Path[len("/api/v1/facility/buildings/"):]
	if buildingID == "" {
		http.Error(w, "Building ID required", http.StatusBadRequest)
		return
	}

	spaces := api.facilityManager.GetSpacesByBuilding(buildingID)
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(spaces)
}

func (api *FacilityAPI) getSpaces(w http.ResponseWriter, r *http.Request) {
	spaces := api.facilityManager.ListSpaces()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(spaces)
}

func (api *FacilityAPI) createSpace(w http.ResponseWriter, r *http.Request) {
	var space Space
	if err := json.NewDecoder(r.Body).Decode(&space); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.facilityManager.CreateSpace(&space); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(space)
}

func (api *FacilityAPI) getSpace(w http.ResponseWriter, r *http.Request, spaceID string) {
	space, err := api.facilityManager.GetSpace(spaceID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(space)
}

func (api *FacilityAPI) updateSpace(w http.ResponseWriter, r *http.Request, spaceID string) {
	var updates map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&updates); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.facilityManager.UpdateSpace(spaceID, updates); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "updated"})
}

func (api *FacilityAPI) deleteSpace(w http.ResponseWriter, r *http.Request, spaceID string) {
	if err := api.facilityManager.DeleteSpace(spaceID); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "deleted"})
}

// Asset Management Handlers

func (api *FacilityAPI) handleAssets(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getAssets(w, r)
	case http.MethodPost:
		api.createAsset(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

func (api *FacilityAPI) handleAssetByID(w http.ResponseWriter, r *http.Request) {
	assetID := r.URL.Path[len("/api/v1/facility/assets/"):]
	if assetID == "" {
		http.Error(w, "Asset ID required", http.StatusBadRequest)
		return
	}

	switch r.Method {
	case http.MethodGet:
		api.getAsset(w, r, assetID)
	case http.MethodPut:
		api.updateAsset(w, r, assetID)
	case http.MethodDelete:
		api.deleteAsset(w, r, assetID)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

func (api *FacilityAPI) handleAssetsByBuilding(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	buildingID := r.URL.Path[len("/api/v1/facility/buildings/"):]
	if buildingID == "" {
		http.Error(w, "Building ID required", http.StatusBadRequest)
		return
	}

	assets := api.facilityManager.GetAssetsByBuilding(buildingID)
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(assets)
}

func (api *FacilityAPI) handleAssetsBySpace(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	spaceID := r.URL.Path[len("/api/v1/facility/spaces/"):]
	if spaceID == "" {
		http.Error(w, "Space ID required", http.StatusBadRequest)
		return
	}

	assets := api.facilityManager.GetAssetsBySpace(spaceID)
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(assets)
}

func (api *FacilityAPI) getAssets(w http.ResponseWriter, r *http.Request) {
	assets := api.facilityManager.ListAssets()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(assets)
}

func (api *FacilityAPI) createAsset(w http.ResponseWriter, r *http.Request) {
	var asset Asset
	if err := json.NewDecoder(r.Body).Decode(&asset); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.facilityManager.CreateAsset(&asset); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(asset)
}

func (api *FacilityAPI) getAsset(w http.ResponseWriter, r *http.Request, assetID string) {
	asset, err := api.facilityManager.GetAsset(assetID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(asset)
}

func (api *FacilityAPI) updateAsset(w http.ResponseWriter, r *http.Request, assetID string) {
	var updates map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&updates); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.facilityManager.UpdateAsset(assetID, updates); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "updated"})
}

func (api *FacilityAPI) deleteAsset(w http.ResponseWriter, r *http.Request, assetID string) {
	if err := api.facilityManager.DeleteAsset(assetID); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "deleted"})
}

// Work Order Management Handlers

func (api *FacilityAPI) handleWorkOrders(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getWorkOrders(w, r)
	case http.MethodPost:
		api.createWorkOrder(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

func (api *FacilityAPI) handleWorkOrderByID(w http.ResponseWriter, r *http.Request) {
	workOrderID := r.URL.Path[len("/api/v1/facility/workorders/"):]
	if workOrderID == "" {
		http.Error(w, "Work Order ID required", http.StatusBadRequest)
		return
	}

	switch r.Method {
	case http.MethodGet:
		api.getWorkOrder(w, r, workOrderID)
	case http.MethodPut:
		api.updateWorkOrder(w, r, workOrderID)
	case http.MethodDelete:
		api.deleteWorkOrder(w, r, workOrderID)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

func (api *FacilityAPI) handleAssignWorkOrder(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		WorkOrderID  string `json:"work_order_id"`
		TechnicianID string `json:"technician_id"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.workOrderManager.AssignWorkOrder(req.WorkOrderID, req.TechnicianID); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "assigned"})
}

func (api *FacilityAPI) handleStartWorkOrder(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		WorkOrderID string `json:"work_order_id"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.workOrderManager.StartWorkOrder(req.WorkOrderID); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "started"})
}

func (api *FacilityAPI) handleCompleteWorkOrder(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		WorkOrderID string   `json:"work_order_id"`
		Notes       []string `json:"notes"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.workOrderManager.CompleteWorkOrder(req.WorkOrderID, req.Notes); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "completed"})
}

func (api *FacilityAPI) handleCancelWorkOrder(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		WorkOrderID string `json:"work_order_id"`
		Reason      string `json:"reason"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.workOrderManager.CancelWorkOrder(req.WorkOrderID, req.Reason); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "cancelled"})
}

func (api *FacilityAPI) getWorkOrders(w http.ResponseWriter, r *http.Request) {
	workOrders := api.workOrderManager.ListWorkOrders()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(workOrders)
}

func (api *FacilityAPI) createWorkOrder(w http.ResponseWriter, r *http.Request) {
	var workOrder WorkOrder
	if err := json.NewDecoder(r.Body).Decode(&workOrder); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.workOrderManager.CreateWorkOrder(&workOrder); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(workOrder)
}

func (api *FacilityAPI) getWorkOrder(w http.ResponseWriter, r *http.Request, workOrderID string) {
	workOrder, err := api.workOrderManager.GetWorkOrder(workOrderID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(workOrder)
}

func (api *FacilityAPI) updateWorkOrder(w http.ResponseWriter, r *http.Request, workOrderID string) {
	var updates map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&updates); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.workOrderManager.UpdateWorkOrder(workOrderID, updates); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "updated"})
}

func (api *FacilityAPI) deleteWorkOrder(w http.ResponseWriter, r *http.Request, workOrderID string) {
	if err := api.workOrderManager.DeleteWorkOrder(workOrderID); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "deleted"})
}

// Maintenance Management Handlers

func (api *FacilityAPI) handleMaintenanceSchedules(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getMaintenanceSchedules(w, r)
	case http.MethodPost:
		api.createMaintenanceSchedule(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

func (api *FacilityAPI) handleMaintenanceScheduleByID(w http.ResponseWriter, r *http.Request) {
	scheduleID := r.URL.Path[len("/api/v1/facility/maintenance/"):]
	if scheduleID == "" {
		http.Error(w, "Schedule ID required", http.StatusBadRequest)
		return
	}

	switch r.Method {
	case http.MethodGet:
		api.getMaintenanceSchedule(w, r, scheduleID)
	case http.MethodPut:
		api.updateMaintenanceSchedule(w, r, scheduleID)
	case http.MethodDelete:
		api.deleteMaintenanceSchedule(w, r, scheduleID)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

func (api *FacilityAPI) handleExecuteMaintenance(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		ScheduleID string `json:"schedule_id"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	workOrder, err := api.maintenanceManager.ExecuteMaintenanceSchedule(req.ScheduleID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(workOrder)
}

func (api *FacilityAPI) handleExecuteAllMaintenance(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	workOrders, err := api.maintenanceManager.ExecuteAllDueMaintenance()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(workOrders)
}

func (api *FacilityAPI) getMaintenanceSchedules(w http.ResponseWriter, r *http.Request) {
	schedules := api.maintenanceManager.ListMaintenanceSchedules()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(schedules)
}

func (api *FacilityAPI) createMaintenanceSchedule(w http.ResponseWriter, r *http.Request) {
	var schedule MaintenanceSchedule
	if err := json.NewDecoder(r.Body).Decode(&schedule); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.maintenanceManager.CreateMaintenanceSchedule(&schedule); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(schedule)
}

func (api *FacilityAPI) getMaintenanceSchedule(w http.ResponseWriter, r *http.Request, scheduleID string) {
	schedule, err := api.maintenanceManager.GetMaintenanceSchedule(scheduleID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(schedule)
}

func (api *FacilityAPI) updateMaintenanceSchedule(w http.ResponseWriter, r *http.Request, scheduleID string) {
	var updates map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&updates); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.maintenanceManager.UpdateMaintenanceSchedule(scheduleID, updates); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "updated"})
}

func (api *FacilityAPI) deleteMaintenanceSchedule(w http.ResponseWriter, r *http.Request, scheduleID string) {
	if err := api.maintenanceManager.DeleteMaintenanceSchedule(scheduleID); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "deleted"})
}

// Inspection Management Handlers

func (api *FacilityAPI) handleInspections(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getInspections(w, r)
	case http.MethodPost:
		api.createInspection(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

func (api *FacilityAPI) handleInspectionByID(w http.ResponseWriter, r *http.Request) {
	inspectionID := r.URL.Path[len("/api/v1/facility/inspections/"):]
	if inspectionID == "" {
		http.Error(w, "Inspection ID required", http.StatusBadRequest)
		return
	}

	switch r.Method {
	case http.MethodGet:
		api.getInspection(w, r, inspectionID)
	case http.MethodPut:
		api.updateInspection(w, r, inspectionID)
	case http.MethodDelete:
		api.deleteInspection(w, r, inspectionID)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

func (api *FacilityAPI) handleStartInspection(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		InspectionID string `json:"inspection_id"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.inspectionManager.StartInspection(req.InspectionID); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "started"})
}

func (api *FacilityAPI) handleCompleteInspection(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		InspectionID string  `json:"inspection_id"`
		Score        float64 `json:"score"`
		Notes        string  `json:"notes"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.inspectionManager.CompleteInspection(req.InspectionID, req.Score, req.Notes); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "completed"})
}

func (api *FacilityAPI) handleFindings(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Get query parameters
	severity := r.URL.Query().Get("severity")
	status := r.URL.Query().Get("status")
	category := r.URL.Query().Get("category")

	var findings []*InspectionFinding

	if severity != "" {
		findings = api.inspectionManager.GetFindingsBySeverity(FindingSeverity(severity))
	} else if status != "" {
		findings = api.inspectionManager.GetFindingsByStatus(FindingStatus(status))
	} else if category != "" {
		findings = api.inspectionManager.GetFindingsByCategory(category)
	} else {
		// Return all findings
		for _, finding := range api.inspectionManager.findings {
			findings = append(findings, finding)
		}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(findings)
}

func (api *FacilityAPI) getInspections(w http.ResponseWriter, r *http.Request) {
	inspections := api.inspectionManager.ListInspections()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(inspections)
}

func (api *FacilityAPI) createInspection(w http.ResponseWriter, r *http.Request) {
	var inspection Inspection
	if err := json.NewDecoder(r.Body).Decode(&inspection); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.inspectionManager.CreateInspection(&inspection); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(inspection)
}

func (api *FacilityAPI) getInspection(w http.ResponseWriter, r *http.Request, inspectionID string) {
	inspection, err := api.inspectionManager.GetInspection(inspectionID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(inspection)
}

func (api *FacilityAPI) updateInspection(w http.ResponseWriter, r *http.Request, inspectionID string) {
	var updates map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&updates); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.inspectionManager.UpdateInspection(inspectionID, updates); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "updated"})
}

func (api *FacilityAPI) deleteInspection(w http.ResponseWriter, r *http.Request, inspectionID string) {
	if err := api.inspectionManager.DeleteInspection(inspectionID); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "deleted"})
}

// Vendor Management Handlers

func (api *FacilityAPI) handleVendors(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getVendors(w, r)
	case http.MethodPost:
		api.createVendor(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

func (api *FacilityAPI) handleVendorByID(w http.ResponseWriter, r *http.Request) {
	vendorID := r.URL.Path[len("/api/v1/facility/vendors/"):]
	if vendorID == "" {
		http.Error(w, "Vendor ID required", http.StatusBadRequest)
		return
	}

	switch r.Method {
	case http.MethodGet:
		api.getVendor(w, r, vendorID)
	case http.MethodPut:
		api.updateVendor(w, r, vendorID)
	case http.MethodDelete:
		api.deleteVendor(w, r, vendorID)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

func (api *FacilityAPI) handleContracts(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getContracts(w, r)
	case http.MethodPost:
		api.createContract(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

func (api *FacilityAPI) handleContractByID(w http.ResponseWriter, r *http.Request) {
	contractID := r.URL.Path[len("/api/v1/facility/contracts/"):]
	if contractID == "" {
		http.Error(w, "Contract ID required", http.StatusBadRequest)
		return
	}

	switch r.Method {
	case http.MethodGet:
		api.getContract(w, r, contractID)
	case http.MethodPut:
		api.updateContract(w, r, contractID)
	case http.MethodDelete:
		api.deleteContract(w, r, contractID)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

func (api *FacilityAPI) getVendors(w http.ResponseWriter, r *http.Request) {
	vendors := api.vendorManager.ListVendors()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(vendors)
}

func (api *FacilityAPI) createVendor(w http.ResponseWriter, r *http.Request) {
	var vendor Vendor
	if err := json.NewDecoder(r.Body).Decode(&vendor); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.vendorManager.CreateVendor(&vendor); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(vendor)
}

func (api *FacilityAPI) getVendor(w http.ResponseWriter, r *http.Request, vendorID string) {
	vendor, err := api.vendorManager.GetVendor(vendorID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(vendor)
}

func (api *FacilityAPI) updateVendor(w http.ResponseWriter, r *http.Request, vendorID string) {
	var updates map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&updates); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.vendorManager.UpdateVendor(vendorID, updates); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "updated"})
}

func (api *FacilityAPI) deleteVendor(w http.ResponseWriter, r *http.Request, vendorID string) {
	if err := api.vendorManager.DeleteVendor(vendorID); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "deleted"})
}

func (api *FacilityAPI) getContracts(w http.ResponseWriter, r *http.Request) {
	contracts := api.vendorManager.ListContracts()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(contracts)
}

func (api *FacilityAPI) createContract(w http.ResponseWriter, r *http.Request) {
	var contract Contract
	if err := json.NewDecoder(r.Body).Decode(&contract); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.vendorManager.CreateContract(&contract); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(contract)
}

func (api *FacilityAPI) getContract(w http.ResponseWriter, r *http.Request, contractID string) {
	contract, err := api.vendorManager.GetContract(contractID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(contract)
}

func (api *FacilityAPI) updateContract(w http.ResponseWriter, r *http.Request, contractID string) {
	var updates map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&updates); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.vendorManager.UpdateContract(contractID, updates); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "updated"})
}

func (api *FacilityAPI) deleteContract(w http.ResponseWriter, r *http.Request, contractID string) {
	if err := api.vendorManager.DeleteContract(contractID); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "deleted"})
}

// Metrics Handlers

func (api *FacilityAPI) handleFacilityMetrics(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	metrics := api.facilityManager.GetMetrics()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(metrics)
}

func (api *FacilityAPI) handleWorkOrderMetrics(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	metrics := api.workOrderManager.GetWorkOrderMetrics()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(metrics)
}

func (api *FacilityAPI) handleMaintenanceMetrics(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	metrics := api.maintenanceManager.GetMaintenanceMetrics()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(metrics)
}

func (api *FacilityAPI) handleInspectionMetrics(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	metrics := api.inspectionManager.GetInspectionMetrics()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(metrics)
}

func (api *FacilityAPI) handleVendorMetrics(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	metrics := api.vendorManager.GetVendorMetrics()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(metrics)
}
