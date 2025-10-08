package integration

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"testing"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestAuthAPI_MobileRegistration(t *testing.T) {
	server, container := setupTestServer(t)
	if server == nil {
		return
	}
	defer server.Close()
	defer container.Shutdown(context.Background())

	t.Run("RegisterMobileUser", func(t *testing.T) {
		registerReq := map[string]any{
			"username":  "testuser",
			"email":     "testuser@example.com",
			"password":  "SecurePass123!",
			"full_name": "Test User",
		}

		body, err := json.Marshal(registerReq)
		require.NoError(t, err)

		req, err := http.NewRequest("POST", server.URL+"/api/v1/mobile/auth/register", bytes.NewBuffer(body))
		require.NoError(t, err)
		req.Header.Set("Content-Type", "application/json")

		resp, err := http.DefaultClient.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusCreated, resp.StatusCode)

		var result map[string]any
		err = json.NewDecoder(resp.Body).Decode(&result)
		require.NoError(t, err)

		assert.Contains(t, result, "user")
		assert.Contains(t, result, "tokens")

		user := result["user"].(map[string]any)
		assert.Equal(t, "testuser@example.com", user["email"])

		tokens := result["tokens"].(map[string]any)
		assert.NotEmpty(t, tokens["access_token"])
		assert.NotEmpty(t, tokens["refresh_token"])
	})
}

func TestAuthAPI_MobileLogin(t *testing.T) {
	server, container := setupTestServer(t)
	if server == nil {
		return
	}
	defer server.Close()
	defer container.Shutdown(context.Background())

	// First register a user
	t.Run("Setup_RegisterUser", func(t *testing.T) {
		registerReq := map[string]any{
			"username": "loginuser",
			"email":    "loginuser@example.com",
			"password": "LoginPass123!",
		}

		body, err := json.Marshal(registerReq)
		require.NoError(t, err)

		req, err := http.NewRequest("POST", server.URL+"/api/v1/mobile/auth/register", bytes.NewBuffer(body))
		require.NoError(t, err)
		req.Header.Set("Content-Type", "application/json")

		resp, err := http.DefaultClient.Do(req)
		require.NoError(t, err)
		resp.Body.Close()
	})

	// Test login
	t.Run("LoginWithCorrectCredentials", func(t *testing.T) {
		loginReq := map[string]any{
			"username": "loginuser@example.com",
			"password": "LoginPass123!",
		}

		body, err := json.Marshal(loginReq)
		require.NoError(t, err)

		req, err := http.NewRequest("POST", server.URL+"/api/v1/mobile/auth/login", bytes.NewBuffer(body))
		require.NoError(t, err)
		req.Header.Set("Content-Type", "application/json")

		resp, err := http.DefaultClient.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var result map[string]any
		err = json.NewDecoder(resp.Body).Decode(&result)
		require.NoError(t, err)

		assert.Contains(t, result, "user")
		assert.Contains(t, result, "tokens")
	})
}

func TestUserUseCase_Registration(t *testing.T) {
	server, container := setupTestServer(t)
	if server == nil {
		return
	}
	defer server.Close()
	defer container.Shutdown(context.Background())

	userUC := container.GetUserUseCase()
	ctx := context.Background()

	t.Run("RegisterUser_Success", func(t *testing.T) {
		user, err := userUC.RegisterUser(ctx, "newuser@example.com", "New User", "SecurePass123!", "user")
		require.NoError(t, err)
		assert.NotNil(t, user)
		assert.Equal(t, "newuser@example.com", user.Email)
		assert.Equal(t, "New User", user.Name)
		assert.Equal(t, "user", user.Role)
		assert.True(t, user.Active)
	})

	t.Run("RegisterUser_DuplicateEmail", func(t *testing.T) {
		// Try to register with same email again
		_, err := userUC.RegisterUser(ctx, "newuser@example.com", "Duplicate User", "AnotherPass123!", "user")
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "already exists")
	})

	t.Run("RegisterUser_WeakPassword", func(t *testing.T) {
		_, err := userUC.RegisterUser(ctx, "weakpass@example.com", "Weak Pass User", "weak", "user")
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "password")
	})
}

func TestUserUseCase_List(t *testing.T) {
	server, container := setupTestServer(t)
	if server == nil {
		return
	}
	defer server.Close()
	defer container.Shutdown(context.Background())

	userUC := container.GetUserUseCase()
	ctx := context.Background()

	// Create some users first
	userUC.RegisterUser(ctx, "user1@example.com", "User One", "Pass123!@#", "user")
	userUC.RegisterUser(ctx, "user2@example.com", "User Two", "Pass456!@#", "admin")
	userUC.RegisterUser(ctx, "user3@example.com", "User Three", "Pass789!@#", "viewer")

	t.Run("ListAllUsers", func(t *testing.T) {
		filter := &domain.UserFilter{
			Limit:  100,
			Offset: 0,
		}

		users, err := userUC.ListUsers(ctx, filter)
		require.NoError(t, err)
		assert.GreaterOrEqual(t, len(users), 3)
	})

	t.Run("FilterByRole", func(t *testing.T) {
		role := "admin"
		filter := &domain.UserFilter{
			Role:   &role,
			Limit:  100,
			Offset: 0,
		}

		users, err := userUC.ListUsers(ctx, filter)
		require.NoError(t, err)
		assert.GreaterOrEqual(t, len(users), 1)
		for _, user := range users {
			assert.Equal(t, "admin", user.Role)
		}
	})

	t.Run("FilterActiveOnly", func(t *testing.T) {
		active := true
		filter := &domain.UserFilter{
			Active: &active,
			Limit:  100,
			Offset: 0,
		}

		users, err := userUC.ListUsers(ctx, filter)
		require.NoError(t, err)
		for _, user := range users {
			assert.True(t, user.Active)
		}
	})
}

func TestUserUseCase_Update(t *testing.T) {
	server, container := setupTestServer(t)
	if server == nil {
		return
	}
	defer server.Close()
	defer container.Shutdown(context.Background())

	userUC := container.GetUserUseCase()
	ctx := context.Background()

	// Create a user
	user, err := userUC.RegisterUser(ctx, "updatetest@example.com", "Update Test", "UpdatePass123!", "user")
	require.NoError(t, err)

	t.Run("UpdateUserName", func(t *testing.T) {
		newName := "Updated Name"
		req := &domain.UpdateUserRequest{
			ID:   user.ID,
			Name: &newName,
		}

		updatedUser, err := userUC.UpdateUser(ctx, req)
		require.NoError(t, err)
		assert.Equal(t, newName, updatedUser.Name)
	})

	t.Run("UpdateUserRole", func(t *testing.T) {
		newRole := "admin"
		req := &domain.UpdateUserRequest{
			ID:   user.ID,
			Role: &newRole,
		}

		updatedUser, err := userUC.UpdateUser(ctx, req)
		require.NoError(t, err)
		assert.Equal(t, newRole, updatedUser.Role)
	})

	t.Run("DeactivateUser", func(t *testing.T) {
		inactive := false
		req := &domain.UpdateUserRequest{
			ID:     user.ID,
			Active: &inactive,
		}

		updatedUser, err := userUC.UpdateUser(ctx, req)
		require.NoError(t, err)
		assert.False(t, updatedUser.Active)
	})
}
