# PDF Upload Guide

## Overview

This guide explains how to upload PDF (or SVG) building drawings to the Arx SVG Parser microservice, automatically recognize and render building system symbols, and extract BIM data from the results.

## Workflow: PDF/SVG to BIM

1. **Upload your PDF or SVG drawing**
2. **Auto-recognize and render symbols**
   - Use the `/v1/parse/auto-recognize-and-render` endpoint
   - The service will:
     - Convert PDF to SVG (if PDF)
     - Recognize all known building system symbols
     - Render recognized symbols as SVG elements with metadata
     - Return the annotated SVG and recognition summary
3. **(Optional) Update or remove symbols**
   - Use `/v1/parse/update-symbol-position` or `/v1/parse/remove-symbol` to adjust the SVG
4. **Extract BIM data**
   - Use `/v1/parse/extract-bim` with the annotated SVG
   - Returns structured BIM data (devices, rooms, systems, relationships)

## Example: Upload and Process a PDF

```bash
curl -X POST http://localhost:8000/v1/parse/auto-recognize-and-render \
  -F "file=@your_drawing.pdf" \
  -F "building_id=MY_BUILDING" \
  -F "floor_label=LEVEL_1" \
  -F "confidence_threshold=0.5"
```
- **Response:**
  - `svg`: Annotated SVG with rendered symbols
  - `recognized_symbols`: List of recognized symbols
  - `rendered_symbols`: List of rendered symbol objects
  - `summary`: Processing summary (rooms, devices, systems, confidence)

## Example: Extract BIM Data from Annotated SVG

```bash
curl -X POST http://localhost:8000/v1/parse/extract-bim \
  -F "svg_content=@annotated.svg" \
  -F "building_id=MY_BUILDING" \
  -F "floor_label=LEVEL_1"
```
- **Response:**
  - `devices`: List of extracted devices
  - `rooms`: List of rooms
  - `systems`: System classification
  - `relationships`: Device relationships

## Troubleshooting

- **PDF not converting?**
  - Ensure Poppler is installed and available in your system PATH (required for PDF-to-SVG conversion)
  - On Windows, download Poppler from [http://blog.alivate.com.au/poppler-windows/](http://blog.alivate.com.au/poppler-windows/) and add the `bin` directory to your PATH
- **Symbols not recognized?**
  - Check that your drawing uses standard abbreviations or names (e.g., "AHU", "RTU", "VAV")
  - Increase the `confidence_threshold` if too many false positives
- **SVG output looks wrong?**
  - Open the SVG in a modern browser or vector editor (e.g., Inkscape)
  - Use `/v1/parse/update-symbol-position` to adjust symbol locations
- **BIM extraction missing data?**
  - Ensure symbols are rendered and have correct metadata in the SVG
  - Use `/v1/parse/recognize-symbols` to debug symbol recognition on your SVG

## Advanced Usage

- **Batch processing:** Use `/v1/parse/batch-parse` for multiple SVGs
- **Symbol library info:** Use `/v1/parse/symbol-library` to see all available symbols and systems
- **API docs:** Visit [http://localhost:8000/docs](http://localhost:8000/docs) for interactive documentation

## Support

If you encounter issues, please provide:
- The PDF/SVG file you tried to upload
- The full API request and response (with error message)
- Your OS and Poppler installation details

---

For more details, see the main [README.md](./README.md). 