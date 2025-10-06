package validation

import (
	"fmt"
	"net/http"
	"regexp"
	"strconv"
	"strings"
	"time"
)

// Validator provides comprehensive request validation
type Validator struct {
	rules map[string]func(string) error
}

// NewValidator creates a new validator instance
func NewValidator() *Validator {
	v := &Validator{
		rules: make(map[string]func(string) error),
	}

	// Register validation rules
	v.registerRules()

	return v
}

// registerRules registers all validation rules
func (v *Validator) registerRules() {
	v.rules["required"] = func(value string) error {
		if strings.TrimSpace(value) == "" {
			return fmt.Errorf("field is required")
		}
		return nil
	}

	v.rules["email"] = func(value string) error {
		if !validateEmail(value) {
			return fmt.Errorf("must be a valid email address")
		}
		return nil
	}

	v.rules["uuid"] = func(value string) error {
		if !validateUUID(value) {
			return fmt.Errorf("must be a valid UUID")
		}
		return nil
	}

	v.rules["date"] = func(value string) error {
		if !validateDate(value) {
			return fmt.Errorf("must be a valid date (YYYY-MM-DD)")
		}
		return nil
	}

	v.rules["datetime"] = func(value string) error {
		if !validateDateTime(value) {
			return fmt.Errorf("must be a valid datetime")
		}
		return nil
	}

	v.rules["alphanumeric"] = func(value string) error {
		if !validateAlphanumeric(value) {
			return fmt.Errorf("must contain only letters and numbers")
		}
		return nil
	}

	v.rules["building_path"] = func(value string) error {
		if !validateBuildingPath(value) {
			return fmt.Errorf("must be a valid building path")
		}
		return nil
	}

	v.rules["component_type"] = func(value string) error {
		if !validateComponentType(value) {
			return fmt.Errorf("must be a valid component type")
		}
		return nil
	}

	v.rules["equipment_type"] = func(value string) error {
		if !validateEquipmentType(value) {
			return fmt.Errorf("must be a valid equipment type")
		}
		return nil
	}
}

// ValidateStruct validates a struct using struct tags
func (v *Validator) ValidateStruct(s any) map[string]string {
	errors := make(map[string]string)

	// Simple validation for common struct types
	switch s := s.(type) {
	case *CreateUserRequest:
		errors = v.validateCreateUserRequest(s)
	case *UpdateUserRequest:
		errors = v.validateUpdateUserRequest(s)
	case *CreateBuildingRequest:
		errors = v.validateCreateBuildingRequest(s)
	case *UpdateBuildingRequest:
		errors = v.validateUpdateBuildingRequest(s)
	case *CreateEquipmentRequest:
		errors = v.validateCreateEquipmentRequest(s)
	case *UpdateEquipmentRequest:
		errors = v.validateUpdateEquipmentRequest(s)
	case *CreateComponentRequest:
		errors = v.validateCreateComponentRequest(s)
	case *UpdateComponentRequest:
		errors = v.validateUpdateComponentRequest(s)
	case *ImportIFCRequest:
		errors = v.validateImportIFCRequest(s)
	case *ExportIFCRequest:
		errors = v.validateExportIFCRequest(s)
	case *LoginRequest:
		errors = v.validateLoginRequest(s)
	case *RegisterRequest:
		errors = v.validateRegisterRequest(s)
	default:
		// Generic validation for unknown types
		errors["type"] = "unsupported validation type"
	}

	return errors
}

// ValidateRequest validates an HTTP request
func (v *Validator) ValidateRequest(r *http.Request, target any) map[string]string {
	// Validate content type for POST/PUT/PATCH requests
	if r.Method == "POST" || r.Method == "PUT" || r.Method == "PATCH" {
		contentType := r.Header.Get("Content-Type")
		if !strings.Contains(contentType, "application/json") {
			return map[string]string{
				"content_type": "Content-Type must be application/json",
			}
		}
	}

	// Validate struct if provided
	if target != nil {
		return v.ValidateStruct(target)
	}

	return nil
}

// ValidateQueryParams validates query parameters
func (v *Validator) ValidateQueryParams(r *http.Request, rules map[string]string) map[string]string {
	errors := make(map[string]string)
	query := r.URL.Query()

	for param, rule := range rules {
		value := query.Get(param)
		if value == "" {
			continue // Optional parameters
		}

		if err := v.validateQueryParam(param, value, rule); err != nil {
			errors[param] = err.Error()
		}
	}

	return errors
}

// validateQueryParam validates a single query parameter
func (v *Validator) validateQueryParam(param, value, rule string) error {
	switch rule {
	case "required":
		if value == "" {
			return fmt.Errorf("%s is required", param)
		}
	case "int":
		if _, err := strconv.Atoi(value); err != nil {
			return fmt.Errorf("%s must be an integer", param)
		}
	case "float":
		if _, err := strconv.ParseFloat(value, 64); err != nil {
			return fmt.Errorf("%s must be a number", param)
		}
	case "bool":
		if _, err := strconv.ParseBool(value); err != nil {
			return fmt.Errorf("%s must be true or false", param)
		}
	case "email":
		if !validateEmail(value) {
			return fmt.Errorf("%s must be a valid email address", param)
		}
	case "uuid":
		if !validateUUID(value) {
			return fmt.Errorf("%s must be a valid UUID", param)
		}
	case "date":
		if !validateDate(value) {
			return fmt.Errorf("%s must be a valid date (YYYY-MM-DD)", param)
		}
	case "datetime":
		if !validateDateTime(value) {
			return fmt.Errorf("%s must be a valid datetime", param)
		}
	case "alphanumeric":
		if !validateAlphanumeric(value) {
			return fmt.Errorf("%s must contain only letters and numbers", param)
		}
	}

	return nil
}

// Validation methods for specific request types

func (v *Validator) validateCreateUserRequest(req *CreateUserRequest) map[string]string {
	errors := make(map[string]string)

	if req.Email == "" {
		errors["email"] = "email is required"
	} else if !validateEmail(req.Email) {
		errors["email"] = "email must be valid"
	}

	if req.Name == "" {
		errors["name"] = "name is required"
	} else if len(req.Name) < 2 || len(req.Name) > 100 {
		errors["name"] = "name must be between 2 and 100 characters"
	}

	if req.Role == "" {
		errors["role"] = "role is required"
	} else if !isValidRole(req.Role) {
		errors["role"] = "role must be one of: admin, user, manager, viewer"
	}

	if req.Password == "" {
		errors["password"] = "password is required"
	} else if len(req.Password) < 8 || len(req.Password) > 128 {
		errors["password"] = "password must be between 8 and 128 characters"
	}

	return errors
}

func (v *Validator) validateUpdateUserRequest(req *UpdateUserRequest) map[string]string {
	errors := make(map[string]string)

	if req.ID == "" {
		errors["id"] = "id is required"
	} else if !validateUUID(req.ID) {
		errors["id"] = "id must be a valid UUID"
	}

	if req.Name != "" && (len(req.Name) < 2 || len(req.Name) > 100) {
		errors["name"] = "name must be between 2 and 100 characters"
	}

	if req.Role != "" && !isValidRole(req.Role) {
		errors["role"] = "role must be one of: admin, user, manager, viewer"
	}

	return errors
}

func (v *Validator) validateCreateBuildingRequest(req *CreateBuildingRequest) map[string]string {
	errors := make(map[string]string)

	if req.Name == "" {
		errors["name"] = "name is required"
	} else if len(req.Name) < 2 || len(req.Name) > 100 {
		errors["name"] = "name must be between 2 and 100 characters"
	}

	if req.Address == "" {
		errors["address"] = "address is required"
	} else if len(req.Address) < 5 || len(req.Address) > 200 {
		errors["address"] = "address must be between 5 and 200 characters"
	}

	if req.Latitude < -90 || req.Latitude > 90 {
		errors["latitude"] = "latitude must be between -90 and 90"
	}

	if req.Longitude < -180 || req.Longitude > 180 {
		errors["longitude"] = "longitude must be between -180 and 180"
	}

	if req.Description != "" && len(req.Description) > 500 {
		errors["description"] = "description must be less than 500 characters"
	}

	return errors
}

func (v *Validator) validateUpdateBuildingRequest(req *UpdateBuildingRequest) map[string]string {
	errors := make(map[string]string)

	if req.ID == "" {
		errors["id"] = "id is required"
	} else if !validateUUID(req.ID) {
		errors["id"] = "id must be a valid UUID"
	}

	if req.Name != "" && (len(req.Name) < 2 || len(req.Name) > 100) {
		errors["name"] = "name must be between 2 and 100 characters"
	}

	if req.Address != "" && (len(req.Address) < 5 || len(req.Address) > 200) {
		errors["address"] = "address must be between 5 and 200 characters"
	}

	if req.Latitude != nil && (*req.Latitude < -90 || *req.Latitude > 90) {
		errors["latitude"] = "latitude must be between -90 and 90"
	}

	if req.Longitude != nil && (*req.Longitude < -180 || *req.Longitude > 180) {
		errors["longitude"] = "longitude must be between -180 and 180"
	}

	if req.Description != "" && len(req.Description) > 500 {
		errors["description"] = "description must be less than 500 characters"
	}

	return errors
}

func (v *Validator) validateCreateEquipmentRequest(req *CreateEquipmentRequest) map[string]string {
	errors := make(map[string]string)

	if req.Name == "" {
		errors["name"] = "name is required"
	} else if len(req.Name) < 2 || len(req.Name) > 100 {
		errors["name"] = "name must be between 2 and 100 characters"
	}

	if req.BuildingID == "" {
		errors["building_id"] = "building_id is required"
	} else if !validateUUID(req.BuildingID) {
		errors["building_id"] = "building_id must be a valid UUID"
	}

	if req.FloorID != "" && !validateUUID(req.FloorID) {
		errors["floor_id"] = "floor_id must be a valid UUID"
	}

	if req.RoomID != "" && !validateUUID(req.RoomID) {
		errors["room_id"] = "room_id must be a valid UUID"
	}

	if req.Type == "" {
		errors["type"] = "type is required"
	} else if !validateEquipmentType(req.Type) {
		errors["type"] = "type must be a valid equipment type"
	}

	if req.Status != "" && !isValidEquipmentStatus(req.Status) {
		errors["status"] = "status must be one of: operational, maintenance, offline, retired"
	}

	return errors
}

func (v *Validator) validateUpdateEquipmentRequest(req *UpdateEquipmentRequest) map[string]string {
	errors := make(map[string]string)

	if req.ID == "" {
		errors["id"] = "id is required"
	} else if !validateUUID(req.ID) {
		errors["id"] = "id must be a valid UUID"
	}

	if req.Name != "" && (len(req.Name) < 2 || len(req.Name) > 100) {
		errors["name"] = "name must be between 2 and 100 characters"
	}

	if req.FloorID != "" && !validateUUID(req.FloorID) {
		errors["floor_id"] = "floor_id must be a valid UUID"
	}

	if req.RoomID != "" && !validateUUID(req.RoomID) {
		errors["room_id"] = "room_id must be a valid UUID"
	}

	if req.Type != "" && !validateEquipmentType(req.Type) {
		errors["type"] = "type must be a valid equipment type"
	}

	if req.Status != "" && !isValidEquipmentStatus(req.Status) {
		errors["status"] = "status must be one of: operational, maintenance, offline, retired"
	}

	return errors
}

func (v *Validator) validateCreateComponentRequest(req *CreateComponentRequest) map[string]string {
	errors := make(map[string]string)

	if req.Name == "" {
		errors["name"] = "name is required"
	} else if len(req.Name) < 2 || len(req.Name) > 100 {
		errors["name"] = "name must be between 2 and 100 characters"
	}

	if req.Type == "" {
		errors["type"] = "type is required"
	} else if !validateComponentType(req.Type) {
		errors["type"] = "type must be a valid component type"
	}

	if req.Path == "" {
		errors["path"] = "path is required"
	} else if !validateBuildingPath(req.Path) {
		errors["path"] = "path must be a valid building path"
	}

	if req.Building == "" {
		errors["building"] = "building is required"
	} else if !validateUUID(req.Building) {
		errors["building"] = "building must be a valid UUID"
	}

	if req.Floor != "" && !validateUUID(req.Floor) {
		errors["floor"] = "floor must be a valid UUID"
	}

	if req.Room != "" && !validateUUID(req.Room) {
		errors["room"] = "room must be a valid UUID"
	}

	return errors
}

func (v *Validator) validateUpdateComponentRequest(req *UpdateComponentRequest) map[string]string {
	errors := make(map[string]string)

	if req.ID == "" {
		errors["id"] = "id is required"
	} else if !validateUUID(req.ID) {
		errors["id"] = "id must be a valid UUID"
	}

	if req.Name != "" && (len(req.Name) < 2 || len(req.Name) > 100) {
		errors["name"] = "name must be between 2 and 100 characters"
	}

	if req.Type != "" && !validateComponentType(req.Type) {
		errors["type"] = "type must be a valid component type"
	}

	if req.Path != "" && !validateBuildingPath(req.Path) {
		errors["path"] = "path must be a valid building path"
	}

	if req.Building != "" && !validateUUID(req.Building) {
		errors["building"] = "building must be a valid UUID"
	}

	if req.Floor != "" && !validateUUID(req.Floor) {
		errors["floor"] = "floor must be a valid UUID"
	}

	if req.Room != "" && !validateUUID(req.Room) {
		errors["room"] = "room must be a valid UUID"
	}

	return errors
}

func (v *Validator) validateImportIFCRequest(req *ImportIFCRequest) map[string]string {
	errors := make(map[string]string)

	if req.RepositoryID == "" {
		errors["repository_id"] = "repository_id is required"
	} else if !validateUUID(req.RepositoryID) {
		errors["repository_id"] = "repository_id must be a valid UUID"
	}

	if req.IFCData == "" {
		errors["ifc_data"] = "ifc_data is required"
	}

	if req.FileName == "" {
		errors["file_name"] = "file_name is required"
	} else if len(req.FileName) > 255 {
		errors["file_name"] = "file_name must be less than 255 characters"
	}

	if req.FileSize <= 0 || req.FileSize > 1073741824 { // Max 1GB
		errors["file_size"] = "file_size must be between 1 and 1073741824 bytes"
	}

	if req.Version != "" && !isValidIFCVersion(req.Version) {
		errors["version"] = "version must be one of: IFC2x3, IFC4, IFC4x1, IFC4x2, IFC4x3"
	}

	if req.Discipline != "" && !isValidDiscipline(req.Discipline) {
		errors["discipline"] = "discipline must be one of: architectural, structural, hvac, electrical, plumbing, fire_safety"
	}

	return errors
}

func (v *Validator) validateExportIFCRequest(req *ExportIFCRequest) map[string]string {
	errors := make(map[string]string)

	if req.BuildingID == "" {
		errors["building_id"] = "building_id is required"
	} else if !validateUUID(req.BuildingID) {
		errors["building_id"] = "building_id must be a valid UUID"
	}

	if req.Version == "" {
		errors["version"] = "version is required"
	} else if !isValidIFCVersion(req.Version) {
		errors["version"] = "version must be one of: IFC2x3, IFC4, IFC4x1, IFC4x2, IFC4x3"
	}

	if req.Discipline != "" && !isValidDiscipline(req.Discipline) {
		errors["discipline"] = "discipline must be one of: architectural, structural, hvac, electrical, plumbing, fire_safety"
	}

	if req.Format != "" && !isValidFormat(req.Format) {
		errors["format"] = "format must be one of: ifc, step, xml"
	}

	return errors
}

func (v *Validator) validateLoginRequest(req *LoginRequest) map[string]string {
	errors := make(map[string]string)

	if req.Email == "" {
		errors["email"] = "email is required"
	} else if !validateEmail(req.Email) {
		errors["email"] = "email must be valid"
	}

	if req.Password == "" {
		errors["password"] = "password is required"
	} else if len(req.Password) < 8 || len(req.Password) > 128 {
		errors["password"] = "password must be between 8 and 128 characters"
	}

	return errors
}

func (v *Validator) validateRegisterRequest(req *RegisterRequest) map[string]string {
	errors := make(map[string]string)

	if req.Email == "" {
		errors["email"] = "email is required"
	} else if !validateEmail(req.Email) {
		errors["email"] = "email must be valid"
	}

	if req.Name == "" {
		errors["name"] = "name is required"
	} else if len(req.Name) < 2 || len(req.Name) > 100 {
		errors["name"] = "name must be between 2 and 100 characters"
	}

	if req.Password == "" {
		errors["password"] = "password is required"
	} else if len(req.Password) < 8 || len(req.Password) > 128 {
		errors["password"] = "password must be between 8 and 128 characters"
	}

	if req.Organization == "" {
		errors["organization"] = "organization is required"
	} else if len(req.Organization) < 2 || len(req.Organization) > 100 {
		errors["organization"] = "organization must be between 2 and 100 characters"
	}

	return errors
}

// Helper validation functions

func validateUUID(uuid string) bool {
	matched, _ := regexp.MatchString(`^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`, uuid)
	return matched
}

func validateEmail(email string) bool {
	matched, _ := regexp.MatchString(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`, email)
	return matched
}

func validateDate(date string) bool {
	_, err := time.Parse("2006-01-02", date)
	return err == nil
}

func validateDateTime(datetime string) bool {
	_, err := time.Parse(time.RFC3339, datetime)
	return err == nil
}

func validateAlphanumeric(text string) bool {
	matched, _ := regexp.MatchString(`^[a-zA-Z0-9]+$`, text)
	return matched
}

func validateBuildingPath(path string) bool {
	// Building path should be like: /B1/3/A/301/HVAC/UNIT-01
	matched, _ := regexp.MatchString(`^/[A-Z0-9]+(/[A-Z0-9]+)*$`, path)
	return matched
}

func validateComponentType(componentType string) bool {
	validTypes := []string{"wall", "door", "window", "floor", "ceiling", "column", "beam", "slab", "roof", "stair", "ramp", "railing", "furnishing", "space", "zone", "system", "group", "annotation", "grid", "reference"}

	for _, validType := range validTypes {
		if componentType == validType {
			return true
		}
	}
	return false
}

func validateEquipmentType(equipmentType string) bool {
	validTypes := []string{"hvac", "electrical", "plumbing", "fire_safety", "security", "lighting", "elevator", "escalator", "generator", "transformer", "panel", "sensor", "controller", "valve", "pump", "fan", "motor", "compressor", "heat_exchanger", "boiler", "chiller"}

	for _, validType := range validTypes {
		if equipmentType == validType {
			return true
		}
	}
	return false
}

func isValidRole(role string) bool {
	validRoles := []string{"admin", "user", "manager", "viewer"}
	for _, validRole := range validRoles {
		if role == validRole {
			return true
		}
	}
	return false
}

func isValidEquipmentStatus(status string) bool {
	validStatuses := []string{"operational", "maintenance", "offline", "retired"}
	for _, validStatus := range validStatuses {
		if status == validStatus {
			return true
		}
	}
	return false
}

func isValidIFCVersion(version string) bool {
	validVersions := []string{"IFC2x3", "IFC4", "IFC4x1", "IFC4x2", "IFC4x3"}
	for _, validVersion := range validVersions {
		if version == validVersion {
			return true
		}
	}
	return false
}

func isValidDiscipline(discipline string) bool {
	validDisciplines := []string{"architectural", "structural", "hvac", "electrical", "plumbing", "fire_safety"}
	for _, validDiscipline := range validDisciplines {
		if discipline == validDiscipline {
			return true
		}
	}
	return false
}

func isValidFormat(format string) bool {
	validFormats := []string{"ifc", "step", "xml"}
	for _, validFormat := range validFormats {
		if format == validFormat {
			return true
		}
	}
	return false
}
