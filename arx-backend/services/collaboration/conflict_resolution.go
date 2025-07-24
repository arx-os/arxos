package collaboration

import (
	"crypto/sha256"
	"fmt"
	"sort"
	"sync"
	"time"
)

// OperationType represents the type of operation
type OperationType string

const (
	InsertOperation OperationType = "insert"
	DeleteOperation OperationType = "delete"
	UpdateOperation OperationType = "update"
	MoveOperation   OperationType = "move"
)

// Operation represents a collaborative operation
type Operation struct {
	ID        string                 `json:"id"`
	Type      OperationType          `json:"type"`
	Position  int                    `json:"position"`
	Length    int                    `json:"length"`
	Content   string                 `json:"content,omitempty"`
	UserID    string                 `json:"user_id"`
	Timestamp time.Time              `json:"timestamp"`
	Vector    map[string]int         `json:"vector"`
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
}

// Document represents a collaborative document
type Document struct {
	ID        string               `json:"id"`
	Content   string               `json:"content"`
	Version   int                  `json:"version"`
	Vector    map[string]int       `json:"vector"`
	History   []Operation          `json:"history"`
	Users     map[string]UserState `json:"users"`
	CreatedAt time.Time            `json:"created_at"`
	UpdatedAt time.Time            `json:"updated_at"`
	mu        sync.RWMutex         `json:"-"`
}

// UserState represents the state of a user in the document
type UserState struct {
	UserID    string    `json:"user_id"`
	Username  string    `json:"username"`
	Cursor    int       `json:"cursor"`
	Selection []int     `json:"selection"`
	LastSeen  time.Time `json:"last_seen"`
	Color     string    `json:"color"`
}

// ConflictResolutionService handles operational transformation and conflict resolution
type ConflictResolutionService struct {
	documents map[string]*Document
	mu        sync.RWMutex
}

// NewConflictResolutionService creates a new conflict resolution service
func NewConflictResolutionService() *ConflictResolutionService {
	return &ConflictResolutionService{
		documents: make(map[string]*Document),
	}
}

// CreateDocument creates a new collaborative document
func (crs *ConflictResolutionService) CreateDocument(id, initialContent string, creatorID string) *Document {
	doc := &Document{
		ID:      id,
		Content: initialContent,
		Version: 0,
		Vector: map[string]int{
			creatorID: 0,
		},
		History:   []Operation{},
		Users:     make(map[string]UserState),
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	crs.mu.Lock()
	crs.documents[id] = doc
	crs.mu.Unlock()

	return doc
}

// GetDocument retrieves a document by ID
func (crs *ConflictResolutionService) GetDocument(id string) (*Document, error) {
	crs.mu.RLock()
	defer crs.mu.RUnlock()

	doc, exists := crs.documents[id]
	if !exists {
		return nil, fmt.Errorf("document not found: %s", id)
	}

	return doc, nil
}

// ApplyOperation applies an operation to a document using operational transformation
func (crs *ConflictResolutionService) ApplyOperation(docID string, op Operation) error {
	doc, err := crs.GetDocument(docID)
	if err != nil {
		return err
	}

	doc.mu.Lock()
	defer doc.mu.Unlock()

	// Transform the operation against concurrent operations
	transformedOp := crs.transformOperation(op, doc.History)

	// Apply the transformed operation
	crs.applyTransformedOperation(doc, transformedOp)

	// Update document metadata
	doc.UpdatedAt = time.Now()
	doc.Version++

	return nil
}

// transformOperation transforms an operation against concurrent operations
func (crs *ConflictResolutionService) transformOperation(op Operation, history []Operation) Operation {
	transformedOp := op

	for _, concurrentOp := range history {
		if crs.isConcurrent(op, concurrentOp) {
			transformedOp = crs.transformOperations(transformedOp, concurrentOp)
		}
	}

	return transformedOp
}

// isConcurrent checks if two operations are concurrent
func (crs *ConflictResolutionService) isConcurrent(op1, op2 Operation) bool {
	// Operations are concurrent if neither happened before the other
	return !crs.happenedBefore(op1, op2) && !crs.happenedBefore(op2, op1)
}

// happenedBefore checks if op1 happened before op2
func (crs *ConflictResolutionService) happenedBefore(op1, op2 Operation) bool {
	// Check vector clock
	for userID, count := range op2.Vector {
		if op1.Vector[userID] < count {
			return true
		}
	}
	return false
}

// transformOperations transforms two concurrent operations
func (crs *ConflictResolutionService) transformOperations(op1, op2 Operation) Operation {
	switch op1.Type {
	case InsertOperation:
		return crs.transformInsert(op1, op2)
	case DeleteOperation:
		return crs.transformDelete(op1, op2)
	case UpdateOperation:
		return crs.transformUpdate(op1, op2)
	default:
		return op1
	}
}

// transformInsert transforms an insert operation against another operation
func (crs *ConflictResolutionService) transformInsert(insertOp, otherOp Operation) Operation {
	switch otherOp.Type {
	case InsertOperation:
		// If other insert is before this insert, adjust position
		if otherOp.Position < insertOp.Position {
			insertOp.Position += len(otherOp.Content)
		}
	case DeleteOperation:
		// If delete overlaps with insert, adjust position
		if otherOp.Position < insertOp.Position {
			insertOp.Position -= otherOp.Length
		}
	}
	return insertOp
}

// transformDelete transforms a delete operation against another operation
func (crs *ConflictResolutionService) transformDelete(deleteOp, otherOp Operation) Operation {
	switch otherOp.Type {
	case InsertOperation:
		// If insert is before delete, adjust delete position
		if otherOp.Position < deleteOp.Position {
			deleteOp.Position += len(otherOp.Content)
		}
	case DeleteOperation:
		// Handle overlapping deletes
		if otherOp.Position < deleteOp.Position {
			deleteOp.Position -= otherOp.Length
		}
	}
	return deleteOp
}

// transformUpdate transforms an update operation against another operation
func (crs *ConflictResolutionService) transformUpdate(updateOp, otherOp Operation) Operation {
	// For updates, we typically merge the changes
	// This is a simplified implementation
	return updateOp
}

// applyTransformedOperation applies a transformed operation to the document
func (crs *ConflictResolutionService) applyTransformedOperation(doc *Document, op Operation) {
	switch op.Type {
	case InsertOperation:
		doc.Content = doc.Content[:op.Position] + op.Content + doc.Content[op.Position:]
	case DeleteOperation:
		doc.Content = doc.Content[:op.Position] + doc.Content[op.Position+op.Length:]
	case UpdateOperation:
		// Handle update operation
		if op.Position+op.Length <= len(doc.Content) {
			doc.Content = doc.Content[:op.Position] + op.Content + doc.Content[op.Position+op.Length:]
		}
	}

	// Add to history
	doc.History = append(doc.History, op)

	// Update vector clock
	if doc.Vector[op.UserID] < op.Vector[op.UserID] {
		doc.Vector[op.UserID] = op.Vector[op.UserID]
	}
}

// JoinDocument allows a user to join a collaborative document
func (crs *ConflictResolutionService) JoinDocument(docID, userID, username string) error {
	doc, err := crs.GetDocument(docID)
	if err != nil {
		return err
	}

	doc.mu.Lock()
	defer doc.mu.Unlock()

	// Initialize user state
	doc.Users[userID] = UserState{
		UserID:    userID,
		Username:  username,
		Cursor:    0,
		Selection: []int{},
		LastSeen:  time.Now(),
		Color:     crs.generateUserColor(userID),
	}

	// Initialize vector clock for new user
	if doc.Vector[userID] == 0 {
		doc.Vector[userID] = 0
	}

	return nil
}

// LeaveDocument allows a user to leave a collaborative document
func (crs *ConflictResolutionService) LeaveDocument(docID, userID string) error {
	doc, err := crs.GetDocument(docID)
	if err != nil {
		return err
	}

	doc.mu.Lock()
	defer doc.mu.Unlock()

	delete(doc.Users, userID)
	return nil
}

// UpdateUserState updates the state of a user in the document
func (crs *ConflictResolutionService) UpdateUserState(docID, userID string, cursor int, selection []int) error {
	doc, err := crs.GetDocument(docID)
	if err != nil {
		return err
	}

	doc.mu.Lock()
	defer doc.mu.Unlock()

	if userState, exists := doc.Users[userID]; exists {
		userState.Cursor = cursor
		userState.Selection = selection
		userState.LastSeen = time.Now()
		doc.Users[userID] = userState
	}

	return nil
}

// GetDocumentState returns the current state of a document
func (crs *ConflictResolutionService) GetDocumentState(docID string) (*Document, error) {
	doc, err := crs.GetDocument(docID)
	if err != nil {
		return nil, err
	}

	doc.mu.RLock()
	defer doc.mu.RUnlock()

	// Create a copy to avoid race conditions
	docCopy := *doc
	return &docCopy, nil
}

// GetDocumentHistory returns the operation history of a document
func (crs *ConflictResolutionService) GetDocumentHistory(docID string) ([]Operation, error) {
	doc, err := crs.GetDocument(docID)
	if err != nil {
		return nil, err
	}

	doc.mu.RLock()
	defer doc.mu.RUnlock()

	// Return a copy of the history
	history := make([]Operation, len(doc.History))
	copy(history, doc.History)
	return history, nil
}

// CreateOperation creates a new operation
func (crs *ConflictResolutionService) CreateOperation(opType OperationType, position, length int, content, userID string, vector map[string]int) Operation {
	return Operation{
		ID:        crs.generateOperationID(),
		Type:      opType,
		Position:  position,
		Length:    length,
		Content:   content,
		UserID:    userID,
		Timestamp: time.Now(),
		Vector:    vector,
		Metadata:  make(map[string]interface{}),
	}
}

// generateOperationID generates a unique operation ID
func (crs *ConflictResolutionService) generateOperationID() string {
	return fmt.Sprintf("op_%d_%s", time.Now().UnixNano(), fmt.Sprintf("%x", sha256.Sum256([]byte(time.Now().String())))[:8])
}

// generateUserColor generates a color for a user
func (crs *ConflictResolutionService) generateUserColor(userID string) string {
	colors := []string{
		"#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
		"#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
	}

	hash := 0
	for _, char := range userID {
		hash = (hash*31 + int(char)) % len(colors)
	}

	return colors[hash%len(colors)]
}

// GetActiveUsers returns the list of active users in a document
func (crs *ConflictResolutionService) GetActiveUsers(docID string) ([]UserState, error) {
	doc, err := crs.GetDocument(docID)
	if err != nil {
		return nil, err
	}

	doc.mu.RLock()
	defer doc.mu.RUnlock()

	// Filter active users (seen in last 30 seconds)
	activeUsers := []UserState{}
	cutoff := time.Now().Add(-30 * time.Second)

	for _, userState := range doc.Users {
		if userState.LastSeen.After(cutoff) {
			activeUsers = append(activeUsers, userState)
		}
	}

	// Sort by username
	sort.Slice(activeUsers, func(i, j int) bool {
		return activeUsers[i].Username < activeUsers[j].Username
	})

	return activeUsers, nil
}

// GetDocumentStatistics returns statistics about a document
func (crs *ConflictResolutionService) GetDocumentStatistics(docID string) (map[string]interface{}, error) {
	doc, err := crs.GetDocument(docID)
	if err != nil {
		return nil, err
	}

	doc.mu.RLock()
	defer doc.mu.RUnlock()

	// Count operations by type
	opCounts := make(map[string]int)
	for _, op := range doc.History {
		opCounts[string(op.Type)]++
	}

	// Count active users
	activeUsers := 0
	cutoff := time.Now().Add(-30 * time.Second)
	for _, userState := range doc.Users {
		if userState.LastSeen.After(cutoff) {
			activeUsers++
		}
	}

	return map[string]interface{}{
		"document_id":      doc.ID,
		"content_length":   len(doc.Content),
		"version":          doc.Version,
		"total_operations": len(doc.History),
		"operation_counts": opCounts,
		"active_users":     activeUsers,
		"total_users":      len(doc.Users),
		"created_at":       doc.CreatedAt,
		"updated_at":       doc.UpdatedAt,
	}, nil
}

// ExportDocument exports a document with its history
func (crs *ConflictResolutionService) ExportDocument(docID string) (map[string]interface{}, error) {
	doc, err := crs.GetDocument(docID)
	if err != nil {
		return nil, err
	}

	doc.mu.RLock()
	defer doc.mu.RUnlock()

	return map[string]interface{}{
		"document": doc,
		"history":  doc.History,
		"users":    doc.Users,
	}, nil
}

// ImportDocument imports a document with its history
func (crs *ConflictResolutionService) ImportDocument(data map[string]interface{}) error {
	// This would implement document import functionality
	// For now, return a placeholder
	return fmt.Errorf("document import not implemented")
}
