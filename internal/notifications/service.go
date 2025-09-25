package notifications

import (
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// Notification represents a system notification
type Notification struct {
	ID          string                 `json:"id"`
	Type        string                 `json:"type"` // info, warning, error, success
	Title       string                 `json:"title"`
	Message     string                 `json:"message"`
	Severity    string                 `json:"severity"` // low, medium, high, critical
	Timestamp   time.Time              `json:"timestamp"`
	Read        bool                   `json:"read"`
	UserID      string                 `json:"user_id,omitempty"`      // For user-specific notifications
	BuildingID  string                 `json:"building_id,omitempty"`  // For building-specific notifications
	EquipmentID string                 `json:"equipment_id,omitempty"` // For equipment-specific notifications
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
	Actions     []NotificationAction   `json:"actions,omitempty"`
}

// NotificationAction represents an action that can be taken on a notification
type NotificationAction struct {
	ID    string `json:"id"`
	Label string `json:"label"`
	URL   string `json:"url,omitempty"`
	Type  string `json:"type"` // link, button, dismiss
}

// NotificationService manages notifications
type NotificationService struct {
	notifications     map[string]*Notification
	userNotifications map[string][]string // userID -> notificationIDs
	mu                sync.RWMutex
	subscribers       []NotificationSubscriber
}

// NotificationSubscriber is an interface for notification subscribers
type NotificationSubscriber interface {
	OnNotificationAdded(notification *Notification)
	OnNotificationUpdated(notification *Notification)
	OnNotificationDeleted(notificationID string)
}

// NewNotificationService creates a new notification service
func NewNotificationService() *NotificationService {
	return &NotificationService{
		notifications:     make(map[string]*Notification),
		userNotifications: make(map[string][]string),
		subscribers:       make([]NotificationSubscriber, 0),
	}
}

// AddNotification adds a new notification
func (s *NotificationService) AddNotification(notification *Notification) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	// Generate ID if not provided
	if notification.ID == "" {
		notification.ID = generateNotificationID()
	}

	// Set timestamp if not provided
	if notification.Timestamp.IsZero() {
		notification.Timestamp = time.Now()
	}

	// Store notification
	s.notifications[notification.ID] = notification

	// Add to user notifications if user-specific
	if notification.UserID != "" {
		s.userNotifications[notification.UserID] = append(s.userNotifications[notification.UserID], notification.ID)
	}

	// Notify subscribers
	for _, subscriber := range s.subscribers {
		go subscriber.OnNotificationAdded(notification)
	}

	logger.Info("Added notification: %s (%s)", notification.Title, notification.Type)
	return nil
}

// GetNotification retrieves a notification by ID
func (s *NotificationService) GetNotification(id string) (*Notification, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	notification, exists := s.notifications[id]
	if !exists {
		return nil, ErrNotificationNotFound
	}

	return notification, nil
}

// GetUserNotifications retrieves notifications for a specific user
func (s *NotificationService) GetUserNotifications(userID string, limit int) ([]*Notification, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	notificationIDs, exists := s.userNotifications[userID]
	if !exists {
		return []*Notification{}, nil
	}

	var notifications []*Notification
	count := 0
	for i := len(notificationIDs) - 1; i >= 0 && count < limit; i-- {
		notificationID := notificationIDs[i]
		if notification, exists := s.notifications[notificationID]; exists {
			notifications = append(notifications, notification)
			count++
		}
	}

	return notifications, nil
}

// GetAllNotifications retrieves all notifications (for admin)
func (s *NotificationService) GetAllNotifications(limit int) ([]*Notification, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	var notifications []*Notification
	count := 0
	for _, notification := range s.notifications {
		if count >= limit {
			break
		}
		notifications = append(notifications, notification)
		count++
	}

	return notifications, nil
}

// MarkAsRead marks a notification as read
func (s *NotificationService) MarkAsRead(id string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	notification, exists := s.notifications[id]
	if !exists {
		return ErrNotificationNotFound
	}

	notification.Read = true

	// Notify subscribers
	for _, subscriber := range s.subscribers {
		go subscriber.OnNotificationUpdated(notification)
	}

	return nil
}

// MarkAllAsRead marks all notifications for a user as read
func (s *NotificationService) MarkAllAsRead(userID string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	notificationIDs, exists := s.userNotifications[userID]
	if !exists {
		return nil
	}

	for _, notificationID := range notificationIDs {
		if notification, exists := s.notifications[notificationID]; exists {
			notification.Read = true
			// Notify subscribers
			for _, subscriber := range s.subscribers {
				go subscriber.OnNotificationUpdated(notification)
			}
		}
	}

	return nil
}

// DeleteNotification deletes a notification
func (s *NotificationService) DeleteNotification(id string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	notification, exists := s.notifications[id]
	if !exists {
		return ErrNotificationNotFound
	}

	// Remove from user notifications
	if notification.UserID != "" {
		userNotifications := s.userNotifications[notification.UserID]
		for i, notificationID := range userNotifications {
			if notificationID == id {
				s.userNotifications[notification.UserID] = append(userNotifications[:i], userNotifications[i+1:]...)
				break
			}
		}
	}

	// Remove notification
	delete(s.notifications, id)

	// Notify subscribers
	for _, subscriber := range s.subscribers {
		go subscriber.OnNotificationDeleted(id)
	}

	return nil
}

// Subscribe adds a notification subscriber
func (s *NotificationService) Subscribe(subscriber NotificationSubscriber) {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.subscribers = append(s.subscribers, subscriber)
}

// CreateSystemNotification creates a system-wide notification
func (s *NotificationService) CreateSystemNotification(notificationType, title, message, severity string) error {
	notification := &Notification{
		Type:     notificationType,
		Title:    title,
		Message:  message,
		Severity: severity,
	}

	return s.AddNotification(notification)
}

// CreateUserNotification creates a user-specific notification
func (s *NotificationService) CreateUserNotification(userID, notificationType, title, message, severity string) error {
	notification := &Notification{
		Type:     notificationType,
		Title:    title,
		Message:  message,
		Severity: severity,
		UserID:   userID,
	}

	return s.AddNotification(notification)
}

// CreateBuildingNotification creates a building-specific notification
func (s *NotificationService) CreateBuildingNotification(buildingID, notificationType, title, message, severity string) error {
	notification := &Notification{
		Type:       notificationType,
		Title:      title,
		Message:    message,
		Severity:   severity,
		BuildingID: buildingID,
	}

	return s.AddNotification(notification)
}

// CreateEquipmentNotification creates an equipment-specific notification
func (s *NotificationService) CreateEquipmentNotification(equipmentID, notificationType, title, message, severity string) error {
	notification := &Notification{
		Type:        notificationType,
		Title:       title,
		Message:     message,
		Severity:    severity,
		EquipmentID: equipmentID,
	}

	return s.AddNotification(notification)
}

// GetUnreadCount returns the count of unread notifications for a user
func (s *NotificationService) GetUnreadCount(userID string) (int, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	notificationIDs, exists := s.userNotifications[userID]
	if !exists {
		return 0, nil
	}

	count := 0
	for _, notificationID := range notificationIDs {
		if notification, exists := s.notifications[notificationID]; exists && !notification.Read {
			count++
		}
	}

	return count, nil
}

// generateNotificationID generates a unique notification ID
func generateNotificationID() string {
	return time.Now().Format("20060102150405") + "-" + randomString(8)
}

// randomString generates a random string of specified length
func randomString(length int) string {
	const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	b := make([]byte, length)
	for i := range b {
		b[i] = charset[time.Now().UnixNano()%int64(len(charset))]
	}
	return string(b)
}
