"""
Integration Tests: End-to-End SVG-to-BIM Pipeline

- Tests the full pipeline from SVG input to BIM assembly, validation, and export via API
"""

import unittest
from fastapi.testclient import TestClient
from ..api.bim_api import app

class TestSVGToBIMIntegration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.svg_sample = """
        <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
            <rect x="100" y="100" width="200" height="20" fill="gray" data-bim-type="wall"/>
            <rect x="300" y="100" width="100" height="20" fill="gray" data-bim-type="wall"/>
            <rect x="150" y="200" width="50" height="50" fill="blue" data-bim-type="room"/>
        </svg>
        """
        self.user_id = "testuser"
        self.project_id = "testproject"

    def test_svg_to_bim_assembly_and_query(self):
        # Assemble BIM
        response = self.client.post("/bim/assemble", json={
            "svg_data": self.svg_sample,
            "user_id": self.user_id,
            "project_id": self.project_id
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("model_id", data)
        model_id = data["model_id"]
        # Query BIM
        response = self.client.post("/bim/query", json={
            "model_id": model_id,
            "user_id": self.user_id,
            "project_id": self.project_id
        })
        self.assertEqual(response.status_code, 200)
        model = response.json()
        self.assertIn("rooms", model)
        self.assertIn("walls", model)

    def test_bim_validation_and_export(self):
        # Assemble BIM
        response = self.client.post("/bim/assemble", json={
            "svg_data": self.svg_sample,
            "user_id": self.user_id,
            "project_id": self.project_id
        })
        model_id = response.json()["model_id"]
        # Validate BIM
        response = self.client.post("/bim/validate", json={
            "model_id": model_id,
            "user_id": self.user_id,
            "project_id": self.project_id
        })
        self.assertEqual(response.status_code, 200)
        validation = response.json()
        self.assertIn("valid", validation)
        # Export BIM
        response = self.client.post("/bim/export", json={
            "model_id": model_id,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "format": "json"
        })
        self.assertEqual(response.status_code, 200)
        export = response.json()
        self.assertIn("export", export) 