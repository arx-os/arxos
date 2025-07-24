package export

import (
	"context"
	"encoding/json"
	"fmt"
	"strconv"
	"time"

	"go.uber.org/zap"
)

// IFCFormatConverter converts data to IFC format
type IFCFormatConverter struct {
	logger *zap.Logger
}

// NewIFCFormatConverter creates a new IFC format converter
func NewIFCFormatConverter(logger *zap.Logger) *IFCFormatConverter {
	return &IFCFormatConverter{
		logger: logger,
	}
}

// Convert converts data to IFC format
func (ifc *IFCFormatConverter) Convert(ctx context.Context, data json.RawMessage, config *ExportConfig) (json.RawMessage, error) {
	var inputData map[string]interface{}
	if err := json.Unmarshal(data, &inputData); err != nil {
		return nil, fmt.Errorf("failed to unmarshal input data: %w", err)
	}

	// Convert to IFC format
	ifcData := ifc.convertToIFC(inputData, config)

	// Marshal back to JSON
	result, err := json.Marshal(ifcData)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal IFC data: %w", err)
	}

	return result, nil
}

// GetSupportedFormats returns supported formats
func (ifc *IFCFormatConverter) GetSupportedFormats() []ExportFormat {
	return []ExportFormat{ExportFormatIFCLite}
}

// GLTFFormatConverter converts data to GLTF format
type GLTFFormatConverter struct {
	logger *zap.Logger
}

// NewGLTFFormatConverter creates a new GLTF format converter
func NewGLTFFormatConverter(logger *zap.Logger) *GLTFFormatConverter {
	return &GLTFFormatConverter{
		logger: logger,
	}
}

// Convert converts data to GLTF format
func (gltf *GLTFFormatConverter) Convert(ctx context.Context, data json.RawMessage, config *ExportConfig) (json.RawMessage, error) {
	var inputData map[string]interface{}
	if err := json.Unmarshal(data, &inputData); err != nil {
		return nil, fmt.Errorf("failed to unmarshal input data: %w", err)
	}

	// Convert to GLTF format
	gltfData := gltf.convertToGLTF(inputData, config)

	// Marshal back to JSON
	result, err := json.Marshal(gltfData)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal GLTF data: %w", err)
	}

	return result, nil
}

// GetSupportedFormats returns supported formats
func (gltf *GLTFFormatConverter) GetSupportedFormats() []ExportFormat {
	return []ExportFormat{ExportFormatGLTF}
}

// ASCIIBIMFormatConverter converts data to ASCII BIM format
type ASCIIBIMFormatConverter struct {
	logger *zap.Logger
}

// NewASCIIBIMFormatConverter creates a new ASCII BIM format converter
func NewASCIIBIMFormatConverter(logger *zap.Logger) *ASCIIBIMFormatConverter {
	return &ASCIIBIMFormatConverter{
		logger: logger,
	}
}

// Convert converts data to ASCII BIM format
func (ascii *ASCIIBIMFormatConverter) Convert(ctx context.Context, data json.RawMessage, config *ExportConfig) (json.RawMessage, error) {
	var inputData map[string]interface{}
	if err := json.Unmarshal(data, &inputData); err != nil {
		return nil, fmt.Errorf("failed to unmarshal input data: %w", err)
	}

	// Convert to ASCII BIM format
	asciiData := ascii.convertToASCIIBIM(inputData, config)

	// Marshal back to JSON
	result, err := json.Marshal(asciiData)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal ASCII BIM data: %w", err)
	}

	return result, nil
}

// GetSupportedFormats returns supported formats
func (ascii *ASCIIBIMFormatConverter) GetSupportedFormats() []ExportFormat {
	return []ExportFormat{ExportFormatASCIIBIM}
}

// ExcelFormatConverter converts data to Excel format
type ExcelFormatConverter struct {
	logger *zap.Logger
}

// NewExcelFormatConverter creates a new Excel format converter
func NewExcelFormatConverter(logger *zap.Logger) *ExcelFormatConverter {
	return &ExcelFormatConverter{
		logger: logger,
	}
}

// Convert converts data to Excel format
func (excel *ExcelFormatConverter) Convert(ctx context.Context, data json.RawMessage, config *ExportConfig) (json.RawMessage, error) {
	var inputData map[string]interface{}
	if err := json.Unmarshal(data, &inputData); err != nil {
		return nil, fmt.Errorf("failed to unmarshal input data: %w", err)
	}

	// Convert to Excel format
	excelData := excel.convertToExcel(inputData, config)

	// Marshal back to JSON
	result, err := json.Marshal(excelData)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal Excel data: %w", err)
	}

	return result, nil
}

// GetSupportedFormats returns supported formats
func (excel *ExcelFormatConverter) GetSupportedFormats() []ExportFormat {
	return []ExportFormat{ExportFormatExcel}
}

// ParquetFormatConverter converts data to Parquet format
type ParquetFormatConverter struct {
	logger *zap.Logger
}

// NewParquetFormatConverter creates a new Parquet format converter
func NewParquetFormatConverter(logger *zap.Logger) *ParquetFormatConverter {
	return &ParquetFormatConverter{
		logger: logger,
	}
}

// Convert converts data to Parquet format
func (parquet *ParquetFormatConverter) Convert(ctx context.Context, data json.RawMessage, config *ExportConfig) (json.RawMessage, error) {
	var inputData map[string]interface{}
	if err := json.Unmarshal(data, &inputData); err != nil {
		return nil, fmt.Errorf("failed to unmarshal input data: %w", err)
	}

	// Convert to Parquet format
	parquetData := parquet.convertToParquet(inputData, config)

	// Marshal back to JSON
	result, err := json.Marshal(parquetData)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal Parquet data: %w", err)
	}

	return result, nil
}

// GetSupportedFormats returns supported formats
func (parquet *ParquetFormatConverter) GetSupportedFormats() []ExportFormat {
	return []ExportFormat{ExportFormatParquet}
}

// GeoJSONFormatConverter converts data to GeoJSON format
type GeoJSONFormatConverter struct {
	logger *zap.Logger
}

// NewGeoJSONFormatConverter creates a new GeoJSON format converter
func NewGeoJSONFormatConverter(logger *zap.Logger) *GeoJSONFormatConverter {
	return &GeoJSONFormatConverter{
		logger: logger,
	}
}

// Convert converts data to GeoJSON format
func (geojson *GeoJSONFormatConverter) Convert(ctx context.Context, data json.RawMessage, config *ExportConfig) (json.RawMessage, error) {
	var inputData map[string]interface{}
	if err := json.Unmarshal(data, &inputData); err != nil {
		return nil, fmt.Errorf("failed to unmarshal input data: %w", err)
	}

	// Convert to GeoJSON format
	geojsonData := geojson.convertToGeoJSON(inputData, config)

	// Marshal back to JSON
	result, err := json.Marshal(geojsonData)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal GeoJSON data: %w", err)
	}

	return result, nil
}

// GetSupportedFormats returns supported formats
func (geojson *GeoJSONFormatConverter) GetSupportedFormats() []ExportFormat {
	return []ExportFormat{ExportFormatGeoJSON}
}

// Helper conversion functions

func (ifc *IFCFormatConverter) convertToIFC(data map[string]interface{}, config *ExportConfig) map[string]interface{} {
	ifcData := map[string]interface{}{
		"type":      "IFC-LITE",
		"version":   "1.0",
		"timestamp": time.Now().Format(time.RFC3339),
		"metadata": map[string]interface{}{
			"format":             "ifc_lite",
			"quality":            string(config.Quality),
			"include_metadata":   config.IncludeMetadata,
			"include_geometry":   config.IncludeGeometry,
			"include_properties": config.IncludeProperties,
		},
		"entities": []map[string]interface{}{},
	}

	// Convert BIM entities to IFC format
	if entities, ok := data["entities"].([]interface{}); ok {
		for _, entity := range entities {
			if entityMap, ok := entity.(map[string]interface{}); ok {
				ifcEntity := ifc.convertEntityToIFC(entityMap, config)
				ifcData["entities"] = append(ifcData["entities"].([]map[string]interface{}), ifcEntity)
			}
		}
	}

	return ifcData
}

func (ifc *IFCFormatConverter) convertEntityToIFC(entity map[string]interface{}, config *ExportConfig) map[string]interface{} {
	ifcEntity := map[string]interface{}{
		"type":        "IFCWALL",
		"global_id":   generateGlobalID(),
		"name":        getStringValue(entity, "name", "Unnamed"),
		"description": getStringValue(entity, "description", ""),
		"object_type": getStringValue(entity, "type", "WALL"),
	}

	// Add geometry if requested
	if config.IncludeGeometry {
		if geometry, ok := entity["geometry"]; ok {
			ifcEntity["geometry"] = ifc.convertGeometryToIFC(geometry)
		}
	}

	// Add properties if requested
	if config.IncludeProperties {
		if properties, ok := entity["properties"]; ok {
			ifcEntity["properties"] = ifc.convertPropertiesToIFC(properties)
		}
	}

	return ifcEntity
}

func (ifc *IFCFormatConverter) convertGeometryToIFC(geometry interface{}) map[string]interface{} {
	// Convert geometry to IFC format
	return map[string]interface{}{
		"type":                "IFCGEOMETRICREPRESENTATIONCONTEXT",
		"representation_type": "SURFACE",
		"coordinate_space":    "MODEL",
	}
}

func (ifc *IFCFormatConverter) convertPropertiesToIFC(properties interface{}) map[string]interface{} {
	// Convert properties to IFC format
	return map[string]interface{}{
		"type":       "IFCPROPERTYSET",
		"properties": properties,
	}
}

func (gltf *GLTFFormatConverter) convertToGLTF(data map[string]interface{}, config *ExportConfig) map[string]interface{} {
	gltfData := map[string]interface{}{
		"asset": map[string]interface{}{
			"version":   "2.0",
			"generator": "Arxos Export Service",
			"timestamp": time.Now().Unix(),
		},
		"scene": 0,
		"scenes": []map[string]interface{}{
			{
				"nodes": []int{0},
			},
		},
		"nodes":       []map[string]interface{}{},
		"meshes":      []map[string]interface{}{},
		"accessors":   []map[string]interface{}{},
		"bufferViews": []map[string]interface{}{},
		"buffers":     []map[string]interface{}{},
	}

	// Convert BIM entities to GLTF format
	if entities, ok := data["entities"].([]interface{}); ok {
		for i, entity := range entities {
			if entityMap, ok := entity.(map[string]interface{}); ok {
				gltfNode := gltf.convertEntityToGLTF(entityMap, i, config)
				gltfData["nodes"] = append(gltfData["nodes"].([]map[string]interface{}), gltfNode)
			}
		}
	}

	return gltfData
}

func (gltf *GLTFFormatConverter) convertEntityToGLTF(entity map[string]interface{}, index int, config *ExportConfig) map[string]interface{} {
	gltfNode := map[string]interface{}{
		"name": getStringValue(entity, "name", fmt.Sprintf("Entity_%d", index)),
		"mesh": index,
	}

	// Add transformation if available
	if transform, ok := entity["transform"]; ok {
		gltfNode["matrix"] = gltf.convertTransformToGLTF(transform)
	}

	return gltfNode
}

func (gltf *GLTFFormatConverter) convertTransformToGLTF(transform interface{}) []float64 {
	// Convert transformation matrix to GLTF format
	return []float64{
		1, 0, 0, 0,
		0, 1, 0, 0,
		0, 0, 1, 0,
		0, 0, 0, 1,
	}
}

func (ascii *ASCIIBIMFormatConverter) convertToASCIIBIM(data map[string]interface{}, config *ExportConfig) map[string]interface{} {
	asciiData := map[string]interface{}{
		"format":    "ASCII-BIM",
		"version":   "1.0",
		"timestamp": time.Now().Format(time.RFC3339),
		"metadata": map[string]interface{}{
			"quality":            string(config.Quality),
			"include_metadata":   config.IncludeMetadata,
			"include_geometry":   config.IncludeGeometry,
			"include_properties": config.IncludeProperties,
		},
		"entities": []map[string]interface{}{},
	}

	// Convert BIM entities to ASCII BIM format
	if entities, ok := data["entities"].([]interface{}); ok {
		for _, entity := range entities {
			if entityMap, ok := entity.(map[string]interface{}); ok {
				asciiEntity := ascii.convertEntityToASCIIBIM(entityMap, config)
				asciiData["entities"] = append(asciiData["entities"].([]map[string]interface{}), asciiEntity)
			}
		}
	}

	return asciiData
}

func (ascii *ASCIIBIMFormatConverter) convertEntityToASCIIBIM(entity map[string]interface{}, config *ExportConfig) map[string]interface{} {
	asciiEntity := map[string]interface{}{
		"id":          getStringValue(entity, "id", generateID()),
		"type":        getStringValue(entity, "type", "ENTITY"),
		"name":        getStringValue(entity, "name", "Unnamed"),
		"description": getStringValue(entity, "description", ""),
	}

	// Add geometry if requested
	if config.IncludeGeometry {
		if geometry, ok := entity["geometry"]; ok {
			asciiEntity["geometry"] = ascii.convertGeometryToASCIIBIM(geometry)
		}
	}

	// Add properties if requested
	if config.IncludeProperties {
		if properties, ok := entity["properties"]; ok {
			asciiEntity["properties"] = ascii.convertPropertiesToASCIIBIM(properties)
		}
	}

	return asciiEntity
}

func (ascii *ASCIIBIMFormatConverter) convertGeometryToASCIIBIM(geometry interface{}) map[string]interface{} {
	// Convert geometry to ASCII BIM format
	return map[string]interface{}{
		"type": "GEOMETRY",
		"data": geometry,
	}
}

func (ascii *ASCIIBIMFormatConverter) convertPropertiesToASCIIBIM(properties interface{}) map[string]interface{} {
	// Convert properties to ASCII BIM format
	return map[string]interface{}{
		"type": "PROPERTIES",
		"data": properties,
	}
}

func (excel *ExcelFormatConverter) convertToExcel(data map[string]interface{}, config *ExportConfig) map[string]interface{} {
	excelData := map[string]interface{}{
		"format":    "EXCEL",
		"version":   "1.0",
		"timestamp": time.Now().Format(time.RFC3339),
		"metadata": map[string]interface{}{
			"quality":            string(config.Quality),
			"include_metadata":   config.IncludeMetadata,
			"include_properties": config.IncludeProperties,
		},
		"sheets": []map[string]interface{}{},
	}

	// Convert data to Excel format
	if entities, ok := data["entities"].([]interface{}); ok {
		sheet := map[string]interface{}{
			"name":    "Entities",
			"headers": []string{"ID", "Type", "Name", "Description"},
			"rows":    [][]string{},
		}

		for _, entity := range entities {
			if entityMap, ok := entity.(map[string]interface{}); ok {
				row := []string{
					getStringValue(entityMap, "id", ""),
					getStringValue(entityMap, "type", ""),
					getStringValue(entityMap, "name", ""),
					getStringValue(entityMap, "description", ""),
				}
				sheet["rows"] = append(sheet["rows"].([][]string), row)
			}
		}

		excelData["sheets"] = append(excelData["sheets"].([]map[string]interface{}), sheet)
	}

	return excelData
}

func (parquet *ParquetFormatConverter) convertToParquet(data map[string]interface{}, config *ExportConfig) map[string]interface{} {
	parquetData := map[string]interface{}{
		"format":    "PARQUET",
		"version":   "1.0",
		"timestamp": time.Now().Format(time.RFC3339),
		"metadata": map[string]interface{}{
			"quality":            string(config.Quality),
			"include_metadata":   config.IncludeMetadata,
			"include_properties": config.IncludeProperties,
		},
		"schema": map[string]interface{}{
			"fields": []map[string]interface{}{
				{"name": "id", "type": "string"},
				{"name": "type", "type": "string"},
				{"name": "name", "type": "string"},
				{"name": "description", "type": "string"},
			},
		},
		"data": []map[string]interface{}{},
	}

	// Convert data to Parquet format
	if entities, ok := data["entities"].([]interface{}); ok {
		for _, entity := range entities {
			if entityMap, ok := entity.(map[string]interface{}); ok {
				row := map[string]interface{}{
					"id":          getStringValue(entityMap, "id", ""),
					"type":        getStringValue(entityMap, "type", ""),
					"name":        getStringValue(entityMap, "name", ""),
					"description": getStringValue(entityMap, "description", ""),
				}
				parquetData["data"] = append(parquetData["data"].([]map[string]interface{}), row)
			}
		}
	}

	return parquetData
}

func (geojson *GeoJSONFormatConverter) convertToGeoJSON(data map[string]interface{}, config *ExportConfig) map[string]interface{} {
	geojsonData := map[string]interface{}{
		"type":     "FeatureCollection",
		"features": []map[string]interface{}{},
	}

	// Convert BIM entities to GeoJSON format
	if entities, ok := data["entities"].([]interface{}); ok {
		for _, entity := range entities {
			if entityMap, ok := entity.(map[string]interface{}); ok {
				feature := geojson.convertEntityToGeoJSON(entityMap, config)
				geojsonData["features"] = append(geojsonData["features"].([]map[string]interface{}), feature)
			}
		}
	}

	return geojsonData
}

func (geojson *GeoJSONFormatConverter) convertEntityToGeoJSON(entity map[string]interface{}, config *ExportConfig) map[string]interface{} {
	feature := map[string]interface{}{
		"type": "Feature",
		"properties": map[string]interface{}{
			"id":          getStringValue(entity, "id", ""),
			"type":        getStringValue(entity, "type", ""),
			"name":        getStringValue(entity, "name", ""),
			"description": getStringValue(entity, "description", ""),
		},
		"geometry": map[string]interface{}{
			"type":        "Point",
			"coordinates": []float64{0, 0, 0},
		},
	}

	// Add geometry if available
	if geometry, ok := entity["geometry"]; ok {
		feature["geometry"] = geojson.convertGeometryToGeoJSON(geometry)
	}

	// Add properties if requested
	if config.IncludeProperties {
		if properties, ok := entity["properties"]; ok {
			if propsMap, ok := properties.(map[string]interface{}); ok {
				for k, v := range propsMap {
					feature["properties"].(map[string]interface{})[k] = v
				}
			}
		}
	}

	return feature
}

func (geojson *GeoJSONFormatConverter) convertGeometryToGeoJSON(geometry interface{}) map[string]interface{} {
	// Convert geometry to GeoJSON format
	return map[string]interface{}{
		"type":        "Point",
		"coordinates": []float64{0, 0, 0},
	}
}

// Helper functions

func generateGlobalID() string {
	return fmt.Sprintf("IFC_%d", time.Now().UnixNano())
}

func generateID() string {
	return fmt.Sprintf("ID_%d", time.Now().UnixNano())
}

func getStringValue(data map[string]interface{}, key, defaultValue string) string {
	if value, ok := data[key]; ok {
		if str, ok := value.(string); ok {
			return str
		}
	}
	return defaultValue
}

func getFloatValue(data map[string]interface{}, key string, defaultValue float64) float64 {
	if value, ok := data[key]; ok {
		switch v := value.(type) {
		case float64:
			return v
		case int:
			return float64(v)
		case string:
			if f, err := strconv.ParseFloat(v, 64); err == nil {
				return f
			}
		}
	}
	return defaultValue
}
