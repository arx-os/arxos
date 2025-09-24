package handlers

import (
	"net/http"

	"github.com/arx-os/arxos/internal/api/models"
	"github.com/arx-os/arxos/internal/api/types"
)

// RoutingHandler handles routing-related HTTP requests
type RoutingHandler struct {
	*BaseHandler
}

// NewRoutingHandler creates a new routing handler
func NewRoutingHandler(server *types.Server) *RoutingHandler {
	return &RoutingHandler{
		BaseHandler: NewBaseHandler(server),
	}
}

// HandleBuildingOperations handles building resource operations
func (h *RoutingHandler) HandleBuildingOperations(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		// Handle GET /api/v1/buildings/{id}
		HandleGetBuilding(h.server)(w, r)
	case http.MethodPut:
		// Handle PUT /api/v1/buildings/{id}
		HandleUpdateBuilding(h.server)(w, r)
	case http.MethodDelete:
		// Handle DELETE /api/v1/buildings/{id}
		HandleDeleteBuilding(h.server)(w, r)
	default:
		h.RespondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// HandleEquipmentOperations handles equipment resource operations
func (h *RoutingHandler) HandleEquipmentOperations(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		// Handle GET /api/v1/equipment/{id}
		HandleGetEquipment(h.server)(w, r)
	case http.MethodPut:
		// Handle PUT /api/v1/equipment/{id}
		HandleUpdateEquipment(h.server)(w, r)
	case http.MethodDelete:
		// Handle DELETE /api/v1/equipment/{id}
		HandleDeleteEquipment(h.server)(w, r)
	default:
		h.RespondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// HandleUserOperations handles user resource operations
func (h *RoutingHandler) HandleUserOperations(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		// Handle GET /api/v1/users/{id}
		HandleGetUser(h.server)(w, r)
	case http.MethodPut:
		// Handle PUT /api/v1/users/{id}
		HandleUpdateUser(h.server)(w, r)
	case http.MethodDelete:
		// Handle DELETE /api/v1/users/{id}
		HandleDeleteUser(h.server)(w, r)
	default:
		h.RespondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// HandleOrganizationOperations handles organization resource operations
func (h *RoutingHandler) HandleOrganizationOperations(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		// Handle GET /api/v1/organizations/{id}
		HandleGetOrganization(h.server)(w, r)
	case http.MethodPut:
		// Handle PUT /api/v1/organizations/{id}
		HandleUpdateOrganization(h.server)(w, r)
	case http.MethodDelete:
		// Handle DELETE /api/v1/organizations/{id}
		HandleDeleteOrganization(h.server)(w, r)
	default:
		h.RespondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// HandleOrganizationMembers handles organization member operations
func (h *RoutingHandler) HandleOrganizationMembers(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		// Handle GET /api/v1/organizations/{id}/members
		HandleGetMembers(h.server)(w, r)
	case http.MethodPost:
		// Handle POST /api/v1/organizations/{id}/members
		HandleAddMember(h.server)(w, r)
	default:
		h.RespondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// HandleOrganizationMember handles individual organization member operations
func (h *RoutingHandler) HandleOrganizationMember(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodPut:
		// Handle PUT /api/v1/organizations/{id}/members/{user_id}
		HandleUpdateMemberRole(h.server)(w, r)
	case http.MethodDelete:
		// Handle DELETE /api/v1/organizations/{id}/members/{user_id}
		HandleRemoveMember(h.server)(w, r)
	default:
		h.RespondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// HandleOrganizationInvitations handles organization invitation operations
func (h *RoutingHandler) HandleOrganizationInvitations(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		// Handle GET /api/v1/organizations/{id}/invitations
		HandleGetInvitations(h.server)(w, r)
	case http.MethodPost:
		// Handle POST /api/v1/organizations/{id}/invitations
		HandleCreateInvitation(h.server)(w, r)
	default:
		h.RespondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// HandleRevokeOrganizationInvitation handles revoking organization invitations
func (h *RoutingHandler) HandleRevokeOrganizationInvitation(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodDelete {
		h.RespondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	// Handle DELETE /api/v1/organizations/{id}/invitations/{invitation_id}
	HandleRevokeInvitation(h.server)(w, r)
}

// HandleAcceptOrganizationInvitation handles accepting organization invitations
func (h *RoutingHandler) HandleAcceptOrganizationInvitation(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		h.RespondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	// Handle POST /api/v1/invitations/accept
	HandleAcceptInvitation(h.server)(w, r)
}

// HandleSearch handles search operations
func (h *RoutingHandler) HandleSearch(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		h.RespondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	// Parse search parameters
	query := r.URL.Query().Get("q")
	if query == "" {
		h.RespondError(w, http.StatusBadRequest, "Search query is required")
		return
	}

	// Get search type
	searchType := r.URL.Query().Get("type")
	if searchType == "" {
		searchType = "all"
	}

	// Parse pagination
	limit, offset := h.ParsePagination(r)

	// Perform search based on type
	switch searchType {
	case "buildings":
		h.handleBuildingSearch(w, r, query, limit, offset)
	case "equipment":
		h.handleEquipmentSearch(w, r, query, limit, offset)
	case "users":
		h.handleUserSearch(w, r, query, limit, offset)
	case "all":
		h.handleGlobalSearch(w, r, query, limit, offset)
	default:
		h.RespondError(w, http.StatusBadRequest, "Invalid search type")
	}
}

// handleBuildingSearch handles building-specific search
func (h *RoutingHandler) handleBuildingSearch(w http.ResponseWriter, r *http.Request, query string, limit, offset int) {
	// This would use the SearchService to search buildings
	// For now, return a placeholder response
	h.RespondJSON(w, http.StatusOK, map[string]interface{}{
		"query":   query,
		"type":    "buildings",
		"results": []interface{}{},
		"limit":   limit,
		"offset":  offset,
	})
}

// handleEquipmentSearch handles equipment-specific search
func (h *RoutingHandler) handleEquipmentSearch(w http.ResponseWriter, r *http.Request, query string, limit, offset int) {
	// This would use the SearchService to search equipment
	// For now, return a placeholder response
	h.RespondJSON(w, http.StatusOK, map[string]interface{}{
		"query":   query,
		"type":    "equipment",
		"results": []interface{}{},
		"limit":   limit,
		"offset":  offset,
	})
}

// handleUserSearch handles user-specific search
func (h *RoutingHandler) handleUserSearch(w http.ResponseWriter, r *http.Request, query string, limit, offset int) {
	// This would use the SearchService to search users
	// For now, return a placeholder response
	h.RespondJSON(w, http.StatusOK, map[string]interface{}{
		"query":   query,
		"type":    "users",
		"results": []interface{}{},
		"limit":   limit,
		"offset":  offset,
	})
}

// handleGlobalSearch handles global search across all entities
func (h *RoutingHandler) handleGlobalSearch(w http.ResponseWriter, r *http.Request, query string, limit, offset int) {
	// This would use the SearchService to search all entities
	// For now, return a placeholder response
	h.RespondJSON(w, http.StatusOK, map[string]interface{}{
		"query":   query,
		"type":    "all",
		"results": []interface{}{},
		"limit":   limit,
		"offset":  offset,
	})
}

// HandlePDFUpload handles PDF file uploads
func (h *RoutingHandler) HandlePDFUpload(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		h.RespondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	// Check authentication
	_, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse multipart form
	if err := r.ParseMultipartForm(32 << 20); err != nil { // 32 MB max
		h.RespondError(w, http.StatusBadRequest, "Failed to parse multipart form")
		return
	}

	// Get file from form
	file, header, err := r.FormFile("file")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "No file provided")
		return
	}
	defer file.Close()

	// Validate file type
	if header.Header.Get("Content-Type") != "application/pdf" {
		h.RespondError(w, http.StatusBadRequest, "File must be a PDF")
		return
	}

	// Get building ID from form
	buildingID := r.FormValue("building_id")
	if buildingID == "" {
		h.RespondError(w, http.StatusBadRequest, "Building ID is required")
		return
	}

	// Process PDF upload
	// This would use the ImportService to process the PDF
	// For now, return a placeholder response
	h.RespondSuccess(w, map[string]interface{}{
		"filename":    header.Filename,
		"size":        header.Size,
		"building_id": buildingID,
		"status":      "uploaded",
	}, "PDF uploaded successfully")
}

// HandleUploadProgress handles upload progress tracking
func (h *RoutingHandler) HandleUploadProgress(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		h.RespondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	// Get upload ID from query
	uploadID := r.URL.Query().Get("id")
	if uploadID == "" {
		h.RespondError(w, http.StatusBadRequest, "Upload ID is required")
		return
	}

	// Get upload progress
	// This would track upload progress in a cache or database
	// For now, return a placeholder response
	h.RespondJSON(w, http.StatusOK, map[string]interface{}{
		"id":       uploadID,
		"progress": 100,
		"status":   "completed",
	})
}

// HandleUpload handles general file uploads
func (h *RoutingHandler) HandleUpload(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		h.RespondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	// Check authentication
	_, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse request
	var req models.UploadRequest
	if err := h.ParseJSON(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate request
	if err := h.ValidateRequest(req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Validation failed")
		return
	}

	// Process upload based on file type
	switch req.FileType {
	case "ifc":
		h.handleIFCUpload(w, r, req)
	case "pdf":
		h.handlePDFUpload(w, r, req)
	case "bim":
		h.handleBIMUpload(w, r, req)
	default:
		h.RespondError(w, http.StatusBadRequest, "Unsupported file type")
	}
}

// handleIFCUpload handles IFC file uploads
func (h *RoutingHandler) handleIFCUpload(w http.ResponseWriter, r *http.Request, req models.UploadRequest) {
	// This would use the ImportService to process IFC files
	// For now, return a placeholder response
	h.RespondSuccess(w, map[string]interface{}{
		"file_type":   req.FileType,
		"building_id": req.BuildingID,
		"status":      "processing",
	}, "IFC file uploaded successfully")
}

// handlePDFUpload handles PDF file uploads
func (h *RoutingHandler) handlePDFUpload(w http.ResponseWriter, r *http.Request, req models.UploadRequest) {
	// This would use the ImportService to process PDF files
	// For now, return a placeholder response
	h.RespondSuccess(w, map[string]interface{}{
		"file_type":   req.FileType,
		"building_id": req.BuildingID,
		"status":      "processing",
	}, "PDF file uploaded successfully")
}

// handleBIMUpload handles BIM file uploads
func (h *RoutingHandler) handleBIMUpload(w http.ResponseWriter, r *http.Request, req models.UploadRequest) {
	// This would use the ImportService to process BIM files
	// For now, return a placeholder response
	h.RespondSuccess(w, map[string]interface{}{
		"file_type":   req.FileType,
		"building_id": req.BuildingID,
		"status":      "processing",
	}, "BIM file uploaded successfully")
}

// Legacy handler functions for backward compatibility
func HandleBuildingOperations(s *types.Server) http.HandlerFunc {
	handler := NewRoutingHandler(s)
	return handler.HandleBuildingOperations
}

func HandleEquipmentOperations(s *types.Server) http.HandlerFunc {
	handler := NewRoutingHandler(s)
	return handler.HandleEquipmentOperations
}

func HandleUserOperations(s *types.Server) http.HandlerFunc {
	handler := NewRoutingHandler(s)
	return handler.HandleUserOperations
}

func HandleOrganizationOperations(s *types.Server) http.HandlerFunc {
	handler := NewRoutingHandler(s)
	return handler.HandleOrganizationOperations
}

func HandleOrganizationMembers(s *types.Server) http.HandlerFunc {
	handler := NewRoutingHandler(s)
	return handler.HandleOrganizationMembers
}

func HandleOrganizationMember(s *types.Server) http.HandlerFunc {
	handler := NewRoutingHandler(s)
	return handler.HandleOrganizationMember
}

func HandleOrganizationInvitations(s *types.Server) http.HandlerFunc {
	handler := NewRoutingHandler(s)
	return handler.HandleOrganizationInvitations
}

func HandleRevokeOrganizationInvitation(s *types.Server) http.HandlerFunc {
	handler := NewRoutingHandler(s)
	return handler.HandleRevokeOrganizationInvitation
}

func HandleAcceptOrganizationInvitation(s *types.Server) http.HandlerFunc {
	handler := NewRoutingHandler(s)
	return handler.HandleAcceptOrganizationInvitation
}

func HandleSearch(s *types.Server) http.HandlerFunc {
	handler := NewRoutingHandler(s)
	return handler.HandleSearch
}

func HandlePDFUpload(s *types.Server) http.HandlerFunc {
	handler := NewRoutingHandler(s)
	return handler.HandlePDFUpload
}

func HandleUploadProgress(s *types.Server) http.HandlerFunc {
	handler := NewRoutingHandler(s)
	return handler.HandleUploadProgress
}

func HandleUpload(s *types.Server) http.HandlerFunc {
	handler := NewRoutingHandler(s)
	return handler.HandleUpload
}
