# Bulk Operations Documentation

## Overview

Bulk operations allow you to efficiently manage multiple symbols at once:

- **Export** multiple symbols to files (JSON, CSV)
- **Import** multiple symbols from files (JSON, CSV)
- **Background processing** for large datasets
- **Progress tracking** for long-running operations
- **Error handling** with detailed reporting

## Bulk Import

### Endpoint
```
POST /api/v1/symbols/bulk-import
```

### Description
Upload a file containing multiple symbols for bulk import. Supports JSON and CSV formats.

### Request
- **Content-Type**: `multipart/form-data`
- **File**: Symbol file (JSON or CSV)

### Supported Formats

#### JSON Format
```json
[
  {
    "name": "HVAC Unit",
    "system": "mechanical",
    "svg": {
      "content": "<g id=\"hvac\">...</g>"
    },
    "description": "Air handling unit",
    "properties": {
      "capacity": "5000 CFM",
      "voltage": "480V"
    }
  },
  {
    "name": "Electrical Outlet",
    "system": "electrical",
    "svg": {
      "content": "<g id=\"outlet\">...</g>"
    },
    "description": "Standard electrical outlet",
    "properties": {
      "voltage": "120V",
      "amperage": "20A"
    }
  }
]
```

#### CSV Format
```csv
name,system,description,svg_content,properties
HVAC Unit,mechanical,Air handling unit,"<g id=""hvac"">...</g>","{""capacity"": ""5000 CFM""}"
Electrical Outlet,electrical,Standard electrical outlet,"<g id=""outlet"">...</g>","{""voltage"": ""120V""}"
```

### Response
```json
{
  "total_processed": 10,
  "successful": 8,
  "failed": 2,
  "errors": [
    {
      "row": 3,
      "error": "Invalid system type: 'invalid_system'"
    }
  ],
  "job_id": "bulk_import_20241201_143022_12345"
}
```

## Bulk Export

### Endpoint
```
GET /api/v1/symbols/export
```

### Parameters
- `format` (optional): Export format (`json`, `csv`) - Default: `json`
- `system` (optional): Filter by system type
- `category` (optional): Filter by category

### Response
```json
{
  "format": "json",
  "total_symbols": 150,
  "download_url": "/api/v1/symbols/export/download?job_id=export_20241201_143022_12345",
  "expires_at": "2024-12-01T15:30:22Z"
}
```

## Progress Tracking

### Get Job Progress
```
GET /api/v1/symbols/progress/{job_id}
```

### Response
```json
{
  "job_id": "bulk_import_20241201_143022_12345",
  "status": "processing",
  "progress": 75,
  "total_items": 100,
  "processed_items": 75,
  "errors": [],
  "result": null
}
```

## Download Export

### Endpoint
```
GET /api/v1/symbols/export/download
```

### Parameters
- `job_id`: Export job ID

### Response
- **Content-Type**: `application/json` or `text/csv`
- **Content-Disposition**: `attachment; filename="symbols_export_20241201_143022.json"`

## Error Handling

### Common Errors

#### Invalid File Format
```json
{
  "detail": "Unsupported file format. Supported formats: JSON, CSV"
}
```

#### Parsing Error
```json
{
  "detail": "Failed to parse file: Invalid JSON syntax"
}
```

#### Validation Error
```json
{
  "detail": "Validation failed",
  "errors": [
    {
      "row": 2,
      "field": "system",
      "error": "Invalid system type: 'invalid_system'"
    }
  ]
}
```

## Best Practices

### File Preparation
- Validate your data before uploading
- Use consistent naming conventions
- Include all required fields
- Test with small datasets first

### Performance
- Use background processing for large files
- Monitor progress for long-running operations
- Handle errors gracefully
- Implement retry logic for failed operations

### Security
- Validate file types and content
- Limit file sizes appropriately
- Sanitize user input
- Implement proper authentication

### Troubleshooting

#### Common Issues
1. **File too large**: Split into smaller files
2. **Invalid format**: Check file structure and encoding
3. **Missing fields**: Ensure all required fields are present
4. **Network timeouts**: Use background processing for large files

#### Debugging
- Check job progress for detailed error information
- Validate file format before upload
- Review error logs for system issues
- Test with sample data first

## API Examples

### Python Client
```python
import requests

# Bulk import
with open('symbols.json', 'rb') as f:
    files = {'file': ('symbols.json', f, 'application/json')}
    response = requests.post('/api/v1/symbols/bulk-import', files=files)
    print(response.json())

# Bulk export
response = requests.get('/api/v1/symbols/export?format=json')
export_data = response.json()
job_id = export_data['job_id']

# Check progress
response = requests.get(f'/api/v1/symbols/progress/{job_id}')
progress = response.json()
print(f"Progress: {progress['progress']}%")

# Download when complete
if progress['status'] == 'completed':
    response = requests.get(f'/api/v1/symbols/export/download?job_id={job_id}')
    with open('exported_symbols.json', 'wb') as f:
        f.write(response.content)
```

### cURL Examples
```bash
# Bulk import
curl -X POST /api/v1/symbols/bulk-import \
  -F "file=@symbols.json"

# Bulk export
curl -X GET "/api/v1/symbols/export?format=json"

# Check progress
curl -X GET "/api/v1/symbols/progress/job_id"

# Download export
curl -X GET "/api/v1/symbols/export/download?job_id=job_id" \
  -o exported_symbols.json
```

## File Format Specifications

### JSON Format
- **Structure**: Array of symbol objects
- **Encoding**: UTF-8
- **Required fields**: `name`, `system`, `svg`
- **Optional fields**: `description`, `properties`, `connections`, `tags`

### CSV Format
- **Encoding**: UTF-8
- **Delimiter**: Comma
- **Quote character**: Double quote
- **Required columns**: `name`, `system`, `svg_content`
- **Optional columns**: `description`, `properties`, `connections`, `tags`

## Validation Rules

### Symbol Validation
- Verify file format (JSON, CSV)
- Check required fields
- Validate system types
- Ensure SVG content is valid
- Verify property formats

### Error Reporting
- Detailed error messages
- Row/field specific errors
- Validation failure reasons
- Suggested fixes 