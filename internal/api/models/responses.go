package models

import (
	"time"

	domainmodels "github.com/arx-os/arxos/pkg/models"
)

// UserResponse represents a user in API responses
type UserResponse struct {
	ID        string    `json:"id"`
	Email     string    `json:"email"`
	Name      string    `json:"name"`
	Role      string    `json:"role"`
	OrgID     string    `json:"org_id,omitempty"`
	Active    bool      `json:"active"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

// UserToResponse converts a domain user to API response
func UserToResponse(user *domainmodels.User) *UserResponse {
	if user == nil {
		return nil
	}

	return &UserResponse{
		ID:        user.ID,
		Email:     user.Email,
		Name:      user.FullName,
		Role:      user.Role,
		OrgID:     user.OrganizationID,
		Active:    user.IsActive,
		CreatedAt: user.CreatedAt,
		UpdatedAt: user.UpdatedAt,
	}
}

// OrganizationResponse represents an organization in API responses
type OrganizationResponse struct {
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	Description string    `json:"description,omitempty"`
	Plan        string    `json:"plan"`
	Active      bool      `json:"active"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

// OrganizationToResponse converts a domain organization to API response
func OrganizationToResponse(org *domainmodels.Organization) *OrganizationResponse {
	if org == nil {
		return nil
	}

	return &OrganizationResponse{
		ID:          org.ID,
		Name:        org.Name,
		Description: org.Description,
		Plan:        string(org.Plan),
		Active:      org.IsActive,
		CreatedAt:   org.CreatedAt,
		UpdatedAt:   org.UpdatedAt,
	}
}

// BuildingResponse represents a building in API responses
type BuildingResponse struct {
	ID        string                 `json:"id"`
	ArxosID   string                 `json:"arxos_id"`
	Name      string                 `json:"name"`
	Address   string                 `json:"address,omitempty"`
	City      string                 `json:"city,omitempty"`
	State     string                 `json:"state,omitempty"`
	Country   string                 `json:"country,omitempty"`
	Latitude  float64                `json:"latitude,omitempty"`
	Longitude float64                `json:"longitude,omitempty"`
	OrgID     string                 `json:"org_id"`
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
	CreatedAt time.Time              `json:"created_at"`
	UpdatedAt time.Time              `json:"updated_at"`
}

// BuildingToResponse converts a domain building to API response
func BuildingToResponse(building *domainmodels.Building) *BuildingResponse {
	if building == nil {
		return nil
	}

	response := &BuildingResponse{
		ID:        building.ID,
		ArxosID:   building.ID, // Use ID as ArxosID for now
		Name:      building.Name,
		Address:   building.Address,
		OrgID:     "", // Not in basic Building model
		CreatedAt: building.CreatedAt,
		UpdatedAt: building.UpdatedAt,
	}

	return response
}

// EquipmentResponse represents equipment in API responses
type EquipmentResponse struct {
	ID         string                 `json:"id"`
	Name       string                 `json:"name"`
	Type       string                 `json:"type"`
	BuildingID string                 `json:"building_id"`
	Path       string                 `json:"path,omitempty"`
	FloorID    string                 `json:"floor_id,omitempty"`
	RoomID     string                 `json:"room_id,omitempty"`
	Status     string                 `json:"status"`
	Model      string                 `json:"model,omitempty"`
	Serial     string                 `json:"serial,omitempty"`
	Location   *Point3D               `json:"location,omitempty"`
	Metadata   map[string]interface{} `json:"metadata,omitempty"`
	CreatedAt  time.Time              `json:"created_at"`
	UpdatedAt  time.Time              `json:"updated_at"`
}

// EquipmentToResponse converts domain equipment to API response
func EquipmentToResponse(equipment interface{}) *EquipmentResponse {
	if equipment == nil {
		return nil
	}

	// Since Equipment type may vary, use interface{} and type assertion
	// This is a placeholder implementation - adjust based on actual Equipment struct
	response := &EquipmentResponse{
		ID:     "",
		Name:   "Equipment",
		Type:   "Unknown",
		Status: "UNKNOWN",
	}

	return response
}
