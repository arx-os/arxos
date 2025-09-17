package core

import (
	"strings"
)

// Canvas represents a drawable terminal area
type Canvas struct {
	cells  [][]Cell
	Width  int
	Height int
}

// Cell represents a single character in the canvas
type Cell struct {
	Char       rune
	Foreground Color
	Background Color
	Bold       bool
	Dim        bool
	Underline  bool
}

// NewCanvas creates a new canvas with the specified dimensions
func NewCanvas(width, height int) *Canvas {
	cells := make([][]Cell, height)
	for y := 0; y < height; y++ {
		cells[y] = make([]Cell, width)
		for x := 0; x < width; x++ {
			cells[y][x] = Cell{
				Char:       ' ',
				Foreground: NoColor,
				Background: NoColor,
			}
		}
	}

	return &Canvas{
		cells:  cells,
		Width:  width,
		Height: height,
	}
}

// SetCell sets a cell at the specified position
func (c *Canvas) SetCell(x, y int, cell Cell) {
	if x >= 0 && x < c.Width && y >= 0 && y < c.Height {
		c.cells[y][x] = cell
	}
}

// GetCell gets the cell at the specified position
func (c *Canvas) GetCell(x, y int) Cell {
	if x >= 0 && x < c.Width && y >= 0 && y < c.Height {
		return c.cells[y][x]
	}
	return Cell{Char: ' '}
}

// DrawText draws text starting at the specified position
func (c *Canvas) DrawText(x, y int, text string, fg, bg Color) {
	for i, ch := range text {
		c.SetCell(x+i, y, Cell{
			Char:       ch,
			Foreground: fg,
			Background: bg,
		})
	}
}

// DrawBox draws a box using the specified symbol set
func (c *Canvas) DrawBox(x, y, width, height int, symbols SymbolSet, fg, bg Color) {
	// Top border
	c.SetCell(x, y, Cell{Char: symbols.BoxTopLeft, Foreground: fg, Background: bg})
	c.SetCell(x+width-1, y, Cell{Char: symbols.BoxTopRight, Foreground: fg, Background: bg})
	for i := 1; i < width-1; i++ {
		c.SetCell(x+i, y, Cell{Char: symbols.BoxHoriz, Foreground: fg, Background: bg})
	}

	// Bottom border
	c.SetCell(x, y+height-1, Cell{Char: symbols.BoxBottomLeft, Foreground: fg, Background: bg})
	c.SetCell(x+width-1, y+height-1, Cell{Char: symbols.BoxBottomRight, Foreground: fg, Background: bg})
	for i := 1; i < width-1; i++ {
		c.SetCell(x+i, y+height-1, Cell{Char: symbols.BoxHoriz, Foreground: fg, Background: bg})
	}

	// Left and right borders
	for i := 1; i < height-1; i++ {
		c.SetCell(x, y+i, Cell{Char: symbols.BoxVert, Foreground: fg, Background: bg})
		c.SetCell(x+width-1, y+i, Cell{Char: symbols.BoxVert, Foreground: fg, Background: bg})
	}
}

// DrawHorizontalBar draws a horizontal bar
func (c *Canvas) DrawHorizontalBar(x, y int, width int, fillRatio float64, symbols SymbolSet, fg, bg Color) {
	if fillRatio < 0 {
		fillRatio = 0
	}
	if fillRatio > 1 {
		fillRatio = 1
	}

	filled := int(float64(width) * fillRatio)

	// Draw filled portion
	for i := 0; i < filled; i++ {
		c.SetCell(x+i, y, Cell{
			Char:       symbols.BarFull,
			Foreground: fg,
			Background: bg,
		})
	}

	// Draw fractional part if Unicode is available and we have partial symbols
	if filled < width && len(symbols.BarPartial) > 0 {
		fraction := (float64(width) * fillRatio) - float64(filled)
		partialIndex := int(fraction * float64(len(symbols.BarPartial)))
		if partialIndex >= len(symbols.BarPartial) {
			partialIndex = len(symbols.BarPartial) - 1
		}
		if partialIndex > 0 {
			c.SetCell(x+filled, y, Cell{
				Char:       symbols.BarPartial[partialIndex],
				Foreground: fg,
				Background: bg,
			})
			filled++
		}
	}

	// Draw empty portion
	for i := filled; i < width; i++ {
		c.SetCell(x+i, y, Cell{
			Char:       symbols.BarEmpty,
			Foreground: fg,
			Background: bg,
		})
	}
}

// DrawVerticalBar draws a vertical bar
func (c *Canvas) DrawVerticalBar(x, y int, height int, fillRatio float64, symbols SymbolSet, fg, bg Color) {
	if fillRatio < 0 {
		fillRatio = 0
	}
	if fillRatio > 1 {
		fillRatio = 1
	}

	filled := int(float64(height) * fillRatio)

	// Draw from bottom up (typical for bar charts)
	for i := 0; i < height; i++ {
		cell := Cell{Background: bg}
		if i < filled {
			cell.Char = symbols.BarFull
			cell.Foreground = fg
		} else {
			cell.Char = symbols.BarEmpty
			cell.Foreground = fg
		}
		c.SetCell(x, y+height-1-i, cell)
	}
}

// Clear clears the canvas
func (c *Canvas) Clear() {
	for y := 0; y < c.Height; y++ {
		for x := 0; x < c.Width; x++ {
			c.cells[y][x] = Cell{
				Char:       ' ',
				Foreground: NoColor,
				Background: NoColor,
			}
		}
	}
}

// ToString converts the canvas to a string (without colors)
func (c *Canvas) ToString() string {
	var output strings.Builder

	for y := 0; y < c.Height; y++ {
		for x := 0; x < c.Width; x++ {
			output.WriteRune(c.cells[y][x].Char)
		}
		if y < c.Height-1 {
			output.WriteRune('\n')
		}
	}

	return output.String()
}