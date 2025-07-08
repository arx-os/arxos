"""
Example: Using the Authenticated Symbol API

This script demonstrates how to use the symbol management API with authentication,
including login, token usage, and different permission levels.

Author: Arxos Development Team
Date: 2024
"""

import requests
import json
from typing import Dict, Any

# API Configuration
BASE_URL = "http://localhost:8000"  # Adjust to your API server URL

class SymbolAPIClient:
    """Client for interacting with the authenticated symbol API."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.token = None
        self.headers = {"Content-Type": "application/json"}
    
    def login(self, username: str, password: str) -> bool:
        """Login and get access token."""
        url = f"{self.base_url}/auth/login"
        data = {"username": username, "password": password}
        
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.token = token_data["access_token"]
            self.headers["Authorization"] = f"Bearer {self.token}"
            
            print(f"✅ Logged in as {username} with role: {token_data['role']}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Login failed: {e}")
            return False
    
    def create_symbol(self, symbol_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new symbol."""
        url = f"{self.base_url}/symbols/"
        
        try:
            response = requests.post(url, json=symbol_data, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Create symbol failed: {e}")
            return {}
    
    def get_symbol(self, symbol_id: str) -> Dict[str, Any]:
        """Get a symbol by ID."""
        url = f"{self.base_url}/symbols/{symbol_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Get symbol failed: {e}")
            return {}
    
    def update_symbol(self, symbol_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a symbol."""
        url = f"{self.base_url}/symbols/{symbol_id}"
        
        try:
            response = requests.put(url, json=updates, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Update symbol failed: {e}")
            return {}
    
    def delete_symbol(self, symbol_id: str) -> bool:
        """Delete a symbol."""
        url = f"{self.base_url}/symbols/{symbol_id}"
        
        try:
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Delete symbol failed: {e}")
            return False
    
    def list_symbols(self, system: str = None) -> list:
        """List symbols."""
        url = f"{self.base_url}/symbols/"
        params = {}
        if system:
            params["system"] = system
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ List symbols failed: {e}")
            return []
    
    def search_symbols(self, query: str, system: str = None) -> list:
        """Search symbols."""
        url = f"{self.base_url}/symbols/"
        params = {"query": query}
        if system:
            params["system"] = system
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Search symbols failed: {e}")
            return []
    
    def bulk_create_symbols(self, symbols: list) -> list:
        """Bulk create symbols."""
        url = f"{self.base_url}/symbols/bulk_create"
        
        try:
            response = requests.post(url, json=symbols, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Bulk create symbols failed: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get symbol statistics."""
        url = f"{self.base_url}/symbols/statistics"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Get statistics failed: {e}")
            return {}


def demonstrate_permissions():
    """Demonstrate different permission levels."""
    print("🔐 Demonstrating Authentication and Permissions\n")
    
    # Test with different user roles
    users = [
        ("admin", "admin123"),
        ("editor", "editor123"),
        ("viewer", "viewer123"),
    ]
    
    for username, password in users:
        print(f"\n👤 Testing with user: {username}")
        client = SymbolAPIClient()
        
        # Login
        if not client.login(username, password):
            continue
        
        # Test permissions
        test_symbol_data = {
            "name": f"Test Symbol by {username}",
            "system": "mechanical",
            "svg": {
                "content": "<g><rect x='0' y='0' width='20' height='20' fill='#fff' stroke='#000'/></g>",
                "width": 20,
                "height": 20,
                "scale": 1.0
            },
            "description": f"Test symbol created by {username}",
            "tags": ["test", "demo"]
        }
        
        # Try to create symbol
        print(f"  📝 Attempting to create symbol...")
        created_symbol = client.create_symbol(test_symbol_data)
        if created_symbol:
            symbol_id = created_symbol.get("id")
            print(f"  ✅ Successfully created symbol: {symbol_id}")
            
            # Try to read symbol
            print(f"  📖 Reading symbol...")
            retrieved_symbol = client.get_symbol(symbol_id)
            if retrieved_symbol:
                print(f"  ✅ Successfully read symbol")
            
            # Try to update symbol
            print(f"  ✏️  Updating symbol...")
            updates = {"description": f"Updated by {username}"}
            updated_symbol = client.update_symbol(symbol_id, updates)
            if updated_symbol:
                print(f"  ✅ Successfully updated symbol")
            
            # Try to delete symbol
            print(f"  🗑️  Deleting symbol...")
            if client.delete_symbol(symbol_id):
                print(f"  ✅ Successfully deleted symbol")
            else:
                print(f"  ❌ Failed to delete symbol (permission denied)")
        else:
            print(f"  ❌ Failed to create symbol (permission denied)")
        
        # Try to get statistics
        print(f"  📊 Getting statistics...")
        stats = client.get_statistics()
        if stats:
            print(f"  ✅ Successfully retrieved statistics")
        else:
            print(f"  ❌ Failed to get statistics (permission denied)")


def demonstrate_bulk_operations():
    """Demonstrate bulk operations with admin user."""
    print("\n📦 Demonstrating Bulk Operations\n")
    
    client = SymbolAPIClient()
    
    # Login as admin
    if not client.login("admin", "admin123"):
        print("❌ Failed to login as admin")
        return
    
    # Prepare bulk symbols
    bulk_symbols = [
        {
            "name": "Bulk Symbol 1",
            "system": "mechanical",
            "svg": {
                "content": "<g><rect x='0' y='0' width='20' height='20' fill='#fff' stroke='#000'/></g>",
                "width": 20,
                "height": 20,
                "scale": 1.0
            },
            "description": "First bulk symbol",
            "tags": ["bulk", "test"]
        },
        {
            "name": "Bulk Symbol 2",
            "system": "electrical",
            "svg": {
                "content": "<g><circle cx='10' cy='10' r='10' fill='#fff' stroke='#000'/></g>",
                "width": 20,
                "height": 20,
                "scale": 1.0
            },
            "description": "Second bulk symbol",
            "tags": ["bulk", "test"]
        }
    ]
    
    # Bulk create
    print("📝 Bulk creating symbols...")
    created_symbols = client.bulk_create_symbols(bulk_symbols)
    print(f"✅ Created {len(created_symbols)} symbols")
    
    # List symbols
    print("📋 Listing all symbols...")
    symbols = client.list_symbols()
    print(f"📊 Total symbols: {len(symbols)}")
    
    # Search symbols
    print("🔍 Searching for 'bulk' symbols...")
    search_results = client.search_symbols("bulk")
    print(f"🔍 Found {len(search_results)} symbols matching 'bulk'")


def demonstrate_user_management():
    """Demonstrate user management with admin user."""
    print("\n👥 Demonstrating User Management\n")
    
    client = SymbolAPIClient()
    
    # Login as admin
    if not client.login("admin", "admin123"):
        print("❌ Failed to login as admin")
        return
    
    # Get users (admin only)
    url = f"{BASE_URL}/users/"
    try:
        response = requests.get(url, headers=client.headers)
        response.raise_for_status()
        users = response.json()
        print(f"👥 Current users: {len(users)}")
        for user in users:
            print(f"  - {user['username']} ({user['role']})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to get users: {e}")


if __name__ == "__main__":
    print("🚀 Symbol API Authentication Demo")
    print("=" * 50)
    
    # Note: This example assumes the API server is running
    # You would need to start the FastAPI server first
    
    print("\n⚠️  Note: Make sure the API server is running before executing this example")
    print("   Start the server with: uvicorn api.symbol_api:router --reload")
    
    # Uncomment the following lines to run the demonstrations
    # demonstrate_permissions()
    # demonstrate_bulk_operations()
    # demonstrate_user_management()
    
    print("\n📚 Example API Usage:")
    print("""
    # Login
    client = SymbolAPIClient()
    client.login("admin", "admin123")
    
    # Create symbol
    symbol_data = {
        "name": "My Symbol",
        "system": "mechanical",
        "svg": {"content": "<g><rect x='0' y='0' width='20' height='20'/></g>"}
    }
    created = client.create_symbol(symbol_data)
    
    # List symbols
    symbols = client.list_symbols()
    
    # Search symbols
    results = client.search_symbols("mechanical")
    """) 