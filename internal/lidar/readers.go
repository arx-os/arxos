package lidar

import (
	"bufio"
	"encoding/binary"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

// Reader interface for point cloud formats
type Reader interface {
	Read(path string) (*PointCloud, error)
	ValidateFile(path string) error
}

// PLYReader reads PLY (Polygon File Format) files
type PLYReader struct {
	binaryMode   bool
	littleEndian bool
}

// NewPLYReader creates a new PLY reader
func NewPLYReader() *PLYReader {
	return &PLYReader{}
}

// Read reads a PLY file and returns a point cloud
func (r *PLYReader) Read(path string) (*PointCloud, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("failed to open PLY file: %w", err)
	}
	defer file.Close()

	// Parse header
	header, err := r.parseHeader(file)
	if err != nil {
		return nil, fmt.Errorf("failed to parse PLY header: %w", err)
	}

	// Create point cloud
	pc := &PointCloud{
		Points: make([]Point, 0, header.vertexCount),
		Metadata: PointCloudMetadata{
			ScanID:           fmt.Sprintf("ply_%d", time.Now().Unix()),
			ScanDate:         time.Now(),
			Scanner:          "PLY Import",
			PointCount:       header.vertexCount,
			CoordinateSystem: "local",
		},
	}

	// Read vertex data
	if header.format == "binary_little_endian" || header.format == "binary_big_endian" {
		err = r.readBinaryData(file, pc, header)
	} else {
		err = r.readASCIIData(file, pc, header)
	}

	if err != nil {
		return nil, fmt.Errorf("failed to read PLY data: %w", err)
	}

	// Calculate bounds
	pc.Metadata.Bounds = pc.GetBoundingBox()

	return pc, nil
}

// ValidateFile validates if the file is a valid PLY file
func (r *PLYReader) ValidateFile(path string) error {
	file, err := os.Open(path)
	if err != nil {
		return err
	}
	defer file.Close()

	// Check PLY magic number
	scanner := bufio.NewScanner(file)
	if scanner.Scan() {
		if scanner.Text() != "ply" {
			return fmt.Errorf("not a PLY file")
		}
	}

	return nil
}

// plyHeader represents PLY file header information
type plyHeader struct {
	format      string
	vertexCount int
	hasColor    bool
	hasNormal   bool
	properties  []plyProperty
}

// plyProperty represents a PLY property
type plyProperty struct {
	name     string
	dataType string
}

// parseHeader parses the PLY file header
func (r *PLYReader) parseHeader(file *os.File) (*plyHeader, error) {
	scanner := bufio.NewScanner(file)
	header := &plyHeader{
		properties: make([]plyProperty, 0),
	}

	for scanner.Scan() {
		line := scanner.Text()
		parts := strings.Fields(line)

		if len(parts) == 0 {
			continue
		}

		switch parts[0] {
		case "format":
			if len(parts) >= 2 {
				header.format = parts[1]
			}
		case "element":
			if len(parts) >= 3 && parts[1] == "vertex" {
				count, err := strconv.Atoi(parts[2])
				if err == nil {
					header.vertexCount = count
				}
			}
		case "property":
			if len(parts) >= 3 {
				prop := plyProperty{
					dataType: parts[1],
					name:     parts[2],
				}
				header.properties = append(header.properties, prop)

				// Check for color and normal properties
				if strings.HasPrefix(prop.name, "r") || strings.HasPrefix(prop.name, "red") {
					header.hasColor = true
				}
				if strings.HasPrefix(prop.name, "nx") {
					header.hasNormal = true
				}
			}
		case "end_header":
			return header, nil
		}
	}

	return nil, fmt.Errorf("end_header not found")
}

// readASCIIData reads ASCII format PLY data
func (r *PLYReader) readASCIIData(file *os.File, pc *PointCloud, header *plyHeader) error {
	scanner := bufio.NewScanner(file)

	if header.hasColor {
		pc.Colors = make([]Color, 0, header.vertexCount)
	}
	if header.hasNormal {
		pc.Normals = make([]Normal, 0, header.vertexCount)
	}

	for i := 0; i < header.vertexCount && scanner.Scan(); i++ {
		line := scanner.Text()
		values := strings.Fields(line)

		if len(values) < 3 {
			return fmt.Errorf("invalid vertex data at line %d", i)
		}

		// Parse XYZ coordinates
		x, _ := strconv.ParseFloat(values[0], 64)
		y, _ := strconv.ParseFloat(values[1], 64)
		z, _ := strconv.ParseFloat(values[2], 64)

		pc.Points = append(pc.Points, Point{X: x, Y: y, Z: z})

		// Parse color if present
		if header.hasColor && len(values) >= 6 {
			r, _ := strconv.ParseUint(values[3], 10, 8)
			g, _ := strconv.ParseUint(values[4], 10, 8)
			b, _ := strconv.ParseUint(values[5], 10, 8)
			pc.Colors = append(pc.Colors, Color{R: uint8(r), G: uint8(g), B: uint8(b)})
		}

		// Parse normals if present
		if header.hasNormal {
			startIdx := 3
			if header.hasColor {
				startIdx = 6
			}
			if len(values) >= startIdx+3 {
				nx, _ := strconv.ParseFloat(values[startIdx], 32)
				ny, _ := strconv.ParseFloat(values[startIdx+1], 32)
				nz, _ := strconv.ParseFloat(values[startIdx+2], 32)
				pc.Normals = append(pc.Normals, Normal{
					NX: float32(nx),
					NY: float32(ny),
					NZ: float32(nz),
				})
			}
		}
	}

	pc.Metadata.PointCount = len(pc.Points)
	return nil
}

// readBinaryData reads binary format PLY data
func (r *PLYReader) readBinaryData(file *os.File, pc *PointCloud, header *plyHeader) error {
	// Determine byte order
	var byteOrder binary.ByteOrder
	if header.format == "binary_little_endian" {
		byteOrder = binary.LittleEndian
	} else {
		byteOrder = binary.BigEndian
	}

	if header.hasColor {
		pc.Colors = make([]Color, 0, header.vertexCount)
	}
	if header.hasNormal {
		pc.Normals = make([]Normal, 0, header.vertexCount)
	}

	for i := 0; i < header.vertexCount; i++ {
		// Read XYZ as floats
		var x, y, z float32
		err := binary.Read(file, byteOrder, &x)
		if err != nil {
			return err
		}
		err = binary.Read(file, byteOrder, &y)
		if err != nil {
			return err
		}
		err = binary.Read(file, byteOrder, &z)
		if err != nil {
			return err
		}

		pc.Points = append(pc.Points, Point{X: float64(x), Y: float64(y), Z: float64(z)})

		// Read color if present
		if header.hasColor {
			var r, g, b uint8
			binary.Read(file, byteOrder, &r)
			binary.Read(file, byteOrder, &g)
			binary.Read(file, byteOrder, &b)
			pc.Colors = append(pc.Colors, Color{R: r, G: g, B: b})
		}

		// Read normals if present
		if header.hasNormal {
			var nx, ny, nz float32
			binary.Read(file, byteOrder, &nx)
			binary.Read(file, byteOrder, &ny)
			binary.Read(file, byteOrder, &nz)
			pc.Normals = append(pc.Normals, Normal{NX: nx, NY: ny, NZ: nz})
		}
	}

	pc.Metadata.PointCount = len(pc.Points)
	return nil
}

// LASReader reads LAS/LAZ (LASer) files
type LASReader struct {
	scaleFactor [3]float64
	offset      [3]float64
}

// NewLASReader creates a new LAS reader
func NewLASReader() *LASReader {
	return &LASReader{}
}

// Read reads a LAS file and returns a point cloud
func (r *LASReader) Read(path string) (*PointCloud, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("failed to open LAS file: %w", err)
	}
	defer file.Close()

	// Read LAS header
	header, err := r.readHeader(file)
	if err != nil {
		return nil, fmt.Errorf("failed to read LAS header: %w", err)
	}

	// Create point cloud
	pc := &PointCloud{
		Points:      make([]Point, 0, header.numberOfPoints),
		Intensities: make([]float32, 0, header.numberOfPoints),
		Metadata: PointCloudMetadata{
			ScanID:           fmt.Sprintf("las_%d", time.Now().Unix()),
			ScanDate:         time.Now(),
			Scanner:          "LAS Import",
			PointCount:       int(header.numberOfPoints),
			CoordinateSystem: "local",
		},
	}

	// Read point data
	if err := r.readPoints(file, pc, header); err != nil {
		return nil, fmt.Errorf("failed to read LAS points: %w", err)
	}

	// Calculate bounds
	pc.Metadata.Bounds = pc.GetBoundingBox()

	return pc, nil
}

// ValidateFile validates if the file is a valid LAS file
func (r *LASReader) ValidateFile(path string) error {
	file, err := os.Open(path)
	if err != nil {
		return err
	}
	defer file.Close()

	// Check LAS signature
	signature := make([]byte, 4)
	if _, err := file.Read(signature); err != nil {
		return err
	}

	if string(signature) != "LASF" {
		return fmt.Errorf("not a LAS file")
	}

	return nil
}

// lasHeader represents LAS file header
type lasHeader struct {
	fileSignature   [4]byte
	fileSourceID    uint16
	globalEncoding  uint16
	versionMajor    uint8
	versionMinor    uint8
	systemID        [32]byte
	softwareID      [32]byte
	creationDay     uint16
	creationYear    uint16
	headerSize      uint16
	offsetToPoints  uint32
	numberOfVLRs    uint32
	pointDataFormat uint8
	pointDataLength uint16
	numberOfPoints  uint32
	xScaleFactor    float64
	yScaleFactor    float64
	zScaleFactor    float64
	xOffset         float64
	yOffset         float64
	zOffset         float64
	maxX            float64
	minX            float64
	maxY            float64
	minY            float64
	maxZ            float64
	minZ            float64
}

// readHeader reads the LAS file header
func (r *LASReader) readHeader(file *os.File) (*lasHeader, error) {
	header := &lasHeader{}

	// Read header fields
	err := binary.Read(file, binary.LittleEndian, &header.fileSignature)
	if err != nil {
		return nil, err
	}

	if string(header.fileSignature[:]) != "LASF" {
		return nil, fmt.Errorf("invalid LAS signature")
	}

	// Read rest of header (simplified)
	binary.Read(file, binary.LittleEndian, &header.fileSourceID)
	binary.Read(file, binary.LittleEndian, &header.globalEncoding)

	// Skip GUID (16 bytes)
	file.Seek(16, io.SeekCurrent)

	binary.Read(file, binary.LittleEndian, &header.versionMajor)
	binary.Read(file, binary.LittleEndian, &header.versionMinor)
	binary.Read(file, binary.LittleEndian, &header.systemID)
	binary.Read(file, binary.LittleEndian, &header.softwareID)
	binary.Read(file, binary.LittleEndian, &header.creationDay)
	binary.Read(file, binary.LittleEndian, &header.creationYear)
	binary.Read(file, binary.LittleEndian, &header.headerSize)
	binary.Read(file, binary.LittleEndian, &header.offsetToPoints)
	binary.Read(file, binary.LittleEndian, &header.numberOfVLRs)
	binary.Read(file, binary.LittleEndian, &header.pointDataFormat)
	binary.Read(file, binary.LittleEndian, &header.pointDataLength)
	binary.Read(file, binary.LittleEndian, &header.numberOfPoints)

	// Skip legacy point counts
	file.Seek(20, io.SeekCurrent)

	binary.Read(file, binary.LittleEndian, &header.xScaleFactor)
	binary.Read(file, binary.LittleEndian, &header.yScaleFactor)
	binary.Read(file, binary.LittleEndian, &header.zScaleFactor)
	binary.Read(file, binary.LittleEndian, &header.xOffset)
	binary.Read(file, binary.LittleEndian, &header.yOffset)
	binary.Read(file, binary.LittleEndian, &header.zOffset)

	// Store scale and offset for point conversion
	r.scaleFactor = [3]float64{header.xScaleFactor, header.yScaleFactor, header.zScaleFactor}
	r.offset = [3]float64{header.xOffset, header.yOffset, header.zOffset}

	return header, nil
}

// readPoints reads point data from LAS file
func (r *LASReader) readPoints(file *os.File, pc *PointCloud, header *lasHeader) error {
	// Seek to point data
	if _, err := file.Seek(int64(header.offsetToPoints), io.SeekStart); err != nil {
		return err
	}

	for i := uint32(0); i < header.numberOfPoints; i++ {
		// Read point coordinates (as int32)
		var x, y, z int32
		binary.Read(file, binary.LittleEndian, &x)
		binary.Read(file, binary.LittleEndian, &y)
		binary.Read(file, binary.LittleEndian, &z)

		// Convert to real coordinates
		realX := float64(x)*r.scaleFactor[0] + r.offset[0]
		realY := float64(y)*r.scaleFactor[1] + r.offset[1]
		realZ := float64(z)*r.scaleFactor[2] + r.offset[2]

		pc.Points = append(pc.Points, Point{X: realX, Y: realY, Z: realZ})

		// Read intensity
		var intensity uint16
		binary.Read(file, binary.LittleEndian, &intensity)
		pc.Intensities = append(pc.Intensities, float32(intensity)/65535.0)

		// Skip rest of point record based on format
		// Format 0 has 20 bytes total, we've read 14
		skipBytes := int64(header.pointDataLength) - 14
		if skipBytes > 0 {
			file.Seek(skipBytes, io.SeekCurrent)
		}
	}

	return nil
}

// E57Reader reads E57 (ASTM E2807) files
// Note: This is a simplified implementation
type E57Reader struct {
	metadata map[string]interface{}
}

// NewE57Reader creates a new E57 reader
func NewE57Reader() *E57Reader {
	return &E57Reader{
		metadata: make(map[string]interface{}),
	}
}

// Read reads an E57 file and returns a point cloud
// Note: This is a placeholder implementation
func (r *E57Reader) Read(path string) (*PointCloud, error) {
	// E57 is a complex format that would require a full XML parser
	// and binary data reader. This is a simplified placeholder.
	return nil, fmt.Errorf("E57 format support not yet implemented")
}

// ValidateFile validates if the file is a valid E57 file
func (r *E57Reader) ValidateFile(path string) error {
	file, err := os.Open(path)
	if err != nil {
		return err
	}
	defer file.Close()

	// Check E57 signature
	signature := make([]byte, 8)
	if _, err := file.Read(signature); err != nil {
		return err
	}

	// E57 files start with "ASTM-E57"
	if string(signature) != "ASTM-E57" {
		return fmt.Errorf("not an E57 file")
	}

	return nil
}

// ReaderFactory creates appropriate reader based on file extension
func GetReader(path string) (Reader, error) {
	ext := strings.ToLower(strings.TrimPrefix(filepath.Ext(path), "."))

	switch ext {
	case "ply":
		return NewPLYReader(), nil
	case "las", "laz":
		return NewLASReader(), nil
	case "e57":
		return NewE57Reader(), nil
	default:
		return nil, fmt.Errorf("unsupported format: %s", ext)
	}
}

// ReadPointCloud reads a point cloud file using the appropriate reader
func ReadPointCloud(path string) (*PointCloud, error) {
	reader, err := GetReader(path)
	if err != nil {
		return nil, err
	}

	if err := reader.ValidateFile(path); err != nil {
		return nil, fmt.Errorf("invalid file: %w", err)
	}

	return reader.Read(path)
}
