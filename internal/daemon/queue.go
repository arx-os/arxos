package daemon

import (
	"fmt"
	"sync"
	"time"
)

// WorkType represents the type of work to be done
type WorkType string

const (
	WorkTypeImport WorkType = "import"
	WorkTypeUpdate WorkType = "update"
	WorkTypeRemove WorkType = "remove"
	WorkTypeSync   WorkType = "sync"
)

// WorkItem represents a unit of work
type WorkItem struct {
	ID        string
	Type      WorkType
	FilePath  string
	Timestamp time.Time
	Retries   int
	Error     error
}

// WorkQueue manages work items
type WorkQueue struct {
	items    chan *WorkItem
	size     int
	closed   bool
	mu       sync.RWMutex
	pending  map[string]*WorkItem // Deduplication
}

// NewWorkQueue creates a new work queue
func NewWorkQueue(size int) *WorkQueue {
	return &WorkQueue{
		items:   make(chan *WorkItem, size),
		size:    size,
		pending: make(map[string]*WorkItem),
	}
}

// Add adds a work item to the queue
func (q *WorkQueue) Add(item *WorkItem) error {
	q.mu.Lock()
	defer q.mu.Unlock()
	
	if q.closed {
		return fmt.Errorf("queue is closed")
	}
	
	// Generate ID if not set
	if item.ID == "" {
		item.ID = fmt.Sprintf("%s-%s-%d", item.Type, item.FilePath, time.Now().UnixNano())
	}
	
	// Check for duplicate
	if existing, exists := q.pending[item.FilePath]; exists {
		// Update existing item if newer
		if item.Timestamp.After(existing.Timestamp) {
			existing.Timestamp = item.Timestamp
			existing.Type = item.Type
		}
		return nil // Don't add duplicate
	}
	
	// Try to add to queue
	select {
	case q.items <- item:
		q.pending[item.FilePath] = item
		return nil
	default:
		return fmt.Errorf("queue is full")
	}
}

// Items returns the items channel for reading
func (q *WorkQueue) Items() <-chan *WorkItem {
	return q.items
}

// Size returns the current queue size
func (q *WorkQueue) Size() int {
	q.mu.RLock()
	defer q.mu.RUnlock()
	return len(q.items)
}

// Close closes the queue
func (q *WorkQueue) Close() {
	q.mu.Lock()
	defer q.mu.Unlock()
	
	if !q.closed {
		q.closed = true
		close(q.items)
	}
}

// Remove removes an item from pending
func (q *WorkQueue) Remove(filePath string) {
	q.mu.Lock()
	defer q.mu.Unlock()
	delete(q.pending, filePath)
}

// IsClosed returns whether the queue is closed
func (q *WorkQueue) IsClosed() bool {
	q.mu.RLock()
	defer q.mu.RUnlock()
	return q.closed
}