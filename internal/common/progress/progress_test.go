package progress

import (
	"testing"
	"time"
)

func TestTracker_New(t *testing.T) {
	tracker := New(5, "Test Task")

	if tracker.total != 5 {
		t.Errorf("New() total = %v, want 5", tracker.total)
	}
	if tracker.label != "Test Task" {
		t.Errorf("New() label = %v, want 'Test Task'", tracker.label)
	}
	if tracker.current != 0 {
		t.Errorf("New() current = %v, want 0", tracker.current)
	}
}

func TestTracker_NewSilent(t *testing.T) {
	tracker := NewSilent(3, "Silent Task")

	if !tracker.silent {
		t.Errorf("NewSilent() silent = %v, want true", tracker.silent)
	}
	if tracker.total != 3 {
		t.Errorf("NewSilent() total = %v, want 3", tracker.total)
	}
}

func TestTracker_Step(t *testing.T) {
	tracker := NewSilent(3, "Test Task")

	// Initial state
	if tracker.current != 0 {
		t.Errorf("Initial current = %v, want 0", tracker.current)
	}

	// First step
	tracker.Step("Step 1")
	if tracker.current != 1 {
		t.Errorf("After step 1: current = %v, want 1", tracker.current)
	}

	// Second step
	tracker.Step("Step 2")
	if tracker.current != 2 {
		t.Errorf("After step 2: current = %v, want 2", tracker.current)
	}

	// Third step
	tracker.Step("Step 3")
	if tracker.current != 3 {
		t.Errorf("After step 3: current = %v, want 3", tracker.current)
	}
}

func TestTracker_SetTotal(t *testing.T) {
	tracker := NewSilent(5, "Test Task")

	tracker.SetTotal(10)
	if tracker.total != 10 {
		t.Errorf("SetTotal(10): total = %v, want 10", tracker.total)
	}
}

func TestTracker_Finish(t *testing.T) {
	tracker := NewSilent(5, "Test Task")

	// Move to step 3
	tracker.Step("Step 1")
	tracker.Step("Step 2")
	tracker.Step("Step 3")

	// Finish should set current to total
	tracker.Finish()
	if tracker.current != tracker.total {
		t.Errorf("Finish(): current = %v, want %v", tracker.current, tracker.total)
	}
}

func TestTracker_Finish_AlreadyComplete(t *testing.T) {
	tracker := NewSilent(2, "Test Task")

	// Complete all steps
	tracker.Step("Step 1")
	tracker.Step("Step 2")

	// Finish should not change current when already complete
	tracker.Finish()
	if tracker.current != 2 {
		t.Errorf("Finish() when complete: current = %v, want 2", tracker.current)
	}
}

func TestTracker_ElapsedTime(t *testing.T) {
	tracker := NewSilent(1, "Test Task")

	// Small delay to ensure time has passed
	time.Sleep(1 * time.Millisecond)

	tracker.Step("Step 1")

	elapsed := time.Since(tracker.started)
	if elapsed <= 0 {
		t.Errorf("Elapsed time should be positive, got %v", elapsed)
	}
}

func TestTracker_ConcurrentAccess(t *testing.T) {
	tracker := NewSilent(100, "Concurrent Task")

	// Run concurrent steps
	done := make(chan bool, 10)
	for i := 0; i < 10; i++ {
		go func(id int) {
			for j := 0; j < 10; j++ {
				tracker.Step("Concurrent step")
			}
			done <- true
		}(i)
	}

	// Wait for all goroutines
	for i := 0; i < 10; i++ {
		<-done
	}

	if tracker.current != 100 {
		t.Errorf("Concurrent access: current = %v, want 100", tracker.current)
	}
}