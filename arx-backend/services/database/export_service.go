package database

import (
	"context"
	"encoding/csv"
	"encoding/json"
	"encoding/xml"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"go.uber.org/zap"
)

// ExportFormat represents supported export formats
type ExportFormat string

const (
	ExportFormatJSON  ExportFormat = "json"
	ExportFormatXML   ExportFormat = "xml"
	ExportFormatCSV   ExportFormat = "csv"
	ExportFormatIFC   ExportFormat = "ifc"
	ExportFormatGBXML ExportFormat = "gbxml"
)

// ExportOptions holds export configuration
type ExportOptions struct {
	Format               ExportFormat           `json:"format"`
	IncludeMetadata      bool                   `json:"include_metadata"`
	IncludeGeometry      bool                   `json:"include_geometry"`
	IncludeProperties    bool                   `json:"include_properties"`
	IncludeRelationships bool                   `json:"include_relationships"`
	PrettyPrint          bool                   `json:"pretty_print"`
	Compression          bool                   `json:"compression"`
	CoordinateSystem     string                 `json:"coordinate_system"`
	Units                string                 `json:"units"`
	CustomOptions        map[string]interface{} `json:"custom_options"`
}

// ExportJob represents an export job
type ExportJobInfo struct {
	ID             string                 `json:"id"`
	JobType        string                 `json:"job_type"`
	ExportFormat   ExportFormat           `json:"export_format"`
	Status         string                 `json:"status"`
	Progress       int                    `json:"progress"`
	TotalItems     int                    `json:"total_items"`
	ProcessedItems int                    `json:"processed_items"`
	FilePath       string                 `json:"file_path"`
	FileSize       int64                  `json:"file_size"`
	Errors         []string               `json:"errors"`
	CreatedBy      string                 `json:"created_by"`
	CreatedAt      time.Time              `json:"created_at"`
	UpdatedAt      time.Time              `json:"updated_at"`
	CompletedAt    *time.Time             `json:"completed_at"`
	Properties     map[string]interface{} `json:"properties"`
}

// ExportService provides export functionality
type ExportService struct {
	dbService *DatabaseService
	logger    *zap.Logger
}

// NewExportService creates a new export service
func NewExportService(dbService *DatabaseService, logger *zap.Logger) *ExportService {
	return &ExportService{
		dbService: dbService,
		logger:    logger,
	}
}

// ExportBIMModel exports a BIM model to the specified format
func (es *ExportService) ExportBIMModel(ctx context.Context, modelID string, format ExportFormat, options *ExportOptions, outputPath string) error {
	if options == nil {
		options = &ExportOptions{
			Format:               format,
			IncludeMetadata:      true,
			IncludeGeometry:      true,
			IncludeProperties:    true,
			IncludeRelationships: true,
			PrettyPrint:          true,
			Compression:          false,
			CoordinateSystem:     "local",
			Units:                "meters",
		}
	}

	// Load the BIM model
	model, err := es.loadBIMModelForExport(ctx, modelID)
	if err != nil {
		return fmt.Errorf("failed to load BIM model for export: %w", err)
	}

	// Create output directory if it doesn't exist
	outputDir := filepath.Dir(outputPath)
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Export based on format
	switch format {
	case ExportFormatJSON:
		return es.exportToJSON(model, options, outputPath)
	case ExportFormatXML:
		return es.exportToXML(model, options, outputPath)
	case ExportFormatCSV:
		return es.exportToCSV(model, options, outputPath)
	case ExportFormatIFC:
		return es.exportToIFC(model, options, outputPath)
	case ExportFormatGBXML:
		return es.exportToGBXML(model, options, outputPath)
	default:
		return fmt.Errorf("unsupported export format: %s", format)
	}
}

// exportToJSON exports BIM model to JSON format
func (es *ExportService) exportToJSON(model *BIMModel, options *ExportOptions, outputPath string) error {
	exportData := es.prepareExportData(model, options)

	var data []byte
	var err error

	if options.PrettyPrint {
		data, err = json.MarshalIndent(exportData, "", "  ")
	} else {
		data, err = json.Marshal(exportData)
	}

	if err != nil {
		return fmt.Errorf("failed to marshal JSON: %w", err)
	}

	if err := os.WriteFile(outputPath, data, 0644); err != nil {
		return fmt.Errorf("failed to write JSON file: %w", err)
	}

	es.logger.Info("BIM model exported to JSON",
		zap.String("model_id", model.ID),
		zap.String("output_path", outputPath),
		zap.Int("file_size", len(data)))

	return nil
}

// exportToXML exports BIM model to XML format
func (es *ExportService) exportToXML(model *BIMModel, options *ExportOptions, outputPath string) error {
	exportData := es.prepareExportData(model, options)

	// Create XML structure
	xmlData := &XMLBIMModel{
		XMLName:   xml.Name{Local: "BIMModel"},
		ID:        model.ID,
		Name:      model.Name,
		Version:   model.Version,
		CreatedAt: model.CreatedAt.Format(time.RFC3339),
		UpdatedAt: model.UpdatedAt.Format(time.RFC3339),
		Data:      exportData,
	}

	data, err := xml.MarshalIndent(xmlData, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal XML: %w", err)
	}

	// Add XML declaration
	xmlContent := xml.Header + string(data)

	if err := os.WriteFile(outputPath, []byte(xmlContent), 0644); err != nil {
		return fmt.Errorf("failed to write XML file: %w", err)
	}

	es.logger.Info("BIM model exported to XML",
		zap.String("model_id", model.ID),
		zap.String("output_path", outputPath),
		zap.Int("file_size", len(xmlContent)))

	return nil
}

// exportToCSV exports BIM model to CSV format
func (es *ExportService) exportToCSV(model *BIMModel, options *ExportOptions, outputPath string) error {
	exportData := es.prepareExportData(model, options)

	file, err := os.Create(outputPath)
	if err != nil {
		return fmt.Errorf("failed to create CSV file: %w", err)
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()

	// Write header
	headers := []string{"ID", "Name", "Description", "CreatedBy", "ProjectID", "Version", "Status", "CreatedAt", "UpdatedAt"}
	if err := writer.Write(headers); err != nil {
		return fmt.Errorf("failed to write CSV header: %w", err)
	}

	// Write model data
	row := []string{
		model.ID,
		model.Name,
		model.Description,
		model.CreatedBy,
		model.ProjectID,
		model.Version,
		model.Status,
		model.CreatedAt.Format(time.RFC3339),
		model.UpdatedAt.Format(time.RFC3339),
	}

	if err := writer.Write(row); err != nil {
		return fmt.Errorf("failed to write CSV row: %w", err)
	}

	// Write metadata if included
	if options.IncludeMetadata && model.ModelMetadata != nil {
		var metadata map[string]interface{}
		if err := json.Unmarshal(model.ModelMetadata, &metadata); err == nil {
			for key, value := range metadata {
				row := []string{"metadata", key, fmt.Sprintf("%v", value), "", "", "", "", "", ""}
				writer.Write(row)
			}
		}
	}

	es.logger.Info("BIM model exported to CSV",
		zap.String("model_id", model.ID),
		zap.String("output_path", outputPath))

	return nil
}

// exportToIFC exports BIM model to IFC format
func (es *ExportService) exportToIFC(model *BIMModel, options *ExportOptions, outputPath string) error {
	// IFC export is a placeholder implementation
	// In a real implementation, this would generate proper IFC format

	ifcContent := es.generateIFCContent(model, options)

	if err := os.WriteFile(outputPath, []byte(ifcContent), 0644); err != nil {
		return fmt.Errorf("failed to write IFC file: %w", err)
	}

	es.logger.Info("BIM model exported to IFC",
		zap.String("model_id", model.ID),
		zap.String("output_path", outputPath),
		zap.Int("file_size", len(ifcContent)))

	return nil
}

// exportToGBXML exports BIM model to gbXML format
func (es *ExportService) exportToGBXML(model *BIMModel, options *ExportOptions, outputPath string) error {
	// gbXML export is a placeholder implementation
	// In a real implementation, this would generate proper gbXML format

	gbxmlContent := es.generateGBXMLContent(model, options)

	if err := os.WriteFile(outputPath, []byte(gbxmlContent), 0644); err != nil {
		return fmt.Errorf("failed to write gbXML file: %w", err)
	}

	es.logger.Info("BIM model exported to gbXML",
		zap.String("model_id", model.ID),
		zap.String("output_path", outputPath),
		zap.Int("file_size", len(gbxmlContent)))

	return nil
}

// prepareExportData prepares data for export based on options
func (es *ExportService) prepareExportData(model *BIMModel, options *ExportOptions) map[string]interface{} {
	exportData := map[string]interface{}{
		"id":          model.ID,
		"name":        model.Name,
		"description": model.Description,
		"version":     model.Version,
		"status":      model.Status,
		"created_at":  model.CreatedAt.Format(time.RFC3339),
		"updated_at":  model.UpdatedAt.Format(time.RFC3339),
		"created_by":  model.CreatedBy,
		"project_id":  model.ProjectID,
		"tags":        model.Tags,
	}

	// Include model data
	if model.ModelData != nil {
		var modelData map[string]interface{}
		if err := json.Unmarshal(model.ModelData, &modelData); err == nil {
			exportData["model_data"] = modelData
		}
	}

	// Include metadata if requested
	if options.IncludeMetadata && model.ModelMetadata != nil {
		var metadata map[string]interface{}
		if err := json.Unmarshal(model.ModelMetadata, &metadata); err == nil {
			exportData["metadata"] = metadata
		}
	}

	// Include properties if requested
	if options.IncludeProperties && model.Properties != nil {
		exportData["properties"] = model.Properties
	}

	// Add export options
	exportData["export_options"] = map[string]interface{}{
		"format":                options.Format,
		"include_metadata":      options.IncludeMetadata,
		"include_geometry":      options.IncludeGeometry,
		"include_properties":    options.IncludeProperties,
		"include_relationships": options.IncludeRelationships,
		"coordinate_system":     options.CoordinateSystem,
		"units":                 options.Units,
		"exported_at":           time.Now().Format(time.RFC3339),
	}

	return exportData
}

// loadBIMModelForExport loads a BIM model for export
func (es *ExportService) loadBIMModelForExport(ctx context.Context, modelID string) (*BIMModel, error) {
	query := `
		SELECT id, name, description, model_data, model_metadata,
			   created_by, project_id, version, created_at, updated_at,
			   status, tags, properties
		FROM bim_models
		WHERE id = ?
	`

	var model BIMModel
	var tagsJSON, propertiesJSON []byte

	err := es.dbService.db.QueryRowContext(ctx, query, modelID).Scan(
		&model.ID, &model.Name, &model.Description, &model.ModelData, &model.ModelMetadata,
		&model.CreatedBy, &model.ProjectID, &model.Version, &model.CreatedAt, &model.UpdatedAt,
		&model.Status, &tagsJSON, &propertiesJSON,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to load BIM model: %w", err)
	}

	// Parse JSON fields
	if len(tagsJSON) > 0 {
		json.Unmarshal(tagsJSON, &model.Tags)
	}
	if len(propertiesJSON) > 0 {
		json.Unmarshal(propertiesJSON, &model.Properties)
	}

	return &model, nil
}

// generateIFCContent generates IFC content (placeholder)
func (es *ExportService) generateIFCContent(model *BIMModel, options *ExportOptions) string {
	var sb strings.Builder

	sb.WriteString("ISO-10303-21;\n")
	sb.WriteString("HEADER;\n")
	sb.WriteString("FILE_DESCRIPTION(('Arxos BIM Export'),'2;1');\n")
	sb.WriteString("FILE_NAME('" + model.Name + "','" + time.Now().Format("2006-01-02T15:04:05") + "',('Arxos'),(''),'Arxos BIM System','','');\n")
	sb.WriteString("FILE_SCHEMA(('IFC4'));\n")
	sb.WriteString("ENDSEC;\n")
	sb.WriteString("DATA;\n")
	sb.WriteString("#1=IFCPROJECT('" + model.ID + "',#2,'" + model.Name + "',$,$,$,$,(#3),#4);\n")
	sb.WriteString("#2=IFCOWNERHISTORY(#5,#6,$,.ADDED.,$,$,$,0);\n")
	sb.WriteString("#3=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-005,#7,$);\n")
	sb.WriteString("#4=IFCUNITASSIGNMENT((#8,#9));\n")
	sb.WriteString("#5=IFCPERSONANDORGANIZATION(#10,#11,$);\n")
	sb.WriteString("#6=IFCAPPLICATION(#12,'Arxos BIM System','1.0');\n")
	sb.WriteString("#7=IFCDIRECTION((0.,0.,1.));\n")
	sb.WriteString("#8=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);\n")
	sb.WriteString("#9=IFCSIUNIT(*,.AREAUNIT.,$,.SQUARE_METRE.);\n")
	sb.WriteString("#10=IFCPERSON('" + model.CreatedBy + "','Unknown','Unknown',$,$,$,$,$);\n")
	sb.WriteString("#11=IFCORGANIZATION('Arxos','Arxos BIM System',$,$,$);\n")
	sb.WriteString("#12=IFCAPPLICATION(#11,'Arxos BIM System','1.0');\n")
	sb.WriteString("ENDSEC;\n")
	sb.WriteString("END-ISO-10303-21;\n")

	return sb.String()
}

// generateGBXMLContent generates gbXML content (placeholder)
func (es *ExportService) generateGBXMLContent(model *BIMModel, options *ExportOptions) string {
	var sb strings.Builder

	sb.WriteString("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
	sb.WriteString("<gbXML version=\"0.37\" temperatureUnit=\"C\" lengthUnit=\"Meters\" areaUnit=\"SquareMeters\" volumeUnit=\"CubicMeters\" useSIUnitsForResults=\"true\">\n")
	sb.WriteString("  <Campus id=\"Campus_1\">\n")
	sb.WriteString("    <Location>\n")
	sb.WriteString("      <Longitude>0.0</Longitude>\n")
	sb.WriteString("      <Latitude>0.0</Latitude>\n")
	sb.WriteString("      <Elevation>0</Elevation>\n")
	sb.WriteString("    </Location>\n")
	sb.WriteString("    <Building id=\"Building_1\" buildingType=\"Office\">\n")
	sb.WriteString("      <Area>1000</Area>\n")
	sb.WriteString("      <Storey id=\"Storey_1\">\n")
	sb.WriteString("        <Level>0</Level>\n")
	sb.WriteString("        <PlanarGeometry>\n")
	sb.WriteString("          <PolyLoop>\n")
	sb.WriteString("            <CartesianPoint>\n")
	sb.WriteString("              <Coordinate>0</Coordinate>\n")
	sb.WriteString("              <Coordinate>0</Coordinate>\n")
	sb.WriteString("              <Coordinate>0</Coordinate>\n")
	sb.WriteString("            </CartesianPoint>\n")
	sb.WriteString("          </PolyLoop>\n")
	sb.WriteString("        </PlanarGeometry>\n")
	sb.WriteString("      </Storey>\n")
	sb.WriteString("    </Building>\n")
	sb.WriteString("  </Campus>\n")
	sb.WriteString("</gbXML>\n")

	return sb.String()
}

// CreateExportJob creates a new export job
func (es *ExportService) CreateExportJob(ctx context.Context, jobType string, exportFormat ExportFormat, totalItems int) (*ExportJobInfo, error) {
	job := &ExportJobInfo{
		ID:             generateID(),
		JobType:        jobType,
		ExportFormat:   exportFormat,
		Status:         "pending",
		Progress:       0,
		TotalItems:     totalItems,
		ProcessedItems: 0,
		CreatedAt:      time.Now(),
		UpdatedAt:      time.Now(),
		Errors:         []string{},
		Properties:     make(map[string]interface{}),
	}

	query := `
		INSERT INTO export_jobs (
			id, job_type, export_format, status, progress, total_items,
			processed_items, file_path, file_size, errors, created_by,
			created_at, updated_at, completed_at, properties
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	`

	errorsJSON, _ := json.Marshal(job.Errors)
	propertiesJSON, _ := json.Marshal(job.Properties)

	_, err := es.dbService.db.ExecContext(ctx, query,
		job.ID, job.JobType, string(job.ExportFormat), job.Status, job.Progress, job.TotalItems,
		job.ProcessedItems, job.FilePath, job.FileSize, errorsJSON, job.CreatedBy,
		job.CreatedAt, job.UpdatedAt, job.CompletedAt, propertiesJSON,
	)

	if err != nil {
		es.logger.Error("Failed to create export job", zap.Error(err))
		return nil, fmt.Errorf("failed to create export job: %w", err)
	}

	es.logger.Info("Export job created", zap.String("job_id", job.ID))
	return job, nil
}

// UpdateExportJob updates an export job
func (es *ExportService) UpdateExportJob(ctx context.Context, jobID string, status string, progress int, processedItems int, filePath string, fileSize int64, errors []string) error {
	now := time.Now()
	var completedAt *time.Time
	if status == "completed" || status == "failed" {
		completedAt = &now
	}

	query := `
		UPDATE export_jobs SET
			status = ?, progress = ?, processed_items = ?, file_path = ?,
			file_size = ?, errors = ?, updated_at = ?, completed_at = ?
		WHERE id = ?
	`

	errorsJSON, _ := json.Marshal(errors)

	_, err := es.dbService.db.ExecContext(ctx, query,
		status, progress, processedItems, filePath, fileSize, errorsJSON, now, completedAt, jobID,
	)

	if err != nil {
		es.logger.Error("Failed to update export job", zap.String("job_id", jobID), zap.Error(err))
		return fmt.Errorf("failed to update export job: %w", err)
	}

	es.logger.Info("Export job updated", zap.String("job_id", jobID), zap.String("status", status))
	return nil
}

// GetExportJob retrieves an export job
func (es *ExportService) GetExportJob(ctx context.Context, jobID string) (*ExportJobInfo, error) {
	query := `
		SELECT id, job_type, export_format, status, progress, total_items,
			   processed_items, file_path, file_size, errors, created_by,
			   created_at, updated_at, completed_at, properties
		FROM export_jobs
		WHERE id = ?
	`

	var job ExportJobInfo
	var errorsJSON, propertiesJSON []byte

	err := es.dbService.db.QueryRowContext(ctx, query, jobID).Scan(
		&job.ID, &job.JobType, &job.ExportFormat, &job.Status, &job.Progress, &job.TotalItems,
		&job.ProcessedItems, &job.FilePath, &job.FileSize, &errorsJSON, &job.CreatedBy,
		&job.CreatedAt, &job.UpdatedAt, &job.CompletedAt, &propertiesJSON,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to get export job: %w", err)
	}

	// Parse JSON fields
	if len(errorsJSON) > 0 {
		json.Unmarshal(errorsJSON, &job.Errors)
	}
	if len(propertiesJSON) > 0 {
		json.Unmarshal(propertiesJSON, &job.Properties)
	}

	return &job, nil
}

// ListExportJobs lists export jobs
func (es *ExportService) ListExportJobs(ctx context.Context, status string) ([]*ExportJobInfo, error) {
	query := `
		SELECT id, job_type, export_format, status, progress, total_items,
			   processed_items, file_path, file_size, errors, created_by,
			   created_at, updated_at, completed_at, properties
		FROM export_jobs
	`
	args := []interface{}{}

	if status != "" {
		query += " WHERE status = ?"
		args = append(args, status)
	}
	query += " ORDER BY created_at DESC"

	rows, err := es.dbService.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to list export jobs: %w", err)
	}
	defer rows.Close()

	var jobs []*ExportJobInfo
	for rows.Next() {
		var job ExportJobInfo
		var errorsJSON, propertiesJSON []byte

		err := rows.Scan(
			&job.ID, &job.JobType, &job.ExportFormat, &job.Status, &job.Progress, &job.TotalItems,
			&job.ProcessedItems, &job.FilePath, &job.FileSize, &errorsJSON, &job.CreatedBy,
			&job.CreatedAt, &job.UpdatedAt, &job.CompletedAt, &propertiesJSON,
		)
		if err != nil {
			es.logger.Error("Failed to scan export job row", zap.Error(err))
			continue
		}

		// Parse JSON fields
		if len(errorsJSON) > 0 {
			json.Unmarshal(errorsJSON, &job.Errors)
		}
		if len(propertiesJSON) > 0 {
			json.Unmarshal(propertiesJSON, &job.Properties)
		}

		jobs = append(jobs, &job)
	}

	return jobs, nil
}

// XMLBIMModel represents XML structure for BIM model export
type XMLBIMModel struct {
	XMLName   xml.Name               `xml:"BIMModel"`
	ID        string                 `xml:"id,attr"`
	Name      string                 `xml:"name,attr"`
	Version   string                 `xml:"version,attr"`
	CreatedAt string                 `xml:"created_at,attr"`
	UpdatedAt string                 `xml:"updated_at,attr"`
	Data      map[string]interface{} `xml:"data"`
}

// generateID generates a unique ID
func generateID() string {
	return strconv.FormatInt(time.Now().UnixNano(), 10)
}
