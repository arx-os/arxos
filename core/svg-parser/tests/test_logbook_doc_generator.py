"""
Tests for Logbook to Doc Generator Service

Comprehensive test suite for log processing, documentation generation,
and multi-format output.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from services.logbook_doc_generator import LogbookDocGenerator, DocFormat, LogEntryType
from routers.logbook_doc_generator import router
from fastapi.testclient import TestClient
from fastapi import FastAPI

class TestLogbookDocGeneratorService:
    @pytest.fixture
    def service(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        service = LogbookDocGenerator(db_path=db_path)
        yield service
        os.unlink(db_path)

    def test_process_log_entries(self, service):
        entries = service.process_log_entries()
        assert isinstance(entries, list)
        assert len(entries) > 0

    def test_generate_changelog(self, service):
        changelog = service.generate_changelog()
        assert changelog.version == "1.0.0"
        assert hasattr(changelog, 'impact_summary')

    def test_generate_contributor_summary(self, service):
        entries = service.process_log_entries()
        contributor = entries[0].author
        summary = service.generate_contributor_summary(contributor)
        assert summary.contributor_id == contributor
        assert summary.total_changes > 0

    def test_generate_system_evolution_report(self, service):
        report = service.generate_system_evolution_report()
        assert report.total_changes > 0
        assert report.active_contributors > 0

    def test_generate_documentation_markdown(self, service):
        doc = service.generate_documentation(doc_type="changelog", format=DocFormat.MARKDOWN)
        assert doc.format == DocFormat.MARKDOWN
        assert doc.content.startswith("# Changelog")

    def test_generate_documentation_json(self, service):
        doc = service.generate_documentation(doc_type="changelog", format=DocFormat.JSON)
        assert doc.format == DocFormat.JSON
        assert doc.content.strip().startswith("{")

    def test_generate_documentation_html(self, service):
        doc = service.generate_documentation(doc_type="changelog", format=DocFormat.HTML)
        assert doc.format == DocFormat.HTML
        assert doc.content.strip().startswith("<!DOCTYPE html>")

    def test_get_performance_metrics(self, service):
        metrics = service.get_performance_metrics()
        assert "total_entries" in metrics
        assert "total_docs_generated" in metrics

class TestLogbookDocGeneratorRouter:
    @pytest.fixture
    def client(self):
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_generate_documentation_endpoint(self, client):
        response = client.post("/logbook-docs/generate", json={"doc_type": "changelog", "format": "markdown"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["format"] == "markdown"

    def test_get_document_endpoint(self, client):
        # Generate a document first
        response = client.post("/logbook-docs/generate", json={"doc_type": "changelog", "format": "markdown"})
        doc_id = response.json()["document_id"]
        response = client.get(f"/logbook-docs/document/{doc_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["document_id"] == doc_id

    def test_status_endpoint(self, client):
        response = client.get("/logbook-docs/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "metrics" in data 