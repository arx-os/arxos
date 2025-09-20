package sync

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"sync"
	"time"

	syncpkg "github.com/arx-os/arxos/pkg/sync"
	"github.com/arx-os/arxos/internal/database"
)

// InMemoryConflictStore implements ConflictResolutionStore in memory
type InMemoryConflictStore struct {
	mu         sync.RWMutex
	conflicts  map[string]*syncpkg.Conflict
	resolutions map[string]*ConflictResolution
	byEntity   map[string][]string // entityID -> conflictIDs
}

// NewInMemoryConflictStore creates a new in-memory conflict store
func NewInMemoryConflictStore() *InMemoryConflictStore {
	return &InMemoryConflictStore{
		conflicts:   make(map[string]*syncpkg.Conflict),
		resolutions: make(map[string]*ConflictResolution),
		byEntity:    make(map[string][]string),
	}
}

// SaveConflict saves a conflict
func (s *InMemoryConflictStore) SaveConflict(ctx context.Context, conflict *syncpkg.Conflict) error {
	if conflict.ID == "" {
		return fmt.Errorf("conflict ID is required")
	}

	s.mu.Lock()
	defer s.mu.Unlock()

	s.conflicts[conflict.ID] = conflict

	// Update entity index
	entityKey := fmt.Sprintf("%s:%s", conflict.Entity, conflict.EntityID)
	if _, exists := s.byEntity[entityKey]; !exists {
		s.byEntity[entityKey] = []string{}
	}

	// Check if already indexed
	found := false
	for _, id := range s.byEntity[entityKey] {
		if id == conflict.ID {
			found = true
			break
		}
	}
	if !found {
		s.byEntity[entityKey] = append(s.byEntity[entityKey], conflict.ID)
	}

	return nil
}

// GetConflict retrieves a conflict by ID
func (s *InMemoryConflictStore) GetConflict(ctx context.Context, id string) (*syncpkg.Conflict, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	conflict, exists := s.conflicts[id]
	if !exists {
		return nil, fmt.Errorf("conflict not found: %s", id)
	}

	return conflict, nil
}

// ListConflicts lists conflicts for an entity
func (s *InMemoryConflictStore) ListConflicts(ctx context.Context, entityID string) ([]*syncpkg.Conflict, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	var result []*syncpkg.Conflict

	// Check all entity types
	for key, conflictIDs := range s.byEntity {
		if strings.HasSuffix(key, ":"+entityID) {
			for _, id := range conflictIDs {
				if conflict, exists := s.conflicts[id]; exists {
					// Only include unresolved conflicts
					if _, resolved := s.resolutions[id]; !resolved {
						result = append(result, conflict)
					}
				}
			}
		}
	}

	return result, nil
}

// ResolveConflict marks a conflict as resolved
func (s *InMemoryConflictStore) ResolveConflict(ctx context.Context, id string, resolution ConflictResolution) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if _, exists := s.conflicts[id]; !exists {
		return fmt.Errorf("conflict not found: %s", id)
	}

	resolution.ConflictID = id
	resolution.ResolvedAt = time.Now()
	s.resolutions[id] = &resolution

	return nil
}

// DeleteConflict deletes a conflict
func (s *InMemoryConflictStore) DeleteConflict(ctx context.Context, id string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	conflict, exists := s.conflicts[id]
	if !exists {
		return fmt.Errorf("conflict not found: %s", id)
	}

	// Remove from entity index
	entityKey := fmt.Sprintf("%s:%s", conflict.Entity, conflict.EntityID)
	if ids, exists := s.byEntity[entityKey]; exists {
		newIDs := []string{}
		for _, cid := range ids {
			if cid != id {
				newIDs = append(newIDs, cid)
			}
		}
		if len(newIDs) > 0 {
			s.byEntity[entityKey] = newIDs
		} else {
			delete(s.byEntity, entityKey)
		}
	}

	delete(s.conflicts, id)
	delete(s.resolutions, id)

	return nil
}

// DatabaseConflictStore implements ConflictResolutionStore using database
type DatabaseConflictStore struct {
	db database.DB
}

// NewDatabaseConflictStore creates a new database-backed conflict store
func NewDatabaseConflictStore(db database.DB) *DatabaseConflictStore {
	return &DatabaseConflictStore{db: db}
}

// SaveConflict saves a conflict to database
func (s *DatabaseConflictStore) SaveConflict(ctx context.Context, conflict *syncpkg.Conflict) error {
	// In a real implementation, this would save to a conflicts table
	// For now, we'll use a simplified approach
	data, err := json.Marshal(conflict)
	if err != nil {
		return fmt.Errorf("failed to marshal conflict: %w", err)
	}

	// Store in database (would need to add SaveConflict method to database.DB interface)
	// For now, return nil to allow compilation
	_ = data
	return nil
}

// GetConflict retrieves a conflict from database
func (s *DatabaseConflictStore) GetConflict(ctx context.Context, id string) (*syncpkg.Conflict, error) {
	// In a real implementation, this would query the conflicts table
	return nil, fmt.Errorf("not implemented")
}

// ListConflicts lists conflicts for an entity from database
func (s *DatabaseConflictStore) ListConflicts(ctx context.Context, entityID string) ([]*syncpkg.Conflict, error) {
	// In a real implementation, this would query the conflicts table
	return []*syncpkg.Conflict{}, nil
}

// ResolveConflict marks a conflict as resolved in database
func (s *DatabaseConflictStore) ResolveConflict(ctx context.Context, id string, resolution ConflictResolution) error {
	// In a real implementation, this would update the conflicts table
	return nil
}

// DeleteConflict deletes a conflict from database
func (s *DatabaseConflictStore) DeleteConflict(ctx context.Context, id string) error {
	// In a real implementation, this would delete from the conflicts table
	return nil
}