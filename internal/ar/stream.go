package ar

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/joelpate/arxos/internal/spatial"
)

// UpdateType represents the type of position update
type UpdateType string

const (
	UpdateTypePosition   UpdateType = "position"
	UpdateTypeRotation   UpdateType = "rotation"
	UpdateTypeInteract   UpdateType = "interact"
	UpdateTypeGesture    UpdateType = "gesture"
	UpdateTypeAnchor     UpdateType = "anchor"
	UpdateTypeTracking   UpdateType = "tracking"
)

// PositionUpdate represents a real-time position update from AR device
type PositionUpdate struct {
	ID           string          `json:"id"`
	SessionID    string          `json:"session_id"`
	DeviceID     string          `json:"device_id"`
	Type         UpdateType      `json:"type"`
	ARPosition   ARPoint3D       `json:"ar_position"`
	WorldPosition spatial.Point3D `json:"world_position,omitempty"`
	Rotation     ARRotation      `json:"rotation"`
	Timestamp    time.Time       `json:"timestamp"`
	Sequence     uint64          `json:"sequence"`
	Confidence   float32         `json:"confidence"`
	Metadata     map[string]interface{} `json:"metadata,omitempty"`
}

// UpdateStream manages real-time position update streaming
type UpdateStream struct {
	id            string
	sessionID     string
	subscribers   map[string]UpdateSubscriber
	buffer        *UpdateBuffer
	interpolator  *PositionInterpolator
	predictor     *PositionPredictor
	converter     *ARCoordinateConverter
	sequence      uint64
	mu            sync.RWMutex
	ctx           context.Context
	cancel        context.CancelFunc
}

// UpdateSubscriber interface for update consumers
type UpdateSubscriber interface {
	OnUpdate(update *PositionUpdate) error
	OnBatch(updates []*PositionUpdate) error
	GetID() string
}

// UpdateBuffer buffers updates for batch processing
type UpdateBuffer struct {
	updates      []*PositionUpdate
	maxSize      int
	flushInterval time.Duration
	mu           sync.Mutex
	lastFlush    time.Time
}

// NewUpdateStream creates a new update stream
func NewUpdateStream(sessionID string, converter *ARCoordinateConverter) *UpdateStream {
	ctx, cancel := context.WithCancel(context.Background())

	stream := &UpdateStream{
		id:           fmt.Sprintf("stream_%d", time.Now().UnixNano()),
		sessionID:    sessionID,
		subscribers:  make(map[string]UpdateSubscriber),
		buffer:       NewUpdateBuffer(100, 50*time.Millisecond),
		interpolator: NewPositionInterpolator(),
		predictor:    NewPositionPredictor(),
		converter:    converter,
		sequence:     0,
		ctx:          ctx,
		cancel:       cancel,
	}

	// Start buffer flush routine
	go stream.flushRoutine()

	return stream
}

// NewUpdateBuffer creates a new update buffer
func NewUpdateBuffer(maxSize int, flushInterval time.Duration) *UpdateBuffer {
	return &UpdateBuffer{
		updates:       make([]*PositionUpdate, 0, maxSize),
		maxSize:       maxSize,
		flushInterval: flushInterval,
		lastFlush:     time.Now(),
	}
}

// PushUpdate pushes a new update to the stream
func (s *UpdateStream) PushUpdate(
	deviceID string,
	updateType UpdateType,
	arPos ARPoint3D,
	rotation ARRotation,
	confidence float32,
) error {

	s.mu.Lock()
	s.sequence++
	seq := s.sequence
	s.mu.Unlock()

	// Convert to world coordinates if converter is calibrated
	var worldPos spatial.Point3D
	if s.converter != nil && s.converter.calibrated {
		var err error
		worldPos, err = s.converter.ARToWorld(arPos)
		if err != nil {
			// Log error but continue with AR coordinates
			worldPos = spatial.Point3D{}
		}
	}

	update := &PositionUpdate{
		ID:            fmt.Sprintf("update_%d", time.Now().UnixNano()),
		SessionID:     s.sessionID,
		DeviceID:      deviceID,
		Type:          updateType,
		ARPosition:    arPos,
		WorldPosition: worldPos,
		Rotation:      rotation,
		Timestamp:     time.Now(),
		Sequence:      seq,
		Confidence:    confidence,
		Metadata:      make(map[string]interface{}),
	}

	// Add to buffer
	s.buffer.Add(update)

	// Check if buffer should be flushed
	if s.buffer.ShouldFlush() {
		s.flushBuffer()
	}

	// Send immediate updates for high-priority types
	if updateType == UpdateTypeInteract || updateType == UpdateTypeGesture {
		s.sendImmediate(update)
	}

	return nil
}

// Subscribe adds a subscriber to the stream
func (s *UpdateStream) Subscribe(subscriber UpdateSubscriber) {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.subscribers[subscriber.GetID()] = subscriber
}

// Unsubscribe removes a subscriber from the stream
func (s *UpdateStream) Unsubscribe(subscriberID string) {
	s.mu.Lock()
	defer s.mu.Unlock()

	delete(s.subscribers, subscriberID)
}

// flushRoutine periodically flushes the buffer
func (s *UpdateStream) flushRoutine() {
	ticker := time.NewTicker(s.buffer.flushInterval)
	defer ticker.Stop()

	for {
		select {
		case <-s.ctx.Done():
			return
		case <-ticker.C:
			if s.buffer.ShouldFlush() {
				s.flushBuffer()
			}
		}
	}
}

// flushBuffer flushes buffered updates to subscribers
func (s *UpdateStream) flushBuffer() {
	updates := s.buffer.Flush()
	if len(updates) == 0 {
		return
	}

	// Apply interpolation for smooth updates
	interpolated := s.interpolator.Interpolate(updates)

	// Send batch to all subscribers
	s.mu.RLock()
	subscribers := make([]UpdateSubscriber, 0, len(s.subscribers))
	for _, sub := range s.subscribers {
		subscribers = append(subscribers, sub)
	}
	s.mu.RUnlock()

	for _, subscriber := range subscribers {
		go subscriber.OnBatch(interpolated)
	}
}

// sendImmediate sends an update immediately to subscribers
func (s *UpdateStream) sendImmediate(update *PositionUpdate) {
	s.mu.RLock()
	subscribers := make([]UpdateSubscriber, 0, len(s.subscribers))
	for _, sub := range s.subscribers {
		subscribers = append(subscribers, sub)
	}
	s.mu.RUnlock()

	for _, subscriber := range subscribers {
		go subscriber.OnUpdate(update)
	}
}

// GetInterpolatedPosition gets interpolated position at specific time
func (s *UpdateStream) GetInterpolatedPosition(timestamp time.Time) (ARPoint3D, error) {
	return s.interpolator.GetPositionAt(timestamp)
}

// GetPredictedPosition predicts position at future time
func (s *UpdateStream) GetPredictedPosition(futureTime time.Duration) (ARPoint3D, error) {
	return s.predictor.PredictPosition(futureTime)
}

// Close closes the update stream
func (s *UpdateStream) Close() {
	s.cancel()
}

// Add adds an update to the buffer
func (b *UpdateBuffer) Add(update *PositionUpdate) {
	b.mu.Lock()
	defer b.mu.Unlock()

	b.updates = append(b.updates, update)
}

// ShouldFlush checks if buffer should be flushed
func (b *UpdateBuffer) ShouldFlush() bool {
	b.mu.Lock()
	defer b.mu.Unlock()

	return len(b.updates) >= b.maxSize ||
		time.Since(b.lastFlush) >= b.flushInterval
}

// Flush returns all buffered updates and clears buffer
func (b *UpdateBuffer) Flush() []*PositionUpdate {
	b.mu.Lock()
	defer b.mu.Unlock()

	if len(b.updates) == 0 {
		return nil
	}

	updates := make([]*PositionUpdate, len(b.updates))
	copy(updates, b.updates)

	b.updates = b.updates[:0]
	b.lastFlush = time.Now()

	return updates
}

// PositionInterpolator handles position interpolation
type PositionInterpolator struct {
	history      []*PositionUpdate
	maxHistory   int
	mu           sync.RWMutex
}

// NewPositionInterpolator creates a new position interpolator
func NewPositionInterpolator() *PositionInterpolator {
	return &PositionInterpolator{
		history:    make([]*PositionUpdate, 0, 100),
		maxHistory: 100,
	}
}

// Interpolate interpolates between position updates
func (pi *PositionInterpolator) Interpolate(updates []*PositionUpdate) []*PositionUpdate {
	if len(updates) <= 1 {
		return updates
	}

	pi.mu.Lock()
	defer pi.mu.Unlock()

	// Add to history
	pi.history = append(pi.history, updates...)
	if len(pi.history) > pi.maxHistory {
		pi.history = pi.history[len(pi.history)-pi.maxHistory:]
	}

	// Simple linear interpolation between updates
	interpolated := make([]*PositionUpdate, 0, len(updates)*2)

	for i := 0; i < len(updates)-1; i++ {
		current := updates[i]
		next := updates[i+1]

		interpolated = append(interpolated, current)

		// Calculate time difference
		timeDiff := next.Timestamp.Sub(current.Timestamp)
		if timeDiff > 100*time.Millisecond {
			// Insert interpolated position
			mid := &PositionUpdate{
				ID:        fmt.Sprintf("interp_%d", time.Now().UnixNano()),
				SessionID: current.SessionID,
				DeviceID:  current.DeviceID,
				Type:      UpdateTypePosition,
				ARPosition: ARPoint3D{
					X: (current.ARPosition.X + next.ARPosition.X) / 2,
					Y: (current.ARPosition.Y + next.ARPosition.Y) / 2,
					Z: (current.ARPosition.Z + next.ARPosition.Z) / 2,
				},
				Rotation:   current.Rotation, // Keep same rotation
				Timestamp:  current.Timestamp.Add(timeDiff / 2),
				Sequence:   current.Sequence,
				Confidence: (current.Confidence + next.Confidence) / 2,
			}
			interpolated = append(interpolated, mid)
		}
	}

	// Add last update
	interpolated = append(interpolated, updates[len(updates)-1])

	return interpolated
}

// GetPositionAt gets interpolated position at specific time
func (pi *PositionInterpolator) GetPositionAt(timestamp time.Time) (ARPoint3D, error) {
	pi.mu.RLock()
	defer pi.mu.RUnlock()

	if len(pi.history) == 0 {
		return ARPoint3D{}, fmt.Errorf("no position history")
	}

	// Find surrounding updates
	var before, after *PositionUpdate
	for i := 0; i < len(pi.history)-1; i++ {
		if pi.history[i].Timestamp.Before(timestamp) &&
			pi.history[i+1].Timestamp.After(timestamp) {
			before = pi.history[i]
			after = pi.history[i+1]
			break
		}
	}

	if before == nil || after == nil {
		// Return nearest position
		nearest := pi.history[0]
		for _, update := range pi.history {
			if absTimeDiff(update.Timestamp, timestamp) < absTimeDiff(nearest.Timestamp, timestamp) {
				nearest = update
			}
		}
		return nearest.ARPosition, nil
	}

	// Linear interpolation
	totalTime := after.Timestamp.Sub(before.Timestamp).Seconds()
	elapsed := timestamp.Sub(before.Timestamp).Seconds()
	t := elapsed / totalTime

	return ARPoint3D{
		X: before.ARPosition.X + (after.ARPosition.X-before.ARPosition.X)*t,
		Y: before.ARPosition.Y + (after.ARPosition.Y-before.ARPosition.Y)*t,
		Z: before.ARPosition.Z + (after.ARPosition.Z-before.ARPosition.Z)*t,
	}, nil
}

// PositionPredictor predicts future positions
type PositionPredictor struct {
	history    []*PositionUpdate
	maxHistory int
	mu         sync.RWMutex
}

// NewPositionPredictor creates a new position predictor
func NewPositionPredictor() *PositionPredictor {
	return &PositionPredictor{
		history:    make([]*PositionUpdate, 0, 50),
		maxHistory: 50,
	}
}

// AddUpdate adds an update to prediction history
func (pp *PositionPredictor) AddUpdate(update *PositionUpdate) {
	pp.mu.Lock()
	defer pp.mu.Unlock()

	pp.history = append(pp.history, update)
	if len(pp.history) > pp.maxHistory {
		pp.history = pp.history[1:]
	}
}

// PredictPosition predicts position at future time
func (pp *PositionPredictor) PredictPosition(futureTime time.Duration) (ARPoint3D, error) {
	pp.mu.RLock()
	defer pp.mu.RUnlock()

	if len(pp.history) < 2 {
		if len(pp.history) == 1 {
			return pp.history[0].ARPosition, nil
		}
		return ARPoint3D{}, fmt.Errorf("insufficient history for prediction")
	}

	// Simple linear extrapolation based on recent velocity
	recent := pp.history[len(pp.history)-5:]
	if len(recent) < 2 {
		recent = pp.history
	}

	// Calculate average velocity
	var velocityX, velocityY, velocityZ float64
	var count int

	for i := 1; i < len(recent); i++ {
		dt := recent[i].Timestamp.Sub(recent[i-1].Timestamp).Seconds()
		if dt > 0 {
			velocityX += (recent[i].ARPosition.X - recent[i-1].ARPosition.X) / dt
			velocityY += (recent[i].ARPosition.Y - recent[i-1].ARPosition.Y) / dt
			velocityZ += (recent[i].ARPosition.Z - recent[i-1].ARPosition.Z) / dt
			count++
		}
	}

	if count == 0 {
		return pp.history[len(pp.history)-1].ARPosition, nil
	}

	// Average velocity
	velocityX /= float64(count)
	velocityY /= float64(count)
	velocityZ /= float64(count)

	// Predict position
	lastPos := pp.history[len(pp.history)-1].ARPosition
	deltaT := futureTime.Seconds()

	return ARPoint3D{
		X: lastPos.X + velocityX*deltaT,
		Y: lastPos.Y + velocityY*deltaT,
		Z: lastPos.Z + velocityZ*deltaT,
	}, nil
}

// StreamManager manages multiple update streams
type StreamManager struct {
	streams   map[string]*UpdateStream
	sessions  map[string]*ARSession
	mu        sync.RWMutex
}

// NewStreamManager creates a new stream manager
func NewStreamManager() *StreamManager {
	return &StreamManager{
		streams:  make(map[string]*UpdateStream),
		sessions: make(map[string]*ARSession),
	}
}

// CreateStream creates a new update stream for a session
func (sm *StreamManager) CreateStream(session *ARSession) (*UpdateStream, error) {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	if _, exists := sm.streams[session.ID]; exists {
		return nil, fmt.Errorf("stream already exists for session %s", session.ID)
	}

	stream := NewUpdateStream(session.ID, session.Converter)
	sm.streams[session.ID] = stream
	sm.sessions[session.ID] = session

	return stream, nil
}

// GetStream gets a stream by session ID
func (sm *StreamManager) GetStream(sessionID string) (*UpdateStream, error) {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	stream, exists := sm.streams[sessionID]
	if !exists {
		return nil, fmt.Errorf("stream not found for session %s", sessionID)
	}

	return stream, nil
}

// CloseStream closes a stream
func (sm *StreamManager) CloseStream(sessionID string) error {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	stream, exists := sm.streams[sessionID]
	if !exists {
		return fmt.Errorf("stream not found for session %s", sessionID)
	}

	stream.Close()
	delete(sm.streams, sessionID)
	delete(sm.sessions, sessionID)

	return nil
}

// BroadcastToDevice broadcasts an update to all streams for a device
func (sm *StreamManager) BroadcastToDevice(deviceID string, update *PositionUpdate) {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	for _, session := range sm.sessions {
		if session.DeviceID == deviceID {
			if stream, exists := sm.streams[session.ID]; exists {
				stream.sendImmediate(update)
			}
		}
	}
}

// absTimeDiff calculates absolute time difference
func absTimeDiff(t1, t2 time.Time) time.Duration {
	diff := t1.Sub(t2)
	if diff < 0 {
		return -diff
	}
	return diff
}

// UpdateMessage represents a message for network transmission
type UpdateMessage struct {
	Type    string          `json:"type"`
	Payload json.RawMessage `json:"payload"`
}

// SerializeUpdate serializes an update for network transmission
func SerializeUpdate(update *PositionUpdate) ([]byte, error) {
	payload, err := json.Marshal(update)
	if err != nil {
		return nil, err
	}

	msg := UpdateMessage{
		Type:    "position_update",
		Payload: payload,
	}

	return json.Marshal(msg)
}

// DeserializeUpdate deserializes an update from network
func DeserializeUpdate(data []byte) (*PositionUpdate, error) {
	var msg UpdateMessage
	if err := json.Unmarshal(data, &msg); err != nil {
		return nil, err
	}

	if msg.Type != "position_update" {
		return nil, fmt.Errorf("unexpected message type: %s", msg.Type)
	}

	var update PositionUpdate
	if err := json.Unmarshal(msg.Payload, &update); err != nil {
		return nil, err
	}

	return &update, nil
}