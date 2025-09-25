package spatial

import (
	"fmt"
	"regexp"
	"strconv"
	"strings"
)

// WKTParser provides basic WKT (Well-Known Text) parsing functionality
type WKTParser struct{}

// NewWKTParser creates a new WKT parser
func NewWKTParser() *WKTParser {
	return &WKTParser{}
}

// ParsePoint parses a WKT POINT string
func (p *WKTParser) ParsePoint(wkt string) (*Point3D, error) {
	// Remove whitespace and convert to uppercase
	wkt = strings.TrimSpace(strings.ToUpper(wkt))

	// Match POINT(x y) or POINT(x y z)
	pointRegex := regexp.MustCompile(`POINT\s*\(\s*([+-]?\d*\.?\d+)\s+([+-]?\d*\.?\d+)(?:\s+([+-]?\d*\.?\d+))?\s*\)`)
	matches := pointRegex.FindStringSubmatch(wkt)

	if len(matches) < 3 {
		return nil, fmt.Errorf("invalid POINT format: %s", wkt)
	}

	x, err := strconv.ParseFloat(matches[1], 64)
	if err != nil {
		return nil, fmt.Errorf("invalid X coordinate: %s", matches[1])
	}

	y, err := strconv.ParseFloat(matches[2], 64)
	if err != nil {
		return nil, fmt.Errorf("invalid Y coordinate: %s", matches[2])
	}

	z := 0.0
	if len(matches) > 3 && matches[3] != "" {
		z, err = strconv.ParseFloat(matches[3], 64)
		if err != nil {
			return nil, fmt.Errorf("invalid Z coordinate: %s", matches[3])
		}
	}

	return &Point3D{X: x, Y: y, Z: z}, nil
}

// Polygon represents a polygon geometry
type Polygon struct {
	Points []Point3D
}

// LineString represents a linestring geometry
type LineString struct {
	Points []Point3D
}

// MultiPolygon represents a multipolygon geometry
type MultiPolygon struct {
	Polygons []Polygon
}

// ParsePolygon parses a WKT POLYGON string
func (p *WKTParser) ParsePolygon(wkt string) (*Polygon, error) {
	// Remove whitespace and convert to uppercase
	wkt = strings.TrimSpace(strings.ToUpper(wkt))

	// Match POLYGON((x1 y1, x2 y2, x3 y3, x1 y1))
	polygonRegex := regexp.MustCompile(`POLYGON\s*\(\s*\(\s*(.+?)\s*\)\s*\)`)
	matches := polygonRegex.FindStringSubmatch(wkt)

	if len(matches) < 2 {
		return nil, fmt.Errorf("invalid POLYGON format: %s", wkt)
	}

	// Parse coordinate pairs
	coordsStr := matches[1]
	coordPairs := strings.Split(coordsStr, ",")

	if len(coordPairs) < 3 {
		return nil, fmt.Errorf("polygon must have at least 3 points")
	}

	points := make([]Point3D, 0, len(coordPairs))
	for _, pair := range coordPairs {
		pair = strings.TrimSpace(pair)
		coords := strings.Fields(pair)

		if len(coords) < 2 {
			return nil, fmt.Errorf("invalid coordinate pair: %s", pair)
		}

		x, err := strconv.ParseFloat(coords[0], 64)
		if err != nil {
			return nil, fmt.Errorf("invalid X coordinate: %s", coords[0])
		}

		y, err := strconv.ParseFloat(coords[1], 64)
		if err != nil {
			return nil, fmt.Errorf("invalid Y coordinate: %s", coords[1])
		}

		z := 0.0
		if len(coords) > 2 {
			z, err = strconv.ParseFloat(coords[2], 64)
			if err != nil {
				return nil, fmt.Errorf("invalid Z coordinate: %s", coords[2])
			}
		}

		points = append(points, Point3D{X: x, Y: y, Z: z})
	}

	// Check if polygon is closed (first and last points should be the same)
	if len(points) > 0 && points[0] != points[len(points)-1] {
		points = append(points, points[0]) // Close the polygon
	}

	return &Polygon{Points: points}, nil
}

// ParseLineString parses a WKT LINESTRING string
func (p *WKTParser) ParseLineString(wkt string) (*LineString, error) {
	// Remove whitespace and convert to uppercase
	wkt = strings.TrimSpace(strings.ToUpper(wkt))

	// Match LINESTRING(x1 y1, x2 y2, ...)
	lineRegex := regexp.MustCompile(`LINESTRING\s*\(\s*(.+?)\s*\)`)
	matches := lineRegex.FindStringSubmatch(wkt)

	if len(matches) < 2 {
		return nil, fmt.Errorf("invalid LINESTRING format: %s", wkt)
	}

	// Parse coordinate pairs
	coordsStr := matches[1]
	coordPairs := strings.Split(coordsStr, ",")

	if len(coordPairs) < 2 {
		return nil, fmt.Errorf("linestring must have at least 2 points")
	}

	points := make([]Point3D, 0, len(coordPairs))
	for _, pair := range coordPairs {
		pair = strings.TrimSpace(pair)
		coords := strings.Fields(pair)

		if len(coords) < 2 {
			return nil, fmt.Errorf("invalid coordinate pair: %s", pair)
		}

		x, err := strconv.ParseFloat(coords[0], 64)
		if err != nil {
			return nil, fmt.Errorf("invalid X coordinate: %s", coords[0])
		}

		y, err := strconv.ParseFloat(coords[1], 64)
		if err != nil {
			return nil, fmt.Errorf("invalid Y coordinate: %s", coords[1])
		}

		z := 0.0
		if len(coords) > 2 {
			z, err = strconv.ParseFloat(coords[2], 64)
			if err != nil {
				return nil, fmt.Errorf("invalid Z coordinate: %s", coords[2])
			}
		}

		points = append(points, Point3D{X: x, Y: y, Z: z})
	}

	return &LineString{Points: points}, nil
}

// ParseMultiPolygon parses a WKT MULTIPOLYGON string
func (p *WKTParser) ParseMultiPolygon(wkt string) (*MultiPolygon, error) {
	// Remove whitespace and convert to uppercase
	wkt = strings.TrimSpace(strings.ToUpper(wkt))

	// Match MULTIPOLYGON(((x1 y1, x2 y2, x3 y3, x1 y1)), ((x4 y4, x5 y5, x6 y6, x4 y4)))
	multiPolygonRegex := regexp.MustCompile(`MULTIPOLYGON\s*\(\s*(.+?)\s*\)`)
	matches := multiPolygonRegex.FindStringSubmatch(wkt)

	if len(matches) < 2 {
		return nil, fmt.Errorf("invalid MULTIPOLYGON format: %s", wkt)
	}

	// Parse individual polygons
	polygonsStr := matches[1]
	polygonStrings := p.splitPolygonStrings(polygonsStr)

	polygons := make([]Polygon, 0, len(polygonStrings))
	for _, polyStr := range polygonStrings {
		polygon, err := p.ParsePolygon("POLYGON" + polyStr)
		if err != nil {
			return nil, fmt.Errorf("failed to parse polygon in multipolygon: %w", err)
		}
		polygons = append(polygons, *polygon)
	}

	return &MultiPolygon{Polygons: polygons}, nil
}

// splitPolygonStrings splits a multipolygon string into individual polygon strings
func (p *WKTParser) splitPolygonStrings(s string) []string {
	var polygons []string
	var current strings.Builder
	parenCount := 0

	for _, char := range s {
		switch char {
		case '(':
			parenCount++
			current.WriteRune(char)
		case ')':
			parenCount--
			current.WriteRune(char)
			if parenCount == 0 {
				polygons = append(polygons, current.String())
				current.Reset()
			}
		case ',':
			if parenCount == 0 {
				// Skip commas at the top level
				continue
			}
			current.WriteRune(char)
		default:
			current.WriteRune(char)
		}
	}

	return polygons
}

// DetectGeometryType detects the type of geometry from WKT string
func (p *WKTParser) DetectGeometryType(wkt string) string {
	wkt = strings.TrimSpace(strings.ToUpper(wkt))

	if strings.HasPrefix(wkt, "POINT") {
		return "POINT"
	} else if strings.HasPrefix(wkt, "LINESTRING") {
		return "LINESTRING"
	} else if strings.HasPrefix(wkt, "POLYGON") {
		return "POLYGON"
	} else if strings.HasPrefix(wkt, "MULTIPOLYGON") {
		return "MULTIPOLYGON"
	}

	return "UNKNOWN"
}
