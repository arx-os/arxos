package api

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/pkg/models"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
	"golang.org/x/crypto/bcrypt"
)

// TestAuthService_Login tests the Login method
func TestAuthService_Login(t *testing.T) {
	// Create password hash for testing
	passwordHash, _ := bcrypt.GenerateFromPassword([]byte("correctpassword"), bcrypt.DefaultCost)
	
	tests := []struct {
		name          string
		email         string
		password      string
		setupMock     func(*MockDB)
		expectedError string
		checkResponse func(*testing.T, *AuthResponse)
	}{
		{
			name:     "successful login",
			email:    "test@example.com",
			password: "correctpassword",
			setupMock: func(m *MockDB) {
				user := createTestUser("test@example.com", string(passwordHash), true)
				m.On("GetUserByEmail", mock.Anything, "test@example.com").
					Return(user, nil)
				m.On("CreateSession", mock.Anything, mock.AnythingOfType("*models.UserSession")).
					Return(nil)
				m.On("UpdateUser", mock.Anything, mock.AnythingOfType("*models.User")).
					Return(nil)
			},
			checkResponse: func(t *testing.T, resp *AuthResponse) {
				assert.NotNil(t, resp)
				assert.NotEmpty(t, resp.AccessToken)
				assert.NotEmpty(t, resp.RefreshToken)
				assert.Equal(t, "Bearer", resp.TokenType)
				assert.Equal(t, 900, resp.ExpiresIn)
				assert.NotNil(t, resp.User)
				assert.Equal(t, "test@example.com", resp.User.Email)
			},
		},
		{
			name:     "user not found",
			email:    "nonexistent@example.com",
			password: "anypassword",
			setupMock: func(m *MockDB) {
				m.On("GetUserByEmail", mock.Anything, "nonexistent@example.com").
					Return(nil, database.ErrNotFound)
			},
			expectedError: "user not found",
		},
		{
			name:     "invalid password",
			email:    "test@example.com",
			password: "wrongpassword",
			setupMock: func(m *MockDB) {
				user := createTestUser("test@example.com", string(passwordHash), true)
				m.On("GetUserByEmail", mock.Anything, "test@example.com").
					Return(user, nil)
			},
			expectedError: "invalid password",
		},
		{
			name:     "inactive user",
			email:    "inactive@example.com",
			password: "correctpassword",
			setupMock: func(m *MockDB) {
				user := createTestUser("inactive@example.com", string(passwordHash), false)
				m.On("GetUserByEmail", mock.Anything, "inactive@example.com").
					Return(user, nil)
			},
			expectedError: "user account is inactive",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mockDB := new(MockDB)
			tt.setupMock(mockDB)
			
			authService := NewAuthService(mockDB)
			ctx := context.Background()
			
			resp, err := authService.Login(ctx, tt.email, tt.password)
			
			if tt.expectedError != "" {
				require.Error(t, err)
				assert.Contains(t, err.Error(), tt.expectedError)
				assert.Nil(t, resp)
			} else {
				require.NoError(t, err)
				tt.checkResponse(t, resp)
			}
			
			mockDB.AssertExpectations(t)
		})
	}
}

// TestAuthService_Register tests the Register method
func TestAuthService_Register(t *testing.T) {
	tests := []struct {
		name          string
		email         string
		password      string
		userName      string
		setupMock     func(*MockDB)
		expectedError string
		checkResponse func(*testing.T, *User)
	}{
		{
			name:     "successful registration",
			email:    "newuser@example.com",
			password: "SecurePassword123!",
			userName: "New User",
			setupMock: func(m *MockDB) {
				m.On("GetUserByEmail", mock.Anything, "newuser@example.com").
					Return(nil, database.ErrNotFound)
				m.On("CreateUser", mock.Anything, mock.AnythingOfType("*models.User")).
					Return(nil)
			},
			checkResponse: func(t *testing.T, user *User) {
				assert.NotNil(t, user)
				assert.NotEmpty(t, user.ID)
				assert.Equal(t, "newuser@example.com", user.Email)
				assert.Equal(t, "New User", user.Name)
				assert.True(t, user.Active)
			},
		},
		{
			name:     "user already exists",
			email:    "existing@example.com",
			password: "password",
			userName: "Existing User",
			setupMock: func(m *MockDB) {
				existingUser := createTestUser("existing@example.com", "hash", true)
				m.On("GetUserByEmail", mock.Anything, "existing@example.com").
					Return(existingUser, nil)
			},
			expectedError: "user already exists",
		},
		{
			name:     "database error during creation",
			email:    "",
			password: "password",
			userName: "Test User",
			setupMock: func(m *MockDB) {
				m.On("GetUserByEmail", mock.Anything, "").
					Return(nil, database.ErrNotFound)
				m.On("CreateUser", mock.Anything, mock.Anything).
					Return(errors.New("invalid input"))
			},
			expectedError: "failed to create user",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mockDB := new(MockDB)
			tt.setupMock(mockDB)
			
			authService := NewAuthService(mockDB)
			ctx := context.Background()
			
			user, err := authService.Register(ctx, tt.email, tt.password, tt.userName)
			
			if tt.expectedError != "" {
				require.Error(t, err)
				assert.Contains(t, err.Error(), tt.expectedError)
				assert.Nil(t, user)
			} else {
				require.NoError(t, err)
				tt.checkResponse(t, user)
			}
			
			mockDB.AssertExpectations(t)
		})
	}
}

// TestAuthService_ValidateToken tests the ValidateToken method
func TestAuthService_ValidateToken(t *testing.T) {
	tests := []struct {
		name          string
		token         string
		setupMock     func(*MockDB)
		expectedError string
		checkClaims   func(*testing.T, *TokenClaims)
	}{
		{
			name:  "valid token",
			token: "valid-token",
			setupMock: func(m *MockDB) {
				session := createTestSession("test-user-id", "valid-token", "refresh-token")
				user := createTestUser("test@example.com", "hash", true)
				
				m.On("GetSession", mock.Anything, "valid-token").
					Return(session, nil)
				m.On("UpdateSession", mock.Anything, mock.AnythingOfType("*models.UserSession")).
					Return(nil)
				m.On("GetUser", mock.Anything, "test-user-id").
					Return(user, nil)
			},
			checkClaims: func(t *testing.T, claims *TokenClaims) {
				assert.NotNil(t, claims)
				assert.Equal(t, "test-user-id", claims.UserID)
				assert.Equal(t, "test@example.com", claims.Email)
			},
		},
		{
			name:  "expired token",
			token: "expired-token",
			setupMock: func(m *MockDB) {
				session := createTestSession("test-user-id", "expired-token", "refresh-token")
				session.ExpiresAt = time.Now().Add(-1 * time.Hour) // Expired
				
				m.On("GetSession", mock.Anything, "expired-token").
					Return(session, nil)
				m.On("DeleteSession", mock.Anything, "session-id").
					Return(nil)
			},
			expectedError: "token expired",
		},
		{
			name:  "token not found",
			token: "nonexistent-token",
			setupMock: func(m *MockDB) {
				m.On("GetSession", mock.Anything, "nonexistent-token").
					Return(nil, database.ErrNotFound)
			},
			expectedError: "token not found",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mockDB := new(MockDB)
			tt.setupMock(mockDB)
			
			authService := NewAuthService(mockDB)
			ctx := context.Background()
			
			claims, err := authService.ValidateToken(ctx, tt.token)
			
			if tt.expectedError != "" {
				require.Error(t, err)
				assert.Contains(t, err.Error(), tt.expectedError)
				assert.Nil(t, claims)
			} else {
				require.NoError(t, err)
				tt.checkClaims(t, claims)
			}
			
			mockDB.AssertExpectations(t)
		})
	}
}

// TestAuthService_Logout tests the Logout method
func TestAuthService_Logout(t *testing.T) {
	tests := []struct {
		name          string
		token         string
		setupMock     func(*MockDB)
		expectedError string
	}{
		{
			name:  "successful logout",
			token: "valid-token",
			setupMock: func(m *MockDB) {
				session := createTestSession("test-user-id", "valid-token", "refresh-token")
				m.On("GetSession", mock.Anything, "valid-token").
					Return(session, nil)
				m.On("DeleteSession", mock.Anything, "session-id").
					Return(nil)
			},
		},
		{
			name:  "token not found (silent success)",
			token: "nonexistent-token",
			setupMock: func(m *MockDB) {
				m.On("GetSession", mock.Anything, "nonexistent-token").
					Return(nil, database.ErrNotFound)
			},
		},
		{
			name:  "database error",
			token: "error-token",
			setupMock: func(m *MockDB) {
				session := &models.UserSession{
					ID:    "session-id",
					Token: "error-token",
				}
				
				m.On("GetSession", mock.Anything, "error-token").Return(session, nil)
				m.On("DeleteSession", mock.Anything, "session-id").
					Return(errors.New("database error"))
			},
			expectedError: "failed to delete session",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mockDB := new(MockDB)
			tt.setupMock(mockDB)
			
			authService := NewAuthService(mockDB)
			ctx := context.Background()
			
			err := authService.Logout(ctx, tt.token)
			
			if tt.expectedError != "" {
				require.Error(t, err)
				assert.Contains(t, err.Error(), tt.expectedError)
			} else {
				require.NoError(t, err)
			}
			
			mockDB.AssertExpectations(t)
		})
	}
}

// TestAuthService_ChangePassword tests the ChangePassword method
func TestAuthService_ChangePassword(t *testing.T) {
	oldPasswordHash, _ := bcrypt.GenerateFromPassword([]byte("oldpassword"), bcrypt.DefaultCost)
	
	tests := []struct {
		name          string
		userID        string
		oldPassword   string
		newPassword   string
		setupMock     func(*MockDB)
		expectedError string
	}{
		{
			name:        "successful password change",
			userID:      "test-user-id",
			oldPassword: "oldpassword",
			newPassword: "newpassword",
			setupMock: func(m *MockDB) {
				user := createTestUser("test@example.com", string(oldPasswordHash), true)
				m.On("GetUser", mock.Anything, "test-user-id").
					Return(user, nil)
				m.On("UpdateUser", mock.Anything, mock.AnythingOfType("*models.User")).
					Return(nil)
			},
		},
		{
			name:        "incorrect old password",
			userID:      "test-user-id",
			oldPassword: "wrongpassword",
			newPassword: "newpassword",
			setupMock: func(m *MockDB) {
				user := createTestUser("test@example.com", string(oldPasswordHash), true)
				m.On("GetUser", mock.Anything, "test-user-id").
					Return(user, nil)
			},
			expectedError: "invalid old password",
		},
		{
			name:        "user not found",
			userID:      "nonexistent-user",
			oldPassword: "oldpassword",
			newPassword: "newpassword",
			setupMock: func(m *MockDB) {
				m.On("GetUser", mock.Anything, "nonexistent-user").
					Return(nil, database.ErrNotFound)
			},
			expectedError: "user not found",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mockDB := new(MockDB)
			tt.setupMock(mockDB)
			
			authService := NewAuthService(mockDB)
			ctx := context.Background()
			
			err := authService.ChangePassword(ctx, tt.userID, tt.oldPassword, tt.newPassword)
			
			if tt.expectedError != "" {
				require.Error(t, err)
				assert.Contains(t, err.Error(), tt.expectedError)
			} else {
				require.NoError(t, err)
			}
			
			mockDB.AssertExpectations(t)
		})
	}
}