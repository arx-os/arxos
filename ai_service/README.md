# AI Service

Python-based AI service for ARXOS building information processing and extraction.

## Purpose

This service handles the ingestion and processing of building data formats (PDF, IFC, DWG, HEIC, LiDAR) and converts them into ArxObjects using AI-powered symbol recognition and classification.

## Structure

```
ai_service/
├── main.py              # FastAPI application entry point
├── models/              # Data models and schemas
├── processors/          # PDF/IFC processing logic
├── tests/               # Test files
├── utils/               # Utility functions
└── requirements.txt     # Python dependencies
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start service
python main.py
```

## Documentation

For detailed information, see [AI Service Documentation](../../docs/development/guide.md#python-ai-service-development).

## Testing

```bash
# Run tests
python -m pytest tests/
```
