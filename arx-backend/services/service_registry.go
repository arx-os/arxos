package services

import (
	"arx/services/notifications"
	"sync"

	"github.com/go-redis/redis/v8"
	"gorm.io/gorm"
)

// ServiceRegistry manages all application services
type ServiceRegistry struct {
	db           *gorm.DB
	redis        *redis.Client
	emailService *notifications.EmailService
	mu           sync.RWMutex
	initialized  bool
}

var (
	registry *ServiceRegistry
	once     sync.Once
)

// GetServiceRegistry returns the singleton service registry
func GetServiceRegistry() *ServiceRegistry {
	once.Do(func() {
		registry = &ServiceRegistry{}
	})
	return registry
}

// Initialize sets up all services with their dependencies
func (sr *ServiceRegistry) Initialize(db *gorm.DB, redis *redis.Client) error {
	sr.mu.Lock()
	defer sr.mu.Unlock()

	if sr.initialized {
		return nil
	}

	sr.db = db
	sr.redis = redis

	// Initialize email service
	sr.emailService = notifications.NewEmailService(db, redis)

	sr.initialized = true
	return nil
}

// GetEmailService returns the email notification service
func (sr *ServiceRegistry) GetEmailService() *notifications.EmailService {
	sr.mu.RLock()
	defer sr.mu.RUnlock()

	if !sr.initialized {
		panic("ServiceRegistry not initialized")
	}

	return sr.emailService
}

// GetDB returns the database connection
func (sr *ServiceRegistry) GetDB() *gorm.DB {
	sr.mu.RLock()
	defer sr.mu.RUnlock()

	if !sr.initialized {
		panic("ServiceRegistry not initialized")
	}

	return sr.db
}

// GetRedis returns the Redis client
func (sr *ServiceRegistry) GetRedis() *redis.Client {
	sr.mu.RLock()
	defer sr.mu.RUnlock()

	if !sr.initialized {
		panic("ServiceRegistry not initialized")
	}

	return sr.redis
}

// Shutdown gracefully shuts down all services
func (sr *ServiceRegistry) Shutdown() error {
	sr.mu.Lock()
	defer sr.mu.Unlock()

	if !sr.initialized {
		return nil
	}

	// Close Redis connection
	if sr.redis != nil {
		if err := sr.redis.Close(); err != nil {
			return err
		}
	}

	sr.initialized = false
	return nil
}
