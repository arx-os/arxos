package core

// SymbolSet defines the characters used for visualization
type SymbolSet struct {
	// Bar chart symbols
	BarFull    rune
	BarEmpty   rune
	BarPartial []rune // For fractional bars (Unicode only)

	// Box drawing
	BoxTopLeft     rune
	BoxTopRight    rune
	BoxBottomLeft  rune
	BoxBottomRight rune
	BoxHoriz       rune
	BoxVert        rune
	BoxCross       rune
	BoxVertRight   rune
	BoxVertLeft    rune
	BoxHorizDown   rune
	BoxHorizUp     rune

	// Tree symbols
	TreeBranch rune
	TreeMid    rune
	TreeEnd    rune
	TreeVert   rune

	// Status indicators
	CheckMark rune
	Warning   rune
	Error     rune
	Info      rune
	Bullet    rune

	// Arrows
	ArrowUp    rune
	ArrowDown  rune
	ArrowLeft  rune
	ArrowRight rune

	// Graph elements
	GraphLine     rune
	GraphDot      rune
	Sparkline     []rune // Different heights for sparklines
	BlockElements []rune // Different fill levels for blocks
}

// ASCIISymbols provides ASCII-only symbols for basic terminals
var ASCIISymbols = SymbolSet{
	// Bar chart
	BarFull:  '#',
	BarEmpty: '-',

	// Box drawing (ASCII)
	BoxTopLeft:     '+',
	BoxTopRight:    '+',
	BoxBottomLeft:  '+',
	BoxBottomRight: '+',
	BoxHoriz:       '-',
	BoxVert:        '|',
	BoxCross:       '+',
	BoxVertRight:   '+',
	BoxVertLeft:    '+',
	BoxHorizDown:   '+',
	BoxHorizUp:     '+',

	// Tree (ASCII)
	TreeBranch: '|',
	TreeMid:    '+',
	TreeEnd:    '+',
	TreeVert:   '|',

	// Status (ASCII)
	CheckMark: 'v',
	Warning:   '!',
	Error:     'X',
	Info:      'i',
	Bullet:    '*',

	// Arrows (ASCII)
	ArrowUp:    '^',
	ArrowDown:  'v',
	ArrowLeft:  '<',
	ArrowRight: '>',

	// Graph (ASCII)
	GraphLine: '-',
	GraphDot:  '*',
}

// UnicodeSymbols provides Unicode symbols for modern terminals
var UnicodeSymbols = SymbolSet{
	// Bar chart
	BarFull:    '█',
	BarEmpty:   '░',
	BarPartial: []rune{'▏', '▎', '▍', '▌', '▋', '▊', '▉'},

	// Box drawing (Unicode)
	BoxTopLeft:     '┌',
	BoxTopRight:    '┐',
	BoxBottomLeft:  '└',
	BoxBottomRight: '┘',
	BoxHoriz:       '─',
	BoxVert:        '│',
	BoxCross:       '┼',
	BoxVertRight:   '├',
	BoxVertLeft:    '┤',
	BoxHorizDown:   '┬',
	BoxHorizUp:     '┴',

	// Tree (Unicode)
	TreeBranch: '├',
	TreeMid:    '├',
	TreeEnd:    '└',
	TreeVert:   '│',

	// Status (Unicode)
	CheckMark: '✓',
	Warning:   '⚠',
	Error:     '✗',
	Info:      'ℹ',
	Bullet:    '•',

	// Arrows (Unicode)
	ArrowUp:    '↑',
	ArrowDown:  '↓',
	ArrowLeft:  '←',
	ArrowRight: '→',

	// Graph (Unicode)
	GraphLine: '─',
	GraphDot:  '●',

	// Sparklines (8 levels)
	Sparkline: []rune{'▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'},

	// Block elements for fine-grained fills
	BlockElements: []rune{'░', '▒', '▓', '█'},
}

// BoldUnicodeSymbols provides bold Unicode symbols
var BoldUnicodeSymbols = SymbolSet{
	// Bar chart
	BarFull:    '█',
	BarEmpty:   '░',
	BarPartial: []rune{'▏', '▎', '▍', '▌', '▋', '▊', '▉'},

	// Box drawing (Bold)
	BoxTopLeft:     '┏',
	BoxTopRight:    '┓',
	BoxBottomLeft:  '┗',
	BoxBottomRight: '┛',
	BoxHoriz:       '━',
	BoxVert:        '┃',
	BoxCross:       '╋',
	BoxVertRight:   '┣',
	BoxVertLeft:    '┫',
	BoxHorizDown:   '┳',
	BoxHorizUp:     '┻',

	// Tree (Bold)
	TreeBranch: '┣',
	TreeMid:    '┣',
	TreeEnd:    '┗',
	TreeVert:   '┃',

	// Status (Unicode)
	CheckMark: '✓',
	Warning:   '⚠',
	Error:     '✗',
	Info:      'ℹ',
	Bullet:    '●',

	// Arrows (Bold)
	ArrowUp:    '⬆',
	ArrowDown:  '⬇',
	ArrowLeft:  '⬅',
	ArrowRight: '➡',

	// Graph (Unicode)
	GraphLine: '━',
	GraphDot:  '●',

	// Sparklines (8 levels)
	Sparkline: []rune{'▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'},

	// Block elements
	BlockElements: []rune{'░', '▒', '▓', '█'},
}

// IsEmpty checks if the symbol set is empty
func (s SymbolSet) IsEmpty() bool {
	return s.BarFull == 0 && s.BarEmpty == 0
}

// GetSparklineChar returns the appropriate sparkline character for a value
func (s SymbolSet) GetSparklineChar(value float64) rune {
	if len(s.Sparkline) == 0 {
		// Fallback to simple ASCII
		if value < 0.25 {
			return '.'
		} else if value < 0.5 {
			return '-'
		} else if value < 0.75 {
			return '='
		} else {
			return '#'
		}
	}

	// Map value (0-1) to sparkline index
	if value < 0 {
		value = 0
	}
	if value > 1 {
		value = 1
	}

	index := int(value * float64(len(s.Sparkline)-1))
	if index >= len(s.Sparkline) {
		index = len(s.Sparkline) - 1
	}

	return s.Sparkline[index]
}

// GetBlockChar returns the appropriate block character for a value
func (s SymbolSet) GetBlockChar(value float64) rune {
	if len(s.BlockElements) == 0 {
		// Fallback to simple ASCII
		if value < 0.25 {
			return ' '
		} else if value < 0.5 {
			return '.'
		} else if value < 0.75 {
			return 'o'
		} else {
			return '#'
		}
	}

	// Map value (0-1) to block index
	if value < 0 {
		value = 0
	}
	if value > 1 {
		value = 1
	}

	index := int(value * float64(len(s.BlockElements)-1))
	if index >= len(s.BlockElements) {
		index = len(s.BlockElements) - 1
	}

	return s.BlockElements[index]
}