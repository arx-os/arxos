package notifications

import "errors"

var (
	// ErrNotificationNotFound is returned when a notification is not found
	ErrNotificationNotFound = errors.New("notification not found")

	// ErrInvalidNotification is returned when a notification is invalid
	ErrInvalidNotification = errors.New("invalid notification")

	// ErrNotificationAlreadyExists is returned when trying to create a duplicate notification
	ErrNotificationAlreadyExists = errors.New("notification already exists")
)
