package animation

import (
	"fmt"
	"os"
	"strings"
	"sync"
	"time"

	"golang.org/x/term"
)

// Animator handles smooth transitions and live updates for terminal visualizations
type Animator struct {
	mu            sync.Mutex
	running       bool
	stopCh        chan struct{}
	frameRate     time.Duration
	currentFrame  string
	previousFrame string
	width         int
	height        int
}

// Frame represents a single animation frame
type Frame struct {
	Content   string
	Timestamp time.Time
	Duration  time.Duration
}

// TransitionType defines animation transition types
type TransitionType int

const (
	TransitionNone TransitionType = iota
	TransitionFade
	TransitionSlide
	TransitionWipe
	TransitionSmooth
)

// NewAnimator creates a new animator
func NewAnimator(fps int) *Animator {
	if fps <= 0 {
		fps = 10 // Default 10 FPS
	}

	width, height, _ := term.GetSize(int(os.Stdout.Fd()))
	if width <= 0 {
		width = 80
	}
	if height <= 0 {
		height = 24
	}

	return &Animator{
		frameRate: time.Second / time.Duration(fps),
		width:     width,
		height:    height,
		stopCh:    make(chan struct{}),
	}
}

// Start begins the animation loop
func (a *Animator) Start() {
	a.mu.Lock()
	defer a.mu.Unlock()

	if a.running {
		return
	}

	a.running = true
	go a.animationLoop()
}

// Stop stops the animation
func (a *Animator) Stop() {
	a.mu.Lock()
	defer a.mu.Unlock()

	if !a.running {
		return
	}

	close(a.stopCh)
	a.running = false
}

// UpdateFrame updates the current frame with smooth transition
func (a *Animator) UpdateFrame(newContent string, transition TransitionType) {
	a.mu.Lock()
	defer a.mu.Unlock()

	a.previousFrame = a.currentFrame
	a.currentFrame = a.applyTransition(a.previousFrame, newContent, transition)
}

// animationLoop runs the animation update cycle
func (a *Animator) animationLoop() {
	ticker := time.NewTicker(a.frameRate)
	defer ticker.Stop()

	for {
		select {
		case <-a.stopCh:
			return
		case <-ticker.C:
			a.renderFrame()
		}
	}
}

// renderFrame renders the current frame
func (a *Animator) renderFrame() {
	a.mu.Lock()
	frame := a.currentFrame
	a.mu.Unlock()

	if frame != "" {
		// Clear screen and render
		clearScreen()
		fmt.Print(frame)
	}
}

// applyTransition applies a transition effect between frames
func (a *Animator) applyTransition(oldFrame, newFrame string, transition TransitionType) string {
	switch transition {
	case TransitionFade:
		return a.fadeTransition(oldFrame, newFrame)
	case TransitionSlide:
		return a.slideTransition(oldFrame, newFrame)
	case TransitionWipe:
		return a.wipeTransition(oldFrame, newFrame)
	case TransitionSmooth:
		return a.smoothTransition(oldFrame, newFrame)
	default:
		return newFrame
	}
}

// fadeTransition creates a fade effect
func (a *Animator) fadeTransition(oldFrame, newFrame string) string {
	// Simple fade: show new frame directly
	// In a more advanced implementation, we could blend characters
	return newFrame
}

// slideTransition creates a slide effect
func (a *Animator) slideTransition(oldFrame, newFrame string) string {
	// Slide from right to left
	oldLines := strings.Split(oldFrame, "\n")
	newLines := strings.Split(newFrame, "\n")

	maxLines := len(oldLines)
	if len(newLines) > maxLines {
		maxLines = len(newLines)
	}

	result := make([]string, maxLines)
	slideOffset := a.width / 4 // Slide 1/4 of the width

	for i := 0; i < maxLines; i++ {
		oldLine := ""
		newLine := ""

		if i < len(oldLines) {
			oldLine = oldLines[i]
		}
		if i < len(newLines) {
			newLine = newLines[i]
		}

		// Combine with slide effect
		if len(oldLine) > slideOffset {
			oldLine = oldLine[slideOffset:]
		} else {
			oldLine = ""
		}

		combined := oldLine + strings.Repeat(" ", slideOffset) + newLine
		if len(combined) > a.width {
			combined = combined[:a.width]
		}

		result[i] = combined
	}

	return strings.Join(result, "\n")
}

// wipeTransition creates a wipe effect
func (a *Animator) wipeTransition(oldFrame, newFrame string) string {
	// Wipe from top to bottom
	oldLines := strings.Split(oldFrame, "\n")
	newLines := strings.Split(newFrame, "\n")

	wipePosition := len(newLines) / 3 // Show 1/3 of new content

	result := []string{}
	for i := 0; i < wipePosition && i < len(newLines); i++ {
		result = append(result, newLines[i])
	}
	for i := wipePosition; i < len(oldLines); i++ {
		result = append(result, oldLines[i])
	}

	return strings.Join(result, "\n")
}

// smoothTransition creates a smooth value transition
func (a *Animator) smoothTransition(oldFrame, newFrame string) string {
	// For numeric values, interpolate between old and new
	// This is a simplified version
	return newFrame
}

// clearScreen clears the terminal screen
func clearScreen() {
	fmt.Print("\033[H\033[2J")
}

// moveCursor moves cursor to position
func moveCursor(x, y int) {
	fmt.Printf("\033[%d;%dH", y+1, x+1)
}

// LiveChart provides live updating charts
type LiveChart struct {
	animator   *Animator
	updateFunc func() string
	interval   time.Duration
	stopCh     chan struct{}
	running    bool
	mu         sync.Mutex
}

// NewLiveChart creates a new live updating chart
func NewLiveChart(updateFunc func() string, interval time.Duration) *LiveChart {
	return &LiveChart{
		animator:   NewAnimator(10),
		updateFunc: updateFunc,
		interval:   interval,
		stopCh:     make(chan struct{}),
	}
}

// Start begins live updates
func (lc *LiveChart) Start() {
	lc.mu.Lock()
	defer lc.mu.Unlock()

	if lc.running {
		return
	}

	lc.running = true
	lc.animator.Start()

	go lc.updateLoop()
}

// Stop stops live updates
func (lc *LiveChart) Stop() {
	lc.mu.Lock()
	defer lc.mu.Unlock()

	if !lc.running {
		return
	}

	close(lc.stopCh)
	lc.animator.Stop()
	lc.running = false
}

// updateLoop runs the update cycle
func (lc *LiveChart) updateLoop() {
	ticker := time.NewTicker(lc.interval)
	defer ticker.Stop()

	// Initial render
	if lc.updateFunc != nil {
		content := lc.updateFunc()
		lc.animator.UpdateFrame(content, TransitionSmooth)
	}

	for {
		select {
		case <-lc.stopCh:
			return
		case <-ticker.C:
			if lc.updateFunc != nil {
				content := lc.updateFunc()
				lc.animator.UpdateFrame(content, TransitionSmooth)
			}
		}
	}
}

// ProgressBar provides animated progress bars
type ProgressBar struct {
	width    int
	current  float64
	target   float64
	label    string
	symbols  []rune
	animated bool
}

// NewProgressBar creates a new progress bar
func NewProgressBar(width int, label string) *ProgressBar {
	return &ProgressBar{
		width:   width,
		label:   label,
		symbols: []rune{'▏', '▎', '▍', '▌', '▋', '▊', '▉', '█'},
	}
}

// Update updates the progress with animation
func (pb *ProgressBar) Update(value float64) {
	pb.target = value
	if pb.animated {
		pb.animateToTarget()
	} else {
		pb.current = value
	}
}

// animateToTarget smoothly animates to target value
func (pb *ProgressBar) animateToTarget() {
	steps := 10
	increment := (pb.target - pb.current) / float64(steps)

	for i := 0; i < steps; i++ {
		pb.current += increment
		pb.render()
		time.Sleep(50 * time.Millisecond)
	}

	pb.current = pb.target
	pb.render()
}

// render renders the progress bar
func (pb *ProgressBar) render() {
	filled := int(pb.current * float64(pb.width))
	empty := pb.width - filled

	var bar strings.Builder

	// Add label
	if pb.label != "" {
		bar.WriteString(fmt.Sprintf("%-15s ", pb.label))
	}

	// Build bar
	for i := 0; i < filled; i++ {
		bar.WriteRune(pb.symbols[len(pb.symbols)-1]) // Full block
	}

	// Add partial block if needed
	fraction := pb.current*float64(pb.width) - float64(filled)
	if fraction > 0 && filled < pb.width {
		index := int(fraction * float64(len(pb.symbols)-1))
		bar.WriteRune(pb.symbols[index])
		empty--
	}

	// Add empty blocks
	for i := 0; i < empty; i++ {
		bar.WriteRune('░')
	}

	// Add percentage
	bar.WriteString(fmt.Sprintf(" %5.1f%%", pb.current*100))

	// Clear line and print
	fmt.Printf("\r%s", bar.String())
}

// Spinner provides loading animations
type Spinner struct {
	frames  []string
	current int
	label   string
	running bool
	stopCh  chan struct{}
	mu      sync.Mutex
}

// NewSpinner creates a new spinner
func NewSpinner(label string) *Spinner {
	return &Spinner{
		label: label,
		frames: []string{
			"⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏",
		},
		stopCh: make(chan struct{}),
	}
}

// Start starts the spinner
func (s *Spinner) Start() {
	s.mu.Lock()
	defer s.mu.Unlock()

	if s.running {
		return
	}

	s.running = true
	go s.spin()
}

// Stop stops the spinner
func (s *Spinner) Stop() {
	s.mu.Lock()
	defer s.mu.Unlock()

	if !s.running {
		return
	}

	close(s.stopCh)
	s.running = false

	// Clear the spinner line
	fmt.Printf("\r%s\r", strings.Repeat(" ", len(s.label)+10))
}

// spin runs the spinner animation
func (s *Spinner) spin() {
	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop()

	for {
		select {
		case <-s.stopCh:
			return
		case <-ticker.C:
			s.mu.Lock()
			frame := s.frames[s.current]
			s.current = (s.current + 1) % len(s.frames)
			s.mu.Unlock()

			fmt.Printf("\r%s %s", frame, s.label)
		}
	}
}

// Example usage functions
func ExampleLiveChart() {
	// Create a live updating sparkline
	counter := 0
	updateFunc := func() string {
		counter++
		// Generate new data
		data := make([]float64, 20)
		for i := range data {
			data[i] = 50 + float64(i+counter)*2
		}

		// Return formatted sparkline
		return fmt.Sprintf("Live Data: %v", data)
	}

	chart := NewLiveChart(updateFunc, 1*time.Second)
	chart.Start()

	// Run for 10 seconds
	time.Sleep(10 * time.Second)
	chart.Stop()
}

func ExampleProgressBar() {
	pb := NewProgressBar(30, "Processing")
	pb.animated = true

	for i := 0; i <= 100; i += 10 {
		pb.Update(float64(i) / 100)
		time.Sleep(500 * time.Millisecond)
	}

	fmt.Println("\nComplete!")
}

func ExampleSpinner() {
	spinner := NewSpinner("Loading data...")
	spinner.Start()

	// Simulate work
	time.Sleep(5 * time.Second)

	spinner.Stop()
	fmt.Println("Done!")
}
