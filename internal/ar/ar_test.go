package ar

import (
	"fmt"
	"math"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/merge"
	"github.com/arx-os/arxos/internal/spatial"
)

func TestARCoordinateConverter(t *testing.T) {
	converter := NewARCoordinateConverter(CoordinateSystemARKit)

	// Test calibration
	arAnchor := ARPoint3D{X: 0, Y: 0, Z: 0}
	worldAnchor := spatial.Point3D{X: 100, Y: 200, Z: 10}
	rotation := ARRotation{X: 0, Y: 0, Z: 0, W: 1} // Identity rotation

	err := converter.Calibrate(arAnchor, worldAnchor, rotation)
	if err != nil {
		t.Fatalf("Failed to calibrate: %v", err)
	}

	// Test AR to World conversion
	arPoint := ARPoint3D{X: 1, Y: 2, Z: -3}
	worldPoint, err := converter.ARToWorld(arPoint)
	if err != nil {
		t.Fatalf("Failed to convert AR to World: %v", err)
	}

	// ARKit: +Y is up, +Z is toward viewer
	// World: +Z is up, +Y is north
	expectedWorld := spatial.Point3D{
		X: 101,  // 100 + 1
		Y: 203,  // 200 + 3 (AR's -Z becomes world's +Y)
		Z: 12,   // 10 + 2 (AR's +Y becomes world's +Z)
	}

	tolerance := 0.001
	if !pointsEqual(worldPoint, expectedWorld, tolerance) {
		t.Errorf("AR to World conversion incorrect. Got %v, expected %v", worldPoint, expectedWorld)
	}

	// Test World to AR conversion
	arPointBack, err := converter.WorldToAR(worldPoint)
	if err != nil {
		t.Fatalf("Failed to convert World to AR: %v", err)
	}

	if !arPointsEqual(arPointBack, arPoint, tolerance) {
		t.Errorf("World to AR conversion incorrect. Got %v, expected %v", arPointBack, arPoint)
	}
}

func TestSpatialAnchor(t *testing.T) {
	persistence := NewMemoryAnchorPersistence()
	store := NewAnchorStore(persistence)

	// Create anchor
	deviceID := "test-device"
	arPos := ARPoint3D{X: 1, Y: 2, Z: 3}
	worldPos := spatial.Point3D{X: 101, Y: 202, Z: 303}
	rotation := ARRotation{X: 0, Y: 0, Z: 0, W: 1}

	anchor, err := store.CreateAnchor(deviceID, arPos, worldPos, rotation, AnchorTypeUser)
	if err != nil {
		t.Fatalf("Failed to create anchor: %v", err)
	}

	if anchor.Type != AnchorTypeUser {
		t.Errorf("Expected anchor type %v, got %v", AnchorTypeUser, anchor.Type)
	}

	// Update anchor
	newARPos := ARPoint3D{X: 1.1, Y: 2.1, Z: 3.1}
	err = store.UpdateAnchor(anchor.ID, newARPos, 0.9)
	if err != nil {
		t.Fatalf("Failed to update anchor: %v", err)
	}

	// Retrieve anchor
	retrieved, err := store.GetAnchor(anchor.ID)
	if err != nil {
		t.Fatalf("Failed to retrieve anchor: %v", err)
	}

	if !arPointsEqual(retrieved.ARPosition, newARPos, 0.001) {
		t.Errorf("Anchor position not updated correctly. Got %v, expected %v",
			retrieved.ARPosition, newARPos)
	}

	// Test nearby anchors
	searchPos := ARPoint3D{X: 1, Y: 2, Z: 3}
	nearby := store.FindNearbyAnchors(searchPos, 1.0)
	if len(nearby) != 1 {
		t.Errorf("Expected 1 nearby anchor, got %d", len(nearby))
	}

	// Test device anchors
	deviceAnchors := store.GetDeviceAnchors(deviceID)
	if len(deviceAnchors) != 1 {
		t.Errorf("Expected 1 device anchor, got %d", len(deviceAnchors))
	}
}

func TestUpdateStream(t *testing.T) {
	converter := NewARCoordinateConverter(CoordinateSystemARKit)
	stream := NewUpdateStream("test-session", converter)
	defer stream.Close()

	// Create test subscriber
	subscriber := &testSubscriber{
		id:      "test-sub",
		updates: make([]*PositionUpdate, 0),
		batches: make([][]*PositionUpdate, 0),
	}

	stream.Subscribe(subscriber)

	// Push updates
	for i := 0; i < 5; i++ {
		err := stream.PushUpdate(
			"test-device",
			UpdateTypePosition,
			ARPoint3D{X: float64(i), Y: float64(i), Z: float64(i)},
			ARRotation{X: 0, Y: 0, Z: 0, W: 1},
			0.95,
		)
		if err != nil {
			t.Fatalf("Failed to push update: %v", err)
		}
		time.Sleep(10 * time.Millisecond)
	}

	// Wait for buffer flush
	time.Sleep(100 * time.Millisecond)

	// Check batches received
	if len(subscriber.batches) == 0 {
		t.Error("No batches received by subscriber")
	}

	// Test interpolation - interpolator needs history
	// Add updates to interpolator's history
	interpolator := stream.interpolator
	for _, batch := range subscriber.batches {
		for _, update := range batch {
			interpolator.history = append(interpolator.history, update)
		}
	}

	// Now test interpolation with history
	if len(interpolator.history) > 1 {
		timestamp := interpolator.history[0].Timestamp.Add(50 * time.Millisecond)
		_, err := stream.GetInterpolatedPosition(timestamp)
		if err != nil {
			t.Errorf("Failed to interpolate with history: %v", err)
		}
	}
}

func TestSyncEngine(t *testing.T) {
	changeDetector := merge.NewChangeDetector()
	conflictResolver := merge.NewConflictResolver(nil)
	bimUpdater := NewMockBIMUpdater()

	syncEngine := NewSyncEngine(changeDetector, conflictResolver, bimUpdater)
	defer syncEngine.Close()

	// Register session
	session := NewARSession("test-device", "test-building", CoordinateSystemARKit)
	syncEngine.RegisterSession(session)

	// Record changes
	change1 := &ARChange{
		ID:          "change1",
		SessionID:   session.ID,
		EquipmentID: "equip1",
		Type:        ChangeTypeMove,
		OldPosition: spatial.Point3D{X: 0, Y: 0, Z: 0},
		NewPosition: spatial.Point3D{X: 1, Y: 1, Z: 0},
		Timestamp:   time.Now(),
		Confidence:  0.8,
	}

	err := syncEngine.RecordChange(change1)
	if err != nil {
		t.Fatalf("Failed to record change: %v", err)
	}

	// Record critical change (add)
	change2 := &ARChange{
		ID:          "change2",
		SessionID:   session.ID,
		EquipmentID: "equip2",
		Type:        ChangeTypeAdd,
		NewPosition: spatial.Point3D{X: 5, Y: 5, Z: 0},
		Timestamp:   time.Now(),
		Confidence:  0.9,
		Attributes: map[string]interface{}{
			"type": "HVAC",
			"model": "XYZ123",
		},
	}

	err = syncEngine.RecordChange(change2)
	if err != nil {
		t.Fatalf("Failed to record critical change: %v", err)
	}

	// Wait for sync
	time.Sleep(100 * time.Millisecond)

	// Check sync status
	status, err := syncEngine.GetSyncStatus(session.ID)
	if err != nil {
		t.Fatalf("Failed to get sync status: %v", err)
	}

	if status.PendingChanges < 0 {
		t.Errorf("Invalid pending changes count: %d", status.PendingChanges)
	}

	// Check BIM updates
	updates := bimUpdater.GetUpdates()
	if len(updates) == 0 {
		// Manually trigger sync
		err = syncEngine.syncSession(session.ID)
		if err != nil {
			t.Errorf("Failed to sync session: %v", err)
		}
		updates = bimUpdater.GetUpdates()
	}

	// Verify updates were recorded
	if len(updates) < 1 {
		t.Errorf("Expected at least 1 BIM update, got %d", len(updates))
	}
}

func TestARSession(t *testing.T) {
	session := NewARSession("test-device", "test-building", CoordinateSystemARKit)

	// Test initial state
	if session.System != CoordinateSystemARKit {
		t.Errorf("Expected system %v, got %v", CoordinateSystemARKit, session.System)
	}

	// Update tracking
	quality := TrackingQuality{
		State:         TrackingStateNormal,
		Confidence:    0.85,
		LightEstimate: 0.7,
		PlaneCount:    3,
		FeatureCount:  150,
		LastUpdate:    time.Now(),
	}

	session.UpdateTracking(quality)

	if !session.IsTrackingStable() {
		t.Error("Expected tracking to be stable")
	}

	// Add anchors
	session.AddAnchor("anchor1")
	session.AddAnchor("anchor2")

	if len(session.ActiveAnchors) != 2 {
		t.Errorf("Expected 2 active anchors, got %d", len(session.ActiveAnchors))
	}

	// Remove anchor
	session.RemoveAnchor("anchor1")

	if len(session.ActiveAnchors) != 1 {
		t.Errorf("Expected 1 active anchor after removal, got %d", len(session.ActiveAnchors))
	}
}

func TestAnchorLocalization(t *testing.T) {
	// Create known anchors
	knownAnchors := map[string]*SpatialAnchor{
		"anchor1": {
			ID:         "anchor1",
			ARPosition: ARPoint3D{X: 0, Y: 0, Z: 0},
		},
		"anchor2": {
			ID:         "anchor2",
			ARPosition: ARPoint3D{X: 10, Y: 0, Z: 0},
		},
		"anchor3": {
			ID:         "anchor3",
			ARPosition: ARPoint3D{X: 5, Y: 5, Z: 0},
		},
	}

	// Simulate observed anchors with drift
	visibleAnchors := map[string]ARPoint3D{
		"anchor1": {X: 0.1, Y: 0.1, Z: 0},
		"anchor2": {X: 10.1, Y: 0.1, Z: 0},
		"anchor3": {X: 5.1, Y: 5.1, Z: 0},
	}

	transform, err := LocalizeWithAnchors(visibleAnchors, knownAnchors)
	if err != nil {
		t.Fatalf("Failed to localize with anchors: %v", err)
	}

	// Check drift correction is approximately (-0.1, -0.1, 0)
	expectedDrift := ARPoint3D{X: -0.1, Y: -0.1, Z: 0}
	tolerance := 0.01

	if !arPointsEqual(transform.Position, expectedDrift, tolerance) {
		t.Errorf("Drift correction incorrect. Got %v, expected %v",
			transform.Position, expectedDrift)
	}

	if transform.Confidence < 0.9 {
		t.Errorf("Expected high confidence, got %f", transform.Confidence)
	}
}

func TestChangeQueue(t *testing.T) {
	queue := NewChangeQueue(10)

	// Add changes
	for i := 0; i < 5; i++ {
		change := &ARChange{
			ID:          fmt.Sprintf("change%d", i),
			SessionID:   "session1",
			EquipmentID: fmt.Sprintf("equip%d", i),
			Type:        ChangeTypeMove,
			Timestamp:   time.Now(),
			Confidence:  0.8,
		}
		queue.Add(change)
	}

	// Add high priority change
	highPriority := &ARChange{
		ID:          "high1",
		SessionID:   "session1",
		EquipmentID: "equip_high",
		Type:        ChangeTypeAdd,
		Timestamp:   time.Now(),
		Confidence:  0.95,
	}
	queue.AddHighPriority(highPriority)

	// Get session changes
	changes := queue.GetSessionChanges("session1")
	if len(changes) != 6 {
		t.Errorf("Expected 6 changes, got %d", len(changes))
	}

	// Verify high priority is first
	if changes[0].ID != "high1" {
		t.Error("High priority change should be first")
	}

	// Mark as applied and clear
	for _, change := range changes {
		change.Applied = true
	}
	queue.ClearSessionChanges("session1")

	// Verify cleared
	remaining := queue.GetSessionChanges("session1")
	if len(remaining) != 0 {
		t.Errorf("Expected 0 changes after clear, got %d", len(remaining))
	}
}

// Helper functions

func pointsEqual(p1 spatial.Point3D, p2 spatial.Point3D, tolerance float64) bool {
	return math.Abs(p1.X-p2.X) < tolerance &&
		math.Abs(p1.Y-p2.Y) < tolerance &&
		math.Abs(p1.Z-p2.Z) < tolerance
}

func arPointsEqual(p1 ARPoint3D, p2 ARPoint3D, tolerance float64) bool {
	return math.Abs(p1.X-p2.X) < tolerance &&
		math.Abs(p1.Y-p2.Y) < tolerance &&
		math.Abs(p1.Z-p2.Z) < tolerance
}

// Test subscriber implementation
type testSubscriber struct {
	id      string
	updates []*PositionUpdate
	batches [][]*PositionUpdate
}

func (ts *testSubscriber) OnUpdate(update *PositionUpdate) error {
	ts.updates = append(ts.updates, update)
	return nil
}

func (ts *testSubscriber) OnBatch(updates []*PositionUpdate) error {
	ts.batches = append(ts.batches, updates)
	return nil
}

func (ts *testSubscriber) GetID() string {
	return ts.id
}