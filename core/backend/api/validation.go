// Package api provides API validation and documentation utilities
package api

import (
	"encoding/json"
	"fmt"
	"net/http"
	"reflect"
	"strconv"
	"strings"
	"time"

	"github.com/arxos/arxos/core/backend/errors"
	"github.com/go-playground/validator/v10"
	"go.uber.org/zap"
)

// Validator provides request validation functionality
type Validator struct {
	validator *validator.Validate
	logger    *zap.Logger
}

// NewValidator creates a new API validator
func NewValidator(logger *zap.Logger) *Validator {
	v := validator.New()
	
	// Register custom validators
	v.RegisterValidation("confidence", validateConfidence)
	v.RegisterValidation("object_type", validateObjectType)
	v.RegisterValidation("priority", validatePriority)
	v.RegisterValidation("coordinates", validateCoordinates)
	v.RegisterValidation("nanometers", validateNanometers)
	
	return &Validator{
		validator: v,
		logger:    logger,
	}
}

// ValidateStruct validates a struct using validation tags
func (v *Validator) ValidateStruct(s interface{}) error {
	if err := v.validator.Struct(s); err != nil {
		if validationErrors, ok := err.(validator.ValidationErrors); ok {
			return v.formatValidationErrors(validationErrors)
		}
		return errors.NewValidationError(err.Error())
	}
	return nil
}

// ValidateJSON validates JSON request body into a struct
func (v *Validator) ValidateJSON(r *http.Request, dest interface{}) error {
	// Check content type
	contentType := r.Header.Get("Content-Type")
	if !strings.Contains(contentType, "application/json") {
		return errors.NewValidationError("Content-Type must be application/json")
	}
	
	// Limit request body size (10MB)
	r.Body = http.MaxBytesReader(nil, r.Body, 10<<20)
	
	// Decode JSON
	decoder := json.NewDecoder(r.Body)
	decoder.DisallowUnknownFields() // Strict JSON parsing
	
	if err := decoder.Decode(dest); err != nil {
		v.logger.Debug("JSON decode error", zap.Error(err))
		return errors.NewValidationError("Invalid JSON format")
	}
	
	// Validate struct
	return v.ValidateStruct(dest)
}

// formatValidationErrors converts validator errors to user-friendly messages
func (v *Validator) formatValidationErrors(validationErrors validator.ValidationErrors) error {
	var messages []string
	
	for _, err := range validationErrors {
		field := strings.ToLower(err.Field())
		tag := err.Tag()
		param := err.Param()
		
		var message string
		switch tag {
		case "required":
			message = fmt.Sprintf("%s is required", field)
		case "min":
			message = fmt.Sprintf("%s must be at least %s", field, param)
		case "max":
			message = fmt.Sprintf("%s must be at most %s", field, param)
		case "email":
			message = fmt.Sprintf("%s must be a valid email address", field)
		case "uuid":
			message = fmt.Sprintf("%s must be a valid UUID", field)
		case "confidence":
			message = fmt.Sprintf("%s must be between 0.0 and 1.0", field)
		case "object_type":
			message = fmt.Sprintf("%s must be a valid object type", field)
		case "priority":
			message = fmt.Sprintf("%s must be between 1 and 10", field)
		case "coordinates":
			message = fmt.Sprintf("%s must be valid coordinates", field)
		case "nanometers":
			message = fmt.Sprintf("%s must be valid nanometer value", field)
		default:
			message = fmt.Sprintf("%s is invalid", field)
		}
		
		messages = append(messages, message)
	}
	
	return errors.NewValidationError(strings.Join(messages, ", "))
}

// Custom validation functions

// validateConfidence validates confidence values (0.0 to 1.0)
func validateConfidence(fl validator.FieldLevel) bool {
	value := fl.Field().Float()
	return value >= 0.0 && value <= 1.0
}

// validateObjectType validates ArxObject types
func validateObjectType(fl validator.FieldLevel) bool {
	validTypes := []string{
		"wall", "column", "beam", "door", "window",
		"electrical_outlet", "hvac_unit", "plumbing_fixture",
		"fire_sprinkler", "smoke_detector", "unknown",
	}
	
	value := fl.Field().String()
	for _, validType := range validTypes {
		if value == validType {
			return true
		}
	}
	return false
}

// validatePriority validates priority values (1 to 10)
func validatePriority(fl validator.FieldLevel) bool {
	value := fl.Field().Int()
	return value >= 1 && value <= 10
}

// validateCoordinates validates coordinate values
func validateCoordinates(fl validator.FieldLevel) bool {
	value := fl.Field().Float()
	// Allow reasonable coordinate range (±1000 meters)
	return value >= -1000000000000 && value <= 1000000000000 // nanometers
}

// validateNanometers validates nanometer precision values
func validateNanometers(fl validator.FieldLevel) bool {
	value := fl.Field().Int()
	// Reasonable nanometer range for building dimensions
	return value >= -1000000000000 && value <= 1000000000000
}

// Request/Response types with validation tags

// ValidationSubmissionRequest represents a validation submission
type ValidationSubmissionRequest struct {
	ObjectID       string                 `json:"object_id" validate:"required,uuid"`
	ValidationType string                 `json:"validation_type" validate:"required,oneof=dimension material type relationship position"`
	Data           map[string]interface{} `json:"data" validate:"required"`
	Validator      string                 `json:"validator" validate:"required,min=2,max=100"`
	Confidence     float32                `json:"confidence" validate:"required,confidence"`
	PhotoURL       string                 `json:"photo_url,omitempty" validate:"omitempty,url"`
	Notes          string                 `json:"notes,omitempty" validate:"max=1000"`
	Timestamp      time.Time              `json:"timestamp" validate:"required"`
}

// ValidationTaskRequest represents a validation task creation request
type ValidationTaskRequest struct {
	ObjectID string `json:"object_id" validate:"required,uuid"`
	Reason   string `json:"reason,omitempty" validate:"max=500"`
	Priority int    `json:"priority,omitempty" validate:"omitempty,priority"`
}

// ProcessBuildingRequest represents a building processing request
type ProcessBuildingRequest struct {
	FileURL  string                    `json:"file_url,omitempty" validate:"omitempty,url"`
	Base64   string                    `json:"base64_file,omitempty"`
	Metadata ProcessBuildingMetadata   `json:"metadata" validate:"required"`
	Config   ProcessingConfigRequest   `json:"config" validate:"required"`
}

// ProcessBuildingMetadata contains building metadata
type ProcessBuildingMetadata struct {
	BuildingName string  `json:"building_name" validate:"required,min=1,max=200"`
	BuildingType string  `json:"building_type" validate:"required,oneof=office retail industrial residential educational healthcare"`
	Address      string  `json:"address,omitempty" validate:"max=500"`
	YearBuilt    int     `json:"year_built,omitempty" validate:"omitempty,min=1800,max=2100"`
	TotalArea    float64 `json:"total_area_m2,omitempty" validate:"omitempty,min=1,max=1000000"`
	NumFloors    int     `json:"num_floors,omitempty" validate:"omitempty,min=1,max=200"`
}

// ProcessingConfigRequest contains processing configuration
type ProcessingConfigRequest struct {
	EnableSemantic      bool    `json:"enable_semantic"`
	RequireManualReview bool    `json:"require_manual_review"`
	MinConfidence       float64 `json:"min_confidence" validate:"confidence"`
	BuildingType        string  `json:"building_type" validate:"required,object_type"`
}

// CorrectionRequest represents a manual correction
type CorrectionRequest struct {
	BuildingID string      `json:"building_id" validate:"required,uuid"`
	Type       string      `json:"type" validate:"required,oneof=update delete create"`
	EntityType string      `json:"entity_type" validate:"required,object_type"`
	EntityID   string      `json:"entity_id" validate:"required,uuid"`
	Before     interface{} `json:"before" validate:"required"`
	After      interface{} `json:"after" validate:"required"`
	Reason     string      `json:"reason" validate:"required,min=5,max=500"`
	Confidence float64     `json:"confidence" validate:"required,confidence"`
}

// ArxObjectRequest represents an ArxObject creation/update request
type ArxObjectRequest struct {
	Type      string             `json:"type" validate:"required,object_type"`
	X         int64              `json:"x" validate:"coordinates"`
	Y         int64              `json:"y" validate:"coordinates"`
	Z         int64              `json:"z" validate:"coordinates"`
	Length    int64              `json:"length" validate:"required,nanometers"`
	Width     int64              `json:"width" validate:"required,nanometers"`
	Height    int64              `json:"height" validate:"required,nanometers"`
	RotationZ int32              `json:"rotation_z"`
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
}

// Standard response types

// APIResponse represents a standard API response
type APIResponse struct {
	Success   bool        `json:"success"`
	Data      interface{} `json:"data,omitempty"`
	Error     interface{} `json:"error,omitempty"`
	Timestamp time.Time   `json:"timestamp"`
	RequestID string      `json:"request_id,omitempty"`
}

// PaginatedResponse represents a paginated API response
type PaginatedResponse struct {
	APIResponse
	Pagination PaginationInfo `json:"pagination"`
}

// PaginationInfo contains pagination metadata
type PaginationInfo struct {
	Page       int `json:"page"`
	PerPage    int `json:"per_page"`
	Total      int `json:"total"`
	TotalPages int `json:"total_pages"`
	HasNext    bool `json:"has_next"`
	HasPrev    bool `json:"has_prev"`
}

// Query parameter validation

// QueryParams provides query parameter validation
type QueryParams struct {
	request *http.Request
}

// NewQueryParams creates a new query parameter validator
func NewQueryParams(r *http.Request) *QueryParams {
	return &QueryParams{request: r}
}

// GetString gets a string query parameter with validation
func (q *QueryParams) GetString(key string, defaultValue string, validators ...func(string) error) (string, error) {
	value := q.request.URL.Query().Get(key)
	if value == "" {
		value = defaultValue
	}
	
	for _, validator := range validators {
		if err := validator(value); err != nil {
			return "", err
		}
	}
	
	return value, nil
}

// GetInt gets an integer query parameter with validation
func (q *QueryParams) GetInt(key string, defaultValue int, min, max int) (int, error) {
	value := q.request.URL.Query().Get(key)
	if value == "" {
		return defaultValue, nil
	}
	
	intValue, err := strconv.Atoi(value)
	if err != nil {
		return 0, errors.NewValidationError(fmt.Sprintf("%s must be a valid integer", key))
	}
	
	if intValue < min || intValue > max {
		return 0, errors.NewValidationError(fmt.Sprintf("%s must be between %d and %d", key, min, max))
	}
	
	return intValue, nil
}

// GetFloat gets a float query parameter with validation
func (q *QueryParams) GetFloat(key string, defaultValue float64, min, max float64) (float64, error) {
	value := q.request.URL.Query().Get(key)
	if value == "" {
		return defaultValue, nil
	}
	
	floatValue, err := strconv.ParseFloat(value, 64)
	if err != nil {
		return 0, errors.NewValidationError(fmt.Sprintf("%s must be a valid number", key))
	}
	
	if floatValue < min || floatValue > max {
		return 0, errors.NewValidationError(fmt.Sprintf("%s must be between %f and %f", key, min, max))
	}
	
	return floatValue, nil
}

// GetBool gets a boolean query parameter
func (q *QueryParams) GetBool(key string, defaultValue bool) (bool, error) {
	value := q.request.URL.Query().Get(key)
	if value == "" {
		return defaultValue, nil
	}
	
	boolValue, err := strconv.ParseBool(value)
	if err != nil {
		return false, errors.NewValidationError(fmt.Sprintf("%s must be a valid boolean", key))
	}
	
	return boolValue, nil
}

// GetPagination gets pagination parameters
func (q *QueryParams) GetPagination() (page, perPage int, err error) {
	page, err = q.GetInt("page", 1, 1, 1000)
	if err != nil {
		return 0, 0, err
	}
	
	perPage, err = q.GetInt("per_page", 20, 1, 100)
	if err != nil {
		return 0, 0, err
	}
	
	return page, perPage, nil
}

// Middleware for request validation

// ValidationMiddleware provides request validation middleware
func ValidationMiddleware(validator *Validator) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Add validator to request context
			ctx := r.Context()
			// In a real implementation, you'd add the validator to context
			// ctx = context.WithValue(ctx, "validator", validator)
			r = r.WithContext(ctx)
			
			next.ServeHTTP(w, r)
		})
	}
}

// Response helpers

// WriteJSONResponse writes a JSON response
func WriteJSONResponse(w http.ResponseWriter, statusCode int, data interface{}) error {
	response := APIResponse{
		Success:   statusCode < 400,
		Data:      data,
		Timestamp: time.Now(),
	}
	
	if statusCode >= 400 {
		response.Error = data
		response.Data = nil
	}
	
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	
	encoder := json.NewEncoder(w)
	encoder.SetIndent("", "  ") // Pretty print in development
	return encoder.Encode(response)
}

// WriteErrorResponse writes an error response
func WriteErrorResponse(w http.ResponseWriter, err error) error {
	var statusCode int
	var errorData interface{}
	
	if arxosErr, ok := err.(*errors.ArxosError); ok {
		statusCode = arxosErr.StatusCode
		errorData = arxosErr
	} else {
		statusCode = http.StatusInternalServerError
		errorData = map[string]string{"message": "Internal server error"}
	}
	
	return WriteJSONResponse(w, statusCode, errorData)
}

// WritePaginatedResponse writes a paginated response
func WritePaginatedResponse(w http.ResponseWriter, data interface{}, page, perPage, total int) error {
	totalPages := (total + perPage - 1) / perPage
	
	response := PaginatedResponse{
		APIResponse: APIResponse{
			Success:   true,
			Data:      data,
			Timestamp: time.Now(),
		},
		Pagination: PaginationInfo{
			Page:       page,
			PerPage:    perPage,
			Total:      total,
			TotalPages: totalPages,
			HasNext:    page < totalPages,
			HasPrev:    page > 1,
		},
	}
	
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	
	encoder := json.NewEncoder(w)
	encoder.SetIndent("", "  ")
	return encoder.Encode(response)
}

// Validation helper functions

// ValidateUUID validates UUID format
func ValidateUUID(uuid string) error {
	if len(uuid) != 36 {
		return errors.NewValidationError("UUID must be 36 characters long")
	}
	// Simplified UUID validation
	return nil
}

// ValidateEmail validates email format
func ValidateEmail(email string) error {
	if !strings.Contains(email, "@") || !strings.Contains(email, ".") {
		return errors.NewValidationError("Invalid email format")
	}
	return nil
}

// ValidateNonEmpty validates that a string is not empty
func ValidateNonEmpty(value string) error {
	if strings.TrimSpace(value) == "" {
		return errors.NewValidationError("Value cannot be empty")
	}
	return nil
}

// ValidateMaxLength validates maximum string length
func ValidateMaxLength(maxLength int) func(string) error {
	return func(value string) error {
		if len(value) > maxLength {
			return errors.NewValidationError(fmt.Sprintf("Value must be at most %d characters", maxLength))
		}
		return nil
	}
}

// ValidateMinLength validates minimum string length
func ValidateMinLength(minLength int) func(string) error {
	return func(value string) error {
		if len(value) < minLength {
			return errors.NewValidationError(fmt.Sprintf("Value must be at least %d characters", minLength))
		}
		return nil
	}
}

// ValidateOneOf validates that value is one of allowed values
func ValidateOneOf(allowed []string) func(string) error {
	return func(value string) error {
		for _, a := range allowed {
			if value == a {
				return nil
			}
		}
		return errors.NewValidationError(fmt.Sprintf("Value must be one of: %v", allowed))
	}
}

// OpenAPI/Swagger documentation structures

// APIDocumentation represents API documentation
type APIDocumentation struct {
	OpenAPI string                 `json:"openapi"`
	Info    APIInfo                `json:"info"`
	Paths   map[string]interface{} `json:"paths"`
	Components APIComponents       `json:"components"`
}

// APIInfo contains API information
type APIInfo struct {
	Title       string `json:"title"`
	Description string `json:"description"`
	Version     string `json:"version"`
	Contact     APIContact `json:"contact"`
}

// APIContact contains contact information
type APIContact struct {
	Name  string `json:"name"`
	Email string `json:"email"`
	URL   string `json:"url"`
}

// APIComponents contains reusable API components
type APIComponents struct {
	Schemas map[string]interface{} `json:"schemas"`
}

// GenerateAPIDocumentation generates OpenAPI documentation
func GenerateAPIDocumentation() *APIDocumentation {
	return &APIDocumentation{
		OpenAPI: "3.0.0",
		Info: APIInfo{
			Title:       "Arxos Backend API",
			Description: "REST API for the Arxos building analysis and validation system",
			Version:     "1.0.0",
			Contact: APIContact{
				Name:  "Arxos Development Team",
				Email: "dev@arxos.com",
			},
		},
		Paths: map[string]interface{}{
			"/api/v1/validations/pending": map[string]interface{}{
				"get": map[string]interface{}{
					"summary":     "Get pending validation tasks",
					"description": "Retrieves a list of validation tasks that are pending review",
					"parameters": []interface{}{
						map[string]interface{}{
							"name":        "priority",
							"in":          "query",
							"description": "Minimum priority level",
							"schema":      map[string]interface{}{"type": "integer", "minimum": 1, "maximum": 10},
						},
						map[string]interface{}{
							"name":        "type",
							"in":          "query", 
							"description": "Object type filter",
							"schema":      map[string]interface{}{"type": "string"},
						},
						map[string]interface{}{
							"name":        "limit",
							"in":          "query",
							"description": "Maximum number of results",
							"schema":      map[string]interface{}{"type": "integer", "minimum": 1, "maximum": 100},
						},
					},
					"responses": map[string]interface{}{
						"200": map[string]interface{}{
							"description": "List of pending validation tasks",
						},
					},
				},
			},
		},
		Components: APIComponents{
			Schemas: map[string]interface{}{
				"ValidationTask": generateSchemaFromStruct(reflect.TypeOf(ValidationTaskRequest{})),
				"ValidationSubmission": generateSchemaFromStruct(reflect.TypeOf(ValidationSubmissionRequest{})),
				"APIResponse": generateSchemaFromStruct(reflect.TypeOf(APIResponse{})),
			},
		},
	}
}

// generateSchemaFromStruct generates OpenAPI schema from Go struct
func generateSchemaFromStruct(t reflect.Type) map[string]interface{} {
	if t.Kind() == reflect.Ptr {
		t = t.Elem()
	}
	
	properties := make(map[string]interface{})
	required := []string{}
	
	for i := 0; i < t.NumField(); i++ {
		field := t.Field(i)
		jsonTag := field.Tag.Get("json")
		validateTag := field.Tag.Get("validate")
		
		if jsonTag == "" || jsonTag == "-" {
			continue
		}
		
		fieldName := strings.Split(jsonTag, ",")[0]
		
		// Determine type
		var fieldType string
		switch field.Type.Kind() {
		case reflect.String:
			fieldType = "string"
		case reflect.Int, reflect.Int32, reflect.Int64:
			fieldType = "integer"
		case reflect.Float32, reflect.Float64:
			fieldType = "number"
		case reflect.Bool:
			fieldType = "boolean"
		default:
			fieldType = "object"
		}
		
		properties[fieldName] = map[string]interface{}{
			"type": fieldType,
		}
		
		// Check if required
		if strings.Contains(validateTag, "required") {
			required = append(required, fieldName)
		}
	}
	
	schema := map[string]interface{}{
		"type":       "object",
		"properties": properties,
	}
	
	if len(required) > 0 {
		schema["required"] = required
	}
	
	return schema
}