package usecase

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/pkg/auth"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

// MockUserRepository is a mock implementation of domain.UserRepository
type MockUserRepository struct {
	mock.Mock
}

func (m *MockUserRepository) Create(ctx context.Context, user *domain.User) error {
	args := m.Called(ctx, user)
	return args.Error(0)
}

func (m *MockUserRepository) GetByID(ctx context.Context, id string) (*domain.User, error) {
	args := m.Called(ctx, id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.User), args.Error(1)
}

func (m *MockUserRepository) GetByEmail(ctx context.Context, email string) (*domain.User, error) {
	args := m.Called(ctx, email)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.User), args.Error(1)
}

func (m *MockUserRepository) List(ctx context.Context, filter *domain.UserFilter) ([]*domain.User, error) {
	args := m.Called(ctx, filter)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.User), args.Error(1)
}

func (m *MockUserRepository) Update(ctx context.Context, user *domain.User) error {
	args := m.Called(ctx, user)
	return args.Error(0)
}

func (m *MockUserRepository) Delete(ctx context.Context, id string) error {
	args := m.Called(ctx, id)
	return args.Error(0)
}

func (m *MockUserRepository) GetOrganizations(ctx context.Context, userID string) ([]*domain.Organization, error) {
	args := m.Called(ctx, userID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Organization), args.Error(1)
}

// MockLogger is a mock implementation of domain.Logger
type MockLogger struct {
	mock.Mock
}

func (m *MockLogger) Debug(msg string, fields ...any) {
	m.Called(msg, fields)
}

func (m *MockLogger) Info(msg string, fields ...any) {
	m.Called(msg, fields)
}

func (m *MockLogger) Warn(msg string, fields ...any) {
	m.Called(msg, fields)
}

func (m *MockLogger) Error(msg string, fields ...any) {
	m.Called(msg, fields)
}

func (m *MockLogger) Fatal(msg string, fields ...any) {
	m.Called(msg, fields)
}

// Helper functions to create test auth components
func createTestJWTManager(t *testing.T) *auth.JWTManager {
	config := &auth.JWTConfig{
		SecretKey:          "test-secret-key-for-testing-only",
		AccessTokenExpiry:  15 * time.Minute,
		RefreshTokenExpiry: 7 * 24 * time.Hour,
		Issuer:             "arxos-test",
		Audience:           "arxos-test-api",
		Algorithm:          "HS256",
	}
	manager, err := auth.NewJWTManager(config)
	require.NoError(t, err)
	return manager
}

func createTestPasswordManager() *auth.PasswordManager {
	config := &auth.PasswordConfig{
		Cost:             4, // Low cost for faster testing
		MinLength:        8,
		MaxLength:        128,
		RequireSpecial:   true,
		RequireNumbers:   true,
		RequireUppercase: true,
		RequireLowercase: true,
	}
	return auth.NewPasswordManager(config)
}

// createTestSessionManager returns nil since SessionManager requires SessionStore
// which is complex to mock. The AuthUseCase handles nil SessionManager gracefully.
func createTestSessionManager() *auth.SessionManager {
	return nil
}

// createPermissiveMockLogger creates a mock logger that allows all log calls
func createPermissiveMockLogger() *MockLogger {
	mockLogger := new(MockLogger)
	mockLogger.On("Debug", mock.Anything, mock.Anything).Return().Maybe()
	mockLogger.On("Info", mock.Anything, mock.Anything).Return().Maybe()
	mockLogger.On("Warn", mock.Anything, mock.Anything).Return().Maybe()
	mockLogger.On("Error", mock.Anything, mock.Anything).Return().Maybe()
	mockLogger.On("Fatal", mock.Anything, mock.Anything).Return().Maybe()
	return mockLogger
}

// Test fixtures
func createTestUser() *domain.User {
	return &domain.User{
		ID:        types.NewID(),
		Email:     "test@example.com",
		Name:      "Test User",
		Role:      "user",
		Active:    true,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}

// TestAuthUseCase_Login tests the Login method
func TestAuthUseCase_Login(t *testing.T) {
	t.Run("successful login", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(MockUserRepository)
		jwtManager := createTestJWTManager(t)
		passwordManager := createTestPasswordManager()
		sessionManager := createTestSessionManager()
		mockLogger := createPermissiveMockLogger()

		testUser := createTestUser()

		mockUserRepo.On("GetByEmail", mock.Anything, "test@example.com").Return(testUser, nil)

		uc := NewAuthUseCase(mockUserRepo, jwtManager, passwordManager, sessionManager, mockLogger)

		req := &LoginRequest{
			Email:    "test@example.com",
			Password: "password123",
		}

		// Act
		result, err := uc.Login(context.Background(), req)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, testUser.Email, result.User.Email)
		assert.NotEmpty(t, result.AccessToken)
		assert.NotEmpty(t, result.RefreshToken)
		assert.NotEmpty(t, result.SessionID)
		mockUserRepo.AssertExpectations(t)
	})

	t.Run("validation fails - empty email", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(MockUserRepository)
		jwtManager := createTestJWTManager(t)
		passwordManager := createTestPasswordManager()
		sessionManager := createTestSessionManager()
		mockLogger := createPermissiveMockLogger()

		uc := NewAuthUseCase(mockUserRepo, jwtManager, passwordManager, sessionManager, mockLogger)

		req := &LoginRequest{
			Email:    "",
			Password: "password123",
		}

		// Act
		result, err := uc.Login(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "email and password are required")
		mockUserRepo.AssertNotCalled(t, "GetByEmail")
	})

	t.Run("validation fails - empty password", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(MockUserRepository)
		jwtManager := createTestJWTManager(t)
		passwordManager := createTestPasswordManager()
		sessionManager := createTestSessionManager()
		mockLogger := createPermissiveMockLogger()

		uc := NewAuthUseCase(mockUserRepo, jwtManager, passwordManager, sessionManager, mockLogger)

		req := &LoginRequest{
			Email:    "test@example.com",
			Password: "",
		}

		// Act
		result, err := uc.Login(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "email and password are required")
		mockUserRepo.AssertNotCalled(t, "GetByEmail")
	})

	t.Run("user not found", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(MockUserRepository)
		jwtManager := createTestJWTManager(t)
		passwordManager := createTestPasswordManager()
		sessionManager := createTestSessionManager()
		mockLogger := createPermissiveMockLogger()

		mockUserRepo.On("GetByEmail", mock.Anything, "nonexistent@example.com").
			Return(nil, errors.New("user not found"))

		uc := NewAuthUseCase(mockUserRepo, jwtManager, passwordManager, sessionManager, mockLogger)

		req := &LoginRequest{
			Email:    "nonexistent@example.com",
			Password: "password123",
		}

		// Act
		result, err := uc.Login(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		// Should not reveal that user doesn't exist
		assert.Contains(t, err.Error(), "invalid email or password")
		mockUserRepo.AssertExpectations(t)
	})

	t.Run("inactive user account", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(MockUserRepository)
		jwtManager := createTestJWTManager(t)
		passwordManager := createTestPasswordManager()
		sessionManager := createTestSessionManager()
		mockLogger := createPermissiveMockLogger()

		inactiveUser := createTestUser()
		inactiveUser.Active = false

		mockUserRepo.On("GetByEmail", mock.Anything, "test@example.com").Return(inactiveUser, nil)

		uc := NewAuthUseCase(mockUserRepo, jwtManager, passwordManager, sessionManager, mockLogger)

		req := &LoginRequest{
			Email:    "test@example.com",
			Password: "password123",
		}

		// Act
		result, err := uc.Login(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "account is inactive")
		mockUserRepo.AssertExpectations(t)
	})
}

// TestAuthUseCase_Register tests the Register method
func TestAuthUseCase_Register(t *testing.T) {
	t.Run("successful registration", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(MockUserRepository)
		jwtManager := createTestJWTManager(t)
		passwordManager := createTestPasswordManager()
		sessionManager := createTestSessionManager()
		mockLogger := createPermissiveMockLogger()

		mockUserRepo.On("GetByEmail", mock.Anything, "newuser@example.com").
			Return(nil, errors.New("not found")).Once()
		mockUserRepo.On("Create", mock.Anything, mock.MatchedBy(func(u *domain.User) bool {
			return u.Email == "newuser@example.com" && u.Name == "New User"
		})).Return(nil)
		// Auto-login after registration
		mockUserRepo.On("GetByEmail", mock.Anything, "newuser@example.com").
			Return(&domain.User{
				ID:     types.NewID(),
				Email:  "newuser@example.com",
				Name:   "New User",
				Role:   "user",
				Active: true,
			}, nil).Once()

		uc := NewAuthUseCase(mockUserRepo, jwtManager, passwordManager, sessionManager, mockLogger)

		req := &RegisterRequest{
			Email:    "newuser@example.com",
			Password: "StrongPass123!",
			Name:     "New User",
		}

		// Act
		result, err := uc.Register(context.Background(), req)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, "newuser@example.com", result.User.Email)
		assert.NotEmpty(t, result.AccessToken)
		mockUserRepo.AssertExpectations(t)
	})

	t.Run("validation fails - empty email", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(MockUserRepository)
		jwtManager := createTestJWTManager(t)
		passwordManager := createTestPasswordManager()
		sessionManager := createTestSessionManager()
		mockLogger := createPermissiveMockLogger()

		uc := NewAuthUseCase(mockUserRepo, jwtManager, passwordManager, sessionManager, mockLogger)

		req := &RegisterRequest{
			Email:    "",
			Password: "password123",
			Name:     "Test User",
		}

		// Act
		result, err := uc.Register(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "email is required")
	})

	t.Run("validation fails - weak password", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(MockUserRepository)
		jwtManager := createTestJWTManager(t)
		passwordManager := createTestPasswordManager()
		sessionManager := createTestSessionManager()
		mockLogger := createPermissiveMockLogger()

		uc := NewAuthUseCase(mockUserRepo, jwtManager, passwordManager, sessionManager, mockLogger)

		req := &RegisterRequest{
			Email:    "test@example.com",
			Password: "weak",
			Name:     "Test User",
		}

		// Act
		result, err := uc.Register(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "password validation failed")
	})

	t.Run("user already exists", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(MockUserRepository)
		jwtManager := createTestJWTManager(t)
		passwordManager := createTestPasswordManager()
		sessionManager := createTestSessionManager()
		mockLogger := createPermissiveMockLogger()

		existingUser := createTestUser()

		mockUserRepo.On("GetByEmail", mock.Anything, "test@example.com").Return(existingUser, nil)

		uc := NewAuthUseCase(mockUserRepo, jwtManager, passwordManager, sessionManager, mockLogger)

		req := &RegisterRequest{
			Email:    "test@example.com",
			Password: "StrongPass123!",
			Name:     "Test User",
		}

		// Act
		result, err := uc.Register(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "already exists")
		mockUserRepo.AssertExpectations(t)
	})
}

// TestAuthUseCase_Logout tests the Logout method
func TestAuthUseCase_Logout(t *testing.T) {
	t.Run("successful logout with nil session manager", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(MockUserRepository)
		jwtManager := createTestJWTManager(t)
		passwordManager := createTestPasswordManager()
		sessionManager := createTestSessionManager() // Returns nil
		mockLogger := createPermissiveMockLogger()

		uc := NewAuthUseCase(mockUserRepo, jwtManager, passwordManager, sessionManager, mockLogger)

		// Act - with nil sessionManager, this should succeed without actually revoking
		err := uc.Logout(context.Background(), "test-session-id")

		// Assert
		require.NoError(t, err)
	})

	t.Run("validation fails - empty session ID", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(MockUserRepository)
		jwtManager := createTestJWTManager(t)
		passwordManager := createTestPasswordManager()
		sessionManager := createTestSessionManager()
		mockLogger := createPermissiveMockLogger()

		uc := NewAuthUseCase(mockUserRepo, jwtManager, passwordManager, sessionManager, mockLogger)

		// Act
		err := uc.Logout(context.Background(), "")

		// Assert
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "session ID is required")
	})
}

// TestAuthUseCase_ValidateToken tests the ValidateToken method
func TestAuthUseCase_ValidateToken(t *testing.T) {
	t.Run("successful token validation", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(MockUserRepository)
		jwtManager := createTestJWTManager(t)
		passwordManager := createTestPasswordManager()
		sessionManager := createTestSessionManager()
		mockLogger := createPermissiveMockLogger()

		testUser := createTestUser()

		// Generate a real token
		tokenPair, err := jwtManager.GenerateTokenPair(
			testUser.ID.String(),
			testUser.Email,
			testUser.Name,
			testUser.Role,
			"",
			[]string{},
			"session-123",
			nil,
		)
		require.NoError(t, err)

		mockUserRepo.On("GetByID", mock.Anything, testUser.ID.String()).Return(testUser, nil)

		uc := NewAuthUseCase(mockUserRepo, jwtManager, passwordManager, sessionManager, mockLogger)

		// Act
		result, err := uc.ValidateToken(context.Background(), tokenPair.AccessToken)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, testUser.ID.String(), result.UserID)
		assert.Equal(t, testUser.Email, result.Email)
		mockUserRepo.AssertExpectations(t)
	})

	t.Run("validation fails - empty token", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(MockUserRepository)
		jwtManager := createTestJWTManager(t)
		passwordManager := createTestPasswordManager()
		sessionManager := createTestSessionManager()
		mockLogger := createPermissiveMockLogger()

		uc := NewAuthUseCase(mockUserRepo, jwtManager, passwordManager, sessionManager, mockLogger)

		// Act
		result, err := uc.ValidateToken(context.Background(), "")

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "token is required")
	})

	t.Run("invalid token", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(MockUserRepository)
		jwtManager := createTestJWTManager(t)
		passwordManager := createTestPasswordManager()
		sessionManager := createTestSessionManager()
		mockLogger := createPermissiveMockLogger()

		uc := NewAuthUseCase(mockUserRepo, jwtManager, passwordManager, sessionManager, mockLogger)

		// Act
		result, err := uc.ValidateToken(context.Background(), "invalid-token")

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "invalid token")
	})

	t.Run("inactive user account", func(t *testing.T) {
		// Arrange
		mockUserRepo := new(MockUserRepository)
		jwtManager := createTestJWTManager(t)
		passwordManager := createTestPasswordManager()
		sessionManager := createTestSessionManager()
		mockLogger := createPermissiveMockLogger()

		inactiveUser := createTestUser()
		inactiveUser.Active = false

		// Generate a real token
		tokenPair, err := jwtManager.GenerateTokenPair(
			inactiveUser.ID.String(),
			inactiveUser.Email,
			inactiveUser.Name,
			inactiveUser.Role,
			"",
			[]string{},
			"session-123",
			nil,
		)
		require.NoError(t, err)

		mockUserRepo.On("GetByID", mock.Anything, inactiveUser.ID.String()).
			Return(inactiveUser, nil)

		uc := NewAuthUseCase(mockUserRepo, jwtManager, passwordManager, sessionManager, mockLogger)

		// Act
		result, err := uc.ValidateToken(context.Background(), tokenPair.AccessToken)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "account is inactive")
		mockUserRepo.AssertExpectations(t)
	})
}
