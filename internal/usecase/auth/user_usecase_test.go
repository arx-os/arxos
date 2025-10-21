package auth

import (
	utesting "github.com/arx-os/arxos/internal/usecase/testing"
	"context"
	"errors"
	"testing"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

// TestUserUseCase_CreateUser tests the CreateUser method
func TestUserUseCase_CreateUser(t *testing.T) {
	t.Run("successful creation", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		mockUserRepo.On("GetByEmail", mock.Anything, "newuser@example.com").
			Return(nil, errors.New("not found"))
		mockUserRepo.On("Create", mock.Anything, mock.MatchedBy(func(u *domain.User) bool {
			return u.Email == "newuser@example.com" && u.Name == "New User" && u.Role == "user"
		})).Return(nil)

		uc := NewUserUseCase(mockUserRepo, mockLogger)

		req := &domain.CreateUserRequest{
			Email: "newuser@example.com",
			Name:  "New User",
			Role:  "user",
		}

		// Act
		result, err := uc.CreateUser(context.Background(), req)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, "newuser@example.com", result.Email)
		assert.Equal(t, "New User", result.Name)
		assert.Equal(t, "user", result.Role)
		assert.True(t, result.Active)
		mockUserRepo.AssertExpectations(t)
	})

	t.Run("validation fails - empty email", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		uc := NewUserUseCase(mockUserRepo, mockLogger)

		req := &domain.CreateUserRequest{
			Email: "",
			Name:  "Test User",
			Role:  "user",
		}

		// Act
		result, err := uc.CreateUser(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "email is required")
		mockUserRepo.AssertNotCalled(t, "Create")
	})

	t.Run("validation fails - invalid role", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		uc := NewUserUseCase(mockUserRepo, mockLogger)

		req := &domain.CreateUserRequest{
			Email: "test@example.com",
			Name:  "Test User",
			Role:  "invalid_role",
		}

		// Act
		result, err := uc.CreateUser(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "invalid role")
		mockUserRepo.AssertNotCalled(t, "Create")
	})

	t.Run("user already exists", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		existingUser := utesting.CreateTestUser()

		mockUserRepo.On("GetByEmail", mock.Anything, "test@example.com").
			Return(existingUser, nil)

		uc := NewUserUseCase(mockUserRepo, mockLogger)

		req := &domain.CreateUserRequest{
			Email: "test@example.com",
			Name:  "Test User",
			Role:  "user",
		}

		// Act
		result, err := uc.CreateUser(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "already exists")
		mockUserRepo.AssertExpectations(t)
		mockUserRepo.AssertNotCalled(t, "Create")
	})
}

// TestUserUseCase_GetUser tests the GetUser method
func TestUserUseCase_GetUser(t *testing.T) {
	t.Run("successful retrieval", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testUser := utesting.CreateTestUser()

		mockUserRepo.On("GetByID", mock.Anything, testUser.ID.String()).
			Return(testUser, nil)

		uc := NewUserUseCase(mockUserRepo, mockLogger)

		// Act
		result, err := uc.GetUser(context.Background(), testUser.ID.String())

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, testUser.Email, result.Email)
		mockUserRepo.AssertExpectations(t)
	})

	t.Run("validation fails - empty ID", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		uc := NewUserUseCase(mockUserRepo, mockLogger)

		// Act
		result, err := uc.GetUser(context.Background(), "")

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "user ID is required")
		mockUserRepo.AssertNotCalled(t, "GetByID")
	})

	t.Run("user not found", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testID := "nonexistent-id"

		mockUserRepo.On("GetByID", mock.Anything, testID).
			Return(nil, errors.New("user not found"))

		uc := NewUserUseCase(mockUserRepo, mockLogger)

		// Act
		result, err := uc.GetUser(context.Background(), testID)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to get user")
		mockUserRepo.AssertExpectations(t)
	})
}

// TestUserUseCase_UpdateUser tests the UpdateUser method
func TestUserUseCase_UpdateUser(t *testing.T) {
	t.Run("successful update", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		existingUser := utesting.CreateTestUser()
		newName := "Updated Name"
		newRole := "admin"

		mockUserRepo.On("GetByID", mock.Anything, existingUser.ID.String()).
			Return(existingUser, nil)
		mockUserRepo.On("Update", mock.Anything, mock.MatchedBy(func(u *domain.User) bool {
			return u.Name == newName && u.Role == newRole
		})).Return(nil)

		uc := NewUserUseCase(mockUserRepo, mockLogger)

		req := &domain.UpdateUserRequest{
			ID:   existingUser.ID,
			Name: &newName,
			Role: &newRole,
		}

		// Act
		result, err := uc.UpdateUser(context.Background(), req)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, newName, result.Name)
		assert.Equal(t, newRole, result.Role)
		mockUserRepo.AssertExpectations(t)
	})

	t.Run("validation fails - invalid role", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		existingUser := utesting.CreateTestUser()
		invalidRole := "invalid_role"

		mockUserRepo.On("GetByID", mock.Anything, existingUser.ID.String()).
			Return(existingUser, nil)

		uc := NewUserUseCase(mockUserRepo, mockLogger)

		req := &domain.UpdateUserRequest{
			ID:   existingUser.ID,
			Role: &invalidRole,
		}

		// Act
		result, err := uc.UpdateUser(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "invalid role")
		mockUserRepo.AssertNotCalled(t, "Update")
	})
}

// TestUserUseCase_DeleteUser tests the DeleteUser method
func TestUserUseCase_DeleteUser(t *testing.T) {
	t.Run("successful deletion", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testUser := utesting.CreateTestUser()
		testUser.Active = false // Inactive user can be deleted

		mockUserRepo.On("GetByID", mock.Anything, testUser.ID.String()).
			Return(testUser, nil)
		mockUserRepo.On("Delete", mock.Anything, testUser.ID.String()).
			Return(nil)

		uc := NewUserUseCase(mockUserRepo, mockLogger)

		// Act
		err := uc.DeleteUser(context.Background(), testUser.ID.String())

		// Assert
		require.NoError(t, err)
		mockUserRepo.AssertExpectations(t)
	})

	t.Run("business rule - cannot delete active user", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testUser := utesting.CreateTestUser()
		testUser.Active = true // Active user cannot be deleted

		mockUserRepo.On("GetByID", mock.Anything, testUser.ID.String()).
			Return(testUser, nil)

		uc := NewUserUseCase(mockUserRepo, mockLogger)

		// Act
		err := uc.DeleteUser(context.Background(), testUser.ID.String())

		// Assert
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "cannot delete active user")
		mockUserRepo.AssertExpectations(t)
		mockUserRepo.AssertNotCalled(t, "Delete")
	})
}

// TestUserUseCase_ListUsers tests the ListUsers method
func TestUserUseCase_ListUsers(t *testing.T) {
	t.Run("successful list with default pagination", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		users := []*domain.User{
			utesting.CreateTestUser(),
			utesting.CreateTestUser(),
		}

		mockUserRepo.On("List", mock.Anything, mock.MatchedBy(func(f *domain.UserFilter) bool {
			return f.Limit == 100
		})).Return(users, nil)

		uc := NewUserUseCase(mockUserRepo, mockLogger)

		filter := &domain.UserFilter{}

		// Act
		result, err := uc.ListUsers(context.Background(), filter)

		// Assert
		require.NoError(t, err)
		assert.Len(t, result, 2)
		mockUserRepo.AssertExpectations(t)
	})
}

// TestUserUseCase_AuthenticateUser tests the AuthenticateUser method
func TestUserUseCase_AuthenticateUser(t *testing.T) {
	t.Run("successful authentication", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testUser := utesting.CreateTestUser()

		mockUserRepo.On("GetByEmail", mock.Anything, "test@example.com").
			Return(testUser, nil)

		uc := NewUserUseCase(mockUserRepo, mockLogger)

		// Act
		result, err := uc.AuthenticateUser(context.Background(), "test@example.com", "password123")

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, testUser.Email, result.Email)
		mockUserRepo.AssertExpectations(t)
	})

	t.Run("inactive user", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		inactiveUser := utesting.CreateTestUser()
		inactiveUser.Active = false

		mockUserRepo.On("GetByEmail", mock.Anything, "test@example.com").
			Return(inactiveUser, nil)

		uc := NewUserUseCase(mockUserRepo, mockLogger)

		// Act
		result, err := uc.AuthenticateUser(context.Background(), "test@example.com", "password123")

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "user account is inactive")
		mockUserRepo.AssertExpectations(t)
	})
}

// TestUserUseCase_RegisterUser tests the RegisterUser method
func TestUserUseCase_RegisterUser(t *testing.T) {
	t.Run("successful registration", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		mockUserRepo.On("GetByEmail", mock.Anything, "newuser@example.com").
			Return(nil, errors.New("not found"))
		mockUserRepo.On("Create", mock.Anything, mock.MatchedBy(func(u *domain.User) bool {
			return u.Email == "newuser@example.com"
		})).Return(nil)

		uc := NewUserUseCase(mockUserRepo, mockLogger)

		// Act
		result, err := uc.RegisterUser(context.Background(), "newuser@example.com", "New User", "StrongPass123!", "user")

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, "newuser@example.com", result.Email)
		mockUserRepo.AssertExpectations(t)
	})

	t.Run("validation fails - weak password", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		uc := NewUserUseCase(mockUserRepo, mockLogger)

		// Act
		result, err := uc.RegisterUser(context.Background(), "test@example.com", "Test User", "weak", "user")

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "password validation failed")
	})
}

// TestUserUseCase_ChangePassword tests the ChangePassword method
func TestUserUseCase_ChangePassword(t *testing.T) {
	t.Run("successful password change", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testUser := utesting.CreateTestUser()

		mockUserRepo.On("GetByID", mock.Anything, testUser.ID.String()).
			Return(testUser, nil)
		mockUserRepo.On("Update", mock.Anything, mock.Anything).
			Return(nil)

		uc := NewUserUseCase(mockUserRepo, mockLogger)

		// Act
		err := uc.ChangePassword(context.Background(), testUser.ID.String(), "OldPass123!", "NewStrongPass123!")

		// Assert
		require.NoError(t, err)
		mockUserRepo.AssertExpectations(t)
	})

	t.Run("validation fails - weak new password", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testUser := utesting.CreateTestUser()

		mockUserRepo.On("GetByID", mock.Anything, testUser.ID.String()).
			Return(testUser, nil)

		uc := NewUserUseCase(mockUserRepo, mockLogger)

		// Act
		err := uc.ChangePassword(context.Background(), testUser.ID.String(), "OldPass123!", "weak")

		// Assert
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "new password validation failed")
		mockUserRepo.AssertNotCalled(t, "Update")
	})
}

// TestUserUseCase_GetUserOrganizations tests the GetUserOrganizations method
func TestUserUseCase_GetUserOrganizations(t *testing.T) {
	t.Run("successful retrieval", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testUser := utesting.CreateTestUser()
		organizations := []*domain.Organization{
			{ID: types.NewID(), Name: "Test Org 1"},
			{ID: types.NewID(), Name: "Test Org 2"},
		}

		mockUserRepo.On("GetOrganizations", mock.Anything, testUser.ID.String()).
			Return(organizations, nil)

		uc := NewUserUseCase(mockUserRepo, mockLogger)

		// Act
		result, err := uc.GetUserOrganizations(context.Background(), testUser.ID.String())

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Len(t, result, 2)
		mockUserRepo.AssertExpectations(t)
	})

	t.Run("validation fails - empty user ID", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(utesting.MockUserRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		uc := NewUserUseCase(mockUserRepo, mockLogger)

		// Act
		result, err := uc.GetUserOrganizations(context.Background(), "")

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "user ID is required")
		mockUserRepo.AssertNotCalled(t, "GetOrganizations")
	})
}
