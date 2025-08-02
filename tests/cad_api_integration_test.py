#!/usr/bin/env python3
"""
CAD API Integration Test Suite
Tests the integration between the CAD system and existing Arxos backend

@author Arxos Team
@version 1.0.0
@license MIT
"""

import unittest
import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestCadApiIntegration(unittest.TestCase):
    """Test suite for CAD API integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_data_dir = project_root / "tests" / "test_data"
        self.test_data_dir.mkdir(exist_ok=True)
        
        # Test configuration
        self.config = {
            "api_base_url": "/api",
            "auth_token": "test_token_123",
            "project_id": "test_project_456",
            "building_id": "test_building_789"
        }
    
    def test_api_client_structure(self):
        """Test that the API client file exists and has correct structure"""
        api_client_path = project_root / "frontend/web/static/js/cad-api-client.js"
        
        self.assertTrue(api_client_path.exists(), "CAD API client file not found")
        
        with open(api_client_path, 'r') as f:
            content = f.read()
        
        # Check for required class
        self.assertIn("class CadApiClient", content)
        
        # Check for required methods
        required_methods = [
            "createProject",
            "getProjects", 
            "getProject",
            "updateProject",
            "deleteProject",
            "saveCadProject",
            "loadCadProject",
            "exportCadToSVGX",
            "importCadFromSVGX"
        ]
        
        for method in required_methods:
            self.assertIn(f"{method}(", content, f"Missing method: {method}")
    
    def test_cad_ui_api_integration(self):
        """Test that CAD UI integrates with API client"""
        cad_ui_path = project_root / "frontend/web/static/js/cad-ui.js"
        
        with open(cad_ui_path, 'r') as f:
            content = f.read()
        
        # Check for API client integration
        self.assertIn("this.apiClient = new CadApiClient()", content)
        self.assertIn("this.apiClient.getCurrentUser()", content)
        self.assertIn("this.apiClient.saveCadProject(", content)
        self.assertIn("this.apiClient.loadCadProject(", content)
    
    def test_project_management_integration(self):
        """Test project management integration"""
        cad_ui_path = project_root / "frontend/web/static/js/cad-ui.js"
        
        with open(cad_ui_path, 'r') as f:
            content = f.read()
        
        # Check for project management methods
        project_methods = [
            "createNewProject",
            "loadProject", 
            "saveProject",
            "exportToSVGX",
            "importFromSVGX",
            "loadCadData"
        ]
        
        for method in project_methods:
            self.assertIn(f"{method}(", content, f"Missing project method: {method}")
    
    def test_auto_save_functionality(self):
        """Test auto-save functionality"""
        cad_ui_path = project_root / "frontend/web/static/js/cad-ui.js"
        
        with open(cad_ui_path, 'r') as f:
            content = f.read()
        
        # Check for auto-save methods
        auto_save_methods = [
            "startAutoSave",
            "stopAutoSave", 
            "toggleAutoSave"
        ]
        
        for method in auto_save_methods:
            self.assertIn(f"{method}(", content, f"Missing auto-save method: {method}")
    
    def test_notification_system(self):
        """Test notification system"""
        cad_ui_path = project_root / "frontend/web/static/js/cad-ui.js"
        
        with open(cad_ui_path, 'r') as f:
            content = f.read()
        
        # Check for notification method
        self.assertIn("showNotification(", content)
    
    def test_html_integration(self):
        """Test HTML integration with API features"""
        html_path = project_root / "frontend/web/browser-cad/index.html"
        
        with open(html_path, 'r') as f:
            content = f.read()
        
        # Check for API client script inclusion
        self.assertIn("cad-api-client.js", content)
        
        # Check for project management UI elements
        self.assertIn('id="project-info"', content)
        self.assertIn('id="project-list"', content)
        self.assertIn('id="new-project"', content)
    
    def test_api_endpoints_mapping(self):
        """Test API endpoints mapping"""
        api_client_path = project_root / "frontend/web/static/js/cad-api-client.js"
        
        with open(api_client_path, 'r') as f:
            content = f.read()
        
        # Check for endpoint mappings
        required_endpoints = [
            "projects: '/projects'",
            "project: (id) => `/projects/${id}`",
            "buildings: '/buildings'",
            "rooms: '/rooms'",
            "devices: '/devices'",
            "floors: '/floors'"
        ]
        
        for endpoint in required_endpoints:
            self.assertIn(endpoint, content, f"Missing endpoint: {endpoint}")
    
    def test_authentication_integration(self):
        """Test authentication integration"""
        api_client_path = project_root / "frontend/web/static/js/cad-api-client.js"
        
        with open(api_client_path, 'r') as f:
            content = f.read()
        
        # Check for authentication methods
        auth_methods = [
            "getAuthToken()",
            "updateAuthToken(",
            "handleAuthError()"
        ]
        
        for method in auth_methods:
            self.assertIn(method, content, f"Missing auth method: {method}")
    
    def test_error_handling(self):
        """Test error handling in API client"""
        api_client_path = project_root / "frontend/web/static/js/cad-api-client.js"
        
        with open(api_client_path, 'r') as f:
            content = f.read()
        
        # Check for error handling
        self.assertIn("catch (error)", content)
        self.assertIn("console.error", content)
        self.assertIn("response.status === 401", content)
    
    def test_cad_specific_api_methods(self):
        """Test CAD-specific API methods"""
        api_client_path = project_root / "frontend/web/static/js/cad-api-client.js"
        
        with open(api_client_path, 'r') as f:
            content = f.read()
        
        # Check for CAD-specific methods
        cad_methods = [
            "saveCadProject(",
            "loadCadProject(",
            "exportCadToSVGX(",
            "importCadFromSVGX("
        ]
        
        for method in cad_methods:
            self.assertIn(method, content, f"Missing CAD method: {method}")
    
    def test_collaboration_api_methods(self):
        """Test collaboration API methods"""
        api_client_path = project_root / "frontend/web/static/js/cad-api-client.js"
        
        with open(api_client_path, 'r') as f:
            content = f.read()
        
        # Check for collaboration methods
        collaboration_methods = [
            "joinCollaboration(",
            "leaveCollaboration(",
            "sendCollaborationUpdate("
        ]
        
        for method in collaboration_methods:
            self.assertIn(method, content, f"Missing collaboration method: {method}")
    
    def test_ai_integration_api_methods(self):
        """Test AI integration API methods"""
        api_client_path = project_root / "frontend/web/static/js/cad-api-client.js"
        
        with open(api_client_path, 'r') as f:
            content = f.read()
        
        # Check for AI integration methods
        ai_methods = [
            "processAiCommand(",
            "getAiSuggestions("
        ]
        
        for method in ai_methods:
            self.assertIn(method, content, f"Missing AI method: {method}")
    
    def test_file_upload_download_methods(self):
        """Test file upload/download methods"""
        api_client_path = project_root / "frontend/web/static/js/cad-api-client.js"
        
        with open(api_client_path, 'r') as f:
            content = f.read()
        
        # Check for file methods
        file_methods = [
            "uploadFile(",
            "downloadFile("
        ]
        
        for method in file_methods:
            self.assertIn(method, content, f"Missing file method: {method}")
    
    def test_symbol_library_integration(self):
        """Test symbol library integration"""
        api_client_path = project_root / "frontend/web/static/js/cad-api-client.js"
        
        with open(api_client_path, 'r') as f:
            content = f.read()
        
        # Check for symbol library methods
        symbol_methods = [
            "getSymbols(",
            "getSymbol(",
            "searchSymbols(",
            "getSymbolCategories("
        ]
        
        for method in symbol_methods:
            self.assertIn(method, content, f"Missing symbol method: {method}")
    
    def test_health_monitoring_integration(self):
        """Test health monitoring integration"""
        api_client_path = project_root / "frontend/web/static/js/cad-api-client.js"
        
        with open(api_client_path, 'r') as f:
            content = f.read()
        
        # Check for health monitoring methods
        health_methods = [
            "getHealth()",
            "getDetailedHealth()",
            "getHealthMetrics()"
        ]
        
        for method in health_methods:
            self.assertIn(method, content, f"Missing health method: {method}")
    
    def test_data_persistence_integration(self):
        """Test data persistence integration"""
        cad_ui_path = project_root / "frontend/web/static/js/cad-ui.js"
        
        with open(cad_ui_path, 'r') as f:
            content = f.read()
        
        # Check for data persistence methods
        persistence_methods = [
            "loadCadData(",
            "updateProjectUI(",
            "updateProjectList("
        ]
        
        for method in persistence_methods:
            self.assertIn(method, content, f"Missing persistence method: {method}")
    
    def test_ui_event_handlers(self):
        """Test UI event handlers"""
        cad_ui_path = project_root / "frontend/web/static/js/cad-ui.js"
        
        with open(cad_ui_path, 'r') as f:
            content = f.read()
        
        # Check for event handler methods
        event_methods = [
            "initializeProjectButtons(",
            "showNewProjectModal("
        ]
        
        for method in event_methods:
            self.assertIn(method, content, f"Missing event handler method: {method}")
    
    def test_backend_api_compatibility(self):
        """Test compatibility with existing backend APIs"""
        # Check that API endpoints match existing backend structure
        api_client_path = project_root / "frontend/web/static/js/cad-api-client.js"
        
        with open(api_client_path, 'r') as f:
            content = f.read()
        
        # Check for compatibility with existing endpoints
        existing_endpoints = [
            "/projects",
            "/buildings", 
            "/rooms",
            "/devices",
            "/floors",
            "/users",
            "/health"
        ]
        
        for endpoint in existing_endpoints:
            self.assertIn(endpoint, content, f"Missing existing endpoint: {endpoint}")
    
    def test_error_recovery_mechanisms(self):
        """Test error recovery mechanisms"""
        api_client_path = project_root / "frontend/web/static/js/cad-api-client.js"
        
        with open(api_client_path, 'r') as f:
            content = f.read()
        
        # Check for error recovery
        self.assertIn("localStorage.removeItem('authToken')", content)
        self.assertIn("sessionStorage.removeItem('authToken')", content)
        self.assertIn("window.location.href = '/login'", content)
    
    def test_performance_optimization(self):
        """Test performance optimization features"""
        cad_ui_path = project_root / "frontend/web/static/js/cad-ui.js"
        
        with open(cad_ui_path, 'r') as f:
            content = f.read()
        
        # Check for performance features
        self.assertIn("autoSaveInterval", content)
        self.assertIn("30000", content)  # 30 second auto-save interval
        self.assertIn("autoSaveEnabled", content)

if __name__ == '__main__':
    # Create test runner
    unittest.main(verbosity=2) 