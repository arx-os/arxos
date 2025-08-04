"""
SVGX Engine Integration Test

Tests the complete integration between SVGX Engine, Browser CAD, and ArxIDE
including real-time collaboration, drawing operations, and API functionality.
"""

import asyncio
import json
import pytest
import requests
import websockets
from datetime import datetime
from typing import Dict, Any, List

class TestSVGXIntegration:
    """Test SVGX Engine integration with Browser CAD and ArxIDE"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1/svgx"
        self.websocket_url = "ws://localhost:8000/api/v1/svgx/ws"
        self.test_session_id = None
        self.test_client_id = "test-client-" + str(int(datetime.now().timestamp()))
    
    def test_api_health(self):
        """Test SVGX Engine API health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "SVGX Engine API"
            assert "version" in data
            assert "active_sessions" in data
            assert "active_connections" in data
            
            print("✅ SVGX Engine API health check passed")
            return True
            
        except Exception as e:
            print(f"❌ SVGX Engine API health check failed: {e}")
            return False
    
    def test_create_drawing_session(self):
        """Test creating a new drawing session"""
        try:
            payload = {
                "name": "Test Drawing",
                "precision_level": "0.001",
                "collaboration_enabled": True
            }
            
            response = requests.post(f"{self.base_url}/session/create", json=payload)
            assert response.status_code == 200
            
            data = response.json()
            assert "session_id" in data
            assert "drawing_id" in data
            assert data["name"] == "Test Drawing"
            assert data["precision_level"] == "0.001"
            assert data["collaboration_enabled"] == True
            
            self.test_session_id = data["session_id"]
            print(f"✅ Created drawing session: {self.test_session_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create drawing session: {e}")
            return False
    
    def test_join_drawing_session(self):
        """Test joining an existing drawing session"""
        if not self.test_session_id:
            print("⚠️  No session ID available, skipping join test")
            return False
            
        try:
            payload = {
                "session_id": self.test_session_id,
                "client_id": self.test_client_id
            }
            
            response = requests.post(f"{self.base_url}/session/join", json=payload)
            assert response.status_code == 200
            
            data = response.json()
            assert data["session_id"] == self.test_session_id
            assert "drawing_id" in data
            assert "message" in data
            
            print(f"✅ Joined drawing session: {self.test_session_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to join drawing session: {e}")
            return False
    
    def test_get_session_info(self):
        """Test getting session information"""
        if not self.test_session_id:
            print("⚠️  No session ID available, skipping session info test")
            return False
            
        try:
            response = requests.get(f"{self.base_url}/session/{self.test_session_id}/info")
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] == True
            assert "data" in data
            assert data["data"]["session_id"] == self.test_session_id
            
            print(f"✅ Retrieved session info for: {self.test_session_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to get session info: {e}")
            return False
    
    async def test_websocket_connection(self):
        """Test WebSocket connection for real-time collaboration"""
        if not self.test_session_id:
            print("⚠️  No session ID available, skipping WebSocket test")
            return False
            
        try:
            ws_url = f"{self.websocket_url}/{self.test_session_id}/{self.test_client_id}"
            
            async with websockets.connect(ws_url) as websocket:
                # Send a test message
                test_message = {
                    "type": "drawing_operation",
                    "sessionId": self.test_session_id,
                    "clientId": self.test_client_id,
                    "operation": {
                        "type": "test_operation",
                        "data": {"test": "data"},
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                await websocket.send(json.dumps(test_message))
                
                # Wait for response (should echo back)
                response = await websocket.recv()
                response_data = json.loads(response)
                
                assert response_data["type"] == "drawing_operation"
                assert response_data["sessionId"] == self.test_session_id
                
                print("✅ WebSocket connection and message passing test passed")
                return True
                
        except Exception as e:
            print(f"❌ WebSocket test failed: {e}")
            return False
    
    def test_real_time_update(self):
        """Test sending real-time updates"""
        if not self.test_session_id:
            print("⚠️  No session ID available, skipping real-time update test")
            return False
            
        try:
            payload = {
                "session_id": self.test_session_id,
                "client_id": self.test_client_id,
                "operation_type": "test_operation",
                "data": {
                    "tool": "line",
                    "startPoint": {"x": 100, "y": 100},
                    "endPoint": {"x": 200, "y": 200}
                }
            }
            
            response = requests.post(f"{self.base_url}/session/{self.test_session_id}/update", json=payload)
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] == True
            assert "message" in data
            assert "timestamp" in data
            
            print("✅ Real-time update test passed")
            return True
            
        except Exception as e:
            print(f"❌ Real-time update test failed: {e}")
            return False
    
    def test_export_drawing(self):
        """Test exporting drawing session"""
        if not self.test_session_id:
            print("⚠️  No session ID available, skipping export test")
            return False
            
        try:
            payload = {
                "format": "svgx"
            }
            
            response = requests.post(f"{self.base_url}/session/{self.test_session_id}/export", json=payload)
            assert response.status_code == 200
            
            data = response.json()
            assert data["session_id"] == self.test_session_id
            assert data["format"] == "svgx"
            assert "file_url" in data
            assert "message" in data
            
            print("✅ Drawing export test passed")
            return True
            
        except Exception as e:
            print(f"❌ Drawing export test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting SVGX Engine Integration Tests")
        print("=" * 50)
        
        results = []
        
        # Test API health
        results.append(("API Health", self.test_api_health()))
        
        # Test session creation
        results.append(("Create Session", self.test_create_drawing_session()))
        
        # Test session joining
        results.append(("Join Session", self.test_join_drawing_session()))
        
        # Test session info
        results.append(("Session Info", self.test_get_session_info()))
        
        # Test real-time updates
        results.append(("Real-time Updates", self.test_real_time_update()))
        
        # Test drawing export
        results.append(("Drawing Export", self.test_export_drawing()))
        
        # Test WebSocket connection (async)
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            websocket_result = loop.run_until_complete(self.test_websocket_connection())
            results.append(("WebSocket Connection", websocket_result))
            loop.close()
        except Exception as e:
            print(f"❌ WebSocket test failed: {e}")
            results.append(("WebSocket Connection", False))
        
        # Print results
        print("\n" + "=" * 50)
        print("📊 Test Results:")
        print("=" * 50)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<25} {status}")
            if result:
                passed += 1
        
        print("=" * 50)
        print(f"Total: {total}, Passed: {passed}, Failed: {total - passed}")
        
        if passed == total:
            print("🎉 All tests passed! SVGX Engine integration is working correctly.")
        else:
            print("⚠️  Some tests failed. Please check the implementation.")
        
        return passed == total

def main():
    """Main test runner"""
    tester = TestSVGXIntegration()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ SVGX Engine Integration Test Suite: PASSED")
        return 0
    else:
        print("\n❌ SVGX Engine Integration Test Suite: FAILED")
        return 1

if __name__ == "__main__":
    exit(main()) 