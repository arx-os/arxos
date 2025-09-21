package web

import (
	"fmt"
	"sync"
	"time"
)

// MemorySessionStore implements in-memory session storage
type MemorySessionStore struct {
	sessions map[string]*Session
	mu       sync.RWMutex
	ticker   *time.Ticker
	done     chan bool
}

// NewMemorySessionStore creates a new in-memory session store
func NewMemorySessionStore(cleanupInterval time.Duration) *MemorySessionStore {
	store := &MemorySessionStore{
		sessions: make(map[string]*Session),
		ticker:   time.NewTicker(cleanupInterval),
		done:     make(chan bool),
	}

	// Start cleanup goroutine
	go store.cleanup()

	return store
}

// Get retrieves a session by ID
func (m *MemorySessionStore) Get(sessionID string) (*Session, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	session, exists := m.sessions[sessionID]
	if !exists {
		return nil, fmt.Errorf("session not found")
	}

	// Check expiration
	if time.Now().After(session.ExpiresAt) {
		return nil, fmt.Errorf("session expired")
	}

	return session, nil
}

// Set stores a session
func (m *MemorySessionStore) Set(sessionID string, session *Session) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.sessions[sessionID] = session
	return nil
}

// Delete removes a session
func (m *MemorySessionStore) Delete(sessionID string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	delete(m.sessions, sessionID)
	return nil
}

// cleanup periodically removes expired sessions
func (m *MemorySessionStore) cleanup() {
	for {
		select {
		case <-m.ticker.C:
			m.removeExpired()
		case <-m.done:
			return
		}
	}
}

// removeExpired removes all expired sessions
func (m *MemorySessionStore) removeExpired() {
	m.mu.Lock()
	defer m.mu.Unlock()

	now := time.Now()
	for id, session := range m.sessions {
		if now.After(session.ExpiresAt) {
			delete(m.sessions, id)
		}
	}
}

// Close stops the cleanup goroutine
func (m *MemorySessionStore) Close() {
	m.ticker.Stop()
	m.done <- true
}

// Count returns the number of active sessions
func (m *MemorySessionStore) Count() int {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return len(m.sessions)
}

// Clear removes all sessions
func (m *MemorySessionStore) Clear() {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.sessions = make(map[string]*Session)
}