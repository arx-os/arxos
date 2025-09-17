# ArxOS Terminal Data Visualization Architecture

## Executive Summary

This document outlines the comprehensive design and architecture for integrating D3-style data visualizations directly into the ArxOS terminal interface. By leveraging modern terminal capabilities (Unicode, 256 colors, box-drawing characters), ArxOS will provide rich data visualization without requiring a web browser or 3D interface.

## Core Philosophy

- **Terminal-First**: All visualizations must work in a standard terminal emulator
- **Progressive Enhancement**: Use colors and Unicode when available, fallback to ASCII
- **Actionable Insights**: Every visualization should lead to executable commands
- **Performance**: Visualizations should render in <100ms for responsive feel
- **Accessibility**: Support screen readers and monochrome displays

## Architecture Overview

```
┌────────────────────────────────────────────────────────┐
│                    CLI Commands                        │
│  (query, monitor, analyze, report, dashboard)          │
└─────────────────────┬──────────────────────────────────┘
                      │
┌─────────────────────▼──────────────────────────────────┐
│              Visualization Engine                       │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Renderer   │  │  Data Mapper │  │ Layout Engine│ │
│  │   - ASCII    │  │  - Aggregator│  │  - Grid      │ │
│  │   - Unicode  │  │  - Normalizer│  │  - Flow      │ │
│  │   - Colors   │  │  - Sampler   │  │  - Tree      │ │
│  └─────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────┬──────────────────────────────────┘
                      │
┌─────────────────────▼──────────────────────────────────┐
│                Terminal Output Layer                    │
│         (termenv for capability detection)              │
└─────────────────────────────────────────────────────────┘
```

## Package Structure

```
internal/visualization/
├── core/
│   ├── renderer.go      # Base renderer interface
│   ├── canvas.go        # Terminal canvas abstraction
│   ├── colors.go        # Color schemes and theming
│   └── symbols.go       # Unicode/ASCII symbol sets
├── charts/
│   ├── bar.go           # Bar charts and histograms
│   ├── line.go          # Line charts and sparklines
│   ├── heatmap.go       # 2D heatmaps and matrices
│   ├── tree.go          # Tree and hierarchy views
│   ├── gauge.go         # Gauges and progress indicators
│   ├── table.go         # Enhanced data tables
│   └── sankey.go        # Flow diagrams (ASCII-simplified)
├── layouts/
│   ├── dashboard.go     # Multi-chart dashboard layouts
│   ├── grid.go          # Grid-based positioning
│   └── responsive.go    # Terminal size adaptation
├── data/
│   ├── transformer.go   # Data transformation pipeline
│   ├── aggregator.go    # Time-series aggregation
│   └── sampler.go       # Data sampling for large datasets
└── examples/
    └── demo.go          # Interactive demo of all charts
```

## Core Components

### 1. Renderer Engine

```go
package visualization

type Renderer interface {
    // Core rendering method
    Render(data DataSet, options RenderOptions) (Canvas, error)

    // Get dimensions
    GetDimensions() (width, height int)

    // Capability detection
    SupportsUnicode() bool
    SupportsColors() bool
    Supports256Colors() bool
    SupportsTrueColor() bool
}

type RenderOptions struct {
    Width        int
    Height       int
    ColorScheme  ColorScheme
    SymbolSet    SymbolSet  // ASCII, Unicode, or Custom
    Title        string
    ShowLegend   bool
    ShowAxes     bool
    Interactive  bool        // For future: mouse support
}

type Canvas struct {
    cells    [][]Cell
    width    int
    height   int
}

type Cell struct {
    Char       rune
    Foreground Color
    Background Color
    Bold       bool
    Dim        bool
}
```

### 2. Chart Types

#### Bar Chart
```go
type BarChart struct {
    renderer Renderer
}

func (b *BarChart) Render(data []DataPoint) string {
    // Example output:
    // Equipment Status by Floor:
    // Floor 5  ████████████████░░░░ 80% (40/50)
    // Floor 4  ███████████████████░ 95% (38/40)
    // Floor 3  █████████░░░░░░░░░░░ 45% (27/60)
}
```

#### Sparkline
```go
type Sparkline struct {
    renderer Renderer
}

func (s *Sparkline) Render(values []float64) string {
    // Example output:
    // Power: ▁▂▃▅▇█▇▅▃▃▂▁▁▂▃▅▇█▇▅▃▂▁▁ (24hr)
}
```

#### Heatmap
```go
type Heatmap struct {
    renderer Renderer
}

func (h *Heatmap) Render(matrix [][]float64) string {
    // Example output:
    // Energy Usage (kWh/sqft):
    //      A    B    C    D    E
    // 5  [█▓▓][▒▒▒][░░░][▒▒▒][▓▓█]
    // 4  [▒▒▒][░░░][   ][░░░][▒▒▓]
    // 3  [░░░][   ][   ][░░░][▒▒▒]
}
```

#### Tree View
```go
type TreeView struct {
    renderer Renderer
}

func (t *TreeView) Render(root *TreeNode) string {
    // Example output:
    // ARXOS-001/
    // ├─ HVAC/ (92% efficient)
    // │  ├─ AHU-01 ✓ operational
    // │  └─ AHU-02 ⚠ maintenance
    // └─ Power/ (98% uptime)
    //    └─ PANEL-A ✓ 45A/100A
}
```

### 3. Symbol Sets

```go
type SymbolSet struct {
    // Bar chart symbols
    BarFull      rune
    BarEmpty     rune
    BarPartial   []rune  // For fractional bars

    // Box drawing
    BoxTopLeft   rune
    BoxTopRight  rune
    BoxHoriz     rune
    BoxVert      rune

    // Tree symbols
    TreeBranch   rune
    TreeMid      rune
    TreeEnd      rune

    // Status indicators
    CheckMark    rune
    Warning      rune
    Error        rune
    Info         rune
}

var ASCIISymbols = SymbolSet{
    BarFull:    '#',
    BarEmpty:   '-',
    BoxTopLeft: '+',
    BoxHoriz:   '-',
    TreeBranch: '|',
    TreeMid:    '+-',
    TreeEnd:    '+-',
    CheckMark:  '[OK]',
    Warning:    '[!]',
    Error:      '[X]',
}

var UnicodeSymbols = SymbolSet{
    BarFull:    '█',
    BarEmpty:   '░',
    BarPartial: []rune{'▏','▎','▍','▌','▋','▊','▉'},
    BoxTopLeft: '┌',
    BoxHoriz:   '─',
    TreeBranch: '│',
    TreeMid:    '├─',
    TreeEnd:    '└─',
    CheckMark:  '✓',
    Warning:    '⚠',
    Error:      '✗',
}
```

### 4. Color Schemes

```go
type ColorScheme struct {
    Primary     Color
    Secondary   Color
    Success     Color
    Warning     Color
    Error       Color
    Info        Color

    // Gradient colors for heatmaps
    GradientLow  Color
    GradientMid  Color
    GradientHigh Color

    // Chart-specific
    BarColors    []Color
    LineColors   []Color
}

var DefaultScheme = ColorScheme{
    Primary:   Blue,
    Success:   Green,
    Warning:   Yellow,
    Error:     Red,
    Info:      Cyan,
}

var MonochromeScheme = ColorScheme{
    // All colors map to different patterns/intensities
}
```

## Integration Points

### 1. Query Command Enhancement

```bash
# New visualization flags for query command
arx query --building ARXOS-001 --visualize bar --metric energy
arx query --building ARXOS-001 --visualize heatmap --metric temperature
arx query --building ARXOS-001 --visualize sparkline --metric occupancy --period 24h
```

### 2. New Monitor Command

```bash
# Real-time monitoring with auto-refreshing visualizations
arx monitor --building ARXOS-001 --dashboard energy
arx monitor --equipment HVAC/* --refresh 5s
```

### 3. New Analyze Command

```bash
# Deep analysis with multiple visualizations
arx analyze efficiency --building ARXOS-001 --period month
arx analyze patterns --system HVAC --correlation temperature,energy
```

### 4. Report Command

```bash
# Generate terminal-based reports with embedded visualizations
arx report daily --building ARXOS-001 --output terminal
arx report maintenance --upcoming 30d --visualize gantt
```

### 5. Dashboard Command

```bash
# Full terminal dashboard with multiple live visualizations
arx dashboard
arx dashboard --layout energy-focus
arx dashboard --building ARXOS-001 --floor 3
```

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] Set up `internal/visualization` package structure
- [ ] Implement base `Renderer` interface
- [ ] Create `Canvas` abstraction for terminal drawing
- [ ] Add terminal capability detection (colors, Unicode)
- [ ] Implement ASCII and Unicode symbol sets

### Phase 2: Basic Charts (Week 3-4)
- [ ] Implement Bar Chart renderer
- [ ] Implement Sparkline renderer
- [ ] Implement basic Table with borders
- [ ] Add color scheme support
- [ ] Create unit tests for each chart type

### Phase 3: Advanced Visualizations (Week 5-6)
- [ ] Implement Heatmap renderer
- [ ] Implement Tree View for hierarchies
- [ ] Implement Gauge/Progress indicators
- [ ] Add Gantt chart for maintenance schedules
- [ ] Implement simplified Sankey diagram

### Phase 4: Integration (Week 7-8)
- [ ] Enhance `query` command with `--visualize` flag
- [ ] Implement `monitor` command for real-time views
- [ ] Create `analyze` command for correlations
- [ ] Add `report` command for formatted reports
- [ ] Implement `dashboard` command

### Phase 5: Polish & Optimization (Week 9-10)
- [ ] Add responsive layout system
- [ ] Optimize rendering performance
- [ ] Add configuration file for preferences
- [ ] Create interactive demo/tutorial
- [ ] Write comprehensive documentation

## Example Implementations

### 1. Bar Chart Example

```go
func RenderBarChart(data map[string]float64, width int) string {
    var output strings.Builder
    maxValue := findMax(data)
    barWidth := width - 20 // Leave room for labels

    for label, value := range data {
        percentage := value / maxValue
        filled := int(percentage * float64(barWidth))
        empty := barWidth - filled

        bar := strings.Repeat("█", filled) + strings.Repeat("░", empty)
        output.WriteString(fmt.Sprintf("%-10s %s %.1f%%\n",
            label, bar, percentage*100))
    }

    return output.String()
}
```

### 2. Sparkline Example

```go
func RenderSparkline(values []float64) string {
    sparks := []rune{'▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'}
    min, max := findMinMax(values)

    var output strings.Builder
    for _, v := range values {
        index := int((v - min) / (max - min) * 7)
        if index > 7 { index = 7 }
        if index < 0 { index = 0 }
        output.WriteRune(sparks[index])
    }

    return output.String()
}
```

### 3. Dashboard Layout Example

```go
func RenderDashboard(building *Building) string {
    term := termenv.NewOutput(os.Stdout)
    width, height := getTerminalSize()

    // Create layout grid
    grid := NewGrid(width, height, 2, 2) // 2x2 grid

    // Render each quadrant
    grid.SetCell(0, 0, RenderEnergyGauge(building))
    grid.SetCell(0, 1, RenderStatusBars(building))
    grid.SetCell(1, 0, RenderAlertsList(building))
    grid.SetCell(1, 1, RenderSparklines(building))

    return grid.Render()
}
```

## Terminal Capability Detection

```go
func DetectCapabilities() TerminalCaps {
    term := termenv.NewOutput(os.Stdout)

    return TerminalCaps{
        Colors:      term.Profile != termenv.Ascii,
        Colors256:   term.Profile >= termenv.ANSI256,
        TrueColor:   term.Profile >= termenv.TrueColor,
        Unicode:     canDisplayUnicode(),
        Width:       getWidth(),
        Height:      getHeight(),
        Interactive: isatty.IsTerminal(os.Stdout.Fd()),
    }
}
```

## Configuration

Users can customize visualizations via `~/.arxos/config/visualization.yaml`:

```yaml
visualization:
  # Symbol preferences
  symbols: unicode  # ascii, unicode, or nerd-fonts

  # Color preferences
  colors: auto      # auto, 16, 256, true, or none
  theme: default    # default, high-contrast, colorblind, monochrome

  # Chart defaults
  defaults:
    bar_chart:
      show_values: true
      show_percentage: true
    sparkline:
      width: 20
      show_trend: true
    heatmap:
      gradient: blue-red  # blue-red, green-red, grayscale

  # Dashboard layouts
  dashboards:
    default:
      layout: "2x2"
      refresh: 5s
      widgets:
        - type: gauge
          metric: energy
        - type: bars
          metric: equipment_status
        - type: sparkline
          metric: temperature
        - type: alerts
          limit: 5
```

## Testing Strategy

### Unit Tests
- Test each chart type with various data inputs
- Test terminal capability detection
- Test color scheme application
- Test responsive sizing

### Integration Tests
- Test command integration (`query --visualize`)
- Test dashboard composition
- Test real-time updates

### Visual Regression Tests
- Capture output snapshots
- Compare against golden files
- Flag any unexpected changes

## Performance Targets

- **Initial Render**: <100ms for any single chart
- **Dashboard Render**: <200ms for full dashboard
- **Real-time Update**: <50ms for incremental updates
- **Memory Usage**: <10MB for typical dashboard
- **CPU Usage**: <5% during monitoring

## Accessibility Considerations

1. **Screen Reader Support**
   - Provide text descriptions for all charts
   - Use semantic markers for navigation

2. **Monochrome Support**
   - Use patterns in addition to colors
   - Ensure sufficient contrast

3. **Keyboard Navigation**
   - All interactive elements accessible via keyboard
   - Clear focus indicators

## Future Enhancements

1. **Mouse Support** (using terminal mouse protocols)
   - Click on chart elements for details
   - Hover tooltips

2. **Chart Export**
   - Save as ASCII art
   - Export data as CSV
   - Generate HTML reports

3. **Custom Widgets**
   - Plugin system for custom visualizations
   - User-defined chart types

4. **Animation**
   - Smooth transitions for value changes
   - Loading indicators
   - Alert pulses

## Dependencies

### Required
- `github.com/muesli/termenv` - Terminal capability detection
- `github.com/pterm/pterm` - Enhanced terminal output
- `golang.org/x/term` - Terminal size detection

### Optional
- `github.com/guptarohit/asciigraph` - ASCII line graphs
- `github.com/aybabtme/uniplot` - Unicode plots

## Success Metrics

1. **User Adoption**
   - 80% of users use at least one visualization daily
   - Positive feedback on visibility of system state

2. **Performance**
   - All charts render within target times
   - No noticeable lag during interaction

3. **Coverage**
   - All major data types have visualization options
   - Dashboards available for all common workflows

## Conclusion

This terminal visualization architecture positions ArxOS as a unique building management system that provides rich, actionable insights without requiring a web browser or 3D interface. By focusing on terminal excellence, we differentiate from traditional BIM tools while providing superior operational efficiency for building managers and technicians.