// Package ascii provides terminal control for interactive viewing
package ascii

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"runtime"
	"strings"
	"time"

	"github.com/arxos/arxos/cmd/models"
)

// TerminalController handles keyboard input and display updates
type TerminalController struct {
	Viewer       *InteractiveViewer
	Running      bool
	RefreshRate  time.Duration
	InputBuffer  chan rune
	CommandMode  bool
	CommandBuffer string
}

// NewTerminalController creates a controller for interactive viewing
func NewTerminalController() *TerminalController {
	// Get terminal dimensions
	width, height := getTerminalSize()
	
	return &TerminalController{
		Viewer:      NewInteractiveViewer(width, height),
		RefreshRate: time.Millisecond * 16, // ~60 FPS
		InputBuffer: make(chan rune, 10),
		Running:     true,
	}
}

// Run starts the interactive terminal session
func (tc *TerminalController) Run(path string, objects []*models.ArxObject) error {
	// Initialize viewer
	tc.Viewer.CurrentPath = path
	tc.Viewer.Objects = objects
	
	// Set up terminal
	if err := tc.setupTerminal(); err != nil {
		return err
	}
	defer tc.restoreTerminal()
	
	// Start input handler in goroutine
	go tc.handleInput()
	
	// Main render loop
	ticker := time.NewTicker(tc.RefreshRate)
	defer ticker.Stop()
	
	for tc.Running {
		select {
		case <-ticker.C:
			// Update animations
			tc.Viewer.Update()
			
			// Render frame
			output := tc.Viewer.Render()
			fmt.Print(output)
			
		case input := <-tc.InputBuffer:
			// Process input
			tc.processInput(input)
		}
	}
	
	return nil
}

// handleInput reads keyboard input in raw mode
func (tc *TerminalController) handleInput() {
	reader := bufio.NewReader(os.Stdin)
	
	for tc.Running {
		char, err := reader.ReadByte()
		if err != nil {
			continue
		}
		
		// Handle escape sequences for arrow keys
		if char == 27 { // ESC
			if next, err := reader.ReadByte(); err == nil && next == '[' {
				if arrow, err := reader.ReadByte(); err == nil {
					switch arrow {
					case 'A': // Up arrow
						tc.InputBuffer <- '↑'
					case 'B': // Down arrow
						tc.InputBuffer <- '↓'
					case 'C': // Right arrow
						tc.InputBuffer <- '→'
					case 'D': // Left arrow
						tc.InputBuffer <- '←'
					}
					continue
				}
			}
		}
		
		tc.InputBuffer <- rune(char)
	}
}

// processInput handles user input
func (tc *TerminalController) processInput(input rune) {
	// Command mode handling
	if tc.CommandMode {
		tc.handleCommandMode(input)
		return
	}
	
	// Normal mode navigation
	switch input {
	case '+', '=':
		// Zoom in
		tc.Viewer.ZoomIn()
		
	case '-', '_':
		// Zoom out
		tc.Viewer.ZoomOut()
		
	case '↑', 'w', 'W':
		// Pan up
		tc.Viewer.Pan(0, -1)
		
	case '↓', 's', 'S':
		// Pan down
		tc.Viewer.Pan(0, 1)
		
	case '←', 'a', 'A':
		// Pan left
		tc.Viewer.Pan(-1, 0)
		
	case '→', 'd', 'D':
		// Pan right
		tc.Viewer.Pan(1, 0)
		
	case '0', '1', '2', '3', '4', '5', '6':
		// Direct zoom level selection
		level := ZoomLevel(input - '0')
		tc.Viewer.ZoomToLevel(level)
		
	case '/':
		// Enter search/command mode
		tc.CommandMode = true
		tc.CommandBuffer = ""
		
	case 'c', 'C':
		// Center on current path
		tc.Viewer.CenterOn(tc.Viewer.CurrentPath)
		
	case 'r', 'R':
		// Reset view
		tc.resetView()
		
	case 'h', 'H', '?':
		// Show help
		tc.showHelp()
		
	case 'q', 'Q', 27: // ESC
		// Quit
		tc.Running = false
		
	case ' ':
		// Toggle animation pause
		tc.Viewer.AnimationActive = !tc.Viewer.AnimationActive
		
	case 'f', 'F':
		// Toggle fullscreen (if supported)
		tc.toggleFullscreen()
	}
}

// handleCommandMode processes command input
func (tc *TerminalController) handleCommandMode(input rune) {
	switch input {
	case 27: // ESC
		// Cancel command mode
		tc.CommandMode = false
		tc.CommandBuffer = ""
		
	case '\n', '\r':
		// Execute command
		tc.executeCommand(tc.CommandBuffer)
		tc.CommandMode = false
		tc.CommandBuffer = ""
		
	case 127, 8: // Backspace
		if len(tc.CommandBuffer) > 0 {
			tc.CommandBuffer = tc.CommandBuffer[:len(tc.CommandBuffer)-1]
		}
		
	default:
		// Add to command buffer
		tc.CommandBuffer += string(input)
	}
}

// executeCommand processes search and navigation commands
func (tc *TerminalController) executeCommand(cmd string) {
	if strings.HasPrefix(cmd, "/") {
		// Search for object
		query := cmd[1:]
		tc.searchAndFocus(query)
	} else if strings.HasPrefix(cmd, ":") {
		// Navigate to path
		path := cmd[1:]
		tc.navigateTo(path)
	}
}

// searchAndFocus finds and centers on an object
func (tc *TerminalController) searchAndFocus(query string) {
	for _, obj := range tc.Viewer.Objects {
		if strings.Contains(strings.ToLower(obj.Name), strings.ToLower(query)) ||
			strings.Contains(strings.ToLower(obj.Path), strings.ToLower(query)) {
			tc.Viewer.centerOnObject(obj)
			tc.Viewer.CurrentPath = obj.Path
			
			// Zoom to appropriate level for object type
			tc.autoZoomForObject(obj)
			break
		}
	}
}

// navigateTo moves to a specific path
func (tc *TerminalController) navigateTo(path string) {
	if !strings.HasPrefix(path, "/") {
		// Relative path
		path = tc.Viewer.CurrentPath + "/" + path
	}
	
	if err := tc.Viewer.CenterOn(path); err == nil {
		tc.Viewer.CurrentPath = path
		
		// Find object and auto-zoom
		if obj := tc.Viewer.findObjectByPath(path); obj != nil {
			tc.autoZoomForObject(obj)
		}
	}
}

// autoZoomForObject sets appropriate zoom level based on object type
func (tc *TerminalController) autoZoomForObject(obj *models.ArxObject) {
	switch obj.Type {
	case "building":
		tc.Viewer.ZoomToLevel(ZoomBuilding)
	case "floor":
		tc.Viewer.ZoomToLevel(ZoomFloor)
	case "room":
		tc.Viewer.ZoomToLevel(ZoomRoom)
	case "equipment", "panel":
		tc.Viewer.ZoomToLevel(ZoomEquipment)
	case "component", "circuit":
		tc.Viewer.ZoomToLevel(ZoomComponent)
	case "chip", "sensor":
		tc.Viewer.ZoomToLevel(ZoomChip)
	default:
		tc.Viewer.ZoomToLevel(ZoomRoom)
	}
}

// resetView resets viewport to default
func (tc *TerminalController) resetView() {
	tc.Viewer.ViewportX = 0
	tc.Viewer.ViewportY = 0
	tc.Viewer.TargetX = 0
	tc.Viewer.TargetY = 0
	tc.Viewer.CurrentZoom = ZoomFloor
	tc.Viewer.TargetZoom = ZoomFloor
	tc.Viewer.FocusObject = nil
}

// showHelp displays help overlay
func (tc *TerminalController) showHelp() {
	help := `
╔══════════════════════════════════════════════════════════════╗
║                    ARXOS ASCII-BIM CONTROLS                  ║
╠══════════════════════════════════════════════════════════════╣
║  Navigation:                                                 ║
║    +/-        Zoom in/out                                   ║
║    0-6        Jump to zoom level                            ║
║    ↑↓←→/WASD  Pan viewport                                  ║
║    c          Center on current object                      ║
║    r          Reset view                                    ║
║                                                              ║
║  Search:                                                     ║
║    /text      Search for object                             ║
║    :path      Navigate to path                              ║
║                                                              ║
║  Display:                                                    ║
║    Space      Pause/resume animation                        ║
║    f          Toggle fullscreen                             ║
║    h/?        Show this help                                ║
║    q/ESC      Quit                                          ║
╚══════════════════════════════════════════════════════════════╝

Press any key to continue...
`
	fmt.Print(help)
	
	// Wait for input
	reader := bufio.NewReader(os.Stdin)
	reader.ReadByte()
}

// toggleFullscreen attempts to maximize terminal window
func (tc *TerminalController) toggleFullscreen() {
	// Platform-specific fullscreen commands
	switch runtime.GOOS {
	case "darwin":
		// macOS: Use AppleScript to toggle fullscreen
		cmd := exec.Command("osascript", "-e", `tell application "Terminal" to set bounds of front window to {0, 0, 1440, 900}`)
		cmd.Run()
	case "linux":
		// Linux: Send F11 key to terminal
		fmt.Print("\033[11~")
	case "windows":
		// Windows: Use mode command
		cmd := exec.Command("cmd", "/c", "mode con: cols=120 lines=50")
		cmd.Run()
	}
}

// setupTerminal configures terminal for raw input
func (tc *TerminalController) setupTerminal() error {
	// Platform-specific terminal setup
	switch runtime.GOOS {
	case "darwin", "linux":
		// Unix-like systems: disable input buffering
		cmd := exec.Command("stty", "-F", "/dev/tty", "cbreak", "min", "1", "-echo")
		return cmd.Run()
	default:
		// Windows and others: basic setup
		return nil
	}
}

// restoreTerminal restores normal terminal mode
func (tc *TerminalController) restoreTerminal() {
	// Clear screen
	fmt.Print("\033[2J\033[H")
	
	// Platform-specific terminal restore
	switch runtime.GOOS {
	case "darwin", "linux":
		// Unix-like systems: restore input buffering
		cmd := exec.Command("stty", "-F", "/dev/tty", "sane")
		cmd.Run()
	}
}

// getTerminalSize returns terminal dimensions
func getTerminalSize() (int, int) {
	// Try to get actual terminal size
	cmd := exec.Command("stty", "size")
	cmd.Stdin = os.Stdin
	out, err := cmd.Output()
	
	if err == nil {
		var h, w int
		fmt.Sscanf(string(out), "%d %d", &h, &w)
		if w > 0 && h > 0 {
			return w, h - 3 // Leave room for header/footer
		}
	}
	
	// Default size if detection fails
	return 80, 24
}