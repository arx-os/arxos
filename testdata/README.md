# Test Data Directory

This directory contains test fixtures and sample data for ArxOS testing.

## Structure

```
testdata/
├── fixtures/      # Test fixtures (if any)
├── watch/         # Files for testing file watch functionality
├── output/        # Test output files (gitignored)
├── temp/          # Temporary test files (gitignored)
└── *.pdf          # Sample PDF floor plans for testing
```

## Sample Files

- `Alafia_ES_IDF_CallOut.pdf` - Sample floor plan PDF for testing import
- `Alafia_ES_IDF_CallOut_Content_page_1.txt` - Extracted text from PDF for testing
- `test_export.pdf` - Sample export output (should be gitignored)

## Usage in Tests

```go
// Example test usage
pdfPath := filepath.Join("testdata", "Alafia_ES_IDF_CallOut.pdf")
result, err := ImportPDF(pdfPath)
```

## Note

Keep test data files small and sanitized. Do not commit:
- Proprietary building plans
- Files with sensitive information
- Large binary files (>1MB unless necessary)