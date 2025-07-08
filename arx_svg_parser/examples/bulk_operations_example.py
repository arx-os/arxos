#!/usr/bin/env python3
"""
Bulk Operations Example

This script demonstrates how to use the bulk import and export operations
with different file formats and progress tracking.

Author: Arxos Development Team
Date: 2024
"""

import requests
import json
import csv
import yaml
import time
import io
from typing import List, Dict, Any

class BulkOperationsClient:
    """Client for testing bulk operations."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.auth_token = None
    
    def login(self, username: str = "admin", password: str = "admin123"):
        """Login and get authentication token."""
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
            print(f"✅ Logged in as {username}")
            return True
        else:
            print(f"❌ Login failed: {response.text}")
            return False
    
    def create_sample_symbols_json(self) -> str:
        """Create sample symbols data in JSON format."""
        symbols = [
            {
                "id": "bulk_test_1",
                "name": "Bulk Test Symbol 1",
                "system": "electrical",
                "svg": {
                    "content": "<svg width='50' height='50'><circle cx='25' cy='25' r='20' fill='blue'/></svg>"
                },
                "description": "Test symbol for bulk import",
                "category": "test",
                "tags": ["bulk", "test", "electrical"]
            },
            {
                "id": "bulk_test_2",
                "name": "Bulk Test Symbol 2",
                "system": "mechanical",
                "svg": {
                    "content": "<svg width='50' height='50'><rect width='40' height='40' fill='red'/></svg>"
                },
                "description": "Another test symbol",
                "category": "test",
                "tags": ["bulk", "test", "mechanical"]
            },
            {
                "id": "bulk_test_3",
                "name": "Bulk Test Symbol 3",
                "system": "plumbing",
                "svg": {
                    "content": "<svg width='50' height='50'><polygon points='25,5 45,45 5,45' fill='green'/></svg>"
                },
                "description": "Third test symbol",
                "category": "test",
                "tags": ["bulk", "test", "plumbing"]
            }
        ]
        
        return json.dumps(symbols, indent=2)
    
    def create_sample_symbols_csv(self) -> str:
        """Create sample symbols data in CSV format."""
        symbols = [
            {
                "id": "bulk_csv_1",
                "name": "CSV Test Symbol 1",
                "system": "electrical",
                "description": "CSV test symbol"
            },
            {
                "id": "bulk_csv_2",
                "name": "CSV Test Symbol 2",
                "system": "mechanical",
                "description": "Another CSV test symbol"
            }
        ]
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["id", "name", "system", "description"])
        writer.writeheader()
        writer.writerows(symbols)
        return output.getvalue()
    
    def create_sample_symbols_yaml(self) -> str:
        """Create sample symbols data in YAML format."""
        symbols = [
            {
                "id": "bulk_yaml_1",
                "name": "YAML Test Symbol 1",
                "system": "electrical",
                "svg": {
                    "content": "<svg width='50' height='50'><circle cx='25' cy='25' r='20' fill='purple'/></svg>"
                },
                "description": "YAML test symbol"
            },
            {
                "id": "bulk_yaml_2",
                "name": "YAML Test Symbol 2",
                "system": "mechanical",
                "svg": {
                    "content": "<svg width='50' height='50'><rect width='40' height='40' fill='orange'/></svg>"
                },
                "description": "Another YAML test symbol"
            }
        ]
        
        return yaml.dump(symbols, default_flow_style=False, allow_unicode=True)
    
    def bulk_import_json(self):
        """Test bulk import with JSON file."""
        print("\n📤 Testing Bulk Import (JSON)...")
        
        # Create JSON file content
        json_content = self.create_sample_symbols_json()
        
        # Upload file
        files = {"file": ("symbols.json", json_content, "application/json")}
        response = self.session.post(f"{self.base_url}/api/v1/symbols/bulk-import", files=files)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Import job created: {data['job_id']}")
            print(f"   Total symbols: {data['total_processed']}")
            
            # Monitor progress
            self.monitor_progress(data['job_id'])
        else:
            print(f"❌ Import failed: {response.text}")
    
    def bulk_import_csv(self):
        """Test bulk import with CSV file."""
        print("\n📤 Testing Bulk Import (CSV)...")
        
        # Create CSV file content
        csv_content = self.create_sample_symbols_csv()
        
        # Upload file
        files = {"file": ("symbols.csv", csv_content, "text/csv")}
        response = self.session.post(f"{self.base_url}/api/v1/symbols/bulk-import", files=files)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Import job created: {data['job_id']}")
            print(f"   Total symbols: {data['total_processed']}")
            
            # Monitor progress
            self.monitor_progress(data['job_id'])
        else:
            print(f"❌ Import failed: {response.text}")
    
    def bulk_import_yaml(self):
        """Test bulk import with YAML file."""
        print("\n📤 Testing Bulk Import (YAML)...")
        
        # Create YAML file content
        yaml_content = self.create_sample_symbols_yaml()
        
        # Upload file
        files = {"file": ("symbols.yaml", yaml_content, "application/x-yaml")}
        response = self.session.post(f"{self.base_url}/api/v1/symbols/bulk-import", files=files)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Import job created: {data['job_id']}")
            print(f"   Total symbols: {data['total_processed']}")
            
            # Monitor progress
            self.monitor_progress(data['job_id'])
        else:
            print(f"❌ Import failed: {response.text}")
    
    def bulk_export_json(self):
        """Test bulk export in JSON format."""
        print("\n📥 Testing Bulk Export (JSON)...")
        
        response = self.session.get(f"{self.base_url}/api/v1/symbols/export?format=json")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Export job created: {data.get('job_id', 'N/A')}")
            print(f"   Total symbols: {data['total_symbols']}")
            
            # Monitor progress and download
            if data.get('job_id'):
                self.monitor_progress_and_download(data['job_id'], "json")
        else:
            print(f"❌ Export failed: {response.text}")
    
    def bulk_export_csv(self):
        """Test bulk export in CSV format."""
        print("\n📥 Testing Bulk Export (CSV)...")
        
        response = self.session.get(f"{self.base_url}/api/v1/symbols/export?format=csv")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Export job created: {data.get('job_id', 'N/A')}")
            print(f"   Total symbols: {data['total_symbols']}")
            
            # Monitor progress and download
            if data.get('job_id'):
                self.monitor_progress_and_download(data['job_id'], "csv")
        else:
            print(f"❌ Export failed: {response.text}")
    
    def bulk_export_yaml(self):
        """Test bulk export in YAML format."""
        print("\n📥 Testing Bulk Export (YAML)...")
        
        response = self.session.get(f"{self.base_url}/api/v1/symbols/export?format=yaml")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Export job created: {data.get('job_id', 'N/A')}")
            print(f"   Total symbols: {data['total_symbols']}")
            
            # Monitor progress and download
            if data.get('job_id'):
                self.monitor_progress_and_download(data['job_id'], "yaml")
        else:
            print(f"❌ Export failed: {response.text}")
    
    def monitor_progress(self, job_id: str):
        """Monitor job progress."""
        print(f"   📊 Monitoring progress for job: {job_id}")
        
        max_attempts = 30  # 30 seconds timeout
        attempt = 0
        
        while attempt < max_attempts:
            response = self.session.get(f"{self.base_url}/api/v1/symbols/progress/{job_id}")
            
            if response.status_code == 200:
                data = response.json()
                status = data['status']
                progress = data['progress']
                
                print(f"   📈 Progress: {progress}% ({data['processed_items']}/{data['total_items']}) - Status: {status}")
                
                if status == "completed":
                    print(f"   ✅ Job completed successfully!")
                    if data.get('result'):
                        result = data['result']
                        if 'successful' in result:
                            print(f"      Successful: {result['successful']}")
                            print(f"      Failed: {result['failed']}")
                    return True
                elif status == "failed":
                    print(f"   ❌ Job failed!")
                    if data.get('result', {}).get('error'):
                        print(f"      Error: {data['result']['error']}")
                    return False
                
                time.sleep(1)
                attempt += 1
            else:
                print(f"   ❌ Failed to get progress: {response.text}")
                return False
        
        print(f"   ⏰ Timeout waiting for job completion")
        return False
    
    def monitor_progress_and_download(self, job_id: str, format_type: str):
        """Monitor progress and download the result."""
        if self.monitor_progress(job_id):
            print(f"   📥 Downloading {format_type} export...")
            
            response = self.session.get(f"{self.base_url}/api/v1/symbols/export/download?job_id={job_id}")
            
            if response.status_code == 200:
                # Save file
                filename = f"exported_symbols.{format_type}"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                
                print(f"   ✅ Export downloaded to: {filename}")
                print(f"   📄 File size: {len(response.content)} bytes")
            else:
                print(f"   ❌ Download failed: {response.text}")
    
    def run_all_tests(self):
        """Run all bulk operation tests."""
        print("🚀 Starting Bulk Operations Tests")
        print("=" * 50)
        
        # Test bulk imports
        self.bulk_import_json()
        self.bulk_import_csv()
        self.bulk_import_yaml()
        
        # Test bulk exports
        self.bulk_export_json()
        self.bulk_export_csv()
        self.bulk_export_yaml()
        
        print("\n🎉 All tests completed!")

def main():
    """Main function."""
    print("Arxos SVG Parser - Bulk Operations Example")
    print("=" * 50)
    
    # Create client
    client = BulkOperationsClient()
    
    # Login
    if not client.login():
        print("❌ Cannot proceed without authentication")
        return
    
    # Run tests
    client.run_all_tests()

if __name__ == "__main__":
    main() 