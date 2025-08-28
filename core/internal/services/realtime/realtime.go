// Package realtime provides real-time updates for ArxOS building data
package realtime

import (
	"encoding/json"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/arxos/arxos/core/internal/arxobject"
)

// UpdateEngine manages real-time updates for building data
type UpdateEngine struct {
	mu            sync.RWMutex
	subscribers   map[string][]Subscriber
	updateQueue   chan Update
	eventLog      []Update
	maxEventLog   int
	updateInterval time.Duration
	running       bool
	stopCh        chan struct{}
}

// Subscriber represents a client subscribing to updates
type Subscriber struct {
	ID       string
	Channel  chan Update
	Filters  SubscriptionFilter
	Created  time.Time
}

// SubscriptionFilter defines what updates a subscriber receives
type SubscriptionFilter struct {
	BuildingID   string   `json:"building_id,omitempty"`
	FloorID      string   `json:"floor_id,omitempty"`
	SystemTypes  []string `json:"system_types,omitempty"`
	ObjectTypes  []string `json:"object_types,omitempty"`
	UpdateTypes  []string `json:"update_types,omitempty"`
	MinPriority  Priority `json:"min_priority,omitempty"`
}

// Update represents a real-time update to building data
type Update struct {
	ID           string                 `json:"id"`
	Timestamp    time.Time             `json:"timestamp"`
	Type         UpdateType            `json:"type"`
	Priority     Priority              `json:"priority"`
	BuildingID   string                `json:"building_id"`
	FloorID      string                `json:"floor_id,omitempty"`
	ObjectID     uint32                `json:"object_id,omitempty"`
	ObjectPath   string                `json:"object_path,omitempty"`
	SystemType   string                `json:"system_type,omitempty"`
	OldValue     interface{}           `json:"old_value,omitempty"`
	NewValue     interface{}           `json:"new_value,omitempty"`
	Description  string                `json:"description"`
	Source       string                `json:"source"`
	Metadata     map[string]interface{} `json:"metadata,omitempty"`
}

// UpdateType defines types of updates
type UpdateType string

const (
	// Object updates
	UpdateObjectCreated   UpdateType = "object_created"
	UpdateObjectModified  UpdateType = "object_modified"
	UpdateObjectDeleted   UpdateType = "object_deleted"
	UpdateObjectMoved     UpdateType = "object_moved"
	
	// System updates
	UpdateSystemStatus    UpdateType = "system_status"
	UpdateSystemAlert     UpdateType = "system_alert"
	UpdateSystemMetric    UpdateType = "system_metric"
	
	// Sensor updates
	UpdateSensorReading   UpdateType = "sensor_reading"
	UpdateSensorStatus    UpdateType = "sensor_status"
	
	// Control updates
	UpdateControlCommand  UpdateType = "control_command"
	UpdateControlResponse UpdateType = "control_response"
	
	// Building updates
	UpdateFloorChanged    UpdateType = "floor_changed"
	UpdateZoneChanged     UpdateType = "zone_changed"
	UpdateOccupancy       UpdateType = "occupancy"
	
	// Emergency updates
	UpdateEmergencyAlert  UpdateType = "emergency_alert"
	UpdateEvacuation      UpdateType = "evacuation"
	UpdateSafetySystem    UpdateType = "safety_system"
)

// Priority levels for updates
type Priority int

const (
	PriorityLow       Priority = 0
	PriorityNormal    Priority = 1
	PriorityHigh      Priority = 2
	PriorityCritical  Priority = 3
	PriorityEmergency Priority = 4
)

// NewUpdateEngine creates a new real-time update engine
func NewUpdateEngine() *UpdateEngine {
	return &UpdateEngine{
		subscribers:    make(map[string][]Subscriber),
		updateQueue:    make(chan Update, 1000),
		eventLog:       make([]Update, 0, 10000),
		maxEventLog:    10000,
		updateInterval: 100 * time.Millisecond, // 10 Hz update rate
		stopCh:         make(chan struct{}),
	}
}

// Start begins processing real-time updates
func (e *UpdateEngine) Start() error {
	e.mu.Lock()
	if e.running {
		e.mu.Unlock()
		return fmt.Errorf("update engine already running")
	}
	e.running = true
	e.mu.Unlock()
	
	// Start update processor
	go e.processUpdates()
	
	// Start simulation for demo
	go e.simulateUpdates()
	
	log.Println("[UpdateEngine] Started real-time update processing")
	return nil
}

// Stop stops the update engine
func (e *UpdateEngine) Stop() {
	e.mu.Lock()
	if !e.running {
		e.mu.Unlock()
		return
	}
	e.running = false
	e.mu.Unlock()
	
	close(e.stopCh)
	log.Println("[UpdateEngine] Stopped real-time update processing")
}

// Subscribe creates a new subscription for updates
func (e *UpdateEngine) Subscribe(filter SubscriptionFilter) (*Subscriber, error) {
	e.mu.Lock()
	defer e.mu.Unlock()
	
	subscriber := &Subscriber{
		ID:      generateSubscriberID(),
		Channel: make(chan Update, 100),
		Filters: filter,
		Created: time.Now(),
	}
	
	// Add to appropriate subscription lists
	key := e.getSubscriptionKey(filter)
	e.subscribers[key] = append(e.subscribers[key], *subscriber)
	
	log.Printf("[UpdateEngine] New subscriber: %s, filter: %+v", subscriber.ID, filter)
	
	return subscriber, nil
}

// Unsubscribe removes a subscription
func (e *UpdateEngine) Unsubscribe(subscriberID string) error {
	e.mu.Lock()
	defer e.mu.Unlock()
	
	// Find and remove subscriber
	found := false
	for key, subs := range e.subscribers {
		for i, sub := range subs {
			if sub.ID == subscriberID {
				// Close channel
				close(sub.Channel)
				
				// Remove from list
				e.subscribers[key] = append(subs[:i], subs[i+1:]...)
				found = true
				break
			}
		}
		if found {
			break
		}
	}
	
	if !found {
		return fmt.Errorf("subscriber not found: %s", subscriberID)
	}
	
	log.Printf("[UpdateEngine] Unsubscribed: %s", subscriberID)
	return nil
}

// PublishUpdate publishes a new update to subscribers
func (e *UpdateEngine) PublishUpdate(update Update) {
	// Add metadata
	update.ID = generateUpdateID()
	update.Timestamp = time.Now()
	
	// Queue update
	select {
	case e.updateQueue <- update:
		// Successfully queued
	default:
		// Queue full, drop oldest update
		<-e.updateQueue
		e.updateQueue <- update
		log.Println("[UpdateEngine] Update queue full, dropped oldest update")
	}
}

// GetRecentUpdates returns recent updates from the event log
func (e *UpdateEngine) GetRecentUpdates(count int, filter SubscriptionFilter) []Update {
	e.mu.RLock()
	defer e.mu.RUnlock()
	
	if count > len(e.eventLog) {
		count = len(e.eventLog)
	}
	
	// Get recent updates in reverse order
	result := make([]Update, 0, count)
	for i := len(e.eventLog) - 1; i >= 0 && len(result) < count; i-- {
		update := e.eventLog[i]
		if e.matchesFilter(update, filter) {
			result = append(result, update)
		}
	}
	
	return result
}

// processUpdates processes the update queue and distributes to subscribers
func (e *UpdateEngine) processUpdates() {
	ticker := time.NewTicker(e.updateInterval)
	defer ticker.Stop()
	
	batch := make([]Update, 0, 10)
	
	for {
		select {
		case <-e.stopCh:
			return
			
		case update := <-e.updateQueue:
			batch = append(batch, update)
			
			// Process batch if it gets too large
			if len(batch) >= 10 {
				e.distributeBatch(batch)
				batch = batch[:0]
			}
			
		case <-ticker.C:
			// Process any pending updates
			if len(batch) > 0 {
				e.distributeBatch(batch)
				batch = batch[:0]
			}
		}
	}
}

// distributeBatch distributes a batch of updates to subscribers
func (e *UpdateEngine) distributeBatch(updates []Update) {
	e.mu.RLock()
	defer e.mu.RUnlock()
	
	// Add to event log
	for _, update := range updates {
		e.eventLog = append(e.eventLog, update)
		
		// Trim event log if too large
		if len(e.eventLog) > e.maxEventLog {
			e.eventLog = e.eventLog[1:]
		}
	}
	
	// Distribute to subscribers
	for _, subscriberList := range e.subscribers {
		for _, subscriber := range subscriberList {
			for _, update := range updates {
				if e.matchesFilter(update, subscriber.Filters) {
					select {
					case subscriber.Channel <- update:
						// Successfully sent
					default:
						// Subscriber channel full, skip
						log.Printf("[UpdateEngine] Subscriber %s channel full, skipping update", subscriber.ID)
					}
				}
			}
		}
	}
}

// matchesFilter checks if an update matches a subscription filter
func (e *UpdateEngine) matchesFilter(update Update, filter SubscriptionFilter) bool {
	// Check building ID
	if filter.BuildingID != "" && update.BuildingID != filter.BuildingID {
		return false
	}
	
	// Check floor ID
	if filter.FloorID != "" && update.FloorID != filter.FloorID {
		return false
	}
	
	// Check system type
	if len(filter.SystemTypes) > 0 {
		found := false
		for _, st := range filter.SystemTypes {
			if update.SystemType == st {
				found = true
				break
			}
		}
		if !found {
			return false
		}
	}
	
	// Check update type
	if len(filter.UpdateTypes) > 0 {
		found := false
		for _, ut := range filter.UpdateTypes {
			if string(update.Type) == ut {
				found = true
				break
			}
		}
		if !found {
			return false
		}
	}
	
	// Check priority
	if filter.MinPriority > 0 && update.Priority < filter.MinPriority {
		return false
	}
	
	return true
}

// getSubscriptionKey generates a key for subscription grouping
func (e *UpdateEngine) getSubscriptionKey(filter SubscriptionFilter) string {
	// Simple key based on building and floor
	// In production, use more sophisticated routing
	if filter.BuildingID != "" {
		if filter.FloorID != "" {
			return fmt.Sprintf("%s:%s", filter.BuildingID, filter.FloorID)
		}
		return filter.BuildingID
	}
	return "global"
}

// simulateUpdates generates simulated updates for demo
func (e *UpdateEngine) simulateUpdates() {
	ticker := time.NewTicker(2 * time.Second)
	defer ticker.Stop()
	
	sensors := []struct {
		path   string
		system string
		floor  string
	}{
		{"/hvac/thermostats/t-101", "hvac", "1"},
		{"/electrical/panels/main", "electrical", "1"},
		{"/hvac/ahu/ahu-1", "hvac", "2"},
		{"/lighting/zones/zone-a", "lighting", "1"},
		{"/security/doors/main-entrance", "security", "1"},
	}
	
	updateTypes := []UpdateType{
		UpdateSensorReading,
		UpdateSystemStatus,
		UpdateSystemMetric,
	}
	
	for {
		select {
		case <-e.stopCh:
			return
			
		case <-ticker.C:
			// Generate random update
			sensor := sensors[time.Now().Unix()%int64(len(sensors))]
			updateType := updateTypes[time.Now().Unix()%int64(len(updateTypes))]
			
			update := Update{
				Type:       updateType,
				Priority:   PriorityNormal,
				BuildingID: "demo-building",
				FloorID:    sensor.floor,
				ObjectPath: sensor.path,
				SystemType: sensor.system,
				Source:     "simulator",
			}
			
			// Add type-specific data
			switch updateType {
			case UpdateSensorReading:
				update.Description = fmt.Sprintf("Sensor reading from %s", sensor.path)
				update.NewValue = map[string]interface{}{
					"temperature": 20 + float64(time.Now().Unix()%10),
					"humidity":    40 + float64(time.Now().Unix()%20),
				}
				
			case UpdateSystemStatus:
				statuses := []string{"online", "offline", "maintenance", "warning"}
				status := statuses[time.Now().Unix()%int64(len(statuses))]
				update.Description = fmt.Sprintf("System status changed to %s", status)
				update.NewValue = status
				if status == "offline" || status == "warning" {
					update.Priority = PriorityHigh
				}
				
			case UpdateSystemMetric:
				update.Description = "System performance metric"
				update.NewValue = map[string]interface{}{
					"cpu_usage":    10 + float64(time.Now().Unix()%80),
					"memory_usage": 20 + float64(time.Now().Unix()%60),
					"response_ms":  50 + float64(time.Now().Unix()%200),
				}
			}
			
			e.PublishUpdate(update)
		}
	}
}

// StreamingRenderer provides real-time ASCII rendering updates
type StreamingRenderer struct {
	updateEngine   *UpdateEngine
	renderFunc     func(Update) string
	subscriber     *Subscriber
	outputChannel  chan string
}

// NewStreamingRenderer creates a new streaming ASCII renderer
func NewStreamingRenderer(engine *UpdateEngine, filter SubscriptionFilter) (*StreamingRenderer, error) {
	subscriber, err := engine.Subscribe(filter)
	if err != nil {
		return nil, err
	}
	
	return &StreamingRenderer{
		updateEngine:  engine,
		subscriber:    subscriber,
		outputChannel: make(chan string, 100),
		renderFunc:    defaultRenderFunc,
	}, nil
}

// Start begins streaming rendered updates
func (r *StreamingRenderer) Start() {
	go func() {
		for update := range r.subscriber.Channel {
			rendered := r.renderFunc(update)
			select {
			case r.outputChannel <- rendered:
				// Sent successfully
			default:
				// Output channel full, skip
			}
		}
	}()
}

// GetOutput returns the output channel for rendered updates
func (r *StreamingRenderer) GetOutput() <-chan string {
	return r.outputChannel
}

// Stop stops the streaming renderer
func (r *StreamingRenderer) Stop() {
	r.updateEngine.Unsubscribe(r.subscriber.ID)
	close(r.outputChannel)
}

// defaultRenderFunc provides default ASCII rendering of updates
func defaultRenderFunc(update Update) string {
	// Simple ASCII representation of updates
	var icon string
	switch update.Priority {
	case PriorityEmergency:
		icon = "🚨"
	case PriorityCritical:
		icon = "❗"
	case PriorityHigh:
		icon = "⚠️"
	default:
		icon = "ℹ️"
	}
	
	// Format the update for ASCII display
	output := fmt.Sprintf("[%s] %s %s\n", 
		update.Timestamp.Format("15:04:05"),
		icon,
		update.Description,
	)
	
	if update.NewValue != nil {
		if data, ok := update.NewValue.(map[string]interface{}); ok {
			for key, value := range data {
				output += fmt.Sprintf("  %s: %v\n", key, value)
			}
		} else {
			output += fmt.Sprintf("  Value: %v\n", update.NewValue)
		}
	}
	
	return output
}

// Helper functions

func generateSubscriberID() string {
	return fmt.Sprintf("sub_%d", time.Now().UnixNano())
}

func generateUpdateID() string {
	return fmt.Sprintf("update_%d", time.Now().UnixNano())
}

// GetUpdateStats returns statistics about the update engine
func (e *UpdateEngine) GetUpdateStats() map[string]interface{} {
	e.mu.RLock()
	defer e.mu.RUnlock()
	
	subscriberCount := 0
	for _, subs := range e.subscribers {
		subscriberCount += len(subs)
	}
	
	return map[string]interface{}{
		"running":          e.running,
		"subscribers":      subscriberCount,
		"event_log_size":   len(e.eventLog),
		"queue_size":       len(e.updateQueue),
		"update_interval":  e.updateInterval.String(),
	}
}