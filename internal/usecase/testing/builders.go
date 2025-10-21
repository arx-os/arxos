package testing

import (
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
)

// =============================================================================
// Builders - Fluent API for Test Data Creation
// =============================================================================
//
// Builders provide a clean, chainable interface for creating complex test
// entities. They use sensible defaults and allow customization through
// method chaining.
//
// Example:
//
//	building := utesting.NewBuildingBuilder().
//	    WithName("Empire State Building").
//	    WithAddress("350 5th Ave, New York, NY").
//	    WithFloor(
//	        utesting.NewFloorBuilder().
//	            WithName("Ground Floor").
//	            WithLevel(0).
//	            Build(),
//	    ).
//	    Build()

// =============================================================================
// BuildingBuilder
// =============================================================================

// BuildingBuilder provides a fluent interface for building test buildings
type BuildingBuilder struct {
	building *domain.Building
}

// NewBuildingBuilder creates a new BuildingBuilder with sensible defaults
func NewBuildingBuilder() *BuildingBuilder {
	return &BuildingBuilder{
		building: &domain.Building{
			ID:        types.NewID(),
			Name:      "Test Building",
			Address:   "123 Test Street, Test City, TS 12345",
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		},
	}
}

// WithID sets a specific building ID
func (b *BuildingBuilder) WithID(id types.ID) *BuildingBuilder {
	b.building.ID = id
	return b
}

// WithName sets the building name
func (b *BuildingBuilder) WithName(name string) *BuildingBuilder {
	b.building.Name = name
	return b
}

// WithAddress sets the building address
func (b *BuildingBuilder) WithAddress(address string) *BuildingBuilder {
	b.building.Address = address
	return b
}

// WithCoordinates sets the building coordinates
func (b *BuildingBuilder) WithCoordinates(x, y float64) *BuildingBuilder {
	b.building.Coordinates = &domain.Location{X: x, Y: y, Z: 0}
	return b
}

// WithCoordinates3D sets the building coordinates with elevation
func (b *BuildingBuilder) WithCoordinates3D(x, y, z float64) *BuildingBuilder {
	b.building.Coordinates = &domain.Location{X: x, Y: y, Z: z}
	return b
}

// WithFloor adds a floor to the building
func (b *BuildingBuilder) WithFloor(floor *domain.Floor) *BuildingBuilder {
	// Set the building ID relationship
	floor.BuildingID = b.building.ID
	b.building.Floors = append(b.building.Floors, floor)
	return b
}

// WithFloors adds multiple floors to the building
func (b *BuildingBuilder) WithFloors(floors ...*domain.Floor) *BuildingBuilder {
	for _, floor := range floors {
		b.WithFloor(floor)
	}
	return b
}

// WithEquipment adds equipment to the building
func (b *BuildingBuilder) WithEquipment(equipment *domain.Equipment) *BuildingBuilder {
	equipment.BuildingID = b.building.ID
	b.building.Equipment = append(b.building.Equipment, equipment)
	return b
}

// Build returns the constructed building
func (b *BuildingBuilder) Build() *domain.Building {
	return b.building
}

// =============================================================================
// FloorBuilder
// =============================================================================

// FloorBuilder provides a fluent interface for building test floors
type FloorBuilder struct {
	floor *domain.Floor
}

// NewFloorBuilder creates a new FloorBuilder with sensible defaults
func NewFloorBuilder() *FloorBuilder {
	return &FloorBuilder{
		floor: &domain.Floor{
			ID:         types.NewID(),
			BuildingID: types.NewID(),
			Name:       "Test Floor",
			Level:      0,
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		},
	}
}

// WithID sets a specific floor ID
func (f *FloorBuilder) WithID(id types.ID) *FloorBuilder {
	f.floor.ID = id
	return f
}

// WithBuildingID sets the parent building ID
func (f *FloorBuilder) WithBuildingID(buildingID types.ID) *FloorBuilder {
	f.floor.BuildingID = buildingID
	return f
}

// WithName sets the floor name
func (f *FloorBuilder) WithName(name string) *FloorBuilder {
	f.floor.Name = name
	return f
}

// WithLevel sets the floor level
func (f *FloorBuilder) WithLevel(level int) *FloorBuilder {
	f.floor.Level = level
	return f
}

// WithRoom adds a room to the floor
func (f *FloorBuilder) WithRoom(room *domain.Room) *FloorBuilder {
	room.FloorID = f.floor.ID
	f.floor.Rooms = append(f.floor.Rooms, room)
	return f
}

// WithRooms adds multiple rooms to the floor
func (f *FloorBuilder) WithRooms(rooms ...*domain.Room) *FloorBuilder {
	for _, room := range rooms {
		f.WithRoom(room)
	}
	return f
}

// WithEquipment adds equipment to the floor
func (f *FloorBuilder) WithEquipment(equipment *domain.Equipment) *FloorBuilder {
	equipment.BuildingID = f.floor.BuildingID
	f.floor.Equipment = append(f.floor.Equipment, equipment)
	return f
}

// Build returns the constructed floor
func (f *FloorBuilder) Build() *domain.Floor {
	return f.floor
}

// =============================================================================
// RoomBuilder
// =============================================================================

// RoomBuilder provides a fluent interface for building test rooms
type RoomBuilder struct {
	room *domain.Room
}

// NewRoomBuilder creates a new RoomBuilder with sensible defaults
func NewRoomBuilder() *RoomBuilder {
	return &RoomBuilder{
		room: &domain.Room{
			ID:        types.NewID(),
			FloorID:   types.NewID(),
			Name:      "Test Room",
			Number:    "101",
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		},
	}
}

// WithID sets a specific room ID
func (r *RoomBuilder) WithID(id types.ID) *RoomBuilder {
	r.room.ID = id
	return r
}

// WithFloorID sets the parent floor ID
func (r *RoomBuilder) WithFloorID(floorID types.ID) *RoomBuilder {
	r.room.FloorID = floorID
	return r
}

// WithName sets the room name
func (r *RoomBuilder) WithName(name string) *RoomBuilder {
	r.room.Name = name
	return r
}

// WithNumber sets the room number
func (r *RoomBuilder) WithNumber(number string) *RoomBuilder {
	r.room.Number = number
	return r
}

// WithLocation sets the room location
func (r *RoomBuilder) WithLocation(x, y float64) *RoomBuilder {
	r.room.Location = &domain.Location{X: x, Y: y, Z: 0}
	return r
}

// WithDimensions sets the room dimensions
func (r *RoomBuilder) WithDimensions(width, height float64) *RoomBuilder {
	r.room.Width = width
	r.room.Height = height
	return r
}

// WithEquipment adds equipment to the room
func (r *RoomBuilder) WithEquipment(equipment *domain.Equipment) *RoomBuilder {
	r.room.Equipment = append(r.room.Equipment, equipment)
	return r
}

// Build returns the constructed room
func (r *RoomBuilder) Build() *domain.Room {
	return r.room
}

// =============================================================================
// EquipmentBuilder
// =============================================================================

// EquipmentBuilder provides a fluent interface for building test equipment
type EquipmentBuilder struct {
	equipment *domain.Equipment
}

// NewEquipmentBuilder creates a new EquipmentBuilder with sensible defaults
func NewEquipmentBuilder() *EquipmentBuilder {
	return &EquipmentBuilder{
		equipment: &domain.Equipment{
			ID:         types.NewID(),
			BuildingID: types.NewID(),
			Name:       "Test Equipment",
			Type:       "hvac",
			Category:   "mechanical",
			Status:     "operational",
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		},
	}
}

// WithID sets a specific equipment ID
func (e *EquipmentBuilder) WithID(id types.ID) *EquipmentBuilder {
	e.equipment.ID = id
	return e
}

// WithBuildingID sets the parent building ID
func (e *EquipmentBuilder) WithBuildingID(buildingID types.ID) *EquipmentBuilder {
	e.equipment.BuildingID = buildingID
	return e
}

// WithName sets the equipment name
func (e *EquipmentBuilder) WithName(name string) *EquipmentBuilder {
	e.equipment.Name = name
	return e
}

// WithType sets the equipment type
func (e *EquipmentBuilder) WithType(equipmentType string) *EquipmentBuilder {
	e.equipment.Type = equipmentType
	return e
}

// WithCategory sets the equipment category
func (e *EquipmentBuilder) WithCategory(category string) *EquipmentBuilder {
	e.equipment.Category = category
	return e
}

// WithStatus sets the equipment status
func (e *EquipmentBuilder) WithStatus(status string) *EquipmentBuilder {
	e.equipment.Status = status
	return e
}

// WithModel sets the equipment model
func (e *EquipmentBuilder) WithModel(model string) *EquipmentBuilder {
	e.equipment.Model = model
	return e
}

// WithLocation sets the equipment location
func (e *EquipmentBuilder) WithLocation(x, y, z float64) *EquipmentBuilder {
	e.equipment.Location = &domain.Location{X: x, Y: y, Z: z}
	return e
}

// WithPath sets the equipment path
func (e *EquipmentBuilder) WithPath(path string) *EquipmentBuilder {
	e.equipment.Path = path
	return e
}

// Build returns the constructed equipment
func (e *EquipmentBuilder) Build() *domain.Equipment {
	return e.equipment
}

// =============================================================================
// UserBuilder
// =============================================================================

// UserBuilder provides a fluent interface for building test users
type UserBuilder struct {
	user *domain.User
}

// NewUserBuilder creates a new UserBuilder with sensible defaults
func NewUserBuilder() *UserBuilder {
	return &UserBuilder{
		user: &domain.User{
			ID:        types.NewID(),
			Email:     "test@example.com",
			Name:      "Test User",
			Role:      "user",
			Active:    true,
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		},
	}
}

// WithID sets a specific user ID
func (u *UserBuilder) WithID(id types.ID) *UserBuilder {
	u.user.ID = id
	return u
}

// WithEmail sets the user email
func (u *UserBuilder) WithEmail(email string) *UserBuilder {
	u.user.Email = email
	return u
}

// WithName sets the user name
func (u *UserBuilder) WithName(name string) *UserBuilder {
	u.user.Name = name
	return u
}

// WithRole sets the user role
func (u *UserBuilder) WithRole(role string) *UserBuilder {
	u.user.Role = role
	return u
}

// WithActive sets the user active status
func (u *UserBuilder) WithActive(active bool) *UserBuilder {
	u.user.Active = active
	return u
}

// AsAdmin configures the user as an admin
func (u *UserBuilder) AsAdmin() *UserBuilder {
	u.user.Role = "admin"
	return u
}

// AsInactive configures the user as inactive
func (u *UserBuilder) AsInactive() *UserBuilder {
	u.user.Active = false
	return u
}

// Build returns the constructed user
func (u *UserBuilder) Build() *domain.User {
	return u.user
}

// =============================================================================
// OrganizationBuilder
// =============================================================================

// OrganizationBuilder provides a fluent interface for building test organizations
type OrganizationBuilder struct {
	org *domain.Organization
}

// NewOrganizationBuilder creates a new OrganizationBuilder with sensible defaults
func NewOrganizationBuilder() *OrganizationBuilder {
	return &OrganizationBuilder{
		org: &domain.Organization{
			ID:          types.NewID(),
			Name:        "Test Organization",
			Description: "A test organization",
			Plan:        "basic",
			Active:      true,
			CreatedAt:   time.Now(),
			UpdatedAt:   time.Now(),
		},
	}
}

// WithID sets a specific organization ID
func (o *OrganizationBuilder) WithID(id types.ID) *OrganizationBuilder {
	o.org.ID = id
	return o
}

// WithName sets the organization name
func (o *OrganizationBuilder) WithName(name string) *OrganizationBuilder {
	o.org.Name = name
	return o
}

// WithDescription sets the organization description
func (o *OrganizationBuilder) WithDescription(description string) *OrganizationBuilder {
	o.org.Description = description
	return o
}

// WithPlan sets the organization plan
func (o *OrganizationBuilder) WithPlan(plan string) *OrganizationBuilder {
	o.org.Plan = plan
	return o
}

// WithActive sets the organization active status
func (o *OrganizationBuilder) WithActive(active bool) *OrganizationBuilder {
	o.org.Active = active
	return o
}

// AsEnterprise configures the organization with enterprise plan
func (o *OrganizationBuilder) AsEnterprise() *OrganizationBuilder {
	o.org.Plan = "enterprise"
	return o
}

// AsProfessional configures the organization with professional plan
func (o *OrganizationBuilder) AsProfessional() *OrganizationBuilder {
	o.org.Plan = "professional"
	return o
}

// AsInactive configures the organization as inactive
func (o *OrganizationBuilder) AsInactive() *OrganizationBuilder {
	o.org.Active = false
	return o
}

// Build returns the constructed organization
func (o *OrganizationBuilder) Build() *domain.Organization {
	return o.org
}
