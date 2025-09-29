package types

import (
	"github.com/arx-os/arxos/internal/domain/analytics"
	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/arx-os/arxos/internal/domain/equipment"
	"github.com/arx-os/arxos/internal/domain/spatial"
	"github.com/arx-os/arxos/internal/domain/workflow"
	"github.com/arx-os/arxos/internal/infra/cache"
	"github.com/arx-os/arxos/internal/infra/database"
	"github.com/arx-os/arxos/internal/infra/messaging"
	"github.com/arx-os/arxos/internal/infra/storage"
)

// Services holds all application services following Clean Architecture principles
type Services struct {
	// Domain Services (Business Logic)
	Building  building.Service
	Equipment equipment.Service
	Spatial   spatial.Service
	Analytics analytics.Service
	Workflow  workflow.Service

	// Infrastructure Services (External Dependencies)
	Database  database.Interface
	Cache     cache.Interface
	Storage   storage.Interface
	Messaging messaging.Interface
}

// NewServices creates a new services container with dependency injection
func NewServices(
	building building.Service,
	equipment equipment.Service,
	spatial spatial.Service,
	analytics analytics.Service,
	workflow workflow.Service,
	database database.Interface,
	cache cache.Interface,
	storage storage.Interface,
	messaging messaging.Interface,
) *Services {
	return &Services{
		Building:  building,
		Equipment: equipment,
		Spatial:   spatial,
		Analytics: analytics,
		Workflow:  workflow,
		Database:  database,
		Cache:     cache,
		Storage:   storage,
		Messaging: messaging,
	}
}
