package progress

import (
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// Tracker tracks progress of operations
type Tracker struct {
	total   int
	current int
	label   string
	started time.Time
	mu      sync.Mutex
	silent  bool
}

// New creates a new progress tracker
func New(total int, label string) *Tracker {
	return &Tracker{
		total:   total,
		label:   label,
		started: time.Now(),
	}
}

// NewSilent creates a silent progress tracker for testing
func NewSilent(total int, label string) *Tracker {
	return &Tracker{
		total:   total,
		label:   label,
		started: time.Now(),
		silent:  true,
	}
}

// Step increments the progress by one step
func (p *Tracker) Step(description string) {
	p.mu.Lock()
	defer p.mu.Unlock()

	p.current++
	if !p.silent {
		percentage := float64(p.current) / float64(p.total) * 100
		logger.Info("📊 %s [%d/%d] %.1f%% - %s",
			p.label, p.current, p.total, percentage, description)
	}
}

// SetTotal updates the total number of steps
func (p *Tracker) SetTotal(total int) {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.total = total
}

// Finish marks the progress as complete
func (p *Tracker) Finish() {
	p.mu.Lock()
	defer p.mu.Unlock()

	if p.current < p.total {
		p.current = p.total
	}

	if !p.silent {
		elapsed := time.Since(p.started)
		logger.Info("✅ %s completed in %v", p.label, elapsed.Truncate(time.Millisecond))
	}
}

// Error logs an error and finishes the progress
func (p *Tracker) Error(err error) {
	p.mu.Lock()
	defer p.mu.Unlock()

	if !p.silent {
		elapsed := time.Since(p.started)
		logger.Error("❌ %s failed after %v: %v", p.label, elapsed.Truncate(time.Millisecond), err)
	}
}
