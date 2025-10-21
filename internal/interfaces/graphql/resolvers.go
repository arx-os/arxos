package graphql

import (
	"fmt"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/usecase/auth"
	"github.com/arx-os/arxos/internal/usecase/building"
	"github.com/graphql-go/graphql"
)

// Resolvers contains all GraphQL resolvers
type Resolvers struct {
	buildingUC     *building.BuildingUseCase
	equipmentUC    *building.EquipmentUseCase
	componentUC    any // ComponentService interface
	userUC         *auth.UserUseCase
	organizationUC *auth.OrganizationUseCase
	logger         domain.Logger
}

// NewResolvers creates a new resolvers instance
func NewResolvers(
	buildingUC *building.BuildingUseCase,
	equipmentUC *building.EquipmentUseCase,
	componentUC any,
	userUC *auth.UserUseCase,
	organizationUC *auth.OrganizationUseCase,
	logger domain.Logger,
) *Resolvers {
	return &Resolvers{
		buildingUC:     buildingUC,
		equipmentUC:    equipmentUC,
		componentUC:    componentUC,
		userUC:         userUC,
		organizationUC: organizationUC,
		logger:         logger,
	}
}

// Building resolvers
func (r *Resolvers) GetBuilding(p graphql.ResolveParams) (any, error) {
	id, ok := p.Args["id"].(string)
	if !ok {
		return nil, fmt.Errorf("building id is required")
	}

	building, err := r.buildingUC.GetBuilding(p.Context, types.FromString(id))
	if err != nil {
		r.logger.Error("Failed to get building", "id", id, "error", err)
		return nil, err
	}

	return building, nil
}

func (r *Resolvers) GetBuildings(p graphql.ResolveParams) (any, error) {
	// Parse arguments
	// This would need to be implemented - for now return empty list
	buildings := []*domain.Building{}

	return buildings, nil
}

func (r *Resolvers) CreateBuilding(p graphql.ResolveParams) (any, error) {
	input, ok := p.Args["input"].(map[string]any)
	if !ok {
		return nil, fmt.Errorf("input is required")
	}

	// Convert input to CreateBuildingRequest
	req := &domain.CreateBuildingRequest{
		Name:    input["name"].(string),
		Address: input["address"].(string),
	}

	// Handle coordinates
	if lat, ok := input["latitude"].(float64); ok {
		if lon, ok := input["longitude"].(float64); ok {
			req.Coordinates = &domain.Location{
				X: lat,
				Y: lon,
				Z: 0,
			}
		}
	}

	building, err := r.buildingUC.CreateBuilding(p.Context, req)
	if err != nil {
		r.logger.Error("Failed to create building", "error", err)
		return nil, err
	}

	return building, nil
}

func (r *Resolvers) UpdateBuilding(p graphql.ResolveParams) (any, error) {
	id, ok := p.Args["id"].(string)
	if !ok {
		return nil, fmt.Errorf("building id is required")
	}

	input, ok := p.Args["input"].(map[string]any)
	if !ok {
		return nil, fmt.Errorf("input is required")
	}

	// Convert input to UpdateBuildingRequest
	req := &domain.UpdateBuildingRequest{
		ID: types.FromString(id),
	}

	if name, ok := input["name"].(string); ok {
		req.Name = &name
	}
	if address, ok := input["address"].(string); ok {
		req.Address = &address
	}
	// Handle coordinates
	if lat, ok := input["latitude"].(float64); ok {
		if lon, ok := input["longitude"].(float64); ok {
			req.Coordinates = &domain.Location{
				X: lat,
				Y: lon,
				Z: 0,
			}
		}
	}

	building, err := r.buildingUC.UpdateBuilding(p.Context, req)
	if err != nil {
		r.logger.Error("Failed to update building", "id", id, "error", err)
		return nil, err
	}

	return building, nil
}

func (r *Resolvers) DeleteBuilding(p graphql.ResolveParams) (any, error) {
	id, ok := p.Args["id"].(string)
	if !ok {
		return nil, fmt.Errorf("building id is required")
	}

	err := r.buildingUC.DeleteBuilding(p.Context, id)
	if err != nil {
		r.logger.Error("Failed to delete building", "id", id, "error", err)
		return false, err
	}

	return true, nil
}

// Equipment resolvers
func (r *Resolvers) GetEquipment(p graphql.ResolveParams) (any, error) {
	id, ok := p.Args["id"].(string)
	if !ok {
		return nil, fmt.Errorf("equipment id is required")
	}

	equipment, err := r.equipmentUC.GetEquipment(p.Context, id)
	if err != nil {
		r.logger.Error("Failed to get equipment", "id", id, "error", err)
		return nil, err
	}

	return equipment, nil
}

func (r *Resolvers) GetEquipments(p graphql.ResolveParams) (any, error) {
	// Parse arguments
	// This would need to be implemented - for now return empty list
	equipments := []*domain.Equipment{}

	return equipments, nil
}

func (r *Resolvers) CreateEquipment(p graphql.ResolveParams) (any, error) {
	input, ok := p.Args["input"].(map[string]any)
	if !ok {
		return nil, fmt.Errorf("input is required")
	}

	// Convert input to CreateEquipmentRequest
	req := &domain.CreateEquipmentRequest{
		Name:       input["name"].(string),
		Type:       input["type"].(string),
		BuildingID: types.FromString(input["buildingId"].(string)),
	}

	if floorID, ok := input["floorId"].(string); ok {
		req.FloorID = types.FromString(floorID)
	}
	if roomID, ok := input["roomId"].(string); ok {
		req.RoomID = types.FromString(roomID)
	}
	if _, ok := input["location"].(string); ok {
		// Parse location string (e.g., "x,y,z")
		req.Location = &domain.Location{
			X: 0, Y: 0, Z: 0, // Would parse from string
		}
	}

	equipment, err := r.equipmentUC.CreateEquipment(p.Context, req)
	if err != nil {
		r.logger.Error("Failed to create equipment", "error", err)
		return nil, err
	}

	return equipment, nil
}

func (r *Resolvers) UpdateEquipment(p graphql.ResolveParams) (any, error) {
	id, ok := p.Args["id"].(string)
	if !ok {
		return nil, fmt.Errorf("equipment id is required")
	}

	input, ok := p.Args["input"].(map[string]any)
	if !ok {
		return nil, fmt.Errorf("input is required")
	}

	// Convert input to UpdateEquipmentRequest
	req := &domain.UpdateEquipmentRequest{
		ID: types.FromString(id),
	}

	if name, ok := input["name"].(string); ok {
		req.Name = &name
	}
	if equipmentType, ok := input["type"].(string); ok {
		req.Type = &equipmentType
	}
	if status, ok := input["status"].(string); ok {
		req.Status = &status
	}
	if _, ok := input["location"].(string); ok {
		// Parse location string (e.g., "x,y,z")
		req.Location = &domain.Location{
			X: 0, Y: 0, Z: 0, // Would parse from string
		}
	}

	equipment, err := r.equipmentUC.UpdateEquipment(p.Context, req)
	if err != nil {
		r.logger.Error("Failed to update equipment", "id", id, "error", err)
		return nil, err
	}

	return equipment, nil
}

func (r *Resolvers) DeleteEquipment(p graphql.ResolveParams) (any, error) {
	id, ok := p.Args["id"].(string)
	if !ok {
		return nil, fmt.Errorf("equipment id is required")
	}

	err := r.equipmentUC.DeleteEquipment(p.Context, id)
	if err != nil {
		r.logger.Error("Failed to delete equipment", "id", id, "error", err)
		return false, err
	}

	return true, nil
}

// Component resolvers
func (r *Resolvers) GetComponent(p graphql.ResolveParams) (any, error) {
	id, ok := p.Args["id"].(string)
	if !ok {
		return nil, fmt.Errorf("component id is required")
	}

	// This would need to be implemented based on the component service interface
	r.logger.Warn("GetComponent not implemented", "id", id)
	return nil, fmt.Errorf("component service not implemented")
}

func (r *Resolvers) GetComponents(p graphql.ResolveParams) (any, error) {
	// This would need to be implemented based on the component service interface
	r.logger.Warn("GetComponents not implemented")
	return []any{}, nil
}

// User resolvers
func (r *Resolvers) GetUser(p graphql.ResolveParams) (any, error) {
	id, ok := p.Args["id"].(string)
	if !ok {
		return nil, fmt.Errorf("user id is required")
	}

	user, err := r.userUC.GetUser(p.Context, id)
	if err != nil {
		r.logger.Error("Failed to get user", "id", id, "error", err)
		return nil, err
	}

	return user, nil
}

func (r *Resolvers) GetUsers(p graphql.ResolveParams) (any, error) {
	// Parse arguments
	// This would need to be implemented - for now return empty list
	users := []*domain.User{}

	return users, nil
}

func (r *Resolvers) CreateUser(p graphql.ResolveParams) (any, error) {
	input, ok := p.Args["input"].(map[string]any)
	if !ok {
		return nil, fmt.Errorf("input is required")
	}

	// Convert input to CreateUserRequest
	req := &domain.CreateUserRequest{
		Email: input["email"].(string),
		Name:  input["name"].(string),
		Role:  input["role"].(string),
	}

	user, err := r.userUC.CreateUser(p.Context, req)
	if err != nil {
		r.logger.Error("Failed to create user", "error", err)
		return nil, err
	}

	return user, nil
}

func (r *Resolvers) UpdateUser(p graphql.ResolveParams) (any, error) {
	id, ok := p.Args["id"].(string)
	if !ok {
		return nil, fmt.Errorf("user id is required")
	}

	input, ok := p.Args["input"].(map[string]any)
	if !ok {
		return nil, fmt.Errorf("input is required")
	}

	// Convert input to UpdateUserRequest
	req := &domain.UpdateUserRequest{
		ID: types.FromString(id),
	}

	if name, ok := input["name"].(string); ok {
		req.Name = &name
	}
	if role, ok := input["role"].(string); ok {
		req.Role = &role
	}
	if active, ok := input["active"].(bool); ok {
		req.Active = &active
	}

	user, err := r.userUC.UpdateUser(p.Context, req)
	if err != nil {
		r.logger.Error("Failed to update user", "id", id, "error", err)
		return nil, err
	}

	return user, nil
}

func (r *Resolvers) DeleteUser(p graphql.ResolveParams) (any, error) {
	id, ok := p.Args["id"].(string)
	if !ok {
		return nil, fmt.Errorf("user id is required")
	}

	err := r.userUC.DeleteUser(p.Context, id)
	if err != nil {
		r.logger.Error("Failed to delete user", "id", id, "error", err)
		return false, err
	}

	return true, nil
}

// Organization resolvers
func (r *Resolvers) GetOrganization(p graphql.ResolveParams) (any, error) {
	id, ok := p.Args["id"].(string)
	if !ok {
		return nil, fmt.Errorf("organization id is required")
	}

	organization, err := r.organizationUC.GetOrganization(p.Context, id)
	if err != nil {
		r.logger.Error("Failed to get organization", "id", id, "error", err)
		return nil, err
	}

	return organization, nil
}

func (r *Resolvers) GetOrganizations(p graphql.ResolveParams) (any, error) {
	// Parse arguments
	// This would need to be implemented - for now return empty list
	organizations := []*domain.Organization{}

	return organizations, nil
}
