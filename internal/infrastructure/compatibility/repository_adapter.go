package compatibility

import (
	"context"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
)

// RepositoryAdapter provides compatibility between old string-based repositories and new ID-based domain models
type RepositoryAdapter struct {
	buildingRepo  domain.BuildingRepository
	equipmentRepo domain.EquipmentRepository
	userRepo      domain.UserRepository
	orgRepo       domain.OrganizationRepository
}

// NewRepositoryAdapter creates a new repository adapter
func NewRepositoryAdapter(
	buildingRepo domain.BuildingRepository,
	equipmentRepo domain.EquipmentRepository,
	userRepo domain.UserRepository,
	orgRepo domain.OrganizationRepository,
) *RepositoryAdapter {
	return &RepositoryAdapter{
		buildingRepo:  buildingRepo,
		equipmentRepo: equipmentRepo,
		userRepo:      userRepo,
		orgRepo:       orgRepo,
	}
}

// Building operations

func (a *RepositoryAdapter) CreateBuilding(ctx context.Context, building *domain.Building) error {
	// Convert ID to string for repository
	buildingStr := &domain.Building{
		ID:          types.ID{Legacy: building.ID.String()}, // Store as legacy for now
		Name:        building.Name,
		Address:     building.Address,
		Coordinates: building.Coordinates,
		Floors:      building.Floors,
		Equipment:   building.Equipment,
		CreatedAt:   building.CreatedAt,
		UpdatedAt:   building.UpdatedAt,
	}
	return a.buildingRepo.Create(ctx, buildingStr)
}

func (a *RepositoryAdapter) GetBuildingByID(ctx context.Context, id types.ID) (*domain.Building, error) {
	building, err := a.buildingRepo.GetByID(ctx, id.String())
	if err != nil {
		return nil, err
	}

	// Convert back to new ID format
	return &domain.Building{
		ID:          types.FromString(building.ID.String()),
		Name:        building.Name,
		Address:     building.Address,
		Coordinates: building.Coordinates,
		Floors:      building.Floors,
		Equipment:   building.Equipment,
		CreatedAt:   building.CreatedAt,
		UpdatedAt:   building.UpdatedAt,
	}, nil
}

func (a *RepositoryAdapter) UpdateBuilding(ctx context.Context, building *domain.Building) error {
	// Convert ID to string for repository
	buildingStr := &domain.Building{
		ID:          types.ID{Legacy: building.ID.String()}, // Store as legacy for now
		Name:        building.Name,
		Address:     building.Address,
		Coordinates: building.Coordinates,
		Floors:      building.Floors,
		Equipment:   building.Equipment,
		CreatedAt:   building.CreatedAt,
		UpdatedAt:   building.UpdatedAt,
	}
	return a.buildingRepo.Update(ctx, buildingStr)
}

func (a *RepositoryAdapter) DeleteBuilding(ctx context.Context, id types.ID) error {
	return a.buildingRepo.Delete(ctx, id.String())
}

func (a *RepositoryAdapter) GetBuildingEquipment(ctx context.Context, buildingID types.ID) ([]*domain.Equipment, error) {
	equipment, err := a.buildingRepo.GetEquipment(ctx, buildingID.String())
	if err != nil {
		return nil, err
	}

	// Convert equipment IDs
	result := make([]*domain.Equipment, len(equipment))
	for i, eq := range equipment {
		result[i] = &domain.Equipment{
			ID:         types.FromString(eq.ID.String()),
			BuildingID: types.FromString(eq.BuildingID.String()),
			FloorID:    types.FromString(eq.FloorID.String()),
			RoomID:     types.FromString(eq.RoomID.String()),
			Name:       eq.Name,
			Type:       eq.Type,
			Model:      eq.Model,
			Location:   eq.Location,
			Status:     eq.Status,
			CreatedAt:  eq.CreatedAt,
			UpdatedAt:  eq.UpdatedAt,
		}
	}

	return result, nil
}

// Equipment operations

func (a *RepositoryAdapter) CreateEquipment(ctx context.Context, equipment *domain.Equipment) error {
	// Convert ID to string for repository
	equipmentStr := &domain.Equipment{
		ID:         types.ID{Legacy: equipment.ID.String()}, // Store as legacy for now
		BuildingID: types.ID{Legacy: equipment.BuildingID.String()},
		FloorID:    types.ID{Legacy: equipment.FloorID.String()},
		RoomID:     types.ID{Legacy: equipment.RoomID.String()},
		Name:       equipment.Name,
		Type:       equipment.Type,
		Model:      equipment.Model,
		Location:   equipment.Location,
		Status:     equipment.Status,
		CreatedAt:  equipment.CreatedAt,
		UpdatedAt:  equipment.UpdatedAt,
	}
	return a.equipmentRepo.Create(ctx, equipmentStr)
}

func (a *RepositoryAdapter) GetEquipmentByID(ctx context.Context, id types.ID) (*domain.Equipment, error) {
	equipment, err := a.equipmentRepo.GetByID(ctx, id.String())
	if err != nil {
		return nil, err
	}

	// Convert back to new ID format
	return &domain.Equipment{
		ID:         types.FromString(equipment.ID.String()),
		BuildingID: types.FromString(equipment.BuildingID.String()),
		FloorID:    types.FromString(equipment.FloorID.String()),
		RoomID:     types.FromString(equipment.RoomID.String()),
		Name:       equipment.Name,
		Type:       equipment.Type,
		Model:      equipment.Model,
		Location:   equipment.Location,
		Status:     equipment.Status,
		CreatedAt:  equipment.CreatedAt,
		UpdatedAt:  equipment.UpdatedAt,
	}, nil
}

func (a *RepositoryAdapter) GetEquipmentByBuilding(ctx context.Context, buildingID types.ID) ([]*domain.Equipment, error) {
	equipment, err := a.equipmentRepo.GetByBuilding(ctx, buildingID.String())
	if err != nil {
		return nil, err
	}

	// Convert equipment IDs
	result := make([]*domain.Equipment, len(equipment))
	for i, eq := range equipment {
		result[i] = &domain.Equipment{
			ID:         types.FromString(eq.ID.String()),
			BuildingID: types.FromString(eq.BuildingID.String()),
			FloorID:    types.FromString(eq.FloorID.String()),
			RoomID:     types.FromString(eq.RoomID.String()),
			Name:       eq.Name,
			Type:       eq.Type,
			Model:      eq.Model,
			Location:   eq.Location,
			Status:     eq.Status,
			CreatedAt:  eq.CreatedAt,
			UpdatedAt:  eq.UpdatedAt,
		}
	}

	return result, nil
}

func (a *RepositoryAdapter) UpdateEquipment(ctx context.Context, equipment *domain.Equipment) error {
	// Convert ID to string for repository
	equipmentStr := &domain.Equipment{
		ID:         types.ID{Legacy: equipment.ID.String()}, // Store as legacy for now
		BuildingID: types.ID{Legacy: equipment.BuildingID.String()},
		FloorID:    types.ID{Legacy: equipment.FloorID.String()},
		RoomID:     types.ID{Legacy: equipment.RoomID.String()},
		Name:       equipment.Name,
		Type:       equipment.Type,
		Model:      equipment.Model,
		Location:   equipment.Location,
		Status:     equipment.Status,
		CreatedAt:  equipment.CreatedAt,
		UpdatedAt:  equipment.UpdatedAt,
	}
	return a.equipmentRepo.Update(ctx, equipmentStr)
}

func (a *RepositoryAdapter) DeleteEquipment(ctx context.Context, id types.ID) error {
	return a.equipmentRepo.Delete(ctx, id.String())
}

// User operations

func (a *RepositoryAdapter) CreateUser(ctx context.Context, user *domain.User) error {
	// Convert ID to string for repository
	userStr := &domain.User{
		ID:        types.ID{Legacy: user.ID.String()}, // Store as legacy for now
		Email:     user.Email,
		Name:      user.Name,
		Role:      user.Role,
		Active:    user.Active,
		CreatedAt: user.CreatedAt,
		UpdatedAt: user.UpdatedAt,
	}
	return a.userRepo.Create(ctx, userStr)
}

func (a *RepositoryAdapter) GetUserByID(ctx context.Context, id types.ID) (*domain.User, error) {
	user, err := a.userRepo.GetByID(ctx, id.String())
	if err != nil {
		return nil, err
	}

	// Convert back to new ID format
	return &domain.User{
		ID:        types.FromString(user.ID.String()),
		Email:     user.Email,
		Name:      user.Name,
		Role:      user.Role,
		Active:    user.Active,
		CreatedAt: user.CreatedAt,
		UpdatedAt: user.UpdatedAt,
	}, nil
}

func (a *RepositoryAdapter) UpdateUser(ctx context.Context, user *domain.User) error {
	// Convert ID to string for repository
	userStr := &domain.User{
		ID:        types.ID{Legacy: user.ID.String()}, // Store as legacy for now
		Email:     user.Email,
		Name:      user.Name,
		Role:      user.Role,
		Active:    user.Active,
		CreatedAt: user.CreatedAt,
		UpdatedAt: user.UpdatedAt,
	}
	return a.userRepo.Update(ctx, userStr)
}

func (a *RepositoryAdapter) DeleteUser(ctx context.Context, id types.ID) error {
	return a.userRepo.Delete(ctx, id.String())
}

// Organization operations

func (a *RepositoryAdapter) CreateOrganization(ctx context.Context, org *domain.Organization) error {
	// Convert ID to string for repository
	orgStr := &domain.Organization{
		ID:          types.ID{Legacy: org.ID.String()}, // Store as legacy for now
		Name:        org.Name,
		Description: org.Description,
		Plan:        org.Plan,
		Active:      org.Active,
		CreatedAt:   org.CreatedAt,
		UpdatedAt:   org.UpdatedAt,
	}
	return a.orgRepo.Create(ctx, orgStr)
}

func (a *RepositoryAdapter) GetOrganizationByID(ctx context.Context, id types.ID) (*domain.Organization, error) {
	org, err := a.orgRepo.GetByID(ctx, id.String())
	if err != nil {
		return nil, err
	}

	// Convert back to new ID format
	return &domain.Organization{
		ID:          types.FromString(org.ID.String()),
		Name:        org.Name,
		Description: org.Description,
		Plan:        org.Plan,
		Active:      org.Active,
		CreatedAt:   org.CreatedAt,
		UpdatedAt:   org.UpdatedAt,
	}, nil
}

func (a *RepositoryAdapter) UpdateOrganization(ctx context.Context, org *domain.Organization) error {
	// Convert ID to string for repository
	orgStr := &domain.Organization{
		ID:          types.ID{Legacy: org.ID.String()}, // Store as legacy for now
		Name:        org.Name,
		Description: org.Description,
		Plan:        org.Plan,
		Active:      org.Active,
		CreatedAt:   org.CreatedAt,
		UpdatedAt:   org.UpdatedAt,
	}
	return a.orgRepo.Update(ctx, orgStr)
}

func (a *RepositoryAdapter) DeleteOrganization(ctx context.Context, id types.ID) error {
	return a.orgRepo.Delete(ctx, id.String())
}
