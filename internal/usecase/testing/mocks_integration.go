package testing

import (
	"context"

	"github.com/arx-os/arxos/internal/domain/bas"
	"github.com/stretchr/testify/mock"
)

// =============================================================================
// Integration Repository Mocks (BAS, IFC, Spatial)
// =============================================================================

// MockBASPointRepository is a mock implementation of bas.BASPointRepository
type MockBASPointRepository struct {
	mock.Mock
}

func (m *MockBASPointRepository) Create(ctx context.Context, point *bas.BASPoint) error {
	args := m.Called(ctx, point)
	return args.Error(0)
}

func (m *MockBASPointRepository) GetByID(ctx context.Context, id string) (*bas.BASPoint, error) {
	args := m.Called(ctx, id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*bas.BASPoint), args.Error(1)
}

func (m *MockBASPointRepository) Update(ctx context.Context, point *bas.BASPoint) error {
	args := m.Called(ctx, point)
	return args.Error(0)
}

func (m *MockBASPointRepository) Delete(ctx context.Context, id string) error {
	args := m.Called(ctx, id)
	return args.Error(0)
}

func (m *MockBASPointRepository) List(ctx context.Context, filter bas.BASPointFilter, limit, offset int) ([]*bas.BASPoint, error) {
	args := m.Called(ctx, filter, limit, offset)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*bas.BASPoint), args.Error(1)
}

func (m *MockBASPointRepository) BulkCreate(ctx context.Context, points []*bas.BASPoint) error {
	args := m.Called(ctx, points)
	return args.Error(0)
}

func (m *MockBASPointRepository) MapToRoom(ctx context.Context, pointID, roomID string, confidence int) error {
	args := m.Called(ctx, pointID, roomID, confidence)
	return args.Error(0)
}

func (m *MockBASPointRepository) ListUnmapped(ctx context.Context, buildingID string) ([]*bas.BASPoint, error) {
	args := m.Called(ctx, buildingID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*bas.BASPoint), args.Error(1)
}

func (m *MockBASPointRepository) GetByRoom(ctx context.Context, roomID string) ([]*bas.BASPoint, error) {
	args := m.Called(ctx, roomID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*bas.BASPoint), args.Error(1)
}

func (m *MockBASPointRepository) GetBySystem(ctx context.Context, systemID string) ([]*bas.BASPoint, error) {
	args := m.Called(ctx, systemID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*bas.BASPoint), args.Error(1)
}

// MockBASSystemRepository is a mock implementation of bas.BASSystemRepository
type MockBASSystemRepository struct {
	mock.Mock
}

func (m *MockBASSystemRepository) Create(ctx context.Context, system *bas.BASSystem) error {
	args := m.Called(ctx, system)
	return args.Error(0)
}

func (m *MockBASSystemRepository) GetByID(ctx context.Context, id string) (*bas.BASSystem, error) {
	args := m.Called(ctx, id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*bas.BASSystem), args.Error(1)
}

func (m *MockBASSystemRepository) Update(ctx context.Context, system *bas.BASSystem) error {
	args := m.Called(ctx, system)
	return args.Error(0)
}

func (m *MockBASSystemRepository) Delete(ctx context.Context, id string) error {
	args := m.Called(ctx, id)
	return args.Error(0)
}

func (m *MockBASSystemRepository) List(ctx context.Context, buildingID string) ([]*bas.BASSystem, error) {
	args := m.Called(ctx, buildingID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*bas.BASSystem), args.Error(1)
}

func (m *MockBASSystemRepository) GetByBuilding(ctx context.Context, buildingID string) ([]*bas.BASSystem, error) {
	args := m.Called(ctx, buildingID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*bas.BASSystem), args.Error(1)
}

func (m *MockBASSystemRepository) GetByType(ctx context.Context, systemType bas.BASSystemType) ([]*bas.BASSystem, error) {
	args := m.Called(ctx, systemType)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*bas.BASSystem), args.Error(1)
}
