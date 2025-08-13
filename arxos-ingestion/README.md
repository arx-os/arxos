# Arxos Ingestion - Getting Building Data In

## Purpose
This module handles all methods of getting building data into Arxos by converting various sources (PDFs, photos, LiDAR) into ArxObjects.

## Three Ingestion Methods

### 1. PDF/IFC Files
When you have digital building plans:
- Extracts vector graphics and text
- Uses Symbol Library for automatic recognition
- Creates ArxObjects with proper hierarchy

### 2. Photo of Paper Maps
The HCPS reality - paper maps at every school:
- Perspective correction for angled photos
- OCR for room numbers
- Edge detection for walls
- Creates basic floor plan from photo

### 3. LiDAR Field Capture
When nothing exists - create from scratch:
- Real-time wall tracing
- Point-and-mark for outlets/fixtures
- AR overlay showing capture progress
- Build entire model on-site

## Key Components

- `symbols/` - Symbol library for recognition
- `pdf/` - PDF parsing and extraction
- `photo/` - Photo processing and OCR
- `lidar/` - LiDAR point cloud processing

## How It Works

```go
// Example: Ingest a PDF floor plan
pdfData, _ := ioutil.ReadFile("floor-plan.pdf")
objects, _ := ingestion.IngestPDF(pdfData)

// Example: Process photo of paper map
photo, _ := ioutil.ReadFile("desk-map-photo.jpg")
objects, _ := ingestion.IngestPhoto(photo)

// Example: Start LiDAR capture session
session := ingestion.StartLiDARSession()
objects, _ := session.Capture()
```

## Symbol Recognition

The ingestion system uses a comprehensive symbol library to automatically identify:
- Electrical: outlets, switches, panels, lights
- HVAC: diffusers, thermostats, units
- Plumbing: fixtures, valves, drains
- Fire: sprinklers, alarms, extinguishers

Each recognized symbol becomes an ArxObject with appropriate properties and system classification.