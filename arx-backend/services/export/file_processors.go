package export

import (
	"context"
	"encoding/csv"
	"encoding/json"
	"encoding/xml"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"go.uber.org/zap"
)

// IFCFileProcessor processes IFC files
type IFCFileProcessor struct {
	logger *zap.Logger
}

// NewIFCFileProcessor creates a new IFC file processor
func NewIFCFileProcessor(logger *zap.Logger) *IFCFileProcessor {
	return &IFCFileProcessor{
		logger: logger,
	}
}

// Process processes data and writes to IFC file
func (ifc *IFCFileProcessor) Process(ctx context.Context, data json.RawMessage, outputPath string, config *ExportConfig) error {
	var ifcData map[string]interface{}
	if err := json.Unmarshal(data, &ifcData); err != nil {
		return fmt.Errorf("failed to unmarshal IFC data: %w", err)
	}

	// Create output directory if it doesn't exist
	if err := os.MkdirAll(filepath.Dir(outputPath), 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Write IFC file
	file, err := os.Create(outputPath)
	if err != nil {
		return fmt.Errorf("failed to create IFC file: %w", err)
	}
	defer file.Close()

	// Write IFC header
	if err := ifc.writeIFCHeader(file, config); err != nil {
		return fmt.Errorf("failed to write IFC header: %w", err)
	}

	// Write IFC entities
	if err := ifc.writeIFCEntities(file, ifcData); err != nil {
		return fmt.Errorf("failed to write IFC entities: %w", err)
	}

	// Write IFC footer
	if err := ifc.writeIFCFooter(file); err != nil {
		return fmt.Errorf("failed to write IFC footer: %w", err)
	}

	return nil
}

// GetSupportedFormats returns supported formats
func (ifc *IFCFileProcessor) GetSupportedFormats() []ExportFormat {
	return []ExportFormat{ExportFormatIFCLite}
}

// GLTFFileProcessor processes GLTF files
type GLTFFileProcessor struct {
	logger *zap.Logger
}

// NewGLTFFileProcessor creates a new GLTF file processor
func NewGLTFFileProcessor(logger *zap.Logger) *GLTFFileProcessor {
	return &GLTFFileProcessor{
		logger: logger,
	}
}

// Process processes data and writes to GLTF file
func (gltf *GLTFFileProcessor) Process(ctx context.Context, data json.RawMessage, outputPath string, config *ExportConfig) error {
	var gltfData map[string]interface{}
	if err := json.Unmarshal(data, &gltfData); err != nil {
		return fmt.Errorf("failed to unmarshal GLTF data: %w", err)
	}

	// Create output directory if it doesn't exist
	if err := os.MkdirAll(filepath.Dir(outputPath), 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Write GLTF file
	file, err := os.Create(outputPath)
	if err != nil {
		return fmt.Errorf("failed to create GLTF file: %w", err)
	}
	defer file.Close()

	// Write GLTF JSON
	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(gltfData); err != nil {
		return fmt.Errorf("failed to write GLTF file: %w", err)
	}

	return nil
}

// GetSupportedFormats returns supported formats
func (gltf *GLTFFileProcessor) GetSupportedFormats() []ExportFormat {
	return []ExportFormat{ExportFormatGLTF}
}

// ASCIIBIMFileProcessor processes ASCII BIM files
type ASCIIBIMFileProcessor struct {
	logger *zap.Logger
}

// NewASCIIBIMFileProcessor creates a new ASCII BIM file processor
func NewASCIIBIMFileProcessor(logger *zap.Logger) *ASCIIBIMFileProcessor {
	return &ASCIIBIMFileProcessor{
		logger: logger,
	}
}

// Process processes data and writes to ASCII BIM file
func (ascii *ASCIIBIMFileProcessor) Process(ctx context.Context, data json.RawMessage, outputPath string, config *ExportConfig) error {
	var asciiData map[string]interface{}
	if err := json.Unmarshal(data, &asciiData); err != nil {
		return fmt.Errorf("failed to unmarshal ASCII BIM data: %w", err)
	}

	// Create output directory if it doesn't exist
	if err := os.MkdirAll(filepath.Dir(outputPath), 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Write ASCII BIM file
	file, err := os.Create(outputPath)
	if err != nil {
		return fmt.Errorf("failed to create ASCII BIM file: %w", err)
	}
	defer file.Close()

	// Write ASCII BIM content
	if err := ascii.writeASCIIBIMContent(file, asciiData); err != nil {
		return fmt.Errorf("failed to write ASCII BIM content: %w", err)
	}

	return nil
}

// GetSupportedFormats returns supported formats
func (ascii *ASCIIBIMFileProcessor) GetSupportedFormats() []ExportFormat {
	return []ExportFormat{ExportFormatASCIIBIM}
}

// ExcelFileProcessor processes Excel files
type ExcelFileProcessor struct {
	logger *zap.Logger
}

// NewExcelFileProcessor creates a new Excel file processor
func NewExcelFileProcessor(logger *zap.Logger) *ExcelFileProcessor {
	return &ExcelFileProcessor{
		logger: logger,
	}
}

// Process processes data and writes to Excel file
func (excel *ExcelFileProcessor) Process(ctx context.Context, data json.RawMessage, outputPath string, config *ExportConfig) error {
	var excelData map[string]interface{}
	if err := json.Unmarshal(data, &excelData); err != nil {
		return fmt.Errorf("failed to unmarshal Excel data: %w", err)
	}

	// Create output directory if it doesn't exist
	if err := os.MkdirAll(filepath.Dir(outputPath), 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Write Excel file (CSV format for simplicity)
	csvPath := strings.Replace(outputPath, ".xlsx", ".csv", -1)
	file, err := os.Create(csvPath)
	if err != nil {
		return fmt.Errorf("failed to create Excel file: %w", err)
	}
	defer file.Close()

	// Write CSV content
	if err := excel.writeCSVContent(file, excelData); err != nil {
		return fmt.Errorf("failed to write CSV content: %w", err)
	}

	return nil
}

// GetSupportedFormats returns supported formats
func (excel *ExcelFileProcessor) GetSupportedFormats() []ExportFormat {
	return []ExportFormat{ExportFormatExcel}
}

// ParquetFileProcessor processes Parquet files
type ParquetFileProcessor struct {
	logger *zap.Logger
}

// NewParquetFileProcessor creates a new Parquet file processor
func NewParquetFileProcessor(logger *zap.Logger) *ParquetFileProcessor {
	return &ParquetFileProcessor{
		logger: logger,
	}
}

// Process processes data and writes to Parquet file
func (parquet *ParquetFileProcessor) Process(ctx context.Context, data json.RawMessage, outputPath string, config *ExportConfig) error {
	var parquetData map[string]interface{}
	if err := json.Unmarshal(data, &parquetData); err != nil {
		return fmt.Errorf("failed to unmarshal Parquet data: %w", err)
	}

	// Create output directory if it doesn't exist
	if err := os.MkdirAll(filepath.Dir(outputPath), 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Write Parquet file (JSON format for simplicity)
	file, err := os.Create(outputPath)
	if err != nil {
		return fmt.Errorf("failed to create Parquet file: %w", err)
	}
	defer file.Close()

	// Write JSON content
	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(parquetData); err != nil {
		return fmt.Errorf("failed to write Parquet file: %w", err)
	}

	return nil
}

// GetSupportedFormats returns supported formats
func (parquet *ParquetFileProcessor) GetSupportedFormats() []ExportFormat {
	return []ExportFormat{ExportFormatParquet}
}

// GeoJSONFileProcessor processes GeoJSON files
type GeoJSONFileProcessor struct {
	logger *zap.Logger
}

// NewGeoJSONFileProcessor creates a new GeoJSON file processor
func NewGeoJSONFileProcessor(logger *zap.Logger) *GeoJSONFileProcessor {
	return &GeoJSONFileProcessor{
		logger: logger,
	}
}

// Process processes data and writes to GeoJSON file
func (geojson *GeoJSONFileProcessor) Process(ctx context.Context, data json.RawMessage, outputPath string, config *ExportConfig) error {
	var geojsonData map[string]interface{}
	if err := json.Unmarshal(data, &geojsonData); err != nil {
		return fmt.Errorf("failed to unmarshal GeoJSON data: %w", err)
	}

	// Create output directory if it doesn't exist
	if err := os.MkdirAll(filepath.Dir(outputPath), 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Write GeoJSON file
	file, err := os.Create(outputPath)
	if err != nil {
		return fmt.Errorf("failed to create GeoJSON file: %w", err)
	}
	defer file.Close()

	// Write GeoJSON content
	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(geojsonData); err != nil {
		return fmt.Errorf("failed to write GeoJSON file: %w", err)
	}

	return nil
}

// GetSupportedFormats returns supported formats
func (geojson *GeoJSONFileProcessor) GetSupportedFormats() []ExportFormat {
	return []ExportFormat{ExportFormatGeoJSON}
}

// JSONFileProcessor processes JSON files
type JSONFileProcessor struct {
	logger *zap.Logger
}

// NewJSONFileProcessor creates a new JSON file processor
func NewJSONFileProcessor(logger *zap.Logger) *JSONFileProcessor {
	return &JSONFileProcessor{
		logger: logger,
	}
}

// Process processes data and writes to JSON file
func (jsonProc *JSONFileProcessor) Process(ctx context.Context, data json.RawMessage, outputPath string, config *ExportConfig) error {
	// Create output directory if it doesn't exist
	if err := os.MkdirAll(filepath.Dir(outputPath), 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Write JSON file
	file, err := os.Create(outputPath)
	if err != nil {
		return fmt.Errorf("failed to create JSON file: %w", err)
	}
	defer file.Close()

	// Write JSON content
	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(data); err != nil {
		return fmt.Errorf("failed to write JSON file: %w", err)
	}

	return nil
}

// GetSupportedFormats returns supported formats
func (jsonProc *JSONFileProcessor) GetSupportedFormats() []ExportFormat {
	return []ExportFormat{ExportFormatJSON}
}

// XMLFileProcessor processes XML files
type XMLFileProcessor struct {
	logger *zap.Logger
}

// NewXMLFileProcessor creates a new XML file processor
func NewXMLFileProcessor(logger *zap.Logger) *XMLFileProcessor {
	return &XMLFileProcessor{
		logger: logger,
	}
}

// Process processes data and writes to XML file
func (xmlProc *XMLFileProcessor) Process(ctx context.Context, data json.RawMessage, outputPath string, config *ExportConfig) error {
	var xmlData map[string]interface{}
	if err := json.Unmarshal(data, &xmlData); err != nil {
		return fmt.Errorf("failed to unmarshal XML data: %w", err)
	}

	// Create output directory if it doesn't exist
	if err := os.MkdirAll(filepath.Dir(outputPath), 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Write XML file
	file, err := os.Create(outputPath)
	if err != nil {
		return fmt.Errorf("failed to create XML file: %w", err)
	}
	defer file.Close()

	// Write XML content
	if err := xmlProc.writeXMLContent(file, xmlData); err != nil {
		return fmt.Errorf("failed to write XML content: %w", err)
	}

	return nil
}

// GetSupportedFormats returns supported formats
func (xmlProc *XMLFileProcessor) GetSupportedFormats() []ExportFormat {
	return []ExportFormat{ExportFormatXML}
}

// CSVFileProcessor processes CSV files
type CSVFileProcessor struct {
	logger *zap.Logger
}

// NewCSVFileProcessor creates a new CSV file processor
func NewCSVFileProcessor(logger *zap.Logger) *CSVFileProcessor {
	return &CSVFileProcessor{
		logger: logger,
	}
}

// Process processes data and writes to CSV file
func (csvProc *CSVFileProcessor) Process(ctx context.Context, data json.RawMessage, outputPath string, config *ExportConfig) error {
	var csvData map[string]interface{}
	if err := json.Unmarshal(data, &csvData); err != nil {
		return fmt.Errorf("failed to unmarshal CSV data: %w", err)
	}

	// Create output directory if it doesn't exist
	if err := os.MkdirAll(filepath.Dir(outputPath), 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Write CSV file
	file, err := os.Create(outputPath)
	if err != nil {
		return fmt.Errorf("failed to create CSV file: %w", err)
	}
	defer file.Close()

	// Write CSV content
	if err := csvProc.writeCSVContent(file, csvData); err != nil {
		return fmt.Errorf("failed to write CSV content: %w", err)
	}

	return nil
}

// GetSupportedFormats returns supported formats
func (csvProc *CSVFileProcessor) GetSupportedFormats() []ExportFormat {
	return []ExportFormat{ExportFormatCSV}
}

// PDFFileProcessor processes PDF files
type PDFFileProcessor struct {
	logger *zap.Logger
}

// NewPDFFileProcessor creates a new PDF file processor
func NewPDFFileProcessor(logger *zap.Logger) *PDFFileProcessor {
	return &PDFFileProcessor{
		logger: logger,
	}
}

// Process processes data and writes to PDF file
func (pdf *PDFFileProcessor) Process(ctx context.Context, data json.RawMessage, outputPath string, config *ExportConfig) error {
	// Create output directory if it doesn't exist
	if err := os.MkdirAll(filepath.Dir(outputPath), 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Write PDF file (placeholder implementation)
	file, err := os.Create(outputPath)
	if err != nil {
		return fmt.Errorf("failed to create PDF file: %w", err)
	}
	defer file.Close()

	// Write PDF content (placeholder)
	if err := pdf.writePDFContent(file, data); err != nil {
		return fmt.Errorf("failed to write PDF content: %w", err)
	}

	return nil
}

// GetSupportedFormats returns supported formats
func (pdf *PDFFileProcessor) GetSupportedFormats() []ExportFormat {
	return []ExportFormat{ExportFormatPDF}
}

// DXFFileProcessor processes DXF files
type DXFFileProcessor struct {
	logger *zap.Logger
}

// NewDXFFileProcessor creates a new DXF file processor
func NewDXFFileProcessor(logger *zap.Logger) *DXFFileProcessor {
	return &DXFFileProcessor{
		logger: logger,
	}
}

// Process processes data and writes to DXF file
func (dxf *DXFFileProcessor) Process(ctx context.Context, data json.RawMessage, outputPath string, config *ExportConfig) error {
	// Create output directory if it doesn't exist
	if err := os.MkdirAll(filepath.Dir(outputPath), 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Write DXF file (placeholder implementation)
	file, err := os.Create(outputPath)
	if err != nil {
		return fmt.Errorf("failed to create DXF file: %w", err)
	}
	defer file.Close()

	// Write DXF content (placeholder)
	if err := dxf.writeDXFContent(file, data); err != nil {
		return fmt.Errorf("failed to write DXF content: %w", err)
	}

	return nil
}

// GetSupportedFormats returns supported formats
func (dxf *DXFFileProcessor) GetSupportedFormats() []ExportFormat {
	return []ExportFormat{ExportFormatDXF}
}

// STEPFileProcessor processes STEP files
type STEPFileProcessor struct {
	logger *zap.Logger
}

// NewSTEPFileProcessor creates a new STEP file processor
func NewSTEPFileProcessor(logger *zap.Logger) *STEPFileProcessor {
	return &STEPFileProcessor{
		logger: logger,
	}
}

// Process processes data and writes to STEP file
func (step *STEPFileProcessor) Process(ctx context.Context, data json.RawMessage, outputPath string, config *ExportConfig) error {
	// Create output directory if it doesn't exist
	if err := os.MkdirAll(filepath.Dir(outputPath), 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Write STEP file (placeholder implementation)
	file, err := os.Create(outputPath)
	if err != nil {
		return fmt.Errorf("failed to create STEP file: %w", err)
	}
	defer file.Close()

	// Write STEP content (placeholder)
	if err := step.writeSTEPContent(file, data); err != nil {
		return fmt.Errorf("failed to write STEP content: %w", err)
	}

	return nil
}

// GetSupportedFormats returns supported formats
func (step *STEPFileProcessor) GetSupportedFormats() []ExportFormat {
	return []ExportFormat{ExportFormatSTEP}
}

// IGESFileProcessor processes IGES files
type IGESFileProcessor struct {
	logger *zap.Logger
}

// NewIGESFileProcessor creates a new IGES file processor
func NewIGESFileProcessor(logger *zap.Logger) *IGESFileProcessor {
	return &IGESFileProcessor{
		logger: logger,
	}
}

// Process processes data and writes to IGES file
func (iges *IGESFileProcessor) Process(ctx context.Context, data json.RawMessage, outputPath string, config *ExportConfig) error {
	// Create output directory if it doesn't exist
	if err := os.MkdirAll(filepath.Dir(outputPath), 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Write IGES file (placeholder implementation)
	file, err := os.Create(outputPath)
	if err != nil {
		return fmt.Errorf("failed to create IGES file: %w", err)
	}
	defer file.Close()

	// Write IGES content (placeholder)
	if err := iges.writeIGESContent(file, data); err != nil {
		return fmt.Errorf("failed to write IGES content: %w", err)
	}

	return nil
}

// GetSupportedFormats returns supported formats
func (iges *IGESFileProcessor) GetSupportedFormats() []ExportFormat {
	return []ExportFormat{ExportFormatIGES}
}

// Helper functions for file writing

func (ifc *IFCFileProcessor) writeIFCHeader(file *os.File, config *ExportConfig) error {
	header := fmt.Sprintf(`ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Arxos Export'),'2;1');
FILE_NAME('%s','%s',('Arxos Engineering Team'),('Arxos'),'','','');
FILE_SCHEMA(('IFC2x3'));
ENDSEC;
DATA;
`, time.Now().Format("2006-01-02T15:04:05"), time.Now().Format("2006-01-02T15:04:05"))

	_, err := file.WriteString(header)
	return err
}

func (ifc *IFCFileProcessor) writeIFCEntities(file *os.File, ifcData map[string]interface{}) error {
	if entities, ok := ifcData["entities"].([]interface{}); ok {
		for _, entity := range entities {
			if entityMap, ok := entity.(map[string]interface{}); ok {
				ifcEntity := ifc.formatIFCEntity(entityMap)
				if _, err := file.WriteString(ifcEntity + "\n"); err != nil {
					return err
				}
			}
		}
	}
	return nil
}

func (ifc *IFCFileProcessor) writeIFCFooter(file *os.File) error {
	footer := "ENDSEC;\nEND-ISO-10303-21;\n"
	_, err := file.WriteString(footer)
	return err
}

func (ifc *IFCFileProcessor) formatIFCEntity(entity map[string]interface{}) string {
	// Format IFC entity (simplified)
	id := getStringValue(entity, "global_id", "")
	name := getStringValue(entity, "name", "")
	description := getStringValue(entity, "description", "")

	return fmt.Sprintf("#%s=IFCWALL('%s','%s','%s',$,#%s,#%s,$);",
		id, id, name, description, id, id)
}

func (ascii *ASCIIBIMFileProcessor) writeASCIIBIMContent(file *os.File, asciiData map[string]interface{}) error {
	// Write ASCII BIM header
	header := fmt.Sprintf("ASCII-BIM Version 1.0\nGenerated: %s\n\n", time.Now().Format(time.RFC3339))
	if _, err := file.WriteString(header); err != nil {
		return err
	}

	// Write entities
	if entities, ok := asciiData["entities"].([]interface{}); ok {
		for _, entity := range entities {
			if entityMap, ok := entity.(map[string]interface{}); ok {
				asciiEntity := ascii.formatASCIIBIMEntity(entityMap)
				if _, err := file.WriteString(asciiEntity + "\n"); err != nil {
					return err
				}
			}
		}
	}

	return nil
}

func (ascii *ASCIIBIMFileProcessor) formatASCIIBIMEntity(entity map[string]interface{}) string {
	id := getStringValue(entity, "id", "")
	entityType := getStringValue(entity, "type", "")
	name := getStringValue(entity, "name", "")
	description := getStringValue(entity, "description", "")

	return fmt.Sprintf("ENTITY %s TYPE %s NAME \"%s\" DESCRIPTION \"%s\"",
		id, entityType, name, description)
}

func (excel *ExcelFileProcessor) writeCSVContent(file *os.File, excelData map[string]interface{}) error {
	writer := csv.NewWriter(file)
	defer writer.Flush()

	if sheets, ok := excelData["sheets"].([]interface{}); ok && len(sheets) > 0 {
		if sheet, ok := sheets[0].(map[string]interface{}); ok {
			if headers, ok := sheet["headers"].([]interface{}); ok {
				// Write headers
				headerRow := make([]string, len(headers))
				for i, header := range headers {
					headerRow[i] = fmt.Sprintf("%v", header)
				}
				if err := writer.Write(headerRow); err != nil {
					return err
				}

				// Write data rows
				if rows, ok := sheet["rows"].([][]string); ok {
					for _, row := range rows {
						if err := writer.Write(row); err != nil {
							return err
						}
					}
				}
			}
		}
	}

	return nil
}

func (csvProc *CSVFileProcessor) writeCSVContent(file *os.File, csvData map[string]interface{}) error {
	writer := csv.NewWriter(file)
	defer writer.Flush()

	// Write CSV content based on data structure
	if data, ok := csvData["data"].([]interface{}); ok {
		for _, row := range data {
			if rowMap, ok := row.(map[string]interface{}); ok {
				csvRow := make([]string, 0)
				for _, value := range rowMap {
					csvRow = append(csvRow, fmt.Sprintf("%v", value))
				}
				if err := writer.Write(csvRow); err != nil {
					return err
				}
			}
		}
	}

	return nil
}

func (xmlProc *XMLFileProcessor) writeXMLContent(file *os.File, xmlData map[string]interface{}) error {
	// Write XML header
	if _, err := file.WriteString("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"); err != nil {
		return err
	}

	// Write XML content
	encoder := xml.NewEncoder(file)
	encoder.Indent("", "  ")

	// Convert to XML structure
	xmlStruct := xmlProc.convertToXMLStructure(xmlData)

	if err := encoder.Encode(xmlStruct); err != nil {
		return err
	}

	return nil
}

func (xmlProc *XMLFileProcessor) convertToXMLStructure(data map[string]interface{}) interface{} {
	// Convert data to XML structure
	return map[string]interface{}{
		"root": data,
	}
}

func (pdf *PDFFileProcessor) writePDFContent(file *os.File, data json.RawMessage) error {
	// Placeholder PDF content
	content := fmt.Sprintf("PDF Content\nGenerated: %s\nData: %s",
		time.Now().Format(time.RFC3339), string(data))

	_, err := file.WriteString(content)
	return err
}

func (dxf *DXFFileProcessor) writeDXFContent(file *os.File, data json.RawMessage) error {
	// Placeholder DXF content
	content := fmt.Sprintf("0\nSECTION\n2\nHEADER\n0\nENDSEC\n0\nSECTION\n2\nENTITIES\n0\nENDSEC\n0\nEOF\n")

	_, err := file.WriteString(content)
	return err
}

func (step *STEPFileProcessor) writeSTEPContent(file *os.File, data json.RawMessage) error {
	// Placeholder STEP content
	content := fmt.Sprintf("ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;\n")

	_, err := file.WriteString(content)
	return err
}

func (iges *IGESFileProcessor) writeIGESContent(file *os.File, data json.RawMessage) error {
	// Placeholder IGES content
	content := fmt.Sprintf("IGES file\nGenerated: %s\n", time.Now().Format(time.RFC3339))

	_, err := file.WriteString(content)
	return err
}

// Helper functions

func getStringValue(data map[string]interface{}, key, defaultValue string) string {
	if value, ok := data[key]; ok {
		if str, ok := value.(string); ok {
			return str
		}
	}
	return defaultValue
}
