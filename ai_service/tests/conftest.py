"""
Test configuration and fixtures for AI service
Following pytest best practices with async support
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Generator, Any

import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from models.arxobject import (
    ArxObject, ConfidenceScore, ArxObjectType, 
    ValidationState, Metadata, Relationship
)
from utils.config import Settings


# Test settings with overrides
class TestSettings(Settings):
    """Test-specific settings"""
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql://test:test@localhost/arxos_test"
    REDIS_URL: str = "redis://localhost:6379/1"
    HOST: str = "127.0.0.1"
    PORT: int = 8001
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://testserver"]


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """Provide test settings"""
    return TestSettings()


@pytest.fixture
def test_client():
    """Create test client for FastAPI app"""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client():
    """Create async test client for FastAPI app"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_confidence_score():
    """Sample confidence score for testing"""
    return ConfidenceScore(
        classification=0.85,
        position=0.92,
        properties=0.78,
        relationships=0.65,
        overall=0.0  # Will be calculated
    )


@pytest.fixture
def sample_arxobject(sample_confidence_score):
    """Sample ArxObject for testing"""
    return ArxObject(
        id="test_wall_001",
        type=ArxObjectType.WALL,
        data={
            "material": "drywall",
            "thickness": 0.15,
            "height": 3.0,
            "fire_rating": "1-hour"
        },
        confidence=sample_confidence_score,
        relationships=[
            Relationship(
                type="adjacent_to",
                target_id="test_room_101",
                confidence=0.90,
                properties={}
            )
        ],
        metadata=Metadata(
            source="test",
            created="2024-01-01T00:00:00",
            validated=False
        ),
        validation_state=ValidationState.PENDING,
        geometry={
            "type": "LineString",
            "coordinates": [[0, 0], [10, 0]]
        }
    )


@pytest.fixture
def sample_pdf_path():
    """Path to sample PDF for testing"""
    # Create test fixtures directory if it doesn't exist
    fixtures_dir = Path(__file__).parent / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)
    
    # Create a minimal PDF file for testing (or use existing)
    pdf_path = fixtures_dir / "sample_floor_plan.pdf"
    
    if not pdf_path.exists():
        # Create a simple PDF for testing
        # In production, you'd have actual floor plan PDFs
        import fitz  # PyMuPDF
        doc = fitz.open()
        page = doc.new_page(width=612, height=792)
        
        # Draw some simple walls
        shape = page.new_shape()
        shape.draw_line((100, 100), (500, 100))  # Top wall
        shape.draw_line((100, 100), (100, 400))  # Left wall
        shape.draw_line((500, 100), (500, 400))  # Right wall
        shape.draw_line((100, 400), (500, 400))  # Bottom wall
        shape.finish(width=2)
        shape.commit()
        
        doc.save(str(pdf_path))
        doc.close()
    
    return str(pdf_path)


@pytest.fixture
def expected_arxobjects():
    """Expected ArxObjects from sample PDF processing"""
    return [
        {
            "type": "wall",
            "confidence": {
                "classification": 0.85,
                "position": 0.90,
                "properties": 0.70,
                "relationships": 0.60,
                "overall": 0.78
            },
            "data": {
                "length": 10.0,
                "thickness": 0.15
            }
        },
        {
            "type": "room",
            "confidence": {
                "classification": 0.80,
                "position": 0.85,
                "properties": 0.65,
                "relationships": 0.70,
                "overall": 0.76
            },
            "data": {
                "area": 100.0,
                "perimeter": 40.0
            }
        }
    ]


@pytest.fixture
def mock_validation_data():
    """Mock validation data for testing"""
    return {
        "object_id": "test_wall_001",
        "validation_type": "dimension",
        "measured_value": 10.5,
        "units": "meters",
        "validator": "test_user",
        "confidence": 0.95
    }


@pytest.fixture
def mock_quality_assessment():
    """Mock PDF quality assessment result"""
    return {
        "extractability": 0.85,
        "vector_content": 0.90,
        "text_quality": 0.75,
        "scale_detection": True,
        "complexity": "medium",
        "recommendations": [
            "Good quality PDF suitable for extraction",
            "Vector content is high - expect accurate results"
        ]
    }


@pytest.fixture(autouse=True)
def reset_database():
    """Reset test database before each test"""
    # This would connect to test database and clean tables
    # For now, we'll just pass
    yield
    # Cleanup after test if needed


@pytest.fixture
def performance_timer():
    """Timer for performance testing"""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.elapsed = None
        
        def start(self):
            self.start_time = time.perf_counter()
        
        def stop(self):
            if self.start_time:
                self.elapsed = time.perf_counter() - self.start_time
                return self.elapsed
            return None
        
        def assert_under(self, seconds):
            assert self.elapsed is not None, "Timer not stopped"
            assert self.elapsed < seconds, f"Operation took {self.elapsed:.2f}s, expected under {seconds}s"
    
    return Timer()


# Fixtures for different building types
@pytest.fixture
def office_building_metadata():
    """Metadata for office building type"""
    return {
        "building_type": "office",
        "building_name": "Test Office Tower",
        "floors": 20,
        "approximate_size": "50000sqft"
    }


@pytest.fixture
def hospital_building_metadata():
    """Metadata for hospital building type"""
    return {
        "building_type": "hospital",
        "building_name": "Test Medical Center",
        "floors": 8,
        "approximate_size": "200000sqft"
    }


@pytest.fixture
def residential_building_metadata():
    """Metadata for residential building type"""
    return {
        "building_type": "residential",
        "building_name": "Test Apartments",
        "floors": 15,
        "approximate_size": "75000sqft"
    }