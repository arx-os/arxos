package rendering

import (
	"fmt"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/gdamore/tcell/v2"
)

// InteractiveViewer provides interactive 3D viewing with keyboard controls
type InteractiveViewer struct {
	renderer     *Renderer
	screen       tcell.Screen
	plan         *models.FloorPlan
	multiFloor   bool
	currentFloor int
	floors       []*models.FloorPlan
	running      bool
	needsRedraw  bool
	statusMsg    string
	msgTimeout   time.Time
}

// NewInteractiveViewer creates a new interactive 3D viewer
func NewInteractiveViewer(renderer *Renderer, plan *models.FloorPlan, multiFloor bool) (*InteractiveViewer, error) {
	screen, err := tcell.NewScreen()
	if err != nil {
		return nil, fmt.Errorf("failed to create screen: %w", err)
	}

	if err := screen.Init(); err != nil {
		return nil, fmt.Errorf("failed to initialize screen: %w", err)
	}

	return &InteractiveViewer{
		renderer:     renderer,
		screen:       screen,
		plan:         plan,
		multiFloor:   multiFloor,
		currentFloor: 0,
		floors:       []*models.FloorPlan{plan},
		running:      true,
		needsRedraw:  true,
	}, nil
}

// Run starts the interactive viewer
func (v *InteractiveViewer) Run() error {
	defer v.screen.Fini()

	// Set default style
	v.screen.SetStyle(tcell.StyleDefault.Background(tcell.ColorReset).Foreground(tcell.ColorReset))
	v.screen.Clear()

	// Initial render
	v.redraw()

	// Event loop
	eventCh := make(chan tcell.Event)
	go func() {
		for v.running {
			eventCh <- v.screen.PollEvent()
		}
	}()

	// Animation ticker for smooth updates
	ticker := time.NewTicker(50 * time.Millisecond)
	defer ticker.Stop()

	for v.running {
		select {
		case event := <-eventCh:
			v.handleEvent(event)
		case <-ticker.C:
			if v.needsRedraw {
				v.redraw()
				v.needsRedraw = false
			}
			// Clear status message after timeout
			if !v.msgTimeout.IsZero() && time.Now().After(v.msgTimeout) {
				v.statusMsg = ""
				v.msgTimeout = time.Time{}
				v.needsRedraw = true
			}
		}
	}

	return nil
}

// handleEvent processes input events
func (v *InteractiveViewer) handleEvent(event tcell.Event) {
	switch ev := event.(type) {
	case *tcell.EventKey:
		v.handleKeyEvent(ev)
	case *tcell.EventResize:
		w, h := v.screen.Size()
		v.renderer.width = w
		v.renderer.height = h - 5 // Leave space for status
		v.renderer.origin.X = float64(w) / 2
		v.renderer.origin.Y = float64(h-5) / 2
		v.needsRedraw = true
		v.screen.Sync()
	}
}

// handleKeyEvent processes keyboard input
func (v *InteractiveViewer) handleKeyEvent(ev *tcell.EventKey) {
	const rotationStep = 0.1
	const tiltStep = 0.1
	const zoomStep = 0.1

	switch ev.Key() {
	case tcell.KeyEscape, tcell.KeyCtrlC:
		v.running = false
		return
	case tcell.KeyLeft:
		v.renderer.RotateView(-rotationStep)
		v.setStatus("Rotating left")
		v.needsRedraw = true
	case tcell.KeyRight:
		v.renderer.RotateView(rotationStep)
		v.setStatus("Rotating right")
		v.needsRedraw = true
	case tcell.KeyUp:
		v.renderer.TiltView(-tiltStep)
		v.setStatus("Tilting up")
		v.needsRedraw = true
	case tcell.KeyDown:
		v.renderer.TiltView(tiltStep)
		v.setStatus("Tilting down")
		v.needsRedraw = true
	case tcell.KeyRune:
		switch ev.Rune() {
		case 'q', 'Q':
			v.running = false
			return
		case '+', '=':
			v.renderer.Zoom(1.0 + zoomStep)
			v.setStatus("Zooming in")
			v.needsRedraw = true
		case '-', '_':
			v.renderer.Zoom(1.0 - zoomStep)
			v.setStatus("Zooming out")
			v.needsRedraw = true
		case ' ':
			// Reset view
			v.renderer.SetViewMode(ViewIsometric)
			v.renderer.scale = 1.0
			v.setStatus("View reset")
			v.needsRedraw = true
		case '1':
			v.renderer.SetViewMode(ViewIsometric)
			v.setStatus("Isometric view")
			v.needsRedraw = true
		case '2':
			v.renderer.SetViewMode(ViewDimetric)
			v.setStatus("Dimetric view")
			v.needsRedraw = true
		case '3':
			v.renderer.SetViewMode(ViewTrimetric)
			v.setStatus("Trimetric view")
			v.needsRedraw = true
		case '4':
			v.renderer.SetViewMode(ViewTopDown)
			v.setStatus("Top-down view")
			v.needsRedraw = true
		case '5':
			v.renderer.SetViewMode(ViewFrontSide)
			v.setStatus("Front view")
			v.needsRedraw = true
		case '6':
			v.renderer.SetViewMode(ViewRightSide)
			v.setStatus("Right side view")
			v.needsRedraw = true
		case 'h', 'H', '?':
			v.showHelp()
		case 'r', 'R':
			// Auto-rotate toggle
			v.toggleAutoRotate()
		case 'g', 'G':
			// Toggle grid
			v.toggleGrid()
		case 'e', 'E':
			// Toggle equipment display
			v.toggleEquipment()
		case 'l', 'L':
			// Toggle labels
			v.toggleLabels()
		case 'f', 'F':
			// Next floor (if multi-floor)
			if v.multiFloor && v.currentFloor < len(v.floors)-1 {
				v.currentFloor++
				v.setStatus(fmt.Sprintf("Floor %d", v.currentFloor+1))
				v.needsRedraw = true
			}
		case 'b', 'B':
			// Previous floor (if multi-floor)
			if v.multiFloor && v.currentFloor > 0 {
				v.currentFloor--
				v.setStatus(fmt.Sprintf("Floor %d", v.currentFloor+1))
				v.needsRedraw = true
			}
		}
	}
}

// redraw renders the current view
func (v *InteractiveViewer) redraw() {
	v.screen.Clear()
	w, h := v.screen.Size()

	// Render the 3D view
	v.renderer.Clear()
	if v.multiFloor && v.currentFloor < len(v.floors) {
		v.renderer.RenderFloorPlan(v.floors[v.currentFloor], float64(v.currentFloor)*15)
	} else {
		v.renderer.RenderFloorPlan(v.plan, 0)
	}

	// Get rendered ASCII
	rendered := v.renderer.Render()
	lines := strings.Split(rendered, "\n")

	// Draw ASCII to screen
	style := tcell.StyleDefault
	for y, line := range lines {
		if y >= h-5 {
			break
		}
		for x, ch := range line {
			if x >= w {
				break
			}
			// Apply colors based on character
			cellStyle := v.getCharStyle(ch, style)
			v.screen.SetContent(x, y, ch, nil, cellStyle)
		}
	}

	// Draw status bar
	v.drawStatusBar(h - 4)

	// Draw controls hint
	v.drawControls(h - 2)

	v.screen.Show()
}

// getCharStyle returns appropriate style for a character
func (v *InteractiveViewer) getCharStyle(ch rune, defaultStyle tcell.Style) tcell.Style {
	switch ch {
	case '●': // Outlet
		return defaultStyle.Foreground(tcell.ColorYellow)
	case '▪': // Switch
		return defaultStyle.Foreground(tcell.ColorBlue)
	case '▣': // Panel
		return defaultStyle.Foreground(tcell.ColorRed)
	case '◊': // Light
		return defaultStyle.Foreground(tcell.ColorWhite).Bold(true)
	case '◉': // Sensor
		return defaultStyle.Foreground(tcell.ColorGreen)
	case '✗': // Failed
		return defaultStyle.Foreground(tcell.ColorRed).Bold(true)
	case '⚠': // Warning
		return defaultStyle.Foreground(tcell.ColorYellow).Bold(true)
	case '│', '─', '┌', '┐', '└', '┘', '├', '┤', '┴', '┬', '┼':
		return defaultStyle.Foreground(tcell.ColorDarkGray)
	case '·':
		return defaultStyle.Foreground(tcell.ColorDarkGray).Dim(true)
	default:
		return defaultStyle
	}
}

// drawStatusBar draws the status information
func (v *InteractiveViewer) drawStatusBar(y int) {
	w, _ := v.screen.Size()
	style := tcell.StyleDefault.Background(tcell.ColorDarkBlue).Foreground(tcell.ColorWhite)

	// Clear the line
	for x := 0; x < w; x++ {
		v.screen.SetContent(x, y, ' ', nil, style)
	}

	// Draw status info
	status := fmt.Sprintf(" %s | %s", v.plan.Name, v.renderer.GetViewInfo())
	if v.statusMsg != "" {
		status += fmt.Sprintf(" | %s", v.statusMsg)
	}

	for i, ch := range status {
		if i >= w {
			break
		}
		v.screen.SetContent(i, y, ch, nil, style)
	}
}

// drawControls draws the control hints
func (v *InteractiveViewer) drawControls(y int) {
	w, _ := v.screen.Size()
	style := tcell.StyleDefault.Foreground(tcell.ColorDarkGray)

	controls := " ←→↑↓: Rotate | +/-: Zoom | 1-6: Views | Space: Reset | h: Help | q: Quit"
	for i, ch := range controls {
		if i >= w {
			break
		}
		v.screen.SetContent(i, y, ch, nil, style)
	}
}

// setStatus sets a temporary status message
func (v *InteractiveViewer) setStatus(msg string) {
	v.statusMsg = msg
	v.msgTimeout = time.Now().Add(2 * time.Second)
}

// showHelp displays help screen
func (v *InteractiveViewer) showHelp() {
	v.screen.Clear()
	w, h := v.screen.Size()

	helpText := []string{
		"3D Isometric Viewer - Keyboard Controls",
		"",
		"Navigation:",
		"  ← →     Rotate view left/right",
		"  ↑ ↓     Tilt view up/down",
		"  + -     Zoom in/out",
		"  Space   Reset view",
		"",
		"View Presets:",
		"  1       Isometric view (classic 30°)",
		"  2       Dimetric view",
		"  3       Trimetric view",
		"  4       Top-down view",
		"  5       Front elevation",
		"  6       Right side elevation",
		"",
		"Display Options:",
		"  g       Toggle grid",
		"  e       Toggle equipment",
		"  l       Toggle labels",
		"  r       Toggle auto-rotation",
		"",
		"Multi-Floor (if available):",
		"  f       Next floor",
		"  b       Previous floor",
		"",
		"General:",
		"  h/?     Show this help",
		"  q/ESC   Quit viewer",
		"",
		"Press any key to continue...",
	}

	style := tcell.StyleDefault
	for y, line := range helpText {
		if y >= h {
			break
		}
		for x, ch := range line {
			if x >= w {
				break
			}
			v.screen.SetContent(x, y, ch, nil, style)
		}
	}

	v.screen.Show()

	// Wait for any key
	v.screen.PollEvent()
	v.needsRedraw = true
}

// Placeholder methods for future features
func (v *InteractiveViewer) toggleAutoRotate() {
	v.setStatus("Auto-rotate: Not implemented")
}

func (v *InteractiveViewer) toggleGrid() {
	v.setStatus("Grid toggle: Not implemented")
}

func (v *InteractiveViewer) toggleEquipment() {
	v.setStatus("Equipment toggle: Not implemented")
}

func (v *InteractiveViewer) toggleLabels() {
	v.setStatus("Labels toggle: Not implemented")
}

// AddFloor adds a floor for multi-floor viewing
func (v *InteractiveViewer) AddFloor(floor *models.FloorPlan) {
	v.floors = append(v.floors, floor)
	logger.Debug("Added floor to interactive viewer: %s", floor.Name)
}

// Stop stops the interactive viewer
func (v *InteractiveViewer) Stop() {
	v.running = false
}
