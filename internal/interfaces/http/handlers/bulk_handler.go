package handlers

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/interfaces/http/types"
	"github.com/arx-os/arxos/internal/usecase"
)

// BulkHandler handles bulk operations for multiple entities
type BulkHandler struct {
	*types.BaseHandler
	buildingUC   *usecase.BuildingUseCase
	equipmentUC  *usecase.EquipmentUseCase
	componentUC  interface{} // ComponentService interface
	userUC       *usecase.UserUseCase
	logger       domain.Logger
}

// NewBulkHandler creates a new bulk handler
func NewBulkHandler(
	server *types.Server,
	buildingUC *usecase.BuildingUseCase,
	equipmentUC *usecase.EquipmentUseCase,
	componentUC interface{},
	userUC *usecase.UserUseCase,
	logger domain.Logger,
) *BulkHandler {
	return &BulkHandler{
		BaseHandler:  types.NewBaseHandler(server),
		buildingUC:   buildingUC,
		equipmentUC:  equipmentUC,
		componentUC:  componentUC,
		userUC:       userUC,
		logger:       logger,
	}
}

// BulkCreateRequest represents a bulk create request
type BulkCreateRequest struct {
	EntityType string                   `json:"entity_type"`
	Data       []map[string]interface{} `json:"data"`
	Options    BulkOptions              `json:"options"`
}

// BulkUpdateRequest represents a bulk update request
type BulkUpdateRequest struct {
	EntityType string                   `json:"entity_type"`
	Data       []map[string]interface{} `json:"data"`
	Options    BulkOptions              `json:"options"`
}

// BulkDeleteRequest represents a bulk delete request
type BulkDeleteRequest struct {
	EntityType string      `json:"entity_type"`
	IDs         []string    `json:"ids"`
	Options     BulkOptions `json:"options"`
}

// BulkOptions represents options for bulk operations
type BulkOptions struct {
	ContinueOnError bool `json:"continue_on_error"`
	BatchSize       int  `json:"batch_size"`
	ValidateOnly    bool `json:"validate_only"`
}

// BulkResponse represents the response from a bulk operation
type BulkResponse struct {
	Success      bool                   `json:"success"`
	Processed    int                    `json:"processed"`
	Successful   int                    `json:"successful"`
	Failed       int                    `json:"failed"`
	Errors       []BulkError            `json:"errors,omitempty"`
	Results      []map[string]interface{} `json:"results,omitempty"`
	Duration     time.Duration           `json:"duration"`
	EntityType   string                 `json:"entity_type"`
	Operation    string                 `json:"operation"`
}

// BulkError represents an error in a bulk operation
type BulkError struct {
	Index   int    `json:"index"`
	ID      string `json:"id,omitempty"`
	Message string `json:"message"`
	Code    string `json:"code"`
}

// BulkCreate handles bulk creation of entities
func (h *BulkHandler) BulkCreate(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Bulk create requested")

	// Validate content type
	if !h.ValidateContentType(r, "application/json") {
		h.HandleError(w, r, fmt.Errorf("content type must be application/json"), http.StatusBadRequest)
		return
	}

	var req BulkCreateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.HandleError(w, r, fmt.Errorf("invalid request body: %v", err), http.StatusBadRequest)
		return
	}

	// Validate request
	if req.EntityType == "" {
		h.HandleError(w, r, fmt.Errorf("entity_type is required"), http.StatusBadRequest)
		return
	}

	if len(req.Data) == 0 {
		h.HandleError(w, r, fmt.Errorf("data array cannot be empty"), http.StatusBadRequest)
		return
	}

	// Set default options
	if req.Options.BatchSize == 0 {
		req.Options.BatchSize = 100
	}

	// Process bulk create
	response, err := h.processBulkCreate(r.Context(), &req)
	if err != nil {
		h.logger.Error("Bulk create failed", "error", err)
		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	response.Duration = time.Since(start)
	h.RespondJSON(w, http.StatusOK, response)
}

// BulkUpdate handles bulk updates of entities
func (h *BulkHandler) BulkUpdate(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Bulk update requested")

	// Validate content type
	if !h.ValidateContentType(r, "application/json") {
		h.HandleError(w, r, fmt.Errorf("content type must be application/json"), http.StatusBadRequest)
		return
	}

	var req BulkUpdateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.HandleError(w, r, fmt.Errorf("invalid request body: %v", err), http.StatusBadRequest)
		return
	}

	// Validate request
	if req.EntityType == "" {
		h.HandleError(w, r, fmt.Errorf("entity_type is required"), http.StatusBadRequest)
		return
	}

	if len(req.Data) == 0 {
		h.HandleError(w, r, fmt.Errorf("data array cannot be empty"), http.StatusBadRequest)
		return
	}

	// Set default options
	if req.Options.BatchSize == 0 {
		req.Options.BatchSize = 100
	}

	// Process bulk update
	response, err := h.processBulkUpdate(r.Context(), &req)
	if err != nil {
		h.logger.Error("Bulk update failed", "error", err)
		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	response.Duration = time.Since(start)
	h.RespondJSON(w, http.StatusOK, response)
}

// BulkDelete handles bulk deletion of entities
func (h *BulkHandler) BulkDelete(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Bulk delete requested")

	// Validate content type
	if !h.ValidateContentType(r, "application/json") {
		h.HandleError(w, r, fmt.Errorf("content type must be application/json"), http.StatusBadRequest)
		return
	}

	var req BulkDeleteRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.HandleError(w, r, fmt.Errorf("invalid request body: %v", err), http.StatusBadRequest)
		return
	}

	// Validate request
	if req.EntityType == "" {
		h.HandleError(w, r, fmt.Errorf("entity_type is required"), http.StatusBadRequest)
		return
	}

	if len(req.IDs) == 0 {
		h.HandleError(w, r, fmt.Errorf("ids array cannot be empty"), http.StatusBadRequest)
		return
	}

	// Set default options
	if req.Options.BatchSize == 0 {
		req.Options.BatchSize = 100
	}

	// Process bulk delete
	response, err := h.processBulkDelete(r.Context(), &req)
	if err != nil {
		h.logger.Error("Bulk delete failed", "error", err)
		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	response.Duration = time.Since(start)
	h.RespondJSON(w, http.StatusOK, response)
}

// processBulkCreate processes bulk creation
func (h *BulkHandler) processBulkCreate(ctx context.Context, req *BulkCreateRequest) (*BulkResponse, error) {
	response := &BulkResponse{
		EntityType: req.EntityType,
		Operation:  "create",
		Errors:     []BulkError{},
		Results:    []map[string]interface{}{},
	}

	// Process in batches
	for i := 0; i < len(req.Data); i += req.Options.BatchSize {
		end := i + req.Options.BatchSize
		if end > len(req.Data) {
			end = len(req.Data)
		}

		batch := req.Data[i:end]
		batchResponse, err := h.processBatchCreate(ctx, req.EntityType, batch, i)
		if err != nil {
			if !req.Options.ContinueOnError {
				return nil, err
			}
			response.Errors = append(response.Errors, BulkError{
				Index:   i,
				Message: err.Error(),
				Code:    "BATCH_ERROR",
			})
		}

		response.Processed += batchResponse.Processed
		response.Successful += batchResponse.Successful
		response.Failed += batchResponse.Failed
		response.Errors = append(response.Errors, batchResponse.Errors...)
		response.Results = append(response.Results, batchResponse.Results...)
	}

	response.Success = response.Failed == 0
	return response, nil
}

// processBatchCreate processes a batch of create operations
func (h *BulkHandler) processBatchCreate(ctx context.Context, entityType string, batch []map[string]interface{}, startIndex int) (*BulkResponse, error) {
	response := &BulkResponse{
		EntityType: entityType,
		Operation:  "create",
		Errors:     []BulkError{},
		Results:    []map[string]interface{}{},
	}

	for i, item := range batch {
		index := startIndex + i
		
		// Convert to appropriate request type
		req, err := h.convertToCreateRequest(entityType, item)
		if err != nil {
			response.Errors = append(response.Errors, BulkError{
				Index:   index,
				Message: err.Error(),
				Code:    "CONVERSION_ERROR",
			})
			response.Failed++
			continue
		}

		// Create entity
		result, err := h.createEntity(ctx, entityType, req)
		if err != nil {
			response.Errors = append(response.Errors, BulkError{
				Index:   index,
				Message: err.Error(),
				Code:    "CREATE_ERROR",
			})
			response.Failed++
		} else {
			response.Results = append(response.Results, result)
			response.Successful++
		}
		
		response.Processed++
	}

	return response, nil
}

// processBulkUpdate processes bulk updates
func (h *BulkHandler) processBulkUpdate(ctx context.Context, req *BulkUpdateRequest) (*BulkResponse, error) {
	response := &BulkResponse{
		EntityType: req.EntityType,
		Operation:  "update",
		Errors:     []BulkError{},
		Results:    []map[string]interface{}{},
	}

	// Process in batches
	for i := 0; i < len(req.Data); i += req.Options.BatchSize {
		end := i + req.Options.BatchSize
		if end > len(req.Data) {
			end = len(req.Data)
		}

		batch := req.Data[i:end]
		batchResponse, err := h.processBatchUpdate(ctx, req.EntityType, batch, i)
		if err != nil {
			if !req.Options.ContinueOnError {
				return nil, err
			}
			response.Errors = append(response.Errors, BulkError{
				Index:   i,
				Message: err.Error(),
				Code:    "BATCH_ERROR",
			})
		}

		response.Processed += batchResponse.Processed
		response.Successful += batchResponse.Successful
		response.Failed += batchResponse.Failed
		response.Errors = append(response.Errors, batchResponse.Errors...)
		response.Results = append(response.Results, batchResponse.Results...)
	}

	response.Success = response.Failed == 0
	return response, nil
}

// processBatchUpdate processes a batch of update operations
func (h *BulkHandler) processBatchUpdate(ctx context.Context, entityType string, batch []map[string]interface{}, startIndex int) (*BulkResponse, error) {
	response := &BulkResponse{
		EntityType: entityType,
		Operation:  "update",
		Errors:     []BulkError{},
		Results:    []map[string]interface{}{},
	}

	for i, item := range batch {
		index := startIndex + i
		
		// Convert to appropriate request type
		req, err := h.convertToUpdateRequest(entityType, item)
		if err != nil {
			response.Errors = append(response.Errors, BulkError{
				Index:   index,
				Message: err.Error(),
				Code:    "CONVERSION_ERROR",
			})
			response.Failed++
			continue
		}

		// Update entity
		result, err := h.updateEntity(ctx, entityType, req)
		if err != nil {
			response.Errors = append(response.Errors, BulkError{
				Index:   index,
				Message: err.Error(),
				Code:    "UPDATE_ERROR",
			})
			response.Failed++
		} else {
			response.Results = append(response.Results, result)
			response.Successful++
		}
		
		response.Processed++
	}

	return response, nil
}

// processBulkDelete processes bulk deletions
func (h *BulkHandler) processBulkDelete(ctx context.Context, req *BulkDeleteRequest) (*BulkResponse, error) {
	response := &BulkResponse{
		EntityType: req.EntityType,
		Operation:  "delete",
		Errors:     []BulkError{},
		Results:    []map[string]interface{}{},
	}

	// Process in batches
	for i := 0; i < len(req.IDs); i += req.Options.BatchSize {
		end := i + req.Options.BatchSize
		if end > len(req.IDs) {
			end = len(req.IDs)
		}

		batch := req.IDs[i:end]
		batchResponse, err := h.processBatchDelete(ctx, req.EntityType, batch, i)
		if err != nil {
			if !req.Options.ContinueOnError {
				return nil, err
			}
			response.Errors = append(response.Errors, BulkError{
				Index:   i,
				Message: err.Error(),
				Code:    "BATCH_ERROR",
			})
		}

		response.Processed += batchResponse.Processed
		response.Successful += batchResponse.Successful
		response.Failed += batchResponse.Failed
		response.Errors = append(response.Errors, batchResponse.Errors...)
		response.Results = append(response.Results, batchResponse.Results...)
	}

	response.Success = response.Failed == 0
	return response, nil
}

// processBatchDelete processes a batch of delete operations
func (h *BulkHandler) processBatchDelete(ctx context.Context, entityType string, batch []string, startIndex int) (*BulkResponse, error) {
	response := &BulkResponse{
		EntityType: entityType,
		Operation:  "delete",
		Errors:     []BulkError{},
		Results:    []map[string]interface{}{},
	}

	for i, id := range batch {
		index := startIndex + i
		
		// Delete entity
		err := h.deleteEntity(ctx, entityType, id)
		if err != nil {
			response.Errors = append(response.Errors, BulkError{
				Index:   index,
				ID:      id,
				Message: err.Error(),
				Code:    "DELETE_ERROR",
			})
			response.Failed++
		} else {
			response.Results = append(response.Results, map[string]interface{}{
				"id":      id,
				"deleted": true,
			})
			response.Successful++
		}
		
		response.Processed++
	}

	return response, nil
}

// Helper methods for entity operations

func (h *BulkHandler) convertToCreateRequest(entityType string, data map[string]interface{}) (interface{}, error) {
	// Convert map to JSON and then to appropriate request type
	jsonData, err := json.Marshal(data)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal data: %w", err)
	}

	switch entityType {
	case "building":
		var req domain.CreateBuildingRequest
		if err := json.Unmarshal(jsonData, &req); err != nil {
			return nil, fmt.Errorf("failed to unmarshal building request: %w", err)
		}
		return &req, nil
	case "equipment":
		var req domain.CreateEquipmentRequest
		if err := json.Unmarshal(jsonData, &req); err != nil {
			return nil, fmt.Errorf("failed to unmarshal equipment request: %w", err)
		}
		return &req, nil
	case "user":
		var req domain.CreateUserRequest
		if err := json.Unmarshal(jsonData, &req); err != nil {
			return nil, fmt.Errorf("failed to unmarshal user request: %w", err)
		}
		return &req, nil
	default:
		return nil, fmt.Errorf("unsupported entity type: %s", entityType)
	}
}

func (h *BulkHandler) convertToUpdateRequest(entityType string, data map[string]interface{}) (interface{}, error) {
	// Convert map to JSON and then to appropriate request type
	jsonData, err := json.Marshal(data)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal data: %w", err)
	}

	switch entityType {
	case "building":
		var req domain.UpdateBuildingRequest
		if err := json.Unmarshal(jsonData, &req); err != nil {
			return nil, fmt.Errorf("failed to unmarshal building request: %w", err)
		}
		return &req, nil
	case "equipment":
		var req domain.UpdateEquipmentRequest
		if err := json.Unmarshal(jsonData, &req); err != nil {
			return nil, fmt.Errorf("failed to unmarshal equipment request: %w", err)
		}
		return &req, nil
	case "user":
		var req domain.UpdateUserRequest
		if err := json.Unmarshal(jsonData, &req); err != nil {
			return nil, fmt.Errorf("failed to unmarshal user request: %w", err)
		}
		return &req, nil
	default:
		return nil, fmt.Errorf("unsupported entity type: %s", entityType)
	}
}

func (h *BulkHandler) createEntity(ctx context.Context, entityType string, req interface{}) (map[string]interface{}, error) {
	switch entityType {
	case "building":
		if req, ok := req.(*domain.CreateBuildingRequest); ok {
			building, err := h.buildingUC.CreateBuilding(ctx, req)
			if err != nil {
				return nil, err
			}
			return map[string]interface{}{
				"id":   building.ID,
				"name": building.Name,
			}, nil
		}
	case "equipment":
		if req, ok := req.(*domain.CreateEquipmentRequest); ok {
			equipment, err := h.equipmentUC.CreateEquipment(ctx, req)
			if err != nil {
				return nil, err
			}
			return map[string]interface{}{
				"id":   equipment.ID,
				"name": equipment.Name,
			}, nil
		}
	case "user":
		if req, ok := req.(*domain.CreateUserRequest); ok {
			user, err := h.userUC.CreateUser(ctx, req)
			if err != nil {
				return nil, err
			}
			return map[string]interface{}{
				"id":    user.ID,
				"email": user.Email,
			}, nil
		}
	}
	return nil, fmt.Errorf("unsupported entity type: %s", entityType)
}

func (h *BulkHandler) updateEntity(ctx context.Context, entityType string, req interface{}) (map[string]interface{}, error) {
	switch entityType {
	case "building":
		if req, ok := req.(*domain.UpdateBuildingRequest); ok {
			building, err := h.buildingUC.UpdateBuilding(ctx, req)
			if err != nil {
				return nil, err
			}
			return map[string]interface{}{
				"id":   building.ID,
				"name": building.Name,
			}, nil
		}
	case "equipment":
		if req, ok := req.(*domain.UpdateEquipmentRequest); ok {
			equipment, err := h.equipmentUC.UpdateEquipment(ctx, req)
			if err != nil {
				return nil, err
			}
			return map[string]interface{}{
				"id":   equipment.ID,
				"name": equipment.Name,
			}, nil
		}
	case "user":
		if req, ok := req.(*domain.UpdateUserRequest); ok {
			user, err := h.userUC.UpdateUser(ctx, req)
			if err != nil {
				return nil, err
			}
			return map[string]interface{}{
				"id":    user.ID,
				"email": user.Email,
			}, nil
		}
	}
	return nil, fmt.Errorf("unsupported entity type: %s", entityType)
}

func (h *BulkHandler) deleteEntity(ctx context.Context, entityType string, id string) error {
	switch entityType {
	case "building":
		return h.buildingUC.DeleteBuilding(ctx, id)
	case "equipment":
		return h.equipmentUC.DeleteEquipment(ctx, id)
	case "user":
		return h.userUC.DeleteUser(ctx, id)
	default:
		return fmt.Errorf("unsupported entity type: %s", entityType)
	}
}
