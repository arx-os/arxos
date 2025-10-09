package usecase

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

// MockOrganizationRepository is a mock implementation of domain.OrganizationRepository
type MockOrganizationRepository struct {
	mock.Mock
}

func (m *MockOrganizationRepository) Create(ctx context.Context, org *domain.Organization) error {
	args := m.Called(ctx, org)
	return args.Error(0)
}

func (m *MockOrganizationRepository) GetByID(ctx context.Context, id string) (*domain.Organization, error) {
	args := m.Called(ctx, id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Organization), args.Error(1)
}

func (m *MockOrganizationRepository) GetByName(ctx context.Context, name string) (*domain.Organization, error) {
	args := m.Called(ctx, name)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Organization), args.Error(1)
}

func (m *MockOrganizationRepository) List(ctx context.Context, filter *domain.OrganizationFilter) ([]*domain.Organization, error) {
	args := m.Called(ctx, filter)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Organization), args.Error(1)
}

func (m *MockOrganizationRepository) Update(ctx context.Context, org *domain.Organization) error {
	args := m.Called(ctx, org)
	return args.Error(0)
}

func (m *MockOrganizationRepository) Delete(ctx context.Context, id string) error {
	args := m.Called(ctx, id)
	return args.Error(0)
}

func (m *MockOrganizationRepository) GetUsers(ctx context.Context, orgID string) ([]*domain.User, error) {
	args := m.Called(ctx, orgID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.User), args.Error(1)
}

func (m *MockOrganizationRepository) AddUser(ctx context.Context, orgID, userID string) error {
	args := m.Called(ctx, orgID, userID)
	return args.Error(0)
}

func (m *MockOrganizationRepository) RemoveUser(ctx context.Context, orgID, userID string) error {
	args := m.Called(ctx, orgID, userID)
	return args.Error(0)
}

// Test fixtures
func createTestOrganization() *domain.Organization {
	return &domain.Organization{
		ID:          types.NewID(),
		Name:        "Test Organization",
		Description: "A test organization",
		Plan:        "professional",
		Active:      true,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}
}

// TestOrganizationUseCase_CreateOrganization tests the CreateOrganization method
func TestOrganizationUseCase_CreateOrganization(t *testing.T) {
	t.Run("successful creation", func(t *testing.T) {
		// Arrange
		mockOrgRepo := new(MockOrganizationRepository)
		mockUserRepo := new(MockUserRepository)
		mockLogger := createPermissiveMockLogger()

		mockOrgRepo.On("GetByName", mock.Anything, "New Organization").
			Return(nil, errors.New("not found"))
		mockOrgRepo.On("Create", mock.Anything, mock.MatchedBy(func(o *domain.Organization) bool {
			return o.Name == "New Organization" && o.Plan == "enterprise"
		})).Return(nil)

		uc := NewOrganizationUseCase(mockOrgRepo, mockUserRepo, mockLogger)

		req := &domain.CreateOrganizationRequest{
			Name:        "New Organization",
			Description: "A new organization",
			Plan:        "enterprise",
		}

		// Act
		result, err := uc.CreateOrganization(context.Background(), req)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, "New Organization", result.Name)
		assert.Equal(t, "enterprise", result.Plan)
		assert.True(t, result.Active)
		mockOrgRepo.AssertExpectations(t)
	})

	t.Run("validation fails - empty name", func(t *testing.T) {
		// Arrange
		mockOrgRepo := new(MockOrganizationRepository)
		mockUserRepo := new(MockUserRepository)
		mockLogger := createPermissiveMockLogger()

		uc := NewOrganizationUseCase(mockOrgRepo, mockUserRepo, mockLogger)

		req := &domain.CreateOrganizationRequest{
			Name: "",
			Plan: "basic",
		}

		// Act
		result, err := uc.CreateOrganization(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "organization name is required")
		mockOrgRepo.AssertNotCalled(t, "Create")
	})

	t.Run("validation fails - invalid plan", func(t *testing.T) {
		// Arrange
		mockOrgRepo := new(MockOrganizationRepository)
		mockUserRepo := new(MockUserRepository)
		mockLogger := createPermissiveMockLogger()

		uc := NewOrganizationUseCase(mockOrgRepo, mockUserRepo, mockLogger)

		req := &domain.CreateOrganizationRequest{
			Name: "Test Org",
			Plan: "invalid_plan",
		}

		// Act
		result, err := uc.CreateOrganization(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "invalid plan")
		mockOrgRepo.AssertNotCalled(t, "Create")
	})

	t.Run("organization already exists", func(t *testing.T) {
		// Arrange
		mockOrgRepo := new(MockOrganizationRepository)
		mockUserRepo := new(MockUserRepository)
		mockLogger := createPermissiveMockLogger()

		existingOrg := createTestOrganization()

		mockOrgRepo.On("GetByName", mock.Anything, "Test Organization").
			Return(existingOrg, nil)

		uc := NewOrganizationUseCase(mockOrgRepo, mockUserRepo, mockLogger)

		req := &domain.CreateOrganizationRequest{
			Name: "Test Organization",
			Plan: "basic",
		}

		// Act
		result, err := uc.CreateOrganization(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "already exists")
		mockOrgRepo.AssertExpectations(t)
		mockOrgRepo.AssertNotCalled(t, "Create")
	})
}

// TestOrganizationUseCase_DeleteOrganization tests the DeleteOrganization method
func TestOrganizationUseCase_DeleteOrganization(t *testing.T) {
	t.Run("successful deletion", func(t *testing.T) {
		// Arrange
		mockOrgRepo := new(MockOrganizationRepository)
		mockUserRepo := new(MockUserRepository)
		mockLogger := createPermissiveMockLogger()

		testOrg := createTestOrganization()

		mockOrgRepo.On("GetByID", mock.Anything, testOrg.ID.String()).
			Return(testOrg, nil)
		mockOrgRepo.On("GetUsers", mock.Anything, testOrg.ID.String()).
			Return([]*domain.User{}, nil) // No users
		mockOrgRepo.On("Delete", mock.Anything, testOrg.ID.String()).
			Return(nil)

		uc := NewOrganizationUseCase(mockOrgRepo, mockUserRepo, mockLogger)

		// Act
		err := uc.DeleteOrganization(context.Background(), testOrg.ID.String())

		// Assert
		require.NoError(t, err)
		mockOrgRepo.AssertExpectations(t)
	})

	t.Run("business rule - cannot delete with users", func(t *testing.T) {
		// Arrange
		mockOrgRepo := new(MockOrganizationRepository)
		mockUserRepo := new(MockUserRepository)
		mockLogger := createPermissiveMockLogger()

		testOrg := createTestOrganization()
		users := []*domain.User{createTestUser()}

		mockOrgRepo.On("GetByID", mock.Anything, testOrg.ID.String()).
			Return(testOrg, nil)
		mockOrgRepo.On("GetUsers", mock.Anything, testOrg.ID.String()).
			Return(users, nil)

		uc := NewOrganizationUseCase(mockOrgRepo, mockUserRepo, mockLogger)

		// Act
		err := uc.DeleteOrganization(context.Background(), testOrg.ID.String())

		// Assert
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "cannot delete organization with existing users")
		mockOrgRepo.AssertExpectations(t)
		mockOrgRepo.AssertNotCalled(t, "Delete")
	})
}

// TestOrganizationUseCase_AddUserToOrganization tests the AddUserToOrganization method
func TestOrganizationUseCase_AddUserToOrganization(t *testing.T) {
	t.Run("successful addition", func(t *testing.T) {
		// Arrange
		mockOrgRepo := new(MockOrganizationRepository)
		mockUserRepo := new(MockUserRepository)
		mockLogger := createPermissiveMockLogger()

		testOrg := createTestOrganization()
		testUser := createTestUser()

		mockOrgRepo.On("GetByID", mock.Anything, testOrg.ID.String()).
			Return(testOrg, nil)
		mockUserRepo.On("GetByID", mock.Anything, testUser.ID.String()).
			Return(testUser, nil)
		mockOrgRepo.On("AddUser", mock.Anything, testOrg.ID.String(), testUser.ID.String()).
			Return(nil)

		uc := NewOrganizationUseCase(mockOrgRepo, mockUserRepo, mockLogger)

		// Act
		err := uc.AddUserToOrganization(context.Background(), testOrg.ID.String(), testUser.ID.String())

		// Assert
		require.NoError(t, err)
		mockOrgRepo.AssertExpectations(t)
		mockUserRepo.AssertExpectations(t)
	})

	t.Run("validation fails - empty organization ID", func(t *testing.T) {
		// Arrange
		mockOrgRepo := new(MockOrganizationRepository)
		mockUserRepo := new(MockUserRepository)
		mockLogger := createPermissiveMockLogger()

		uc := NewOrganizationUseCase(mockOrgRepo, mockUserRepo, mockLogger)

		// Act
		err := uc.AddUserToOrganization(context.Background(), "", "user-id")

		// Assert
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "organization ID is required")
		mockOrgRepo.AssertNotCalled(t, "AddUser")
	})

	t.Run("organization not found", func(t *testing.T) {
		// Arrange
		mockOrgRepo := new(MockOrganizationRepository)
		mockUserRepo := new(MockUserRepository)
		mockLogger := createPermissiveMockLogger()

		orgID := "nonexistent-org"
		userID := "user-id"

		mockOrgRepo.On("GetByID", mock.Anything, orgID).
			Return(nil, errors.New("organization not found"))

		uc := NewOrganizationUseCase(mockOrgRepo, mockUserRepo, mockLogger)

		// Act
		err := uc.AddUserToOrganization(context.Background(), orgID, userID)

		// Assert
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "organization not found")
		mockOrgRepo.AssertExpectations(t)
		mockOrgRepo.AssertNotCalled(t, "AddUser")
	})

	t.Run("user not found", func(t *testing.T) {
		// Arrange
		mockOrgRepo := new(MockOrganizationRepository)
		mockUserRepo := new(MockUserRepository)
		mockLogger := createPermissiveMockLogger()

		testOrg := createTestOrganization()
		userID := "nonexistent-user"

		mockOrgRepo.On("GetByID", mock.Anything, testOrg.ID.String()).
			Return(testOrg, nil)
		mockUserRepo.On("GetByID", mock.Anything, userID).
			Return(nil, errors.New("user not found"))

		uc := NewOrganizationUseCase(mockOrgRepo, mockUserRepo, mockLogger)

		// Act
		err := uc.AddUserToOrganization(context.Background(), testOrg.ID.String(), userID)

		// Assert
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "user not found")
		mockOrgRepo.AssertExpectations(t)
		mockUserRepo.AssertExpectations(t)
		mockOrgRepo.AssertNotCalled(t, "AddUser")
	})
}

// TestOrganizationUseCase_RemoveUserFromOrganization tests the RemoveUserFromOrganization method
func TestOrganizationUseCase_RemoveUserFromOrganization(t *testing.T) {
	t.Run("successful removal", func(t *testing.T) {
		// Arrange
		mockOrgRepo := new(MockOrganizationRepository)
		mockUserRepo := new(MockUserRepository)
		mockLogger := createPermissiveMockLogger()

		testOrg := createTestOrganization()
		testUser := createTestUser()

		mockOrgRepo.On("GetByID", mock.Anything, testOrg.ID.String()).
			Return(testOrg, nil)
		mockUserRepo.On("GetByID", mock.Anything, testUser.ID.String()).
			Return(testUser, nil)
		mockOrgRepo.On("RemoveUser", mock.Anything, testOrg.ID.String(), testUser.ID.String()).
			Return(nil)

		uc := NewOrganizationUseCase(mockOrgRepo, mockUserRepo, mockLogger)

		// Act
		err := uc.RemoveUserFromOrganization(context.Background(), testOrg.ID.String(), testUser.ID.String())

		// Assert
		require.NoError(t, err)
		mockOrgRepo.AssertExpectations(t)
		mockUserRepo.AssertExpectations(t)
	})

	t.Run("validation fails - empty user ID", func(t *testing.T) {
		// Arrange
		mockOrgRepo := new(MockOrganizationRepository)
		mockUserRepo := new(MockUserRepository)
		mockLogger := createPermissiveMockLogger()

		uc := NewOrganizationUseCase(mockOrgRepo, mockUserRepo, mockLogger)

		// Act
		err := uc.RemoveUserFromOrganization(context.Background(), "org-id", "")

		// Assert
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "user ID is required")
		mockOrgRepo.AssertNotCalled(t, "RemoveUser")
	})
}

// TestOrganizationUseCase_GetOrganizationUsers tests the GetOrganizationUsers method
func TestOrganizationUseCase_GetOrganizationUsers(t *testing.T) {
	t.Run("successful retrieval", func(t *testing.T) {
		// Arrange
		mockOrgRepo := new(MockOrganizationRepository)
		mockUserRepo := new(MockUserRepository)
		mockLogger := createPermissiveMockLogger()

		testOrg := createTestOrganization()
		users := []*domain.User{
			createTestUser(),
			createTestUser(),
		}

		mockOrgRepo.On("GetByID", mock.Anything, testOrg.ID.String()).
			Return(testOrg, nil)
		mockOrgRepo.On("GetUsers", mock.Anything, testOrg.ID.String()).
			Return(users, nil)

		uc := NewOrganizationUseCase(mockOrgRepo, mockUserRepo, mockLogger)

		// Act
		result, err := uc.GetOrganizationUsers(context.Background(), testOrg.ID.String())

		// Assert
		require.NoError(t, err)
		assert.Len(t, result, 2)
		mockOrgRepo.AssertExpectations(t)
	})

	t.Run("organization not found", func(t *testing.T) {
		// Arrange
		mockOrgRepo := new(MockOrganizationRepository)
		mockUserRepo := new(MockUserRepository)
		mockLogger := createPermissiveMockLogger()

		orgID := "nonexistent-org"

		mockOrgRepo.On("GetByID", mock.Anything, orgID).
			Return(nil, errors.New("organization not found"))

		uc := NewOrganizationUseCase(mockOrgRepo, mockUserRepo, mockLogger)

		// Act
		result, err := uc.GetOrganizationUsers(context.Background(), orgID)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "organization not found")
		mockOrgRepo.AssertExpectations(t)
	})
}
