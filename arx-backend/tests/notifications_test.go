package tests

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"arx/models"
	"arx/repository"
	"arx/services/notifications"
	"arx/utils"

	"github.com/go-chi/chi/v5"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
)

// TestNotificationService provides comprehensive testing for notification services
type TestNotificationService struct {
	db      *gorm.DB
	repo    *repository.NotificationRepository
	service *notifications.EnhancedNotificationService
	router  *chi.Mux
	handler *notifications.EnhancedNotificationHandler
}

// setupTestDB creates an in-memory SQLite database for testing
func setupTestDB(t *testing.T) *gorm.DB {
	db, err := gorm.Open(sqlite.Open(":memory:"), &gorm.Config{})
	require.NoError(t, err)

	// Auto-migrate the database
	err = db.AutoMigrate(
		&models.User{},
		&models.Building{},
		&models.NotificationEnhanced{},
		&models.NotificationDeliveryEnhanced{},
		&models.NotificationTemplateEnhanced{},
		&models.NotificationConfigEnhanced{},
		&models.NotificationPreference{},
		&models.NotificationLog{},
		&models.NotificationStats{},
		&models.NotificationQueue{},
		&models.NotificationChannelConfig{},
	)
	require.NoError(t, err)

	return db
}

// setupTestService creates a complete test service setup
func setupTestService(t *testing.T) *TestNotificationService {
	db := setupTestDB(t)
	repo := repository.NewNotificationRepository(db)
	service := notifications.NewEnhancedNotificationService(repo)
	handler := notifications.NewEnhancedNotificationHandler(service, db)

	// Setup Gin router
	utils.SetMode(utils.TestMode)
	router := chi.NewRouter()
	handler.RegisterRoutes(router)

	return &TestNotificationService{
		db:      db,
		repo:    repo,
		service: service,
		router:  router,
		handler: handler,
	}
}

// createTestUser creates a test user in the database
func (ts *TestNotificationService) createTestUser(t *testing.T) *models.User {
	user := &models.User{
		Email:    "test@example.com",
		Username: "testuser",
		Password: "password123",
		Role:     "user",
	}

	err := ts.db.Create(user).Error
	require.NoError(t, err)
	return user
}

// createTestTemplate creates a test notification template
func (ts *TestNotificationService) createTestTemplate(t *testing.T) *models.NotificationTemplateEnhanced {
	template := &models.NotificationTemplateEnhanced{
		Name:        "test_template",
		Description: "Test notification template",
		Type:        models.NotificationTypeSystem,
		Subject:     "Test Subject",
		Body:        "Hello {{user_name}}, this is a test message.",
		HTMLBody:    "<h1>Hello {{user_name}}</h1><p>This is a test message.</p>",
		Variables:   []byte(`{"user_name": "string"}`),
		IsActive:    true,
		CreatedBy:   1,
	}

	err := ts.db.Create(template).Error
	require.NoError(t, err)
	return template
}

// createTestConfig creates a test notification configuration
func (ts *TestNotificationService) createTestConfig(t *testing.T) *models.NotificationConfigEnhanced {
	config := &models.NotificationConfigEnhanced{
		Name:          "test_config",
		Description:   "Test notification configuration",
		Channels:      []byte(`["email", "slack"]`),
		Priority:      models.NotificationPriorityNormal,
		RetryAttempts: 3,
		RetryDelay:    60,
		Timeout:       30,
		IsActive:      true,
		CreatedBy:     1,
	}

	err := ts.db.Create(config).Error
	require.NoError(t, err)
	return config
}

// TestNotificationRepository tests the notification repository
func TestNotificationRepository(t *testing.T) {
	ts := setupTestService(t)

	t.Run("CreateNotification", func(t *testing.T) {
		user := ts.createTestUser(t)

		notification := &models.NotificationEnhanced{
			Title:       "Test Notification",
			Message:     "This is a test notification",
			Type:        models.NotificationTypeSystem,
			Channels:    []byte(`["email"]`),
			Priority:    models.NotificationPriorityNormal,
			Status:      models.NotificationStatusPending,
			RecipientID: user.ID,
			SenderID:    &user.ID,
		}

		err := ts.repo.CreateNotification(notification)
		assert.NoError(t, err)
		assert.NotZero(t, notification.ID)
	})

	t.Run("GetNotificationByID", func(t *testing.T) {
		user := ts.createTestUser(t)

		notification := &models.NotificationEnhanced{
			Title:       "Test Notification",
			Message:     "This is a test notification",
			Type:        models.NotificationTypeSystem,
			Channels:    []byte(`["email"]`),
			Priority:    models.NotificationPriorityNormal,
			Status:      models.NotificationStatusPending,
			RecipientID: user.ID,
		}

		err := ts.repo.CreateNotification(notification)
		require.NoError(t, err)

		retrieved, err := ts.repo.GetNotificationByID(notification.ID)
		assert.NoError(t, err)
		assert.Equal(t, notification.Title, retrieved.Title)
		assert.Equal(t, notification.Message, retrieved.Message)
	})

	t.Run("GetNotificationsWithFilters", func(t *testing.T) {
		user := ts.createTestUser(t)

		// Create multiple notifications
		for i := 0; i < 5; i++ {
			notification := &models.NotificationEnhanced{
				Title:       fmt.Sprintf("Test Notification %d", i),
				Message:     fmt.Sprintf("This is test notification %d", i),
				Type:        models.NotificationTypeSystem,
				Channels:    []byte(`["email"]`),
				Priority:    models.NotificationPriorityNormal,
				Status:      models.NotificationStatusPending,
				RecipientID: user.ID,
			}
			err := ts.repo.CreateNotification(notification)
			require.NoError(t, err)
		}

		filters := map[string]interface{}{
			"recipient_id": user.ID,
			"type":         models.NotificationTypeSystem,
		}

		notifications, total, err := ts.repo.GetNotifications(filters, 1, 10)
		assert.NoError(t, err)
		assert.Equal(t, int64(5), total)
		assert.Len(t, notifications, 5)
	})

	t.Run("CreateDelivery", func(t *testing.T) {
		user := ts.createTestUser(t)

		notification := &models.NotificationEnhanced{
			Title:       "Test Notification",
			Message:     "This is a test notification",
			Type:        models.NotificationTypeSystem,
			Channels:    []byte(`["email"]`),
			Priority:    models.NotificationPriorityNormal,
			Status:      models.NotificationStatusPending,
			RecipientID: user.ID,
		}

		err := ts.repo.CreateNotification(notification)
		require.NoError(t, err)

		delivery := &models.NotificationDeliveryEnhanced{
			NotificationID: notification.ID,
			Channel:        models.NotificationChannelTypeEmail,
			Status:         models.NotificationStatusPending,
			AttemptNumber:  1,
		}

		err = ts.repo.CreateDelivery(delivery)
		assert.NoError(t, err)
		assert.NotZero(t, delivery.ID)
	})

	t.Run("UpdateDeliveryStatus", func(t *testing.T) {
		user := ts.createTestUser(t)

		notification := &models.NotificationEnhanced{
			Title:       "Test Notification",
			Message:     "This is a test notification",
			Type:        models.NotificationTypeSystem,
			Channels:    []byte(`["email"]`),
			Priority:    models.NotificationPriorityNormal,
			Status:      models.NotificationStatusPending,
			RecipientID: user.ID,
		}

		err := ts.repo.CreateNotification(notification)
		require.NoError(t, err)

		delivery := &models.NotificationDeliveryEnhanced{
			NotificationID: notification.ID,
			Channel:        models.NotificationChannelTypeEmail,
			Status:         models.NotificationStatusPending,
			AttemptNumber:  1,
		}

		err = ts.repo.CreateDelivery(delivery)
		require.NoError(t, err)

		// Update delivery status
		now := time.Now()
		delivery.Status = models.NotificationStatusDelivered
		delivery.DeliveredAt = &now

		err = ts.repo.UpdateDelivery(delivery)
		assert.NoError(t, err)

		// Verify update
		updated, err := ts.repo.GetDeliveryByID(delivery.ID)
		assert.NoError(t, err)
		assert.Equal(t, models.NotificationStatusDelivered, updated.Status)
		assert.NotNil(t, updated.DeliveredAt)
	})
}

// TestNotificationService tests the notification service
func TestNotificationService(t *testing.T) {
	ts := setupTestService(t)

	t.Run("SendNotification", func(t *testing.T) {
		user := ts.createTestUser(t)
		template := ts.createTestTemplate(t)
		config := ts.createTestConfig(t)

		request := &notifications.SendNotificationRequest{
			Title:       "Test Notification",
			Message:     "This is a test notification",
			Type:        models.NotificationTypeSystem,
			Channels:    []models.NotificationChannelType{models.NotificationChannelTypeEmail},
			Priority:    models.NotificationPriorityNormal,
			RecipientID: user.ID,
			TemplateID:  &template.ID,
			ConfigID:    &config.ID,
			TemplateData: map[string]interface{}{
				"user_name": "Test User",
			},
		}

		response, err := ts.service.SendNotification(request)
		assert.NoError(t, err)
		assert.True(t, response.Success)
		assert.NotZero(t, response.NotificationID)
	})

	t.Run("SendNotificationWithTemplate", func(t *testing.T) {
		user := ts.createTestUser(t)
		template := ts.createTestTemplate(t)

		request := &notifications.SendNotificationRequest{
			Title:       "Welcome {{user_name}}",
			Message:     "Hello {{user_name}}, welcome to our platform!",
			Type:        models.NotificationTypeUser,
			Channels:    []models.NotificationChannelType{models.NotificationChannelTypeEmail},
			Priority:    models.NotificationPriorityNormal,
			RecipientID: user.ID,
			TemplateID:  &template.ID,
			TemplateData: map[string]interface{}{
				"user_name": "John Doe",
			},
		}

		response, err := ts.service.SendNotification(request)
		assert.NoError(t, err)
		assert.True(t, response.Success)

		// Verify template substitution
		notification, err := ts.repo.GetNotificationByID(response.NotificationID)
		assert.NoError(t, err)
		assert.Contains(t, notification.Title, "John Doe")
		assert.Contains(t, notification.Message, "John Doe")
	})

	t.Run("GetNotificationHistory", func(t *testing.T) {
		user := ts.createTestUser(t)

		// Create test notifications
		for i := 0; i < 3; i++ {
			notification := &models.NotificationEnhanced{
				Title:       fmt.Sprintf("Test Notification %d", i),
				Message:     fmt.Sprintf("This is test notification %d", i),
				Type:        models.NotificationTypeSystem,
				Channels:    []byte(`["email"]`),
				Priority:    models.NotificationPriorityNormal,
				Status:      models.NotificationStatusSent,
				RecipientID: user.ID,
			}
			err := ts.repo.CreateNotification(notification)
			require.NoError(t, err)
		}

		request := &notifications.GetNotificationHistoryRequest{
			RecipientID: user.ID,
			Page:        1,
			PageSize:    10,
		}

		response, err := ts.service.GetNotificationHistory(request)
		assert.NoError(t, err)
		assert.Equal(t, int64(3), response.Total)
		assert.Len(t, response.Notifications, 3)
	})

	t.Run("GetNotificationStatistics", func(t *testing.T) {
		user := ts.createTestUser(t)

		// Create test notifications with different statuses
		statuses := []models.NotificationStatus{
			models.NotificationStatusSent,
			models.NotificationStatusDelivered,
			models.NotificationStatusFailed,
		}

		for i, status := range statuses {
			notification := &models.NotificationEnhanced{
				Title:       fmt.Sprintf("Test Notification %d", i),
				Message:     fmt.Sprintf("This is test notification %d", i),
				Type:        models.NotificationTypeSystem,
				Channels:    []byte(`["email"]`),
				Priority:    models.NotificationPriorityNormal,
				Status:      status,
				RecipientID: user.ID,
			}
			err := ts.repo.CreateNotification(notification)
			require.NoError(t, err)
		}

		response, err := ts.service.GetNotificationStatistics()
		assert.NoError(t, err)
		assert.NotNil(t, response)
		assert.Equal(t, int64(3), response.TotalNotifications)
	})
}

// TestNotificationAPI tests the HTTP API endpoints
func TestNotificationAPI(t *testing.T) {
	ts := setupTestService(t)

	t.Run("SendNotificationAPI", func(t *testing.T) {
		user := ts.createTestUser(t)

		requestBody := map[string]interface{}{
			"title":        "Test API Notification",
			"message":      "This is a test notification via API",
			"type":         "system",
			"channels":     []string{"email"},
			"priority":     "normal",
			"recipient_id": user.ID,
		}

		jsonBody, _ := json.Marshal(requestBody)
		req := httptest.NewRequest("POST", "/api/notifications/send", bytes.NewBuffer(jsonBody))
		req.Header.Set("Content-Type", "application/json")

		w := httptest.NewRecorder()
		ts.router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response map[string]interface{}
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.True(t, response["success"].(bool))
	})

	t.Run("GetNotificationHistoryAPI", func(t *testing.T) {
		user := ts.createTestUser(t)

		// Create test notification
		notification := &models.NotificationEnhanced{
			Title:       "Test API History",
			Message:     "This is a test notification for API history",
			Type:        models.NotificationTypeSystem,
			Channels:    []byte(`["email"]`),
			Priority:    models.NotificationPriorityNormal,
			Status:      models.NotificationStatusSent,
			RecipientID: user.ID,
		}
		err := ts.repo.CreateNotification(notification)
		require.NoError(t, err)

		req := httptest.NewRequest("GET", fmt.Sprintf("/api/notifications/history?recipient_id=%d", user.ID), nil)
		w := httptest.NewRecorder()
		ts.router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response map[string]interface{}
		err = json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.Equal(t, float64(1), response["total"])
	})

	t.Run("GetNotificationStatisticsAPI", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/notifications/statistics", nil)
		w := httptest.NewRecorder()
		ts.router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response map[string]interface{}
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.NotNil(t, response["statistics"])
	})

	t.Run("CreateNotificationTemplateAPI", func(t *testing.T) {
		user := ts.createTestUser(t)

		requestBody := map[string]interface{}{
			"name":        "API Test Template",
			"description": "Test template created via API",
			"type":        "system",
			"channels":    []string{"email", "slack"},
			"subject":     "Test Subject",
			"body":        "Hello {{user_name}}, this is a test.",
			"html_body":   "<h1>Hello {{user_name}}</h1><p>This is a test.</p>",
			"variables":   map[string]string{"user_name": "string"},
			"is_active":   true,
			"created_by":  user.ID,
		}

		jsonBody, _ := json.Marshal(requestBody)
		req := httptest.NewRequest("POST", "/api/notifications/templates", bytes.NewBuffer(jsonBody))
		req.Header.Set("Content-Type", "application/json")

		w := httptest.NewRecorder()
		ts.router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response map[string]interface{}
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.True(t, response["success"].(bool))
	})

	t.Run("GetNotificationTemplatesAPI", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/notifications/templates", nil)
		w := httptest.NewRecorder()
		ts.router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response map[string]interface{}
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.NotNil(t, response["templates"])
	})
}

// TestNotificationIntegration tests integration scenarios
func TestNotificationIntegration(t *testing.T) {
	ts := setupTestService(t)

	t.Run("EndToEndNotificationFlow", func(t *testing.T) {
		user := ts.createTestUser(t)
		template := ts.createTestTemplate(t)

		// 1. Create notification via API
		requestBody := map[string]interface{}{
			"title":        "Integration Test",
			"message":      "Hello {{user_name}}, this is an integration test.",
			"type":         "system",
			"channels":     []string{"email"},
			"priority":     "normal",
			"recipient_id": user.ID,
			"template_id":  template.ID,
			"template_data": map[string]interface{}{
				"user_name": "Integration User",
			},
		}

		jsonBody, _ := json.Marshal(requestBody)
		req := httptest.NewRequest("POST", "/api/notifications/send", bytes.NewBuffer(jsonBody))
		req.Header.Set("Content-Type", "application/json")

		w := httptest.NewRecorder()
		ts.router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response map[string]interface{}
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.True(t, response["success"].(bool))

		notificationID := int(response["notification_id"].(float64))

		// 2. Verify notification was created in database
		notification, err := ts.repo.GetNotificationByID(uint(notificationID))
		assert.NoError(t, err)
		assert.Equal(t, "Integration Test", notification.Title)
		assert.Contains(t, notification.Message, "Integration User")

		// 3. Verify delivery records were created
		deliveries, err := ts.repo.GetDeliveriesByNotificationID(uint(notificationID))
		assert.NoError(t, err)
		assert.Len(t, deliveries, 1)
		assert.Equal(t, models.NotificationChannelTypeEmail, deliveries[0].Channel)

		// 4. Update delivery status
		now := time.Now()
		deliveries[0].Status = models.NotificationStatusDelivered
		deliveries[0].DeliveredAt = &now

		err = ts.repo.UpdateDelivery(&deliveries[0])
		assert.NoError(t, err)

		// 5. Verify notification history includes the notification
		historyReq := &notifications.GetNotificationHistoryRequest{
			RecipientID: user.ID,
			Page:        1,
			PageSize:    10,
		}

		historyResp, err := ts.service.GetNotificationHistory(historyReq)
		assert.NoError(t, err)
		assert.Equal(t, int64(1), historyResp.Total)
		assert.Len(t, historyResp.Notifications, 1)
		assert.Equal(t, uint(notificationID), historyResp.Notifications[0].ID)
	})

	t.Run("MultiChannelNotification", func(t *testing.T) {
		user := ts.createTestUser(t)

		requestBody := map[string]interface{}{
			"title":        "Multi-Channel Test",
			"message":      "This notification should be sent to multiple channels",
			"type":         "alert",
			"channels":     []string{"email", "slack", "sms"},
			"priority":     "high",
			"recipient_id": user.ID,
		}

		jsonBody, _ := json.Marshal(requestBody)
		req := httptest.NewRequest("POST", "/api/notifications/send", bytes.NewBuffer(jsonBody))
		req.Header.Set("Content-Type", "application/json")

		w := httptest.NewRecorder()
		ts.router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response map[string]interface{}
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.True(t, response["success"].(bool))

		notificationID := int(response["notification_id"].(float64))

		// Verify multiple delivery records were created
		deliveries, err := ts.repo.GetDeliveriesByNotificationID(uint(notificationID))
		assert.NoError(t, err)
		assert.Len(t, deliveries, 3)

		channels := make(map[models.NotificationChannelType]bool)
		for _, delivery := range deliveries {
			channels[delivery.Channel] = true
		}

		assert.True(t, channels[models.NotificationChannelTypeEmail])
		assert.True(t, channels[models.NotificationChannelTypeSlack])
		assert.True(t, channels[models.NotificationChannelTypeSMS])
	})
}

// TestNotificationErrorHandling tests error scenarios
func TestNotificationErrorHandling(t *testing.T) {
	ts := setupTestService(t)

	t.Run("InvalidRecipientID", func(t *testing.T) {
		requestBody := map[string]interface{}{
			"title":        "Test Notification",
			"message":      "This should fail",
			"type":         "system",
			"channels":     []string{"email"},
			"priority":     "normal",
			"recipient_id": 99999, // Non-existent user
		}

		jsonBody, _ := json.Marshal(requestBody)
		req := httptest.NewRequest("POST", "/api/notifications/send", bytes.NewBuffer(jsonBody))
		req.Header.Set("Content-Type", "application/json")

		w := httptest.NewRecorder()
		ts.router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
	})

	t.Run("InvalidNotificationType", func(t *testing.T) {
		user := ts.createTestUser(t)

		requestBody := map[string]interface{}{
			"title":        "Test Notification",
			"message":      "This should fail",
			"type":         "invalid_type",
			"channels":     []string{"email"},
			"priority":     "normal",
			"recipient_id": user.ID,
		}

		jsonBody, _ := json.Marshal(requestBody)
		req := httptest.NewRequest("POST", "/api/notifications/send", bytes.NewBuffer(jsonBody))
		req.Header.Set("Content-Type", "application/json")

		w := httptest.NewRecorder()
		ts.router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
	})

	t.Run("EmptyChannels", func(t *testing.T) {
		user := ts.createTestUser(t)

		requestBody := map[string]interface{}{
			"title":        "Test Notification",
			"message":      "This should fail",
			"type":         "system",
			"channels":     []string{},
			"priority":     "normal",
			"recipient_id": user.ID,
		}

		jsonBody, _ := json.Marshal(requestBody)
		req := httptest.NewRequest("POST", "/api/notifications/send", bytes.NewBuffer(jsonBody))
		req.Header.Set("Content-Type", "application/json")

		w := httptest.NewRecorder()
		ts.router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
	})
}

// TestNotificationPerformance tests performance aspects
func TestNotificationPerformance(t *testing.T) {
	ts := setupTestService(t)

	t.Run("BulkNotificationCreation", func(t *testing.T) {
		user := ts.createTestUser(t)

		start := time.Now()

		// Create 100 notifications
		for i := 0; i < 100; i++ {
			notification := &models.NotificationEnhanced{
				Title:       fmt.Sprintf("Bulk Test %d", i),
				Message:     fmt.Sprintf("This is bulk test notification %d", i),
				Type:        models.NotificationTypeSystem,
				Channels:    []byte(`["email"]`),
				Priority:    models.NotificationPriorityNormal,
				Status:      models.NotificationStatusPending,
				RecipientID: user.ID,
			}
			err := ts.repo.CreateNotification(notification)
			require.NoError(t, err)
		}

		duration := time.Since(start)
		assert.Less(t, duration, 5*time.Second, "Bulk creation should complete within 5 seconds")

		// Verify all notifications were created
		filters := map[string]interface{}{
			"recipient_id": user.ID,
		}
		notifications, total, err := ts.repo.GetNotifications(filters, 1, 200)
		assert.NoError(t, err)
		assert.Equal(t, int64(100), total)
		assert.Len(t, notifications, 100)
	})

	t.Run("ConcurrentNotificationAccess", func(t *testing.T) {
		user := ts.createTestUser(t)

		// Create notifications concurrently
		const numGoroutines = 10
		const notificationsPerGoroutine = 10

		done := make(chan bool, numGoroutines)

		for i := 0; i < numGoroutines; i++ {
			go func(goroutineID int) {
				for j := 0; j < notificationsPerGoroutine; j++ {
					notification := &models.NotificationEnhanced{
						Title:       fmt.Sprintf("Concurrent Test %d-%d", goroutineID, j),
						Message:     fmt.Sprintf("This is concurrent test notification %d-%d", goroutineID, j),
						Type:        models.NotificationTypeSystem,
						Channels:    []byte(`["email"]`),
						Priority:    models.NotificationPriorityNormal,
						Status:      models.NotificationStatusPending,
						RecipientID: user.ID,
					}
					err := ts.repo.CreateNotification(notification)
					assert.NoError(t, err)
				}
				done <- true
			}(i)
		}

		// Wait for all goroutines to complete
		for i := 0; i < numGoroutines; i++ {
			<-done
		}

		// Verify all notifications were created
		filters := map[string]interface{}{
			"recipient_id": user.ID,
		}
		notifications, total, err := ts.repo.GetNotifications(filters, 1, 200)
		assert.NoError(t, err)
		assert.Equal(t, int64(numGoroutines*notificationsPerGoroutine), total)
		assert.Len(t, notifications, numGoroutines*notificationsPerGoroutine)
	})
}

// Benchmark tests for performance measurement
func BenchmarkNotificationCreation(b *testing.B) {
	ts := setupTestService(&testing.T{})
	user := ts.createTestUser(&testing.T{})

	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		notification := &models.NotificationEnhanced{
			Title:       fmt.Sprintf("Benchmark Test %d", i),
			Message:     fmt.Sprintf("This is benchmark test notification %d", i),
			Type:        models.NotificationTypeSystem,
			Channels:    []byte(`["email"]`),
			Priority:    models.NotificationPriorityNormal,
			Status:      models.NotificationStatusPending,
			RecipientID: user.ID,
		}
		err := ts.repo.CreateNotification(notification)
		if err != nil {
			b.Fatal(err)
		}
	}
}

func BenchmarkNotificationRetrieval(b *testing.B) {
	ts := setupTestService(&testing.T{})
	user := ts.createTestUser(&testing.T{})

	// Create test notifications
	for i := 0; i < 100; i++ {
		notification := &models.NotificationEnhanced{
			Title:       fmt.Sprintf("Benchmark Test %d", i),
			Message:     fmt.Sprintf("This is benchmark test notification %d", i),
			Type:        models.NotificationTypeSystem,
			Channels:    []byte(`["email"]`),
			Priority:    models.NotificationPriorityNormal,
			Status:      models.NotificationStatusPending,
			RecipientID: user.ID,
		}
		err := ts.repo.CreateNotification(notification)
		if err != nil {
			b.Fatal(err)
		}
	}

	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		filters := map[string]interface{}{
			"recipient_id": user.ID,
		}
		_, _, err := ts.repo.GetNotifications(filters, 1, 50)
		if err != nil {
			b.Fatal(err)
		}
	}
}
