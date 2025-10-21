package auth

import (
	"context"
	"errors"
	"testing"

	utesting "github.com/arx-os/arxos/internal/usecase/testing"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

// Test fixtures - using shared helpers from testing_helpers.go
// Note: Organization repository has additional methods (GetByName, GetUsers, AddUser, RemoveUser)
// that need to be added to the shared MockOrganizationRepository if needed

// TestOrganizationUseCase_CreateOrganization tests the CreateOrganization method
func TestOrganizationUseCase_CreateOrganization(t *testing.T) {
	t.Run("successful creation", func(t *testing.T) {
		// Arrange
		mockOrgRepo := new(utesting.MockOrganizationRepository)
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		expectedOrg := utesting.NewOrganizationBuilder().
			WithName("New Organization").
			WithPlan("enterprise").
			Build()

		mockOrgRepo.On("GetByName", mock.Anything, "New Organization").
			Return(nil, errors.New("not found"))
		mockOrgRepo.On("Create", mock.Anything, mock.Anything).Return(nil)

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
		assert.Equal(t, expectedOrg.Name, result.Name)
		assert.Equal(t, expectedOrg.Plan, result.Plan)
		assert.True(t, result.Active)
		mockOrgRepo.AssertExpectations(t)
	})

	t.Run("validation fails - empty name", func(t *testing.T) {
		// Arrange
		mockOrgRepo := new(utesting.MockOrganizationRepository)
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

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
		mockOrgRepo := new(utesting.MockOrganizationRepository)
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

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
		mockOrgRepo := new(utesting.MockOrganizationRepository)
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		existingOrg := utesting.CreateTestOrganization()

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
		mockOrgRepo := new(utesting.MockOrganizationRepository)
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testOrg := utesting.NewOrganizationBuilder().Build()

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
		mockOrgRepo := new(utesting.MockOrganizationRepository)
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testOrg := utesting.CreateTestOrganization()
		users := []*domain.User{utesting.CreateTestUser()}

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
		mockOrgRepo := new(utesting.MockOrganizationRepository)
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testOrg := utesting.NewOrganizationBuilder().Build()
		testUser := utesting.NewUserBuilder().Build()

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
		mockOrgRepo := new(utesting.MockOrganizationRepository)
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

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
		mockOrgRepo := new(utesting.MockOrganizationRepository)
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

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
		mockOrgRepo := new(utesting.MockOrganizationRepository)
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testOrg := utesting.CreateTestOrganization()
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
		mockOrgRepo := new(utesting.MockOrganizationRepository)
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testOrg := utesting.CreateTestOrganization()
		testUser := utesting.CreateTestUser()

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
		mockOrgRepo := new(utesting.MockOrganizationRepository)
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

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
		mockOrgRepo := new(utesting.MockOrganizationRepository)
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testOrg := utesting.CreateTestOrganization()
		users := []*domain.User{
			utesting.CreateTestUser(),
			utesting.CreateTestUser(),
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
		mockOrgRepo := new(utesting.MockOrganizationRepository)
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

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
