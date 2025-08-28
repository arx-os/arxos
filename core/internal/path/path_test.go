package path

import (
	"testing"
)

func TestNormalize(t *testing.T) {
	testCases := []struct {
		input    string
		expected string
	}{
		// Basic normalization
		{"", "/"},
		{"/", "/"},
		{"electrical/panel", "/electrical/panel"},
		{"/electrical/panel", "/electrical/panel"},
		
		// Colon separator
		{"building:demo", "/building/demo"},
		{"floor:1:room:101", "/floor/1/room/101"},
		
		// Underscore handling
		{"building_demo", "/building/demo"},
		{"floor_1", "/floor/1"},
		{"panel_a", "/panel_a"}, // Preserve underscore within name
		
		// Mixed separators
		{"building:demo/floor_1", "/building/demo/floor/1"},
		
		// Plural to singular
		{"/buildings/demo", "/building/demo"},
		{"/floors/1/rooms/101", "/floor/1/room/101"},
		
		// Path cleaning
		{"//electrical//panel//", "/electrical/panel"},
		{"/electrical/./panel", "/electrical/panel"},
		{"/electrical/panel/../circuit", "/electrical/circuit"},
		
		// Complex paths
		{"/electrical/main-panel/circuit-7/outlet-3", "/electrical/main-panel/circuit-7/outlet-3"},
		{"/hvac/ahu/ahu-1/damper/d-101", "/hvac/ahu/ahu-1/damper/d-101"},
	}
	
	for _, tc := range testCases {
		result := Normalize(tc.input)
		if string(result) != tc.expected {
			t.Errorf("Normalize(%q) = %q, expected %q", tc.input, result, tc.expected)
		}
	}
}

func TestArxPath_Parent(t *testing.T) {
	testCases := []struct {
		path     string
		expected string
	}{
		{"/electrical/panel/main", "/electrical/panel"},
		{"/electrical/panel", "/electrical"},
		{"/electrical", "/"},
		{"/", "/"},
	}
	
	for _, tc := range testCases {
		p := Normalize(tc.path)
		parent := p.Parent()
		if string(parent) != tc.expected {
			t.Errorf("%q.Parent() = %q, expected %q", p, parent, tc.expected)
		}
	}
}

func TestArxPath_Join(t *testing.T) {
	base := Normalize("/electrical/panel")
	
	testCases := []struct {
		elements []string
		expected string
	}{
		{[]string{"main"}, "/electrical/panel/main"},
		{[]string{"circuit-7", "outlet-3"}, "/electrical/panel/circuit-7/outlet-3"},
		{[]string{}, "/electrical/panel"},
	}
	
	for _, tc := range testCases {
		result := base.Join(tc.elements...)
		if string(result) != tc.expected {
			t.Errorf("Join(%v) = %q, expected %q", tc.elements, result, tc.expected)
		}
	}
}

func TestArxPath_Split(t *testing.T) {
	testCases := []struct {
		path     string
		expected []string
	}{
		{"/", []string{}},
		{"/electrical", []string{"electrical"}},
		{"/electrical/panel/main", []string{"electrical", "panel", "main"}},
	}
	
	for _, tc := range testCases {
		p := Normalize(tc.path)
		segments := p.Split()
		
		if len(segments) != len(tc.expected) {
			t.Errorf("%q.Split() returned %d segments, expected %d", 
				p, len(segments), len(tc.expected))
			continue
		}
		
		for i, seg := range segments {
			if seg != tc.expected[i] {
				t.Errorf("%q.Split()[%d] = %q, expected %q", 
					p, i, seg, tc.expected[i])
			}
		}
	}
}

func TestArxPath_GetSystem(t *testing.T) {
	testCases := []struct {
		path     string
		expected string
	}{
		{"/electrical/panel/main", "electrical"},
		{"/hvac/ahu/ahu-1", "hvac"},
		{"/fire/alarm/fa-1", "fire"},
		{"/", ""},
	}
	
	for _, tc := range testCases {
		p := Normalize(tc.path)
		system := p.GetSystem()
		if system != tc.expected {
			t.Errorf("%q.GetSystem() = %q, expected %q", p, system, tc.expected)
		}
	}
}

func TestArxPath_Validate(t *testing.T) {
	validPaths := []string{
		"/electrical/panel/main",
		"/hvac/ahu-1/damper/d-101",
		"/floor/1/room/101",
	}
	
	for _, path := range validPaths {
		p := Normalize(path)
		if err := p.Validate(); err != nil {
			t.Errorf("%q should be valid, got error: %v", p, err)
		}
	}
	
	invalidPaths := []string{
		"/electrical/../../../etc/passwd",
		"/electrical/panel;rm -rf /",
		"/electrical/panel`whoami`",
	}
	
	for _, path := range invalidPaths {
		p := ArxPath(path) // Don't normalize to preserve invalid chars
		if err := p.Validate(); err == nil {
			t.Errorf("%q should be invalid", p)
		}
	}
}

func TestCompare(t *testing.T) {
	testCases := []struct {
		p1       string
		p2       string
		expected bool
	}{
		{"building:demo", "building_demo", true},
		{"/electrical/panel", "electrical/panel", true},
		{"/buildings/demo", "/building/demo", true},
		{"/electrical/panel", "/hvac/ahu", false},
	}
	
	for _, tc := range testCases {
		result := Compare(tc.p1, tc.p2)
		if result != tc.expected {
			t.Errorf("Compare(%q, %q) = %v, expected %v", 
				tc.p1, tc.p2, result, tc.expected)
		}
	}
}

func TestCommonPrefix(t *testing.T) {
	testCases := []struct {
		paths    []string
		expected string
	}{
		{
			[]string{"/electrical/panel/main", "/electrical/panel/backup"},
			"/electrical/panel",
		},
		{
			[]string{"/electrical/panel", "/electrical/circuit"},
			"/electrical",
		},
		{
			[]string{"/electrical/panel", "/hvac/ahu"},
			"/",
		},
		{
			[]string{"/electrical/panel/main"},
			"/electrical/panel/main",
		},
		{
			[]string{},
			"/",
		},
	}
	
	for _, tc := range testCases {
		paths := ParseMultiple(tc.paths...)
		result := CommonPrefix(paths...)
		if string(result) != tc.expected {
			t.Errorf("CommonPrefix(%v) = %q, expected %q", 
				tc.paths, result, tc.expected)
		}
	}
}

func TestArxPath_IsSubpathOf(t *testing.T) {
	testCases := []struct {
		child    string
		parent   string
		expected bool
	}{
		{"/electrical/panel/main", "/electrical", true},
		{"/electrical/panel/main", "/electrical/panel", true},
		{"/electrical/panel", "/hvac", false},
		{"/electrical", "/electrical", true},
	}
	
	for _, tc := range testCases {
		child := Normalize(tc.child)
		parent := Normalize(tc.parent)
		result := child.IsSubpathOf(parent)
		if result != tc.expected {
			t.Errorf("%q.IsSubpathOf(%q) = %v, expected %v",
				child, parent, result, tc.expected)
		}
	}
}

func BenchmarkNormalize(b *testing.B) {
	paths := []string{
		"building:demo/floor:1/room:101",
		"/buildings/main/floors/2/rooms/202",
		"electrical_panel_main_circuit_7",
		"/hvac/ahu/ahu-1/damper/d-101",
	}
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		for _, p := range paths {
			_ = Normalize(p)
		}
	}
}